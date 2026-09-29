# BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE

Task này khóa **toolchain chính thức của Axiom**. Compiler không chỉ là một binary biến source thành executable; toàn bộ developer workflow phải được thiết kế ngay từ đầu để phục vụ:

- lập trình viên;
- IDE/LSP;
- CI/CD;
- build system;
- debugger;
- profiler;
- AI coding agent;
- incremental compilation;
- cross-compilation.

Nguyên tắc lớn:

> **Một compiler core, nhiều frontend/tooling command; mọi công cụ dùng chung semantic database và diagnostic engine.**

---

# 434.1 — Toolchain architecture

Kiến trúc:

```text
                    axiom
                      │
              ┌───────┴────────┐
              │ Compiler Driver │
              └───────┬────────┘
                      │
       ┌──────────────┼─────────────────┐
       │              │                 │
    Frontend        Build             Tooling
       │              │                 │
   Lexer/Parser    Resolver           Formatter
   TypeChecker     Dependency         LSP
   Comptime        Cache              Docs
       │              │                 │
       └──────────────┼─────────────────┘
                      │
                    IR/Backend
                      │
                Object/Linker
```

---

# 434.2 — Một executable chính

CLI chính:

```text
axiom
```

subcommand:

```text
axiom build
axiom check
axiom run
axiom test
axiom fmt
axiom doc
axiom package
axiom clean
axiom cache
axiom lsp
axiom version
axiom target
```

Có thể cung cấp các binary wrapper sau này, nhưng semantic implementation dùng chung.

---

# 434.3 — `axiom build`

Build project:

```text
axiom build
```

Release:

```text
axiom build --release
```

Target:

```text
axiom build --target x86_64-linux
```

Output:

```text
build/
    debug/
    release/
```

---

# 434.4 — `axiom check`

Chỉ kiểm tra:

```text
axiom check
```

Không emit executable.

Pipeline:

```text
parse
→ resolve
→ type check
→ ownership
→ comptime
→ diagnostics
```

Có thể bỏ qua machine-code emission.

---

# 434.5 — `axiom run`

```text
axiom run
```

Conceptually:

```text
build
→ execute
```

Arguments:

```text
axiom run -- arg1 arg2
```

---

# 434.6 — `axiom test`

```text
axiom test
```

Tự động discover test functions.

Ví dụ:

```text
@test
fn add_test() {
    assert(add(2, 3) == 5)
}
```

---

# 434.7 — Test discovery

Compiler metadata ghi nhận:

```text
@test
```

không cần runtime reflection.

Test runner có thể được generate ở compile time.

---

# 434.8 — Test isolation

Mỗi test có thể chạy:

```text
in-process
```

hoặc:

```text
separate-process
```

tùy test profile.

---

# 434.9 — Benchmark

```text
axiom bench
```

benchmark framework là library/tooling.

Compiler cung cấp optimization/profile facilities.

---

# 434.10 — `axiom fmt`

Formatter chính thức:

```text
axiom fmt
```

Formatting phải deterministic.

---

# 434.11 — Formatter invariant

```text
axiom fmt
```

sau đó chạy lại:

```text
axiom fmt
```

không được tạo thêm diff.

Tức:

```text
fmt(fmt(source)) == fmt(source)
```

---

# 434.12 — Formatter configuration

Project:

```text
axiom.toml
```

có thể chứa:

```toml
[format]
indent = 4
line_width = 100
trailing_comma = true
```

Nhưng formatter phải có default canonical.

---

# 434.13 — Không có nhiều formatter style

Axiom nên có **một canonical formatter**.

Cho phép một số preference không ảnh hưởng semantics, nhưng không biến formatter thành hệ thống style fragmentation như nhiều ecosystem khác.

---

# 434.14 — `axiom doc`

Generate documentation:

```text
axiom doc
```

Nguồn documentation:

```text
/// Adds two numbers.
fn add(...)
```

---

# 434.15 — Documentation format

Documentation có thể output:

```text
HTML
Markdown
JSON
```

---

# 434.16 — Documentation semantic metadata

Doc generator lấy trực tiếp semantic model:

```text
symbol
type
visibility
generic parameters
traits
attributes
documentation
```

Không parse source lần nữa.

---

# 434.17 — Machine-readable API

Compiler phải expose semantic information dạng:

```text
JSON
```

hoặc binary semantic protocol.

Ví dụ:

```json
{
  "symbol": "Vec.push",
  "kind": "method",
  "receiver": "Vec<T>",
  "arguments": ["T"],
  "returns": "unit"
}
```

