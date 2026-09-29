# BOOTSTRAP-115 — Compiler Tooling, Diagnostics & Developer/AI Interface

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu của task này là biến Axiom compiler từ một chương trình chỉ biết **biên dịch** thành một hệ thống mà lập trình viên và AI agent có thể **hiểu, kiểm tra, điều khiển và debug compiler**.

Nguyên tắc:

> **Compiler phải giải thích được quyết định của chính nó ở mức semantic, nhưng explanation không được trở thành một phần của language semantics.**

---

# 1. Kiến trúc tooling tổng thể

```text
                    ax
                     │
          ┌──────────┴──────────┐
          │                     │
       CLI Driver              LSP
          │                     │
          └──────────┬──────────┘
                     │
                CompilerDB
                     │
      ┌──────────────┼──────────────┐
      │              │              │
 Diagnostics      Inspect        Explain
      │              │              │
      └──────────────┼──────────────┘
                     │
              Compiler Pipeline
```

CLI, LSP, IDE, AI agent **không được tự xây semantic logic riêng**.

Tất cả phải dùng chung `CompilerDB`.

---

# 2. CLI chuẩn

Axiom sử dụng:

```text
ax
```

làm driver chính.

Các command Core:

```text
ax build
ax check
ax run
ax test
ax bench
ax clean
ax fmt
ax doc
ax inspect
ax explain
ax query
ax package
```

Toolchain:

```text
ax toolchain
ax target
ax version
```

---

# 3. `ax check`

Chỉ thực hiện:

```text
parse
resolve
type-check
trait solving
comptime
ownership
capability
concurrency
ABI validation
```

Không nhất thiết codegen.

Ví dụ:

```text
ax check
```

phải đủ nhanh để IDE gọi liên tục.

---

# 4. `ax build`

Pipeline:

```text
source
 ↓
check
 ↓
verify
 ↓
optimize
 ↓
ABI
 ↓
LIR
 ↓
machine code
 ↓
object
 ↓
link
```

Nếu cache hợp lệ thì mỗi tầng chỉ chạy lại khi fingerprint thay đổi.

---

# 5. `ax run`

```text
ax run
```

tương đương:

```text
build → execute
```

Nhưng compiler có thể tránh link lại nếu artifact vẫn hợp lệ.

---

# 6. `ax inspect`

Đây là command đặc biệt quan trọng với Axiom.

Ví dụ:

```text
ax inspect ast
ax inspect hir
ax inspect mir
ax inspect verified-mir
ax inspect optir
ax inspect abi
ax inspect lir
ax inspect machine
ax inspect object
ax inspect link
```

Có thể giới hạn:

```text
ax inspect mir --function foo
ax inspect optir --function foo
ax inspect abi --type MyStruct
```

---

# 7. Compiler không chỉ xuất text

Mọi IR nên có hai representation:

```text
HumanReadable
MachineReadable
```

Ví dụ:

```text
ax inspect mir --format=json
```

AI agent có thể đọc trực tiếp.

Không bắt AI phải parse text compiler output.

---

# 8. `ax explain`

Đây là một tính năng nên trở thành đặc trưng của Axiom.

Ví dụ:

```text
ax explain EOWN_MOVED
```

hoặc:

```text
ax explain --function foo
```

Compiler có thể giải thích:

```text
value x
  ownership acquired here

x moved here
  call: consume(x)

x used here
  invalid because ownership was transferred
```

---

# 9. Explain phải dựa trên semantic facts

Không dùng LLM để giải thích semantics.

Compiler tạo:

```text
ExplanationGraph
```

gồm:

```text
Declaration
Type
OwnershipState
Capability
Region
ControlFlow
TraitResolution
Move
Drop
Await
Synchronization
```

AI/IDE chỉ chuyển graph thành cách trình bày dễ hiểu.

---

# 10. Diagnostic model

Diagnostic không chỉ là:

```text
error: something went wrong
```

Mà là object:

```text
Diagnostic {
    code
    severity
    message
    primary_span
    secondary_spans[]
    notes[]
    help[]
    related[]
    semantic_facts
}
```

---

# 11. Stable diagnostic code

Ví dụ:

```text
E0001
ERESOLVE_UNDEFINED
ERESOLVE_AMBIGUOUS
ETYPE_MISMATCH
EOWN_MOVED
EOWN_DOUBLE_DROP
ECAP_CONFLICT
ECAP_ESCAPE
ESEND_REQUIRED
EAWAIT_CAPABILITY
ETRAIT_UNSATISFIED
EABI_INVALID
```

Code là stable API.

Message text có thể thay đổi.

---

# 12. Diagnostic severity

Chuẩn:

```text
ERROR
WARNING
NOTE
HELP
INFO
```

Không để warning trở thành semantic error tùy formatter.

---

# 13. Source spans

Compiler phải lưu:

```text
SourceFileId
start
end
line
column
```

và mapping:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
MIR
 ↓
OptIR
 ↓
LIR
 ↓
Machine
```

---

# 14. Diagnostic nhiều vị trí

Ví dụ capability conflict:

```text
error ECAP_CONFLICT

write access starts here
        ↓
    [x.field]

read access occurs here
        ↓
       foo(x)

these regions may overlap
```

Compiler chỉ ra **tất cả nguyên nhân liên quan**, không chỉ token cuối cùng.

---

# 15. Suggestions phải có semantic proof

Compiler có thể đưa:

```text
help:
  move this operation before the borrow

help:
  create an owned copy with `clone()`

help:
  restrict this view to the disjoint field
```

Nhưng suggestion chỉ được sinh nếu compiler biết nó hợp lệ.

Không đưa “AI guess” như compiler suggestion chính thức.

---

# 16. Machine-readable diagnostics

```text
ax check --diagnostic-format=json
```

Output:

```text
{
  "code": "EOWN_MOVED",
  "severity": "error",
  "file": "...",
  "span": {...},
  "related": [...]
}
```

Có thể thêm:

```text
--format=json
--format=jsonl
--format=text
--format=human
```

---

# 17. AI compiler interface

Axiom nên có:

```text
ax query
```

Ví dụ:

```text
ax query symbol foo
ax query type MyStruct
ax query callers foo
ax query implementations Trait
ax query ownership foo
ax query capabilities foo
ax query dependencies foo
```

AI agent không cần parse toàn bộ source để trả lời các câu hỏi cơ bản.

---

# 18. Semantic query

Ví dụ:

```text
ax query "why is foo not Send"
```

Compiler không cần LLM.

Nó trả:

```text
foo
 └── contains Bar
      └── contains Rc<Baz>
           └── Rc is not Send
```

Đây là **semantic explanation graph**.

---

# 19. Ownership visualization

Compiler có thể xuất:

```text
ax explain ownership foo
```

Ví dụ:

```text
x : Owned<T>
 │
 ├── read
 │
 ├── view ───────┐
 │               │
 │               └── ends
 │
 └── move
       │
       └── Moved
```

Điều này đặc biệt hữu ích cho AI agent.

---

# 20. Capability visualization

```text
ax explain capability foo
```

Ví dụ:

```text
owner: buffer

capabilities:
    C1 READ  [0..1024]
    C2 READ  [512..768]

no conflict

C3 WRITE [700..900]

conflicts with C2
```

---

# 21. Trait solver explanation

Compiler phải giải thích:

```text
ax explain trait Send MyType
```

Ví dụ:

```text
Send(MyType)
 ├── Send(FieldA)
 │    └── yes
 │
 └── Send(FieldB)
      └── no
           └── Rc<T> is not Send
```

Không để AI phải reverse-engineer trait solver.

---

# 22. Generic instantiation inspection

```text
ax inspect generic foo
```

có thể hiển thị:

```text
foo<i32>
foo<f64>
foo<MyType>
```

và:

```text
monomorphized
shared
deduplicated
specialized
```

---

# 23. Optimization explanation

Một điểm rất mạnh cho Axiom:

```text
ax explain optimize foo
```

Ví dụ:

```text
allocation eliminated:
    Box<T>

reason:
    address does not escape

bounds check eliminated:
    index range proven [0, n)

inlined:
    bar()

vectorized:
    loop L3
```

---

# 24. Failed optimization cũng có explanation

Không chỉ nói compiler tối ưu được gì.

Ví dụ:

```text
allocation not eliminated

reason:
    storage identity escapes through foreign call
```

hoặc:

```text
bounds check retained

reason:
    index range is UNKNOWN
