# BOOTSTRAP-312 — AXIOM LANGUAGE SERVER, IDE SEMANTIC ENGINE & INTERACTIVE COMPILER SERVICES

Sau khi Axiom đã có compiler validation và kiến trúc self-hosting, bước tiếp theo hợp lý là biến `CompilerDB` + Diagnostics + AI Interface thành **một semantic service dùng chung** cho IDE, LSP, editor, AI agent và các công cụ phân tích.

Mục tiêu không phải tạo một compiler thứ hai, mà là:

> **IDE/AI nhìn thấy chính xác cùng một semantic world mà compiler nhìn thấy.**

---

## 312.1. Kiến trúc tổng thể

```text
                         AXIOM COMPILER CORE
                                │
                         ┌──────▼──────┐
                         │ CompilerDB  │
                         └──────┬──────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
        CLI Compiler        IDE/LSP           AI Interface
             │                  │                  │
             ▼                  ▼                  ▼
        executable          editor           AI agent
```

Không được tạo:

```text
IDE Type Checker
IDE Resolver
AI Type Checker
AI Ownership Analyzer
```

riêng biệt.

Tất cả phải gọi semantic engine chung.

---

# 312.2. Language Server Core

Tạo:

```text
compiler/ide/
├── language_server/
├── semantic_service/
├── workspace/
├── completion/
├── navigation/
├── refactor/
├── symbols/
├── hover/
├── inlay/
├── diagnostics/
└── indexing/
```

API nền tảng:

```text
open_document()
change_document()
close_document()

get_diagnostics()
get_symbol()
get_type()
get_definition()
get_references()
get_signature()
get_hover()
get_completion()
get_semantic_tokens()

rename()
format()
code_actions()

explain()
```

---

# 312.3. Incremental Document Model

IDE không gửi toàn bộ project mỗi lần người dùng gõ một ký tự.

Mỗi document có:

```text
DocumentId
Version
Text
SyntaxRevision
SemanticRevision
```

Khi sửa:

```text
old text
   ↓
text edit
   ↓
new revision
```

CompilerDB invalidation chỉ ảnh hưởng những query thực sự phụ thuộc vào vùng thay đổi.

---

# 312.4. Snapshot Model

Mỗi request IDE sử dụng một compiler snapshot:

```text
CompilerSnapshot {
    revision
    workspace
    source revisions
    package revisions
    semantic state
}
```

Request:

```text
hover()
```

được thực hiện trên snapshot cụ thể.

Điều này tránh lỗi:

```text
request A đọc revision 10
request B sửa source → revision 11
request A trả kết quả dựa trên revision 11
```

---

# 312.5. Cancellation

IDE request phải cancellable.

Ví dụ:

```text
AI/IDE:
    "find all references"
```

người dùng tiếp tục gõ:

```text
"find all references..."
```

Request cũ phải bị hủy.

Compiler query phải hỗ trợ:

```text
CancellationToken
```

nhưng cancellation **không được làm hỏng CompilerDB**.

---

# 312.6. Query Architecture

Các dịch vụ IDE dùng query:

```text
parse(file)
resolve(name)
type_of(expr)
definition_at(span)
references(symbol)
public_api(module)
ownership_at(span)
capabilities_at(span)
effects_at(span)
```

Query có:

```text
input revision
dependencies
result
fingerprint
```

Nếu dependency không thay đổi → reuse.

---

# 312.7. Diagnostics Realtime

Khi người dùng gõ:

```text
let x = ...
```

compiler có thể tạm thời có syntax error.

Language server phải:

- recover;
- tạo ErrorNode;
- tiếp tục semantic analysis ở phần còn hợp lệ;
- không biến ErrorNode thành semantic fact giả.

Ví dụ:

```text
let x = foo(
let y = 10
```

vẫn có thể cung cấp:

```text
type(y)
definition(y)
completion
```

mà không cần đợi source hoàn chỉnh.

---

# 312.8. Completion Engine

Completion không chỉ là text matching.

Nó phải dựa trên semantic context:

```text
foo.
```

→ methods/fields/extensions.

```text
x::<
```

→ generic parameters.

```text
match value {
```

→ enum variants.

```text
fn f(x: impl Trait)
```