Schema chính thức sẽ được khóa ở tooling specification.

---

# 434.18 — Diagnostics architecture

Diagnostic engine độc lập:

```text
Diagnostic {
    severity
    code
    message
    primary_span
    secondary_spans
    notes
    suggestions
}
```

---

# 434.19 — Diagnostic severity

Tối thiểu:

```text
error
warning
note
help
```

---

# 434.20 — Stable error codes

Ví dụ:

```text
E430001
E423014
E434002
```

Error code không thay đổi tùy wording message.

---

# 434.21 — Diagnostic source span

Mỗi diagnostic phải có:

```text
file
start
end
line
column
```

nếu source tồn tại.

---

# 434.22 — Multi-span diagnostics

Ví dụ duplicate definition:

```text
error: duplicate definition of `foo`

 --> src/a.ax:10
      ...

note: previous definition here

 --> src/b.ax:24
      ...
```

---

# 434.23 — Suggested fixes

Compiler có thể emit structured fix:

```text
Fix {
    range
    replacement
}
```

---

# 434.24 — Machine-readable diagnostics

CLI:

```text
axiom check --format=json
```

trả JSON ổn định.

---

# 434.25 — SARIF

Toolchain có thể hỗ trợ SARIF cho CI/static analysis.

---

# 434.26 — Human diagnostics

Default terminal output tối ưu cho con người:

```text
error[E430012]: type mismatch
```

với source snippet.

---

# 434.27 — AI diagnostics

AI mode:

```text
axiom check --format=ai
```

có thể trả:

```text
{
    "code": "E430012",
    "kind": "type_mismatch",
    "location": ...,
    "expected": "i32",
    "found": "String",
    "fixes": [...]
}
```

Không yêu cầu AI phải suy luận từ prose.

---

# 434.28 — Diagnostic IDs ổn định

Mỗi diagnostic category có stable identifier.

Message text có thể thay đổi giữa versions mà machine consumer vẫn hoạt động.

---

# 434.29 — Compiler suggestions

Suggestion phải phân biệt:

```text
machine_applicable
maybe_applicable
informational
```

---

# 434.30 — Automatic fix

LSP/IDE chỉ auto-apply suggestion nếu compiler đánh dấu:

```text
machine_applicable
```

---

# 434.31 — Error recovery

Parser phải recover sau syntax error để tiếp tục phân tích file.

Mục tiêu:

```text
1 lỗi syntax
```

không biến thành:

```text
500 lỗi cascade
```

---

# 434.32 — Semantic error suppression

Nếu type information không còn đáng tin cậy vì lỗi trước đó, compiler phải hạn chế diagnostic cascade.

---

# 434.33 — `axiom lsp`

CLI:

```text
axiom lsp
```

hoạt động theo Language Server Protocol.

---

# 434.34 — LSP capabilities

Tối thiểu:

```text
completion
hover
go-to-definition
go-to-declaration
find-references
rename
signature-help
diagnostics
formatting
code-actions
semantic-tokens
document-symbols
workspace-symbols
```

---

# 434.35 — Semantic completion

Completion không dựa đơn thuần vào text matching.

Ví dụ:

```text
user.
```

compiler semantic database biết:

```text
User
 ├── id
 ├── name
 ├── save()
 └── delete()
```

---

# 434.36 — Type-aware completion

Generic:

```text
vec.map(...)
```

LSP phải resolve:

```text
T
Item
closure signature
return type
```

---

# 434.37 — Trait-aware completion

Nếu:

```text
x.draw()
```

compiler tìm:

```text
inherent method
trait implementation
extension method
```

theo đúng method resolution rules 426/430.

---

# 434.38 — Hover

Hover phải có structured semantic information:

```text
fn add(a: i32, b: i32) -> i32
```

và có thể thêm:

```text
module
documentation
generic constraints
attributes
```

---

# 434.39 — Go to definition

Resolver dùng symbol identity thay vì text search.

---

# 434.40 — Rename

Rename phải dựa trên semantic symbol ID.

Không rename nhầm:

```text
foo
```

ở string/comment/unrelated scope.

---

# 434.41 — Find references

Compiler semantic index có thể trả tất cả references chính xác.

---

# 434.42 — Semantic tokens

LSP phân biệt:

```text
type
trait
function
method
variable
constant
parameter
field
module
generic parameter
macro/generator
```

---

# 434.43 — Incremental semantic database