```

Điều này cực kỳ hữu ích cho performance engineering.

---

# 25. `ax explain perf`

Có thể tổng hợp:

```text
allocations
branches
inlining
vectorization
locks
atomics
foreign calls
cache-sensitive structures
```

Nhưng đây là static explanation, không thay thế profiler.

---

# 26. LSP

Axiom cần official language server:

```text
axiom-lsp
```

Không để mỗi IDE tự implement parser/type checker.

LSP sử dụng trực tiếp:

```text
CompilerDB
```

---

# 27. LSP features

Core:

```text
completion
hover
definition
declaration
references
rename
signature help
diagnostics
semantic tokens
document symbols
workspace symbols
code actions
formatting
```

---

# 28. Refactoring phải semantic

Ví dụ rename:

```text
foo → bar
```

phải dựa trên:

```text
DeclarationId
```

không phải search/replace text.

Điều này tránh phá:

```text
comments
strings
unrelated symbols
shadowed names
```

---

# 29. Formatter

```text
ax fmt
```

Formatter là deterministic.

Không có:

```text
project-local arbitrary formatting engine
```

mặc định.

Có config:

```text
axiom.toml
```

nhưng formatter phải giữ semantic identity.

---

# 30. Documentation

```text
ax doc
```

sinh documentation từ:

```text
pub declarations
/// comments
types
traits
examples
attributes
```

Có thể xuất:

```text
HTML
Markdown
JSON
```

---

# 31. API documentation graph

Documentation không chỉ là text.

Compiler biết:

```text
FunctionId
TypeId
TraitId
ModuleId
```

nên documentation có thể liên kết trực tiếp:

```text
type → methods
trait → implementations
function → callers
type → fields
```

---

# 32. Test runner

```text
ax test
```

phát hiện:

```text
@test fn ...
```

Test binary không link những thành phần không cần.

Có:

```text
unit
integration
compile-fail
runtime
property
fuzz
```

---

# 33. Compile-fail tests

Đặc biệt quan trọng với compiler.

Ví dụ:

```text
tests/ui/ownership/moved.ax
```

mong đợi:

```text
EOWN_MOVED
```

Không nên so sánh toàn bộ message text.

So sánh:

```text
diagnostic code
span
semantic facts
```

---

# 34. Snapshot diagnostics

Có thể có:

```text
.axdiag
```

nhưng snapshot phải tránh phụ thuộc:

```text
absolute path
machine address
nondeterministic ordering
```

---

# 35. Benchmark

```text
ax bench
```

tách:

```text
compile benchmark
runtime benchmark
memory benchmark
code-size benchmark
```

Không trộn compile performance với runtime performance.

---

# 36. Profiler integration

Compiler có thể emit:

```text
debug symbols
DWARF
CodeView
unwind info
perf metadata
```

tùy target.

Profiler không phải compiler semantic layer.

---

# 37. Sanitizers

Axiom nên hỗ trợ:

```text
address
memory
thread
undefined-machine-condition
```

nhưng sanitizer không thay đổi language semantics.

Ví dụ:

```text
ax build --sanitize=address
```

có thể inject instrumentation.

---

# 38. Debugger

Compiler phải duy trì:

```text
source → HIR → MIR → optimized code → machine
```

debug mapping.

Cho phép:

```text
breakpoint
step
locals
watch
stack
threads
async tasks
```

Các capability/ownership state có thể được expose trong debug build.

---

# 39. Ownership-aware debugger

Đây là một điểm nên làm riêng cho Axiom.

Debugger có thể hiển thị:

```text
x
  state: Owned
  type: Buffer
  storage: dynamic
  capabilities: 1 READ
  address: ...
```

Sau move:

```text
x
  state: Moved
```

Không chỉ hiển thị raw memory.

---

# 40. Async debugger

Future state:

```text
Future<T>
    state: Suspended
    suspension: #4
    live fields:
        socket
        buffer
```

Task:

```text
READY
RUNNING
WAITING
COMPLETED
CANCELLED
PANICKED
```

được hiển thị nếu runtime hỗ trợ debug metadata.

---

# 41. GPU debugging

Có thể inspect:

```text
kernel
device buffer
launch
event
```

nhưng không giả định mọi GPU debugger đều có cùng khả năng.

Axiom chỉ phát metadata chuẩn.

---

# 42. Compiler server

IDE/AI không nên mỗi lần lại khởi động compiler mới.

Có:

```text
ax daemon
```

giữ:

```text
CompilerDB
TypeDB
PackageDB
incremental cache
```

trong memory.

---

# 43. Incremental IDE architecture

```text
edit
 ↓
