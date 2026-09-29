Tiếp tục với **BOOTSTRAP-002 — Minimal Self-Hosting Subset**.

Đây là bước rất quan trọng vì nó kiểm tra một giả thuyết cốt lõi của Axiom:

> **Axiom đủ mạnh để viết một compiler native hiệu năng cao, nhưng không buộc người viết compiler phải vật lộn với ownership/reference/GC/runtime.**

# BOOTSTRAP-002 — MINIMAL SELF-HOSTING SUBSET

## 1. Mục tiêu

Ta không cố hỗ trợ toàn bộ Axiom rồi mới viết compiler.

Mục tiêu là tìm **tập con nhỏ nhất nhưng đủ thực dụng**:

```text
Axiom Self-Hosting Subset
```

để viết:

```text
Lexer
Parser
Resolver
Type Checker
HIR
Ownership
MIR
Optimizer
Backend
Object Writer
Linker
Driver
```

---

# 2. Self-hosting subset không phải "Axiom Lite"

Điểm này rất quan trọng.

Không tạo một ngôn ngữ thứ hai kiểu:

```text
Axiom Bootstrap Language
```

rồi sau đó chuyển sang Axiom.

Thay vào đó:

```text
Axiom v0.1
    └── compiler-usable subset
```

Tức là mọi semantics đều là Axiom thật.

Ví dụ nếu Axiom có:

```text
struct
enum
trait
generic
match
ownership
```

thì compiler dùng **chính những semantics đó**.

---

# 3. Những gì compiler thực sự cần

Sau khi phân tích compiler architecture, subset cần:

```text
Core Language
├── primitive types
├── struct
├── enum
├── tuple
├── array
├── function
├── generic
├── trait
├── impl
├── module
├── match
├── if
├── loop
├── while
├── for
├── let
├── var
├── closure
├── Result
├── Option
├── ownership
├── view
├── mut_view
└── comptime (limited)
```

---

# 4. Những thứ compiler chưa cần

Có thể trì hoãn:

```text
async
GPU
dyn Trait
runtime reflection
advanced comptime
network
GUI
HTTP
database
filesystem watcher
```

Compiler có thể dùng filesystem sync thông thường.

Không cần async để viết compiler đầu tiên.

---

# 5. Compiler không cần GC

Đây là một test rất hay cho thiết kế Axiom.

Compiler có rất nhiều dữ liệu dạng:

```text
AST
HIR
Type
Symbol
MIR
Instruction
Diagnostic
```

Nhưng không cần GC.

Ví dụ:

```text id="h9j9xw"
struct Ast {
    nodes: Vec<Node>,
}
```

Compiler sở hữu:

```text
Ast
```

và các view:

```text
view<Node>
```

chỉ tồn tại trong phạm vi sử dụng.

Khi AST chết:

```text
Drop
```

được thực hiện deterministic.

---

# 6. Nhưng đừng biến compiler thành "borrow-checker torture"

Đây là điểm tôi muốn điều chỉnh rất rõ so với cách thiết kế Rust.

Trong compiler Axiom:

```text
let ast = Parser.parse(source);

Resolver.resolve(ast);
TypeChecker.check(ast);
```

Không nên buộc programmer phải viết hàng loạt:

```text
view<'a>
mut_view<'b>
lifetime...
```

Axiom compiler tự suy luận.

Nếu cần:

```text
view<Node>
```

thì compiler quản lý provenance/lifetime phía sau.

---

# 7. Compiler Data Ownership

Kiến trúc nên thiên về:

```text
Owner
    ↓
Arena / Vec / Table
    ↓
IDs / Handles
```

thay vì:

```text
Node chứa pointer tới Node
Node chứa pointer tới Type
Type chứa pointer tới Symbol
Symbol chứa pointer tới Node
```

Ví dụ:

```text
struct AstNode {
    kind: NodeKind,
    span: Span,
}

type NodeId = u32;

struct Ast {
    nodes: Vec<AstNode>,
}
```

Tham chiếu:

```text
NodeId
```

thay vì raw pointer.

---

# 8. Đây là trường hợp Handle rất phù hợp

Ta đã phân biệt:

```text
Value Identity
Storage Identity
Logical Identity
```

Compiler nên sử dụng:

```text
NodeId
TypeId
SymbolId
ScopeId
FunctionId
BlockId
LocalId
```

Ví dụ:

```text
struct TypeId {
    index: u32,
    generation: u32,
}
```

nếu cần chống stale handle.

---

# 9. Không nên over-engineer generation ngay

Compiler phase thường có ownership khá rõ.

