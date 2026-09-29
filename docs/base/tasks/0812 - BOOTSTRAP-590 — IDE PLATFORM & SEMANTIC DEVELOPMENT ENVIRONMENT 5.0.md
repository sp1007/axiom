# BOOTSTRAP-590 — IDE PLATFORM & SEMANTIC DEVELOPMENT ENVIRONMENT 5.0
## EDITOR, PROJECT MODEL, SEMANTIC INDEX, LSP, DEBUGGER INTEGRATION, BUILD GRAPH, REFACTORING, CODE ACTIONS, PROFILING, TESTING, VISUAL UI & AI-NATIVE DEVELOPMENT WORKSPACE

**Trạng thái: COMPLETED / LOCKED**

`590` hợp nhất các hệ thống đã xây trước đó thành một môi trường phát triển thống nhất.

Nguyên tắc quan trọng:

> **IDE không được tự xây một semantic engine thứ hai.**

Compiler query engine, semantic database, build graph, debugger, profiler, test engine và AI interface phải chia sẻ cùng một nguồn semantic truth.

```text
                         AXIOM IDE
                            │
                 ┌──────────┴──────────┐
                 │ Unified Workspace   │
                 └──────────┬──────────┘
                            │
                  ┌─────────▼─────────┐
                  │ Semantic Database │
                  └─────────┬─────────┘
                            │
       ┌────────────┬───────┼────────┬─────────────┐
       ▼            ▼       ▼        ▼             ▼
     Editor       LSP    Build     Debugger      AI
       │            │       │        │             │
       └────────────┴───────┴────────┴─────────────┘
                            │
                     Compiler Pipeline
                            │
                     Native Artifact
```

---

# 590.1. IDE architecture

IDE gồm:

```text
IDE Shell
├── Workspace
├── Editor
├── Project Explorer
├── Semantic Services
├── Build Services
├── Test Services
├── Debug Services
├── Profile Services
├── Terminal
├── Diagnostics
├── Refactoring
├── Package/SDK Manager
└── AI Integration
```

---

# 590.2. IDE không phải compiler frontend thứ hai

IDE sử dụng compiler semantic infrastructure từ `436`, `559`, `570`.

Không được có:

```text
IDE parser ≠ Compiler parser
IDE type checker ≠ Compiler type checker
```

---

# 590.3. Unified semantic database

Semantic DB là nguồn dữ liệu chung:

```text
SemanticDB
├── files
├── modules
├── symbols
├── types
├── traits
├── references
├── call graph
├── CFG
├── diagnostics
├── source maps
├── build state
└── dependency graph
```

---

# 590.4. Workspace

Workspace chứa một hoặc nhiều project:

```text
Workspace
├── Project A
├── Project B
└── Shared Packages
```

---

# 590.5. Workspace identity

Workspace có:

```text
workspace_id
root
projects
toolchain
target
configuration
```

---

# 590.6. Project model

Project model lấy thông tin từ manifest `432` và build graph `487`.

---

# 590.7. Project discovery

IDE tự phát hiện project dựa trên:

```text
axiom.toml
workspace.toml
```

hoặc canonical project manifest tương lai.

---

# 590.8. Multi-project workspace

Một workspace có thể chứa:

```text
application
library
test
tool
plugin
benchmark
```

---

# 590.9. Virtual project

IDE có thể mở source tree chưa có project manifest để hỗ trợ browsing.

---

# 590.10. Target context

Mỗi editor semantic context phải biết:

```text
target
toolchain
profile
features
SDK
```

---

# 590.11. Multi-target workspace

Một project có thể simultaneously có:

```text
Windows
Linux
Android
WASM
```

semantic contexts.

---

# 590.12. Target switching

Đổi target phải invalidate những query phụ thuộc target nhưng giữ lại source-independent information.

---

# 590.13. Configuration profiles

IDE hỗ trợ:

```text
debug
release
test
bench
custom
```

---

# 590.14. Editor architecture

Editor gồm:

```text
Document Model
    ↓
Text Buffer
    ↓
Syntax Layer
    ↓
Semantic Layer
    ↓
Presentation Layer
```

