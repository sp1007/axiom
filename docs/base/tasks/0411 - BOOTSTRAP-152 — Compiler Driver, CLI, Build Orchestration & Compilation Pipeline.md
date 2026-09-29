# BOOTSTRAP-152 — Compiler Driver, CLI, Build Orchestration & Compilation Pipeline
**STATUS: FROZEN / COMPLETED**

> **`axc` không chỉ là compiler frontend/backend; nó là bộ điều phối toàn bộ quá trình từ source → dependency graph → cache → compilation → linking → artifact.**

Mục tiêu của 152 là biến toàn bộ kiến trúc Axiom đã thiết kế thành **một compiler driver có pipeline thực tế**, đồng thời không biến driver thành một “god object”.

---

# 1. Kiến trúc tổng thể

```text id="7q5m4p"
                    axc
                     │
             ┌───────┴────────┐
             │ Compiler Driver │
             └───────┬────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   Workspace      Target       Profile
        │            │            │
        └────────────┼────────────┘
                     ↓
               Build Planner
                     ↓
              Package Graph
                     ↓
              Module Graph
                     ↓
             Incremental DB
                     ↓
          Compilation Scheduler
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
      Cache       CompilerDB    Parallel Jobs
        │            │            │
        └────────────┼────────────┘
                     ↓
               Object Files
                     ↓
                    LTO
                     ↓
                   Linker
                     ↓
             Binary Validator
                     ↓
                 Artifact
```

Driver chỉ **điều phối**.

Semantic compiler vẫn nằm trong `CompilerDB`.

---

# 2. CLI Core

Axiom giữ CLI nhỏ và ổn định:

```text id="r5p8fw"
axc build
axc check
axc run
axc test
axc bench
axc emit
axc link
axc inspect
axc profile
axc tune
```

Không nên có hàng trăm command top-level.

---

# 3. `axc build`

Lệnh chính:

```text id="m1m7jz"
axc build
```

Pipeline:

```text id="k8u4da"
Discover Workspace
      ↓
Load Manifest
      ↓
Resolve Dependencies
      ↓
Resolve Target/Profile
      ↓
Load Lockfile
      ↓
Build Graph
      ↓
Query Incremental Cache
      ↓
Compile Changed Units
      ↓
Generate Objects
      ↓
LTO
      ↓
Link
      ↓
Validate
      ↓
Write Artifact
```

---

# 4. `axc check`

```text id="2h8t8b"
axc check
```

không cần:

```text
codegen
link
```

Pipeline:

```text id="eq6i4u"
Source
 ↓
Parse
 ↓
Resolve
 ↓
Type
 ↓
Trait
 ↓
Comptime
 ↓
HIR
 ↓
MIR
 ↓
Verification
```

Mục tiêu:

> Phát hiện mọi lỗi semantic mà không cần tạo binary.

---

# 5. `axc run`

```text id="s8j3m2"
axc run
```

về logic:

```text id="0a6e4r"
build
 ↓
artifact
 ↓
execute
```

Nhưng driver phải tránh rebuild nếu artifact còn hợp lệ.

```text id="k0f3fs"
source unchanged
+
config unchanged
+
dependencies unchanged
+
compiler semantic version unchanged
```

→ sử dụng artifact cache.

---

# 6. `axc test`

Test runner không nên là một chương trình riêng biệt không hiểu Axiom.

Nó sử dụng:

```text id="a1e2b3"
CompilerDB
BuildGraph
ArtifactGraph
```

để:

```text id="t1x8a9"
discover tests
 ↓
compile tests
 ↓
parallel execute
 ↓
collect results
```

Test isolation là trách nhiệm của test runtime/profile.

---

# 7. `axc bench`

Benchmark cần tách khỏi test:

```text id="q6y7k1"
axc bench
```

có thể:

```text id="l4q8s2"
compile
 ↓
warmup
 ↓
measurement
 ↓
statistics
 ↓
profile
```

