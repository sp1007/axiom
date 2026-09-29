# BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE

**Trạng thái: COMPLETED / LOCKED**

BOOTSTRAP-434 định nghĩa lớp công cụ phía trên compiler/build system. Mục tiêu là Axiom phải có một toolchain hoàn chỉnh ngay từ đầu, nhưng **không biến compiler thành một hệ thống khổng lồ hoặc phụ thuộc IDE cụ thể**.

Nguyên tắc lớn:

> **Compiler cung cấp semantic truth; CLI điều khiển compiler; LSP tiêu thụ semantic API; IDE chỉ là client.**

---

## 434.1 — Toolchain architecture

Toolchain Axiom gồm:

```text
axiom
 ├── driver
 ├── frontend
 ├── semantic engine
 ├── comptime engine
 ├── IR/lowering
 ├── optimizer
 ├── codegen
 ├── object writer
 ├── linker
 ├── build system
 ├── package manager
 ├── diagnostic engine
 ├── formatter
 ├── test runner
 ├── documentation generator
 ├── artifact inspector
 └── LSP server
```

Các thành phần này dùng chung semantic infrastructure.

Không cho phép tình trạng:

```text
compiler biết một kiểu
LSP tự parse lại theo cách khác
formatter tự hiểu grammar khác
test runner tự hiểu package khác
```

Nguồn sự thật phải là compiler frontend/semantic model.

---

# 434.2 — Compiler driver

Executable chính:

```text
axiom
```

Compiler driver chịu trách nhiệm:

```text
arguments
    ↓
configuration
    ↓
workspace discovery
    ↓
target/profile resolution
    ↓
dependency graph
    ↓
compilation graph
    ↓
compiler pipeline
    ↓
artifact generation
```

Driver không chứa logic semantic riêng biệt.

---

# 434.3 — Command model

Các command chuẩn:

```text
axiom build
axiom check
axiom run
axiom test
axiom bench
axiom fmt
axiom doc
axiom package
axiom publish
axiom clean
axiom cache
axiom lsp
axiom inspect
axiom disasm
axiom version
```

Command phải có hành vi deterministic.

---

# 434.4 — `axiom build`

```text
axiom build
```

Compile package/workspace và tạo artifact.

Ví dụ:

```text
axiom build --release
axiom build --target x86_64-linux
axiom build --target aarch64-linux
axiom build --target x86_64-windows
```

---

# 434.5 — Build output

Artifact mặc định phụ thuộc package type:

```text
binary
static library
dynamic library
WASM module
object file
```

Compiler không tự động tạo các file trung gian không cần thiết.

---

# 434.6 — `axiom check`

```text
axiom check
```

Chỉ thực hiện các bước cần thiết để xác nhận:

- syntax;
- names;
- types;
- traits;
- generics;
- ownership;
- comptime;
- layout;
- ABI consistency;
- build graph.

Không bắt buộc machine code emission.

Mục tiêu:

```text
check << build
```

về thời gian chạy.

---

# 434.7 — `axiom run`

```text
axiom run
```

Tương đương:

```text
build → execute
```

Có thể truyền arguments:

```text
axiom run -- arg1 arg2
```

Compiler arguments và application arguments phải được phân biệt rõ.

---

# 434.8 — `axiom test`

```text
axiom test
```

Build test artifacts rồi chạy test.

Hỗ trợ:

```text
axiom test
axiom test foo
axiom test --filter parser
axiom test --failed
axiom test --jobs 8
```

Output có hai mode:

```text
human
machine
```

---

# 434.9 — `axiom bench`

Benchmark runner là một command riêng.

```text
axiom bench
```

Compiler không được biến benchmark thành một dạng test thông thường vì benchmark cần:

- warm-up;
- repeated execution;
- statistical measurement;
- outlier handling;
- CPU information;
- compiler/profile information.

Kết quả phải machine-readable.

---

# 434.10 — `axiom fmt`

Formatter canonical:

```text
axiom fmt
axiom fmt --check
```

`--check` không sửa file.

Exit code khác zero nếu source không canonical.

---

# 434.11 — Formatter invariant

Formatter phải có tính chất:

```text
fmt(fmt(source)) == fmt(source)
```

Tức:

> **Idempotent.**

Formatter không được thay đổi semantic meaning.

---

# 434.12 — Formatter authority

Formatter phải dùng parser/AST chính thức.

Không xây formatter bằng regex.

Pipeline:

```text
source
 ↓
lexer
 ↓
parser
 ↓
AST
 ↓
canonical printer
 ↓
source
```

---

# 434.13 — Formatting policy

Default:

```text
4 spaces
no tabs
```

Các quy tắc như:

- brace placement;
- line wrapping;
- trailing comma;
- generic formatting;
- match formatting;
- import grouping

được compiler formatter quyết định thống nhất.

---

# 434.14 — `axiom doc`

```text
axiom doc
```

Sinh documentation từ:

- declarations;
- doc comments;
- signatures;
- traits;
- implementations;
- attributes;
- compile-time metadata.

Documentation generator không được tự suy diễn semantic information.

---

# 434.15 — Documentation formats

Ít nhất:

```text
HTML
JSON
Markdown-compatible
```

JSON đặc biệt quan trọng cho AI tooling.

---

# 434.16 — `axiom package`

Package command chịu trách nhiệm:

```text
package validation
metadata
source archive
artifact metadata
dependency metadata
checksums
```

---

# 434.17 — `axiom publish`

```text
axiom publish
```

Chỉ upload package khi package đã:

- validate;
- resolve dependency;
- generate metadata;
- pass required checks.

Registry không thuộc compiler core.

---

# 434.18 — `axiom clean`

```text
axiom clean
```

Xóa build artifacts.

Không được xóa global cache nếu không có explicit option.

---

# 434.19 — `axiom cache`

Quản lý cache:

```text
axiom cache info
axiom cache clean
axiom cache prune
axiom cache verify
```

Cache phải phân biệt:

```text
source cache
semantic cache
comptime cache
IR cache
object cache
artifact cache
package cache
```

---

# 434.20 — `axiom inspect`

Artifact inspector:

```text
axiom inspect app.exe
```

Có thể hiển thị:

```text
format
architecture
entry point
sections
symbols
imports
exports
relocations
debug info
dependencies
build identity
compiler version
```

---

# 434.21 — `axiom disasm`

Disassembler tích hợp:

```text
axiom disasm app.exe
```

Không yêu cầu objdump/llvm-objdump.

Đây là hệ quả trực tiếp của BOOTSTRAP-420.

---

# 434.22 — Artifact introspection

Có thể query:

```text
axiom inspect --json app.exe
```

Output dành cho:

- scripts;
- CI;
- AI agents;
- debugging;
- binary analysis.

---

# 434.23 — Cross compilation

Compiler driver phải hỗ trợ:

```text
--target <target>
```

Target specification chứa:

```text
architecture
OS
ABI
object format
calling convention
pointer width
endianness
linking model
runtime capabilities
```

---

# 434.24 — Target examples

Ví dụ:

```text
x86_64-pc-windows-msvc
x86_64-unknown-linux-gnu
x86_64-unknown-linux-musl
aarch64-unknown-linux-gnu
aarch64-apple-darwin
aarch64-apple-ios
wasm32-unknown-wasm
```

Tên chính xác có thể được chuẩn hóa ở target registry.

---

# 434.25 — Host ≠ target

Compiler host và target phải hoàn toàn độc lập.

Ví dụ:

```text
Windows x86-64 compiler
        ↓
AArch64 Linux executable
```

Comptime phải biết distinction:

```text
host
target
```

Không được mặc định chúng giống nhau.

---

# 434.26 — Build profiles

Profiles chuẩn:

```text
debug
release
test
bench
sanitize
```

Profile chứa:

```text
optimization
debug info
assertion policy
overflow policy
panic policy
LTO
codegen settings
```

---

# 434.27 — Debug profile

Mục tiêu:

- compile nhanh;
- debug dễ;
- diagnostics đầy đủ;
- optimization vừa phải.

---

# 434.28 — Release profile

Mục tiêu:

- maximum optimization;
- dead-code elimination;
- inlining;
- constant propagation;
- generic optimization;
- linker optimization;
- binary size optimization nếu yêu cầu.

---

# 434.29 — Configuration hierarchy

Configuration resolution:

```text
compiler defaults
 ↓
global config
 ↓
workspace config
 ↓
package config
 ↓
profile
 ↓
target
 ↓
command-line override
```

Override phải deterministic.

---

# 434.30 — Exit codes

Toolchain phải có exit code ổn định.

Ví dụ:

```text
0  success
1  compilation/test failure
2  command-line/configuration error
3  package/dependency resolution failure
4  internal compiler error
5  environment/toolchain failure
```

Các mã cụ thể được lock trong CLI specification.

---

# 434.31 — Diagnostic architecture

Diagnostic là một object có cấu trúc:

```text
Diagnostic {
    severity
    code
    message
    primary_span
    secondary_spans[]
    notes[]
    help[]
    fixes[]
    related[]
}
```

---

# 434.32 — Severity

Chuẩn:

```text
error
warning
info
hint
```

---

# 434.33 — Stable diagnostic codes

Mỗi diagnostic public có code ổn định:

```text
E430001
E431002
E434001
W434001
```

Không dùng message text làm machine identifier.

---

# 434.34 — Diagnostic stability

Message có thể cải thiện theo version.

Code và semantic category phải ổn định trong cùng edition/compatibility policy.

AI agent phải dựa vào:

```text
code
structured fields
spans
fixes
```

không dựa vào wording.

---

# 434.35 — Source span

Diagnostic phải xác định:

```text
file
start offset
end offset
line
column
```

Canonical internal representation dùng byte offsets.

---

# 434.36 — Unicode columns

Do Axiom dùng UTF-8, compiler phải phân biệt:

```text
byte offset
Unicode scalar position
display column
```

Không được nhầm byte offset với visual column.

---

# 434.37 — Primary span