---

# 590.15. Rope/piece table

Text editor phải dùng cấu trúc dữ liệu phù hợp với file lớn.

Không được thiết kế dựa trên việc copy toàn bộ string sau mỗi keystroke.

---

# 590.16. UTF-8

Source editor native encoding là UTF-8 theo `429`.

---

# 590.17. Unicode positions

IDE phải distinguish:

```text
byte offset
code point offset
grapheme position
line/column
```

---

# 590.18. Canonical source position

Compiler APIs sử dụng byte offset nội bộ.

IDE presentation có thể dùng line/column/grapheme.

---

# 590.19. Incremental editing

Mỗi thay đổi chỉ invalidate vùng liên quan.

```text
Edit
 ↓
Changed Range
 ↓
Incremental Lexer
 ↓
Incremental Parser
 ↓
Affected Queries
```

---

# 590.20. Semantic latency target

Editor operation thông thường phải ưu tiên phản hồi incremental thay vì chờ full build.

---

# 590.21. Cancellation

Mọi long-running IDE query phải có cancellation.

---

# 590.22. Stale result

Query cũ không được overwrite semantic state mới hơn.

---

# 590.23. Snapshot model

Mỗi IDE request gắn với semantic snapshot:

```text
Snapshot {
    revision
    semantic_db
    configuration
}
```

---

# 590.24. Snapshot isolation

Một response chỉ được commit nếu snapshot còn hợp lệ.

---

# 590.25. Diagnostics

IDE nhận diagnostics trực tiếp từ compiler diagnostic engine `569`.

---

# 590.26. Diagnostic categories

```text
error
warning
note
hint
info
```

---

# 590.27. Diagnostic identity

Mỗi diagnostic có stable ID để IDE không nhấp nháy khi refresh.

---

# 590.28. Fix-it

Diagnostic có thể chứa:

```text
replacement
insert
delete
multi-edit
```

---

# 590.29. Code actions

IDE biến fix-it thành action:

```text
Apply Fix
```

---

# 590.30. Safe vs unsafe actions

Code action phải phân biệt:

```text
semantic-safe
behavior-changing
potentially-destructive
```

---

# 590.31. Completion engine

Completion sử dụng semantic DB:

```text
prefix
 ↓
scope
 ↓
symbols
 ↓
types
 ↓
traits
 ↓
ranking
```

---

# 590.32. Completion sources

Có thể đề xuất:

```text
local variable
parameter
field
method
function
type
module
trait
package
keyword
```

---

# 590.33. Type-aware completion

Ví dụ:

```text
foo.
```

chỉ đề xuất members phù hợp với type của `foo`.

---

# 590.34. Trait completion

Nếu trait cung cấp method cho type, completion phải nhận diện extension/trait methods.

---

# 590.35. Generic completion

Completion phải preserve generic constraints.

---

# 590.36. Signature help

Khi gọi:

```text
foo(
```

IDE hiển thị:

```text
foo<T>(x: T, y: T) -> Result<T>
```

---

# 590.37. Parameter selection

Current argument được highlight.

---

# 590.38. Hover

Hover có thể hiển thị:

```text
type
documentation
trait implementations
source
ABI
```

---

# 590.39. Go to definition

Navigation tới semantic declaration.

---

# 590.40. Go to implementation

Đối với trait:

```text
trait
 ↓
implementations
```

---

# 590.41. Go to type definition

Từ variable/member tới type declaration.

---

# 590.42. Find references

Compiler semantic graph cung cấp reference set.

---

# 590.43. Reference accuracy

Không được dùng text search làm nguồn chính cho semantic references.

Text search chỉ là fallback.

---

# 590.44. Call hierarchy

Hỗ trợ:

```text
callers
callees
```

---

# 590.45. Type hierarchy

Axiom không có class inheritance nhưng IDE vẫn hiển thị:

```text
trait
 ├── implementor A
 ├── implementor B
 └── implementor C
```

---

# 590.46. Symbol hierarchy

```text
module
 └── type
      ├── field
      └── function
```

---