Compiler phải giữ semantic state giữa các lần build.

Concept:

```text
Source
 ↓
Syntax tree
 ↓
Name resolution
 ↓
Type information
 ↓
Comptime results
 ↓
IR
 ↓
Object
```

Mỗi tầng có cache riêng.

---

# 434.44 — Incremental compilation

Nếu thay đổi:

```text
foo.ax
```

không được compile lại toàn bộ project nếu dependency graph chứng minh không cần.

---

# 434.45 — Fine-grained invalidation

Dependency có thể ở mức:

```text
module
symbol
type
generic instantiation
comptime result
IR unit
```

---

# 434.46 — Semantic fingerprint

Mỗi declaration có hash:

```text
semantic_hash(symbol)
```

Thay đổi comment không làm invalidate downstream compilation.

---

# 434.47 — API fingerprint

Public API thay đổi:

```text
old API hash != new API hash
```

→ dependent modules được kiểm tra/recompile.

---

# 434.48 — Private implementation change

Nếu public semantic interface không đổi:

```text
Axiom source
 ↓
private implementation changed
 ↓
recompile A
 ↓
B may reuse cached interface
```

---

# 434.49 — Generic cache

Mỗi generic instantiation có cache key:

```text
generic_definition_hash
+
concrete_types
+
const_arguments
+
target
+
compiler_profile
```

---

# 434.50 — Comptime cache

431 comptime result cache key:

```text
comptime_function_hash
+
arguments
+
type_context
+
target_config
```

---

# 434.51 — Object cache

420 object cache:

```text
IR hash
+
target
+
optimization profile
+
ABI
```

---

# 434.52 — Link cache

Linking có thể reuse unchanged object sections khi dependency graph cho phép.

---

# 434.53 — Build cache directory

Ví dụ:

```text
.axiom/
    cache/
    index/
    artifacts/
```

---

# 434.54 — Cache integrity

Cache entries phải có:

```text
version
compiler identity
target
profile
dependency hashes
content hash
```

---

# 434.55 — Cache corruption

Nếu cache entry invalid:

```text
ignore
rebuild
replace
```

Không được coi cache là source of truth.

---

# 434.56 — Reproducible builds

Build cùng:

```text
source
dependencies
compiler
target
profile
environment contract
```

phải tạo artifact deterministic nếu build profile yêu cầu reproducibility.

---

# 434.57 — Build timestamp

Không được tự động chèn timestamp khiến binary hash thay đổi.

Nếu application cần timestamp → explicit API.

---

# 434.58 — Build ID

Có thể tạo build ID deterministic từ:

```text
source graph hash
compiler version
target
profile
dependency graph
```

---

# 434.59 — Debug builds

Debug profile:

```text
-O0
debug info
assertions
overflow diagnostics
```

có thể được cấu hình.

---

# 434.60 — Release builds

Release profile:

```text
optimization
dead-code elimination
inlining
LTO optional
debug info optional
```

---

# 434.61 — Optimization levels

Không nên tạo quá nhiều mức khó hiểu.

Đề xuất:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

với semantic compatibility.

---

# 434.62 — Safety profile

Optimization và safety là hai chiều độc lập.

Ví dụ:

```text
debug + O2
release + checks
release + unchecked
```

---

# 434.63 — Overflow profile

Có thể chọn:

```text
checked
wrap
saturate
```

theo operator/API đã định nghĩa.

---

# 434.64 — Panic profile

```text
panic=abort
panic=unwind
```

từ 425.

---

# 434.65 — Target triple

Canonical target descriptor:

```text
architecture
vendor
os
environment
abi
```

Ví dụ conceptual:

```text
x86_64-pc-windows-msvc
x86_64-unknown-linux-gnu
aarch64-apple-darwin
aarch64-linux-android
wasm32-unknown-none
```

---

# 434.66 — Target specification

Target là data/configuration chứ không hard-code toàn bộ trong CLI.

Compiler backend đọc:

```text
TargetSpec
```

chứa:

```text
ISA
ABI
pointer size
endianness
OS
linker format
calling convention
features
```

---

# 434.67 — Cross compilation

```text
axiom build --target aarch64-linux
```

không cần chạy compiler trên target.

---

# 434.68 — Host vs target

Phải phân biệt:

```text
HOST
```

và:

```text
TARGET
```

đặc biệt quan trọng với comptime.

---

# 434.69 — Comptime environment

Comptime mặc định thấy:

```text
target.arch
target.os
target.pointer_size
target.endian
target.features
```