Kết quả benchmark có thể trở thành input cho:

```text id="f4j2m9"
axc tune
```

nhưng **không trở thành semantic input**.

---

# 8. `axc emit`

Cho phép dừng ở từng tầng:

```text id="b8p7n4"
axc emit --ast
axc emit --hir
axc emit --mir
axc emit --verified-mir
axc emit --opt-ir
axc emit --abi
axc emit --lir
axc emit --machine
axc emit --object
```

Điều này cực kỳ quan trọng cho:

- compiler development;
- debugging;
- AI agent;
- compiler conformance;
- miscompilation analysis.

---

# 9. `axc inspect`

`inspect` không phải debug hack.

Nó là **compiler introspection API chính thức**.

Ví dụ:

```text id="x4r8c1"
axc inspect type Foo
axc inspect traits Foo
axc inspect effects foo
axc inspect ownership foo
axc inspect aliases foo
axc inspect escape foo
axc inspect storage foo
axc inspect inline foo
axc inspect vectorize foo
axc inspect layout Foo
axc inspect callgraph foo
axc inspect binary app
```

---

# 10. CompilerDB không thuộc Driver

Driver không được tự giữ:

```text
types
functions
MIR
traits
```

thành những cache riêng.

Thay vào đó:

```text id="x9q3m2"
Driver
  ↓
CompilerDB
  ↓
Query Engine
```

Driver chỉ xác định:

```text
inputs
targets
requested outputs
build policy
```

---

# 11. Build Planner

`BuildPlanner` chuyển:

```text
Workspace
```

thành:

```text id="p4k8w2"
BuildPlan
```

Ví dụ:

```text id="s1d5x7"
BuildPlan {
    packages[]
    modules[]
    compiler_units[]
    generic_units[]
    comptime_units[]
    objects[]
    link_units[]
    runtime_components[]
    final_artifact
}
```

---

# 12. Build Graph

Graph:

```text id="q8r4m6"
Source
 ↓
Module
 ↓
Package
 ↓
Generic Instance
 ↓
Object
 ↓
Library
 ↓
Executable
```

Các edge:

```text id="j6s2p8"
depends-on
imports
generates
instantiates
references
links
```

Graph phải DAG ở cấp package/build artifact.

---

# 13. Module cycle

Như đã frozen:

```text id="d8k1p4"
Module A → Module B
Module B → Module A
```

có thể hợp lệ.

Nhưng:

```text id="z5m2q7"
Package A → Package B
Package B → Package A
```

→ reject.

Driver phải phân biệt hai loại graph.

---

# 14. Compilation Unit

Không nhất thiết:

```text
1 source file = 1 compiler process
```

Axiom nên có logical:

```text id="n7w4p2"
CompilationUnit
```

có thể gồm:

- module;
- generic instance;
- generated comptime declarations;
- specialized implementation.

Điều này cho phép incremental compilation tốt hơn.

---

# 15. Parallel scheduler

Scheduler:

```text id="w6x3j9"
Ready Queue
    ↓
Worker 1
Worker 2
Worker 3
...
Worker N
```

Một unit chỉ chạy khi dependency semantic cần thiết đã hoàn thành.

Ví dụ:

```text id="x5d7p1"
A ─┐
B ─┼→ D
C ─┘
```

A/B/C compile song song.

D chờ A/B/C.

---

# 16. Query parallelism

Không chỉ build unit.

CompilerDB cũng có thể chạy:

```text id="c3v8m1"
type queries
trait queries
comptime queries
MIR queries
analysis queries
```

song song.

Query engine phải đảm bảo:

```text
deterministic result
```

không phụ thuộc worker count.

---

# 17. Cancellation

Compiler phải hỗ trợ:

```text id="h8n2q5"
Ctrl+C
IDE cancellation
build superseded
```

Query đang chạy có thể nhận:

```text id="r7m4x2"
CancellationToken
```

và dừng an toàn.

