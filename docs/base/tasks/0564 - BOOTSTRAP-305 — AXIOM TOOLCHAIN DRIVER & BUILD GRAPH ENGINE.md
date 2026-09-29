# BOOTSTRAP-305 — AXIOM TOOLCHAIN DRIVER & BUILD GRAPH ENGINE

## 305.1. Mục tiêu

Sau `301 → 302 → 303 → 304`, Axiom đã có chuỗi backend:

```text
Source
  ↓
Frontend
  ↓
HIR
  ↓
MIR
  ↓
Machine IR
  ↓
Machine Code
  ↓
Object
  ↓
LinkedImage
  ↓
Native Image
```

Nhưng một compiler thực tế vẫn cần một thành phần điều phối:

> **Toolchain Driver** — biến một project Axiom thành toàn bộ artifact cuối cùng, tự quyết định những module nào cần compile, những thư viện nào cần link, target nào được sử dụng, và những bước nào có thể reuse từ cache.

305 xây dựng thành phần đó.

---

# 305.2. Kiến trúc tổng thể

```text
                     axiom
                       │
                       ↓
              ┌─────────────────┐
              │ Toolchain Driver│
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
      SourceDB     PackageDB    TargetDB
          │            │            │
          └────────────┼────────────┘
                       ↓
                   Build Graph
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Compile       Comptime      Link
          │            │            │
          ↓            ↓            ↓
        .axobj       generated     Image
                       │
                       ↓
                  Final Artifact
```

Driver không chứa semantic compiler logic.

Nó điều phối các subsystem đã có.

---

# 305.3. Một lệnh compiler phải đủ

Mục tiêu:

```text
axiom build
```

có thể thực hiện:

```text
project
 ↓
module discovery
 ↓
dependency resolution
 ↓
incremental compilation
 ↓
comptime
 ↓
code generation
 ↓
object emission
 ↓
library resolution
 ↓
link
 ↓
executable
```

Người dùng không cần tự gọi:

```text
frontend
backend
assembler
linker
```

và cũng không cần external assembler/linker.

---

# 305.4. Các command chính

Driver v0.1 nên có:

```text
axiom build
axiom check
axiom run
axiom test
axiom bench
axiom clean
axiom fmt
axiom doc
axiom inspect
```

Compiler-level:

```text
axiom compile
axiom emit-obj
axiom emit-ir
axiom emit-machine
axiom link
```

Các command debug compiler:

```text
axiom explain
axiom query
axiom dump
```

Không cần biến CLI thành một hệ thống khổng lồ ngay từ đầu.

---

# 305.5. Build Graph

Đây là thành phần trung tâm.

```text
BuildGraph {
    nodes[]
    edges[]
    artifacts[]
    actions[]
}
```

Node:

```text
Source
Module
Comptime
Object
StaticLibrary
SharedLibrary
Executable
Test
GeneratedFile
```

Edge:

```text
Imports
Uses
Generates
CompilesTo
Links
Runs
```

Ví dụ:

```text
main.ax
   │
   ├── imports math
   │              │
   │              ↓
   │          math.ax
   │
   ↓
main.axobj
   │
   ├──────────────┐
   ↓              ↓
math.axobj      libc
   │              │
   └──────┬───────┘
          ↓
       program
```

---

# 305.6. Không build theo file đơn giản

Không dùng logic:

```text
file changed
→ rebuild everything
```

Axiom phải dựa trên semantic dependency graph.

Ví dụ:

```text
foo.ax
```

thay đổi implementation private nhưng public interface không đổi.

Module phụ thuộc:

```text
bar.ax
```

có thể không cần recompile.

Ngược lại:

```text
public struct Foo
```

thay đổi layout hoặc public trait contract có thể invalidate nhiều module.

---

# 305.7. Semantic Fingerprint

Build system sử dụng fingerprint đã được thiết kế từ trước:

```text
SemanticFingerprint
```

Bao gồm:

```text
source semantic identity
public API
types
traits
generic contracts
ABI
repr
comptime dependencies
target
features
compiler semantic version
```

Phân biệt:

```text
SourceHash
```

với:

```text
SemanticHash
```

và:

```text
ArtifactHash
```

---

# 305.8. Ba loại thay đổi

### Implementation-only

```text
fn foo() {
    x + 1
}
```

đổi thành:

```text
fn foo() {
    x + 2
}
```

→ module sử dụng `foo` có thể cần relink nhưng không nhất thiết re-type-check.

### Interface change

```text
fn foo(x: i32)
```

đổi thành:

```text
fn foo(x: i64)
```