# 590.47. Rename

Rename phải dựa trên symbol identity.

---

# 590.48. Rename safety

Rename phải preview toàn bộ affected files trước khi commit.

---

# 590.49. Cross-package rename

Có thể rename public API nếu dependency graph cho phép.

---

# 590.50. Rename collision detection

IDE phải phát hiện:

```text
scope collision
import collision
overload ambiguity
trait ambiguity
```

---

# 590.51. Extract function

Có thể extract:

```text
statements
expression
```

thành function.

---

# 590.52. Extract variable

Có thể extract expression thành local.

---

# 590.53. Inline variable

Có thể inline local nếu semantic analysis chứng minh an toàn.

---

# 590.54. Inline function

Refactoring phải phân biệt:

```text
source-level inline
compiler optimization inline
```

---

# 590.55. Change signature

IDE có thể thay đổi parameter và cập nhật call sites.

---

# 590.56. Move symbol

Có thể move function/type giữa modules.

---

# 590.57. Import organizer

IDE tự:

```text
add import
remove unused import
sort import
merge import
```

---

# 590.58. Refactoring transaction

Mỗi refactor là transaction:

```text
Analyze
 ↓
Preview
 ↓
Validate
 ↓
Apply
 ↓
Re-index
```

---

# 590.59. Refactoring rollback

Nếu validation fail, workspace không được ở trạng thái partial.

---

# 590.60. Formatting

IDE gọi formatter `434`.

Không có formatter riêng.

---

# 590.61. Format-on-save

Có thể bật:

```text
format_on_save = true
```

---

# 590.62. Formatting range

Formatter hỗ trợ range formatting khi semantic constraints cho phép.

---

# 590.63. Semantic highlighting

Syntax highlighting:

```text
keyword
string
number
comment
```

Semantic highlighting bổ sung:

```text
type
function
parameter
field
trait
constant
mutable variable
```

---

# 590.64. Semantic color categories

Theme API phải phân biệt token categories, nhưng không hardcode màu.

---

# 590.65. Inlay hints

IDE có thể hiển thị:

```text
x: Int32
T = Float64
return type
parameter names
```

---

# 590.66. Inlay hint policy

Không được biến source thành biển thông tin.

Có cấu hình:

```text
off
minimal
normal
verbose
```

---

# 590.67. Type inference visualization

Có thể inspect inferred type mà không cần sửa source.

---

# 590.68. Ownership visualization

IDE có thể hiển thị:

```text
moved
borrowed
owned
dropped
```

từ semantic metadata.

---

# 590.69. Async visualization

IDE có thể hiển thị:

```text
async function
await points
task boundary
executor
```

---

# 590.70. Error propagation visualization

Có thể trace:

```text
Result<T,E>
 ↓
?
 ↓
caller
 ↓
caller
```

---

# 590.71. Build integration

IDE không tự build bằng shell command tùy tiện.

Nó gọi Build Engine `487/568`.

---

# 590.72. Build graph view

Hiển thị:

```text
App
├── Core
├── Graphics
├── Network
└── Platform
```

---

# 590.73. Build task

Build task có:

```text
source inputs
dependencies
toolchain
target
configuration
outputs
```

---

# 590.74. Incremental build

IDE nhận incremental result từ compiler daemon `555`.

---

# 590.75. Build cancellation

User có thể cancel build mà không corrupt cache.

---

# 590.76. Build progress

Progress phải dựa trên actual DAG state, không phải phần trăm giả định.

---

# 590.77. Build diagnostics

Diagnostic links tới:

```text
file
line
symbol
build action
```

---

# 590.78. Test integration

IDE sử dụng test framework `435`.

---

# 590.79. Test discovery

Semantic DB có thể discover:

```text
#[test]
```

hoặc canonical Axiom test declaration.

---

# 590.80. Test tree

```text
Tests
├── unit
├── integration
├── compile
├── runtime
└── benchmark
```

---

# 590.81. Test execution

Có thể:

```text
run test
run package tests
run workspace tests
run failed tests
```

---

# 590.82. Test filtering

Filter theo:

```text
name
module
tag
package
```

---

# 590.83. Test output

IDE phải parse structured test events thay vì screen-scraping terminal output.

---

# 590.84. Test diagnostics

Failure phải map về source assertion.

---

# 590.85. Benchmark integration

IDE có thể chạy benchmark và hiển thị:

```text
time
throughput
allocations
binary size
```

---

# 590.86. Regression detection

Benchmark engine `450/476` cung cấp baseline.

---

# 590.87. Debugger integration

Debugger `589` là first-class service.

---

# 590.88. Debug launch

IDE tạo DebugSession từ Build artifact identity.

---

# 590.89. Debug configuration

```text
DebugConfig {
    program
    arguments
    environment
    working_directory
    target
    breakpoints
}
```

---

# 590.90. Breakpoint editor

Breakpoint được lưu semantic:

```text
file
line
symbol
condition
```

không chỉ lưu address.

---

# 590.91. Breakpoint relocation

Khi rebuild, IDE tự resolve breakpoint về binary mới.

---

# 590.92. Debug source synchronization

Editor highlight current instruction:

```text
source line
 ↓
machine location
```

---

# 590.93. Debug variable panel

Có:

```text
Locals
Arguments
Globals
Watch
Registers
```

---

# 590.94. Debug expression

IDE sử dụng Debug Expression Engine `589`.

---

# 590.95. Memory viewer

Memory viewer có:

```text
hex
ASCII/UTF-8
typed view
```

---

# 590.96. Disassembly view

Disassembly phải đồng bộ:

```text
source
machine instruction
register state
```

---

# 590.97. Stack view

Stack frame click được để chuyển source context.

---

# 590.98. Async debug view

Có logical task tree:

```text
Executor
├── Task A
│    └── await
├── Task B
└── Task C
```

---

# 590.99. Thread view

```text
Process
├── Thread 1
├── Thread 2
└── Thread 3
```

---

# 590.100. Crash analysis UI

Crash dump mở trực tiếp trong IDE:

```text
Exception
 ↓
Thread
 ↓
Stack
 ↓
Source
 ↓
Variables
```

---

# 590.101. Profiler integration

Profiler `476/481` là IDE service.

---

# 590.102. CPU profiler

Hiển thị:

```text
hot functions
call tree
flame graph
samples
```

---

# 590.103. Allocation profiler

Có thể hiển thị:

```text
allocation site
allocation count
bytes
lifetime
```

---

# 590.104. Lock profiler

Hiển thị:

```text
lock
contention
wait time
owner
```

---

# 590.105. Async profiler

Hiển thị:

```text
task latency
await time
scheduler delay
queue time
```

---

# 590.106. GPU profiler

Khi target hỗ trợ GPU:

```text
kernel
dispatch
memory transfer
occupancy
```

---

# 590.107. Performance source mapping

Profiler samples map về:

```text
function
source line
module
```

---

# 590.108. Hotspot navigation

Click hotspot → source line.

---

# 590.109. Performance comparison

Cho phép compare:

```text
baseline
current
```

nhưng IDE không tự kết luận nguyên nhân nếu evidence chưa đủ.

---

# 590.110. Static analysis integration

IDE sử dụng `571–574`.

---

# 590.111. Live analysis

Analysis chạy incremental.

---

# 590.112. Severity

```text
error
warning
advisory
```

---

# 590.113. Dataflow visualization

Có thể visualize:

```text
input
 ↓
transform
 ↓
sink
```

---

# 590.114. Security flow

Security analyzer có thể highlight:

```text
source
 ↓
propagation
 ↓
sink
```

---

# 590.115. Dead code visualization

IDE có thể dim dead code nhưng không thay đổi source.

---

# 590.116. Unreachable state

Hiển thị unreachable branches với diagnostic explanation.

---

# 590.117. Contract integration

Contracts `479` được IDE hiển thị:

```text
precondition
postcondition
invariant
```

---

# 590.118. Contract failure navigation

Runtime contract failure map về source declaration.

---

# 590.119. Package manager integration

IDE gọi package manager `432/447`.

---

