# BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE

**Trạng thái: LOCKED DESIGN**

BOOTSTRAP-434 định nghĩa lớp công cụ bao quanh compiler Axiom. Mục tiêu là compiler phải **dễ sử dụng bằng người, dễ điều khiển bằng AI agent, dễ tích hợp IDE/CI**, nhưng không biến CLI/toolchain thành một hệ thống quá phức tạp.

---

## 434.1 — Toolchain Boundary

Axiom toolchain được chia thành:

```text
axiom
 ├── driver
 ├── compiler
 ├── linker
 ├── formatter
 ├── test runner
 ├── package manager
 ├── documentation generator
 ├── LSP server
 ├── artifact inspector
 └── cache manager
```

Compiler core không phụ thuộc IDE.

LSP không được chứa logic type-check riêng.

Formatter không được tự xây parser khác compiler.

Package manager không được quyết định semantics của ngôn ngữ.

Nguyên tắc:

```text
One compiler frontend
One semantic engine
One IR
Many consumers
```

Các công cụ dùng chung semantic database của compiler.

---

# 434.2 — CLI Root

Executable chính:

```text
axiom
```

Cú pháp:

```text
axiom <command> [options] [arguments]
```

Các command chính:

```text
build
check
run
test
bench
fmt
doc
package
publish
clean
cache
lsp
inspect
version
target
```

Không yêu cầu người dùng nhớ hàng chục command cấp thấp.

---

# 434.3 — `axiom build`

Build project:

```bash
axiom build
```

Release:

```bash
axiom build --release
```

Target:

```bash
axiom build --target x86_64-linux
```

Artifact:

```bash
axiom build --artifact exe
```

Static library:

```bash
axiom build --artifact staticlib
```

Dynamic library:

```bash
axiom build --artifact dylib
```

WASM:

```bash
axiom build --target wasm32
```

---

# 434.4 — Build Output

Mặc định:

```text
build/
 ├── debug/
 ├── release/
 ├── cache/
 └── artifacts/
```

Artifact cuối cùng phải có tên xác định.

Ví dụ:

```text
myapp.exe
libmyapp.a
libmyapp.so
libmyapp.dylib
myapp.wasm
```

---

# 434.5 — `axiom check`

Chỉ kiểm tra:

```bash
axiom check
```

Không:

- machine-code emission;
- linker;
- executable generation.

Pipeline:

```text
parse
 → resolve
 → type check
 → ownership
 → comptime
 → layout
 → diagnostics
```

Điều này cho phép IDE và AI kiểm tra project rất nhanh.

---

# 434.6 — `axiom run`

```bash
axiom run
```

Build nếu cần rồi chạy executable.

Arguments:

```bash
axiom run -- arg1 arg2
```

Không được mơ hồ giữa compiler arguments và application arguments.

---

# 434.7 — `axiom test`

```bash
axiom test
```

Chạy test suite.

Hỗ trợ:

```bash
axiom test package
axiom test module
axiom test --filter parser
axiom test --failed
```

Test runner dùng metadata từ compiler thay vì parse source độc lập.

---

# 434.8 — `axiom bench`

Benchmark không thuộc `test` hoàn toàn vì semantics khác.

```bash
axiom bench
```

Có thể chạy:

```bash
axiom bench --filter hashmap
```

Compiler phải hỗ trợ:

```text
release optimization
warmup
repetition
statistical aggregation
```

Nhưng benchmark framework chi tiết nằm ở standard library/tooling layer.

---

# 434.9 — `axiom fmt`

```bash
axiom fmt
```

Kiểm tra nhưng không sửa:

```bash
axiom fmt --check
```

Một file:

```bash
axiom fmt src/main.ax
```

Formatter phải:

```text
deterministic
canonical
idempotent
AST-aware
comment-preserving
```

---

# 434.10 — Formatter Invariant

Phải thỏa:

```text
format(format(source)) == format(source)
```

Formatter không được thay đổi semantics.

Không format dựa trên heuristic text replacement.

---

# 434.11 — `axiom doc`

```bash
axiom doc
```

Sinh documentation từ:

```text
pub declarations
doc comments
attributes
type information
trait relationships
examples
```

Có thể sinh:

```text
HTML
Markdown
JSON API metadata
```

---

# 434.12 — `axiom package`

Các thao tác package:

```bash
axiom package check
axiom package build
axiom package install
axiom package remove
axiom package update
axiom package tree
```

Package manager phải sử dụng dependency graph của BOOTSTRAP-432.

---

# 434.13 — `axiom publish`

```bash
axiom publish
```

Publish package chỉ là packaging/distribution operation.

Compiler không phụ thuộc registry.

---

# 434.14 — `axiom clean`

```bash
axiom clean
```

Xóa build artifacts.

```bash
axiom clean --cache
```

xóa cache tương ứng.

---

# 434.15 — `axiom cache`

```bash
axiom cache info
axiom cache clean
axiom cache verify
axiom cache gc
```

Cache có content-addressed identity.

Không được xóa artifact đang được sử dụng bởi process build khác.

---

# 434.16 — `axiom lsp`

```bash
axiom lsp
```

Chạy Language Server Protocol server qua stdio.

Editor không cần biết compiler internals.

---

# 434.17 — `axiom inspect`

Đây là command rất quan trọng cho compiler development và AI.

Ví dụ:

```bash
axiom inspect ast src/main.ax
axiom inspect hir src/main.ax
axiom inspect mir src/main.ax
axiom inspect asm src/main.ax
axiom inspect obj build/app.o
axiom inspect symbols build/app
axiom inspect sections build/app
axiom inspect abi build/app
```

---

# 434.18 — IR Inspection

Cho phép:

```bash
axiom inspect ir
```

Output có thể:

```text
text
json
```

AI agent có thể đọc JSON.

Ví dụ conceptual:

```json
{
  "function": "main",
  "return_type": "i32",
  "blocks": 1,
  "instructions": [...]
}
```

---

# 434.19 — Machine-Code Inspection

Compiler phải cung cấp disassembler nội bộ cho các ISA mà Axiom hỗ trợ.

```bash
axiom inspect asm binary
```

Không phụ thuộc bắt buộc vào:

```text
objdump
llvm-objdump
ndisasm
```

Third-party tools có thể được sử dụng tùy chọn bên ngoài, nhưng Axiom phải tự kiểm tra artifact cơ bản.

---

# 434.20 — Symbol Inspection

```bash
axiom inspect symbols app.exe
```

Hiển thị:

```text
symbol
address
size
binding
visibility
section
type
```

---

# 434.21 — Section Inspection

```bash
axiom inspect sections app.exe
```

Ví dụ:

```text
.text
.rodata
.data
.bss
.rdata
.reloc
```

phụ thuộc target.

---

# 434.22 — ABI Inspection

```bash
axiom inspect abi
```

Có thể hiển thị:

```text
target
architecture
pointer size
endianness
calling convention
stack alignment
register ABI
aggregate ABI
```

Rất hữu ích khi debug FFI.

---

# 434.23 — Diagnostic Architecture

Diagnostic subsystem độc lập:

```text
DiagnosticEngine
 ├── Diagnostic
 ├── Span
 ├── Label
 ├── Note
 ├── Help
 ├── FixIt
 └── RelatedDiagnostic
```

---

# 434.24 — Diagnostic Severity

Có:

```text
error
warning
info
hint
```

Compiler có thể cấu hình warning thành error:

```bash
axiom build --deny warnings
```

---

# 434.25 — Stable Error Codes

Mỗi diagnostic compiler-facing có mã:

```text
E430001
E434001
...
W434001
```

Không được dùng message text làm machine identity.

Message có thể thay đổi.

Error code phải ổn định theo edition/major compatibility policy.

---

# 434.26 — Source Span

Diagnostic phải xác định chính xác:

```text
file
start byte
end byte
line
column
```

UTF-8 được xử lý đúng.

Compiler nội bộ nên dùng byte offsets làm canonical representation.

---

# 434.27 — Diagnostic Example

Ví dụ:

```text
error[E430021]: cannot use moved value `buffer`
  --> src/main.ax:18:9
   |
16 |     send(buffer)
   |          ------ value moved here
17 |
18 |     print(buffer)
   |           ^^^^^^ value used after move
   |
help: clone the value before sending if both uses are required
```

Diagnostic phải phân biệt:

```text
primary error
secondary location
explanation
suggestion
```

---

# 434.28 — Fix-It

Compiler có thể đưa replacement:

```text
start
end
replacement
```

Ví dụ machine-readable:

```json
{
  "file": "src/main.ax",
  "start": 152,
  "end": 158,
  "replacement": "buffer.clone()"
}
```

IDE có thể áp dụng tự động.

---

# 434.29 — JSON Diagnostics

```bash
axiom check --diagnostic-format=json
```

Output phải là structured records.

Không trộn:

```text
progress
logs
diagnostics
```

vào cùng stdout.

---

# 434.30 — Diagnostic Streams

Quy ước:

```text
stdout = machine result / normal output
stderr = diagnostics/logs
```

Machine JSON mode phải giữ stdout parseable.

---

# 434.31 — Exit Codes

Một bộ mã tối thiểu:

```text
0 = success
1 = compilation/build failure
2 = command usage error
3 = configuration/target error
4 = package/dependency failure
5 = test failure
6 = internal compiler failure
```

Không được phụ thuộc vào OS-specific exit codes nếu không cần.

---

# 434.32 — Internal Compiler Error

ICE phải có:

```text
compiler version
target
phase
diagnostic ID
source context
stack/backtrace nếu debug
reproduction information
```

Ví dụ:

```text
internal compiler error[ICE-0012]
phase: MIR lowering
```

---

# 434.33 — ICE Reproduction

Compiler cung cấp:

```bash
axiom bugreport
```

Tạo bundle:

```text
compiler version
target
flags
package manifest
relevant source
diagnostic
IR snapshot
```

Nhưng phải loại bỏ secret/environment variables.

---

# 434.34 — Reproducibility

Build phải hỗ trợ:

```text
reproducible build
```

Cùng:

```text
source
dependencies
compiler
target
configuration
```

→ cùng semantic artifact.

Timestamp ngẫu nhiên không được nhúng vào binary.

---

# 434.35 — Build ID

Artifact có thể có:

```text
semantic build ID
```

Hash từ:

```text
source graph
dependency graph
compiler version
language edition
target
compiler options
comptime inputs
```

---

# 434.36 — Incremental Compilation

Compiler cache theo đơn vị semantic.

Không chỉ:

```text
file timestamp
```

mà dựa trên content/dependency identity.

Ví dụ:

```text
source hash
AST hash
declaration hash
type/signature hash
IR hash
codegen hash
```

---

# 434.37 — Dependency-Aware Incremental Build

Nếu thay đổi implementation nhưng không đổi public ABI:

```text
dependent package
```

không nhất thiết phải compile lại toàn bộ.

Nếu thay đổi:

```text
public type
public function signature
trait contract
ABI
const generic interface
```

dependent nodes có thể bị invalidated.

---

# 434.38 — Compilation Units

Đơn vị cache có thể là:

```text
module
declaration
generic instantiation
comptime result
IR function
object section
```

Không bắt buộc compile nguyên package mỗi lần.

---

# 434.39 — Generic Cache

Monomorphized generic:

```text
Vec<i32>
Vec<f64>
Vec<MyStruct>
```

được cache độc lập.

Key:

```text
generic definition hash
type argument hash
const argument hash
target ABI
optimization configuration
```

---

# 434.40 — Comptime Cache

Kết quả comptime từ BOOTSTRAP-431 được cache riêng.

Key phải bao gồm:

```text
comptime function hash
input values
type information
compiler version
target-sensitive inputs
```

---

# 434.41 — Parallel Compilation

Compiler phải tận dụng CPU cores.

Dependency graph:

```text
A ──┐
B ──┼──> D
C ──┘
```

A/B/C có thể compile song song.

D chờ dependencies.

---

# 434.42 — Deterministic Parallelism

Thứ tự thread execution không được ảnh hưởng:

```text
symbol ordering
diagnostic ordering
artifact content
cache identity
```

Nếu nhiều diagnostic độc lập:

```text
sort by source position + diagnostic code
```

---

# 434.43 — Compiler Daemon

Có thể:

```bash
axiom daemon
```

Daemon giữ:

```text
AST
semantic database
type tables
dependency graph
cache metadata
```

trong memory.

Mục tiêu:

```text
fast LSP
fast check
fast incremental rebuild
```

---

# 434.44 — Watch Mode

```bash
axiom build --watch
```

Theo dõi source/dependencies.

Không được biến watch mode thành một compiler khác.

---

# 434.45 — LSP Architecture

LSP sử dụng:

```text
DocumentStore
SemanticDatabase
DiagnosticEngine
SymbolIndex
BuildGraph
```

Không parse lại bằng implementation riêng.

---

# 434.46 — LSP Completion

Hỗ trợ:

```text
variables
functions
struct fields
methods
traits
generic parameters
modules
imports
keywords
attributes
```

Completion phải dựa trên semantic context.

---

# 434.47 — LSP Hover

Hover hiển thị:

```text
type
signature
documentation
generic constraints
ownership information nếu hữu ích
ABI information khi yêu cầu
```

---

# 434.48 — Go To Definition

Hỗ trợ:

```text
function
struct
enum
trait
type alias
constant
module
field
method
```

---

# 434.49 — Find References

Index semantic symbol identity, không tìm text đơn thuần.

---

# 434.50 — Rename

Rename phải semantic.

Ví dụ:

```text
Foo::value
```

không được đổi nhầm:

```text
Other::value
```

---

# 434.51 — Signature Help

Hiển thị:

```text
fn open(path: StringView, mode: OpenMode) -> Result<File, Error>
```

và parameter hiện tại.

---

# 434.52 — Semantic Tokens

Hỗ trợ phân biệt:

```text
type
function
method
field
variable
constant
trait
enum
module
generic parameter
macro/comptime entity
```

---

# 434.53 — Code Actions

Compiler/LSP có thể cung cấp:

```text
add import
qualify ambiguous method
apply fix-it
generate trait implementation
generate missing match arms
derive implementation
```

---

# 434.54 — Generate Trait Implementation

Ví dụ IDE có thể phát hiện:

```text
trait Eq for MyType
```

và sinh skeleton:

```text
impl Eq for MyType {
    ...
}
```

---

# 434.55 — Exhaustiveness Code Action

Nếu:

```text
match value {
    Some(x) => ...
}
```

thiếu `None`, IDE có thể tạo branch.

---

# 434.56 — LSP Workspace Symbols

Cho phép:

```text
search function
search type
search trait
search module
```

toàn workspace.

---

# 434.57 — AI Semantic Interface

Axiom phải cung cấp machine-readable semantic API.

Mục tiêu:

```text
AI agent
   ↓
compiler semantic database
   ↓
AST/HIR/types/symbols/diagnostics
```

thay vì AI phải đọc hàng nghìn dòng source để hiểu một symbol.

---

# 434.58 — AI Query

CLI có thể hỗ trợ:

```bash
axiom query symbol Foo
axiom query type Foo
axiom query references Foo
axiom query callers Foo
axiom query implements Foo
axiom query diagnostics
```

---

# 434.59 — Machine Semantic Output

Ví dụ:

```bash
axiom query symbol Foo --json
```

trả về:

```json
{
  "kind": "struct",
  "name": "Foo",
  "module": "app.core",
  "visibility": "pub",
  "fields": [],
  "methods": [],
  "traits": []
}
```

---

# 434.60 — AI Build Interface

```bash
axiom build --json
```

phải cung cấp:

```text
status
artifacts
errors
warnings
cache hits
cache misses
duration
target
```

---

# 434.61 — AI Test Interface

```bash
axiom test --json
```

Ví dụ:

```json
{
  "passed": 42,
  "failed": 1,
  "ignored": 2,
  "duration_ms": 183
}
```

AI agent không phải parse human-readable text.

---

# 434.62 — AI Task Recovery

Compiler output nên xác định:

```text
what failed
where
why
possible fix
affected dependency
```

Điều này phù hợp với workflow autonomous agent của Axiom.

---

# 434.63 — Structured Compiler State

Compiler có thể xuất:

```bash
axiom status --json
```

gồm:

```text
project
target
compiler
edition
dependency graph
dirty nodes
cache
diagnostics
```

---

# 434.64 — No AI-Specific Language Semantics

AI tooling không được làm thay đổi semantics.

Ví dụ:

```text
AI mode
```

không được tạo implicit conversion khác.

AI chỉ là consumer của semantic information.

---

# 434.65 — Configuration

Project config nằm trong:

```text
axiom.toml
```

Các setting chính:

```text
package
target
profile
dependencies
features
compiler options
```

Không nhúng machine-specific absolute paths nếu không cần.

---

# 434.66 — Profiles

Tối thiểu:

```text
dev
release
```

Có thể:

```text
test
bench
sanitize
coverage
```

---

# 434.67 — Optimization Profiles

Release có:

```text
optimize = speed
optimize = size
optimize = balanced
```

Compiler vẫn phải giữ semantics giống nhau.

---

# 434.68 — Debug Information

Hỗ trợ:

```text
none
line
full
```

Debug information không được làm thay đổi chương trình.

---

# 434.69 — Sanitizer Integration

Toolchain có thể cung cấp:

```text
address
memory
thread
undefined-behavior
```

nhưng sanitizer runtime là component tùy chọn.

Không biến sanitizer thành runtime mặc định.

---

# 434.70 — Cross Compilation

```bash
axiom build --target aarch64-linux
```

Compiler architecture:

```text
Frontend
   ↓
Target-independent IR
   ↓
Target lowering
   ↓
Machine encoder
   ↓
Object writer
   ↓
Axiom linker
```

Không cần host compiler.

---

# 434.71 — Target Query

```bash
axiom target list
axiom target info x86_64-linux
```

Target info phải machine-readable.

---

# 434.72 — Toolchain Self-Description

```bash
axiom version
```

hiển thị:

```text
compiler
frontend
backend
language edition
host
target defaults
```

---

# 434.73 — Compiler Editions

Language có edition:

```text
axiom 1
axiom 2
...
```

Edition không đồng nghĩa compiler version.

Mục tiêu cho phép syntax/semantic evolution có kiểm soát.

---

# 434.74 — Compatibility

Compiler mới có thể compile project edition cũ.

Breaking changes phải thuộc edition mới hoặc explicit migration.

---

# 434.75 — Migration Tool

```bash
axiom migrate
```

Có thể áp dụng:

```text
syntax migrations
deprecated API migrations
edition migrations
```

Migration phải dựa trên AST/semantic transformation, không regex.

---

# 434.76 — Package Tree

```bash
axiom package tree
```

Hiển thị dependency graph:

```text
app
├── core
├── image
│   └── math
└── net
```

---

# 434.77 — Dependency Diagnostics

Ví dụ:

```text
dependency cycle
version conflict
missing package
unsupported target
feature conflict
```

phải có error code riêng.

---

# 434.78 — Offline Mode

```bash
axiom build --offline
```

Không truy cập registry/network.

Chỉ dùng dependency cache/local sources.

---

# 434.79 — Locked Dependencies

Lockfile bảo đảm dependency resolution deterministic.

Ví dụ:

```text
axiom.lock
```

---

# 434.80 — Package Security Boundary

Compiler không được tự động thực thi:

```text
arbitrary package build code
```

Build scripts nếu tồn tại phải là một capability rõ ràng.

