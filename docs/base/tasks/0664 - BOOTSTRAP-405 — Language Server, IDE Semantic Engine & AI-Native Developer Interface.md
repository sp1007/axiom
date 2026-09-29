# BOOTSTRAP-405 — Language Server, IDE Semantic Engine & AI-Native Developer Interface

Sau `404`, bước tiếp theo nên khóa **lớp tương tác với programmer và AI agent**.

Axiom đã có một lợi thế kiến trúc rất lớn: `CompilerDB` chứa semantic graph xuyên suốt source → HIR → MIR → build → proof → machine code. Vì vậy IDE/LSP **không nên tự xây một parser/type checker riêng**.

Mục tiêu:

> **IDE, CLI và AI agent đều truy cập cùng một semantic truth do compiler cung cấp.**

---

# 1. Kiến trúc tổng thể

```text
                    Axiom CompilerDB
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
           CLI            LSP        AI Interface
             │             │             │
             ▼             ▼             ▼
         Developer       IDE/UI       AI Agent
```

Không được có:

```text
IDE parser ≠ compiler parser
IDE type checker ≠ compiler type checker
AI semantic model ≠ compiler semantic model
```

Đó là nguồn gốc của rất nhiều tooling inconsistency.

---

# 2. Axiom Language Server

Axiom cung cấp:

```text
axiom-lsp
```

hoặc language server tích hợp trực tiếp vào compiler daemon.

Các client:

```text
VS Code
JetBrains
Neovim
Emacs
custom IDE
AI coding agent
```

đều dùng cùng protocol layer.

---

# 3. Compiler daemon là semantic server

`CompilerDaemonDB` từ `402–403` trở thành nền tảng.

Daemon giữ:

```text
CompilerDB
BuildGraph
DependencyGraph
SemanticIndex
DiagnosticIndex
```

trong memory.

IDE request:

```text
hover
definition
references
completion
rename
```

không cần compile lại toàn project.

---

# 4. Incremental document model

Khi user sửa:

```text
foo.ax
```

IDE gửi incremental text update.

Compiler:

```text
TextDelta
   ↓
Incremental Parse
   ↓
Affected AST
   ↓
Affected HIR
   ↓
Affected semantic queries
```

Chỉ phần bị ảnh hưởng được invalidate.

---

# 5. Semantic queries

LSP không nên hỏi compiler bằng API kiểu:

```text
get_text_at_line_42()
```

mà bằng semantic identity:

```text
SymbolId
TypeId
FunctionId
ModuleId
ExpressionId
```

Ví dụ:

```text
hover(ExpressionId)
definition(SymbolId)
references(SymbolId)
```

---

# 6. Source ↔ Semantic Identity

Compiler phải duy trì mapping:

```text
SourceSpan
    ↕
SyntaxNodeId
    ↕
HIRNodeId
    ↕
MIRNodeId
```

Khi AST được incremental update, identity của phần không đổi nên được giữ nếu có thể.

Điều này giúp IDE không “nhảy loạn” sau mỗi lần gõ.

---

# 7. Go to definition

Ví dụ:

```axiom
foo.bar()
```

IDE hỏi:

```text
resolve `bar`
```

Compiler trả:

```text
SymbolId
DeclarationSpan
Module
Package
```

Nếu `bar` là extension method:

```text
foo.bar()
   ↓
method resolution
   ↓
extension function
```

IDE phải hiển thị đúng declaration thật.

---

# 8. Go to implementation

Với trait:

```axiom
trait Drawable {
    fn draw(self)
}
```

IDE:

```text
Go to implementations
```

trả:

```text
impl Drawable for Circle
impl Drawable for Rectangle
...
```

Compiler đã có `TraitDB`/`ImplDB`, nên không cần index bằng regex.

---

# 9. Find references

Compiler semantic graph biết chính xác symbol nào được dùng.

Do đó:

```text
find references
```

không nhầm:

```text
foo
```

với:

```text
foo_bar
```

hoặc string/comment.

---

# 10. Rename

Rename phải là semantic transformation.

```text
rename SymbolId
```

Compiler tìm toàn bộ:

```text
references
imports
re-exports
generated references
documentation references nếu policy cho phép
```

Sau đó tạo edit set.

Không dùng global text replace.

---

# 11. Completion

Completion dựa trên semantic context.

Ví dụ:

```axiom
user.
```

Compiler biết:

```text
Type(user) = User
```

→ chỉ đề xuất:

```text
fields
methods
extensions
traits
```

---

# 12. Completion phải hiểu ownership

Đây là điểm Axiom có thể vượt nhiều IDE thông thường.

Nếu:

```axiom
let x = resource
x.
```

compiler biết:

```text
x = owner
```

Nếu resource đã move:

```text
x.
```

completion có thể giải thích:

```text
value unavailable: moved into y
```

thay vì chỉ không hiện autocomplete.

---

# 13. Type information

Hover:

```text
x
```

có thể trả:

```text
User
owner
mutable
non-Copy
```

hoặc:

```text
view<User>
read capability
```

Nhưng UI mặc định không nên phơi bày toàn bộ compiler internals.

---

# 14. Inlay hints

Axiom có thể hiển thị:

```text
let user = ...
```

thành:

```text
let user: User = ...
```

hoặc:

```text
let x = foo()
       ^ i32
```

Có thể bật/tắt.

---

# 15. Ownership visualization

Đây là một tính năng nên coi là **Axiom-specific IDE feature**.

Ví dụ:

```text
x
│
├── owner
├── borrowed read → line 32
└── moved → line 40
```

Compiler có thể cung cấp ownership trace.

Programmer không phải viết lifetime annotation, nhưng IDE vẫn có thể **giải thích compiler đã suy luận gì**.

---

# 16. Capability visualization

Tương tự:

```text
view(buffer)
```

IDE có thể hiển thị:

```text
READ
region: buffer[0..1024]
valid until: call returns
```

Với:

```text
mut_view(buffer)
```

hiển thị:

```text
WRITE
exclusive
region: buffer[0..1024]
```

Đây là explanatory tooling, không phải syntax bắt buộc.

---

# 17. Effect visualization

Function:

```axiom
fn load() -> Result<Data>
```

compiler có thể biết:

```text
Effects:
    filesystem.read
    allocation
```

IDE có thể hiển thị effect summary.

---

# 18. Call hierarchy

Compiler graph:

```text
foo
 ↓
bar
 ↓
baz
```

cho phép:

```text
Call hierarchy
Incoming calls
Outgoing calls
```

với generic specialization và dynamic dispatch được phân biệt.

---

# 19. Type hierarchy

Axiom không có class inheritance.

Do đó “type hierarchy” không phải inheritance tree.

IDE hiển thị:

```text
Trait
 ├── implementation A
 ├── implementation B
 └── implementation C
```

và:

```text
Type
 ├── implemented traits
 └── extension methods
```

---

# 20. Semantic search

CLI:

```text
axiom search
```

có thể tìm:

```text
functions returning Result<T>
types implementing Trait
functions taking view<T>
unsafe blocks
allocating functions
GPU kernels
async functions
```

Ví dụ:

```text
axiom search --implements Serialize
```

---

# 21. `axiom explain`

Từ `403`, nâng cấp thành semantic explanation system.

Ví dụ:

```text
axiom explain move foo.ax:42
```

Compiler trả:

```text
x
  owner: local
  move destination: y
  move location: foo.ax:40
  attempted use: foo.ax:42
```

---

# 22. Explain type inference

```text
axiom explain type foo.ax:42
```

Có thể:

```text
expression:
    foo.bar(x)

resolved function:
    Package.Module.bar<T>

inferred:
    T = User

result:
    Result<i32>
```

Rất hữu ích cho AI.

---

# 23. Explain method resolution

Ví dụ:

```text
x.render()
```

Compiler giải thích:

```text
1. inherent method: none
2. trait candidates: 3
3. extension candidates: 2
4. selected:
   Render.render(User)
```

Nếu ambiguous:

```text
candidate A
candidate B
reason ambiguity
```

---

# 24. Explain borrow/capability conflict

Thay vì:

```text
error
```

Compiler có thể:

```text
WRITE capability requested
existing READ capability:
    foo.ax:30 → line 45

regions:
    R1 overlaps R2

therefore WRITE conflicts with READ
```

AI agent có thể sửa chính xác hơn rất nhiều.

---

# 25. AI Interface

Axiom nên có một interface riêng:

```text
Axiom Semantic API
```

Không bắt AI phải:

```text
read thousands of source files
grep
guess compiler behavior
```

AI có thể query:

```text
workspace
package
module
symbol
type
trait
implementation
dependency
build
diagnostic
proof
MIR
```

---

# 26. AI semantic query

Ví dụ:

```text
find function:
    returns Result<User>
    reads filesystem
    is async
```

Compiler query trực tiếp:

```text
FunctionQuery {
    return_type = Result<User>
    effects contains filesystem.read
    async = true
}
```

---

# 27. AI code action

AI có thể yêu cầu:

```text
generate implementation
```

Compiler cung cấp context:

```text
TraitSchema
TypeSchema
ExistingImpls
Constraints
Visibility
ABI
```

AI không cần đọc toàn repository.

---

# 28. AI patch validation

AI tạo patch:

```text
source delta
```

Compiler pipeline:

```text
Patch
 ↓
Parse
 ↓
Resolve
 ↓
Type
 ↓
Ownership
 ↓
Effects
 ↓
Tests
 ↓
Build
```

AI chỉ nhận:

```text
valid
```

hoặc structured diagnostics.

---

# 29. AI không được bypass compiler

AI interface không có quyền:

```text
disable ownership
disable type checking
inject MIR
```

trừ explicit compiler-development mode.

AI cũng không phải một “trusted compiler component”.

---

# 30. AI planning interface

Compiler có thể cung cấp dependency impact:

```text
change Symbol X
```

→

```text
affected modules
affected packages
affected artifacts
affected tests
```

AI agent có thể lập kế hoạch sửa code dựa trên graph thật.

---

# 31. Refactoring engine

Compiler semantic graph cho phép refactor:

```text
rename
move symbol
extract function
extract type
inline function
change visibility
split module
merge module
replace trait implementation
```

Không phải text transformation đơn thuần.

---

# 32. Safe refactoring

Mọi refactoring phải:

```text
precondition
→ transformation
→ semantic verification
```

Nếu transformation làm thay đổi observable semantics ngoài phạm vi được yêu cầu:

```text
reject
```

---

# 33. Code actions

LSP có thể cung cấp:

```text
Implement trait
Add missing match cases
Import symbol
Remove unused import
Fix visibility
Fix moved value
Fix capability conflict
Generate derive
```

Nhưng action phải dựa trên compiler diagnostics.

---

# 34. Missing match cases

Compiler đã có exhaustiveness proof.

Ví dụ:

```axiom
match x {
    Some(v) => ...
}
```

Compiler biết thiếu:

```text
None
```

IDE có thể tạo case tự động.

---

# 35. Import management

Compiler biết symbol provenance.

IDE có thể:

```text
Add import
Remove unused import
Merge imports
```

Không cần regex.

---

# 36. Documentation integration

Hover có thể lấy:

```text
/// documentation
```

từ semantic metadata.

Package binary interface cũng có thể chứa public docs metadata nếu được publish.

---

# 37. Source navigation across binary packages

Nếu chỉ có:

```text
foo.axiom-interface
```

IDE vẫn có thể hiển thị:

```text
type
function
trait
docs
ABI
signature
```

Nếu package cung cấp source:

```text
Go to source
```

Nếu không:

```text
Go to interface
```

---

# 38. Machine-readable semantic schema

Axiom nên định nghĩa một schema ổn định:

```text
AxiomSemanticSchema
```

Các entity:

```text
Workspace
Package
Module
Symbol
Type
Function
Trait
Impl
Field
Expression
Diagnostic
Proof
Artifact
```

Schema này có thể serialize thành JSON/binary.

---

# 39. Semantic snapshots

Compiler có thể tạo:

```text
semantic snapshot
```

Ví dụ:

```text
workspace.axs
```

chứa:

```text
package graph
symbol graph
type graph
dependency graph
diagnostics
ABI metadata
```

AI/indexer không phải reparse toàn bộ source.

---

# 40. AI context minimization

Một AI agent hỏi:

> “Tại sao function này không thể chạy trên GPU?”

Compiler có thể trả trực tiếp:

```text
GPU legality failure

function: process()
reason:
    filesystem.read
source:
    foo.ax:82

GPU kernel restrictions:
    File I/O not permitted
```

Không cần AI đọc hàng nghìn dòng source để tự suy luận.

---

# 41. Compiler explanation confidence

Không phải mọi explanation đều giống nhau.

Compiler đánh dấu:

```text
proven
derived
heuristic
optimization
```

Ví dụ:

```text
ownership conflict = proven
```

nhưng:

```text
performance warning = heuristic
```

AI không được coi heuristic như semantic fact.

---

# 42. IDE performance

LSP request phải có cancellation.

Ví dụ user đang gõ:

```text
fo
foo
foo.
foo.ba
```

request cũ phải bị cancel.

Không để 5 semantic queries chạy nối tiếp rồi trả kết quả lỗi thời.

---

# 43. Stale result detection

Mỗi request gắn:

```text
DocumentRevision
CompilerDBRevision
```

Nếu result thuộc revision cũ:

```text
discard
```

Không hiển thị diagnostic cũ trên source mới.

---

# 44. Multi-package workspace

IDE phải hiểu toàn workspace:

```text
App
 ├── Core
 ├── Network
 └── UI
```

nhưng incremental semantic loading.

Không bắt buộc load implementation của toàn bộ dependency nếu interface artifact đủ.

---

# 45. Remote development

Semantic server có thể chạy:

```text
local
remote
container
VM
```

IDE chỉ giao tiếp qua protocol.

Đây là nền tảng cho:

```text
remote build
remote compiler
GPU development machine
cross compilation server
```

---

# 46. CompilerDB additions

```text
LanguageServerDB
DocumentDB
DocumentRevisionDB
SemanticQueryDB
SemanticIndexDB
SourceSemanticMapDB

CompletionDB
HoverDB
DefinitionDB
ReferenceDB
RenameDB
CallHierarchyDB
TraitHierarchyDB
TypeHierarchyDB

CodeActionDB
RefactorDB
ImportActionDB

ExplanationDB
OwnershipExplanationDB
CapabilityExplanationDB
EffectExplanationDB
TypeInferenceExplanationDB
MethodResolutionExplanationDB
GpuLegalityExplanationDB

AISemanticDB
AISchemaDB
AIQueryDB
AICodeActionDB
AIPatchDB
AIValidationDB
AIContextDB

SemanticSnapshotDB
SemanticRevisionDB
```

---

# 47. LSP/IDE IR

Không cần tạo một IR compiler mới.

Dùng:

```text
Semantic Query IR
```

Ví dụ:

```text
QUERY_SYMBOL
QUERY_TYPE
QUERY_DEFINITION
QUERY_REFERENCES
QUERY_IMPLEMENTATIONS
QUERY_CALLERS
QUERY_CALLEES
QUERY_COMPLETION
QUERY_EXPLANATION
QUERY_EFFECT
QUERY_OWNERSHIP
QUERY_CAPABILITY
QUERY_BUILD_IMPACT
QUERY_TEST_IMPACT
```

---

