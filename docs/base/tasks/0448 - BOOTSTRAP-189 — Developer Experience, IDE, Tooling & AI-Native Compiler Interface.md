# BOOTSTRAP-189 — Developer Experience, IDE, Tooling & AI-Native Compiler Interface
## FROZEN / COMPLETED

Đây là bước chuyển từ **“compiler biết biên dịch”** sang **“compiler trở thành semantic engine của toàn bộ hệ sinh thái Axiom”**.

Quyết định quan trọng nhất:

> **Không để IDE, LSP, formatter, debugger, refactoring và AI agent tự xây các semantic model riêng. Tất cả phải dùng chung CompilerDB.**

---

# 1. Compiler là Semantic Platform

Kiến trúc:

```text
                         ┌──────────────────┐
                         │    CompilerDB     │
                         │                  │
                         │ SyntaxDB         │
                         │ TypeDB           │
                         │ TraitDB          │
                         │ HIRDB            │
                         │ MIRDB            │
                         │ DiagnosticDB     │
                         │ LayoutDB         │
                         │ AbiDB            │
                         │ BuildDB          │
                         └────────┬─────────┘
                                  │
          ┌───────────────┬───────┼────────┬──────────────┐
          ↓               ↓       ↓        ↓              ↓
        IDE/LSP         Debug   Refactor   Docs           AI
          ↓               ↓       ↓        ↓              ↓
       Editor          Debugger Formatter Analyzer     Agent
```

Không có:

```text
IDE parser
AI parser
Formatter parser
LSP parser
```

riêng biệt nếu có thể tránh.

---

# 2. Axiom Compiler API

Compiler phải expose semantic query API.

Ví dụ:

```text
parse(file)
resolve(symbol)
type_of(expr)
definition_of(symbol)
references_of(symbol)
members_of(type)
trait_impls(type)
layout_of(type)
abi_of(function)
ownership_state(place)
capabilities_at(location)
effects_of(function)
async_info(function)
gpu_info(function)
dependencies(package)
```

Những API này không chỉ dành cho IDE.

Chúng chính là **compiler's semantic interface**.

---

# 3. Query-Based Compiler

Thay vì mỗi tool yêu cầu compiler chạy lại toàn bộ pipeline:

```text
query → dependency graph → only required computation
```

Ví dụ IDE hỏi:

```text
type_of(expr_123)
```

CompilerDB chỉ tính những gì cần thiết:

```text
Syntax
 ↓
Resolution
 ↓
Type
```

không cần:

```text
MIR
↓
optimization
↓
codegen
```

---

# 4. Incremental Semantic Engine

Axiom đã có `CompilerDB` và revision model.

Cần đóng băng nguyên tắc:

```text
Source change
     ↓
invalidate dependent queries
     ↓
recompute minimal semantic region
```

Ví dụ sửa:

```text
x + y
```

không được khiến toàn project:

```text
parse
typecheck
ownership
codegen
```

lại từ đầu nếu dependency graph chứng minh không cần.

---

# 5. Stable Semantic IDs

IDE/AI không nên phụ thuộc vào line number.

Mỗi semantic object có ID:

```text
FunctionId
DeclarationId
TypeId
FieldId
TraitId
GenericInstanceId
InstructionId
```

Ví dụ:

```text
FunctionId(0x81A2...)
```

Source span chỉ là mapping:

```text
Semantic ID ↔ Source Span
```

Do đó khi code thay đổi nhẹ, tooling vẫn có thể giữ identity.

---

# 6. Language Server

Axiom LSP nên chỉ là adapter:

```text
Editor
  ↓
LSP
  ↓
CompilerDB
```

Hỗ trợ:

- completion
- hover
- go to definition
- find references
- rename
- signature help
- diagnostics
- semantic highlighting
- code actions
- document symbols
- workspace symbols
- call hierarchy
- type hierarchy qua trait relationships
- inlay hints
- formatting
- refactoring

---

# 7. Completion không dựa trên Text Search

Ví dụ:

```axiom
user.
```

Compiler biết:

```text
Type(user) = User
```

sau đó:

```text
inherent methods
trait methods
extension methods
fields
associated items
```

theo đúng **method resolution rules**.

AI không cần đoán.

---

# 8. Semantic Hover

Hover không chỉ hiển thị:

```text
fn foo(x: i32) -> i32
```

mà có thể cung cấp:

```text
Type
Ownership
Copy/Move
Effects
Send/Share
Capability requirements
ABI
Comptime status
GPU legality
```

Ví dụ conceptually:

```text
foo
────────────────────
fn foo(x: Buffer) -> Result<i32, Error>

Ownership:
    consumes x

Effects:
    Read
    Allocate

Send:
    Yes

Share:
    No
```

---

# 9. Explain API

Đây là một trong những phần quan trọng nhất của Axiom.

Compiler phải trả lời:

```text
why(type_of(x))
why(move_required(x))
why(not_copy(x))
why(view_escape_rejected)
why(alias_conflict)
why(not_send)
why(not_share)
why(await_rejected)
why(allocation_not_eliminated)
why(inline_not_applied)
why(vectorization_not_applied)
why(trait_selected)
why(overload_selected)
```

Không chỉ:

```text
error
```

mà là **proof/explanation graph**.

---

# 10. Structured Diagnostic

Diagnostic object:

```text
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message
    explanation
    semantic_context
    notes
    fixes[]
    related_symbols[]
    proof[]
}
```

Ví dụ capability conflict:

```text
ACAP-204

Cannot create mutable capability.

Reason:
    an active read capability overlaps this region.

Read capability:
    source.ax:42

Requested write:
    source.ax:43

Proven relation:
    OVERLAPS
```

---

# 11. Compiler Proof Trace

Axiom có thể expose một dạng:

```text
ax explain --proof
```

Ví dụ:

```text
mut_view(buffer)
│
├── owner = buffer
├── region = buffer[0..1024]
├── access = WRITE
│
├── existing capability:
│     view(buffer[512..2048])
│
└── region relation:
      OVERLAPS
         ↓
      conflict
         ↓
      reject
```

Đây là cách rất mạnh để debug ownership/capability.

---

# 12. AI-Native Interface

Axiom không nên thiết kế một API riêng kiểu:

```text
"ask compiler in natural language"
```

ở tầng semantic core.

Thay vào đó:

> **AI phải truy cập structured compiler facts.**

Ví dụ:

```text
ax query type_of expr_123
```

trả:

```text
{
  "type": "Vec<f32>",
  "copy": false,
  "drop": true,
  "send": true,
  "share": false
}
```

AI có thể tự giải thích cho programmer.

---

# 13. AI Explainability

Compiler có thể trả:

```text
reason:
  MOVED_VALUE

source:
  foo(buffer)

ownership:
  buffer -> MOVED

later_use:
  buffer.len()

fixes:
  - clone before move
  - pass a view
  - change parameter ownership
```

AI không cần reverse-engineer compiler.

---

# 14. AI không được sửa Semantic Rules

AI interface **không có quyền**:

```text
disable ownership
disable verifier
assume aliasing
mark unsafe automatically
change compiler semantics
```

AI chỉ:

```text
query
suggest
generate
refactor
```

Compiler vẫn là authority.

```text
AI
 ↓
proposal
 ↓
Compiler
 ↓
verify
 ↓
accept/reject
```

---

# 15. Machine-Readable Compiler Protocol

Axiom nên có một protocol ổn định:

```text
AXCP — Axiom Compiler Protocol
```

Các nhóm request:

```text
syntax/*
semantic/*
type/*
trait/*
ownership/*
capability/*
effect/*
async/*
gpu/*
abi/*
layout/*
build/*
optimization/*
diagnostic/*
refactor/*
```

Có thể transport qua:

```text
stdio
Unix socket
named pipe
TCP/local IPC
```

nhưng protocol semantic độc lập transport.

---

# 16. Refactoring Engine

Refactoring phải dùng semantic identity.

Không được làm kiểu:

```text
replace "foo" → "bar"
```