Không mặc định thấy:

```text
host filesystem
host environment
host CPU quirks
```

---

# 434.70 — Compiler built-ins

Compiler expose target information thông qua stable API:

```text
target.arch
target.os
target.abi
target.feature(...)
```

---

# 434.71 — CPU feature detection

Compile-time:

```text
if target.feature("avx2") {
    ...
}
```

Runtime feature detection nếu cần phải explicit.

---

# 434.72 — Multi-versioning

Toolchain có thể hỗ trợ:

```text
generic implementation
AVX2 implementation
AVX512 implementation
NEON implementation
```

với dispatcher explicit/generated.

---

# 434.73 — Package manager

Axiom cần package manager chính thức:

```text
axiom package
```

---

# 434.74 — Project manifest

Tên dự kiến:

```text
axiom.toml
```

---

# 434.75 — Minimal manifest

```toml
[package]
name = "hello"
version = "0.1.0"

[build]
entry = "src/main.ax"
```

---

# 434.76 — Dependencies

```toml
[dependencies]
http = "..."
image = "..."
```

Exact dependency syntax sẽ khóa trong package specification.

---

# 434.77 — Dependency identity

Dependency phải được xác định bởi:

```text
name
source
version
integrity hash
```

---

# 434.78 — Lock file

Project dùng:

```text
axiom.lock
```

để khóa dependency graph.

---

# 434.79 — Reproducible dependency resolution

Có lock file:

```text
same dependency graph
```

không tự thay đổi khi build lại.

---

# 434.80 — Versioning

Axiom package manager sử dụng semantic-version-compatible rules hoặc một biến thể được khóa riêng.

---

# 434.81 — Dependency source

Có thể hỗ trợ:

```text
registry
git
local path
archive
```

---

# 434.82 — Integrity

Downloaded package phải kiểm tra content hash.

---

# 434.83 — Registry

Official registry nếu được triển khai phải cung cấp:

```text
package metadata
versions
checksums
signatures
documentation
```

---

# 434.84 — Package signing

Package signing là security layer.

Không nên biến signature thành language semantic requirement.

---

# 434.85 — Dependency build scripts

Build script có thể cần execute host tools.

Nhưng:

> **Build script không phải `comptime`.**

Đây là distinction quan trọng từ 431.

---

# 434.86 — Build scripts

Nếu có:

```text
build.ax
```

thì nó thuộc **build orchestration phase**.

Có thể truy cập:

```text
filesystem
environment
external tools
```

nếu user cho phép.

---

# 434.87 — Comptime sandbox

Ngược lại:

```text
comptime
```

không mặc định có:

```text
filesystem
network
process
environment mutation
```

---

# 434.88 — Security boundary

```text
comptime
```

→ deterministic compiler sandbox.

```text
build script
```

→ explicit host execution.

---

# 434.89 — Dependency isolation

Mỗi package có namespace riêng.

---

# 434.90 — Dependency cycle

Module dependency cycle bị reject nếu không thuộc loại cycle được compiler xử lý đặc biệt.

Package dependency cycle mặc định bị reject.

---

# 434.91 — Workspace

Monorepo:

```text
workspace/
    axiom.toml
    packages/
        core/
        app/
        tools/
```

---

# 434.92 — Workspace dependency

Package trong workspace có thể reference package khác mà không publish.

---

# 434.93 — Local package

```toml
[dependencies]
foo = { path = "../foo" }
```

conceptually.

---

# 434.94 — Package feature flags

Dependency có thể optional:

```toml
[features]
network = [...]
gui = [...]
gpu = [...]
```

---

# 434.95 — Feature unification

Toolchain phải tránh dependency graph tạo ra feature combination không deterministic.

---

# 434.96 — Conditional compilation

Không dùng preprocessor kiểu C làm cơ chế chính.

Dùng semantic condition:

```text
comptime if target.os == "windows" {
    ...
}
```

hoặc module-level target declarations.

---

# 434.97 — No textual macro preprocessor

Axiom không có:

```text
#define
#ifdef
#include
```

làm cơ chế build chính.

---

# 434.98 — Imports

Import semantic:

```text
import std::io::File
```

Compiler resolve symbol graph.

---

# 434.99 — Module index

Compiler giữ module graph:

```text
package
 ↓
module
 ↓
declaration
 ↓
symbol
```

---

# 434.100 — Module file mapping

Một module không bắt buộc tương ứng 1:1 với filesystem directory.

Nhưng convention nên rõ ràng.