# 590.120. Dependency explorer

Hiển thị:

```text
App
 ├── A
 │   └── C
 └── B
```

---

# 590.121. Dependency versions

Hiển thị:

```text
resolved version
source
hash
license metadata
```

---

# 590.122. Dependency conflict

Conflict có diagnostic/action:

```text
required X
resolved Y
```

---

# 590.123. SDK manager integration

IDE có thể chọn:

```text
toolchain
target SDK
runtime
```

---

# 590.124. Target selector

UI:

```text
Target: Linux x86_64
Profile: Debug
Toolchain: Axiom 2.x
```

---

# 590.125. Configuration inspector

Hiển thị effective configuration sau resolution.

---

# 590.126. No hidden configuration

User phải có thể inspect vì sao một option đang active.

---

# 590.127. Environment inspector

IDE có thể show:

```text
compiler
SDK
sysroot
target
features
environment
```

---

# 590.128. Terminal integration

IDE terminal chỉ là shell integration.

Không được trở thành semantic source of truth.

---

# 590.129. Command palette

Mọi IDE command có stable ID:

```text
axiom.build
axiom.test
axiom.debug
axiom.rename
axiom.format
```

---

# 590.130. Keyboard-first design

Mọi chức năng chính phải có keyboard command.

Điều này đặc biệt quan trọng với remote desktop/accessibility workflows.

---

# 590.131. Command keymap

Keymap configurable.

---

# 590.132. Context-aware commands

Command availability phụ thuộc:

```texteditor
debugger
project
selection
```

---

# 590.133. Workspace state

IDE lưu:

```text
open files
panels
breakpoints
debug configurations
search history
```

---

# 590.134. State persistence

State persistence không được làm thay đổi source/build semantics.

---

# 590.135. Session restore

Có thể restore workspace sau crash.

---

# 590.136. File watcher

File watcher phải incremental.

---

# 590.137. External file change

Nếu file bị sửa ngoài IDE:

```text
detect
compare
prompt/merge
reindex
```

---

# 590.138. Conflict model

Không overwrite silently user changes.

---

# 590.139. Git integration boundary

IDE có thể tích hợp source control nhưng compiler không phụ thuộc Git.

---

# 590.140. Change visualization

Semantic diff có thể phân biệt:

```text
text change
symbol change
API change
behavior-risking change
```

---

# 590.141. Refactoring diff

Refactor phải show exact edits trước apply.

---

# 590.142. AI integration

AI Agent là client của semantic workspace, không phải một compiler frontend mới.

```text
AI Agent
   ↓
Axiom Semantic API
   ↓
Compiler/IDE
```

---

# 590.143. AI workspace context

AI có thể query:

```text
project structure
symbols
dependencies
diagnostics
build state
tests
debug state
profiler data
```

---

# 590.144. AI code generation

Generated code phải đi qua:

```text
parse
type-check
analysis
tests
build
```

như code người viết.

---

# 590.145. AI edit transaction

AI edits phải:

```text
plan
preview
apply
compile
validate
```

---

# 590.146. AI semantic search

Agent có thể hỏi:

```text
find all implementations of Trait X
```

thay vì scan text.

---

# 590.147. AI impact analysis

Agent có thể query:

```text
what depends on function X?
```

từ semantic dependency graph.

---

# 590.148. AI debugging

AI có thể consume `DebugSnapshot`.

---

# 590.149. AI test repair

AI có thể nhận:

```text
failed test
stack
source
diagnostics
diff
```

nhưng mọi sửa đổi phải qua compiler/test validation.

---

# 590.150. AI permissions

AI action phải có permission levels:

```text
read
edit
build
test
debug
run
package
```

---

# 590.151. AI destructive operations

Các thao tác như:

```text
delete files
change dependencies
publish package
sign artifact
```

phải explicit authorization.

---

# 590.152. AI audit log

Workspace phải có audit record cho AI mutations.

---

# 590.153. Semantic API

Canonical API:

```text
WorkspaceQuery
SymbolQuery
TypeQuery
ReferenceQuery
BuildQuery
TestQuery
DebugQuery
ProfileQuery
```