changed SourceFile
 ↓
incremental revision
 ↓
affected declarations
 ↓
affected type/trait facts
 ↓
affected diagnostics
```

Không rebuild toàn workspace cho một ký tự.

---

# 44. AI agent interface

Axiom cần một interface chính thức:

```text
ax agent
```

với structured operations:

```text
inspect
query
explain
check
patch
test
build
benchmark
```

AI không cần shell-scrape output.

---

# 45. Agent transaction model

AI agent có thể yêu cầu:

```text
check current workspace
```

và nhận:

```text
BuildResult {
    diagnostics
    changed_files
    affected_packages
    artifacts
}
```

Mọi operation có identity.

---

# 46. AI không được bypass compiler

AI agent không được tự kết luận:

```text
"chắc là Send"
```

rồi sửa code.

Workflow đúng:

```text
AI hypothesis
      ↓
compiler query
      ↓
compiler semantic facts
      ↓
AI reasoning
      ↓
patch
      ↓
ax check
```

Compiler là authority về language semantics.

---

# 47. Machine-readable project graph

```text
ax query graph
```

xuất:

```text
package
module
dependency
symbol
type
generic
trait
comptime
artifact
```

AI có thể xây context chính xác mà không cần đọc toàn bộ repository.

---

# 48. Token-efficiency cho AI

Điều này đặc biệt phù hợp mục tiêu Axiom.

Thay vì AI đọc:

```text
5000 dòng source
```

có thể hỏi:

```text
ax query symbol Foo
```

và nhận:

```text
signature
visibility
traits
fields
dependencies
source span
ABI
```

Sau đó chỉ đọc phần source cần thiết.

---

# 49. Semantic diff

Nên có:

```text
ax diff
```

không chỉ text diff.

Ví dụ:

```text
API changed:
    fn foo(i32) -> i32
    →
    fn foo(i64) -> i32

ABI changed: YES

trait contract changed: NO

private implementation changed: YES
```

---

# 50. API compatibility checker

```text
ax check-api old.axmeta new.axmeta
```

có thể phát hiện:

```text
breaking API
ABI change
repr change
trait compatibility
generic constraint change
visibility change
export change
```

---

# 51. Compiler contracts

Mỗi compiler stage phải có machine-readable contract.

Ví dụ:

```text
Parser:
    valid syntax tree

Resolver:
    all references resolved

TypeChecker:
    typed HIR

Verifier:
    safety invariants proven

Optimizer:
    semantics preserved

ABI:
    all physical representation decisions resolved

LIR:
    target-legal operations
```

---

# 52. Trust boundaries

```text
Source
  ↓
Parser
  ↓
Semantic Compiler
  ↓
VERIFIED MIR  ← correctness boundary
  ↓
Optimizer
  ↓
ABI
  ↓