Mỗi error phải có primary location nếu có thể.

Ví dụ:

```text
error[E430101]: mismatched types
  --> src/main.ax:12:9
```

---

# 434.38 — Secondary span

Có thể chỉ ra nguyên nhân liên quan:

```text
expected i32 here
found String here
```

Điều này đặc biệt quan trọng với generic/trait errors.

---

# 434.39 — Notes

Diagnostic có thể có:

```text
note:
help:
```

Nhưng không được biến error message thành một bài văn dài.

---

# 434.40 — Fix-it

Compiler có thể cung cấp machine-readable replacement:

```text
Fix {
    file
    span
    replacement
    applicability
}
```

---

# 434.41 — Fix applicability

Các mức:

```text
machine-applicable
maybe-applicable
display-only
```

AI/IDE chỉ tự động apply loại đầu tiên.

---

# 434.42 — JSON diagnostics

```text
axiom check --diagnostic-format=json
```

Ví dụ conceptual:

```json
{
  "severity": "error",
  "code": "E430101",
  "message": "mismatched types",
  "primary_span": {...},
  "secondary_spans": [...],
  "fixes": [...]
}
```

Schema phải versioned.

---

# 434.43 — JSONL mode

Cho AI/CI:

```text
--diagnostic-format=jsonl
```

Mỗi diagnostic là một record độc lập.

Ưu điểm:

- streaming;
- không cần parse toàn document;
- agent dễ xử lý.

---

# 434.44 — Human diagnostics

Default CLI phải dễ đọc:

```text
error[E430101]: mismatched types
  --> src/math.ax:17:12
   |
17 |     return x + text
   |            ^ expected i32, found String
   |
help: convert the value explicitly before addition
```

Nhưng wording chỉ là presentation layer.

---

# 434.45 — Diagnostic localization

Compiler có thể hỗ trợ localization trong tương lai.

Machine-readable code/schema vẫn giữ nguyên.

---

# 434.46 — Error recovery

Parser phải cố gắng tiếp tục sau syntax error để phát hiện nhiều lỗi trong một lần chạy.

Ví dụ:

```text
missing `}`
missing `)`
unknown identifier
```

không nên dừng ngay ở lỗi đầu tiên nếu recovery an toàn.

---

# 434.47 — Recovery boundary

Compiler phải tránh cascading errors.

Nếu AST node đã mất semantic integrity, các bước sau phải đánh dấu:

```text
error-recovered node
```

thay vì sinh hàng trăm lỗi giả.

---

# 434.48 — Internal compiler error

ICE có format riêng:

```text
internal compiler error
```

Phải bao gồm:

```text
compiler version
target
profile
stage
diagnostic fingerprint
```

Không expose internal memory contents hoặc dữ liệu nhạy cảm mặc định.

---

# 434.49 — Compiler crash reproduction

Có thể tạo:

```text
axiom bug-report
```

để thu thập:

- source hash;
- compiler version;
- target;
- flags;
- ICE fingerprint;
- optional reduced reproducer.

---

# 434.50 — Semantic query API

Compiler semantic engine phải expose query layer:

```text
resolve_symbol
type_of
definition_of
references_of
members_of
implementations_of
documentation_of
signature_of
layout_of
```

LSP dùng API này.

AI tools cũng dùng API này.

---

# 434.51 — LSP architecture

```text
Editor
   ↓
LSP
   ↓
Axiom Language Server
   ↓
Compiler semantic engine
   ↓
incremental project state
```

Không xây một compiler thứ hai cho LSP.

---

# 434.52 — LSP minimum capabilities

Axiom LSP phải hỗ trợ:

- diagnostics;
- completion;
- hover;
- go-to-definition;
- go-to-declaration;
- find references;
- rename;
- signature help;
- document symbols;
- workspace symbols;
- formatting;
- code actions;
- semantic tokens.

---

# 434.53 — Completion

Completion phải dựa trên semantic context.

Ví dụ:

```text
value.
```

LSP biết:

```text
type(value)
→ member set
→ trait extensions
→ visibility
```

Không chỉ grep source text.

---

# 434.54 — Method completion

Với struct-first methods:

```text
v.
```

compiler tìm:

```text
methods whose first parameter accepts v
```

bao gồm:

- inherent methods;
- trait methods;
- extension methods.

---

# 434.55 — Hover

Hover hiển thị:

```text
symbol
type
documentation
source package
visibility
generic parameters
trait constraints
```

---

# 434.56 — Go to definition

Definition phải dựa vào semantic symbol identity.

Không dựa vào tên text đơn thuần.

---

# 434.57 — Find references

Compiler symbol table cung cấp reference index.

Có thể query:

```text
references(SymbolId)
```

---

# 434.58 — Rename

Rename phải hiểu:

```text
identifier identity
shadowing
imports
generic parameters
pattern bindings
field names
methods
```

Không được dùng search/replace đơn giản.

---

# 434.59 — Signature help

Hỗ trợ:

```text
foo(
```

và xác định:

```text
overload
generic parameters
argument index
expected type
```

---

# 434.60 — Semantic tokens

Token classification:

```text
keyword
type
function
method
variable
constant
field
parameter
trait
enum
enum_variant
macro/generated item
attribute
```

Editor tự quyết định màu sắc.

---

# 434.61 — Code actions

Code actions có thể đến từ:

```text
compiler
LSP
formatter
package tools
```

Ví dụ:

```text
add import
qualify trait method
insert explicit cast
implement missing trait member
derive required trait
apply safe fix
```

---

# 434.62 — Import assistance

LSP có thể phát hiện:

```text
unknown symbol
```

và đề xuất import phù hợp.

Không tự động thêm dependency package nếu chưa được yêu cầu.

---

# 434.63 — Trait implementation assistance

Nếu compiler phát hiện:

```text
trait Foo requires:
    a()
    b()
```

LSP có thể tạo skeleton:

```text
impl Foo for Bar {
    ...
}
```

---

# 434.64 — Generic diagnostics

Generic errors phải ưu tiên hiển thị:

```text
root cause
constraint
actual type
expected constraint
```

thay vì dump toàn bộ substitution graph.

---

# 434.65 — Trait solver diagnostics

Ví dụ:

```text
error[E426201]: trait bound not satisfied

required:
    T: Hash

because:
    Map<T, V> requires Hash<T>

found:
    T has no Hash implementation
```

---

# 434.66 — LSP incremental state

Language server giữ:

```text
source snapshot
syntax tree
semantic model
dependency graph
diagnostic cache
symbol index
```

Chỉ invalidated phần liên quan.

---

# 434.67 — Compiler daemon

Optional:

```text
axiom daemon
```

hoặc:

```text
axiom build --watch
```

Daemon giữ compiler state giữa các build.

---

# 434.68 — Watch mode

```text
axiom build --watch
```

Khi source thay đổi:

```text
file changed
 ↓
dependency invalidation
 ↓
recompile affected units
 ↓
link
```

Không rebuild toàn bộ workspace nếu không cần.

---

# 434.69 — Incremental compilation identity

Một compilation unit được cache dựa trên semantic identity, gồm tối thiểu:

```text
source hash
compiler version
edition
target
profile
dependencies
compiler options
comptime inputs
environment contract
```

---

# 434.70 — Dependency invalidation

Thay đổi implementation private không nhất thiết invalidate downstream packages.

Thay đổi public API phải invalidate dependents.

---

# 434.71 — Public interface fingerprint

Mỗi module/package có semantic fingerprint:

```text
PublicInterfaceHash
```

Downstream cache dùng hash này.

---

# 434.72 — Implementation hash

Riêng:

```text
ImplementationHash
```

dùng để xác định object/codegen có cần rebuild hay không.

---

# 434.73 — Two-level incremental cache

```text
interface unchanged
+
implementation changed
```

có thể giữ semantic checking downstream và chỉ regenerate code cần thiết.

---

# 434.74 — Parallel compilation

Compilation graph phải hỗ trợ parallelism:

```text
package A ─┐
package B ─┼→ package D
package C ─┘
```

Independent units compile đồng thời.

---

# 434.75 — Deterministic parallelism

Thứ tự execution có thể khác nhau nhưng output phải giống nhau.

Không được để race làm thay đổi artifact.

---

# 434.76 — Build graph visualization

Có thể:

```text
axiom build --graph
```

Output:

```text
package
 ├── module
 │    ├── dependency
 │    └── dependency
 └── module
```

Machine-readable graph cũng phải tồn tại.

---

# 434.77 — AI compiler interface

Axiom phải có semantic interface đặc biệt dành cho agent.

Không cần để agent parse toàn bộ source nếu compiler đã biết semantic model.

Ví dụ:

```text
axiom query symbol Foo
axiom query type src/main.ax:42:8
axiom query references Foo
axiom query implementations Trait
axiom query diagnostics
```

---

# 434.78 — Machine-readable project state

```text
axiom project --json
```

trả về:

```text
workspace
packages
targets
profiles
dependencies
source roots
artifacts
compiler version
```

---

# 434.79 — AI task loop

Agent có thể thực hiện:

```text
edit
 ↓
axiom check --json
 ↓
parse diagnostics
 ↓
semantic query
 ↓
edit
 ↓
axiom test --json
```

Không cần scrape terminal text.

---

# 434.80 — Semantic source ranges

AI tool có thể query:

```text
symbol_at(file, byte_offset)
```

và nhận:

```text
SymbolId
TypeId
Definition
Scope
Documentation
```

Điều này giảm mạnh việc agent phải đọc toàn bộ file.

---

# 434.81 — Stable IDs

Compiler internal IDs không nên được coi là persistent giữa các compilation.

Nhưng semantic entities có thể có stable identity hash:

```text
package identity
module identity
declaration identity
```

để tooling cache.

---

# 434.82 — AI-friendly edit protocol

Compiler có thể trả về edit:

```text
replace span X-Y
with text Z
```

hoặc semantic transformation:

```text
add_import
rename_symbol
implement_trait
```

Semantic transformation an toàn hơn raw text replacement.