---

# 590.154. Query consistency

Tất cả query đều gắn snapshot/revision.

---

# 590.155. Query caching

Semantic query cache dùng infrastructure `559`.

---

# 590.156. Query invalidation

Thay đổi source chỉ invalidate dependent queries.

---

# 590.157. Parallel IDE services

Editor, diagnostics, indexing, completion và build status có thể chạy song song.

---

# 590.158. Resource limits

IDE phải có memory/CPU budget.

---

# 590.159. Large workspace

Thiết kế phải scale tới workspace có hàng triệu LOC.

---

# 590.160. Lazy indexing

Không cần index toàn bộ dependency tree nếu chưa được query.

---

# 590.161. Dependency pre-index

Binary package có semantic metadata có thể index mà không parse source.

---

# 590.162. Remote workspace

Semantic service có thể chạy remote:

```text
IDE
 │
 ▼
Remote Semantic Server
 │
 ▼
Compiler/Workspace
```

---

# 590.163. Remote build

IDE tích hợp distributed build `567`.

---

# 590.164. Remote cache

IDE có thể query build cache status.

---

# 590.165. Offline IDE

IDE phải hoạt động đầy đủ cho local project khi network unavailable.

---

# 590.166. Offline degradation

Network-dependent features phải degrade rõ ràng, không làm hỏng local development.

---

# 590.167. Plugin architecture

IDE plugin có thể cung cấp:

```text
language extension
debug adapter
visualizer
formatter
tool integration
```

---

# 590.168. Plugin isolation

Plugin không mặc định có full filesystem/process privileges.

---

# 590.169. Plugin API version

Plugin API versioned độc lập với language version.

---

# 590.170. Plugin trust

Plugin metadata phải khai báo:

```text
permissions
publisher
version
hash
```

---

# 590.171. UI architecture

UI layer phải tách khỏi semantic core:

```text
Semantic Core
      ↓
IDE Service API
      ↓
Desktop UI
Web UI
CLI/TUI
```

---

# 590.172. Desktop UI

Axiom có thể cung cấp native desktop IDE.

---

# 590.173. Web IDE

Có thể cung cấp web frontend sử dụng cùng semantic backend.

---

# 590.174. TUI

Core commands phải hoạt động qua terminal/TUI.

---

# 590.175. Accessibility

IDE phải follow accessibility model `466`.

---

# 590.176. Screen reader

Semantic tree phải có accessible labels.

---

# 590.177. High contrast

UI theme phải hỗ trợ accessibility contrast requirements.

---

# 590.178. Localization

UI strings không được hardcode trong semantic core.

---

# 590.179. Crash recovery

IDE crash phải preserve unsaved buffers khi có thể.

---

# 590.180. Safe write

Source save phải atomic:

```text
temporary
 ↓
fsync/commit policy
 ↓
rename
```

---

# 590.181. File corruption protection

IDE không được overwrite source bằng empty/truncated buffer sau crash.

---

# 590.182. Telemetry

IDE telemetry nếu có phải optional.

---

# 590.183. Privacy

Source code không được gửi ra ngoài workspace mặc định.

---

# 590.184. AI privacy

AI integration phải có explicit data boundary.

---

# 590.185. Build reproducibility UI

IDE phải cho xem:

```text
compiler hash
toolchain hash
SDK hash
dependency hashes
build configuration
```

---

# 590.186. Artifact provenance UI

Artifact có thể truy ngược:

```text
binary
 ↓
build action
 ↓
source
 ↓
dependencies
 ↓
toolchain
```

---

# 590.187. Artifact explorer

IDE hiển thị:

```text
executable
libraries
debug artifacts
metadata
SBOM/provenance
```

---

# 590.188. Binary inspection

Có thể inspect:

```text
sections
symbols
imports
exports
relocations
architecture
ABI
```

---

# 590.189. Size analysis

IDE có thể hiển thị:

```text
code
data
rodata
debug
resources
```

---

# 590.190. Binary diff

So sánh hai binaries theo:

```text
section
symbol
function
size
machine code
```

---

