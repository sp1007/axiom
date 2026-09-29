# BOOTSTRAP-784 — AXIDE

**Native Axiom Development Environment, Language Server, Semantic Editor Services, Incremental Parsing, Diagnostics, Symbol Navigation, Refactoring, Debug Integration, Build/Test Integration, AI Context Integration & IDE Protocol Runtime 5.0**

**Status:** FROZEN  
**Namespace:** `AXIDE`  
**ABI:** `AXIDE_ABI_1`  
**Depends on:** `AXCOMPILER`, `AXDOC`, `AXTEST`, `AXBUILD`, `AXPACKAGE`, `AXDEBUG`/debug facilities, `AXPROCESS`, `AXFILE`/`AXSTORAGE`, `AXWINDOW`, `AXDISPLAY`, `AXCOMPOSITOR`, `AXINPUT`, `AXAPPLICATION`, `AXRUNTIME`, `AXCONFIG`

---

# 1. Mục tiêu

AXIDE là **semantic development platform** của Axiom.

Nó không chỉ là một text editor và cũng không phải một GUI cụ thể.

```text
                    Axiom Source
                         │
                         ▼
                 ┌─────────────────┐
                 │     AXIDE       │
                 │                 │
                 │ Workspace       │
                 │ Documents       │
                 │ Incremental     │
                 │ Parser          │
                 │ Semantic State  │
                 │ Diagnostics    │
                 │ Navigation      │
                 │ Refactoring     │
                 │ Completion      │
                 │ Debug           │
                 │ Build/Test      │
                 │ AXDOC           │
                 │ AI Context      │
                 └────────┬────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
      AXCOMPILER       AXBUILD          AXTEST
          │               │                │
          ▼               ▼                ▼
       AXOBJECT        AXLINKER        Debug/Test
```

AXIDE phải cung cấp cùng một semantic model cho:

- IDE GUI
- CLI
- headless server
- editor integration
- automation
- AI tools
- debugger
- build system
- test system

**Nguyên tắc quan trọng:**

> GUI chỉ là frontend của AXIDE; AXIDE core phải hoạt động hoàn toàn không cần GUI.

---

# 2. Phạm vi

AXIDE sở hữu:

- workspace state
- document state
- incremental source state
- syntax tree snapshots
- semantic snapshots
- diagnostics
- symbol/navigation services
- completion
- signature help
- hover
- refactoring
- code actions
- formatting
- semantic highlighting
- project indexing
- build/test integration
- debugger integration
- profiler integration
- crash diagnostics
- AI semantic context
- IDE protocol
- session/checkpoint state
- editor task scheduling
- IDE caching

AXIDE **không sở hữu**:

- compiler semantics → `AXCOMPILER`
- compiler IR → `AXCOMPILER`
- linking → `AXLINKER`
- object representation → `AXOBJECT`
- executable format → `AXBINARY`
- package resolution → `AXPACKAGE`
- build graph authority → `AXBUILD`
- documentation semantics → `AXDOC`
- test execution authority → `AXTEST`
- OS window manager → `AXWINDOW`
- display compositor → `AXCOMPOSITOR`
- debugger engine → debugger/runtime subsystem
- AI model itself

AXIDE chỉ **điều phối và trình bày** những subsystem này.

---

# 3. Kiến trúc tổng thể

```text
┌────────────────────────────────────────────────────────────┐
│                        AXIDE UI                             │
│                                                            │
│ editor │ explorer │ terminal │ debugger │ problems │ AI    │
└──────────────────────────┬─────────────────────────────────┘
                           │
                    AXIDE Protocol
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                      AXIDE CORE                             │
│                                                            │
│ Workspace Manager                                          │
│ Document Manager                                           │
│ Incremental Parser                                         │
│ Semantic Snapshot Manager                                   │
│ Diagnostic Engine                                          │
│ Symbol Index                                               │
│ Completion Engine                                          │
│ Navigation Engine                                          │
│ Refactoring Engine                                         │
│ Formatting Engine                                          │
│ Build/Test Coordinator                                     │
│ Debug Coordinator                                          │
│ AI Context Engine                                          │
│ Cache Manager                                               │
│ Session/Checkpoint Manager                                  │
│ Task Scheduler                                              │
└──────────────┬──────────────┬──────────────┬───────────────┘
               │              │              │
        AXCOMPILER          AXBUILD        AXTEST
               │              │              │
             AXDOC         AXPACKAGE      Debug
```

---

# 4. Hai lớp bắt buộc

AXIDE được chia thành:

```text
AXIDE CORE
     │
     ├── headless
     ├── CLI
     ├── language server
     ├── AI integration
     └── editor services

AXIDE SHELL
     │
     ├── windows
     ├── tabs
     ├── panels
     ├── menus
     ├── toolbar
     ├── explorer
     └── visual editor
```

`AXIDE CORE` không được import GUI APIs.

Điều này cho phép:

```text
axiom ide
axiom ide --headless
axiom ide --server
axiom ide --check
axiom ide --index
axiom ide --symbol ...
```

hoạt động trên cùng một semantic engine.

---

# 5. Workspace Model

Workspace là đơn vị semantic lớn nhất của AXIDE.

```text
Workspace {
    id
    roots[]
    projects[]
    dependencies[]
    target_matrix[]
    active_target
    configuration
    documents[]
    semantic_snapshot
    indexes
    tasks
    session
}
```

Workspace hỗ trợ:

- single-root
- multi-root
- nested projects
- workspace dependencies
- external dependencies
- generated sources
- virtual sources
- test projects
- examples
- documentation projects

---

# 6. Project Model

```text
Project {
    id
    name
    root
    manifest
    source_roots[]
    test_roots[]
    resource_roots[]
    generated_roots[]
    dependencies[]
    targets[]
    configurations[]
}
```

AXIDE không tự định nghĩa build semantics.

Manifest được `AXBUILD`/`AXPACKAGE` xác định.

AXIDE chỉ tạo **IDE projection** của project graph.

---

# 7. Target Matrix

Một workspace có thể có:

```text
Project
 ├── Windows x86_64
 ├── Linux x86_64
 ├── Linux AArch64
 ├── macOS AArch64
 ├── iOS AArch64
 ├── Android AArch64
 └── WASM32
```

Semantic state phải có target identity.

```text
SemanticTarget {
    target
    abi
    platform
    features
    optimization
    debug_mode
}
```

Điều này đặc biệt quan trọng khi:

```text
#if target.windows
```