Điều này liên kết trực tiếp với BOOTSTRAP-431: `comptime` không có filesystem/network/process access mặc định.

---

# 434.81 — Documentation Comments

Syntax:

```text
/// Calculate vector length.
fn length(self: Vec2) -> f32 {
    ...
}
```

Documentation parser dùng AST.

---

# 434.82 — Source Examples

Doc examples có thể được compile/test.

Ví dụ:

```text
/// Example:
/// ```axiom
/// let ...
/// ```
```

Không nên chỉ render text.

---

# 434.83 — Test Discovery

Test runner tìm test thông qua compiler metadata.

Không dùng reflection runtime bắt buộc.

---

# 434.84 — Test Attributes

Concept:

```text
@test
fn test_add() {
    ...
}
```

Có thể:

```text
@ignore
@should_panic
@timeout(...)
```

---

# 434.85 — Test Isolation

Test runner có thể chạy:

```text
in-process
separate process
```

Tùy loại test.

System/integration tests nên có process isolation khi cần.

---

# 434.86 — Test Parallelism

Các test độc lập được chạy song song.

Test có resource conflict phải khai báo/được scheduler xử lý.

Không implicit global locking.

---

# 434.87 — Build Logging

Các mức:

```text
quiet
normal
verbose
debug
trace
```

---

# 434.88 — Timing Information

Verbose mode có thể hiển thị:

```text
parse: 12ms
typecheck: 21ms
comptime: 3ms
MIR: 8ms
codegen: 14ms
link: 5ms
```

Rất hữu ích để tối ưu compiler.

---

# 434.89 — Cache Statistics

```bash
axiom build --verbose
```

có thể hiển thị:

```text
cache hits: 187
cache misses: 12
recompiled: 4 modules
```

---

# 434.90 — Compiler Performance

Compiler itself phải được thiết kế để:

```text
parallel
incremental
cache-friendly
memory-efficient
```

Không hy sinh quá nhiều compile-time để phục vụ những tính năng tooling hiếm dùng.

---

# 434.91 — Error Recovery

Parser phải cố gắng tiếp tục sau lỗi.

Ví dụ thiếu:

```text
}
```

không nên làm mất toàn bộ semantic diagnostics phía sau.

---

# 434.92 — Cascading Error Suppression

Nếu một lỗi gốc khiến 100 lỗi phụ xuất hiện, compiler nên giảm diagnostics không hữu ích.

Ví dụ:

```text
unknown type Foo
```

không cần phát sinh hàng chục lỗi "cannot infer type Foo".

---

# 434.93 — Diagnostic Ranking

Không phải ranking chính trị hay đánh giá người dùng; đây là thứ tự kỹ thuật.

Compiler ưu tiên:

```text
root-cause
source-order
severity
```

---

# 434.94 — Parser Recovery Synchronization

Synchronization tokens:

```text
}
)
]
;
declaration keywords
```

được dùng để phục hồi parser.

---

# 434.95 — Source Map

Compiler giữ source mappings:

```text
AST
→ HIR
→ MIR
→ machine instruction
```

để debugger và diagnostics có thể truy ngược source.

---

# 434.96 — Debugger Integration

Axiom không cần tự viết debugger hoàn chỉnh.

Nhưng compiler phải sinh debug information tương thích với platform debugger.

Mục tiêu:

```text
GDB
LLDB
Windows debugger
```

có thể được hỗ trợ thông qua debug formats chuẩn.

---

# 434.97 — Native Debug Formats

Target backend có thể emit:

```text
DWARF
CodeView/PDB-related data
```

tùy platform.

Compiler không phụ thuộc debugger để build executable.

---

# 434.98 — Artifact Metadata

Artifact có thể chứa metadata tối thiểu:

```text
compiler version
language edition
target
build ID
```

Không bắt buộc nhúng toàn bộ source.

---

# 434.99 — Privacy

Không được mặc định nhúng:

```text
absolute source paths
username
hostname
environment variables
```

nếu không cần cho debug.

---

# 434.100 — Path Remapping

Hỗ trợ:

```bash
--remap-path-prefix
```

để reproducible build.

---

# 434.101 — Compiler Frontend API

Nội bộ nên có API:

```text
parse()
resolve()
type_check()
ownership_check()
const_eval()
lower()
```

Các API này dùng chung bởi:

```text
compiler
LSP
IDE
formatter
AI tooling
```

---

# 434.102 — Semantic Database

Một semantic database thống nhất:

```text
Source
 ↓
Syntax
 ↓
Declarations
 ↓
Types
 ↓
Traits
 ↓
Ownership
 ↓
Comptime
 ↓