→ trait-compatible symbols.

```text
await
```

→ Future-related completions.

---

# 312.9. Method Resolution trong IDE

Do Axiom không có class inheritance và method thực chất là function với receiver đầu tiên, IDE phải hiểu:

```text
v.length()
```

có thể resolve thành:

```text
length(v)
```

Resolution order vẫn đúng semantics:

```text
1. inherent
2. trait implementation
3. imported extension
4. generic extension
```

Nếu ambiguous:

```text
AMBIGUOUS-METHOD
```

IDE phải hiển thị tất cả candidate hợp lệ.

---

# 312.10. Go-to Definition

Phải hỗ trợ:

```text
function
type
trait
impl
field
variant
module
package
constant
generic parameter
associated type
associated function
macro-like compiler-generated declaration
```

Đặc biệt generated declarations từ:

```text
@derive
comptime
```

phải giữ source provenance.

---

# 312.11. Go-to Definition của Generated Code

Ví dụ:

```text
@derive(Serialize)
struct User {
    ...
}
```

IDE có thể thấy:

```text
serialize(user)
```

nhưng definition nằm trong generated declaration.

Phải có mapping:

```text
GeneratedDeclaration
      ↓
GenerationOrigin
      ↓
SourceSpan
      ↓
Comptime/Derive invocation
```

Người dùng có thể truy ngược:

```text
generated function
→ generated source
→ @derive
→ original struct
```

---

# 312.12. Find References

Find references phải semantic, không phải grep.

Phải phân biệt:

```text
foo
```

với:

```text
foo
```

cùng tên nhưng khác declaration.

Hỗ trợ:

- local;
- field;
- method;
- trait;
- generic;
- associated item;
- import;
- re-export;
- generated code.

---

# 312.13. Rename

Rename phải thực hiện trên declaration identity.

Ví dụ:

```text
rename TypeA → TypeB
```

chỉ sửa references tới đúng `TypeId`.

Không được rename string/text không liên quan.

Rename phải cập nhật:

```text
source
imports
reexports
generated dependencies
package interfaces
tests
```

nhưng không tự ý sửa external dependency.

---

# 312.14. Semantic Hover

Hover có thể hiển thị:

```text
fn add(x: i32, y: i32) -> i32
```

nhưng có thể mở rộng:

```text
Type
Ownership
Effects
Traits
ABI
```

Ví dụ:

```text
Ownership:
    owned

Effects:
    ReadMemory
    Panic

Send:
    yes

Share:
    yes
```

Thông tin phải lấy trực tiếp từ compiler facts.

---

# 312.15. Ownership Visualization

Đây là một tính năng rất quan trọng với triết lý Axiom.

Khi hover:

```text
x
```

IDE có thể cho:

```text
Ownership:
    Owned by local x

State:
    Initialized

Capabilities:
    READ [line 20..31]

Moved:
    no

Drop:
    yes
```

Khi có lỗi:

```text
use of moved value
```

IDE có thể trực quan hóa:

```text
x
│
├── initialized
│
├── moved → foo(x)
│
└── invalid here
```

Không bắt programmer viết lifetime annotation nhưng compiler vẫn có thể **giải thích lifetime/ownership**.

---

# 312.16. Capability Visualization

Ví dụ:

```text
let a = mut_view(x.a)
let b = view(x.b)
```

IDE có thể hiển thị:

```text
a
  WRITE
  region: x.a

b
  READ
  region: x.b

relationship:
  DISJOINT
```

Nếu:

```text
mut_view(x[i])
mut_view(x[j])
```

thì:

```text
relationship:
    UNKNOWN
```

và giải thích vì sao compiler không cho phép.

---

# 312.17. Effect Visualization

Hover function:

```text
foo()
```

có thể hiển thị:

```text
Effects:
    ReadMemory
    Allocate
    Panic
```

hoặc:

```text
Effects:
    Pure
```

Effect information không được dùng để tạo một hệ thống effect khác với compiler.

---

# 312.18. Async Visualization

IDE phải hiểu Future lowering.

Ví dụ:

```text
async fn fetch() {
    let x = ...
    await foo()
    use(x)
}
```

Có thể hiển thị:

```text
Suspension Point #1

Live across await:
    x

Must satisfy:
    Future storage contract
    Send if task migrates
```

Nếu compiler báo lỗi view sống qua await:

```text
Capability cannot cross suspension
```

IDE có thể highlight chính capability và suspension point liên quan.

---

# 312.19. Trait Solver Explanation

Một tính năng quan trọng cho AI và IDE:

```text
why does T satisfy Trait?
```

Compiler trả:

```text
Trait: Display
Type: User

Proof:
    impl Display for User
```

Nếu fail:

```text
why not?
```

trả:

```text
Required:
    Display<User>

Candidates:
    impl Display for String
    impl Display for Number

No applicable implementation for User
```

Đây phải là structured explanation, không phải chỉ string.

---

# 312.20. Type Inference Explanation

Ví dụ:

```text
let x = foo(bar)
```

IDE có thể giải thích:

```text
bar : User
foo : fn(User) -> i32
x : i32
```

Nếu ambiguity:

```text
x has unresolved type variable T

Constraints:
    T: Numeric
    T: Comparable
```

AI có thể sử dụng chính dữ liệu này để giải thích cho programmer.

---

# 312.21. AI Agent Interface

AI agent không cần parse compiler output text.

Nó có thể query:

```text
get_diagnostics
get_ast
get_hir
get_type
get_symbol
get_definition
get_references
get_ownership
get_capabilities
get_effects
get_traits
get_cfg
get_mir
get_optimization
get_codegen
```

Các API này phải trả structured data.

---

# 312.22. AI Patch Validation

AI đề xuất patch:

```text
patch
```

Language server chạy:

```text
parse
resolve
type-check
ownership
capability
effect
tests
```

trước khi báo:

```text
PatchValid
```

AI không được tự tuyên bố code đúng.

Compiler là authority.

---

# 312.23. AI Explain Mode

Ví dụ AI hỏi:

```text
Why does this fail?
```

Compiler trả:

```text
DiagnosticGraph
```

AI chỉ chuyển nó thành ngôn ngữ tự nhiên.

Điều này tốt hơn việc AI tự suy luận từ source.

---

# 312.24. Semantic Code Actions

Compiler có thể đề xuất:

```text
add import
qualify symbol
change move → clone
introduce owned value
split overlapping view
await future
add explicit cast
```

Nhưng code action phải có:

```text
TextEdit
Precondition
SemanticRisk
Applicability
```

Ví dụ:

```text
Applicability:
    Safe

SemanticRisk:
    Low
```

Không tự động áp dụng transformation nếu semantic risk cao.

---

# 312.25. Refactoring Engine

Axiom refactoring phải dựa trên semantic graph:

```text
extract function
inline function
extract type
move declaration
change visibility
introduce trait
implement trait
rename
```

Không được làm bằng regex.

---

# 312.26. Semantic Tokens

IDE syntax highlighting phải phân biệt:

```text
type
function
method
trait
field
constant
variable
generic
module
macro/generated
keyword
```

và có thể thêm:

```text
owned
borrowed/view
mutable capability
unsafe
comptime
async
GPU
FFI
```

Semantic token classification phải đến từ compiler.

---

# 312.27. Unsafe Visualization

Đây là điểm đặc biệt quan trọng với Axiom.

IDE phải đánh dấu:

```text
unsafe block
unsafe fn
raw pointer
FFI boundary
unsafe capability creation
```

và cho phép:

```text
Explain safety obligations
```

Ví dụ:

```text
unsafe {
    ...
}
```

có thể hiển thị:

```text
Trusted Preconditions:
    pointer is non-null
    alignment >= align_of(T)
    region contains sizeof(T)
```

Các precondition này đến từ contract/verifier, không do IDE tự đoán.

---

# 312.28. FFI Visualization

Hover foreign function:

```text
extern "C" fn foo(...)
```

hiển thị:

```text
ABI:
    C

Ownership:
    borrowed input
    owned output

Thread safety:
    unknown / contract-defined

Allocator:
    foreign

Error:
    errno / Result / explicit contract
```

Điều này giảm đáng kể lỗi FFI.

---

# 312.29. Package Workspace Model

Language server phải hiểu:

```text
Workspace
 ├── Package A
 ├── Package B
 ├── Package C
 └── dependency packages
```