hoặc API platform-specific tồn tại.

---

# 8. Document Model

Document không đồng nghĩa với file.

```text
Document {
    document_id
    uri
    language
    version
    text
    encoding
    state
    source_origin
}
```

`source_origin`:

```text
FILE
UNSAVED
GENERATED
VIRTUAL
DEPENDENCY
EMBEDDED
REMOTE
```

Một buffer chưa save là **nguồn sự thật hiện tại** của editor.

Compiler không được tự động đọc file cũ từ filesystem thay thế buffer.

---

# 9. Document Lifecycle

```text
create
   ↓
open
   ↓
edit*
   ↓
semantic update
   ↓
save ───────┐
   │        │
   ▼        │
filesystem  │
   │        │
   └────────┘
   ↓
close
```

Mỗi document có monotonic version:

```text
DocumentVersion = u64
```

Mỗi edit tạo version mới.

Không được sử dụng version cũ để ghi đè state mới.

---

# 10. Text Change Model

Không gửi toàn bộ file sau mỗi ký tự.

```text
TextEdit {
    range
    replacement
}
```

Batch:

```text
DocumentChange {
    document_id
    from_version
    to_version
    edits[]
}
```

AXIDE phải hỗ trợ:

- insertion
- deletion
- replacement
- multiple edits
- UTF-8 boundary validation

---

# 11. Incremental Parsing

Đây là một trong những thành phần hiệu năng quan trọng nhất.

Không:

```text
edit 1 character
      ↓
parse entire 2 MB file
```

Mà:

```text
edit
 ↓
changed text region
 ↓
affected syntax region
 ↓
incremental reparse
 ↓
reuse unchanged syntax nodes
```

Syntax tree phải có stable identity.

```text
SyntaxNode {
    node_id
    kind
    span
    children[]
    version
}
```

Node không thay đổi phải được tái sử dụng.

---

# 12. Incremental Semantic Analysis

Parsing chỉ là tầng đầu.

```text
Text
 ↓
Incremental Lexer
 ↓
Incremental Parser
 ↓
Syntax Tree
 ↓
Name Resolution
 ↓
Type Analysis
 ↓
Trait Resolution
 ↓
Control/Data Flow
 ↓
Semantic Snapshot
```

AXIDE không được bắt AXCOMPILER phân tích lại toàn workspace cho mỗi keystroke.

Semantic dependencies được lưu:

```text
Symbol A
 ├── references B
 ├── type depends C
 └── trait depends D
```

Khi `D` thay đổi:

```text
D
 ↓
dependent semantic nodes
 ↓
affected symbols
 ↓
affected diagnostics/features
```

chỉ được tính lại phần cần thiết.

---

# 13. Semantic Snapshot

Đây là trung tâm của AXIDE.

```text
SemanticSnapshot {
    snapshot_id
    workspace_id
    document_versions[]
    compiler_version
    target
    abi
    symbol_table
    type_info
    syntax_roots[]
    diagnostics[]
    dependency_graph
    source_maps
}
```

Snapshot là immutable.

```text
Snapshot N
     │
     ├── readers đang sử dụng
     │
Snapshot N+1
     │
     └── generated asynchronously
```

Không mutate snapshot đang được editor sử dụng.

---

# 14. Snapshot Generation

```text
Document v42
    ↓
parse
    ↓
semantic delta
    ↓
Snapshot v43
```

Nếu user tiếp tục edit:

```text
v42 → v43 → v44 → v45
```

Task cũ có thể bị cancel.

Kết quả chỉ được commit nếu:

```text
result.document_versions == current_versions
```

Nếu không:

```text
STALE_RESULT
```

và bỏ kết quả.

---

# 15. Diagnostics Pipeline

```text
AXCOMPILER
     ↓
CompilerDiagnostic
     ↓
AXIDE Diagnostic Adapter
     ↓
DiagnosticStore
     ↓
Editor / Problems / CLI / AI
```

Model:

```text
Diagnostic {
    id
    severity
    code
    message
    primary_location
    related_locations[]
    source
    category
    fixes[]
    documentation
}
```

Severity:

```text
ERROR
WARNING
INFO
HINT
```

---

# 16. Diagnostic Identity

Không sử dụng text message làm identity.

```text
DiagnosticId {
    compiler_code
    symbol_id?
    source_location
    semantic_context_hash
}
```

Điều này giúp editor:

- giữ trạng thái diagnostic
- tránh flicker
- map quick fix
- theo dõi thay đổi

---

# 17. Completion

Completion phải dựa trên semantic snapshot.

```text
completion(
    document,
    position,
    trigger
) -> CompletionList
```

Entry:

```text
CompletionItem {
    label
    kind
    detail
    documentation
    insert_text
    replacement_range
    symbol_id?
    score
    availability
}
```

`score` chỉ là **internal relevance ordering**, không phải đánh giá chính trị hay nội dung người dùng; nó không được public như “quality score”.

Completion phải hỗ trợ:

- locals
- functions
- methods
- fields
- types
- traits
- modules
- imports
- enum variants
- constants
- keywords
- attributes
- generic parameters

---

# 18. Signature Help

```text
Signature {
    symbol
    parameters[]
    return_type
    documentation
}
```

Hỗ trợ:

```text
foo(
    arg1,
    arg2
)
```

AXIDE xác định:

- function
- overload
- generic specialization
- active parameter

---

# 19. Hover

Hover sử dụng:

```text
SymbolId
    ↓
semantic model
    ↓
AXDOC
    ↓
formatted semantic information
```

Ví dụ:

```text
function parse(input: Str) -> Result<Node, ParseError>
```

Có thể hiển thị:

- signature
- documentation
- type
- effects
- ownership
- allocation behavior
- panic behavior
- target availability
- source location

---

# 20. Go To Definition

```text
position
 ↓
syntax node
 ↓
SymbolId
 ↓
symbol definition
 ↓
SourceLocation
```

Không tìm bằng text matching.

---

# 21. Go To Declaration

Tách biệt với definition.

Một symbol có thể có:

```text
declaration
definition
implementation
generated_definition
foreign_definition
```

AXIDE phải giữ distinction này.

---

# 22. Find References

```text
SymbolId
 ↓
ReferenceIndex
 ↓
Reference[]
```

Reference:

```text
Reference {
    symbol_id
    source_location
    access_kind
    semantic_context
}
```

Access kind:

```text
READ
WRITE
CALL
TYPE_USE
IMPORT
IMPLEMENTATION
PATTERN
ATTRIBUTE
```