---

# 434.101 — CLI project initialization

```text
axiom init my_app
```

tạo:

```text
my_app/
    axiom.toml
    src/
        main.ax
```

---

# 434.102 — New library

```text
axiom init --lib my_lib
```

---

# 434.103 — New binary

```text
axiom init --bin my_app
```

---

# 434.104 — Project validation

```text
axiom check
```

phải kiểm tra:

- manifest;
- dependency graph;
- source;
- target;
- semantic correctness.

---

# 434.105 — Build graph

Compiler tạo DAG:

```text
Package
   ↓
Module
   ↓
Semantic Unit
   ↓
IR Unit
   ↓
Object
   ↓
Executable
```

---

# 434.106 — Parallel compilation

Independent modules compile song song.

---

# 434.107 — Deterministic parallelism

Parallel compilation không được làm thay đổi artifact semantics/hash.

---

# 434.108 — Job control

CLI:

```text
-j 8
```

hoặc:

```text
--jobs=auto
```

---

# 434.109 — Compiler server

Có thể có long-lived compiler process:

```text
axiom serve
```

để LSP/incremental builds reuse:

- parsed AST;
- semantic DB;
- type information;
- comptime cache.

---

# 434.110 — No mandatory daemon

Normal:

```text
axiom build
```

vẫn hoạt động độc lập.

---

# 434.111 — LSP server reuse

LSP server có thể trở thành compiler daemon tự nhiên.

---

# 434.112 — IDE integration

Axiom phải cung cấp chính thức:

```text
LSP
DAP
formatter
diagnostic protocol
```

---

# 434.113 — Debug Adapter Protocol

Debugger integration qua DAP.

---

# 434.114 — Debug information

Compiler emits:

```text
DWARF
CodeView/PDB
```

tùy target.

---

# 434.115 — Source mapping

Debug metadata phải map:

```text
machine instruction
→ IR
→ AST node
→ source span
```

---

# 434.116 — Inlining debug info

Khi inline:

```text
foo()
```

debugger vẫn phải có inline call-site information.

---

# 434.117 — Optimized debugging

Compiler không cần tắt toàn bộ optimization để tạo usable debug information.

---

# 434.118 — Symbol information

Release build có thể:

```text
strip
split-debug-info
```

---

# 434.119 — Split debug files

Ví dụ:

```text
app.exe
app.debug
```

---

# 434.120 — Static analysis

Toolchain có thể có:

```text
axiom analyze
```

cho:

- unreachable code;
- unused symbols;
- suspicious ownership;
- race-risk metadata;
- unsafe usage;
- allocation analysis.

---

# 434.121 — Warnings

Warnings có stable codes.

Ví dụ:

```text
W434001
```

---

# 434.122 — Warning configuration

```text
-Wall
-Werror
-Wno-unused
```

hoặc Axiom-native equivalents.

---

# 434.123 — Warning levels

Không nên có hàng trăm obscure switches.

Default warning set phải hữu ích.

---

# 434.124 — Lint

Lint rules có thể là compiler diagnostics hoặc plugin/tooling.

---

# 434.125 — Compiler plugins

Không cho arbitrary compiler plugins mutate semantic rules trong core.

Điều này phá reproducibility.

---

# 434.126 — Analyzer plugins

External analyzers có thể consume machine-readable AST/semantic metadata.

---

# 434.127 — AI compiler API

Axiom phải expose:

```text
source
AST
symbols
types
diagnostics
fixes
dependency graph
build graph
```

qua machine-readable interface.

---

# 434.128 — AI symbol query

AI agent có thể query:

```text
find_symbol("User")
find_references("User.save")
type_of(expression)
```

thay vì đọc toàn bộ repository.

---

# 434.129 — AI code action

Compiler có thể trả:

```text
diagnostic
→ suggested patch
→ affected symbols
→ affected files
```

---

# 434.130 — AI-safe editing

Tooling nên cung cấp patch theo range:

```text
file
start
end
replacement
```

AI agent không phải rewrite nguyên file nếu chỉ cần sửa một declaration.

---

# 434.131 — Semantic diff

Toolchain có thể báo:

```text
API changed
ABI changed
private implementation changed
behavioral metadata changed
```

---

# 434.132 — ABI diff

Một tool:

```text
axiom abi-diff old new
```

có thể kiểm tra:

- symbol;
- parameter;
- return;
- layout;
- alignment;
- calling convention.

---

# 434.133 — API extraction

```text
axiom api
```