→ downstream semantic compilation bị invalid.

### ABI change

```text
@repr(C)
struct Foo
```

thay đổi layout:

→ mọi consumer ABI-dependent phải invalid.

Build graph phải phân biệt ba trường hợp.

---

# 305.9. Compilation Unit

Định nghĩa:

```text
CompilationUnit {
    module
    target
    profile
    features
    semantic_fingerprint
    codegen_fingerprint
}
```

Artifact:

```text
CompiledUnit {
    object
    public_metadata
    debug_metadata
    dependency_metadata
}
```

Metadata này rất quan trọng cho incremental compilation.

---

# 305.10. Artifact Metadata

Mỗi `.axobj` nên có metadata companion hoặc embedded metadata:

```text
AxiomObjectMetadata {
    compiler_version
    language_version
    target
    abi
    semantic_fingerprint
    public_api_fingerprint
    codegen_fingerprint

    dependencies[]
    exported_symbols[]
    required_runtime_components[]
}
```

Mục tiêu là compiler không phải parse lại toàn bộ source dependency để biết artifact có còn hợp lệ.

---

# 305.11. Cache

Cache key:

```text
CacheKey =
    source semantic fingerprint
    +
    dependency fingerprints
    +
    compiler semantic version
    +
    target
    +
    optimization profile
    +
    features
    +
    ABI
    +
    comptime inputs
```

Không được dùng:

```text
source filename
```

làm cache identity.

---

# 305.12. Cache levels

Có thể có nhiều tầng:

```text
L1:
in-memory query cache

L2:
local incremental cache

L3:
shared/distributed cache
```

Core v0.1 chỉ cần L1 + L2.

Distributed cache là extension.

---

# 305.13. Comptime dependency tracking

Ví dụ:

```text
comptime {
    read_source("config.ax")
}
```

thì:

```text
config.ax
```

phải trở thành build dependency.

Nếu:

```text
comptime read filesystem
```

thay đổi:

```text
file content
```

artifact phải invalidate.

Không được cache comptime result chỉ dựa trên source file chính.

---

# 305.14. Environment dependency

Comptime có thể phụ thuộc:

```text
Environment
Time
Random
Filesystem
Network
External tool
```

Những capability này phải được ghi vào build graph.

Ví dụ:

```text
comptime read env("TARGET_MODE")
```

thì:

```text
TARGET_MODE
```

là build input.

---

# 305.15. Reproducible build

Build graph phải có mode:

```text
--deterministic
```

Khi bật:

- thời gian không được tự chèn;
- random seed phải cố định;
- path canonicalization;
- artifact ordering deterministic;
- metadata deterministic;
- build ID deterministic.

---

# 305.16. Target specification

Tạo:

```text
TargetSpec {
    architecture
    operating_system
    abi
    object_format
    executable_format
    endianness
    pointer_width
    cpu_features
    os_features
}
```

Ví dụ:

```text
x86_64-linux-gnu
x86_64-windows-msvc
aarch64-linux-gnu
aarch64-macos
aarch64-ios
wasm32-wasi
```

Target triple chỉ là identifier.

Compiler phải resolve nó thành `TargetSpec` đầy đủ.

---

# 305.17. Cross compilation

Driver phải hỗ trợ:

```text
axiom build --target=aarch64-linux
```

trên:

```text
x86_64-windows
```

Không được giả định:

```text
host == target
```

Phân biệt:

```text
HostTarget
BuildTarget
TargetTarget
```

---

# 305.18. Build vs Host vs Target

Ba khái niệm:

```text
Build:
máy đang build compiler

Host:
máy chạy compiler

Target:
máy chạy artifact
```

Trong self-hosting:

```text
Build = Host
```

thường đúng, nhưng không được hard-code.

---

# 305.19. Profiles

V0.1:

```text
dev
release
test
bench
```

Mỗi profile chứa:

```text
optimization
debug
assertions
overflow_policy
panic_policy
LTO
incremental
strip
```

Ví dụ:

```text
release:
    opt = aggressive
    debug = false
    lto = true
```

---

# 305.20. Optimization profile không phải semantic profile

Điểm cực kỳ quan trọng:

```text
-O0
-O2
-O3
```

không được thay đổi safe-language semantics.

Nếu:

```text
-O0
```

pass nhưng:

```text
-O3
```

fail verifier:

→ compiler bug.

Build graph fingerprint phải phân biệt codegen profile, nhưng semantic verifier vẫn giữ cùng language semantics.

---

# 305.21. Parallel build

Build graph phải hỗ trợ:

```text
A ──→ C
B ──→ C
D ──→ E
```

thì:

```text
A
B
D
```

có thể compile song song.

Nhưng:

```text
C
```

chỉ chạy sau A/B.

Scheduler:

```text
ready queue
dependency count
worker pool
```

---

# 305.22. Deterministic parallelism

Parallel build không được làm artifact phụ thuộc vào scheduling order.

Không:

```text
worker 3 finishes first
→ symbol index khác
```

Mọi output ordering phải canonicalize sau parallel computation.

---

# 305.23. Query-based compiler integration

Driver phải sử dụng `CompilerDB` query system đã thiết kế.

Ví dụ:

```text
parse(module)
resolve(module)
typecheck(module)
lower_mir(module)
verify(module)
optimize(module)
codegen(module)
emit_object(module)
```

Không tạo một pipeline riêng song song với compiler database.

---

# 305.24. Incremental invalidation

Dependency graph phải hỗ trợ:

```text
Artifact A
    ↓
Semantic Fact B
    ↓
Object C
```

Nếu A thay đổi:

```text
invalidate only dependent facts
```

Không:

```text
clear entire cache
```

---

# 305.25. Generic instantiation cache

Ví dụ:

```text
Vec<i32>
Vec<f64>
Vec<u8>
```

Codegen instance có thể được cache riêng:

```text
GenericInstanceFingerprint
```

Nếu generic source không đổi:

```text
Vec<i32>
```

không cần instantiate lại.

---

# 305.26. Comptime cache

Tương tự:

```text
ComptimeFingerprint
```

bao gồm:

```text
comptime source
input values
external dependencies
compiler semantic version
target
```

Kết quả có thể cache.

---

# 305.27. Build artifacts

Chuẩn hóa artifact tree:

```text
build/
├── cache/
├── objects/
├── generated/
├── debug/
├── deps/
└── bin/
```

Không bắt buộc layout này là public contract.

Compiler có thể thay đổi internal structure mà không ảnh hưởng source semantics.

---

# 305.28. Atomic artifact publishing

Compile:

```text
foo.ax
```

không được ghi trực tiếp:

```text
foo.axobj
```

trong lúc đang compile.

Phải:

```text
foo.axobj.tmp
    ↓
verify
    ↓
atomic rename
```

Tránh cache corruption khi:

- compiler crash
- mất điện
- process bị kill.

---

# 305.29. Failure recovery

Build graph phải biết:

```text
Running
Completed
Failed
Cancelled
Invalid
```

Nếu compilation bị dừng giữa chừng:

```text
Running artifact
```

không được coi là valid cache.

---

# 305.30. Cancellation

Driver phải hỗ trợ:

```text
Ctrl+C
```

và cancellation propagation:

```text
Build
 ↓
Compile
 ↓
Comptime
 ↓
Codegen
 ↓
Link
```

Các task đang chạy phải được cancel an toàn.

Không để:

```text
half-written artifact
```

được publish.

---

# 305.31. Diagnostics aggregation

Nếu 10 module lỗi:

```text
A
B
C
...
```

driver không nên dừng ngay sau lỗi đầu tiên nếu có thể tiếp tục phân tích độc lập.

Ví dụ:

```text
compile A ─ error
compile B ─ error
compile C ─ success
```

Sau đó báo cáo tất cả lỗi semantic có thể thu thập.

Nhưng nếu dependency graph khiến B không thể phân tích vì A chưa có public interface hợp lệ, phải báo dependency failure rõ ràng.

---

# 305.32. Explain build

Một tính năng rất phù hợp với Axiom:

```text
axiom explain build
```

Có thể trả lời:

```text
why was foo.ax rebuilt?
```

Ví dụ:

```text
foo.ax rebuilt because:

  dependency bar.ax changed
  ↓
  public API fingerprint changed
  ↓
  foo semantic cache invalidated
  ↓
  object cache invalidated
```

Hoặc:

```text
why was this file not rebuilt?
```

```text
foo.ax:
  source unchanged
  public dependencies unchanged
  target unchanged
  compiler semantics unchanged

→ cache hit
```

Đây là một lợi thế rất lớn cho AI-assisted development.

---

# 305.33. Build graph introspection

CLI:

```text
axiom inspect build-graph
axiom inspect dependencies
axiom inspect cache
axiom inspect artifact
```

Output machine-readable:

```text
--format=json
```

để AI agent có thể đọc trực tiếp.

---

# 305.34. AI-friendly compiler state

Không để AI phải parse log text dài.

Compiler nên cung cấp structured diagnostics:

```text
Diagnostic {
    code
    severity
    message
    primary_span
    secondary_spans[]
    notes[]
    fixes[]
    related_symbols[]
    dependency_chain[]
}
```

Build failure:

```text
BuildFailure {
    failed_node
    diagnostic_ids[]
    root_cause
    blocked_nodes[]
}
```

---

# 305.35. Machine-readable build protocol

Có thể có:

```text
axiom --json build
```

trả:

```text
{
    "status": "success",
    "artifacts": [...],
    "cache_hits": [...],
    "cache_misses": [...],
    "diagnostics": [...]
}
```

Không nên yêu cầu AI agent scrape terminal output.

---

# 305.36. Package dependency

305 chỉ cần xây foundation:

```text
PackageGraph
```

chưa cần thiết kế package registry hoàn chỉnh.

Package:

```text
Package {
    name
    version
    source
    dependencies[]
    targets[]
}
```

Dependency graph:

```text
app
 ├── math
 │    └── core
 └── ui
      └── core
```

Phải phát hiện:

```text
cycle
duplicate version conflict
target incompatibility
ABI incompatibility
```

---

# 305.37. Version identity

Không được chỉ dùng:

```text
package name
```

làm identity.

Dùng:

```text
PackageId
Version
SourceIdentity
```

Ví dụ cùng:

```text
foo@1.2.0
```

nhưng từ hai source khác nhau không nhất thiết là cùng package.

---

# 305.38. Module vs Package

Phải giữ:

```text
Package
  contains
Modules
```

Không đồng nhất:

```text
package == module
```

Ví dụ:

```text
package graphics
├── math
├── image
├── texture
└── renderer
```

---

# 305.39. Build script

Không đưa scripting tùy ý vào Core build system ngay lập tức.

Thay vào đó:

```text
BuildAction
```

là abstraction có capability.

Các action:

```text
Compile
Generate
Copy
Link
RunComptime
RunTool
Package
```

`RunTool` phải explicit.

---

# 305.40. Không phụ thuộc shell

Không nên xây:

```text
system("gcc ...")
```

làm cơ chế build.

Driver phải gọi native compiler subsystems trực tiếp.

External tool chỉ là:

```text
optional FFI/tool action
```

cho trường hợp thật sự cần.

---

# 305.41. Bootstrap mode

Trong giai đoạn compiler chưa self-host:

```text
Bootstrap Compiler
```

có thể chạy trên:

```text
C++ / Rust / another implementation
```

nhưng artifact model và build graph phải giống compiler Axiom cuối cùng.

Khi self-host:

```text
axiom compiler
```

chính nó thực hiện:

```text
parse
typecheck
MIR
codegen
object
link
image
```

không cần thay đổi build architecture.

---

# 305.42. Self-hosting transition

Mục tiêu cuối:

```text
Stage 0
External bootstrap compiler
        ↓
Stage 1
Axiom compiler compiled by bootstrap compiler
        ↓
Stage 2
Axiom compiler compiles itself
        ↓
Stage 3
Bootstrap compiler no longer required
```

Build graph phải hỗ trợ bootstrap stages:

```text
BootstrapToolchain
AxiomToolchain
SelfHostedToolchain
```

---

# 305.43. Toolchain manifest

Có:

```text
ToolchainManifest {
    compiler_version
    language_version
    supported_targets[]
    runtime_components[]
    object_formats[]
    executable_formats[]
}
```

Driver dùng nó để kiểm tra:

```text
target supported?
backend available?
runtime component available?
```

thay vì fail sâu trong pipeline.

---

# 305.44. Implementation tree

```text
compiler/driver/
│
├── driver.ax
├── commands.ax
├── build_graph.ax
├── build_scheduler.ax
├── build_state.ax
├── fingerprints.ax
├── cache.ax
├── artifact.ax
├── target.ax
├── profile.ax
├── diagnostics.ax
├── cancellation.ax
├── package.ax
├── toolchain.ax
│
├── actions/
│   ├── compile.ax
│   ├── comptime.ax
│   ├── codegen.ax
│   ├── link.ax
│   └── package.ax
│
├── query/
│   ├── explain.ax
│   ├── inspect.ax
│   └── why_rebuilt.ax
│
└── tests/
    ├── incremental/
    ├── cache/
    ├── dependency/
    ├── parallel/
    ├── deterministic/
    ├── cross_compile/
    └── bootstrap/
```

---

# 305.45. Public API

Core API:

```text
fn build(
    project: Project,
    target: Target,
    profile: Profile
) -> Result<BuildResult, BuildError>
```