---

# 23. Symbol Index

Workspace-wide index:

```text
SymbolIndex {
    symbol_id
    qualified_name
    kind
    module
    package
    visibility
    location
    target
    signature_hash
}
```

Index được cập nhật incremental.

Không rebuild toàn bộ index sau mỗi file change.

---

# 24. Workspace Symbol Search

Hỗ trợ:

```text
exact
prefix
substring
fuzzy
qualified
module-qualified
type-qualified
```

Index phải mmap/compact được để workspace lớn không gây memory explosion.

---

# 25. Semantic Navigation

AXIDE cung cấp graph:

```text
symbol
 ├── definition
 ├── references
 ├── callers
 ├── callees
 ├── implementations
 ├── trait
 ├── derived types
 ├── documentation
 ├── tests
 └── source
```

Điều này cũng là nền tảng cho AI context.

---

# 26. Rename

Rename chỉ hoạt động trên `SymbolId`.

```text
rename(
    symbol_id,
    new_name
) -> WorkspaceEdit
```

Không được thực hiện:

```text
global text replace
```

Phải xử lý:

- references
- imports
- qualified names
- patterns
- documentation references nếu configured
- generated references
- tests
- source files

---

# 27. Safe Refactoring

Mọi refactoring phải tạo:

```text
WorkspaceEdit
```

không tự động ghi file.

```text
RefactorRequest
       ↓
analysis
       ↓
WorkspaceEdit
       ↓
preview
       ↓
apply
```

`apply` là operation explicit.

---

# 28. WorkspaceEdit

```text
WorkspaceEdit {
    edits[]
    file_operations[]
    affected_symbols[]
    diagnostics_before[]
    diagnostics_after?
}
```

Editor có thể:

- preview
- accept
- reject
- partially apply

---

# 29. Code Actions

Code action:

```text
CodeAction {
    id
    title
    kind
    diagnostics[]
    edit?
    command?
    documentation?
}
```

Ví dụ:

```text
import missing module
add explicit cast
replace deprecated API
derive trait
generate implementation
```

---

# 30. Quick Fix

Quick fix bắt buộc có:

```text
precondition
diagnostic identity
edit
postcondition
```

Ví dụ:

```text
Diagnostic D
   ↓
Fix F
   ↓
apply
   ↓
re-analyze
   ↓
verify D disappeared
```

Không được coi việc apply thành công là đồng nghĩa diagnostic đã được sửa.

---

# 31. Formatting

AXIDE gọi formatter semantic của Axiom.

```text
format_document()
format_range()
format_selection()
```

Formatter phải deterministic.

Cùng:

```text
source + configuration + formatter_version
```

→ cùng output.

---

# 32. Import Management

AXIDE hỗ trợ:

```text
add import
remove unused import
sort imports
merge imports
qualify symbol
```

Nhưng semantic legality phải do compiler xác nhận.

---

# 33. Semantic Highlighting

Syntax highlighting:

```text
lexer-based
```

Semantic highlighting:

```text
compiler-based
```

Token:

```text
SemanticToken {
    range
    token_type
    modifiers
    symbol_id?
}
```

Ví dụ:

```text
TYPE
FUNCTION
METHOD
VARIABLE
PARAMETER
FIELD
CONSTANT
MODULE
TRAIT
ENUM
MACRO
KEYWORD
```

---

# 34. Folding

Có thể fold:

- blocks
- functions
- structs
- enums
- modules
- comments
- imports
- documentation
- generated regions

Folding range phải dựa trên syntax tree.

---

# 35. Inlay Hints

Hỗ trợ:

```text
parameter names
inferred types
generic arguments
implicit conversions
trait resolution
lifetime/storage information
```

Ví dụ:

```text
calculate(/* rate: */ 10)
```

Inlay hints chỉ là presentation; không thay đổi source semantics.

---

# 36. AXDOC Integration

AXDOC là authority về documentation.

```text
AXIDE
  ↓
SymbolId
  ↓
AXDOC
  ↓
DocNode / AIDocNode
```

IDE có thể hiển thị:

- API documentation
- examples
- specification
- implementation
- tests
- ABI
- availability
- provenance

Đặc biệt:

```text
API
 ↕
SPEC
 ↕
TEST
 ↕
IMPLEMENTATION
```

được điều hướng trực tiếp.

---

# 37. AXTEST Integration

AXIDE không tự trở thành test runner.

```text
AXIDE
   ↓
AXTEST
   ↓
TestPlan
   ↓
TestExecution
   ↓
TestResult
```

IDE cung cấp:

- Run Test
- Debug Test
- Run File
- Run Module
- Run Workspace
- Run Failed
- Repeat
- Filter
- Test tree

---

# 38. AXBUILD Integration

```text
AXIDE
  ↓
BuildRequest
  ↓
AXBUILD
  ↓
BuildGraph
  ↓
AXCOMPILER / AXLINKER
  ↓
BuildResult
```

AXIDE phải hiển thị:

- progress
- diagnostics
- artifact
- dependency
- cache hit
- compile time
- link time

---

# 39. Build Cancellation

Build là cancellable task.

```text
BuildHandle {
    id
    state
    cancellation_token
}
```

Cancellation phải truyền xuống:

```text
AXIDE
 ↓
AXBUILD
 ↓
compiler
 ↓
linker
```

Không được chỉ ẩn progress UI trong khi build vẫn chạy.

---

# 40. Debug Integration

AXIDE không tự implement CPU debugger.

Nó là frontend/coordinator.

```text
AXIDE
   ↓
DebugSession
   ↓
Debugger Engine
   ↓
Process
```

Hỗ trợ:

- launch
- attach
- detach
- restart
- continue
- pause
- step into
- step over
- step out
- terminate

---

# 41. Breakpoint Model

```text
Breakpoint {
    id
    source_location
    condition?
    hit_condition?
    enabled
    verified
}
```

Breakpoint có thể được:

```text
SOURCE
FUNCTION
ADDRESS
DATA
EXCEPTION
```

tùy debugger backend.

---

# 42. Source-Level Debugging

Compiler phải tạo mapping:

```text
MachineAddress
    ↕
IRLocation
    ↕
SourceLocation
```

AXIDE sử dụng mapping để hiển thị:

```text
CPU instruction
 ↓
source line
 ↓
function
 ↓
variable
```

AXCOMPILER/AXOBJECT/AXBINARY là authority về debug metadata.

---

# 43. Variables