Không được để cancellation làm cache lưu trạng thái nửa hợp lệ.

---

# 18. Incremental compilation

Một thay đổi nhỏ:

```ax id="w2k5v8"
fn foo() { ... }
```

không nên rebuild toàn workspace.

Compiler sử dụng:

```text id="e3q7n1"
Source Fingerprint
 ↓
Query Dependencies
 ↓
Invalidation
```

Chỉ những query phụ thuộc semantic result bị invalidated.

---

# 19. Interface vs implementation

Ví dụ:

```text id="j5k9r3"
pub struct Foo {
    pub x: i32
}
```

thay đổi implementation:

```text id="a4c8m2"
fn internal_helper()
```

không nên invalidate downstream nếu public interface không đổi.

Do đó mỗi module có:

```text id="f2w7k9"
InterfaceFingerprint
ImplementationFingerprint
```

---

# 20. Cache hierarchy

Axiom đã có cache model:

```text id="q1r8m4"
L0 Memory
L1 Query Cache
L2 Module/Package Cache
L3 Object Cache
L4 Artifact Cache
```

Driver phải quyết định cache nào có thể reuse.

---

# 21. Cache key

Không được dùng:

```text
source hash
```

đơn độc.

Artifact identity cần:

```text id="n8x4c2"
source
dependency fingerprints
compiler semantic version
target
ABI
profile
features
comptime inputs
codegen configuration
```

và các input semantic khác.

---

# 22. Cache poisoning defense

Một artifact cache không đáng tin không được coi là semantic truth.

Cache entry phải:

```text id="u3k6m9"
verify identity
verify content hash
verify metadata
verify target
verify ABI
```

Không match:

```text
→ rebuild
```

---

# 23. Dependency resolution

Driver:

```text id="c8m2q7"
package.ax
   ↓
dependency resolver
   ↓
axiom.lock
   ↓
exact dependency graph
```

Lockfile quyết định source/version/content identity chính xác.

---

# 24. Cross compilation

Ví dụ:

```text id="y4p8n1"
axc build
    --target=x86_64-linux
```

Host:

```text id="j2f6q8"
Windows x64
```

Target:

```text id="m7k3r5"
Linux x64
```

Compiler driver phải tách:

```text
Host
Target
Build
```

khỏi nhau.

---

# 25. Target configuration

Target descriptor:

```text id="b6v9s4"
Target {
    architecture
    operating_system
    environment
    object_format
    abi
    pointer_width
    endianness
    features
    calling_conventions
    linker
    runtime_profile
}
```

Không hard-code:

```text
if windows ...
if linux ...
```

tràn lan trong compiler.

---

# 26. Native linker selection

Bootstrap có thể:

```text id="p3x8k6"
Axiom
 ↓
ObjectWriter
 ↓
system linker / LLD
```

nhưng production cuối cùng:

```text id="m8q2r4"
Axiom ObjectWriter
 ↓
Axiom Linker
```

Driver abstraction:

```text id="v6w1s9"
LinkStrategy
```

cho phép thay backend mà không đổi semantic compiler.

---

# 27. Bootstrap compiler pipeline

Đây là phần đặc biệt quan trọng.

### Stage 0

```text id="h4n7q2"
External compiler
 ↓
Axiom frontend
 ↓
LLVM/other temporary backend
```

### Stage 1

```text id="k3m8p1"
External compiler
 ↓
Axiom Compiler
 ↓
Axiom MIR
 ↓
temporary backend
```

### Stage 2

```text id="q7r2x5"
Axiom Compiler
 ↓
Axiom LIR
 ↓
Axiom Machine Backend
 ↓
external linker
```

### Stage 3

```text id="z8c4m6"
Axiom Compiler
 ↓
Axiom ObjectWriter
 ↓
Axiom Linker
```

### Stage 4

```text id="n5w9k2"
Axiom Compiler
      ↓
compiles
      ↓
Axiom Compiler
```