xuất public semantic API.

---

# 434.134 — Dependency visualization

```text
axiom deps
```

có thể xuất:

```text
text
JSON
Graphviz
```

---

# 434.135 — Build trace

```text
axiom build --trace
```

hiển thị:

```text
parse
typecheck
comptime
IR
codegen
link
```

và thời gian từng phase.

---

# 434.136 — Performance diagnostics

Compiler có thể report:

```text
allocations
inlining
vectorization
bounds-check elimination
monomorphization
code size
```

---

# 434.137 — Optimization remarks

Ví dụ:

```text
remark: loop vectorized
remark: bounds check eliminated
remark: function inlined
remark: allocation eliminated
```

---

# 434.138 — No misleading optimization claims

Compiler chỉ báo optimization đã thực sự xảy ra, không tuyên bố chung chung rằng code "đã tối ưu".

---

# 434.139 — IR dump

Developer có thể:

```text
axiom emit-ir
```

---

# 434.140 — AST dump

```text
axiom dump-ast
```

---

# 434.141 — Semantic dump

```text
axiom dump-sema
```

---

# 434.142 — Object dump

```text
axiom dump-obj
```

---

# 434.143 — Assembly dump

```text
axiom emit-asm
```

---

# 434.144 — Machine code dump

Có thể inspect instruction encoding:

```text
axiom objdump
```

---

# 434.145 — Linker trace

```text
axiom link --trace
```

hiển thị:

```text
symbol resolution
archive extraction
relocations
section layout
dead stripping
```

---

# 434.146 — Compiler self-test

Compiler repository phải có:

```text
unit tests
lexer tests
parser tests
type tests
ownership tests
comptime tests
IR tests
backend tests
ABI tests
linker tests
integration tests
```

---

# 434.147 — Golden tests

Diagnostics có golden snapshots.

---

# 434.148 — Cross-target tests

Backend test matrix:

```text
x86-64 ELF
x86-64 PE
x86-64 Mach-O
AArch64 ELF
AArch64 Mach-O
WASM
```

---

# 434.149 — Differential tests

Nếu Axiom có nhiều backend encoding paths, semantic result phải nhất quán.

---

# 434.150 — Fuzzing

Compiler phải hỗ trợ fuzz:

```text
lexer
parser
type checker
comptime evaluator
object writer
linker
```

---

# 434.151 — Compiler crash

Compiler crash là:

```text
ICE — Internal Compiler Error
```

và phải tạo diagnostic report.

---

# 434.152 — ICE report

Report:

```text
compiler version
target
source hash
phase
stack trace
repro command
```

Không mặc định gửi dữ liệu ra Internet.

---

# 434.153 — Privacy

Compiler/toolchain không tự upload:

```text
source code
diagnostics
telemetry
```

nếu user không explicit bật telemetry.

---

# 434.154 — Offline-first

Các chức năng cơ bản:

```text
check
build
run
test
fmt
doc
```

phải hoạt động offline khi dependencies/cache đã có.

---

# 434.155 — No mandatory cloud

Axiom compiler không phụ thuộc cloud service.

---

# 434.156 — Package registry optional

Registry giúp dependency distribution nhưng compiler local vẫn hoạt động không registry.

---

# 434.157 — Compiler distribution

Axiom compiler distribution nên chứa:

```text
compiler
linker
formatter
LSP
standard libraries
target specs
debug tooling integration
```

---

# 434.158 — Self-contained compiler

Đúng mục tiêu ban đầu:

```text
Axiom source
 ↓
Axiom compiler
 ↓
Axiom object
 ↓
Axiom linker
 ↓
native executable
```

Không cần:

```text
GCC
Clang
LLVM
MSVC C++ compiler
```

làm compiler backend bắt buộc.

---

# 434.159 — System linker

Axiom **có thể** dùng system linker khi target/platform yêu cầu interoperability, nhưng native Axiom linker vẫn là implementation chính.

---

# 434.160 — Self-hosting path

Bootstrap:

```text
Stage 0
minimal compiler implementation
        ↓
Stage 1
Axiom compiler
        ↓
Stage 2
compiler written substantially in Axiom
        ↓
Stage 3
self-hosting compiler
```

---

# 434.161 — Compiler source modularity

Compiler itself nên chia:

```text
compiler/
    lexer/
    parser/
    resolver/
    typecheck/
    ownership/
    comptime/
    ir/
    optimizer/
    backend/
    object/
    linker/
    diagnostics/
    tooling/
```

---