```text
VariableView {
    name
    type
    value
    location
    children[]
    expandable
}
```

AXIDE không giả định mọi variable tồn tại trong memory.

Compiler optimization có thể khiến:

```text
optimized_out
constant_folded
register_only
materialized
```

---

# 44. Stack

```text
StackFrame {
    id
    function
    module
    source_location
    instruction_address
    locals[]
}
```

---

# 45. Watch

Watch expression phải chạy trong debugger context.

Không tự compile/evaluate tùy tiện trong AXIDE.

```text
watch_add(expression)
watch_evaluate(frame)
```

Kết quả:

```text
VALUE
ERROR
OPTIMIZED_OUT
UNAVAILABLE
SIDE_EFFECT_BLOCKED
```

---

# 46. Profiler Integration

AXIDE có frontend cho:

- CPU profile
- allocation profile
- lock contention
- task scheduling
- async latency
- IO latency
- startup time

Không sở hữu profiler engine.

```text
AXIDE
 ↓
ProfileSession
 ↓
AXRUNTIME / profiler backend
```

---

# 47. Crash Diagnostics

Crash report:

```text
CrashReport {
    process
    target
    build_id
    timestamp
    exception
    registers
    stack
    modules
    source_mapping
    threads
    runtime_state?
}
```

AXIDE có thể:

```text
open crash report
resolve symbols
map source
show stack
show registers
locate instruction
```

Không tự gửi crash data ra Internet.

---

# 48. Terminal / Process Integration

AXIDE có process abstraction:

```text
TerminalSession {
    id
    process
    stdin
    stdout
    stderr
    environment
    working_directory
}
```

Dùng `AXPROCESS`.

Terminal không được có quyền vượt workspace trust policy.

---

# 49. File Watching

```text
FileWatchEvent {
    path
    kind
    timestamp
}
```

Events:

```text
CREATE
MODIFY
DELETE
RENAME
```

Filesystem change phải được reconcile với unsaved buffer.

---

# 50. Unsaved Buffer Conflict

Ví dụ:

```text
buffer = v10
filesystem = v9
external editor writes v11
```

AXIDE không được silently overwrite buffer.

State:

```text
EXTERNAL_CHANGE
CONFLICT
```

User/editor shell quyết định cách merge.

---

# 51. Virtual Documents

Hỗ trợ:

```text
ax://generated/...
ax://dependency/...
ax://compiler/...
ax://docs/...
ax://test/...
```

Virtual document có semantic identity riêng.

---

# 52. Background Indexing

Sau khi workspace mở:

```text
foreground:
    active document

background:
    dependency index
    symbol index
    AXDOC index
    reference index
    test discovery
```

Foreground operations luôn có priority cao hơn background indexing.

---

# 53. Scheduling

AXIDE scheduler có priority:

```text
P0  user keystroke
P1  completion/hover/navigation
P2  diagnostics current file
P3  active project analysis
P4  background workspace indexing
P5  cache maintenance
```

Không để P5 block P0.

---

# 54. Cancellation

Mọi tác vụ dài phải có:

```text
CancellationToken
Deadline?
Priority
```

Task state:

```text
QUEUED
RUNNING
CANCELLING
CANCELLED
COMPLETED
FAILED
STALE
```

---

# 55. Concurrency Model

Workspace state immutable snapshot-based.

```text
Writer
   │
   ▼
new snapshot
   │
   ├──── Reader A
   ├──── Reader B
   └──── Reader C
```

Không dùng global mutable lock cho toàn workspace.

Mục tiêu:

- nhiều readers
- minimal writer contention
- deterministic commit order

---

# 56. Cache Architecture

```text
AXIDE Cache
 ├ syntax cache
 ├ semantic cache
 ├ symbol index
 ├ reference index
 ├ completion cache
 ├ documentation cache
 ├ build projection
 ├ test discovery
 └ session cache
```

Cache key tối thiểu:

```text
source_hash
compiler_version
compiler_semantic_version
target
abi
configuration
dependency_fingerprint
```

---

# 57. Cache Correctness

Cache hit chỉ hợp lệ nếu fingerprint match.

Không:

```text
same filename → same result
```

Mà:

```text
semantic_input_fingerprint
       ==
cache_fingerprint
```

---

# 58. Memory Architecture

AXIDE phải ưu tiên:

- arena cho immutable semantic snapshots
- compact IDs thay pointer-heavy graph
- string interning
- memory mapping cho persistent indexes
- copy-on-write snapshot structures
- bounded caches

Không được giữ toàn bộ duplicate source strings cho từng snapshot.

---

# 59. Stable IDs

Các subsystem phải dùng ID thống nhất.

```text
DocumentId
FileId
ModuleId
PackageId
SymbolId
TypeId
SyntaxNodeId
DiagnosticId
TestId
BuildNodeId
DebugSessionId
```

`SymbolId` do compiler semantic layer sở hữu.

AXIDE không tự tạo semantic symbol identity thay compiler.

---

# 60. Protocol Architecture

Axiom không phụ thuộc LSP.

Native protocol:

```text
AXIDE Protocol
```

transport có thể là:

```text
IN_PROCESS
PIPE
SOCKET
STDIO
SHARED_MEMORY
REMOTE
```

Protocol message:

```text
Request
Response
Notification
Event
Cancellation
Error
```

---

# 61. Native Protocol Example

```text
Request {
    id
    method
    payload
    workspace_id?
    document_version?
}
```

Response:

```text
Response {
    id
    status
    result?
    error?
    snapshot_id?
}
```

Mọi semantic response có thể đính kèm:

```text
snapshot_id
```

để editor biết kết quả thuộc state nào.

---

# 62. JSON Compatibility

Có adapter:

```text
AXIDE Native Protocol
          ↕
JSON/JSON-RPC Adapter
          ↕
external editor
```

Nhưng:

> JSON/LSP compatibility là adapter, không phải nền tảng kiến trúc.

---

# 63. Editor Protocol Methods

Core methods:

```text
workspace/open
workspace/close
workspace/symbol
workspace/index

document/open
document/change
document/save
document/close

text/completion
text/signature
text/hover

symbol/definition
symbol/declaration
symbol/references
symbol/implementation

refactor/rename
refactor/action
text/format

debug/start
debug/attach
debug/continue
debug/pause
debug/step

build/start
build/cancel

test/discover
test/run
test/debug

docs/lookup
docs/context
```

---

# 64. AI Integration

AXIDE không chứa AI model.