---

# 434.83 — No AI-specific language semantics

Axiom không thêm keyword chỉ vì AI.

AI integration nằm ở:

```text
metadata
semantic APIs
diagnostics
query interfaces
structured artifacts
```

Ngôn ngữ vẫn phải dễ sử dụng cho con người.

---

# 434.84 — Documentation metadata

Declarations có thể cung cấp metadata:

```text
@doc(...)
@deprecated(...)
@since(...)
@must_use
```

Metadata được compiler hiểu ở mức cần thiết.

---

# 434.85 — Deprecated symbols

Diagnostic:

```text
warning[W434xxx]: `foo` is deprecated
help: use `bar` instead
```

LSP có thể cung cấp code action.

---

# 434.86 — Compiler warnings

Warnings phải configurable:

```text
-Wall
-Werror
-Wno-unused
```

hoặc syntax Axiom-specific tương đương.

---

# 434.87 — Warning policy

Warnings không được làm thay đổi generated code semantic behavior.

---

# 434.88 — Lints

Compiler core chỉ chứa lints có giá trị semantic rõ ràng.

Các style lint phức tạp có thể nằm ở tooling.

Ví dụ:

```text
unused variable
unreachable code
unnecessary clone
unnecessary allocation
```

có thể là compiler diagnostics.

---

# 434.89 — Performance diagnostics

Compiler có thể cung cấp:

```text
allocation count
inlining decisions
vectorization
bounds-check elimination
generic instantiations
code size
```

thông qua:

```text
axiom build --explain
```

hoặc machine-readable reports.

---

# 434.90 — Optimization remarks

Ví dụ:

```text
remark:
    bounds check eliminated

remark:
    function inlined

remark:
    allocation promoted to stack
```

Không được mặc định spam terminal.

---

# 434.91 — Binary size report

```text
axiom inspect --size app.exe
```

có thể phân tích:

```text
text
rodata
data
bss
debug
runtime
per-function size
per-symbol size
```

---

# 434.92 — Linker diagnostics

Native linker của Axiom phải trả diagnostics thống nhất với compiler.

Ví dụ:

```text
E420xxx unresolved symbol
E420xxx duplicate symbol
E420xxx relocation overflow
E420xxx invalid relocation
```

Không expose raw linker internals như giao diện duy nhất.

---

# 434.93 — Object diagnostics

```text
axiom inspect object.o
```

phải hiểu object formats do BOOTSTRAP-420 định nghĩa.

---

# 434.94 — Debug information

Compiler hỗ trợ:

```text
DWARF
CodeView/PDB
```

tùy target.

Debug information không được ảnh hưởng release artifact nếu disabled.

---

# 434.95 — Source maps

WASM cần source mapping.

Axiom phải emit source maps khi requested.

---

# 434.96 — Reproducible builds

Hai build với cùng:

```text
source
dependencies
compiler
target
profile
configuration
```

phải tạo artifact byte-identical hoặc có cơ chế normalize các trường vốn không deterministic.

---

# 434.97 — Build identity

Artifact metadata có:

```text
source identity
dependency identity
compiler identity
target identity
profile identity
```

Nhưng không được nhúng timestamp ngẫu nhiên vào binary.

---

# 434.98 — Timestamp normalization

Reproducible mode:

```text
SOURCE_DATE_EPOCH
```

hoặc cơ chế Axiom-native tương đương.

---

# 434.99 — Environment capture

Build system phải phân biệt:

```text
declared build input
undeclared host environment
```

Build không được vô tình phụ thuộc vào environment không khai báo.

---

# 434.100 — Build environment

Các environment-dependent values phải explicit:

```text
target
profile
features
comptime configuration
build script outputs
```

---

# 434.101 — Build scripts

Build script **không phải comptime**.

Nếu tồn tại:

```text
build.ax
```

hoặc cơ chế tương đương, nó chạy trong build phase sandbox/capability model.

Build script mới được phép:

- filesystem;
- environment;
- external tool;
- code generation;
- platform probing.

---

# 434.102 — Comptime boundary

Comptime của BOOTSTRAP-431:

```text
deterministic
sandboxed
language-level
```

Build script:

```text
external
capability-based
environment-aware
```

Hai cơ chế không được nhập làm một.

---

# 434.103 — Package manager

Package manager phải hỗ trợ:

```text
local path
git
registry
archive
```

Registry là optional ecosystem component.

---

# 434.104 — No mandatory central registry

Axiom package system không phụ thuộc một server trung tâm duy nhất.

Package có thể được lấy từ:

```text
path
git repository
private registry
public registry
artifact store
```

---

# 434.105 — Dependency lock

Workspace application nên có:

```text
axiom.lock
```

để khóa dependency resolution.

---

# 434.106 — Dependency identity

Dependency identity gồm:

```text
name
source
version/revision
checksum
features
```

---

# 434.107 — Semantic versioning

Package manager có thể hỗ trợ semantic version constraints:

```text
1.x
^1.4
>=1.4,<2
```

Nhưng lockfile mới quyết định version thực tế.

---

# 434.108 — Dependency verification

Package cache phải hỗ trợ checksum/hash verification.

Registry signatures có thể bổ sung sau.

---

# 434.109 — Dependency graph cycles

Package dependency cycle mặc định không hợp lệ.

Module cycles có thể được phép ở mức hạn chế nếu declaration graph vẫn acyclic semantic dependency.

---

# 434.110 — Feature flags

Package features phải deterministic.

Ví dụ:

```text
features = [
    "simd",
    "network",
    "tls"
]
```

Feature resolution phải được ghi vào build identity.

---

# 434.111 — Optional dependencies

Optional dependency chỉ được đưa vào compilation graph khi feature yêu cầu.

Điều này giúp giảm binary size.

---

# 434.112 — Native libraries

Axiom package có thể cung cấp:

```text
native static library
native dynamic library
headers/interface metadata
ABI metadata
```

---

# 434.113 — FFI package metadata

Package FFI phải mô tả:

```text
target
architecture
ABI
calling convention
symbols
ownership contracts
layout
```

---

# 434.114 — Toolchain self-description

```text
axiom version
```

phải trả:

```text
compiler version
language edition
host
supported targets
codegen backend version
package format version
```

---

# 434.115 — Edition

Axiom hỗ trợ language edition để evolution syntax/semantics.

Ví dụ conceptual:

```text
edition = "2026"
```

Edition không nên tạo fork compiler.

---

# 434.116 — Compatibility

Compiler mới có thể compile source edition cũ theo compatibility rules.

Breaking changes phải thuộc edition mới hoặc explicit migration.

---

# 434.117 — Migration tooling

```text
axiom fix --edition-next
```

có thể tạo semantic/source transformations.

---

# 434.118 — Project initialization

Có thể có:

```text
axiom new app
axiom new lib
```

Sinh project tối thiểu.

Không sinh hàng chục file không cần thiết.

---

# 434.119 — Minimal project

Ví dụ:

```text
app/
 ├── axiom.toml
 └── src/
      └── main.ax
```

Library:

```text
lib/
 ├── axiom.toml
 └── src/
      └── lib.ax
```

---

# 434.120 — Workspace

Workspace:

```text
workspace/
 ├── axiom.workspace
 ├── app/
 ├── core/
 └── tools/
```

Một build graph chung.

---

# 434.121 — Source root

Package manifest xác định source root.

Không dựa vào tên thư mục đặc biệt nếu manifest đã chỉ rõ.

---

# 434.122 — Module discovery

Module mapping phải deterministic.

Không tự động include mọi file trong directory nếu điều đó làm thay đổi project semantics ngoài ý muốn.

---

# 434.123 — Package API

Package public API có thể được xuất dưới dạng semantic metadata:

```text
axiom api package
```

Useful cho:

- documentation;
- ABI checking;
- AI;
- dependency analysis.

---

# 434.124 — API diff

Có thể:

```text
axiom api-diff old.api new.api
```

Phát hiện:

```text
removed symbol
changed signature
changed visibility
changed trait requirement
changed ABI
```

---

# 434.125 — ABI diff

ABI-sensitive changes phải được detect riêng.

Ví dụ:

```text
@repr(C)
field addition
alignment change
calling convention change
export signature change
```

---

# 434.126 — Package tests

Package có thể chứa:

```text
unit tests
integration tests
compile-fail tests
documentation tests
benchmark tests
```

---

# 434.127 — Test discovery

Test runner không nên phụ thuộc naming convention duy nhất.

Compiler metadata đánh dấu test entities.

---

# 434.128 — Test isolation

Mỗi test có thể chạy:

```text
same process
isolated process
```

theo annotation/profile.

---

# 434.129 — Test output

Machine result:

```text
test_id
status
duration
stdout
stderr
failure
diagnostics
```

---

# 434.130 — Snapshot diagnostics

Compiler phải hỗ trợ golden diagnostic tests.

Ví dụ:

```text
tests/compile_fail/type_mismatch.ax
tests/compile_fail/type_mismatch.expected.json
```

---

# 434.131 — LSP test harness

LSP phải có protocol-level tests:

```text
initialize
open
change
diagnostics
completion
hover
rename
shutdown
```

---

# 434.132 — Formatter tests

Mỗi grammar construct phải có:

```text
input
expected formatted output
```

và idempotency test.

---

# 434.133 — CLI tests

Test:

```text
command
arguments
exit code
stdout
stderr
artifact
```

---

# 434.134 — Toolchain schema versioning

Machine-readable outputs có:

```text
schema_version
```

Không được silently thay đổi JSON schema.

---

# 434.135 — JSON schema

Các schema quan trọng:

```text
diagnostic.schema.json
build-result.schema.json
test-result.schema.json
project.schema.json
artifact.schema.json
semantic-query.schema.json
```

---

# 434.136 — Streaming

Long operations nên stream events:

```text
build started
compiling module
linking
artifact generated
```

AI agent có thể consume mà không chờ toàn bộ process.

---

# 434.137 — Build events

Conceptual:

```text
BuildEvent {
    kind
    package
    unit
    target
    status
    duration
    artifact
}
```

---

# 434.138 — Progress UI

Human CLI có progress.

Machine mode không được trộn ANSI control sequences vào JSON.

---

# 434.139 — Quiet mode

```text
--quiet
```

chỉ hiển thị diagnostics/errors hoặc kết quả cuối.

---

# 434.140 — Verbose mode

```text
--verbose
```

hiển thị build decisions.

---

# 434.141 — Trace mode

Compiler developers có thể dùng:

```text
--trace
```

Nhưng trace không phải stable API.

---

# 434.142 — Compiler performance profiling

Có thể:

```text
axiom build --timings
```

cho:

```text
parse
resolve
typecheck
comptime
IR
optimization
codegen
link
```

---

# 434.143 — Memory profiling

Development build có thể báo:

```text
peak compiler memory
cache memory
AST memory
IR memory
```

---

# 434.144 — Build server protocol

Nếu daemon được dùng, client/server protocol phải versioned.

Compiler daemon không được trở thành requirement để compile.

---

# 434.145 — Daemon failure

Nếu daemon crash:

```text
CLI → restart/fallback
```

Compilation phải có khả năng chạy one-shot.

---

# 434.146 — Remote cache

Remote cache có thể được hỗ trợ sau.

Nhưng cache artifact phải content-addressed và verified.

---

# 434.147 — Distributed builds

Không phải core requirement.

Build graph được thiết kế sao cho sau này có thể phân phối compilation units.

---

# 434.148 — Security

Package manager phải tránh chạy code arbitrary chỉ vì dependency được resolve.

Build scripts có capability restrictions.

---

# 434.149 — Untrusted package

Package source được compile như source.

Không được mặc định có quyền:

```text
filesystem
network
process execution
```

trong comptime.

---

# 434.150 — Compiler plugin boundary

Compiler plugin không được trở thành dependency bắt buộc của language semantics.

Các extension nên dùng:

```text
comptime
derive
semantic metadata
build tools
```

trước khi cho phép native compiler plugins.

---

# 434.151 — Macro tooling

Nếu Axiom có macro/generator, LSP phải thấy generated semantic entities.

Generated source không được trở thành “black box”.

---

# 434.152 — Generated code diagnostics

Diagnostic trên generated code phải map ngược về:

```text
generator source
invocation site
generated span
```

---

# 434.153 — Documentation for generated APIs

Generated declarations phải có documentation origin nếu có thể.

---

# 434.154 — Package metadata for AI

Package metadata có thể cung cấp:

```text
public symbols
types
traits
examples
effects
allocation behavior
threading requirements
ABI
platform constraints
```

Đây là metadata machine-readable, không phải AI-specific semantic hack.

---

# 434.155 — API usage discovery

Agent có thể query:

```text
find symbol matching:
    "parse JSON"
```

nhưng semantic search là tooling/ecosystem capability, không phải language syntax.

---

# 434.156 — Compiler query performance

Semantic queries phải tận dụng incremental caches.

Một hover không được trigger full native compilation.

---

# 434.157 — Partial project validity

LSP phải hoạt động khi project đang có lỗi.

Compiler cần error-tolerant semantic representation.

---

# 434.158 — Missing dependency

LSP có thể hiển thị:

```text
dependency unavailable
```

nhưng vẫn parse local code.

---

# 434.159 — Broken source

Editor đang gõ:

```text
fn foo(x: i32 {
```

LSP vẫn phải recover AST tốt nhất có thể.

---

# 434.160 — Cancellation

Long compiler/LSP operations phải cancel được.

Ví dụ:

```text
completion request
```

không nên tiếp tục computation nếu editor đã gửi request mới.

---

# 434.161 — Request priority

LSP ưu tiên:

```text
diagnostics
completion
hover
navigation
```

trước background indexing.

---

# 434.162 — Background indexing

Workspace symbol/reference indexing có thể chạy background.

Không block typing.

---

# 434.163 — File watcher

LSP/build daemon cần file watcher native platform khi có thể.

Fallback polling tồn tại nhưng không phải default.

---

# 434.164 — Terminal output

Compiler output phải hỗ trợ:

```text
plain
ANSI
JSON
JSONL
```

---

# 434.165 — CI mode

```text
axiom ci
```

có thể là convenience command:

```text
fmt --check
check
test
package validation
```

Không cần thiết phải là một compiler subsystem riêng.

---

# 434.166 — Reproducibility verification

```text
axiom build --verify-reproducible
```

có thể build hai lần và compare normalized artifacts.

---

# 434.167 — Artifact manifest

Mỗi build có optional manifest:

```text
artifact
target
profile
compiler
dependencies
hash
debug-info
```

---

# 434.168 — Binary provenance

Có thể query provenance:

```text
axiom inspect --provenance app.exe
```

---

# 434.169 — Source embedding

Release binary không mặc định embed full source.

Debug builds có thể embed source/debug information tùy configuration.

---

# 434.170 — Compiler self-hosting compatibility

Toolchain architecture phải cho phép compiler Axiom cuối cùng được viết bằng Axiom.

Không command nào phụ thuộc vào compiler implementation language.

---

# 434.171 — Bootstrap toolchain

Trong giai đoạn bootstrap:

```text
bootstrap compiler
    ↓
Axiom compiler
    ↓
self-hosted Axiom compiler
```

Các CLI contracts phải giữ ổn định qua transition.

---

# 434.172 — Native compiler dependency invariant

Không được yêu cầu:

```text
LLVM
GCC
Clang
MSVC compiler
Rust compiler
```

để thực hiện Axiom code generation/linking chuẩn.

OS SDK/import libraries có thể là platform inputs khi target yêu cầu.

---

# 434.173 — External SDK distinction

Ví dụ Windows:

```text
Windows SDK
```

không được coi là “third-party compiler dependency”.

Axiom tự generate PE/COFF và link các system libraries theo ABI/platform contract.

---

# 434.174 — Toolchain bootstrap dependency

Bootstrap compiler có thể tạm thời sử dụng host tooling trong giai đoạn đầu.

Nhưng final architecture phải self-host.

---

# 434.175 — CLI simplicity invariant

Không tạo command cho mọi permutation.

Ví dụ:

```text
axiom build --release --target ...
```

thay vì hàng chục command riêng.

---

# 434.176 — Configuration-over-command explosion

Complexity nằm trong:

```text
manifest/profile/config
```

không nằm trong tên command.

---

# 434.177 — Standard aliases

Có thể hỗ trợ:

```text
axiom b   → build
axiom c   → check
axiom t   → test
```

nhưng canonical command names vẫn đầy đủ.

---

# 434.178 — Help system

```text
axiom --help
axiom build --help
```

Help phải machine-readable optional:

```text
axiom --help --json
```

---

# 434.179 — Completion scripts

CLI có thể generate shell completion:

```text
bash
zsh
fish
powershell
```

---

# 434.180 — Environment diagnostics

Khi build fail vì environment:

```text
target unavailable
SDK missing
link input missing
permission denied
```

diagnostic phải chỉ rõ:

```text
what was required
what was found
how to inspect configuration
```

---

# 434.181 — Toolchain doctor

Một convenience command:

```text
axiom doctor
```

kiểm tra:

```text
compiler
targets
cache
SDK
link environment
package registry
LSP
```

---

# 434.182 — Doctor must not mutate

`axiom doctor` mặc định chỉ kiểm tra.

Không tự cài hoặc sửa environment.

---

# 434.183 — Documentation examples

Doc examples có thể được compile/test tự động.

Điều này tránh documentation drift.

---

# 434.184 — Compile-tested documentation

```text
/// ```
/// let x := add(1, 2)
/// ```
```

Nếu enabled, example được compile như test.

---

# 434.185 — Example isolation

Documentation example có thể chạy:

```text
compile only
compile + execute
```

theo metadata.

---

# 434.186 — Error-message quality

Diagnostics phải ưu tiên:

```text
what happened
where
why
what expected
possible fix
```

Không đưa quá nhiều compiler implementation detail.

---

# 434.187 — Error chaining

Một diagnostic có thể tham chiếu diagnostics khác:

```text
caused_by
related_to
```

để AI reconstruct root cause graph.

---

# 434.188 — Diagnostic fingerprint

Mỗi diagnostic có optional fingerprint:

```text
diagnostic kind
symbol identity
source region
```

Useful để CI/IDE theo dõi lỗi qua nhiều builds.

---

# 434.189 — Stable semantic errors

Compiler phải phân biệt:

```text
user error
configuration error
dependency error
compiler bug
environment error
```

Không gom tất cả thành exit code 1/message text.

---

# 434.190 — Test result contract

Test output machine-readable phải có schema ổn định:

```text
passed
failed
ignored
skipped
timeout
crashed
```

---

# 434.191 — Benchmark contract

Benchmark output chứa:

```text
iterations
duration
statistics
compiler
target
profile
```

Không dùng benchmark result để compiler tự thay đổi optimization mặc định.

---

# 434.192 — Artifact inspection as first-class feature

Vì Axiom tự kiểm soát native emission, developer phải có khả năng quan sát:

```text
source
→ IR
→ object
→ executable
```

---

# 434.193 — IR inspection

```text
axiom inspect --ir
```

hoặc command tương đương.

IR format debug-oriented, không phải public stable ABI.

---

# 434.194 — Machine-code inspection

```text
axiom disasm
```

cho phép kiểm tra:

```text
instruction bytes
symbol
source location
relocation
```

---

# 434.195 — Compilation pipeline dump

Developer mode:

```text
--emit ast
--emit hir
--emit mir
--emit ir
--emit obj
```

Các tên IR chính xác sẽ được khóa trong compiler architecture.

---

# 434.196 — Emit controls

User có thể chọn artifact intermediate:

```text
check
ast
semantic
ir
obj
exe
```

Không bắt buộc generate tất cả.

---

# 434.197 — Compiler extensibility

Toolchain phải có internal plugin points nhưng public extension API chỉ được expose khi ABI/API ổn định.

---

# 434.198 — Toolchain invariants

Các invariant quan trọng:

1. Một compiler semantic engine duy nhất.
2. CLI không chứa semantic duplicate.
3. LSP dùng semantic engine.
4. Formatter dùng parser chính thức.
5. Diagnostics có stable codes.
6. Machine-readable diagnostics là first-class.
7. JSON/JSONL schema versioned.
8. Incremental compilation là kiến trúc nền.
9. Build graph deterministic.
10. Parallel build không làm thay đổi output.
11. Cross compilation là first-class.
12. Host và target tách biệt.
13. Compiler daemon optional.
14. One-shot compilation luôn tồn tại.
15. Cache content-addressed.
16. Reproducible build được hỗ trợ.
17. Native object/linker tooling tích hợp.
18. Không cần LLVM/GCC/Clang cho final native codegen.
19. LSP không phải compiler thứ hai.
20. AI tooling dùng semantic API thay vì scrape text.
21. Comptime và build scripts tách biệt.
22. Package registry không phải dependency của language core.
23. Package dependency resolution deterministic.
24. Formatter canonical/idempotent.
25. Test/bench/diagnostic results machine-readable.
26. Toolchain không tự động mutate environment ngoài explicit commands.
27. CLI giữ đơn giản.
28. IDE là client, không phải thành phần bắt buộc.
29. Compiler có thể self-host.
30. Binary inspection/debugging là first-class.

---

# BOOTSTRAP-434.199 — Kiến trúc cuối

```text
                    ┌───────────────┐
                    │ IDE / Editor  │
                    └───────┬───────┘
                            │ LSP
                    ┌───────▼───────┐
                    │  Axiom LSP    │
                    └───────┬───────┘
                            │