# 434.162 — Shared semantic engine

LSP không được tự viết một type checker riêng.

```text
CLI
LSP
IDE
Doc
AI tooling
```

đều gọi semantic engine chung.

---

# 434.163 — One source of truth

```text
                    Semantic Database
                    /   |    |    \
                   /    |    |     \
                CLI    LSP   Docs    AI
```

---

# 434.164 — Tool protocol versioning

Machine-readable protocols phải có:

```text
schema_version
compiler_version
language_edition
```

---

# 434.165 — Forward compatibility

AI tooling có thể bỏ qua field chưa biết thay vì crash.

---

# 434.166 — Unknown fields

Machine protocol phải thiết kế theo kiểu extensible:

```text
unknown field
→ ignore
```

nếu không phải required semantic field.

---

# 434.167 — Stable source positions

Source positions dùng byte offsets UTF-8 làm canonical representation.

Line/column là derived information.

---

# 434.168 — Unicode-aware diagnostics

Column display phải xử lý Unicode đúng, không coi mỗi byte UTF-8 là một ký tự hiển thị.

---

# 434.169 — Diagnostic localization

Compiler internal diagnostic code bằng semantic identifier.

Human message có thể localization về sau.

---

# 434.170 — Compiler language

Default diagnostics có thể English để phù hợp ecosystem quốc tế.

Localization là tooling layer.

---

# 434.171 — Exit codes

CLI phải có stable exit codes:

```text
0 = success
nonzero = failure
```

Các category có thể phân biệt thêm:

```text
compile error
test failure
usage error
internal error
```

---

# 434.172 — Quiet mode

```text
axiom build --quiet
```

---

# 434.173 — Verbose mode

```text
axiom build --verbose
```

---

# 434.174 — JSON mode

```text
axiom build --format=json
```

để CI/AI consume.

---

# 434.175 — Progress output

Interactive terminal có progress, nhưng JSON mode không được trộn human text vào output stream.

---

# 434.176 — stdout/stderr contract

Machine-readable result:

```text
stdout = structured result
stderr = diagnostic/log
```

hoặc một contract tương đương phải được khóa để AI/CI dễ xử lý.

---

# 434.177 — Build manifest output

Compiler có thể emit:

```text
build-manifest.json
```

chứa:

```text
artifacts
dependencies
target
compiler
source hashes
```

---

# 434.178 — Artifact manifest

Ví dụ:

```json
{
  "target": "x86_64-linux",
  "artifacts": [
    {
      "kind": "executable",
      "path": "build/app",
      "hash": "..."
    }
  ]
}
```

---

# 434.179 — Artifact provenance

Có thể truy vấn:

```text
artifact
→ source
→ dependencies
→ compiler
→ target
```

---

# 434.180 — Reproducibility verification

Tool:

```text
axiom verify-build
```

có thể rebuild và compare hashes.

---

# 434.181 — Cache command

```text
axiom cache list
axiom cache clean
axiom cache verify
```

---

# 434.182 — Clean

```text
axiom clean
```

xóa generated build artifacts nhưng không xóa source/dependencies.

---

# 434.183 — Package commands

```text
axiom package build
axiom package test
axiom package publish
axiom package install
```

---

# 434.184 — Publish safety

Publish phải kiểm tra:

- manifest;
- lock;
- version;
- metadata;
- package contents;
- integrity.

---

# 434.185 — Package contents

Không tự động publish:

```text
.axiom/
build/
cache/
secrets
```

---

# 434.186 — Workspace commands

Commands chạy ở workspace root phải hiểu dependency graph toàn workspace.

---

# 434.187 — Profiles

Manifest hỗ trợ:

```text
[profile.debug]
[profile.release]
```

và custom profiles nếu cần.

---

# 434.188 — Target profiles

Có thể override:

```text
optimization
panic mode
debug info
CPU features
allocator
runtime
```

---

# 434.189 — Freestanding profile

Ví dụ conceptual:

```toml
[profile.kernel]
runtime = "none"
allocator = "none"
panic = "abort"
```

---

# 434.190 — Application profile

```toml
[profile.release]
optimization = 3
panic = "abort"
```

---

# 434.191 — Library profile

Libraries nên compile intermediate artifacts có thể được reuse ở nhiều final applications.

---

# 434.192 — Precompiled library

Axiom hỗ trợ:

```text
source package
semantic package
object package
static library
dynamic library
```

---

# 434.193 — Module interface artifact

Có thể tạo:

```text
.foo.axmi
```