```text
AXIDE
   │
   ▼
AI Context Provider
   │
   ├── AXDOC
   ├── AXCOMPILER
   ├── AXTEST
   ├── AXBUILD
   ├── source
   └── diagnostics
```

AI nhận **semantic context**, không phải toàn bộ workspace một cách mặc định.

---

# 65. AI Context Pack

```text
AIContextPack {
    task
    workspace
    target
    relevant_files[]
    relevant_symbols[]
    diagnostics[]
    documentation[]
    tests[]
    build_state
    dependencies[]
    source_ranges[]
    provenance[]
}
```

Mỗi item:

```text
ContextItem {
    id
    kind
    source
    content
    symbol_id?
    location?
    provenance
    confidence
}
```

`confidence` ở đây mô tả metadata/context provenance, không phải đánh giá con người.

---

# 66. AI Context Selection

Ví dụ user hỏi:

> sửa lỗi này

AXIDE có thể tạo:

```text
Diagnostic
 ↓
symbol
 ↓
containing function
 ↓
related types
 ↓
relevant imports
 ↓
tests
 ↓
AXDOC
 ↓
AIContextPack
```

Không gửi toàn workspace nếu không cần.

---

# 67. AI Mutation Boundary

AI **không được tự ý sửa filesystem**.

Flow bắt buộc:

```text
AI
 ↓
proposed change
 ↓
AXIDE semantic validation
 ↓
WorkspaceEdit / Patch
 ↓
preview
 ↓
explicit apply
 ↓
reparse
 ↓
diagnostic/test verification
```

Mỗi mutation phải có audit record:

```text
AIMutation {
    id
    actor
    input_context
    proposed_patch
    affected_files[]
    validation
    applied
    timestamp
}
```

---

# 68. AI Code Generation

AI có thể yêu cầu:

```text
generate implementation
generate test
generate documentation
generate migration
generate refactor
```

Nhưng AXIDE luôn chuyển thành:

```text
proposal
```

không thành hidden mutation.

---

# 69. AI Provenance

Mọi AI-generated source change phải có thể truy xuất:

```text
proposal_id
context_hash
model_identifier?
prompt/context reference
patch_hash
validation result
```

Không bắt buộc lưu prompt đầy đủ nếu policy không cho phép; nhưng patch provenance phải tồn tại.

---

# 70. Project Trust

Project có trạng thái:

```text
TRUSTED
UNTRUSTED
RESTRICTED
```

Untrusted project:

- không tự chạy build scripts
- không tự chạy tests
- không tự launch processes
- không tự load extensions
- không tự execute generated tools

Semantic parsing vẫn có thể hoạt động ở restricted mode.

---

# 71. Extension Boundary

Axiom không yêu cầu third-party extensions.

Nhưng AXIDE có extension ABI:

```text
AXIDE Extension
     ↓
Capability declaration
     ↓
AXIDE host
```

Extension phải khai báo:

```text
capabilities
permissions
ABI version
target
dependencies
```

Không được mặc định có toàn quyền filesystem/process/network.

---

# 72. Remote Development

Remote mode:

```text
LOCAL AXIDE SHELL
       │
       │ AXIDE protocol
       ▼
REMOTE AXIDE CORE
       │
       ├── compiler
       ├── build
       ├── test
       └── debugger
```

Source có thể:

- local
- remote
- hybrid

Transport không được thay đổi semantic behavior.

---

# 73. Headless Mode

```text
axiom ide --headless
```

có thể:

```text
open workspace
index
diagnose
query symbols
rename
format
build
test
debug
generate AI context
```

Không được yêu cầu GUI.

---

# 74. CLI Mode

Ví dụ:

```text
axiom ide check
axiom ide symbols Foo
axiom ide references Foo
axiom ide rename Foo Bar
axiom ide format
axiom ide index
axiom ide context Foo
```

CLI phải dùng cùng AXIDE core.

---

# 75. GUI Boundary

GUI sử dụng:

```text
AXWINDOW
AXDISPLAY
AXCOMPOSITOR
AXINPUT
AXAPPLICATION
```

Kiến trúc:

```text
AXIDE CORE
     ↑
IDE UI Controller
     ↑
Editor Widgets
     ↑
AXWINDOW / AXCOMPOSITOR
```

Không được đưa compiler semantic logic vào widget.

---

# 76. Editor Buffer Engine

Editor shell cần:

```text
Gap/Rope/Piece-table equivalent
```

nhưng AXIDE không khóa vào một cấu trúc duy nhất.

Interface:

```text
TextBuffer {
    length()
    slice()
    insert()
    delete()
    replace()
    line_map()
    offset_to_position()
    position_to_offset()
}
```

Mục tiêu là edit file lớn mà không copy toàn bộ buffer.

---

# 77. Source Mapping

AXIDE phải có hai chiều:

```text
byte offset
    ↕
UTF-8 code point
    ↕
line/column
```

Compiler có thể sử dụng byte offsets để hiệu năng cao.

UI có thể sử dụng line/column.

---

# 78. UTF-8

Axiom source mặc định UTF-8.

AXIDE phải:

- validate UTF-8
- preserve valid bytes
- report malformed input
- không nhầm byte offset với character index

Unicode identifier legality thuộc compiler.

---

# 79. Accessibility

GUI frontend phải hỗ trợ abstraction:

```text
AccessibleNode {
    role
    name
    description
    state
    actions
}
```

AXIDE core không phụ thuộc accessibility backend.

---

# 80. Session Persistence

Session:

```text
IDESession {
    workspace
    open_documents[]
    active_document
    cursor_positions[]
    selections[]
    folds[]
    panels[]
    breakpoints[]
    watches[]
    target
    configuration
}
```

Không lưu secret credentials.

---

# 81. Crash Recovery

AXIDE sử dụng journal/checkpoint:

```text
edit
 ↓
journal
 ↓
checkpoint
 ↓
session
```

Nếu IDE crash:

```text
startup
 ↓
detect incomplete session
 ↓
validate journal
 ↓
recover buffers
 ↓
present recovery state
```

Recovery phải không tự overwrite filesystem.

---

# 82. Checkpoint Model

```text
IDECheckpoint {
    id
    workspace_id
    document_versions[]
    buffer_hashes[]
    session_state
    timestamp
}
```

Checkpoint immutable.

---

# 83. Determinism

Cùng:

```text
workspace
source versions
compiler
target
configuration
```

thì semantic query phải deterministic, ngoại trừ explicit nondeterministic services.