# 48. Proofs

Bổ sung:

```text
SemanticQueryProof
SourceIdentityProof
IncrementalDocumentProof
CompletionValidityProof
DefinitionResolutionProof
ReferenceResolutionProof
RenameSafetyProof
RefactorSafetyProof
DiagnosticFreshnessProof
AISchemaConsistencyProof
AIPatchValidationProof
AIContextValidityProof
ExplanationConsistencyProof
OwnershipExplanationProof
CapabilityExplanationProof
EffectExplanationProof
TypeInferenceExplanationProof
GpuExplanationProof
SemanticSnapshotProof
```

---

# 49. Invariants — AIDE-01 → AIDE-30

**AIDE-01** — IDE semantic results phải dựa trên cùng CompilerDB semantics với compiler.

**AIDE-02** — LSP không được có type checker riêng tạo semantic result khác compiler.

**AIDE-03** — Semantic query phải tham chiếu stable semantic identity.

**AIDE-04** — Source/semantic mapping phải giữ provenance.

**AIDE-05** — Incremental document revision phải deterministic.

**AIDE-06** — Result của revision cũ không được áp dụng cho revision mới.

**AIDE-07** — LSP request phải có cancellation semantics.

**AIDE-08** — Completion phải phản ánh method/trait/extension resolution thực tế.

**AIDE-09** — Go-to-definition phải trả declaration semantic thật.

**AIDE-10** — Find-reference phải dựa trên symbol identity, không text matching.

**AIDE-11** — Rename phải là semantic transformation.

**AIDE-12** — Refactoring phải được compiler verification sau transformation.

**AIDE-13** — Code action không được bypass compiler safety.

**AIDE-14** — Ownership explanation phải khớp ownership proof.

**AIDE-15** — Capability explanation phải khớp capability proof.

**AIDE-16** — Effect explanation phải khớp effect analysis.

**AIDE-17** — Type explanation phải khớp type inference.

**AIDE-18** — Method-resolution explanation phải khớp resolver.

**AIDE-19** — GPU explanation phải khớp kernel legality verifier.

**AIDE-20** — Diagnostic explanation phải giữ source provenance.

**AIDE-21** — AI semantic query không được tạo semantic interpretation riêng.

**AIDE-22** — AI patch phải được compile/verify trước khi được coi là valid.

**AIDE-23** — AI interface không được bypass ownership/type/effect verification.

**AIDE-24** — AI context phải có revision identity.

**AIDE-25** — Semantic snapshot phải có compiler semantic version.

**AIDE-26** — Binary interface metadata phải đủ cho các query được công bố.

**AIDE-27** — Heuristic explanation phải được phân biệt với proven fact.

**AIDE-28** — Semantic index không được trở thành nguồn sự thật độc lập với CompilerDB.

**AIDE-29** — Refactoring không được âm thầm thay đổi observable ABI/semantics.

**AIDE-30** — CLI, IDE và AI phải quan sát cùng một semantic model.

---

# 50. Kết quả kiến trúc

Sau `405`, Axiom có một mô hình rất đáng giá:

```text
                         CompilerDB
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
      Build               Verify              Semantic
        │                    │                    │
        │                    │             ┌──────┴──────┐
        │                    │             │             │
        ▼                    ▼             ▼             ▼
    Artifact              Proofs         IDE            AI
                                              │             │
                                              └──────┬──────┘
                                                     ▼
                                             Developer / Agent
```

Điểm cốt lõi là **AI không phải một compiler thay thế**.

AI chỉ cần hỏi compiler:

```text
What is this?
Why is this invalid?
What depends on this?
What can be changed safely?
What tests are affected?
What implementation satisfies this trait?
```

và compiler trả lời bằng **semantic facts có provenance**, thay vì AI phải tự đoán từ source.

Đây sẽ là một trong những đặc điểm quan trọng nhất để Axiom trở thành ngôn ngữ **AI-native nhưng vẫn compiler-first**.