IR
```

LSP query vào database này.

---

# 434.103 — Stable Symbol IDs

Mỗi declaration có semantic identity.

Không dùng source line làm ID.

Ví dụ:

```text
SymbolId = hash(package + module + declaration identity)
```

Có versioning/invalidation phù hợp.

---

# 434.104 — Stable Type IDs

Type interning từ BOOTSTRAP-430 được expose cho tooling.

```text
TypeId
```

cho phép AI/IDE hỏi:

```text
what is this expression's type?
```

---

# 434.105 — Ownership Query

Tooling có thể hỏi:

```text
is this value moved?
is this value owned?
where is it dropped?
```

Đây là semantic information, không phải runtime instrumentation.

---

# 434.106 — Allocation Query

Compiler có thể cung cấp thông tin:

```text
allocates
may_allocate
no_alloc
```

nếu analysis đủ chắc chắn.

---

# 434.107 — Blocking Query

Tương tự:

```text
blocks
may_block
no_block
```

hữu ích cho async/concurrency tooling.

---

# 434.108 — Unsafe Query

AI/IDE có thể tìm:

```text
unsafe blocks
unsafe functions
raw pointer operations
FFI boundaries
```

---

# 434.109 — ABI Query

Tooling có thể hỏi:

```text
what ABI does this function use?
what is its parameter layout?
what registers are involved?
```

Đặc biệt hữu ích khi xây FFI.

---

# 434.110 — Build Graph Query

```bash
axiom query graph --json
```

trả:

```text
packages
modules
dependencies
generated nodes
artifacts
```

---

# 434.111 — Dependency Impact Query

```bash
axiom query impact Foo
```

cho biết các module có thể bị invalidated nếu declaration `Foo` thay đổi.

---

# 434.112 — Codegen Report

```bash
axiom inspect codegen Foo
```

có thể hiển thị:

```text
IR
register allocation
stack frame
instruction count
branches
calls
```

Không phải tất cả backend phải expose mọi chi tiết ngay từ bootstrap.

---

# 434.113 — Size Report

```bash
axiom inspect size app
```

Ví dụ:

```text
.text   12.4 KB
.rodata 3.1 KB
.data   1.2 KB
.bss    0.8 KB
```

---

# 434.114 — Dependency Size Report

Có thể xác định component nào kéo binary size tăng.

```bash
axiom inspect size --tree
```

Điều này phù hợp mục tiêu binary nhỏ của Axiom.

---

# 434.115 — Linker Map

```bash
axiom inspect linkmap app
```

Hiển thị:

```text
symbol
section
address
size
object source
```

---

# 434.116 — Dead Code Report

Compiler/linker có thể báo:

```text
removed 134 unused functions
removed 8 unused sections
```

chỉ trong verbose/inspect mode.

---

# 434.117 — Compile Command Database

Có thể sinh:

```text
compile_commands.json
```

để hỗ trợ ecosystem tools.

Nhưng đây không phải input canonical của compiler.

---

# 434.118 — Environment Isolation

Build phải có cách xác định:

```text
target
host
environment
features
```

Không đọc tùy tiện environment variables làm thay đổi binary.

---

# 434.119 — Explicit Environment Inputs

Nếu build cần environment:

```text
axiom build --env NAME=value
```

hoặc build-system capability tương ứng.

Input đó phải được đưa vào build identity.

---

# 434.120 — Build Script Boundary

Build script nếu được hỗ trợ:

```text
build tool
```

không phải:

```text
comptime
```

Build script có thể:

```text
generate files
probe platform
invoke external tools
```

nhưng phải được đánh dấu là external build phase.

---

# 434.121 — Comptime Purity Boundary

Comptime:

```text
deterministic
sandboxed
no arbitrary external effects
```

Build script:

```text
external
capability-based
potentially nondeterministic
```

Hai hệ thống không được trộn.

---

# 434.122 — Toolchain Self-Hosting

Mục tiêu cuối:

```text
Axiom compiler
written in Axiom
```

nhưng bootstrap compiler ban đầu có thể được viết bằng implementation language tạm thời.

Sau self-hosting, compiler không cần:

```text
LLVM
GCC
Clang
```

để tạo native artifact.

---

# 434.123 — Bootstrap Toolchain

Có thể tồn tại:

```text
axiom-bootstrap
```

nhưng nó phải dần được thay thế bởi:

```text
axiom
```

self-hosted.

---

# 434.124 — Compiler Components

Kiến trúc implementation:

```text
axiom-driver
axiom-lexer
axiom-parser
axiom-semantic
axiom-ir
axiom-codegen
axiom-object
axiom-linker
axiom-tools
```

Có thể link thành một executable duy nhất.

---

# 434.125 — Single Binary Distribution

Người dùng có thể chỉ cần:

```text
axiom.exe
```

Không cần cài:

```text
LLVM
GCC
Clang
MSVC
```

cho native compilation cơ bản.

---

# 434.126 — Platform SDK Boundary

Một ngoại lệ quan trọng:

Axiom có thể cần platform SDK/API definitions để tạo ứng dụng OS-specific.

Ví dụ:

```text
Windows API
Linux system interfaces
Apple frameworks
Android NDK interfaces
```

Nhưng compiler không dùng compiler khác để emit machine code.

---

# 434.127 — External System Libraries

Nếu chương trình yêu cầu system library:

```text
libc
Win32
system frameworks
```

đó là dependency của application/platform, không phải dependency của Axiom compiler.

---

# 434.128 — Freestanding

Có thể:

```bash
axiom build --freestanding
```

Không:

```text
OS
libc
standard runtime
```

nếu source không yêu cầu chúng.

---

# 434.129 — Minimal Runtime

Một chương trình:

```text
fn main() -> i32 {
    42
}
```

phải có khả năng tạo executable với runtime tối thiểu.

Mục tiêu:

```text
startup
main
exit
```

không kéo toàn bộ std.

---

# 434.130 — Toolchain Capability Detection

```bash
axiom doctor
```

kiểm tra:

```text
compiler
targets
SDK
link capability
debug capability
cache
package registry
```

---

# 434.131 — `axiom doctor`

Output machine-readable:

```bash
axiom doctor --json
```

Không tự sửa hệ thống.

---

# 434.132 — No Hidden Network Access

Các command local như:

```text
check
build
test
fmt
```

không tự động truy cập Internet.

Network chỉ khi package/build operation yêu cầu.

---

# 434.133 — Offline-First Development

Project đã có dependency cache phải có thể:

```text
edit
check
build
test
```

offline.

---

# 434.134 — Lockfile Integrity

Nếu lockfile thay đổi ngoài ý muốn, package manager phải báo.

---

# 434.135 — Package Verification

Package có thể có:

```text
checksum
signature
publisher metadata
```

nhưng trust model là package ecosystem layer, không phải compiler semantics.

---

# 434.136 — Tool Version Pinning

Project có thể yêu cầu compiler version range.

Ví dụ conceptual:

```text
axiom = "1.x"
edition = "1"
```

---

# 434.137 — Compiler Version Compatibility

Compiler phải phân biệt:

```text
language edition
compiler release
package version
ABI version
```

Không dùng một version number cho tất cả.

---

# 434.138 — ABI Version

Public binary interfaces có thể ghi:

```text
ABI version
```

để tránh load library không tương thích.

---

# 434.139 — Plugin Boundary

Axiom compiler core không phụ thuộc plugin để compile language.

Plugin chỉ có thể mở rộng:

```text
IDE
documentation
lint
analysis
package tooling
```

nếu ABI/plugin API ổn định.

---

# 434.140 — Linter Boundary

Lint không thuộc type checker core trừ các diagnostic cần thiết cho correctness.

Ví dụ:

```text
unused variable
style issue
suspicious code
```

có thể là lint.

---

# 434.141 — Compiler Warning

Warnings phải deterministic.

Không phụ thuộc thứ tự hash-map iteration.

---

# 434.142 — Warning Configuration

Có thể:

```text
allow
warn
deny
```

theo:

```text
global
module
declaration
```

---

# 434.143 — Attributes

Ví dụ:

```text
@allow(unused)
@deny(...)
```

nhưng phải tránh hệ thống attribute trở thành DSL phức tạp.

---

# 434.144 — Formatter Configuration

Canonical formatter nên có rất ít configuration.

Mục tiêu:

```text
same source → same format
```

không tạo ra "format wars".

---

# 434.145 — Import Formatting

Formatter có thể sắp xếp imports deterministic:

```text
std
external
workspace
local
```

theo quy tắc cố định.

---

# 434.146 — Documentation Index

Doc generator xây:

```text
symbol index
module hierarchy
trait relationships
type links
source links
```

---

# 434.147 — Searchable Documentation

Generated docs phải có:

```text
search
cross references
source locations
signature
examples
```

---

# 434.148 — Compiler Help

```bash
axiom --help
axiom build --help
```

Help phải ngắn, có ví dụ và không liệt kê mọi internal flag mặc định.

---

# 434.149 — Experimental Flags

Flag thử nghiệm:

```text
-Z...
```

hoặc namespace tương đương.

Không được coi là stable API.

---

# 434.150 — Internal Flags

Internal/debug options phải được tách khỏi public CLI.

Ví dụ:

```text
--dump-hir
--dump-mir
--trace-typecheck
```

có thể thuộc developer/debug mode.

---

# 434.151 — Stable CLI Contract

Các command và JSON schema được coi là public interface.

Nếu thay đổi breaking phải version hóa.

---

# 434.152 — JSON Schema Version

Machine output có:

```json
{
  "schema_version": 1
}
```

---

# 434.153 — AI-Friendly Error Contract

AI không nên phải đoán:

```text
error message
```

để biết lỗi.

Structured diagnostic có:

```text
code
severity
phase
span
symbol
expected
actual
fixes
notes
```

khi thông tin có sẵn.

---

# 434.154 — Semantic Difference

Ví dụ type mismatch:

```json
{
  "code": "E430021",
  "kind": "type_mismatch",
  "expected": "i32",
  "actual": "String",
  "span": {...}
}
```

Đây là mục tiêu đặc biệt quan trọng cho Axiom AI workflow.

---

# 434.155 — No Natural-Language Parsing Dependency

Agent/tooling không cần parse:

```text
"expected i32 but found String"
```

để xác định semantics.

---

# 434.156 — Compiler Event Stream

Optional:

```bash
axiom build --events=json
```

Event:

```text
parse-start
parse-end
compile-start
cache-hit
cache-miss
codegen
link
artifact
```

Hữu ích cho IDE/CI/AI.

---

# 434.157 — Progress UI

Human CLI có thể hiển thị progress.

Machine mode không được trộn progress vào JSON output.

---

# 434.158 — CI Mode

```bash
axiom build --ci
```

tắt:

```text
interactive prompts
ANSI decoration nếu cần
non-deterministic progress
```

---

# 434.159 — Noninteractive Default

Compiler không được hỏi:

```text
"Continue? [Y/n]"
```

trong build.

Đặc biệt phù hợp autonomous agent.

---

# 434.160 — Agent-Friendly Failure

Khi build thất bại:

```text
1. error
2. exact source location
3. structured reason
4. dependency impact
5. suggested fixes
```

rồi process exit.

Không chờ người dùng.

---

# 434.161 — Autonomous Build Loop

AI agent có thể:

```text
edit
→ axiom check --json
→ inspect diagnostics
→ edit
→ axiom test --json
→ axiom build --json
```

mà không cần human interaction.

---

# 434.162 — No Hidden State

Build result không được phụ thuộc:

```text
random cache state
IDE state
previous process memory
```

ngoài cache hit/miss.

---

# 434.163 — Cache Corruption Recovery

Nếu cache artifact invalid:

```text
verify
→ invalidate
→ rebuild
```

Không làm hỏng source build.

---

# 434.164 — Compiler Crash Recovery

Daemon crash không được làm project unusable.

Build graph/cache phải recover được.

---

# 434.165 — File Locking

Concurrent compiler processes phải có lock nhẹ cho:

```text
cache writes
artifact writes
lockfile updates
```

---

# 434.166 — Atomic Artifact Writes

Compiler ghi:

```text
temporary artifact
→ fsync nếu policy yêu cầu
→ atomic rename
```

để tránh artifact half-written.

---

# 434.167 — Interrupted Build

Ctrl+C:

```text
terminate current build
preserve valid cache
remove incomplete artifacts
```

---

# 434.168 — Signal Handling

Platform layer xử lý:

```text
SIGINT
SIGTERM
```

và tương đương Windows.

---

# 434.169 — Tooling Memory Model

LSP/daemon có thể giữ semantic cache lâu dài.

Nhưng semantic cache không được ảnh hưởng compiler correctness.

---

# 434.170 — Toolchain Layering

Kiến trúc cuối:

```text
axiom CLI
    │
    ├── project/build manager
    │
    ├── semantic engine
    │
    ├── IR
    │
    ├── backend
    │
    ├── object writer
    │
    └── linker
```

LSP:

```text
LSP
 ↓
semantic engine
```

AI:

```text
AI
 ↓
structured tooling API
 ↓