MVP có thể:

```text
type NodeId = u32;
```

và container:

```text
AstArena
```

chịu trách nhiệm validity.

Generation handle chỉ cần khi:

```text
remove/reuse
```

thực sự xảy ra.

Điều này phù hợp philosophy:

> Không thêm cơ chế chỉ để giải quyết vấn đề chưa tồn tại.

---

# 10. Arena rất hữu ích cho compiler

Compiler có nhiều dữ liệu:

```text
AST
HIR
temporary types
diagnostic nodes
symbol tables
```

Arena cho phép:

```text
Parser
   ↓
AstArena
   ↓
Resolver
   ↓
TypeChecker
```

và cuối phase:

```text
drop arena
```

toàn bộ memory được giải phóng một lần.

---

# 11. Arena không phải GC

Ví dụ:

```text
Arena<AstNode>
```

có:

```text
owner = Arena
```

Các:

```text
NodeId
view<Node>
```

không được phép sống lâu hơn arena.

Không có tracing.

Không có background collector.

---

# 12. Compiler có thể dùng nhiều Arena

Ví dụ:

```text id="b2m5c0"
ParseArena
TypeArena
MirArena
DiagnosticArena
```

Mỗi phase có lifetime rõ.

Điều này giúp giảm fragmentation và đơn giản hóa lifetime.

---

# 13. Compiler nên ưu tiên immutable data

Ví dụ:

```text id="bqj9m4"
AST
```

sau parsing gần như immutable.

Resolver tạo:

```text id="q1a6l8"
ResolvedAST / HIR
```

Type checker tạo:

```text id="xj5o3n"
TypedHIR
```

MIR:

```text id="w8nt5x"
VerifiedMIR
```

Thay vì tất cả phase cùng mutate một object graph khổng lồ.

---

# 14. Pipeline dữ liệu

```text id="4c2q54"
Source
  ↓
AST
  ↓
Resolved HIR
  ↓
Typed HIR
  ↓
Verified HIR
  ↓
MIR
  ↓
Optimized MIR
  ↓
LIR
  ↓
Machine IR
```

Mỗi phase có ownership rõ.

Điều này làm Axiom compiler dễ kiểm soát hơn rất nhiều.

---

# 15. Không cần copy toàn bộ dữ liệu

Điều này không có nghĩa:

```text id="d2j9ar"
AST → deep copy → HIR
HIR → deep copy → MIR
```

Không.

Có thể:

```text id="0b0ux7"
AST
 ↓
lower
 ↓
HIR
```

và sau khi HIR hoàn tất:

```text id="qv1wq4"
AST arena
↓
DROP
```

Compiler chỉ giữ semantic data cần thiết.

---

# 16. `view` giúp giảm copy

Ví dụ parser:

```text id="f9y5zk"
fn parse(tokens: view<Token>) -> Ast
```

Không copy toàn bộ token array.

Resolver:

```text id="3f6m9z"
fn resolve(ast: view<Ast>) -> HIR
```

Type checker:

```text id="1a3z3u"
fn check(hir: view<HIR>) -> TypedHIR
```

Đây chính là use case Axiom muốn làm đơn giản.

---

# 17. `mut_view`

Khi cần mutation:

```text id="b4gq0c"
fn optimize(mir: mut_view<MIR>)
```

compiler programmer không phải quản lý lifetime.

Axiom verifier tự đảm bảo:

```text
không có read/write conflict
```

---

# 18. Nhưng compiler cũng cần persistent tables

Ví dụ type interner:

```text id="b3cv3f"
TypeInterner
```

sống lâu hơn nhiều phase.

Kiến trúc:

```text
CompilerContext
├── TypeInterner
├── SymbolDatabase
├── Target
├── Diagnostics
└── Intern tables
```

Các phase nhận:

```text
view<CompilerContext>
```

hoặc capability cụ thể.

---

# 19. CompilerContext không nên là God Object

Không làm:

```text
struct CompilerContext {
    everything...
}
```

rồi mọi function có:

```text
fn foo(ctx: mut_view<CompilerContext>)
```

Điều này phá vỡ lợi ích của capability model.

Thay vào đó:

```text
ParserContext
ResolverContext
TypeContext
MirContext
CodegenContext
```

và shared immutable databases.

---

# 20. Semantic Database

Có thể có:

```text
CompilerDatabase
```

nhưng API phải granular.

Ví dụ:

```text
db.type_of(expr_id)
db.symbol(symbol_id)
db.module(module_id)
db.layout(type_id)
```

Không cần cho mọi phase quyền mutation toàn bộ database.