và target:

```text
Windows
Linux
macOS
Android
iOS
WASM
```

Completion/diagnostics phải phụ thuộc target đang active.

---

# 312.30. Multi-target IDE

Một source có thể:

```text
@cfg(target_os = "windows")
```

và:

```text
@cfg(target_os = "linux")
```

IDE phải cho phép chọn:

```text
Target Profile
```

Ví dụ:

```text
Target:
    x86_64-linux
```

sau đó semantic engine sử dụng đúng:

- target types;
- ABI;
- features;
- conditional declarations;
- platform libraries.

---

# 312.31. Build Integration

Language server phải dùng `BuildDB`.

Không tự tạo dependency graph khác.

```text
IDE
 │
 └── BuildDB
       ├── package graph
       ├── module graph
       ├── target
       ├── features
       └── generated files
```

---

# 312.32. Hot Reload / Fast Feedback

Không đưa hot reload vào Core language semantics.

Nếu hỗ trợ:

```text
axiom run --watch
```

nó là toolchain feature.

Flow:

```text
edit
 ↓
incremental compile
 ↓
rebuild affected units
 ↓
restart/reload according to target capability
```

Không làm thay đổi ownership hoặc runtime semantics.

---

# 312.33. Debugger Integration

Compiler phải giữ:

```text
SourceSpan
HIR
MIR
MachineInstruction
```

mapping.

Debugger có thể truy:

```text
source variable
→ MIR place
→ optimized value
→ register/stack
```

Nếu variable bị optimized away:

```text
<optimized out>
```

chứ không tạo giá trị giả.

---

# 312.34. Optimization Explanation trong IDE

Ví dụ:

```text
x * 2
```

IDE có thể hỏi:

```text
Why optimized?
```

Compiler trả:

```text
StrengthReduction
Reason:
    integer multiplication by constant 2

Preconditions:
    no overflow semantic conflict

Result:
    shift/add representation
```

Nếu không optimize:

```text
Why not vectorized?
```

có thể trả:

```text
Dependency:
    possible alias between A and B

Proof:
    DISJOINT not established
```

Điều này rất phù hợp với mục tiêu AI-friendly của Axiom.

---

# 312.35. Performance Explanation

Compiler có thể expose:

```text
allocation count
inlining
vectorization
branch optimization
register pressure
spill
cache-sensitive transformation
```

Ví dụ:

```text
foo()
```

→

```text
Inlining:
    yes

Reason:
    body size 8 instructions
    hot call site

Allocation:
    eliminated

Escape:
    NoEscape
```

---

# 312.36. Query Cost Control

IDE không được vô tình chạy expensive analysis cho mỗi keystroke.

Query classification:

```text
O(1)/local
O(file)
O(module)
O(package)
O(workspace)
O(global
```

Ví dụ:

```text
hover local variable
```

→ local.

```text
find all references
```

→ workspace.

```text
whole-program optimization explanation
```

→ global/expensive.

---

# 312.37. Background Analysis

Expensive queries có thể chạy background:

```text
foreground:
    syntax
    local type
    diagnostics

background:
    references
    whole workspace
    optimization analysis
    indexing
```

Kết quả background phải gắn với compiler revision.

Nếu revision thay đổi:

```text
stale result
```

không được hiển thị như current truth.

---

# 312.38. Indexing

Workspace index:

```text
SymbolIndex
TypeIndex
TraitIndex
ReferenceIndex
PackageIndex
```

phải dựa trên semantic IDs.

Không index bằng tên string đơn thuần.

Có thể persist index giữa sessions.

---

# 312.39. LSP

Có thể cung cấp LSP adapter:

```text
Axiom Semantic Engine
        ↓
Axiom Language Server
        ↓
LSP
        ↓
VS Code
Neovim
Zed
Emacs
IntelliJ adapter
```

LSP chỉ là protocol adapter.

Không phải semantic implementation.

---

# 312.40. Native Axiom IDE API

Ngoài LSP, Axiom nên có native API:

```text
libaxiom_ide
```

cho:

- official IDE;
- GUI;
- AI coding agent;
- compiler explorer;
- documentation tools.

Điều này tránh giới hạn của LSP.

---