→ self-hosted.

---

# 28. Three-way bootstrap

Không chỉ:

```text
compiler A
→ compiler B
```

Mà:

```text id="a2f7m9"
axc1
 ↓ compile axc
axc2
 ↓ compile axc
axc3
```

Sau đó so sánh:

```text
semantic output
diagnostics
compiler behavior
```

và trong reproducible configurations có thể so sánh artifact hashes khi pipeline đảm bảo deterministic output.

---

# 29. Driver không được quyết định semantics

Ví dụ driver thấy:

```text
-Oz
```

thì được phép thay:

```text
optimization policy
```

nhưng không được thay:

```text
ownership rules
type rules
overflow semantics
drop semantics
```

Optimization configuration nằm dưới semantic boundary.

---

# 30. Profile composition

Build config:

```text id="u8q3m5"
Profile {
    optimization
    debug
    panic
    lto
    pgo
    sanitizer
    cpu_features
    size_policy
}
```

Ví dụ:

```text
dev
release
size
debug
sanitize
bench
```

Profile chỉ là policy.

---

# 31. Runtime composition

Sau semantic analysis:

```text id="w4n7c2"
RequiredCapabilities
        ↓
RuntimeComponentResolver
        ↓
STARTUP
ALLOCATOR
THREAD
IO
...
```

Chỉ component cần thiết mới đi vào link graph.

---

# 32. Build event stream

Đây là một điểm nên làm rất mạnh cho Axiom.

Compiler phát:

```text id="m9x2q6"
BuildEvent
```

Ví dụ:

```text
ParseStarted
ParseFinished
TypeCheckStarted
TypeCheckFinished
MIRVerified
OptimizationStarted
ObjectGenerated
CacheHit
CacheMiss
LinkStarted
LinkFinished
ArtifactProduced
Diagnostic
```

Mỗi event có:

```text id
timestamp
unit
phase
status
duration
source
```

---

# 33. AI-readable build protocol

BuildEvent nên có machine-readable format:

```text id="f7k3p8"
JSON / binary structured protocol
```

Ví dụ:

```text id="s2n6r4"
{
    "event": "MIRVerified",
    "function": "foo",
    "status": "success"
}
```

AI agent có thể hiểu:

```text
what happened
what failed
what is compiling
what is cached
what is blocking
```

mà không phải parse terminal text.

---

# 34. Diagnostic pipeline

Compiler diagnostic:

```text id="e6m2k8"
Compiler
 ↓
DiagnosticDB
 ↓
Driver formatter
```

Có thể output:

```text
human
json
jsonl
machine
```

Ví dụ:

```text
axc build --diagnostic-format=json
```

---

# 35. Error categories

Driver phân biệt:

```text id="r4v8m1"
SourceError
SemanticError
VerificationError
CodegenError
LinkError
BuildError
EnvironmentError
CompilerBug
```

Đặc biệt:

```text
CompilerBug ≠ user error
```

---

# 36. ICE

Internal Compiler Error phải có:

```text id="k7p3x9"
compiler version
target
phase
query
source fingerprint
diagnostic ID
stack/context
repro command
```

để AI/compiler developer tái hiện.

---

# 37. Repro command

Ví dụ compiler gặp lỗi:

```text id="d8m4q2"
axc: internal compiler error
```

có thể xuất:

```text
Reproduce:
axc build --target=x86_64-linux --profile=debug ...
```

với config đã canonicalized.

---

# 38. Build locking

Hai process cùng build workspace:

```text
axc build
axc build
```

không được phá cache/artifact.

Cần:

```text id="p5n8w3"
workspace lock
artifact atomic write
cache atomic publish
```

---

# 39. Atomic artifact publication

Compiler không nên:

```text
ghi trực tiếp app.exe
```

rồi crash giữa chừng.

Nên:

```text id="s7q2m4"
temporary artifact
 ↓
validate
 ↓
fsync/commit policy
 ↓
atomic rename
```