┌──────────────┐     ┌──────▼──────────┐
│ CLI / CI     ├────►│ Compiler Driver │
└──────────────┘     └──────┬──────────┘
                            │
                    ┌───────▼────────┐
                    │ Semantic Engine │
                    └───────┬────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
         Comptime       Build Graph      Package
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                         IR
                            │
                     Optimization
                            │
                        Codegen
                            │
                    Object / Linker
                            │
                       Artifact
```

Đây là toolchain architecture chính thức của Axiom.

---

# BOOTSTRAP-434.200 — Kết luận

**BOOTSTRAP-434 hoàn tất.**

Axiom hiện đã có đầy đủ chuỗi:

```text
Language
→ Type System
→ Memory
→ Concurrency
→ Error
→ Generics/Traits
→ Syntax
→ Comptime
→ Modules/Build
→ Standard Library
→ Toolchain
```

Bước tiếp theo hợp lý là khóa **độ tin cậy của compiler**, bởi từ đây không nên tiếp tục thêm feature mà chưa có cơ chế chứng minh compiler thực sự compile đúng.

---

# BOOTSTRAP-435 — TESTING, CONFORMANCE, VALIDATION, FUZZING, BENCHMARKING & COMPILER CORRECTNESS

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của BOOTSTRAP-435:

> Không chỉ xác định Axiom *phải làm gì*, mà phải xác định cách chứng minh compiler Axiom *đang làm đúng*.

Đây là task đặc biệt quan trọng vì Axiom có:

- compiler riêng;
- optimizer riêng;
- machine-code encoder riêng;
- object writer riêng;
- linker riêng;
- ABI riêng;
- comptime;
- ownership;
- generics;
- trait solver;
- native targets.

Một compiler như vậy không thể chỉ dựa vào vài chương trình mẫu.

---

## 435.1 — Testing pyramid

Axiom testing architecture:

```text
                    End-to-end
                       ▲
                  Integration
                       ▲
                 Semantic tests
                       ▲
                IR/codegen tests
                       ▲
              Machine/object tests
                       ▲
                Unit/property tests
                       ▲
                     Fuzzing