Completion ordering phải deterministic.

Index ordering phải deterministic.

Diagnostics ordering phải deterministic.

---

# 84. Error Model

AXIDE errors:

```text
IDE_INVALID_REQUEST
IDE_WORKSPACE_NOT_FOUND
IDE_DOCUMENT_NOT_FOUND
IDE_VERSION_CONFLICT
IDE_STALE_RESULT
IDE_PARSE_FAILED
IDE_SEMANTIC_FAILED
IDE_SYMBOL_NOT_FOUND
IDE_REFERENCE_NOT_FOUND
IDE_REFACTOR_FAILED
IDE_BUILD_FAILED
IDE_TEST_FAILED
IDE_DEBUG_FAILED
IDE_PROTOCOL_ERROR
IDE_PERMISSION_DENIED
IDE_UNTRUSTED_PROJECT
IDE_RESOURCE_LIMIT
IDE_CACHE_CORRUPT
IDE_SESSION_CORRUPT
IDE_UNSUPPORTED_TARGET
```

---

# 85. Resource Limits

AXIDE phải giới hạn:

- open documents
- semantic memory
- index memory
- concurrent tasks
- completion timeout
- hover timeout
- indexing budget
- AI context size
- recovery journal size
- protocol message size

Không để một file/workspace độc hại làm IDE treo vô hạn.

---

# 86. Performance Targets

Mục tiêu thiết kế, không phải guarantee cho mọi hardware:

### Interactive

```text
keystroke → buffer update       < 1 ms
simple syntax update            < 10 ms
completion                      < 50 ms target
hover                           < 50 ms target
navigation                      < 100 ms target
current-file diagnostics        < 100 ms target
```

Nếu semantic operation lâu hơn:

```text
return partial result
continue background computation
```

không block editor.

---

# 87. Large Workspace Strategy

Workspace lớn phải:

```text
lazy load
lazy index
incremental analyze
memory-map persistent index
evict cold semantic data
```

Không bắt buộc load toàn bộ dependency semantic graph vào RAM.

---

# 88. Partial Results

Một số query có thể trả:

```text
PARTIAL
COMPLETE
STALE
```

Ví dụ completion:

```text
local symbols
      ↓
immediate result

workspace symbols
      ↓
background expansion
```

---

# 89. Semantic Degradation

Khi compiler chưa thể phân tích đầy đủ:

```text
FULL_SEMANTIC
PARTIAL_SEMANTIC
SYNTAX_ONLY
TEXT_ONLY
```

IDE vẫn phải hoạt động.

Ví dụ file đang có syntax error vẫn có:

- syntax highlighting
- folding
- basic completion
- navigation tới những symbol đã resolve
- diagnostics

---

# 90. Dependency Graph

```text
Workspace
 ↓
Package
 ↓
Module
 ↓
Source
 ↓
Symbol
```

Graph edge:

```text
IMPORTS
DEPENDS_ON
REFERENCES
IMPLEMENTS
GENERATES
TESTS
DOCUMENTS
```

Graph này dùng chung cho navigation và incremental invalidation.

---

# 91. Platform-Specific APIs

IDE phải hiển thị availability:

```text
Function foo()

available:
 Windows
 Linux

unavailable:
 WASM
```

Thông tin đến từ compiler/package/target metadata, không hard-code trong UI.

---

# 92. Generated Source

Generated source phải đánh dấu:

```text
generated = true
generator
source_dependencies[]
```

IDE mặc định không sửa trực tiếp generated source.

Nếu user yêu cầu edit:

```text
navigate_to_generator
```

nếu metadata cho phép.

---

# 93. Source ↔ Test

AXIDE có thể truy từ:

```text
function
 ↓
tests referencing function
```

và:

```text
test
 ↓
symbols under test
```

AXTEST là authority.

---

# 94. Source ↔ Documentation

```text
Symbol
 ↕
AXDOC
```

có thể:

```text
Open documentation
Generate documentation
Find undocumented public APIs
Open specification
Open tests
```

---

# 95. Build Diagnostics Mapping

Compiler/linker errors:

```text
AXCOMPILER
AXASSEMBLER
AXOBJECT
AXLINKER
AXBINARY
```

đều phải được normalize thành AXIDE diagnostic model.

Ví dụ:

```text
undefined symbol
```

có thể map tới:

- call site
- import
- dependency package

nếu backend cung cấp source provenance.

---

# 96. Protocol Versioning

```text
AXIDE_PROTOCOL_1
```

được version độc lập với:

```text
AXIDE_ABI_1
```

Protocol compatibility:

```text
major mismatch → reject
minor compatible → negotiate
```

---

# 97. ABI Boundary

Public ABI:

```text
AXIDE_ABI_1
```

bao gồm:

- opaque handles
- versioned structs
- stable enum values
- error codes
- callback ABI
- allocator boundary
- ownership rules
- thread rules

Không expose internal compiler pointer layout.

---

# 98. Native API

Core lifecycle:

```text
ide_open()
ide_close()

ide_workspace_open()
ide_workspace_close()

ide_document_open()
ide_document_change()
ide_document_save()
ide_document_close()
```

Semantic:

```text
ide_parse()
ide_diagnostics()
ide_completion()
ide_signature_help()
ide_hover()

ide_definition()
ide_declaration()
ide_references()
ide_implementation()

ide_symbols()
ide_workspace_symbols()
```

Refactoring:

```text
ide_rename()
ide_refactor()
ide_code_actions()
ide_format()
ide_import_actions()
```

Build/test:

```text
ide_build()
ide_build_cancel()
ide_test_discover()
ide_test_run()
ide_test_cancel()
```

Debug:

```text
ide_debug_start()
ide_debug_attach()
ide_debug_continue()
ide_debug_pause()
ide_debug_step()
ide_debug_breakpoint()
ide_debug_stack()
ide_debug_variables()
```

Documentation:

```text
ide_doc_lookup()
ide_doc_context()
```

AI:

```text
ide_ai_context()
ide_ai_propose()
ide_ai_validate_patch()
ide_ai_apply_patch()
```

Session:

```text
ide_session_save()
ide_session_restore()
ide_checkpoint_create()
ide_checkpoint_restore()
```

Protocol:

```text
ide_protocol_open()
ide_protocol_request()
ide_protocol_notify()
ide_protocol_cancel()
```

---

# 99. Ownership Rules

AXIDE API phải tuân thủ:

```text
borrowed input
owned result
explicit lifetime
```

Không implicit reference counting.