Backend
```

Compiler debug tooling **không được bypass boundary**.

---

# 53. Compiler panic vs user panic

Phân biệt tuyệt đối:

```text
User program panic
```

và:

```text
Compiler internal error / ICE
```

Ví dụ:

```text
ICE0001
```

không được biến thành:

```text
E...
```

vì compiler bug không phải source error.

---

# 54. ICE report

Compiler crash phải tạo:

```text
compiler version
target
source fingerprint
stage
pass
function/type
stack
reproduction command
```

Có thể:

```text
ax bug-report
```

để đóng gói report.

---

# 55. Deterministic tooling

Cùng:

```text
source
compiler
target
config
```

phải tạo cùng semantic result.

Không để diagnostic ordering phụ thuộc thread scheduling.

Parallel compilation chỉ thay đổi tốc độ.

---

# 56. Tooling invariants

### `ATOOL-20`
All tooling shares the compiler semantic database.

### `ATOOL-21`
IDE tooling does not implement an independent semantic engine.

### `ATOOL-22`
Diagnostics have stable machine-readable codes.

### `ATOOL-23`
Diagnostic messages are not semantic identifiers.

### `ATOOL-24`
Compiler explanations derive from compiler facts.

### `ATOOL-25`
AI is not a semantic authority.

### `ATOOL-26`
AI tooling cannot bypass semantic verification.

### `ATOOL-27`
IR inspection is available in machine-readable form.

### `ATOOL-28`
Semantic source-to-machine provenance is preserved.

### `ATOOL-29`
Ownership diagnostics expose relevant move/drop facts.

### `ATOOL-30`
Capability diagnostics expose relevant region/access facts.

### `ATOOL-31`
Trait diagnostics can expose solver reasoning.

### `ATOOL-32`
Optimization diagnostics can expose transformation decisions.

### `ATOOL-33`
Failed optimizations may be explained.

### `ATOOL-34`
LSP uses CompilerDB.

### `ATOOL-35`
Refactoring is semantic rather than textual.

### `ATOOL-36`
Formatter is deterministic.

### `ATOOL-37`
Compile-fail tests identify diagnostics by stable code.

### `ATOOL-38`
Compiler ICEs are distinct from user diagnostics.

### `ATOOL-39`
Tooling output is deterministic.

### `ATOOL-40`
Compiler server state is incremental.

### `ATOOL-41`
Semantic queries use compiler IDs rather than textual heuristics.

### `ATOOL-42`
AI-facing APIs are structured.

### `ATOOL-43`
AI-facing APIs expose enough information to reduce unnecessary source retrieval.

### `ATOOL-44`
Tooling cannot weaken ownership, capability, concurrency, ABI, or FFI verification.

### `ATOOL-45`
Debug information does not alter program semantics.

### `ATOOL-46`
Profiling instrumentation does not redefine language semantics.

### `ATOOL-47`
Sanitizers are optional instrumentation.

### `ATOOL-48`
Optimization explanations reflect actual compiler decisions.

### `ATOOL-49`
Semantic diff distinguishes API, ABI, and implementation changes.

### `ATOOL-50`
Tooling operates consistently across hosted and freestanding profiles where applicable.

### `ATOOL-51`
No mandatory AI service is required by the compiler.

### `ATOOL-52`
No LLM is required to compile valid Axiom programs.

### `ATOOL-53`
AI integration is an external tooling layer.

### `ATOOL-54`
Compiler semantic results remain deterministic regardless of AI tooling.

### `ATOOL-55`
CompilerDB is the authoritative source for IDE, CLI, and AI semantic queries.

---

# Trạng thái Axiom sau 115

Đến đây kiến trúc đã đi khá xa:

```text
Language
   ↓
Type / Ownership / Capability
   ↓
Concurrency / Async / GPU
   ↓
Comptime / Reflection
   ↓
HIR / MIR / Verification
   ↓
Optimization
   ↓
ABI
   ↓
LIR / Backend
   ↓
Object / Linker
   ↓
Runtime
   ↓
Stdlib
   ↓
Build System
   ↓
Tooling / IDE / AI
```

**Điểm quan trọng:** chúng ta đã gần hoàn thành phần **kiến trúc tĩnh của Axiom**. Bước tiếp theo không nên tiếp tục thêm feature ngôn ngữ một cách tùy tiện nữa.

# BOOTSTRAP-116 — Compiler Correctness, Conformance & Validation Architecture

Task tiếp theo sẽ khóa **cách chứng minh compiler thực sự implement đúng Axiom**, thay vì chỉ có một compiler chạy được.

Nó sẽ thiết kế:

```text
Language Specification
        ↓
Semantic Rules
        ↓
Reference Tests
        ↓
Conformance Suite
        ↓
Compiler
        ↓
Verified MIR
        ↓
Backend
        ↓
Native Execution
```

và đặc biệt:

- Core Language Conformance Suite
- type-system tests
- ownership/capability tests
- concurrency memory-model tests
- async tests
- GPU legality tests
- comptime tests
- ABI/FFI tests
- object/linker tests
- runtime tests
- stdlib conformance
- compile-fail suite
- fuzzing parser/type checker/MIR
- differential testing
- metamorphic testing
- miscompilation detection
- optimizer correctness
- backend correctness
- bootstrap compiler validation
- cross-target validation
- deterministic/reproducible-build testing
- **semantic golden tests**
- và quan trọng nhất: cơ chế đảm bảo một optimization không bao giờ được phép biến chương trình hợp lệ thành chương trình có semantics khác.

Sau 116, chúng ta có thể chuyển sang **BOOTSTRAP-117 — Axiom Core v0.1 Language Specification Consolidation**, tức gom toàn bộ các quyết định đã khóa thành một **specification chính thức, không còn là các task rời rạc**.