# 590.191. Function-level size diff

Có thể xác định function nào làm binary tăng kích thước.

---

# 590.192. Compiler explorer mode

IDE có thể hiển thị:

```text
Axiom source
   ↓
MIR
   ↓
Machine IR
   ↓
Assembly
   ↓
Machine bytes
```

---

# 590.193. Optimization explanation

Compiler có thể giải thích:

```text
inlined
vectorized
constant-folded
dead-code eliminated
not optimized
```

---

# 590.194. Optimization diagnostics

Không được coi optimization explanation là semantic truth nếu pass không cung cấp evidence.

---

# 590.195. Query provenance

Mọi AI/IDE explanation có thể reference:

```text
query
snapshot
compiler phase
source range
```

---

# 590.196. Workspace command API

Mọi action có command ID và structured input/output.

---

# 590.197. Automation

Workspace có thể chạy:

```text
build
test
format
lint
benchmark
package
```

theo workflow.

---

# 590.198. Workflow state

Workflow phải có:

```text
pending
running
success
failed
cancelled
```

---

# 590.199. Task graph

IDE có thể visualize workflow DAG.

---

# 590.200. Final architecture

```text
                         AXIOM WORKSPACE
                                │
       ┌────────────────────────┼────────────────────────┐
       ▼                        ▼                        ▼
   SOURCE MODEL            PROJECT MODEL           TOOLCHAIN
       │                        │                        │
       └──────────────┬─────────┴────────────┬───────────┘
                      ▼                      ▼
               SEMANTIC DATABASE       BUILD GRAPH
                      │                      │
          ┌───────────┼──────────┐           │
          ▼           ▼          ▼           ▼
        LSP       Refactor      AI        Compiler
          │           │          │           │
          └───────────┼──────────┘           ▼
                      │                  Artifact
                      │                     │
          ┌───────────┴─────────────┐       │
          ▼                         ▼       ▼
      Debugger                  Profiler  Tests
          │                         │       │
          └──────────────┬──────────┴───────┘
                         ▼
                  Unified IDE State
```

---

# 590.201. Performance requirements

IDE phải tận dụng:

- incremental compilation;
- query cache;
- parallel query execution;
- lazy indexing;
- immutable semantic snapshots;
- content-addressed artifacts.

Không được full-reparse/full-typecheck workspace sau mỗi keystroke.

---

# 590.202. IDE correctness model

IDE semantic information có ba trạng thái:

```text
Current
Stale
Unavailable
```

Không được biến `Stale` thành `Current`.

---

# 590.203. Editor/compiler race

Nếu user sửa file trong lúc compiler đang chạy:

```text
Revision N
   ↓
build starts
   ↓
user edits
   ↓
Revision N+1
```

artifact từ `N` không được gắn với source `N+1`.

---

# 590.204. Build artifact association

Artifact phải record source/build context identity.

---

# 590.205. Debug/build association

Debugger chỉ tự động attach debug symbols nếu build ID tương ứng.

---

# 590.206. Test/build association

Test result phải record artifact/build identity.

---

# 590.207. Profile/build association

Profile phải record executable identity.

---

# 590.208. AI/build association

AI diagnosis phải biết snapshot/build/test revision mà nó dựa vào.

---

# 590.209. Unified provenance

Toàn bộ development state có thể truy:

```text
Source Revision
      ↓
Semantic Snapshot
      ↓
Build Context
      ↓
Artifact
      ↓
Test
      ↓
Debug/Profile
```

---

# 590.210. No duplicated truth

Đây là invariant kiến trúc quan trọng nhất của `590`:

> Editor, LSP, compiler, debugger, profiler, test runner và AI không được duy trì các bản sao semantic độc lập có thể mâu thuẫn.

---

# 590.211. FINAL HARD INVARIANTS

### Invariant 1 — one semantic truth

> Compiler semantic database là nguồn canonical cho IDE semantic services.

### Invariant 2 — incremental

> Một thay đổi nhỏ trong source không được bắt buộc reparse/reanalyze toàn workspace nếu dependency graph không yêu cầu.