Graph API:

```text
fn create_build_graph(
    project: Project
) -> Result<BuildGraph, BuildError>
```

Incremental:

```text
fn invalidate(
    graph: BuildGraph,
    changed_inputs: []InputId
) -> InvalidationSet
```

Build explanation:

```text
fn explain_rebuild(
    artifact: ArtifactId
) -> RebuildExplanation
```

---

# 305.46. Invariants

```text
ADRIVER-20  Driver điều phối compiler, không tái triển khai compiler semantics.

ADRIVER-21  Build graph là source of truth cho dependency build.

ADRIVER-22  Build dependency phải dựa trên semantic dependency khi có thể.

ADRIVER-23  Host và target phải độc lập.

ADRIVER-24  Cross compilation là first-class.

ADRIVER-25  Optimization profile không được thay đổi language semantics.

ADRIVER-26  Cache key phải chứa compiler semantic identity.

ADRIVER-27  Cache key phải chứa target identity.

ADRIVER-28  Cache key phải chứa comptime dependencies.

ADRIVER-29  Public API fingerprint phải được theo dõi riêng.

ADRIVER-30  ABI changes phải invalidate ABI-dependent artifacts.

ADRIVER-31  Implementation-only changes không được invalidate quá mức khi không cần.

ADRIVER-32  Parallel build không được tạo nondeterministic artifacts.

ADRIVER-33  Cache artifact chưa verify không được publish.

ADRIVER-34  Build cancellation không được publish partial artifact.

ADRIVER-35  Build failure không được biến thành valid cache entry.

ADRIVER-36  Comptime external inputs phải là build dependencies.

ADRIVER-37  Package và module là hai abstraction khác nhau.

ADRIVER-38  Package identity không chỉ dựa trên tên.

ADRIVER-39  Dependency cycles phải được phát hiện.

ADRIVER-40  Runtime components chỉ được đưa vào khi dependency yêu cầu.

ADRIVER-41  External tools không phải compiler dependency.

ADRIVER-42  External linker không phải final Axiom dependency.

ADRIVER-43  Build graph phải hỗ trợ self-hosting transition.

ADRIVER-44  Build state phải machine-readable.

ADRIVER-45  Diagnostics phải giữ provenance tới build node.

ADRIVER-46  Cache invalidation phải deterministic.

ADRIVER-47  Artifact publication phải atomic.

ADRIVER-48  Host filesystem path không được trở thành semantic artifact identity.

ADRIVER-49  Build graph phải hỗ trợ explain/why-rebuilt.

ADRIVER-50  Compiler phải có thể tự build chính nó bằng cùng build architecture.

ADRIVER-51  Build system không được yêu cầu shell/GCC/Clang/LLD để thực hiện native Axiom build cuối cùng.

ADRIVER-52  Final self-hosted toolchain phải có thể build runtime-free application.

ADRIVER-53  Final self-hosted toolchain phải có thể build application sử dụng optional runtime components.

ADRIVER-54  Driver phải có thể điều phối toàn bộ pipeline Source → Native Image.

ADRIVER-55  Driver architecture phải cho phép IDE/AI agent sử dụng compiler như một structured service.
```

---

# 305.47. Definition of Done

Một project Axiom đơn giản:

```text
hello/
├── axiom.toml
└── src/
    └── main.ax
```

chỉ cần:

```text
axiom build
```

để tạo:

```text
build/bin/hello.exe
```

hoặc target tương ứng.

Lần build thứ hai không thay đổi source:

```text
semantic cache hit
codegen cache hit
link cache hit
```

Nếu thay đổi một implementation private:

```text
chỉ rebuild các artifact thực sự bị ảnh hưởng
```

Nếu thay đổi public ABI:

```text
compiler tự xác định downstream artifacts cần rebuild
```

Nếu cross-compile:

```text
axiom build --target=aarch64-linux
```

thì compiler không được gọi external GCC/Clang/LLD.

Và quan trọng nhất, 305 phải tạo được nền tảng cho trạng thái cuối:

```text
┌─────────────────────────────────────────────┐
│                AXIOM TOOLCHAIN              │
│                                             │
│ Source → Compiler → Object → Link → Image  │
│                  ↑                          │
│             Build Graph                    │
│                  ↑                          │
│        Cache / Comptime / Package           │
└─────────────────────────────────────────────┘
```

Từ đây, Axiom không chỉ có **compiler backend**, mà đã bắt đầu có **một toolchain hoàn chỉnh có khả năng tự điều phối quá trình xây dựng**.