mù.

Ví dụ Rename:

```text
DeclarationId(Function42)
```

Compiler tìm:

```text
all semantic references
```

sau đó sửa đúng symbol.

Điều này tránh đổi nhầm:

```text
foo()
```

trong comment/string/namespace khác.

---

# 17. Safe Automated Refactoring

Compiler có thể cung cấp:

```text
extract function
inline function
introduce variable
change parameter
change return type
move declaration
rename
convert loop ↔ iterator
convert match
derive trait
generate impl
```

Nhưng sau mỗi transformation:

```text
Generated Source
      ↓
CompilerDB
      ↓
Full semantic verification
```

Không tin transformation engine một cách mù quáng.

---

# 18. Formatter

Formatter nên hoạt động trên **lossless syntax tree** đã có từ BOOTSTRAP-126.

Không format bằng AST đã mất trivia.

Giữ:

```text
comments
whitespace-sensitive information
doc comments
attributes
```

Nhưng formatter vẫn phải parse bằng compiler frontend chính.

---

# 19. Documentation Generator

CompilerDB đã biết:

```text
modules
functions
types
traits
fields
visibility
generic constraints
effects
examples
```

Do đó:

```text
ax doc
```

có thể tạo documentation trực tiếp từ semantic model.

Không cần parser riêng.

---

# 20. Debugger Integration

Debug information phải map:

```text
Source
 ↔
HIR
 ↔
MIR
 ↔
Machine Code
```

đã được thiết kế ở các tầng trước.

Debugger có thể hiển thị:

```text
variable x
type
value
ownership state
capabilities
source location
```

Ví dụ:

```text
x: Buffer
state: Owned
storage: dynamic
len: 4096
capabilities: none
```

Các trạng thái compiler-internal có thể chỉ xuất hiện trong developer/debug mode.

---

# 21. Optimization Explorer

Một tính năng rất phù hợp với mục tiêu performance của Axiom:

```text
ax inspect optimize foo
```

Ví dụ:

```text
foo
├── inlined: yes
├── allocation eliminated: yes
├── bounds checks removed: 4
├── vectorized: yes
├── specialization: Vec<f32>
├── devirtualization: yes
└── estimated hot loop: 1
```

Nếu vectorization thất bại:

```text
vectorized: no

reason:
    loop-carried dependency

dependency:
    store(out[i])
    load(out[i-1])
```

Đây là **optimization transparency**, không phải thay đổi semantics.

---

# 22. Allocation Explorer

Do Axiom đặc biệt chú trọng hiệu năng:

```text
ax inspect alloc foo
```

có thể cho:

```text
Allocation #1
    type: Buffer
    origin: line 24
    escape: ReturnEscape
    eliminated: no

Allocation #2
    type: Temp
    escape: NoEscape
    scalar-replaced: yes
```

Điều này giúp programmer hiểu compiler mà không phải viết memory-management code thủ công.

---

# 23. Capability Explorer

Tương tự:

```text
ax inspect capability function_name
```

cho:

```text
Capability C17
    source: buffer
    region: [0, 1024]
    access: READ
    lifetime: line 20 → line 31
```

Rất hữu ích khi compiler báo:

```text
cannot mutate buffer
```

---

# 24. Dependency Explorer

Tích hợp trực tiếp với BOOTSTRAP-187:

```text
ax why package
ax tree
ax why symbol
ax why runtime
```

Ví dụ:

```text
ax why runtime::async
```

trả:

```text
main
 ↓
http::Client
 ↓
async::TcpStream
 ↓
executor
```

Và:

```text
ax why runtime::gc
```

có thể trả:

```text
No dependency.
```

Điều này hỗ trợ mục tiêu binary nhỏ.

---

# 25. Profile-Aware IDE

IDE có thể biết profile:

```text
debug
release
size
freestanding
gpu
```

Ví dụ một API chỉ tồn tại dưới:

```text
@cfg(target_os = "windows")
```

completion phải hiểu configuration hiện tại.

Không hiển thị API không hợp lệ cho target/profile hiện tại.