### Invariant 3 — snapshot consistency

> Mọi IDE result phải thuộc một semantic snapshot xác định.

### Invariant 4 — stale safety

> Kết quả của snapshot cũ không được ghi đè trạng thái mới.

### Invariant 5 — semantic navigation

> Definition/reference/rename phải dựa trên semantic identity, không dựa chủ yếu trên text matching.

### Invariant 6 — refactoring atomicity

> Refactoring hoặc được apply hoàn chỉnh hoặc không thay đổi workspace.

### Invariant 7 — build identity

> Build artifact phải gắn với source revision + toolchain + target + configuration.

### Invariant 8 — debug identity

> Debugger không được ghép nhầm binary với debug information khác build.

### Invariant 9 — AI validation

> Code do AI tạo hoặc sửa phải đi qua cùng compiler/type-check/test pipeline như code của con người.

### Invariant 10 — AI evidence

> AI tooling không được coi dữ liệu stale, unavailable hoặc suy đoán là semantic fact.

### Invariant 11 — no hidden mutation

> IDE/AI/plugin không được âm thầm sửa source, dependency, toolchain hoặc signing state ngoài command transaction tương ứng.

### Invariant 12 — offline development

> Core IDE development workflow phải hoạt động offline với toolchain/project artifacts đã có.

### Invariant 13 — plugin isolation

> Plugin không được mặc định có quyền hệ thống vượt quá capability được cấp.

### Invariant 14 — UI independence

> Semantic engine không phụ thuộc desktop UI; CLI/TUI/web/native UI có thể cùng sử dụng một backend.

### Invariant 15 — performance

> IDE phải tận dụng compiler incremental/query infrastructure thay vì xây một pipeline phân tích song song tốn tài nguyên.

---

# 590 — LOCKED

Axiom hiện có một chuỗi developer infrastructure khá hoàn chỉnh:

```text
436–438   Compiler architecture
559       Query engine
569–578   Analysis / optimization
580–584   Machine code → executable
586–587   Self-hosting + trust
588       Toolchain / SDK
589       Native debugger
590       Unified IDE
```

Kiến trúc lúc này đã đạt:

```text
                    AXIOM PLATFORM
                         │
       ┌─────────────────┼──────────────────┐
       ▼                 ▼                  ▼
    LANGUAGE          TOOLCHAIN          IDE
       │                 │                  │
       ▼                 ▼                  ▼
   Compiler           SDK/ABI          Semantic DB
       │                 │                  │
       ▼                 ▼          ┌───────┼────────┐
 Native Binary       Cross Build     LSP   Debug    AI
                                      │      │       │
                                      └──────┼───────┘
                                             ▼
                                      Developer Workflow
```

---

# NEXT — BOOTSTRAP-591

## PACKAGE REGISTRY, DEPENDENCY RESOLUTION & SUPPLY-CHAIN PLATFORM 5.0
### PACKAGE INDEX, VERSION SOLVER, LOCKFILE, SOURCE/BINARY PACKAGES, NATIVE LIBRARIES, TARGET VARIANTS, ABI COMPATIBILITY, CONTENT-ADDRESSED STORAGE, SIGNATURES, PROVENANCE, OFFLINE MIRRORS & REPRODUCIBLE DEPENDENCY GRAPH

```text
                    Axiom Project
                         │
                         ▼
                  Dependency Graph
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         Local Cache             Registry
              │                     │
              └──────────┬──────────┘
                         ▼
                  Version Solver
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Source     Binary      Native
           Package    Package     Package
              │          │          │
              └──────────┼──────────┘
                         ▼
                  Verified Graph
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Signature   Provenance   ABI
              │          │          │
              └──────────┼──────────┘
                         ▼
                 Reproducible Build
```

`591` sẽ đặc tả tầng package ecosystem còn thiếu để Axiom có thể đi từ **một toolchain tự chủ** tới **một hệ sinh thái package có source package, precompiled package và native library package**, đồng thời vẫn giữ các invariant về ABI, reproducibility, offline build và supply-chain trust đã khóa ở `447`, `487`, `550`, `587`, `588`.