```

Mỗi tầng kiểm tra một loại invariant khác nhau.

---

# 435.2 — Compiler correctness layers

Compiler correctness được chia thành:

```text
Lexer correctness
Parser correctness
AST correctness
Name-resolution correctness
Type-check correctness
Trait-solver correctness
Comptime correctness
Ownership correctness
IR correctness
Optimization correctness
ABI correctness
Instruction encoding correctness
Object-format correctness
Linker correctness
Runtime correctness
```

---

# 435.3 — Golden tests

Mỗi compiler subsystem phải có golden tests khi output có tính ổn định.

Ví dụ:

```text
source
→ AST dump
→ expected AST
```

hoặc:

```text
source
→ IR
→ expected IR
```

---

# 435.4 — Lexer tests

Kiểm tra:

- Unicode identifiers;
- UTF-8;
- escapes;
- numbers;
- strings;
- comments;
- operators;
- attributes;
- invalid UTF-8;
- malformed literals.

---

# 435.5 — Parser tests

Kiểm tra toàn bộ grammar.

Mỗi construct phải có:

```text
valid
invalid
edge cases
ambiguity cases
recovery cases
```

---

# 435.6 — Formatter tests

Mỗi valid AST phải có canonical representation.

Test:

```text
parse(source)
→ format
→ parse
```

AST semantic equivalence phải giữ nguyên.

---

# 435.7 — Round-trip invariant

Phải đảm bảo:

```text
parse(format(parse(source)))
```

tạo semantic-equivalent AST.

---

# 435.8 — Name resolution tests

Kiểm tra:

```text
scope
shadowing
imports
re-exports
visibility
modules
generic parameters
associated items
```

---

# 435.9 — Type checker tests

Test matrix:

```text
primitive
struct
enum
tuple
array
slice
function
generic
trait
dyn Trait
closure
pointer
opaque
never
unit
```

---

# 435.10 — Negative type tests

Compile-fail suite phải được xem là first-class.

Ví dụ:

```text
wrong argument
wrong return
missing trait
ambiguous method
invalid cast
invalid move
```

---

# 435.11 — Trait solver tests

Test:

```text
direct impl
generic impl
associated types
associated constants
default methods
coherence
orphan rules
recursive constraints
ambiguity
specialization
dyn compatibility
```

---

# 435.12 — Generic instantiation tests

Test:

```text
generic function
generic struct
generic enum
nested generic
const generic
generic trait
generic method
```

---

# 435.13 — Ownership tests

Kiểm tra:

```text
move
copy
clone
drop
partial initialization
early return
defer
panic cleanup
scope cleanup
```

---

# 435.14 — Ownership negative suite

Compiler phải reject:

```text
use after move
double owner destruction
invalid move
invalid reassignment
invalid cleanup
```

trong safe language subset.

---

# 435.15 — Unsafe boundary tests

Unsafe operations phải:

```text
compile inside unsafe
reject where unsafe is required but absent
```

Compiler không được vô tình “safe hóa” raw-pointer operation.

---

# 435.16 — Comptime tests

Test:

```text
constant arithmetic
const functions
const generic
type queries
layout queries
comptime branches
generated declarations
resource limits
```

---

# 435.17 — Comptime determinism test

Cùng input phải tạo:

```text
same value
same generated AST
same metadata
```

trên cùng semantic target conditions.

---

# 435.18 — Comptime sandbox tests

Comptime không được tự ý:

```text
read arbitrary file
network
spawn process
modify external state
```

trừ capability explicitly defined nếu language sau này bổ sung.

---

# 435.19 — IR verification

Mỗi IR pass phải có verifier.

Ví dụ:

```text
verify_types
verify_cfg
verify_ssa
verify_memory
verify_calls
verify_terminators
```

---

# 435.20 — Pass invariant

Mỗi optimization pass phải thỏa:

```text
valid IR
→ pass
→ valid IR
```

---

# 435.21 — Optimization correctness

Optimization phải bảo toàn observable semantics.

Conceptual:

```text
Semantics(IR_before)
==
Semantics(IR_after)
```

trong phạm vi language-defined behavior.

---

# 435.22 — Differential optimization testing

Cùng source:

```text
-O0
-O1
-O2
-O3
```

phải cho cùng observable result.

---

# 435.23 — Undefined behavior

Nếu chương trình có UB, test không được yêu cầu compiler giữ một behavior không được language guarantee.

Test suite phải phân biệt:

```text
defined behavior
implementation-defined
target-defined
undefined behavior
```

---

# 435.24 — Constant folding tests

Ví dụ:

```text
1 + 2
```

phải có thể fold.

Nhưng overflow policy phải được test theo đúng semantics:

```text
checked
wrapping
saturating
```

---

# 435.25 — Floating-point tests

Comptime và optimizer phải tôn trọng floating-point policy.

Không được biến:

```text
NaN
Inf
signed zero
rounding
```

thành semantics khác nếu optimization mode không cho phép.

---

# 435.26 — Machine encoder tests

Mỗi instruction encoding cần golden test:

```text
IR instruction
→ machine instruction
→ exact bytes
```

---

# 435.27 — ISA reference vectors

Machine encoder dùng test vectors độc lập:

```text
opcode
operands
expected bytes
```

---

# 435.28 — Decoder/encoder round trip

Nếu Axiom có disassembler decoder:

```text
encode(instruction)
→ bytes
→ decode(bytes)
→ instruction
```

phải preserve semantic instruction.

---

# 435.29 — Relocation tests

Test:

```text
ABS
PCREL
branch
GOT
PLT
TLS
symbol difference
overflow
```

---

# 435.30 — Object format tests

Mỗi backend:

```text
ELF
PE/COFF
Mach-O
WASM
```

có structural validation tests.

---

# 435.31 — Object parser independence

Nên có validator độc lập với object writer.

Không kiểm tra:

```text
writer output == writer expectation
```

bằng cùng code path.

Nếu writer và validator cùng bug, test sẽ vô nghĩa.

---

# 435.32 — ELF tests

Kiểm tra:

```text
headers
sections
segments
symbols
relocations
entry point
alignment
TLS
dynamic linking metadata
```

---

# 435.33 — PE/COFF tests

Kiểm tra:

```text
COFF headers
sections
imports
exports
relocations
entry point
subsystem
alignment
```

---

# 435.34 — Mach-O tests

Kiểm tra:

```text
load commands
segments
sections
symbols
relocations
exports
entry point
code signature metadata where applicable
```

---

# 435.35 — WASM tests

Kiểm tra:

```text
module
types
imports
exports
functions
code
data
custom sections
```

---

# 435.36 — Linker tests

Test:

```text
symbol resolution
archive extraction
weak symbols
duplicate symbols
relocation
section placement
dead section elimination
entry point
imports/exports
```

---

# 435.37 — Linker differential testing

Với supported formats, có thể đối chiếu structural behavior với independently generated object files.

Không cần sử dụng third-party linker để tạo production artifact.

Third-party tools chỉ có thể làm oracle trong test infrastructure nếu cần.

---

# 435.38 — ABI tests

Mỗi ABI có test suite riêng:

```text
SysV64
Win64
AAPCS64
Apple AArch64
WASM
```

---

# 435.39 — ABI call tests

Test combinations:

```text
i32
i64
f32
f64
small struct
large struct
array
vector
mixed integer/float
return values
```

---

# 435.40 — FFI tests

C ABI interoperability tests phải kiểm tra:

```text
arguments
return
struct layout
alignment
strings
callbacks
function pointers
ownership contracts
```

---

# 435.41 — Native executable smoke tests

Mỗi supported target có chương trình tối thiểu:

```text
main → return 42
```

sau đó:

```text
arithmetic
function call
struct
array
string
allocation
thread
```

theo capability.

---

# 435.42 — Cross-target test matrix

Không cần chạy mọi test trên mọi target.

Có ba tầng:

```text
compile-only
execute
ABI/native integration
```

---

# 435.43 — Host-independent compile tests

Các tests như:

```text
parser
type checker
IR
comptime
```

có thể chạy trên host duy nhất.

---

# 435.44 — Target execution tests

Các tests yêu cầu native execution phải chạy trên target tương ứng hoặc emulator/CI runner phù hợp.

---

# 435.45 — Freestanding tests

Axiom phải test:

```text
no std
no allocator
no OS runtime
```

để đảm bảo runtime boundary thực sự modular.

---

# 435.46 — Runtime component tests

Từng component:

```text
allocator
thread
panic
IO
async
```

được test độc lập.

---

# 435.47 — Memory tests

Kiểm tra:

```text
allocation
deallocation
reallocation
alignment
zero-size
OOM
arena
pool
stack allocator
```

---

# 435.48 — Resource lifetime tests

Kiểm tra deterministic destruction bằng observable test resource.

Ví dụ conceptual:

```text
resource created
resource moved
resource dropped
```

---

# 435.49 — Drop order test

Phải xác nhận:

```text
reverse acquisition order
```

và partial initialization behavior.

---

# 435.50 — Panic cleanup tests

Nếu:

```text
panic
```

xảy ra giữa nhiều resource acquisitions:

```text
all initialized resources cleaned
```

theo policy.

---

# 435.51 — Concurrency tests

Test:

```text
thread
join
detach
mutex
rwlock
atomic
channel
TLS
async
cancellation
```

---

# 435.52 — Memory ordering tests

Các atomic tests phải chạy trên architectures khác nhau khi có thể:

```text
x86-64
AArch64
```

để tránh test chỉ vô tình pass do memory model mạnh hơn.

---

# 435.53 — Race tests

Optional race instrumentation có thể được bật:

```text
-sanitize=thread
```

hoặc equivalent.

---

# 435.54 — Sanitizer suite

Axiom nên hỗ trợ compiler/runtime instrumentation cho:

```text
address
undefined behavior
thread
integer
bounds
```

khi target cho phép.

---

# 435.55 — Sanitizer separation

Sanitizer instrumentation không được xuất hiện trong release binary nếu không requested.

---

# 435.56 — Property-based testing

Compiler components phù hợp với property testing:

```text
lexer
parser
formatter
type canonicalization
constant evaluator
machine encoder
object parser
```

---

# 435.57 — Lexer property

Random valid tokens phải:

```text
lex
→ token stream
→ stable re-lex after formatting where applicable
```

---

# 435.58 — Parser fuzzing

Parser phải có thể nhận arbitrary bytes mà:

```text
never memory-corrupt
never hang indefinitely
never crash unexpectedly
```

---

# 435.59 — Compiler fuzzing

Fuzz target chính:

```text
source bytes
```

Compiler phải:

```text
accept
reject
diagnose
```

nhưng không crash/hang vượt timeout.

---

# 435.60 — Fuzzing stages

Có fuzz targets riêng:

```text
lexer
parser
AST
type checker
comptime
trait solver
IR
optimizer
codegen
object parser
linker
LSP
```

---

# 435.61 — Fuzz corpus

Corpus phải tích lũy:

```text
interesting programs
previous bugs
minimal reproducers
boundary cases
```

---

# 435.62 — Crash preservation

Mỗi compiler crash được biến thành regression test sau khi reduced.

---

# 435.63 — Fuzz reduction

Fuzzer phải cố gắng giảm:

```text
10,000-line failure
→ 20-line reproducer
```

để compiler developer xử lý.

---

# 435.64 — Hang detection

Fuzzing phải có:

```text
wall-clock timeout
instruction/step budget
memory limit
```

đặc biệt cho comptime và trait solver.

---

# 435.65 — Compiler resource limits

Compiler phải có giới hạn an toàn cho:

```text
recursion
comptime steps
memory
generated code
generic instantiation
trait solving
macro expansion
```

---

# 435.66 — No infinite generic expansion

Compiler phải phát hiện/giới hạn:

```text
T → Foo<T> → Foo<Foo<T>> ...
```

---

# 435.67 — Trait solver termination

Trait solver phải có strategy bảo đảm termination hoặc explicit bounded failure.

---

# 435.68 — Comptime termination

Không yêu cầu compiler chứng minh termination toán học.

Thay vào đó:

```text
step budget
recursion budget
memory budget
```

---

# 435.69 — Differential compiler testing

Nếu có nhiều compiler implementation trong bootstrap:

```text
bootstrap compiler
vs
self-hosted compiler
```

có thể compile cùng source và so sánh:

```text
diagnostics
IR
object
behavior
```

---

# 435.70 — Bootstrap equivalence

Khi compiler Axiom tự host:

```text
Compiler A compiled by B
Compiler B compiled by A
```

phải dần hội tụ về artifact-equivalent behavior.

---

# 435.71 — Self-hosting test

Pipeline:

```text
stage0 compiler
→ stage1 Axiom compiler
→ stage2 compiler built by stage1
→ stage3 compiler built by stage2
```

Hash convergence hoặc semantic equivalence được kiểm tra.

---

# 435.72 — Stage stability

Nếu:

```text
stage2 != stage3
```

compiler team phải điều tra.

Không bắt buộc byte-identical trong mọi bootstrap configuration, nhưng semantic/compiler output stability phải đạt contract.

---

# 435.73 — Compiler regression database

Mọi bug compiler được lưu thành:

```text
issue
→ minimal source
→ expected behavior
→ regression test
```

---

# 435.74 — Regression categories

```text
frontend
semantic
ownership
comptime
IR
optimizer
ABI
codegen
object
linker
runtime
tooling
LSP
```

---

# 435.75 — Test naming

Test ID ổn định:

```text
LEX-...
PARSE-...
TYPE-...
MEM-...
CONC-...
ERR-...
GEN-...
CONST-...
ABI-...
CODEGEN-...
OBJ-...
LINK-...
LSP-...
CLI-...
```

---

# 435.76 — Conformance suite

Axiom Language Conformance Suite:

```text
AXCS
```

là bộ test chuẩn cho language semantics.

---

# 435.77 — Conformance categories

```text
syntax
types
evaluation
memory
ownership
traits
generics
comptime
errors
concurrency
ABI
```

---

# 435.78 — Target conformance

Language conformance và target conformance phải tách.

Một compiler có thể:

```text
pass language semantics
fail target backend
```

mà test report phải phản ánh rõ.

---

# 435.79 — Standard library conformance

Core/std APIs có test contract riêng.

Không trộn toàn bộ với language conformance.

---

# 435.80 — ABI conformance suite

ABI tests phải có reference layouts/calling sequences.

---

# 435.81 — Layout golden tests

Test:

```text
sizeof
alignof
offsetof
strideof
enum layout
repr(C)
packed
align
```

---

# 435.82 — Cross-language ABI validation

Có thể sử dụng independently compiled C test fixtures để kiểm tra Axiom FFI.

Đây là **test oracle**, không phải dependency của Axiom compiler.

---

# 435.83 — Reference implementation

Axiom semantics nên có một semantic reference model đơn giản cho phần quan trọng.

Không cần nhanh.

Mục đích:

```text
spec semantics
vs
optimized compiler
```

---

# 435.84 — Interpreter oracle

Có thể có:

```text
Axiom semantic interpreter
```

chạy subset/full language ở mức interpreter.

Compiler output được đối chiếu với interpreter ở test suite.

---

# 435.85 — Why interpreter matters

Ví dụ:

```text
source
→ interpreter result = 42