# 312.41. Snapshot Serialization

Compiler semantic snapshot có thể serialize:

```text
.axsnap
```

chứa:

```text
source fingerprint
semantic fingerprint
symbol graph
type graph
diagnostics
public API
```

Dùng cho:

- remote IDE;
- distributed build;
- AI agents;
- cache;
- compiler daemon.

Không serialize machine pointers.

---

# 312.42. Compiler Daemon

Có thể có:

```text
axiomd
```

giữ:

```text
CompilerDB
PackageDB
TypeDB
Index
Cache
```

trong memory.

CLI:

```text
axiom check
```

có thể kết nối `axiomd`.

Nếu daemon chết:

```text
axiom
```

phải fallback sang standalone mode.

Daemon không được là semantic dependency.

---

# 312.43. Multi-Agent Safety

Vì Axiom hướng tới AI-friendly development, nhiều agent có thể cùng sửa workspace.

Semantic service cần:

```text
WorkspaceRevision
DocumentRevision
PatchBaseRevision
```

AI patch chỉ được áp dụng nếu:

```text
patch.base_revision == current_revision
```

hoặc có cơ chế merge semantic rõ ràng.

Không silently overwrite code của agent khác.

---

# 312.44. AI Context Minimization

Compiler không nên buộc AI đọc toàn bộ project.

AI query:

```text
"why does foo fail?"
```

có thể trả:

```text
Diagnostic
Relevant symbols
Relevant types
Relevant ownership states
Relevant source spans
Required fixes
```

thay vì hàng nghìn dòng source.

Điều này trực tiếp phục vụ mục tiêu:

> **AI hiểu project bằng semantic facts thay vì đọc toàn bộ source.**

---

# 312.45. Definition of Done

BOOTSTRAP-312 hoàn thành khi:

- `CompilerDB` có incremental document revisions;
- language server sử dụng cùng semantic engine với compiler;
- diagnostics realtime;
- completion semantic;
- go-to-definition;
- find references;
- rename;
- hover;
- semantic tokens;
- code actions;
- refactoring foundation;
- ownership visualization;
- capability visualization;
- effect explanation;
- trait solver explanation;
- async explanation;
- unsafe explanation;
- FFI explanation;
- optimization explanation;
- multi-target workspace;
- package-aware analysis;
- AI structured semantic API;
- AI patch validation;
- cancellation;
- snapshot isolation;
- compiler daemon tùy chọn;
- deterministic semantic snapshots;
- LSP adapter;
- native compiler/IDE API;
- không có semantic checker thứ hai trong IDE/AI.

---

# 312.46. Invariants

`AIDE-20` — IDE semantic results must originate from the same semantic engine as compiler validation.

`AIDE-21` — IDE must never invent semantic facts when compiler information is unavailable.

`AIDE-22` — Stale semantic results must not be presented as current.

`AIDE-23` — Cancellation must not corrupt compiler state.

`AIDE-24` — Completion and navigation must resolve declarations by semantic identity, not text matching alone.

`AIDE-25` — Rename must operate on declaration identity.

`AIDE-26` — Generated code must preserve source provenance.

`AIDE-27` — Ownership visualization must reflect compiler ownership facts exactly.

`AIDE-28` — Capability visualization must reflect compiler region/access facts exactly.

`AIDE-29` — AI-generated patches must pass normal compiler verification.

`AIDE-30` — AI tooling cannot bypass compiler verification.

`AIDE-31` — IDE target configuration must use the same target semantics as the compiler.

`AIDE-32` — IDE must not introduce a second type/trait/ownership system.

`AIDE-33` — Compiler daemon is optional and must not become a semantic dependency.

`AIDE-34` — Semantic snapshots must be revision-consistent.

`AIDE-35` — Expensive analysis must not block basic interactive editing unnecessarily.

`AIDE-36` — Optimization explanations must expose actual compiler analysis/proof facts.

`AIDE-37` — Unsafe explanations must expose established safety contracts, not invented guarantees.

`AIDE-38` — FFI information must originate from explicit ABI/FFI contracts.

`AIDE-39` — Multi-agent edits must be revision-aware.

`AIDE-40` — AI context APIs should expose minimal relevant semantic information rather than requiring whole-project source transfer.