---

# 21. Query architecture

Sau này có thể tiến tới:

```text
query:
    parse(file)
    resolve(module)
    type_of(expr)
    layout(type)
    mir(function)
```

Mỗi query có:

```text
inputs
outputs
cache key
dependencies
```

Điều này cực kỳ phù hợp incremental compilation.

---

# 22. Nhưng không cần bắt chước Salsa

Không nhất thiết phải đưa ngay một framework incremental phức tạp.

MVP:

```text
explicit dependency graph
+
semantic hashes
+
artifact cache
```

sau này mới tối ưu thành query engine nếu cần.

---

# 23. Compiler Collections

Compiler cần tối thiểu:

```text
Vec<T>
Map<K,V>
Set<T>
String
Buffer
```

Nhưng implementation có thể rất đơn giản ban đầu.

Ví dụ:

```text
Vec<T>
```

đủ:

```text
push
pop
get
set
len
capacity
reserve
view
mut_view
```

Không cần hàng trăm method.

---

# 24. String

Compiler cần ít nhất:

```text
String
StringView
```

và source text có thể được lưu:

```text
Buffer<u8>
```

Không cần Unicode processing đầy đủ.

Lexer đã có:

```text
UTF-8
```

nhưng compiler không cần grapheme engine.

---

# 25. HashMap

Compiler gần như chắc chắn cần.

MVP có thể:

```text
HashMap<K,V>
```

với:

```text
open addressing
```

thay vì tree.

Lý do:

- cache locality
- implementation đơn giản
- ít allocation
- compiler workload phù hợp

---

# 26. Interning

Compiler cần intern:

```text
Identifier
Type
Symbol name
String literals
```

Ví dụ:

```text
StringId
```

thay vì copy string liên tục.

```text
"foo"
"foo"
"foo"
```

→ cùng:

```text
StringId(42)
```

---

# 27. Compiler Memory Model

Đây là một test quan trọng cho Axiom.

Ta có:

```text
Compiler
├── SourceBuffer
├── TokenBuffer
├── AstArena
├── HirArena
├── TypeInterner
├── MirArena
└── Diagnostics
```

Mỗi component có owner rõ ràng.

Không cần:

```text
GC
```

Không cần:

```text
Rc mọi nơi
```

Không cần:

```text
Arc mọi nơi
```

---

# 28. Shared immutable compiler state

Nếu compiler parallel:

```text
Thread A ─┐
Thread B ─┼── read TypeInterner
Thread C ─┘
```

có thể dùng:

```text
Arc<TypeInterner>
```

nếu thực sự cần shared ownership.

Nhưng mutation:

```text
intern()
```

có thể được serialize hoặc dùng specialized concurrent structure.

Không biến mọi object thành Arc.

---

# 29. Parallel compiler architecture

Ví dụ:

```text
Module A ──┐
Module B ──┼── Type checking
Module C ──┘
```

có thể chạy song song nếu dependency graph cho phép.

Sau đó:

```text
MIR generation
```

song song.

Codegen:

```text
Function A ──┐
Function B ──┼── parallel
Function C ──┘
```

Linker sau cùng.

---

# 30. Compiler Thread Safety

Không nên dùng global mutable state.

Tránh:

```text id="ghy2po"
global SymbolTable
global TypeTable
global currentModule
```

Thay bằng:

```text id="4obq51"
CompilerSession
ModuleContext
TypeContext
```

Global immutable constants vẫn được.

---

# 31. Compiler Error Handling

Compiler phase bình thường:

```text
Result<T, Diagnostic>
```

Ví dụ:

```text id="ngn6km"
parse(source) -> Result<Ast, Diagnostic>
```

Compiler bug:

```text id="3a1hbc"
ICE
```

không dùng:

```text id="4w1fdo"
panic
```

cho expected user errors.

---

# 32. Error Recovery

Parser phải recover:

```text id="kq7t4s"
fn foo( {
    ...
}
```

và tạo diagnostic.

Không dừng compiler ngay lỗi đầu tiên nếu có thể tiếp tục.

Điều này quan trọng cho IDE.

---

# 33. Compiler Diagnostics as Data

```text id="zljg1u"
Diagnostic {
    code
    severity
    message
    primary_span
    secondary_spans
    notes
    suggestions
}
```

Compiler có thể:

```text id="pfu1l9"
render_text()
render_json()
render_jsonl()
render_lsp()
```

---

# 34. Stage-1 Compiler Modules

Khi viết bằng Axiom:

```text id="4s1jds"
compiler.ax
├── lexer
├── parser
├── syntax
├── resolver
├── types
├── traits
├── ownership
├── hir
├── mir
├── verifier
├── optimizer
├── abi
├── lir
├── machine
├── object
├── linker
└── driver
```

Mỗi module có API nhỏ.

---

# 35. Không dùng inheritance

Đây là nơi mô hình:

```text
struct + functions + traits
```

thực sự được kiểm nghiệm.

Ví dụ:

```text id="2i2w8b"
struct Lexer {
    source: view<u8>,
    pos: usize,
}
```

và:

```text id="ovl0ha"
fn next(lex: mut_view<Lexer>) -> Token
```

Method syntax:

```text id="9x4i9s"
lex.next()
```

vẫn hoạt động.

Không cần:

```text id="9s3d6u"
class Lexer : Iterator
```

---

# 36. Trait cho compiler abstractions

Ví dụ:

```text id="7e1p7k"
trait Writer {
    fn write(self: mut_view<Self>, data: view<u8>) -> Result<usize, Error>;
}
```

Implement:

```text id="6k1y8m"
impl Writer for FileWriter { ... }

impl Writer for BufferWriter { ... }
```

Static dispatch mặc định.

Compiler backend có thể monomorphize.

---

# 37. Dynamic dispatch chỉ khi compiler thực sự cần

Không nên:

```text id="p0m38k"
Box<dyn Writer>
```

mọi nơi.

Compiler biết các concrete types.

Do đó:

```text id="7ifx53"
generic static dispatch
```

là default.

Dynamic dispatch chỉ dùng khi plugin architecture hoặc runtime polymorphism thực sự cần.

---

# 38. Compiler plugin architecture

Đừng xây plugin system phức tạp trong bootstrap.

Không:

```text id="jz4j5a"
dynamic compiler plugins
```

Không:

```text id="0k9l5x"
third-party compiler passes
```

Stage-1 compiler nên có:

```text id="n0j6bc"
compiler-internal passes
```

và API ổn định sau này.

---

# 39. Comptime trong compiler

Compiler Stage-1 có thể dùng `comptime` cho:

```text id="z1u9z3"
instruction tables
target definitions
keyword tables
diagnostic metadata
```

Ví dụ:

```text id="l8i4x0"
comptime {
    generate_keyword_table(...)
}
```

Nhưng không nên phụ thuộc vào advanced procedural code generation quá sớm.

---

# 40. Machine tables

Một use case rất tốt:

```text id="1h6b6b"
comptime fn make_opcode_table(...) -> ...
```

Compiler source:

```text id="id1c4p"
instruction definitions
register definitions
ABI tables
```

có thể được generate tại compile time.

Nhưng generated code vẫn phải:

```text id="zck0qx"
typed
ownership checked
verified
```

đúng theo Axiom model.

---

# 41. Stage-1 self-hosting ladder

Đây là phần quan trọng nhất.

### S0

```text
Host compiler
    ↓
Stage-0
```

### S1

```text
Stage-0
    ↓
Stage-1.ax
    ↓
stage1
```

### S2

```text
stage1
    ↓
compile Stage-1.ax
    ↓
stage2
```

### S3

```text
stage2
    ↓
compile Stage-1.ax
    ↓
stage3
```

Ta cần:

```text
stage2 ≡ stage3
```

ở mức functional semantics.

---

# 42. Three Compiler Test

Một compiler self-hosted đáng tin cần ba lớp:

### Semantic

```text
MIR interpreter
```

### Native

```text
Axiom backend
```

### Bootstrap

```text
Stage-N compiler
```

Tức:

```text id="5tsv4u"
Source
  ↓
MIR
  ├── interpreter
  └── native backend

Compiler source
  ↓
Stage-N
  ↓
Stage-N+1
```

Ba đường kiểm chứng lẫn nhau.

---

# 43. Bootstrap Trust Chain

Cuối cùng:

```text id="j9f02m"
Stage-0
   ↓
Stage-1
   ↓
Stage-2
   ↓
Self-hosted compiler
```

Nhưng Stage-0 là binary bên ngoài.

Do đó sau này có thể thêm:

```text id="e7odc8"
reproducible bootstrap
```

để kiểm tra:

```text source
→ compiler
→ compiler
```

không bị thay đổi bất ngờ.

---

# 44. Self-hosting không phải điểm kết thúc

Sau self-host:

```text id="lfuwyt"
Axiom compiler
```

vẫn cần:

```text
better optimizer
better register allocator
AArch64
RISC-V
Windows
macOS
Android
WASM
debugger
LSP
package manager
```