semantic engine
```

---

# 434.171 — Tooling Does Not Duplicate Compiler Logic

Không được có:

```text
LSP type checker
Formatter parser
AI parser
```

riêng biệt.

Một grammar.

Một semantic model.

---

# 434.172 — Performance Target

Mục tiêu tooling:

```text
LSP response: interactive
incremental check: fast
formatter: near-linear
symbol query: indexed
full build: parallel
```

Không đặt con số cứng trước benchmark thực tế.

---

# 434.173 — Toolchain Testability

Mọi command phải có test:

```text
CLI
diagnostic
JSON
exit code
cache
incremental
LSP
formatter
package
```

---

# 434.174 — Golden Diagnostics

Diagnostic test lưu:

```text
source
expected diagnostic code
span
message structure
fix-it
```

Không nên khóa cứng toàn bộ whitespace của human message nếu không cần.

---

# 434.175 — Formatter Golden Tests

Input:

```text
unformatted source
```

Expected:

```text
canonical source
```

và test idempotence.

---

# 434.176 — LSP Golden Tests

Các request:

```text
completion
hover
definition
references
rename
code action
```

có expected structured result.

---

# 434.177 — CLI Golden Tests

Test:

```text
stdout
stderr
exit code
filesystem result
```

---

# 434.178 — Toolchain Security

Compiler phải tránh:

```text
path traversal
unsafe cache extraction
malicious package metadata
unbounded diagnostic output
```

---

# 434.179 — Resource Limits

Tooling có thể giới hạn:

```text
diagnostic count
file size
package graph size
comptime resources
LSP request duration
```

---

# 434.180 — LSP Cancellation

LSP request phải hỗ trợ cancellation.

Ví dụ user gõ tiếp:

```text
completion request A
```

request A có thể bị hủy khi:

```text
completion request B
```

xuất hiện.

---

# 434.181 — Semantic Snapshot

LSP query hoạt động trên snapshot immutable.

Điều này tránh race:

```text
edit source
+
query old semantic state
```

---

# 434.182 — Incremental Semantic Snapshot

Chỉ invalidated nodes được recompute.

---

# 434.183 — AI Snapshot

AI agent có thể yêu cầu:

```bash
axiom snapshot --json
```

để lấy semantic state tại một build point xác định.

---

# 434.184 — Project Manifest Metadata

Manifest có thể chứa:

```text
language edition
minimum compiler
targets
features
dependencies
license
authors
documentation
```

---

# 434.185 — No Central Registry Requirement

Axiom package ecosystem hỗ trợ:

```text
local
path
git
registry
archive
```

Không khóa language vào một server duy nhất.

---

# 434.186 — Package Reproducibility

Package source distribution phải có:

```text
manifest
lock metadata
source hashes
dependency hashes
```

---

# 434.187 — Build Artifact Identity

Artifact identity:

```text
Package
+ Version
+ SourceHash
+ DependencyHash
+ Target
+ Profile
+ Compiler
```

---

# 434.188 — Artifact Cache

Có thể cache:

```text
source → IR
IR → object
objects → executable
```

nhưng final linking phải kiểm tra tất cả inputs.

---

# 434.189 — Link Cache

Nếu:

```text
objects unchanged
link configuration unchanged
```

link result có thể reuse.

---

# 434.190 — Thin Rebuild

Thay đổi một function:

```text
function
→ affected object section
→ relink
```

thay vì rebuild mọi thứ.

---

# 434.191 — Whole-Program Optimization

Có thể bật:

```bash
axiom build --lto
```

Nhưng LTO là optimization layer, không thay đổi language semantics.

---

# 434.192 — Link-Time Optimization

IR có thể được giữ đủ thông tin cho:

```text
inlining
devirtualization
dead code elimination
constant propagation
specialization
```

---

# 434.193 — Toolchain Artifact Matrix

Một package có thể build:

```text
Windows x64
Linux x64
Linux ARM64
macOS ARM64
macOS x64
Android ARM64
iOS ARM64
WASM
```

từ cùng source khi APIs hỗ trợ target.

---

# 434.194 — Target Capability Diagnostics

Nếu source dùng:

```text
std::net
```

nhưng target freestanding không có network:

```text
E... target capability unavailable
```

không phải linker crash.

---

# 434.195 — Capability Query

Compiler/AI có thể hỏi:

```bash
axiom target info wasm32 --json
```

và nhận:

```text
threads: false
filesystem: false
simd: true
atomics: ...
```

---

# 434.196 — Toolchain Documentation Contract

Mọi public CLI command phải có:

```text
purpose
syntax
options
exit codes
examples
machine-readable behavior
```

---

# 434.197 — Minimal Public CLI

**Stable initial command set:**

```text
build
check
run
test
bench
fmt
doc
package
clean
cache
lsp
inspect
target
version
```

Không thêm command chỉ vì "có thể hữu ích".

---

# 434.198 — Developer Experience Principle

Axiom phải cho cảm giác:

```text
install
→ create
→ edit
→ check
→ run
```

với số lượng khái niệm tối thiểu.

---

# 434.199 — AI Developer Experience Principle

AI phải có khả năng:

```text
inspect
→ understand
→ modify
→ check
→ test
→ build
```

bằng structured interfaces.

---

# 434.200 — Hard Invariants

BOOTSTRAP-434 khóa các invariant:

1. Một semantic engine dùng chung cho compiler/LSP/tooling.
2. CLI deterministic.
3. Diagnostics có stable error codes.
4. Diagnostics có source spans.
5. Có structured JSON output.
6. Exit codes ổn định.
7. Formatter canonical/idempotent.
8. Build incremental.
9. Build parallel.
10. Cache content-addressed.
11. Reproducible build được hỗ trợ.
12. Không hidden network trong build local.
13. Không hidden compiler dependency vào LLVM/GCC/Clang.
14. Native compiler tự emit machine code/object/link.
15. Cross compilation first-class.
16. LSP không duplicate semantic engine.
17. AI tooling dùng structured semantic data.
18. Build/test không interactive mặc định.
19. Comptime và external build scripts tách biệt.
20. Debug info tùy chọn.
21. Runtime không bị kéo vào chỉ vì tooling.
22. Freestanding build được hỗ trợ.
23. Package registry không bắt buộc.
24. Cache corruption phải recover được.
25. Interrupted build không phá cache hợp lệ.
26. Tooling không làm thay đổi language semantics.
27. Compiler version và language edition tách biệt.
28. ABI version được phân biệt với package version.
29. Machine-readable schema có version.
30. Không để CLI trở thành một DSL phức tạp.

**BOOTSTRAP-434 hoàn tất.**

---

# BOOTSTRAP-435 — TESTING, CONFORMANCE, VALIDATION, FUZZING, BENCHMARKING & COMPILER CORRECTNESS

**Trạng thái: LOCKED DESIGN**

435 là phần cực kỳ quan trọng trước khi chuyển sang các subsystem cấp cao. Axiom không thể chỉ có specification; phải có một **verification architecture** chứng minh compiler thực sự tuân thủ specification.

Mục tiêu:

```text
Specification
      ↓
Executable Tests
      ↓
Compiler
      ↓
Artifact
      ↓