Artifact chỉ trở thành cache entry sau khi hoàn tất.

---

# 40. Build determinism

Scheduler có thể chạy:

```text
1 thread
```

hoặc:

```text
32 threads
```

nhưng semantic output phải tương đương.

Nếu reproducible mode:

```text id="h2c9m6"
worker count
query scheduling
hash-map iteration
```

không được làm thay đổi output.

---

# 41. Distributed compilation

Kiến trúc 152 nên **cho phép** distributed build nhưng không bắt buộc.

```text id="q6x3p8"
BuildPlan
 ↓
Remote Workers
 ↓
Object Cache
 ↓
Local Link
```

Artifact phải content-addressed.

Remote worker không được trở thành trusted semantic authority.

---

# 42. Remote cache

Có thể:

```text
local cache
        ↓ miss
remote cache
        ↓ miss
compile
```

Nhưng remote artifact phải xác minh:

```text id="v8m1r5"
content hash
build identity
compiler identity
target
ABI
```

---

# 43. Compiler daemon

IDE có thể chạy:

```text id="a7k4n2"
axc daemon
```

giữ:

```text
CompilerDB
TypeDB
SyntaxDB
```

trong memory.

Kết quả:

```text id="x3p9m6"
edit
 ↓
incremental query
 ↓
diagnostic
```

rất nhanh.

CLI vẫn có thể dùng one-shot mode.

---

# 44. `axc` architecture

Đóng băng cấu trúc:

```text id="z5w8r1"
axc/
 ├── driver/
 ├── cli/
 ├── workspace/
 ├── resolver/
 ├── build/
 ├── scheduler/
 ├── cache/
 ├── target/
 ├── compiler/
 ├── linker/
 ├── diagnostics/
 ├── profile/
 └── daemon/
```

`compiler/` sử dụng `CompilerDB`, không phụ thuộc ngược vào CLI.

---

# 45. End-to-end build

Một build thực tế:

```text id="c9m4x7"
$ axc build --release

CLI
 ↓
Load workspace
 ↓
Load axiom.lock
 ↓
Resolve packages
 ↓
Resolve target
 ↓
Load profile
 ↓
Create BuildPlan
 ↓
Query CompilerDB
 ↓
Incremental invalidation
 ↓
Parallel compile
 ↓
Verify MIR
 ↓
Optimize
 ↓
Generate object
 ↓
LTO
 ↓
Link
 ↓
Section GC
 ↓
Binary validation
 ↓
Artifact cache
 ↓
app.exe
```

---

# 46. Điều quan trọng: CompilerDB là “não”, Driver là “hệ thần kinh”

Có thể coi:

```text id="f3q7n8"
CompilerDB
    = semantic brain

Driver
    = orchestration layer

BuildGraph
    = execution plan

Scheduler
    = execution engine

Cache
    = persistent memory

ObjectWriter/Linker
    = artifact production
```

Không nên trộn chúng.

---

# 47. Invariants

Đóng băng:

### `ADRIVER-20`
Driver orchestration cannot redefine language semantics.

### `ADRIVER-21`
CompilerDB remains the authoritative semantic compilation state.

### `ADRIVER-22`
Build planning is deterministic for identical inputs.

### `ADRIVER-23`
Parallel scheduling cannot change semantic results.

### `ADRIVER-24`
Cancellation cannot publish incomplete semantic or artifact cache entries.

### `ADRIVER-25`
Incremental compilation preserves clean-build semantics.

### `ADRIVER-26`
Interface changes and implementation-only changes are distinguished.

### `ADRIVER-27`
Cache identity includes all semantic-relevant build inputs.

### `ADRIVER-28`
Invalid or mismatched cache entries are never trusted as valid artifacts.

### `ADRIVER-29`
Build graph dependencies are explicit.

### `ADRIVER-30`
Package cycles are rejected.

### `ADRIVER-31`
Module cycles remain governed by module semantics.