Nhưng nền móng đã tự chủ.

---

# 45. Invariants

Đóng băng:

### ABOOT-41 — Self-Hosting Uses Axiom Semantics

### ABOOT-42 — Bootstrap Subset Is Axiom, Not A Separate Language

### ABOOT-43 — Stage-0 Must Preserve Final Semantic Model

### ABOOT-44 — Stage-0 Includes Ownership Semantics

### ABOOT-45 — Stage-0 Includes Capability Semantics

### ABOOT-46 — Stage-0 Produces MIR

### ABOOT-47 — Stage-0 Has MIR Verification

### ABOOT-48 — Stage-0 Has MIR Interpretation

### ABOOT-49 — Compiler Data Has Explicit Ownership

### ABOOT-50 — Compiler Does Not Require GC

### ABOOT-51 — Compiler Does Not Require Implicit RC

### ABOOT-52 — Compiler May Use Arenas

### ABOOT-53 — Arena Lifetime Is Explicit

### ABOOT-54 — Logical Compiler IDs Are Preferred Over Raw Pointers

### ABOOT-55 — Compiler Handles Are Not Memory Capabilities

### ABOOT-56 — Compiler Phases Have Explicit Data Ownership

### ABOOT-57 — Phase Boundaries Permit Data Reclamation

### ABOOT-58 — Compiler State Is Not Global Mutable State

### ABOOT-59 — Parallel Compilation Must Preserve Semantics

### ABOOT-60 — Compiler Diagnostics Are Structured Data

### ABOOT-61 — Expected Errors Are Not Compiler Panics

### ABOOT-62 — Compiler Bugs Are Distinct From User Errors

### ABOOT-63 — Compiler Can Operate Without Full Std

### ABOOT-64 — Compiler Runtime Requirements Are Minimal

### ABOOT-65 — Compiler Does Not Require Async

### ABOOT-66 — Compiler Does Not Require GPU Support

### ABOOT-67 — Compiler Does Not Require Dynamic Reflection

### ABOOT-68 — Compiler Can Use Compile-Time Generation

### ABOOT-69 — Generated Compiler Data Is Type Checked

### ABOOT-70 — Generated Code Is Re-verified

### ABOOT-71 — Stage-0 Can Compile Stage-1

### ABOOT-72 — Stage-1 Can Compile Itself

### ABOOT-73 — Self-Compilation Is Deterministic

### ABOOT-74 — Bootstrap Does Not Require External Assembler

### ABOOT-75 — Final Bootstrap Does Not Require External Linker

### ABOOT-76 — MIR Interpreter Is Independent Of Native Backend

### ABOOT-77 — Native Execution Agrees With MIR Semantics

### ABOOT-78 — Stage-N and Stage-N+1 Must Preserve Compiler Behavior

### ABOOT-79 — Bootstrap Artifacts Are Reproducible

### ABOOT-80 — Self-Hosting Does Not Change Language Semantics

---

# 46. Một kết luận quan trọng về thiết kế Axiom

Qua việc thiết kế compiler của chính nó, mô hình hiện tại cho thấy một hướng khá rõ:

```text
Axiom
```

không nên cố trở thành:

```text
Rust nhưng đơn giản hơn
```

hay:

```text
C++ nhưng an toàn hơn
```

Mà nên hướng tới:

> **Một systems language trong đó compiler thực hiện phần lớn công việc phức tạp mà programmer không cần nhìn thấy.**

Ví dụ compiler developer viết:

```text
fn lower_function(
    function: view<Function>,
    context: mut_view<LoweringContext>
) -> Result<MirFunction, Diagnostic>
```

chứ không phải:

```text
unsafe pointer
manual lifetime
reference counting
GC
```

trong toàn bộ compiler.

---

# 47. Sau BOOTSTRAP-002

Bước tiếp theo hợp lý nhất là **BOOTSTRAP-003 — Compiler Written In Axiom**, nhưng lúc đó chúng ta nên làm một việc quan trọng trước:

**thiết kế chính xác skeleton source code của compiler Axiom đầu tiên.**

Tức từ:

```text
axiom/
```

đi đến một repository thực tế:

```text
compiler/
├── lexer/
├── parser/
├── resolver/
├── types/
├── ownership/
├── hir/
├── mir/
├── verifier/
├── optimizer/
├── abi/
├── lir/
├── machine/
├── object/
├── linker/
└── driver/
```

và xác định **mỗi module chứa struct/enum/trait/function nào, dependency một chiều ra sao**, để AI agent có thể bắt đầu code mà không tự ý làm lệch kiến trúc.