source
→ optimized native result = 42
```

Nếu khác, compiler bug được phát hiện.

---

# 435.86 — Interpreter is not production runtime

Interpreter chỉ phục vụ:

```text
testing
debugging
comptime reference
semantic validation
```

Không phải runtime requirement.

---

# 435.87 — Differential optimization oracle

Pipeline:

```text
source
→ interpreter
→ -O0
→ -O2
→ native
```

so sánh observable output.

---

# 435.88 — Random program generation

Compiler fuzzer có thể sinh Axiom programs với grammar-aware generator.

Không chỉ random bytes.

---

# 435.89 — Typed random programs

Generator có thể sinh chương trình đã biết type để test optimizer/codegen sâu hơn.

---

# 435.90 — Mutation testing

Test suite có thể dùng mutation:

```text
remove branch
change opcode
change type
remove bounds check
```

để đánh giá test strength.

---

# 435.91 — Machine encoder mutation

Nếu encoder bị sửa sai một byte, golden tests phải fail.

---

# 435.92 — Linker mutation

Nếu relocation offset bị thay đổi, executable tests phải fail.

---

# 435.93 — Test oracle hierarchy

Ưu tiên:

```text
formal invariant
independent model
golden data
runtime behavior
differential compiler
```

Không chỉ dựa vào snapshot.

---

# 435.94 — Performance benchmarks

Benchmark phải bao phủ:

```text
compile time
memory usage
binary size
runtime performance
startup time
allocation overhead
```

---

# 435.95 — Compiler compile-time benchmark

Các benchmark lớn:

```text
frontend
type checking
trait solver
comptime
codegen
linking
incremental rebuild
```

---

# 435.96 — Runtime benchmark

Representative workload:

```text
integer
floating point
memory
string
collections
concurrency
async
SIMD
FFI
```

---

# 435.97 — Binary-size benchmark

Theo dõi:

```text
empty executable
hello world
small CLI
medium application
library
```

---

# 435.98 — Empty runtime benchmark

Một executable:

```text
main() → 0
```

phải được đo riêng.

Điều này kiểm tra:

```text
startup overhead
runtime bloat
linker dead stripping
```

---

# 435.99 — Capability-linked runtime

Nếu chương trình không dùng:

```text
thread
network
filesystem
async
```

các runtime components đó không được link chỉ vì `std` được import.

---

# 435.100 — Binary growth invariant

Binary size nên gần với:

```text
used code
+
required metadata
+
required runtime
```

thay vì:

```text
whole standard library
```

---

# 435.101 — Benchmark reproducibility

Benchmark reports phải lưu:

```text
compiler
commit
target
CPU
OS
profile
flags
```

---

# 435.102 — Benchmark interpretation

Compiler không được tự động coi một benchmark nhỏ là bằng chứng cho performance tổng quát.

Benchmark suite phải chứa nhiều workload.

---

# 435.103 — Performance regression thresholds

CI có thể đặt threshold:

```text
compile time regression > X%
binary size regression > Y%
```

Nhưng thresholds là project policy, không phải language semantics.

---

# 435.104 — ABI regression

ABI golden tests phải chạy trong CI trước khi merge compiler changes.

---

# 435.105 — Object regression

Object files phải được structural diff, không chỉ byte diff, vì một số metadata có thể hợp lệ nhưng khác encoding.

---

# 435.106 — Reproducibility CI

Build cùng commit nhiều lần:

```text
artifact A
artifact B
```

và compare.

---

# 435.107 — Multi-platform CI

Mỗi target production tier phải có:

```text
compile
link
smoke execution
```

nếu CI platform hỗ trợ.

---

# 435.108 — Target tiers

Target được phân:

```text
Tier 1
Tier 2
Tier 3
```

nhưng đây là **support maturity**, không phải quality ranking.

---

# 435.109 — Tier 1 requirement

Tier 1 cần:

- compile;
- link;
- runtime smoke tests;
- standard library core tests;
- ABI tests;
- regression tests.

---

# 435.110 — Tier 2

Có compile/link/runtime coverage giới hạn hơn.

---

# 435.111 — Tier 3

Experimental/platform-specific.

Không được coi là stable conformance target.

---

# 435.112 — Test sharding

Large suite được chia:

```text
frontend shard
backend shard
target shard
library shard
```

---

# 435.113 — Parallel tests

Tests độc lập chạy song song.

Test order không được ảnh hưởng kết quả.

---

# 435.114 — Test isolation

Test không được phụ thuộc:

```text
previous test filesystem state
previous test global state
execution order
```

trừ tests explicitly tagged integration.

---

# 435.115 — Temporary directories

Test runner cấp temporary workspace riêng.

---

# 435.116 — Deterministic randomness

Fuzz/test randomness phải có seed.

Ví dụ:

```text
axiom test --seed 1234
```

---

# 435.117 — Reproduce fuzz failure

Fuzz failure phải ghi:

```text
seed
input
compiler version
target
flags
```

---

# 435.118 — Minimized reproducer

Mọi fuzz crash được reduced trước khi trở thành regression test nếu có thể.

---

# 435.119 — Security testing

Compiler phải được fuzz như một parser/compiler attack surface.

Đặc biệt:

```text
malformed source
malformed package
malformed object
malformed debug info
```

---

# 435.120 — Resource exhaustion tests

Test:

```text
deep recursion
huge array
huge generic expansion
huge comptime output
pathological trait constraints
```

Compiler phải fail gracefully.

---

# 435.121 — No compiler denial-of-service

Không để một source hợp lệ đơn giản gây:

```text
unbounded memory
infinite loop
unbounded recursion
```

mà không có diagnostic/resource limit.

---

# 435.122 — Parser stack safety

Parser phải có chiến lược cho nesting cực sâu.

Có thể:

```text
explicit parser stack
depth limit
```

thay vì native call stack không giới hạn.

---

# 435.123 — Trait solver resource safety

Trait solving phải có:

```text
depth limit
candidate limit
time/step budget
```

---

# 435.124 — Generic instantiation resource safety

Compiler phải detect pathological code explosion.

---

# 435.125 — Code-size limits

Generated code có thể có configurable limit.

Nếu vượt:

```text
E435xxx generated code exceeds configured limit
```

---

# 435.126 — Compile-time memory limit

Comptime engine có memory budget.

---

# 435.127 — Test compiler determinism

Chạy cùng compilation nhiều lần với:

```text
different thread count
```

vẫn phải cho cùng semantic/artifact result trong reproducible mode.

---

# 435.128 — Race detection in compiler

Compiler itself phải được test under:

```text
parallel compilation
parallel package resolution
parallel LSP queries
```

---

# 435.129 — Compiler thread safety

Shared global mutable compiler state phải được tránh hoặc bảo vệ.

---

# 435.130 — Incremental correctness

Test:

```text
full build
```

so với:

```text
incremental build
```

phải cho equivalent artifacts/behavior.

---

# 435.131 — Incremental invalidation test

Sửa:

```text
private implementation
```

không được invalidate unrelated semantic units unnecessarily.

Sửa:

```text
public API
```

phải invalidate dependent units.

---

# 435.132 — Cache correctness

Cache hit phải cho kết quả tương đương cache miss.

Đây là invariant bắt buộc.

---

# 435.133 — Cache poisoning defense

Cache key phải chứa mọi semantic input quan trọng.

Không dùng:

```text
source hash alone
```

---

# 435.134 — Package resolution reproducibility

Cùng lockfile:

```text
same dependency graph
```

bất kể registry response ordering.

---

# 435.135 — Build graph correctness

Build graph phải không bỏ sót dependency implicit được compiler semantic engine xác định.

---

# 435.136 — Generated source dependency

Comptime/build-generated artifacts phải xuất hiện trong graph.

---

# 435.137 — Documentation test correctness

Documentation examples phải được compile trong CI khi marked executable.

---

# 435.138 — LSP correctness

LSP result phải nhất quán với compiler semantic result.

Ví dụ:

```text
hover type
```

phải cùng TypeId/type representation với compiler.

---

# 435.139 — LSP stale-state tests

Sau:

```text
didChange
```

LSP không được trả semantic result từ snapshot cũ.

---

# 435.140 — LSP cancellation tests

Canceled request không được mutate semantic state.

---

# 435.141 — CLI compatibility tests

Canonical CLI behavior phải có regression suite.

---

# 435.142 — Diagnostic compatibility tests

Stable diagnostic codes phải được kiểm tra qua compiler versions/editions.

---

# 435.143 — Error-code registry

Compiler có một registry:

```text
code
category
severity
meaning
introduced edition
deprecated status
```

---

# 435.144 — Specification traceability

Mỗi locked specification requirement nên map tới test IDs.

Ví dụ:

```text
BOOTSTRAP-423.XX
    ↓