Runtime Verification
```

Không chấp nhận:

```text
"compiler chạy được vài ví dụ"
```

là đủ.

---

# 435.1 — Verification Layers

Axiom có 8 tầng kiểm thử:

```text
1. Lexer tests
2. Parser tests
3. Semantic tests
4. IR/codegen tests
5. Object/linker tests
6. Runtime tests
7. End-to-end tests
8. Differential/property/fuzz testing
```

---

# 435.2 — Specification Is Executable

Mỗi phần spec quan trọng phải có:

```text
normative rule
→ test ID
→ executable test
```

Ví dụ:

```text
BOOTSTRAP-430
TYPE-017
```

---

# 435.3 — Test Taxonomy

Test ID thống nhất:

```text
LEX-xxx
PARSE-xxx
TYPE-xxx
OWN-xxx
CONST-xxx
IR-xxx
ABI-xxx
CODEGEN-xxx
OBJ-xxx
LINK-xxx
RUNTIME-xxx
LSP-xxx
CLI-xxx
FUZZ-xxx
PERF-xxx
```

---

# 435.4 — Conformance Suite

Có một suite:

```text
axiom-conformance
```

Mục tiêu kiểm tra language semantics độc lập với backend.

---

# 435.5 — Backend Conformance

Một chương trình đúng phải cho kết quả semantic tương đương trên:

```text
x86-64
AArch64
WASM
```

trừ behavior explicitly target-specific.

---

# 435.6 — Golden Tests

Golden test lưu:

```text
source
expected AST/diagnostics/IR/output
```

Không chỉ lưu binary vì binary có thể thay đổi do optimization implementation.

---

# 435.7 — Lexer Tests

Kiểm tra:

```text
identifiers
unicode
numbers
strings
characters
operators
comments
attributes
keywords
```

---

# 435.8 — Unicode Lexer Tests

Phải test:

```text
UTF-8 valid
UTF-8 invalid
Unicode identifier
NFC/NFD
combining characters
byte offsets
```

---

# 435.9 — Parser Tests

Test:

```text
valid syntax
invalid syntax
recovery
precedence
associativity
generics
patterns
attributes
```

---

# 435.10 — Formatter Tests

Mọi valid syntax phải có khả năng:

```text
parse
→ format
→ parse
```

và giữ semantic equivalence.

---

# 435.11 — Type Tests

Kiểm tra:

```text
inference
coercion
generics
traits
associated types
dyn Trait
arrays
slices
function types
casts
```

---

# 435.12 — Negative Type Tests

Các chương trình sai phải **thất bại đúng cách**.

Ví dụ:

```text
wrong argument type
unknown field
ambiguous method
invalid trait implementation
use moved value
```

---

# 435.13 — Ownership Tests

Test:

```text
move
copy
clone
drop
partial initialization
early return
defer
nested scopes
panic cleanup
```

---

# 435.14 — Ownership Runtime Tests

Không chỉ kiểm tra compiler diagnostics.

Test destructor thực sự chạy đúng:

```text
construct
move
scope exit
drop
```

---

# 435.15 — Double Drop Tests

Compiler phải ngăn trường hợp safe code có:

```text
double destruction
```

---

# 435.16 — Partial Initialization

Ví dụ:

```text
struct S {
    a: Resource
    b: Resource
}
```

Nếu `b` initialization fail:

```text
a → drop
b → không drop
```

---

# 435.17 — `defer` Tests

Kiểm tra thứ tự:

```text
defer A
defer B
```

phải deterministic.

---

# 435.18 — Panic Cleanup Tests

Nếu panic/unwind được bật:

```text
scope resources
→ cleanup
→ unwind
```

---

# 435.19 — Result Tests

Kiểm tra:

```text
Ok
Err
try propagation
error conversion
match
```

---

# 435.20 — Option Tests

Kiểm tra:

```text
Some
None
pattern matching
niche optimization
```

---

# 435.21 — Const Evaluation Tests

Kiểm tra:

```text
arithmetic
array generation
struct construction
match
type queries
trait queries
const generics
```

---

# 435.22 — Comptime Determinism

Cùng:

```text
source
inputs
target context
```

phải tạo cùng kết quả.

---

# 435.23 — Comptime Resource Limits

Test:

```text
infinite recursion
huge loop
huge allocation
excessive generated code
```

Compiler phải terminate có kiểm soát.

---

# 435.24 — Comptime Sandbox

Test rằng comptime không thể mặc định:

```text
read arbitrary file
network
spawn process
```

---

# 435.25 — Generic Tests

Test:

```text
generic function
generic struct
generic enum
generic trait
const generic
nested generic
```

---

# 435.26 — Monomorphization Tests

Đảm bảo:

```text
Vec<i32>
Vec<f32>
```

được instantiate đúng.

---

# 435.27 — Generic Deduplication Tests

Nếu hai instantiation có machine representation tương đương, compiler có thể deduplicate.

Test chỉ kiểm tra:

```text
semantic correctness
```

không khóa implementation optimization.

---

# 435.28 — Trait Tests

Kiểm tra:

```text
impl
default method
associated type
associated const
constraints
coherence
```

---

# 435.29 — Override Tests

Kiểm tra cơ chế đã khóa:

```text
trait default method
→ impl provides replacement
```

không cần class inheritance.

---

# 435.30 — Dynamic Trait Tests

Kiểm tra:

```text
dyn Trait
vtable
method dispatch
object safety
```

---

# 435.31 — Dispatch Correctness

Test:

```text
static dispatch
dynamic dispatch
```

cho cùng semantic result.

---

# 435.32 — ABI Test Suite

Mỗi supported ABI phải có golden tests.

```text
SYSV64
WIN64
AAPCS64
Apple AArch64
WASM
```

---

# 435.33 — ABI Argument Tests

Kiểm tra từng nhóm:

```text
integer
float
vector
small aggregate
large aggregate
nested aggregate
```

---

# 435.34 — ABI Return Tests

Kiểm tra:

```text
scalar return
aggregate return
sret
multiple register return
```

---

# 435.35 — ABI Stack Tests

Kiểm tra:

```text
alignment
stack args
callee/caller saved
red zone
shadow space
```

theo target.

---

# 435.36 — FFI Tests

Axiom ↔ C:

```text
Axiom caller → C function
C caller → Axiom function
```

---

# 435.37 — FFI Struct Tests

Kiểm tra:

```text
@repr(C)
alignment
padding
packed
enum representation
```

---

# 435.38 — FFI String Tests

Kiểm tra:

```text
UTF-8
CString
StringView
null termination
ownership
```

---

# 435.39 — Calling Convention Tests

Mỗi convention phải test:

```text
argument passing
return
stack cleanup
function pointer
variadic
```

nếu ABI hỗ trợ.

---

# 435.40 — Machine Encoder Tests

Mỗi ISA instruction encoding phải có:

```text
source instruction
expected bytes
```

---

# 435.41 — Decoder Round Trip

Nếu Axiom có decoder:

```text
instruction
→ encode
→ decode
→ equivalent instruction
```

---

# 435.42 — Relocation Tests

Kiểm tra:

```text
ABS
PCREL
branch
GOT
PLT
TLS
```

theo target.

---

# 435.43 — Object Writer Tests

ELF:

```text
headers
sections
symbols
relocations
```

PE/COFF:

```text
headers
sections
symbols
relocations
imports
exports
```

Mach-O tương tự.

---

# 435.44 — Linker Tests

Kiểm tra:

```text
symbol resolution
archive extraction
section layout
relocation
dead stripping
imports/exports
```

---

# 435.45 — Linker Error Tests

Phải báo đúng:

```text
undefined symbol
duplicate symbol
invalid relocation
unsupported ABI
architecture mismatch
```

---

# 435.46 — Native Smoke Tests

Test tối thiểu:

```text
main → return 42
```

cho mỗi target.

---

# 435.47 — Native Execution Tests

Pipeline:

```text
compile
→ link
→ execute
→ verify exit code
```

---

# 435.48 — Cross-Target Tests

CI phải có target matrix phù hợp với runner/cross execution strategy.

Không nhất thiết mọi target phải execute trên mọi host.

---

# 435.49 — WASM Tests

Kiểm tra:

```text
WASM module generation
exports
imports
memory
function calls
return values
```

---

# 435.50 — Runtime Tests

Kiểm tra:

```text
startup
allocator
panic
thread
TLS
IO
async
```

theo runtime component.

---

# 435.51 — Minimal Runtime Tests

Một binary:

```text
main → 42
```

không được vô tình link:

```text
network
filesystem
async
thread runtime
```

nếu không sử dụng.

---

# 435.52 — Binary Size Tests

Không đặt một số byte tuyệt đối quá sớm.

Theo dõi regression:

```text
baseline
current
delta
```

---

# 435.53 — Code Generation Tests

Test semantic output, không khóa register allocation nếu không cần.

Ví dụ:

```text
a + b
```

phải trả đúng kết quả dù backend dùng:

```text
add
lea
other legal sequence
```

---

# 435.54 — Assembly Golden Tests

Dùng cho các trường hợp backend cần kiểm soát chính xác:

```text
ABI
atomic
special instruction
relocation
prologue
```

---

# 435.55 — Optimization Tests

Mỗi optimization phải có:

```text
before
after
semantic equivalence
```

---

# 435.56 — Optimization Soundness

Optimization không được làm thay đổi behavior hợp lệ.

Ví dụ:

```text
constant folding
dead code elimination
inlining
loop optimization
bounds-check elimination
```

---

# 435.57 — Undefined Behavior Boundary

Test phải phân biệt:

```text
defined
implementation-defined
unspecified
undefined
```

không biến UB thành compiler crash.

---

# 435.58 — Unsafe Tests

Unsafe code được test riêng.

Compiler không cần chứng minh raw-pointer safety.

---

# 435.59 — Safe/Unsafe Boundary Tests

Kiểm tra:

```text
safe → unsafe
unsafe → safe
```

và các annotation/requirements.

---

# 435.60 — Concurrency Tests

Test:

```text
thread spawn
join
TLS
atomic
mutex
channel
```

---

# 435.61 — Atomic Tests

Mỗi operation:

```text
load
store
exchange
CAS
fetch_add
```

với memory ordering phù hợp.

---

# 435.62 — Memory Ordering Tests

Không chỉ test trên x86.

Cần target/runtime test trên kiến trúc có memory ordering khác biệt như AArch64.

---

# 435.63 — Race Tests

Race detector/debug runtime nếu có phải được test riêng.

Không dựa vào race detector để chứng minh compiler semantics.

---

# 435.64 — Async Tests

Kiểm tra:

```text
async function
await
suspend
resume
completion
cancellation
cleanup
```

---

# 435.65 — Async Allocation Tests

Kiểm tra async state machine không allocation khi compiler chứng minh object không escape.

---

# 435.66 — Cancellation Tests

Cancellation phải đảm bảo cleanup.

---

# 435.67 — Panic Tests

Test:

```text
panic=abort
panic=unwind
```

---

# 435.68 — Double Panic

Nếu destructor panic trong quá trình unwind:

```text
abort
```

theo BOOTSTRAP-425.

---

# 435.69 — Error Propagation Tests

`try` phải preserve:

```text
Ok
Err
error conversion
cleanup
```

---

# 435.70 — Pattern Matching Tests

Kiểm tra:

```text
enum
tuple
struct
OR pattern
range
guard
wildcard
```

---

# 435.71 — Exhaustiveness Tests

Compiler phải detect missing cases.

---

# 435.72 — Unreachable Pattern Tests

Compiler có thể cảnh báo/error theo rule đã định nghĩa.

---

# 435.73 — Numeric Tests

Mỗi integer type:

```text
min
max
zero
overflow
```

và mode:

```text
checked
wrapping
saturating
```

---

# 435.74 — Float Tests

Kiểm tra:

```text
NaN
infinity
negative zero
rounding
comparisons
```

---

# 435.75 — Endianness Tests

Test serialization trên:

```text
little endian
big endian
```

hoặc simulation nếu CI hardware không đủ.

---

# 435.76 — Layout Tests

Test:

```text
sizeof
alignof
offsetof
strideof
```

---

# 435.77 — Layout Golden ABI

`@repr(C)` phải khớp layout C-compatible target.

---

# 435.78 — Niche Optimization Tests

Optimization có thể được kiểm tra:

```text
Option<NonNull<T>>
```

nhưng semantic test không được phụ thuộc niche.

---

# 435.79 — String Tests

Kiểm tra:

```text
UTF-8 valid
invalid bytes
length
slice
capacity
append
```

---

# 435.80 — Unicode Tests

Phân biệt:

```text
byte length
code point count
grapheme count
```

Core không được giả định chúng giống nhau.

---

# 435.81 — Memory Allocation Tests

Allocator API:

```text
alloc
dealloc
realloc
alignment
zero-size
```

---

# 435.82 — Custom Allocator Tests

Kiểm tra:

```text
arena
pool
stack
custom
```

---

# 435.83 — OOM Tests

Mỗi policy:

```text
Result
panic
abort
handler
```

phải có test.

---

# 435.84 — Cache Correctness Tests

Nếu source unchanged:

```text
cache hit
```

Nếu semantic input thay đổi:

```text
cache invalidation
```

---

# 435.85 — Incremental Compilation Tests

Scenario:

```text
build
modify implementation
build
```

kiểm tra chỉ nodes cần thiết bị rebuild.

---

# 435.86 — Incremental Semantic Equivalence

Incremental build output phải semantic-equivalent với clean build.

---

# 435.87 — Clean vs Incremental

Test:

```text
clean build
incremental build
```

phải tạo equivalent artifact.

---

# 435.88 — Reproducibility Tests

Build hai lần trong môi trường tương đương:

```text
hash(A) == hash(B)
```

---

# 435.89 — Reproducibility Across Paths

Source ở:

```text
/path/A
/path/B
```

không được thay đổi binary nếu path remapping/metadata policy yêu cầu reproducibility.

---

# 435.90 — Determinism Tests

Kiểm tra nhiều lần:

```text
AST serialization
IR ordering
symbol ordering
diagnostic ordering
artifact ordering
```

---

# 435.91 — Parallel Determinism

Build:

```text
--jobs=1
--jobs=8
```

phải cho artifact equivalent.

---

# 435.92 — Fuzzing Architecture

Fuzzer targets:

```text
lexer
parser
formatter
type checker
comptime
IR verifier
object parser
linker
LSP
```

---

# 435.93 — Lexer Fuzzing

Input:

```text
arbitrary UTF-8 bytes
```

Compiler phải:

```text
accept
or produce diagnostic
```

nhưng không crash/hang.

---

# 435.94 — Parser Fuzzing

Random token streams phải không gây:

```text
memory corruption
infinite loop
compiler crash
```

---

# 435.95 — Formatter Fuzzing

Invariant:

```text
format(valid source)
```

phải tạo source parseable.

---

# 435.96 — Formatter Idempotence Fuzzing

```text
f = format(source)
format(f) == f
```

---

# 435.97 — Type Checker Fuzzing

AST fuzzing tạo malformed semantic programs.

Compiler phải diagnostic graceful.

---

# 435.98 — Comptime Fuzzing

Phải có resource limit để fuzz không treo compiler.

---

# 435.99 — IR Verifier

Trước codegen:

```text
verify(IR)
```

IR invalid phải fail ở verifier.

Không để backend crash vì IR invariant violation.

---

# 435.100 — IR Fuzzing

Sinh random valid/near-valid IR.

Kiểm tra:

```text
verifier
optimizer
codegen
```

---

# 435.101 — Object Parser Fuzzing

Axiom đọc:

```text
ELF
PE/COFF
Mach-O
```

phải chống malformed files.

Đặc biệt quan trọng nếu `axiom inspect` đọc binary do bên ngoài tạo.

---

# 435.102 — Linker Fuzzing

Malformed object:

```text
invalid relocation
truncated section
duplicate symbol
bad alignment
```

phải báo lỗi.

---

# 435.103 — LSP Fuzzing

Fuzz:

```text
document edits
requests
positions
cancellation
```

không được crash daemon.

---

# 435.104 — Property-Based Testing

Ngoài example tests, dùng property:

```text
parse(format(parse(source))) 
```

semantic preservation.

---

# 435.105 — Compiler Differential Testing

Nếu có reference/interpreter semantic engine:

```text
source
→ interpreter
→ compiler executable
```

so sánh kết quả.

---

# 435.106 — Axiom Reference Interpreter

Nên có một **small semantic interpreter** cho test/conformance.

Không phải runtime production.

Nó ưu tiên:

```text
correctness
clarity
determinism
```

thay vì speed.

---

# 435.107 — Why Reference Interpreter

Cho phép:

```text
Frontend semantic result
vs
native compiled result
```

được so sánh.

Điều này cực kỳ hữu ích khi optimizer/backend còn đang phát triển.

---

# 435.108 — Interpreter Scope

Interpreter không cần hỗ trợ:

```text
OS-specific syscalls
native ABI
raw hardware
```

trừ test harness đặc biệt.

---

# 435.109 — Differential Backend Testing

Một source:

```text
reference interpreter
x86-64
AArch64
WASM
```

phải cho semantic result tương đương.

---

# 435.110 — Random Program Generation

Generator tạo chương trình hợp lệ gồm:

```text
arithmetic
branches
loops
functions
structs
enums
match
generics
```

---

# 435.111 — Seed Corpus

Fuzzer phải có corpus:

```text
minimal programs
real-world snippets
historical compiler bugs
edge cases
```

---

# 435.112 — Regression Corpus

Mỗi compiler bug được chuyển thành:

```text
regression test
```

Không cho phép bug quay lại mà không có test.

---

# 435.113 — Bug Test Naming

Ví dụ:

```text
REG-2026-001
REG-2026-002
```

hoặc issue-linked stable IDs.

---

# 435.114 — Compiler Crash Corpus

ICE phải được lưu lại dưới dạng minimized reproducer.

---

# 435.115 — Automatic Test Minimization

Fuzzer nên giảm:

```text
10,000-line failing program
```

thành:

```text
10-line reproducer
```

---

# 435.116 — Timeouts

Mọi compiler fuzz test có timeout.

Không để:

```text
infinite loop
```

đóng băng CI.

---

# 435.117 — Memory Limits

Fuzz runner giới hạn:

```text
RAM
CPU time
output size
process count
```

---

# 435.118 — Compiler Security Testing

Fuzz đặc biệt vào:

```text
parser
comptime
package metadata
object reader
linker
LSP
```

vì đây là attack surface.

---

# 435.119 — Malformed UTF-8

Compiler phải không crash khi source chứa byte sequence invalid.

---

# 435.120 — Huge Input Tests

Test:

```text
huge file
huge identifier
huge string
huge array
deep nesting
```

---

# 435.121 — Deep Type Tests

Ví dụ:

```text
Vec<Vec<Vec<...>>>
```

Compiler phải có recursion/resource limit thích hợp.

---

# 435.122 — Generic Explosion Tests

Kiểm tra pathological monomorphization:

```text
T<T<T<...>>>
```

và số lượng instantiations cực lớn.

---

# 435.123 — Compile-Time Code Explosion

Comptime generation phải bị giới hạn bởi:

```text
generated item count
generated AST size
generated code size
```

---

# 435.124 — Stack Depth

Compiler phases cần tránh stack overflow từ source nesting sâu.

---

# 435.125 — Benchmark Categories

Benchmark compiler theo:

```text
frontend
semantic
comptime
IR
codegen
linker
LSP
formatter
full build
```

---

# 435.126 — Compile-Time Benchmark

Đo:

```text
cold build
warm build
incremental build
```

---

# 435.127 — Runtime Benchmark

Đo:

```text
startup
CPU
memory
throughput
latency
binary size
```

nhưng không biến một benchmark cụ thể thành semantic requirement.

---

# 435.128 — Code Size Benchmark

Track:

```text
.text
.rodata
.data
total file
```

---

# 435.129 — Compile Memory Benchmark

Theo dõi:

```text
peak RSS
AST memory
IR memory
cache memory
```

---

# 435.130 — LSP Latency Benchmark

Đo:

```text
completion
hover
definition
rename
diagnostics
```

trên project nhỏ/vừa/lớn.

---

# 435.131 — Formatter Benchmark

Đo:

```text
small
medium
large
generated
```

---

# 435.132 — Scaling Tests

Project size:

```text
1K LOC
10K LOC
100K LOC
1M LOC
```

Mục tiêu xác định bottleneck.

---

# 435.133 — Build Graph Scaling

Dependency graph lớn phải không có algorithm vô tình:

```text
O(N²)
```

nếu có thể tránh.

---

# 435.134 — Semantic Query Scaling

Symbol lookup phải dùng index.

Không scan toàn source mỗi query.

---

# 435.135 — CI Matrix

CI nên chia:

```text
frontend
backend
platform
runtime
tooling
fuzz
performance
```

---

# 435.136 — Host Matrix

Tùy hạ tầng:

```text
Windows
Linux
macOS
```

---

# 435.137 — Architecture Matrix

Ít nhất cần coverage cho:

```text
x86-64
AArch64
WASM
```

theo từng giai đoạn bootstrap.

---

# 435.138 — Sanitized Compiler Builds

Compiler itself có thể build với:

```text
ASan
UBSan
TSan
```

nếu implementation language/toolchain bootstrap hỗ trợ.

Sau self-hosting, Axiom phải có equivalent strategy.

---

# 435.139 — Compiler Self-Test

Compiler có test suite chạy bằng chính compiler:

```text
axiom test compiler-tests
```

---

# 435.140 — Bootstrap Compiler Comparison

Trong giai đoạn self-hosting:

```text
bootstrap compiler
vs
self-hosted compiler
```

compile cùng source.

Artifact semantics phải tương đương.

---

# 435.141 — Stage Bootstrap

Concept:

```text
stage0
→ stage1
→ stage2
```

Nếu:

```text
stage2 compiler
```

có thể build chính source của nó và kết quả ổn định, self-hosting được xem là đạt một mốc quan trọng.

---

# 435.142 — Trusting Trust Mitigation

Bootstrap có thể kiểm tra:

```text
stage1
→ stage2
→ stage3
```

và so sánh compiler behavior/artifacts.

Không cần phụ thuộc vào một compiler ngoài vĩnh viễn.

---

# 435.143 — Compiler Reproducible Bootstrap

Mục tiêu cuối:

```text
compiler source
+ pinned bootstrap inputs
→ deterministic compiler binary
```

---

# 435.144 — Semantic Version Test

Mỗi compiler release phải chạy:

```text
full conformance suite
```

trước release.

---

# 435.145 — Release Gates

Release không đạt nếu:

```text
conformance failure
regression failure
compiler crash
unexpected nondeterminism
```

trong các phần bắt buộc.

---

# 435.146 — Specification Coverage

Theo dõi:

```text
spec rule
→ implementation
→ test
```

Không để section trong spec không có verification path.

---

# 435.147 — Coverage Types

Có ba coverage chính:

```text
code coverage
feature coverage
semantic rule coverage
```

Semantic coverage quan trọng hơn việc chỉ đạt một phần trăm code coverage.

---

# 435.148 — Mutation Testing

Có thể thay đổi compiler logic có chủ đích:

```text
remove check
invert condition
skip diagnostic
```

Test suite phải bắt được nhiều mutation quan trọng.

---

# 435.149 — Metamorphic Testing

Các transformation semantic-equivalent:

```text
x + 0
```

hoặc những rewrite hợp lệ khác có thể dùng để kiểm tra optimizer.

Không giả định mọi transformation đều universally valid.

---

# 435.150 — Optimization Differential Testing

So sánh:

```text
-O0
-O1
-O2
-O3
-size
```

với cùng input.

Kết quả observable phải tương đương với behavior defined.

---

# 435.151 — UB Exclusion

Differential testing không dùng chương trình có behavior undefined làm oracle.

---

# 435.152 — Floating Point Differential Testing

Phải tính đến:

```text
NaN
rounding
fast-math
target differences
```

Không yêu cầu bit-identical nếu semantics không quy định như vậy.

---

# 435.153 — Atomic Differential Testing

Không so sánh execution ordering như deterministic output.

Kiểm tra properties được quy định bởi memory model.

---

# 435.154 — Concurrency Stress Tests

Chạy:

```text
many threads
many iterations
random scheduling
```

để tìm race/deadlock/runtime bug.

---

# 435.155 — Deadlock Tests

Test lock combinations nhưng phải tránh phụ thuộc scheduler cụ thể.

Timeout được dùng để detect deadlock.

---

# 435.156 — Async Stress

Test:

```text
thousands of tasks
nested await
cancellation
executor shutdown
```

---

# 435.157 — Resource Leak Tests

Theo dõi:

```text
allocation
file handles
threads
sockets
locks
```

---

# 435.158 — Drop Order Verification

Có test recorder:

```text
A constructed
B constructed
B dropped
A dropped
```

để xác nhận deterministic lifetime.

---

# 435.159 — FFI Resource Verification

Test:

```text
Axiom alloc → C free
C alloc → Axiom free
```

chỉ khi allocator contract cho phép.

---

# 435.160 — ABI Compatibility Regression

Mỗi public ABI-sensitive declaration có thể được snapshot:

```text
size
alignment
calling convention
symbol
```

---

# 435.161 — Library ABI Tests

Nếu package là dynamic library:

```text
v1
→ application
→ v2
```

được kiểm tra compatibility theo policy.

---

# 435.162 — Static Library Tests

Archive extraction phải không kéo object không cần thiết.

---

# 435.163 — Dead-Stripping Tests

Unused code phải được loại bỏ khi profile cho phép.

---

# 435.164 — Linker Determinism

Object order khác nhau không nên làm semantic artifact khác nhau nếu linker contract yêu cầu deterministic output.

---

# 435.165 — Object Compatibility

Axiom phải reject:

```text
x86 object + AArch64 executable
```

một cách rõ ràng.

---

# 435.166 — Relocation Overflow Tests

Test relocation không đủ range.

Compiler/linker phải:

```text
relax
or error
```

chứ không silently truncate.

---

# 435.167 — Branch Relaxation Tests

Nếu backend hỗ trợ short/long branch:

```text
near
far
```

đều phải được test.

---

# 435.168 — Instruction Encoder Boundary Tests

Test:

```text
min displacement
max displacement
immediate boundaries
register boundaries
```

---

# 435.169 — Register Allocator Tests

Kiểm tra:

```text
register pressure
spill
reload
call clobbers
```

---

# 435.170 — Stack Frame Tests

Test:

```text
leaf
non-leaf
large frame
dynamic stack
alignment
callee saved
```

---

# 435.171 — Debug Info Tests

Source:

```text
breakpoint
step
local variable
stack trace
```

phải map đúng nếu debug info enabled.

---

# 435.172 — Error Message Stability

Không nhất thiết khóa wording.

Test stable:

```text
error code
category
span
semantic payload
```

---

# 435.173 — Localization

Human diagnostics có thể được localized sau này.

Machine diagnostics không được phụ thuộc ngôn ngữ.

---

# 435.174 — Test Language

Test source vẫn là Axiom.

Không tạo một test DSL riêng nếu không cần.

---

# 435.175 — Test Harness

Có harness:

```text
axiom-test
```

nhưng đây là tooling, không phải language runtime requirement.

---

# 435.176 — Test Metadata

Mỗi test có:

```text
id
kind
target
expected
timeout
features
```

---

# 435.177 — Feature-Gated Tests

Test có thể yêu cầu:

```text
threads
simd
filesystem
network
gpu
```

và skip hợp lệ nếu target không hỗ trợ.

---

# 435.178 — Expected Failure

Negative tests khai báo:

```text
expected_error = E430021
```

Không chỉ:

```text
compile failed
```

---

# 435.179 — Diagnostic Span Verification

Negative test có thể yêu cầu:

```text
primary span
secondary span
```

để đảm bảo compiler chỉ đúng vị trí.

---

# 435.180 — Snapshot Updating

Không được có:

```bash
axiom test --bless
```

tự động overwrite mọi golden file mà không review.

Có thể có explicit update mode nhưng phải hiển thị diff.

---

# 435.181 — Fuzz Seed Reproducibility

Mỗi fuzz failure lưu:

```text
seed
input
compiler version
target
flags
```

---

# 435.182 — Randomness

Fuzzer dùng random seed.

Compiler semantic behavior không được phụ thuộc randomness.

---

# 435.183 — Fuzz Corpus Versioning

Corpus được version cùng compiler.

---

# 435.184 — Fuzz CI

CI có:

```text
short fuzz smoke
```

Mở rộng fuzz chạy định kỳ.

---

# 435.185 — Long-Running Fuzz

Nightly/continuous fuzz có thể chạy hàng giờ/ngày.

Không block mọi commit.

---

# 435.186 — Performance Regression Gate

Một số benchmark critical có threshold tương đối.

Ví dụ:

```text
compile time regression > configured threshold
```

có thể báo regression.

Không biến mọi benchmark thành hard language correctness requirement.

---

# 435.187 — Memory Regression

Theo dõi:

```text
peak compiler memory
binary size
runtime memory
```

---

# 435.188 — Benchmark Reproducibility

Benchmark phải ghi:

```text
CPU
OS
compiler version
target
profile
iterations
```

---

# 435.189 — Statistical Reporting

Runtime benchmark không chỉ lấy một lần chạy.

Báo:

```text
median
min
max
variance/dispersion
```

theo benchmark framework.

---

# 435.190 — No Ranking-Based Performance Policy

Không định nghĩa semantics bằng:

```text
"must beat C"
```

Thay vào đó:

```text
measure
track
regressions
```

vì C/C++ implementation cụ thể không phải một specification oracle.

---

# 435.191 — Compiler Correctness Priority

Thứ tự verification:

```text
correctness
→ determinism
→ robustness
→ performance
```

Optimization không được phá correctness.

---

# 435.192 — Reference Semantics

Language specification phải có semantic model đủ rõ để test biết:

```text
expected result
```

mà không cần đoán từ implementation.

---

# 435.193 — Undefined Behavior Tests

UB tests chỉ kiểm tra:

```text
compiler accepts/rejects according to rules
```

không yêu cầu runtime result cụ thể.

---

# 435.194 — Implementation-Defined Tests

Nếu behavior implementation-defined:

```text
document chosen behavior
```

và test compiler consistency.

---

# 435.195 — Target-Defined Tests

Nếu behavior phụ thuộc target:

```text
test matrix
```

phải ghi target expectation rõ ràng.

---

# 435.196 — Test Result Schema

```bash
axiom test --json
```

schema:

```text
schema_version
suite
tests[]
summary
duration
artifacts
```

Mỗi test:

```text
id
status
duration
diagnostics
stdout
stderr
```

---

# 435.197 — Machine-Test Contract

AI agent phải có thể biết:

```text
PASS
FAIL
SKIP
XFAIL
TIMEOUT
CRASH
```

mà không parse human text.

---

# 435.198 — Compiler Crash Status

`CRASH` khác:

```text
FAIL
```

và phải chứa reproduction information.

---

# 435.199 — Conformance Release Criteria

Một stable compiler release phải đạt:

```text
required conformance
required regression suite
required backend smoke tests
required determinism
```

Các experimental backend có thể có trạng thái riêng.

---

# 435.200 — Hard Invariants

BOOTSTRAP-435 khóa:

1. Specification phải ánh xạ được tới executable tests.
2. Có conformance suite.
3. Có negative tests.
4. Lexer/parser/semantic/backend đều có test.
5. ABI phải có golden tests.
6. Machine encoder có encoding tests.
7. Object writer có format tests.
8. Linker có relocation/symbol tests.
9. Native smoke test bắt buộc.
10. Clean và incremental build phải tương đương.
11. Parallel và serial build phải deterministic.
12. Reproducibility phải được kiểm tra.
13. Fuzzing là một phần chính thức của compiler validation.
14. Parser/lexer/object reader/linker phải chịu malformed-input testing.
15. Comptime phải có sandbox/resource-limit tests.
16. Reference semantic interpreter được dùng làm oracle khi phù hợp.
17. Differential testing được dùng giữa interpreter/backend/optimization levels.
18. UB không được dùng làm correctness oracle.
19. Concurrency được stress-test riêng.
20. Async cancellation/cleanup được test.
21. Ownership/drop order được test runtime.
22. FFI/ABI được test hai chiều.
23. Regression bug phải trở thành regression test.
24. Fuzz failure phải có reproducible seed/input.
25. Compiler crash phải có minimized reproducer.
26. Test result có machine-readable schema.
27. AI không cần parse human-readable output để xác định PASS/FAIL.
28. Performance regression được theo dõi riêng với correctness.
29. Compiler correctness luôn cao hơn optimization.
30. Stable release phải vượt qua required conformance gates.

**BOOTSTRAP-435 hoàn tất.**

---

# BOOTSTRAP-436 — DEBUGGING, PROFILING, SANITIZATION & OBSERVABILITY

Task tiếp theo sẽ khóa hệ thống **debug/profiling/observability** của Axiom, bao gồm:

```text
source-level debugging
DWARF/CodeView
stack traces
breakpoints
watch variables
debugger metadata
profiling
CPU sampling
instrumentation
allocation profiling
memory diagnostics
sanitizers
coverage
trace events
crash dumps
panic diagnostics
```

Đặc biệt, 436 sẽ phải bảo đảm một nguyên tắc quan trọng của Axiom:

```text
Debug/diagnostic capability
        ≠
mandatory runtime overhead
```

Build release tối ưu vẫn phải có khả năng tạo binary rất gọn khi không yêu cầu debug/profiling/sanitizer.