### `ADRIVER-32`
Host and target environments are distinct.

### `ADRIVER-33`
Cross compilation does not execute target code during ordinary compilation unless explicitly requested through a supported capability.

### `ADRIVER-34`
Optimization profiles cannot change language semantics.

### `ADRIVER-35`
Runtime components are resolved from actual program requirements.

### `ADRIVER-36`
Unused runtime components remain removable.

### `ADRIVER-37`
Build events are machine-readable.

### `ADRIVER-38`
Diagnostics have stable machine-readable identity.

### `ADRIVER-39`
Compiler errors are distinguishable from user errors.

### `ADRIVER-40`
Internal compiler failures carry reproducible context.

### `ADRIVER-41`
Artifact publication is atomic.

### `ADRIVER-42`
Concurrent builds cannot corrupt shared caches.

### `ADRIVER-43`
Remote cache artifacts require identity/content validation.

### `ADRIVER-44`
Distributed compilation cannot weaken semantic verification.

### `ADRIVER-45`
One-shot and daemon compilation use the same semantic CompilerDB model.

### `ADRIVER-46`
Compiler introspection uses the same internal semantic data as compilation.

### `ADRIVER-47`
`axc check` does not require code generation.

### `ADRIVER-48`
`axc run` reuses valid build artifacts.

### `ADRIVER-49`
`axc emit` can expose intermediate compiler representations without redefining them.

### `ADRIVER-50`
Bootstrap stages may temporarily use external tools but production Axiom does not semantically depend on them.

### `ADRIVER-51`
Three-way bootstrap must be supported for compiler self-validation.

### `ADRIVER-52`
Build reproducibility does not depend on worker count.

### `ADRIVER-53`
Compiler cache is an optimization, never a semantic authority.

### `ADRIVER-54`
Build orchestration remains separate from semantic compilation.

### `ADRIVER-55`
The final native compiler can replace temporary external compiler/linker components without redesigning the language semantics.

---

# Kiến trúc Axiom hiện tại

Sau 152, chuỗi chính đã đi rất xa:

```text id="p9m3w7"
CORE LANGUAGE
      ↓
TYPE / TRAIT
      ↓
OWNERSHIP / CAPABILITY
      ↓
MIR
      ↓
VERIFICATION
      ↓
ALIAS / EFFECT / ESCAPE
      ↓
SSA / MemorySSA
      ↓
INTERPROCEDURAL
      ↓
INLINE / SPECIALIZE / DEVIRTUALIZE
      ↓
LOOP / MEMORY / DATA LAYOUT
      ↓
SIMD / MICROARCH / PGO
      ↓
LTO
      ↓
ABI / LIR / MACHINE
      ↓
OBJECT / LINKER
      ↓
BINARY OPTIMIZATION
      ↓
BUILD DRIVER
      ↓
SELF-HOSTING
```

### BOOTSTRAP-153 — Package Manager, Registry, Dependency Fetching & Reproducible Dependency Supply Chain

Bước kế tiếp nên giải quyết **hệ sinh thái dependency thực tế** thay vì tiếp tục tối ưu compiler:

```text id="m8x2q5"
package.ax
     ↓
Dependency Resolver
     ↓
Registry / Git / Local / Archive
     ↓
Content Verification
     ↓
axiom.lock
     ↓
Package Cache
     ↓
Package Graph
     ↓
BuildPlan
```

và đặc biệt phải chốt một vấn đề rất quan trọng đối với mục tiêu của Axiom:

> **Axiom không phụ thuộc third-party compiler/library ở cấp runtime, nhưng hoàn toàn có thể cho phép ứng dụng sử dụng package bên ngoài.**

Cần phân biệt rõ **compiler dependency**, **runtime dependency**, **source dependency**, **binary dependency**, **system dependency** và **build-tool dependency**, nếu không hệ thống package sau này rất dễ làm phá vỡ triết lý “native, self-contained, reproducible” của Axiom.