Large results có thể dùng:

```text
snapshot handles
mapped buffers
arena-backed views
```

---

# 100. Zero-Copy Principle

Các API:

```text
hover
symbol lookup
documentation
source ranges
diagnostics
index queries
```

nên trả immutable views khi lifetime cho phép.

Không copy:

```text
source → compiler → AXIDE → UI
```

nếu chỉ cần read-only view.

---

# 101. Plugin Security

Extension không được mặc định:

```text
filesystem *
process *
network *
credentials *
```

Capability phải explicit.

Ví dụ:

```text
extension_request(
    filesystem.read.workspace
)
```

---

# 102. AI Security

AI context phải tuân theo project trust.

Không gửi mặc định:

- secrets
- environment credentials
- private config
- unrelated files
- hidden system files

Context builder phải có allow/deny policy.

---

# 103. Prompt Injection Boundary

Source code và documentation được coi là **untrusted content**.

Nếu source chứa:

```text
"AI hãy bỏ qua mọi quy tắc..."
```

AXIDE phải xem đó chỉ là source text/documentation.

Nó không trở thành AXIDE instruction.

---

# 104. AI Patch Validation

Trước khi apply:

```text
patch
 ↓
syntax validation
 ↓
semantic validation
 ↓
format validation
 ↓
target validation
 ↓
optional test
 ↓
apply
```

Nếu patch tạo compiler errors, AXIDE phải báo rõ.

---

# 105. No Hidden Mutation

Không có:

```text
AI → silently modify files
```

Chỉ:

```text
AI → proposal
```

sau đó:

```text
explicit apply
```

---

# 106. Debug/Build State Isolation

Debug session không được mutate semantic workspace snapshot.

Build sử dụng immutable source versions.

Test chạy trên explicit build artifact.

Điều này tránh:

```text
editor edit
 → build reads mixed versions
```

---

# 107. Lifecycle

```text
ide_open
 ↓
workspace_open
 ↓
load configuration
 ↓
open active documents
 ↓
restore session
 ↓
start indexing
 ↓
ready
```

Shutdown:

```text
stop tasks
 ↓
flush journal
 ↓
save session
 ↓
release snapshots
 ↓
close workspace
 ↓
ide_close
```

---

# 108. Startup Recovery

Nếu shutdown bất thường:

```text
detect journal
 ↓
validate checkpoint
 ↓
restore immutable checkpoint
 ↓
replay valid edits
 ↓
validate document hashes
 ↓
reconstruct semantic state
```

---

# 109. Test Architecture

AXIDE phải được kiểm thử qua AXTEST.

Các nhóm:

```text
IDE unit
IDE integration
compiler integration
protocol
incremental parser
semantic snapshot
navigation
refactoring
build
test
debug
AI context
cache
recovery
security
performance
determinism
```

---

# 110. Golden Tests

Golden tests cho:

- diagnostics
- completion
- hover
- navigation
- formatting
- semantic tokens
- refactoring
- protocol responses

Golden output phải canonicalize:

- path
- timestamp
- memory address
- process ID
- machine-specific values

---

# 111. Incremental Correctness Test

Mỗi test phải có thể so sánh:

```text
incremental result
       VS
full recomputation result
```

Hai semantic snapshots phải tương đương.

Đây là một test quan trọng của AXIDE.

---

# 112. Fuzzing

Fuzz:

```text
lexer input
parser input
text edits
UTF-8
workspace graph
protocol messages
refactoring
cache files
session journal
AI patches
```

Đặc biệt:

```text
random edit sequence
```

phải không làm semantic state corrupt.

---

# 113. Protocol Fuzzing

Test:

```text
malformed request
unknown method
wrong version
oversized payload
invalid document version
cancelled request
duplicate request ID
out-of-order notification
```

Không được crash process.

---

# 114. Crash Recovery Tests

Scenario:

```text
edit
checkpoint
edit
CRASH
restart
recover
```

Expected:

```text
buffer state recoverable
filesystem untouched
semantic state rebuildable
journal consistent
```

---

# 115. Performance Tests

Measure distribution:

```text
P50
P95
P99
```

cho:

- keystroke processing
- completion
- diagnostics
- navigation
- indexing
- rename
- workspace open
- memory usage
- recovery

Không chỉ đo average.

---

# 116. Compatibility Matrix

AXIDE phải test:

```text
Windows x86_64
Windows AArch64

Linux x86_64
Linux AArch64

macOS x86_64
macOS AArch64

iOS
Android

WASM32
```

GUI có thể không tồn tại trên WASM standalone; headless/protocol mode vẫn phải hoạt động.

---

# 117. Bootstrap

Stage 0:

```text
external host
   ↓
AXIDE implementation
```

Stage 1:

```text
Axiom compiler
   ↓
AXIDE
```

Stage 2:

```text
Axiom compiler
   ↓
AXIDE
   ↓
AXIDE builds AXIDE
```

Self-hosting verification:

```text
Stage1 build
      ↓
Stage2 build
      ↓
semantic/artifact convergence
```

---

# 118. Self-Hosting Boundary

AXIDE không được yêu cầu:

```text
VS Code
Node.js
Electron
.NET
Java
third-party compiler
```

để tồn tại trong final native stack.

Có thể dùng external tooling ở Stage0/bootstrap, nhưng final architecture phải native Axiom.

---

# 119. IDE State vs Compiler State

Đây là boundary quan trọng:

```text
AXIDE state
    │
    ├── cursor
    ├── open tabs
    ├── unsaved buffers
    ├── UI state
    └── session

AXCOMPILER state
    │
    ├── syntax
    ├── semantic
    ├── type
    ├── symbols
    └── IR
```

AXIDE có snapshot reference tới compiler state, không sở hữu compiler semantics.

---

# 120. Semantic Authority Chain

```text
SOURCE
  ↓
AXCOMPILER
  ↓
SymbolId / TypeId / SemanticSnapshot
  ↓
AXIDE
  ├── navigation
  ├── completion
  ├── refactor
  ├── diagnostics
  └── AI context
```

Không tạo một semantic universe thứ hai trong IDE.

---

# 121. Performance Architecture Summary

Axiom IDE phải đạt hiệu năng nhờ:

```text
immutable snapshots
+
incremental parsing
+
incremental semantic analysis
+
stable IDs
+
dependency invalidation
+
lazy indexing
+
memory mapping
+
zero-copy views
+
priority scheduler
+
cancellation
+
parallel background work
```

Thay vì:

```text
reparse everything
retypecheck everything
reindex everything
copy everything
lock everything
```

---

# 122. 40 Invariants

### IDE-INV-01
AXIDE core không phụ thuộc GUI.

### IDE-INV-02
Unsaved document buffer là authoritative source cho document đang mở.

### IDE-INV-03
Document version tăng đơn điệu.

### IDE-INV-04
Kết quả semantic cũ không được commit lên state mới.

### IDE-INV-05
Semantic snapshot là immutable.

### IDE-INV-06
Mọi semantic query xác định snapshot tương ứng.

### IDE-INV-07
Incremental parser phải bảo toàn semantic equivalence với full parse.

### IDE-INV-08
Incremental semantic analysis phải tương đương full analysis.

### IDE-INV-09
Symbol identity không dựa trên text position.

### IDE-INV-10
Navigation dùng SymbolId.

### IDE-INV-11
Rename không được là global text replacement.

### IDE-INV-12
Refactoring phải tạo explicit WorkspaceEdit.

### IDE-INV-13
AI không được tự ý mutate filesystem.

### IDE-INV-14
AI mutation phải có provenance.

### IDE-INV-15
AXDOC là authority về documentation semantics.

### IDE-INV-16
AXTEST là authority về test execution.

### IDE-INV-17
AXBUILD là authority về build graph.

### IDE-INV-18
AXCOMPILER là authority về language semantics.

### IDE-INV-19
AXIDE không phụ thuộc LSP.

### IDE-INV-20
LSP/JSON-RPC chỉ là compatibility adapter.

### IDE-INV-21
Protocol request phải có correlation identity.

### IDE-INV-22
Task dài phải cancellable.

### IDE-INV-23
Task stale không được commit.

### IDE-INV-24
Foreground interaction có priority cao hơn background indexing.

### IDE-INV-25
Completion ordering phải deterministic.

### IDE-INV-26
Diagnostic ordering phải deterministic.

### IDE-INV-27
Index phải có fingerprint.

### IDE-INV-28
Cache hit chỉ hợp lệ khi fingerprint tương thích.

### IDE-INV-29
External filesystem changes không được silent overwrite unsaved buffers.

### IDE-INV-30
Untrusted project không được tự động execute arbitrary project code.

### IDE-INV-31
Extension capability phải explicit.

### IDE-INV-32
AI context không được tự động chứa secrets.

### IDE-INV-33
Source/documentation phải được coi là untrusted instruction content.

### IDE-INV-34
GUI không được chứa compiler semantic authority.

### IDE-INV-35
Headless mode phải dùng cùng AXIDE core.

### IDE-INV-36
Session recovery không được tự động overwrite filesystem.

### IDE-INV-37
Crash journal phải có integrity validation.

### IDE-INV-38
Incremental state phải có full-recompute verification path.

### IDE-INV-39
ABI của AXIDE phải versioned và stable trong major version.

### IDE-INV-40
AXIDE final architecture phải có thể self-host bằng Axiom.

---

# 123. Definition of Done

`BOOTSTRAP-784` chỉ được coi là hoàn thành khi có:

- [x] AXIDE core architecture
- [x] headless architecture
- [x] native protocol
- [x] optional JSON compatibility
- [x] workspace model
- [x] multi-root support
- [x] document lifecycle
- [x] unsaved buffers
- [x] virtual documents
- [x] incremental parser
- [x] semantic snapshots
- [x] incremental semantic analysis
- [x] diagnostics
- [x] completion
- [x] signature help
- [x] hover
- [x] navigation
- [x] references
- [x] rename
- [x] refactoring
- [x] code actions
- [x] formatting
- [x] semantic highlighting
- [x] folding
- [x] inlay hints
- [x] AXDOC integration
- [x] AXTEST integration
- [x] AXBUILD integration
- [x] AXPACKAGE integration
- [x] debugger integration
- [x] profiler integration
- [x] crash diagnostics
- [x] terminal/process integration
- [x] file watching
- [x] caching
- [x] background indexing
- [x] cancellation
- [x] deterministic scheduling
- [x] project trust
- [x] extension capability boundary
- [x] AI semantic context
- [x] AI patch/provenance model
- [x] explicit mutation boundary
- [x] session persistence
- [x] crash recovery
- [x] checkpointing
- [x] GUI boundary
- [x] remote development boundary
- [x] accessibility boundary
- [x] resource limits
- [x] platform matrix
- [x] AXIDE_ABI_1
- [x] 40 invariants
- [x] AXTEST conformance suite
- [x] Stage0 → Stage1 → Stage2 bootstrap path
- [x] native self-hosting target

**AXIDE 5.0 được đóng băng.**

---

# 124. Vị trí AXIDE trong Axiom

Sau AXIDE, chuỗi kiến trúc đã đạt tới một điểm rất quan trọng:

```text
                         AXDOC
                           ▲
                           │
                           │
AXCOMPILER ────────► AXIDE ◄──────── AXTEST
    │                  │
    │                  │
    ▼                  ▼
 AXOBJECT           AXBUILD
    │                  │
    ▼                  ▼
 AXLINKER          AXPACKAGE
    │
    ▼
 AXBINARY
    │
    ▼
 AXLOADER
    │
    ▼
 AXSTARTUP
    │
    ▼
 AXRUNTIME
```

AXIDE trở thành **semantic control plane của developer experience**, nhưng không chiếm quyền sở hữu của các subsystem bên dưới.

---

# BOOTSTRAP-785 — AXEDITOR

**Native Axiom Code Editor Engine, Text Buffer, Piece/Rope Storage, Cursor & Selection Model, Unicode Text Layout, Syntax/Token Rendering, Multi-Cursor Editing, Undo/Redo Transaction Engine, Search/Replace, Folding, Minimap, Viewport Virtualization & High-Performance Editor Runtime 5.0**

Đây là bước hợp lý tiếp theo: **AXIDE đã định nghĩa các dịch vụ IDE; AXEDITOR sẽ định nghĩa engine chỉnh sửa văn bản thực sự**.

Kiến trúc tiếp theo sẽ tách rõ:

```text
AXIDE
  │
  ▼
AXEDITOR
  ├── text buffer
  ├── cursor
  ├── selection
  ├── undo/redo
  ├── multi-cursor
  ├── search
  ├── folding
  ├── viewport
  └── rendering model
       │
       ▼
 AXWINDOW / AXDISPLAY / AXCOMPOSITOR
```

**Không dừng chuỗi ở đây.**