MEM-001
MEM-002
MEM-003
```

---

# 435.145 — Requirement coverage

Không được coi:

```text
100% line coverage
```

là:

```text
100% semantic coverage
```

---

# 435.146 — Semantic coverage

Coverage phải theo:

```text
language construct
type combination
control flow
ABI category
target
error path
```

---

# 435.147 — Compiler source coverage

Code coverage vẫn hữu ích nhưng chỉ là metric bổ sung.

---

# 435.148 — Mutation score

Mutation testing có thể dùng để đánh giá chất lượng test suite.

---

# 435.149 — Specification tests

Mỗi specification invariant quan trọng phải có ít nhất:

```text
positive test
negative test
edge-case test
```

nếu áp dụng.

---

# 435.150 — Conformance release gate

Không release stable compiler nếu:

```text
core conformance failures
ABI failures
object writer failures
linker failures
critical regression
```

vẫn còn.

---

# 435.151 — Compiler correctness hierarchy

Axiom không tuyên bố:

> “Compiler đã được formal verified hoàn toàn.”

Thay vào đó sử dụng nhiều lớp assurance:

```text
specification
+
reference semantics
+
unit tests
+
golden tests
+
property tests
+
fuzzing
+
differential testing
+
integration tests
+
cross-target tests
```

---

# 435.152 — Formal verification hooks

Một số subsystem có thể được formal verify sau:

```text
lexer
parser
constant evaluator
machine encoder
relocation arithmetic
```

Kiến trúc phải không cản trở việc này.

---

# 435.153 — Machine encoder verification

Đây là candidate rất tốt cho formal/property verification vì:

```text
instruction semantics
→ encoding bytes
```

có input/output rõ ràng.

---

# 435.154 — Relocation verification

Tương tự:

```text
symbol address
+
addend
+
relocation type
→ patched value
```

có thể verify bằng property tests/formal methods.

---

# 435.155 — Constant evaluator verification

Interpreter semantic model có thể trở thành oracle cho optimizer constant folding.

---

# 435.156 — Reference semantics

Language specification nên có semantic rules đủ chính xác để viết interpreter/reference evaluator.

---

# 435.157 — Undefined behavior tests

UB examples không được dùng làm correctness oracle.

Compiler test harness phải đánh dấu:

```text
@ub
```

hoặc metadata tương đương nếu cần.

---

# 435.158 — Platform-dependent tests

Test phải khai báo:

```text
requires(target.os == ...)
requires(arch == ...)
requires(feature == ...)
```

---

# 435.159 — Test capability model

Test runner biết:

```text
requires_network
requires_threads
requires_filesystem
requires_gpu
```

và skip hợp lệ khi capability unavailable.

---

# 435.160 — Skip semantics

Phân biệt:

```text
pass
fail
skip
unsupported
not-run
```

Không coi tất cả skip là pass.

---

# 435.161 — Test timeout

Mỗi integration test có timeout mặc định.

---

# 435.162 — Crash classification

Native test có thể:

```text
exit normally
non-zero
signal/crash
timeout
```

Test runner phải phân biệt.

---

# 435.163 — Signal handling

Runtime test harness không được che giấu crash information.

---

# 435.164 — Core library test bootstrap

Core library phải có thể test mà không cần full standard library.

---

# 435.165 — Runtime bootstrap tests

Allocator/panic/startup có test freestanding riêng.

---

# 435.166 — Linker bootstrap tests

Linker phải test được bằng synthetic object files, không cần compile full Axiom source.

---

# 435.167 — Object writer bootstrap tests

Object writer cũng test bằng synthetic sections/symbols/relocations.

---

# 435.168 — Compiler layering test

Không được để:

```text
frontend
```

phụ thuộc:

```text
native linker
```

vì điều đó phá vỡ `axiom check`.

---

# 435.169 — Backend isolation

Backend tests có thể chạy mà không cần standard library.

---

# 435.170 — Frontend isolation

Frontend tests không cần target-specific machine encoder.

---

# 435.171 — Target-independent semantics

Type/ownership/comptime semantics phải target-independent trừ những phần explicitly target-aware.

---

# 435.172 — Target-specific semantics

Chỉ các phần như:

```text
sizeof pointer
ABI
alignment
SIMD availability
atomic availability
```

được target-dependent.

---

# 435.173 — Test matrix generation

Compiler test harness tự sinh matrix:

```text
feature × type × target × optimization
```

cho các test phù hợp.

---

# 435.174 — Golden update policy

Golden output không được auto-update mặc định.

Phải có explicit:

```text
--bless
```

hoặc equivalent.

---

# 435.175 — Bless safety

Bless chỉ được dùng khi developer chủ động xác nhận semantic change.

---

# 435.176 — Diagnostic snapshot stability

Diagnostic snapshots nên ưu tiên:

```text
code
spans
structured fields
```

hơn full terminal formatting.

---

# 435.177 — Test artifact retention

CI giữ:

```text
failed source
diagnostic JSON
IR
object
binary
logs
```

khi failure cần debug.

---

# 435.178 — Minimal bug reproducer

Compiler project phải có tool:

```text
axiom reduce testcase.ax
```

để giảm reproducer.

---

# 435.179 — Reduction correctness

Reducer chỉ được loại bỏ phần source khi failure property vẫn giữ nguyên.

---

# 435.180 — Fuzz regression lifecycle

```text
fuzz discovery
→ minimize
→ classify
→ fix
→ regression test
→ permanent corpus
```

---

# 435.181 — Benchmark regression lifecycle

```text
baseline
→ change
→ measure
→ detect regression
→ inspect
→ accept/reject
```

Không tự động sửa optimization chỉ dựa vào benchmark.

---

# 435.182 — Compiler correctness report

CI có thể sinh:

```text
conformance
regression
fuzz
ABI
backend
performance
reproducibility
```

dashboard machine-readable.

---

# 435.183 — Release certification

Một compiler release candidate cần pass:

```text
frontend suite
semantic suite
comptime suite
ownership suite
IR verifier suite
codegen suite
object suite
linker suite
ABI suite
runtime suite
stdlib suite
LSP suite
CLI suite
fuzz smoke suite
reproducibility suite
```

---

# 435.184 — Bootstrap certification

Self-hosting compiler cần thêm:

```text
stage convergence
self-build
self-test
self-hosted rebuild
```

---

# 435.185 — Trust boundaries

Axiom phân biệt:

```text
Specification
Reference model
Compiler implementation
Test oracle
Platform
```

Không được để compiler tự xác nhận chính nó bằng cùng một implementation path.

---

# 435.186 — Independent oracle principle

Các test quan trọng nên có ít nhất một oracle khác implementation đang test.

Ví dụ:

```text
Axiom machine encoder
vs
known instruction byte vectors
```

---

# 435.187 — Compiler test determinism

Test runner phải deterministic mặc định.

Randomized testing chỉ random khi explicit seed.

---

# 435.188 — CI reproducibility

CI test command phải ghi:

```text
compiler version
git revision
host
target
profile
test seed
environment contract
```

---

# 435.189 — Test result machine contract

```text
axiom test --format=json
```

phải cung cấp:

```text
schema_version
suite
tests[]
summary
environment
```

---

# 435.190 — Benchmark result machine contract

```text
axiom bench --format=json
```

có:

```text
benchmark
samples
statistics
environment
compiler
target
```

---

# 435.191 — Fuzz result machine contract

Fuzz failure phải có:

```text
seed
input hash
reproducer path
failure type
stack/diagnostic
compiler revision
```

---

# 435.192 — Conformance manifest

AXCS có manifest:

```text
language edition
required tests
optional tests
target requirements
expected behavior
```

---

# 435.193 — Versioned conformance

Conformance suite version gắn với language edition/spec revision.

---

# 435.194 — Compiler acceptance levels

Có thể định nghĩa:

```text
bootstrap
experimental
preview
stable
```

theo mức test/conformance đạt được.

Đây là **release maturity**, không phải đánh giá chất lượng của từng backend hay ngôn ngữ.

---

# 435.195 — Hard correctness invariants

1. Compiler không được crash trên arbitrary source.
2. Parser phải memory-safe.
3. Fuzz input không được phá compiler process.
4. Comptime có resource limits.
5. Trait solver có termination/resource limits.
6. Generic instantiation có resource limits.
7. IR luôn được verify giữa các critical passes.
8. Optimization phải preserve defined semantics.
9. `-O0` và optimized builds phải tương đương về observable behavior.
10. Incremental và clean builds phải tương đương.
11. Cache hit và cache miss phải tương đương.
12. Formatter phải semantic-preserving.
13. LSP phải dùng semantic truth của compiler.
14. Machine-code encoder phải có exact byte tests.
15. Relocations phải có independent tests.
16. Object writers phải có structural validation.
17. ABI phải có golden tests.
18. FFI phải có interoperability tests.
19. Self-hosted compiler phải có bootstrap tests.
20. Regression bugs phải trở thành permanent tests.
21. Fuzz failures phải được reproducible bằng seed/input.
22. Reproducible builds phải được kiểm tra.
23. Test result phải machine-readable.
24. Diagnostic code phải stable.
25. Target-specific behavior phải được test riêng.
26. Undefined behavior không được dùng làm correctness oracle.
27. Compiler subsystem tests phải tôn trọng architecture boundaries.
28. Production compiler không phụ thuộc third-party compiler để codegen/link.
29. Reference semantics phải độc lập đủ để phát hiện compiler bugs.
30. Không coi code coverage đơn thuần là compiler correctness.

---

# BOOTSTRAP-435.196 — Verification architecture

```text
                       AXIOM SPEC
                           │
                           ▼
                  Reference Semantics
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       Compiler Implementation       Test Generator
              │                         │
      ┌───────┼────────┐                │
      ▼       ▼        ▼                ▼
    Frontend  IR     Backend          Fuzzer
      │       │        │                │
      └───────┼────────┴────────────────┘
              ▼
       Independent Oracles
              │
      ┌───────┼──────────┐
      ▼       ▼          ▼
   Golden   Differential  Runtime
   Tests      Tests       Tests
              │
              ▼
             CI
              │
              ▼
       Release Certification
```

---

# BOOTSTRAP-435.197 — Ý nghĩa đối với Axiom

Từ thời điểm này, Axiom không còn chỉ là một danh sách feature.

Ta đã có ba lớp quan trọng:

```text
SPECIFICATION
     ↓
IMPLEMENTATION ARCHITECTURE
     ↓
VERIFICATION ARCHITECTURE
```

Điều này đặc biệt quan trọng với các thành phần mà Axiom tự làm thay vì dựa vào LLVM:

```text
IR
optimizer
machine encoder
ELF writer
PE/COFF writer
Mach-O writer
linker
ABI
```

Các thành phần này sẽ được kiểm chứng độc lập thay vì chỉ kiểm tra “chương trình chạy được”.

---

# BOOTSTRAP-435.198 — Trạng thái chuỗi Axiom

Chuỗi hiện tại đã đi tới:

```text
420  Machine Code / Object / Native Artifact
421  ABI / Calling Convention
422  Memory Layout / Data Representation
423  Memory Management / Ownership
424  Concurrency / Thread / Async
425  Error / Panic / Result
426  Generics / Traits / Interfaces
427  [đã hoàn tất]
428  [đã hoàn tất]
429  Lexical Model / Syntax
430  Type System
431  Comptime / Metaprogramming
432  Modules / Packages / Build
433  Standard Library / Runtime Boundary
434  Toolchain / CLI / LSP / DX
435  Testing / Conformance / Compiler Correctness
```

**BOOTSTRAP-434 và BOOTSTRAP-435 hoàn tất.**

Theo nguyên tắc đã khóa của project, không dừng ở đây để hỏi “có tiếp tục không”. Bước kế tiếp sẽ chuyển sang nhóm specification tiếp theo, nơi các thành phần đã khóa được ghép thành **compiler architecture/pipeline thực thi hoàn chỉnh**, rồi mới tiến dần sang các subsystem nâng cao.