---

# 26. Semantic Search

Axiom có thể cung cấp:

```text
ax query
```

không chỉ search text.

Ví dụ:

```text
find all functions:
    taking Buffer
    returning Result
    effect = IO
```

hoặc:

```text
find all types:
    Drop
    Send
    !Share
```

Đây là semantic database, rất hữu ích cho AI agent.

---

# 27. AI Agent Workflow

Một agent Axiom lý tưởng:

```text
Read task
   ↓
Query CompilerDB
   ↓
Inspect relevant symbols
   ↓
Modify source
   ↓
ax check
   ↓
Read structured diagnostics
   ↓
Fix
   ↓
ax test
   ↓
ax inspect optimize
   ↓
Commit
```

Agent **không cần đọc hàng nghìn file để đoán architecture** nếu compiler/build database đã cung cấp facts.

---

# 28. Compiler Context Bundle

Có thể tạo:

```text
ax context <symbol>
```

Output gồm:

```text
symbol definition
type
dependencies
callers
callees
traits
ownership
effects
ABI
target constraints
tests
diagnostics
optimization status
```

AI agent có thể yêu cầu context chính xác thay vì toàn project.

Đây là một cách giảm đáng kể token và hallucination.

---

# 29. Semantic Snapshot

CompilerDB có thể serialize một snapshot:

```text
.axdb
```

chứa dữ liệu semantic/incremental phù hợp.

Mục đích:

- IDE startup nhanh
- CI incremental
- AI context
- cross-process compiler tools
- indexing
- navigation

Không phải runtime artifact.

---

# 30. Tooling không làm phình Runtime

Tất cả:

```text
LSP
debug metadata
.axmeta
.axdb
AI protocol
documentation
profiling
compiler diagnostics
```

đều thuộc **toolchain**, không thuộc runtime của application.

Vì vậy một chương trình:

```axiom
fn main() {
    print("hello")
}
```

không tự nhiên kéo theo:

```text
LSP
reflection
AI
debugger
metadata
async
GC
```

---

# 31. CLI Architecture

CLI chính:

```text
ax
├── init
├── build
├── run
├── check
├── test
├── fmt
├── doc
├── clean
├── fetch
├── update
├── tree
├── vendor
├── package
├── publish
├── inspect
├── query
├── explain
└── lsp
```

Compiler primitive:

```text
axc
```

có thể vẫn tồn tại cho low-level/compiler development.

---

# 32. `ax inspect` — thống nhất tooling

Thay vì tạo hàng chục command:

```text
ax inspect type Foo
ax inspect mir foo
ax inspect abi foo
ax inspect layout Foo
ax inspect ownership foo
ax inspect capability foo
ax inspect effects foo
ax inspect optimize foo
ax inspect alloc foo
```

Một semantic inspection framework thống nhất.

---

# 33. Human vs AI Interface

Một điểm quan trọng:

### Human

```text
ax explain foo
```

→ readable output.

### AI

```text
ax query --format=json ...
```

→ structured output.

Không nên bắt AI parse text terminal.

---

# 34. Schema Versioning

Protocol machine-readable phải version:

```text
AXCP v1
```

và:

```text
schema_version
compiler_semantic_version
target
profile
```

AI/tooling có thể biết schema nào đang sử dụng.

Compiler có thể thêm field mà không phá client cũ.

---

# 35. Security Boundary

AI/compiler tooling không được tự động có quyền:

```text
filesystem write
network
execute arbitrary process
modify compiler
```

Build/comptime capabilities đã có model riêng.

AI tool permissions cũng phải explicit.

Ví dụ:

```text
ax ai --allow-edit
ax ai --allow-test
ax ai --allow-build
```

là tooling policy, không phải language semantics.

---

# 36. Final Architecture

Sau BOOTSTRAP-189:

```text
                    AXIOM COMPILER
                         │
                   ┌─────┴─────┐
                   │ CompilerDB │
                   └─────┬─────┘
                         │
       ┌─────────────────┼─────────────────┐
       ↓                 ↓                 ↓
   Semantic          Verification      Build Graph
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                  Semantic Query API
                         │
       ┌──────────┬──────┼──────┬──────────┐
       ↓          ↓      ↓      ↓          ↓
      IDE        LSP    Debug  Refactor    AI
       │          │      │      │          │
       └──────────┴──────┼──────┴──────────┘
                         ↓
                  Human / AI Developer
```

Đây chính là điểm Axiom có một lợi thế kiến trúc rất lớn:

> **AI không cần hiểu compiler bằng cách đọc source compiler; AI có thể hỏi compiler trực tiếp về semantic facts.**

---

# Invariants mới — FROZEN

### `ATOOL-20`
CompilerDB là semantic authority chung cho compiler và tooling.

### `ATOOL-21`
IDE/LSP/tooling không được duy trì semantic model mâu thuẫn với compiler.

### `ATOOL-22`
Semantic objects có identity ổn định trong phạm vi compiler database.

### `ATOOL-23`
Incremental queries chỉ invalidate các dependency liên quan.

### `ATOOL-24`
Semantic query không yêu cầu code generation nếu query không cần.

### `ATOOL-25`
Structured diagnostics có stable semantic codes.

### `ATOOL-26`
Compiler có thể giải thích các quyết định semantic quan trọng bằng structured facts.

### `ATOOL-27`
AI interface chỉ đề xuất/thay đổi source; compiler vẫn là authority xác minh.

### `ATOOL-28`
AI không được bypass ownership, capability, type, concurrency hoặc safety verifier.

### `ATOOL-29`
Automated refactoring phải được compiler re-verify.

### `ATOOL-30`
Formatter sử dụng lossless syntax representation.

### `ATOOL-31`
Debugger duy trì mapping Source ↔ HIR ↔ MIR ↔ Machine Code.

### `ATOOL-32`
Optimization explanations không thay đổi optimization semantics.

### `ATOOL-33`
Tooling metadata không trở thành runtime dependency mặc định.

### `ATOOL-34`
Machine-readable compiler protocol phải versioned.

### `ATOOL-35`
AI/tooling context có thể được lấy theo semantic scope thay vì toàn bộ source tree.

### `ATOOL-36`
Compiler inspection phải có thể phân biệt semantic facts với optimization decisions.

### `ATOOL-37`
Tooling permissions không thay đổi language semantics.

### `ATOOL-38`
Compiler query results phải phản ánh cùng semantic rules được production compiler sử dụng.

### `ATOOL-39`
`.axmeta`/`.axdb`/debug information là tooling artifacts, không phải runtime requirements mặc định.

### `ATOOL-40`
Axiom tooling phải có thể hoạt động trên source chưa hoàn chỉnh với diagnostics có cấu trúc.

---

# Trạng thái

**BOOTSTRAP-189 — FROZEN / COMPLETED**

Đến đây Axiom đã có một vòng khá hoàn chỉnh:

```text
Language
 → Type System
 → Ownership
 → Memory
 → Capability
 → Concurrency
 → Async
 → GPU
 → Comptime
 → Reflection
 → IR
 → Verification
 → Optimization
 → ABI
 → Backend
 → Runtime
 → OS
 → Package/Build
 → Conformance
 → Compiler Correctness
 → IDE/Tooling
 → AI Compiler Interface
```

## BOOTSTRAP-190 — Security, Sandboxing, Supply Chain & Trust Model

Bước tiếp theo nên giải quyết một vấn đề còn rất lớn: **Axiom đã có package manager, comptime, FFI, unsafe, dynamic loading, plugins, external build capabilities và AI tooling — vậy ranh giới tin cậy nằm ở đâu?**

Sẽ thiết kế:

```text
Safe Axiom
   │
   ├── unsafe
   ├── FFI
   ├── comptime capabilities
   ├── external tools
   ├── packages
   ├── dynamic libraries
   ├── plugins
   ├── build scripts
   └── AI agents
```

và một **Axiom Trust/Security Model** thống nhất, nhưng không biến Axiom thành một ngôn ngữ quá nặng về security ceremony.