hoặc binary tương đương chứa:

```text
public API
type metadata
generic metadata
ABI metadata
documentation metadata
dependency fingerprints
```

Tên extension chỉ là placeholder; binary format sẽ khóa ở artifact specification.

---

# 434.194 — Source-free consumption

Một package binary có thể expose API mà không cần ship source.

---

# 434.195 — Generic library metadata

Nếu consumer cần instantiate generic code, artifact phải chứa đủ semantic/generic information hoặc precompiled instantiations.

---

# 434.196 — AI metadata

Artifact có thể chứa machine-readable:

```text
symbol descriptions
ownership contracts
effects
examples
documentation
ABI
```

---

# 434.197 — No runtime AI metadata requirement

AI metadata không được tự động phình executable.

Nó nằm trong:

```text
debug/interface/documentation artifact
```

---

# 434.198 — Build graph serialization

Compiler có thể serialize build graph để:

- IDE;
- CI;
- AI;
- build cache;
- visualization.

---

# 434.199 — Final architecture

```text
                    ┌────────────────────┐
                    │     axiom CLI      │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
          Build             Check             Run
             │                │                │
             └────────────────┼────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Semantic Database │
                    └─────────┬─────────┘
                              │
          ┌──────────┬────────┼─────────┬─────────┐
          │          │        │         │         │
         LSP        Docs      AI       Test      Fmt
          │          │        │         │         │
          └──────────┴────────┼─────────┴─────────┘
                              │
                           Typed IR
                              │
                         Optimizer
                              │
                       Native Backend
                              │
                    Object / Linker 420
                              │
                         Artifact
```

---

# 434.200 — Hard invariants

BOOTSTRAP-434 khóa:

1. `axiom` là CLI chính thức.
2. Compiler core và tooling dùng chung semantic engine.
3. LSP không có type checker riêng.
4. Diagnostics có stable codes.
5. Diagnostics có machine-readable format.
6. Suggestions có structured source ranges.
7. Formatter deterministic và idempotent.
8. Incremental compilation là kiến trúc nền tảng.
9. Semantic fingerprints dùng cho invalidation/cache.
10. Comptime cache được tích hợp build cache.
11. Generic instantiation cache được tích hợp.
12. Object/link cache từ 420 được giữ.
13. Host và target luôn phân biệt.
14. Cross compilation là first-class.
15. Package manifest là `axiom.toml`.
16. Lock file dùng để đảm bảo dependency reproducibility.
17. Build scripts khác hoàn toàn `comptime`.
18. `comptime` mặc định sandbox/deterministic.
19. Không có textual C-style preprocessor làm build mechanism chính.
20. Compiler không phụ thuộc LLVM/GCC/Clang để native code generation.
21. Native Axiom linker là backend chính.
22. Runtime/library chỉ được link khi cần.
23. AI tooling được cung cấp semantic API chính thức.
24. Compiler metadata không mặc định làm tăng runtime binary.
25. Offline build được hỗ trợ.
26. Build reproducibility được thiết kế từ đầu.
27. Debug info là target-specific artifact.
28. Compiler crash phải có ICE diagnostics.
29. Fuzzing và golden tests là một phần của compiler QA.
30. Toolchain phải đủ khả năng phục vụ quá trình **Axiom self-hosting**.

**BOOTSTRAP-434 hoàn tất.**

---

# BOOTSTRAP-435 — DEBUGGING, PROFILING, SANITIZER & OBSERVABILITY MODEL

Tiếp theo cần khóa một phần rất quan trọng để Axiom có thể được dùng thực tế cho hệ thống lớn: **debugging và performance analysis**.

Axiom không chỉ cần compile nhanh và chạy nhanh. Developer phải có khả năng trả lời chính xác:

```text
Tại sao chương trình crash?
Tại sao dòng này chậm?
Allocation nào gây tốn memory?
Thread nào đang block?
Race xảy ra ở đâu?
Instruction nào tạo bottleneck?
Compiler đã optimize đoạn này như thế nào?
```

435 sẽ thiết kế:

```text
Axiom source
      ↓
debug metadata
      ↓
native debugger
      ↓
breakpoint/watch/stack
      ↓
profiler
      ↓
CPU counters
      ↓
allocation tracing
      ↓
sanitizer
      ↓
optimization feedback
```

và đặc biệt phải giữ nguyên nguyên tắc của Axiom:

> **Debug/profiling/sanitizer là capability của build profile, không phải overhead bắt buộc của production binary.**