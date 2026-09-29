# BOOTSTRAP-768 — AXBUILD

**Title:** Native Build Graph, Project Model, Compilation Orchestration, Incremental Build, Artifact Cache, Link Planning, Cross-Compilation & Reproducible Build Runtime 5.0  
**Namespace:** `AXBUILD`  
**Phase:** Axiom Native Toolchain / Build Orchestration  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXBUILD` là build engine native của Axiom, chịu trách nhiệm biến:

```text
Project
   ↓
Source Graph
   ↓
Dependency Graph
   ↓
Compilation Plan
   ↓
Compiled Modules
   ↓
Link Plan
   ↓
Native Artifact
```

AXBUILD phải đạt các mục tiêu:

- incremental build rất nhanh;
- parallel compilation;
- deterministic build;
- reproducible build;
- cross compilation;
- dependency-aware scheduling;
- compiler cache;
- linker planning;
- multi-target;
- multi-configuration;
- IDE/CLI integration;
- không tạo runtime dependency cho application;
- không phụ thuộc third-party build system.

---

# 2. Boundary

`AXBUILD` sở hữu:

- project model;
- workspace;
- build graph;
- source graph;
- build configuration;
- target configuration;
- compilation scheduling;
- incremental invalidation;
- artifact cache orchestration;
- linker planning;
- build transactions;
- build diagnostics;
- reproducibility coordination.

Không sở hữu:

```text
AXCOMPILER  → source → IR/machine code
AXLINKER    → final symbol/layout resolution
AXPACKAGE   → packages/dependencies
AXREGISTRY  → service/resource registry
AXPROCESS   → process execution
AXSECURITY  → authorization/sandbox
AXSTORAGE    → storage primitives
AXNETWORK    → network transport
```

AXBUILD điều phối các subsystem này.

---

# 3. Core principle

Build system phải là **orchestrator**, không phải runtime.

Sau khi:

```text
axiom build app
```

binary không được cần:

```text
AXBUILD
```

để chạy.

---

# 4. Architecture

```text id="buildarch"
                 AXBUILD
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Project       Config       Target
       │            │            │
       └────────────┼────────────┘
                    ▼
               Build Graph
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Source     Package    Toolchain
        Graph      Graph       Graph
          │         │           │
          └─────────┼───────────┘
                    ▼
             Incremental Plan
                    │
                    ▼
              Parallel Scheduler
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      AXCOMPILER           AXBUILD CACHE
          │                   │
          └─────────┬─────────┘
                    ▼
                AXLINKER
                    │
                    ▼
              Native Artifact
```

---

# 5. Project

Canonical project:

```text id="project"
project {
    identity
    source_roots
    module_roots
    dependencies
    targets
    profiles
    outputs
    build_options
}
```

---

# 6. Project identity

Project identity phải stable nhưng không được dùng làm artifact identity.

```text
project_id
```

không đồng nghĩa:

```text
package_id
module_id
artifact_id
```

---

# 7. Workspace

Workspace chứa một hoặc nhiều projects:

```text id="workspace"
workspace
 ├── project A
 ├── project B
 └── project C
```

Cho phép monorepo và multi-project builds.

---

# 8. Workspace graph

```text id="workspacegraph"
App
 ├── Core
 ├── Graphics
 └── Network

Tools
 └── Core
```

AXBUILD phải detect dependency graph giữa projects.

---

# 9. Source roots

Project khai báo:

```text
src/
modules/
generated/
tests/
```

Compiler không được tự động quét toàn bộ filesystem ngoài declared roots.

---

# 10. Module discovery

Module có thể được:

- explicitly declared;
- discovered theo canonical project rules.

Discovery phải deterministic.

---

# 11. Build configuration

Configuration:

```text id="config"
DEBUG
RELEASE
PROFILE
TEST
CUSTOM
```

Configuration là input của build graph.

---

# 12. Target configuration

Target:

```text id="targetconfig"
OS
ARCH
ABI
CPU_FEATURES
LINK_MODE
SUBSYSTEM
SDK
```

Ví dụ:

```text
windows-x86_64-msvc-compatible
linux-x86_64
linux-arm64
macos-arm64
ios-arm64
android-arm64
wasm32
```

---

# 13. Toolchain

Toolchain descriptor:

```text id="toolchain"
compiler
linker
assembler
object_format
sysroot
sdk
target
version
```

Axiom native toolchain có thể do chính Axiom cung cấp.

---

# 14. Native bootstrap

AXBUILD phải hỗ trợ bootstrap stages:

```text
stage0
 ↓
stage1 compiler
 ↓
stage2 self-hosted compiler
 ↓
native AXBUILD
```

Mục tiêu cuối:

```text
Axiom compiler builds Axiom compiler
```

---

# 15. Build graph

Canonical graph:

```text id="graph"
Node
 ├── Source
 ├── Module
 ├── Generated Source
 ├── Object
 ├── Static Library
 ├── Dynamic Library
 ├── Resource
 └── Executable

Edge
 ├── imports
 ├── compile-depends
 ├── link-depends
 ├── generates
 └── packages
```

---

# 16. Graph acyclicity

Compilation graph phải DAG.

```text
A → B → C
```

Cycle:

```text
A → B → A
```

phải diagnostic.

Các graph đặc biệt được phép cycle chỉ khi subsystem định nghĩa semantics riêng.

---

# 17. Source dependency

Nếu:

```text
A imports B
```

thay đổi public interface của B có thể invalidate A.

---

# 18. Implementation-only change

Nếu B thay đổi implementation nhưng interface/ABI không đổi:

```text
B.recompile
A → reusable
```

đây là mục tiêu quan trọng của incremental build.

---

# 19. Interface hash

Mỗi module có:

```text
interface_hash
```

Hash đại diện canonical exported interface.

---

# 20. ABI hash

Native module có:

```text
abi_hash
```

ABI hash thay đổi → dependent native artifacts có thể cần rebuild.

---

# 21. Implementation hash

```text
implementation_hash
```

dùng để xác định source implementation thay đổi.

---

# 22. Build fingerprint

Build node fingerprint:

```text id="fingerprint"
source_hash
interface_hash
abi_hash
compiler_hash
compiler_options
target
features
dependencies
environment_inputs
```

→ canonical build key.

---

# 23. Build key

```text id="buildkey"
build_key = HASH(canonical_build_inputs)
```

Không sử dụng filesystem timestamp làm identity chính.

---

# 24. Timestamp

Timestamp chỉ là optimization hint.

Correctness không được phụ thuộc timestamp.

---

# 25. Incremental build

Flow:

```text
source change
 ↓
hash/fingerprint
 ↓
detect affected node
 ↓
invalidate minimal closure
 ↓
reuse unaffected artifacts
```

---

# 26. Minimal invalidation

Nếu:

```text
A → B → C
D → C
```

C thay implementation nhưng interface unchanged:

```text
C rebuild
A/D reuse
```

nếu C's artifact contract remains compatible.

---

# 27. Interface change

Nếu C interface thay đổi:

```text
C rebuild
 ↓
A rebuild
D rebuild
```

chỉ những dependents bị ảnh hưởng.

---

# 28. Link-only changes

Thay linker option không cần recompile source nếu object artifacts vẫn valid.

```text
objects
 ↓
new link plan
 ↓
link
```

---

# 29. Compile-only changes

Compiler optimization change:

```text
-O2 → -O3
```

phải invalidate compiled artifacts affected by the option.

---

# 30. Parallel scheduler

AXBUILD scheduler:

```text
ready nodes
    ↓
worker pool
    ↓
completed nodes
    ↓
unlock dependents
```

---

# 31. Scheduling

Scheduler ưu tiên:

1. dependency readiness;
2. critical path;
3. resource constraints;
4. cache availability.

Không yêu cầu fixed heuristic trong core, nhưng kết quả phải deterministic nếu deterministic scheduling mode được bật.

---

# 32. CPU parallelism

Compiler jobs có thể chạy:

```text
N = available CPU resources
```

nhưng phải respect memory limits.

---

# 33. Memory-aware scheduling

Mỗi build node có estimate:

```text
cpu_cost
memory_cost
io_cost
```

Scheduler tránh launch quá nhiều compiler instances gây RAM exhaustion.

---

# 34. NUMA

Machine nhiều NUMA node có thể schedule compile workers gần memory locality.

Đây là optimization, không phải semantic requirement.

---

# 35. Job isolation

Mỗi compile job phải có explicit:

```text
input set
output set
environment
target
capabilities
```

---

# 36. Hermetic build

Hermetic build:

```text
declared inputs
+
declared toolchain
+
declared environment
```

không phụ thuộc hidden machine state.

---

# 37. Environment capture

Chỉ environment variables được project khai báo mới được phép ảnh hưởng deterministic build.

Ví dụ:

```text
AX_BUILD_MODE
AX_TARGET
```

---

# 38. Hidden input detection

AXBUILD có thể detect compiler attempting undeclared file/environment dependency.

Trong strict mode:

```text
BUILD_UNDECLARED_INPUT
```

---

# 39. Generated sources

Generated source là graph node:

```text
schema
 ↓
generator
 ↓
generated.ax
 ↓
compiler
```

Generator inputs/outputs phải explicit.

---

# 40. Generated source cache

Generator output có thể cache bằng fingerprint.

---

# 41. Build actions

Canonical action:

```text
build_action {
    inputs
    outputs
    command
    toolchain
    environment
    capabilities
}
```

---

# 42. Action determinism

Action phải declare complete logical inputs.

Không dựa vào:

```text
current directory
current time
randomness
machine-specific hidden state
```

nếu reproducibility yêu cầu.

---

# 43. Build sandbox

Build action có thể chạy trong AXSECURITY sandbox.

Default:

```text
filesystem = declared inputs/outputs
network = deny
process = restricted
device = deny
```

---

# 44. Explicit network build

Một package build requiring network phải declare capability/policy.

Không silently access Internet.

---

# 45. Build secrets

Secrets không được trở thành build fingerprint hoặc artifact content trừ khi explicitly required.

---

# 46. Compiler invocation

AXBUILD gọi AXCOMPILER thông qua native API:

```text
compiler_compile(request)
```

Không bắt buộc spawn process cho từng source.

---

# 47. In-process compiler

IDE hoặc AXBUILD có thể dùng compiler library:

```text
AXBUILD
   ↓
AXCOMPILER API
```

giảm process startup overhead.

---

# 48. Out-of-process compiler

Có thể chạy compiler worker process khi isolation cần thiết.

Hai modes phải produce equivalent semantic artifacts.

---

# 49. Compiler server

Persistent compiler worker:

```text
AXCOMPILER SERVER
       ↑
       │
    AXBUILD
```

giảm startup/parsing overhead.

Không phải runtime dependency.

---

# 50. Compiler state

Compiler server state phải được invalidatable.

Không được để stale state silently alter build correctness.

---

# 51. Parse cache

AST/parse representation có thể cache:

```text
source hash
+
parser version
```

---

# 52. Semantic cache

Typed/module analysis có thể cache:

```text
source
+
imports
+
compiler semantic version
```

---

# 53. IR cache

IR cache key:

```text
interface
implementation
compiler
target
optimization
```

---

# 54. Object cache

Object cache key:

```text
canonical build key
```

Object artifact immutable.

---

# 55. Link cache

Final link output có thể cache khi:

```text
objects
linker
link options
target
resources
```

không đổi.

---

# 56. Cache hierarchy

```text
memory cache
      ↓
project cache
      ↓
user cache
      ↓
shared cache
      ↓
AXPACKAGE repository
```

---

# 57. Cache locality

Local cache-hit phải tránh network.

---

# 58. Remote cache

Remote build cache optional.

Remote cache artifact phải verify content hash.

---

# 59. Remote cache trust

Remote cache không mặc nhiên trusted.

Security policy kiểm tra:

```text
hash
signature
provenance
```

nếu required.

---

# 60. Cache poisoning

Artifact key + cryptographic content verification phải ngăn cache entry thay thế artifact khác.

---

# 61. Cache garbage collection

Cache GC dùng reachability:

```text
active builds
+
lockfiles
+
pinned artifacts
+
recent roots
```

không xóa live artifact.

---

# 62. Build transaction

Một build có:

```text
BUILD_BEGIN
PLAN
EXECUTE
VALIDATE
COMMIT
```

---

# 63. Failed build

Nếu build fail:

```text
previous valid artifacts
```

không bị corrupt.

---

# 64. Output staging

Build output:

```text
workspace/.axiom/staging/
```

sau validation mới activate thành output chính.

---

# 65. Artifact activation

Activation phải atomic đối với logical project state.

---

# 66. Build manifest

AXBUILD có thể emit:

```text
build.manifest
```

chứa:

- input hashes;
- output hashes;
- compiler;
- target;
- dependency graph;
- build options.

---

# 67. Reproducible build

Strict reproducibility:

```text
same source
same lockfile
same toolchain
same target
same declared environment
```

→ same canonical artifact bytes, nếu target/toolchain semantics hỗ trợ.

---

# 68. Reproducibility classes

```text
BITWISE
SEMANTIC
DIAGNOSTIC
```

`BITWISE` là strongest.

---

# 69. Bitwise reproducibility

Phải normalize:

- timestamps;
- paths;
- archive ordering;
- symbol ordering;
- UUID-like nondeterministic fields;
- random seeds;
- debug metadata.

---

# 70. Build path normalization

Absolute local paths không được embedded trong release artifact nếu reproducibility yêu cầu.

Có thể dùng:

```text
/source/project
```

canonical virtual root.

---

# 71. Deterministic ordering

Directory/archive/object metadata ordering phải canonical.

---

# 72. Deterministic parallelism

Parallel execution không được làm output ordering nondeterministic.

---

# 73. Randomized compiler passes

Nếu compiler sử dụng randomization:

```text
build_seed
```

phải explicit trong reproducible mode.

---

# 74. Build profiles

Canonical profiles:

```text
DEBUG
RELEASE
SIZE
SPEED
PROFILE
TEST
SANITIZE
```

Profiles là presets, không phải semantic requirement.

---

# 75. Optimization policy

AXBUILD truyền optimization policy tới AXCOMPILER.

Compiler quyết định transformation correctness.

---

# 76. Size optimization

```text
SIZE
```

có thể enable:

- dead code elimination;
- section elimination;
- link-time optimization;
- compact metadata.

---

# 77. Speed optimization

```text
SPEED
```

có thể enable:

- inlining;
- specialization;
- vectorization;
- LTO;
- profile-guided optimization.

---

# 78. PGO

Profile-guided build:

```text
instrument
 ↓
run workload
 ↓
collect profile
 ↓
rebuild
```

Profile là explicit build input.

---

# 79. LTO

AXBUILD phải support:

```text
module compilation
 ↓
IR/object metadata
 ↓
link-time optimization
 ↓
native output
```

nếu AXCOMPILER/AXLINKER hỗ trợ.

---

# 80. Whole-program optimization

Có thể optimize toàn application nhưng phải preserve explicit module boundaries khi dynamic libraries yêu cầu ABI.

---

# 81. Static vs dynamic build

Build target:

```text
STATIC
DYNAMIC
MIXED
```

---

# 82. Executable output

AXBUILD phải orchestrate:

```text
.exe
ELF
Mach-O
WASM
```

và các target tương ứng.

---

# 83. PE64 build

Windows target:

```text
compile
 ↓
COFF/object
 ↓
link
 ↓
PE64
```

AXBUILD phải preserve target metadata.

---

# 84. ELF build

Linux:

```text
compile
 ↓
ELF objects
 ↓
link
 ↓
ELF executable/shared object
```

---

# 85. Mach-O build

macOS/iOS:

```text
compile
 ↓
Mach-O objects
 ↓
link
 ↓
Mach-O artifact
```

---

# 86. WASM build

WASM:

```text
Axiom modules
 ↓
WASM code generation
 ↓
WASM linking/validation
 ↓
.wasm
```

---

# 87. Resource compilation

Resources là build graph nodes:

```text
image
font
translation
shader
model
```

và được compiled/packed theo target.

---

# 88. Shader build

Graphics package:

```text
shader source
 ↓
target shader representation
 ↓
resource artifact
```

AXBUILD chỉ orchestrate; graphics compiler semantics thuộc AXGRAPHICS/compiler subsystem.

---

# 89. Tests

Test target:

```text
test executable
```

AXBUILD có thể compile and execute tests.

Execution chịu AXPROCESS/AXSECURITY.

---

# 90. Test isolation

Parallel tests phải có explicit resource isolation.

---

# 91. Test caching

Test results có thể cache only when:

```text inputs
+
environment
+
test binary
```

đủ deterministic.

---

# 92. Build diagnostics

Build error phải identify:

```text
project
module
action
input
target
dependency path
```

---

# 93. Failure graph

Khi action fail:

```text
failed node
 ↓
dependent nodes
```

không nên báo hàng trăm lỗi cascading như lỗi độc lập nếu chúng chỉ là consequences.

---

# 94. Diagnostic categories

```text
BUILD_CONFIG_ERROR
BUILD_GRAPH_ERROR
BUILD_DEPENDENCY_ERROR
BUILD_TOOLCHAIN_ERROR
BUILD_COMPILER_ERROR
BUILD_LINK_ERROR
BUILD_IO_ERROR
BUILD_SECURITY_ERROR
BUILD_CACHE_ERROR
BUILD_REPRODUCIBILITY_ERROR
```

---

# 95. Explain plan

AXBUILD phải support:

```text
axiom build --plan
```

hiển thị:

```text
nodes
dependencies
cache hits
rebuild reasons
targets
```

---

# 96. Why rebuild

Một feature quan trọng:

```text
axiom build --why
```

Ví dụ:

```text
module A rebuilt because:
  B interface hash changed
```

---

# 97. Dry run

```text
axiom build --dry-run
```

không mutate artifacts.

---

# 98. Clean build

```text
axiom build --clean
```

xóa derived state nhưng không được xóa source/package data ngoài explicit scope.

---

# 99. Build watch

Optional:

```text
axiom build --watch
```

file change:

```text
detect
 ↓
invalidate
 ↓
rebuild
```

---

# 100. IDE integration

AXBUILD cung cấp machine-readable:

```text
project graph
target graph
diagnostics
symbol/source mappings
build status
```

cho IDE.

---

# 101. Language server integration

AXBUILD expose module/package resolution environment cho language server.

Không duplicate dependency semantics.

---

# 102. Multi-target build

Một project có thể build:

```text
windows-x86_64
linux-x86_64
linux-arm64
```

trong cùng invocation.

---

# 103. Target matrix

```text id="matrix"
project
 ├── windows-x64
 ├── linux-x64
 ├── linux-arm64
 └── wasm32
```

Mỗi target có independent build graph/cache key.

---

# 104. SDK

SDK identity là build input:

```text
sdk_id
sdk_version
sdk_hash
```

---

# 105. Sysroot

Native target có:

```text
sysroot
```

được fingerprint.

---

# 106. Platform headers/interfaces

Axiom không nên phụ thuộc C headers để build native Axiom code.

Platform ABI descriptions nên có native metadata.

---

# 107. Foreign libraries

Axiom vẫn phải link native external libraries khi developer explicit yêu cầu.

AXBUILD records:

```text
foreign_dependency
```

nhưng không biến chúng thành mandatory Axiom compiler dependencies.

---

# 108. C ABI

AXBUILD phải hỗ trợ projects sử dụng foreign ABI:

```text
C
C++
system ABI
```

thông qua explicit FFI declarations.

---

# 109. Foreign dependency reproducibility

External library phải được represent bằng:

```text
identity
version
target
ABI
hash
location/provenance
```

nếu reproducible build yêu cầu.

---

# 110. Package integration

AXBUILD consumes AXPACKAGE lock graph:

```text
AXPACKAGE
   ↓
resolved dependency graph
   ↓
AXBUILD
```

---

# 111. Registry integration

AXREGISTRY có thể discover build services/tools nhưng local build phải không phụ thuộc registry availability.

---

# 112. Configuration integration

AXCONFIG cung cấp build profiles/environment settings.

Build snapshot phải immutable trong một build transaction.

---

# 113. Time integration

AXTIME cung cấp:

- build timing;
- deterministic virtual time;
- timestamps when explicitly required.

Build reproducibility không được phụ thuộc wall clock.

---

# 114. Random integration

AXRANDOM deterministic seed chỉ dùng khi compiler/build action cần randomness.

Secure randomness không được dùng làm build identity.

---

# 115. Storage integration

AXSTORAGE cung cấp:

- cache;
- staging;
- artifact persistence;
- atomic file operations.

---

# 116. Network integration

AXNETWORK chỉ được sử dụng khi:

- package fetch;
- remote cache;
- remote build;
- explicit external build operation.

Không tự động network.

---

# 117. Security integration

AXSECURITY controls:

- build sandbox;
- file access;
- network;
- process spawn;
- credentials;
- remote cache;
- package installation.

---

# 118. Audit integration

AXAUDIT có thể record:

- package installation;
- privileged build actions;
- security-sensitive configuration;
- trust decisions.

Normal compile events không bắt buộc audit.

---

# 119. Observability integration

AXOBSERVABILITY có thể measure:

```text
compile duration
cache hit rate
queue latency
link duration
memory usage
parallelism
```

---

# 120. Diagnostics integration

AXDIAGNOSTICS handles:

- compiler crash;
- linker crash;
- worker crash;
- build dump;
- failure reproduction.

---

# 121. Logging integration

AXLOGGING records structured build events.

Build logs không thay thế diagnostics.

---

# 122. Build provenance

AXBUILD emits:

```text
build_provenance {
    project
    source_revision
    dependency_lock
    toolchain
    target
    options
    outputs
}
```

---

# 123. Build attestation

Optional signed attestation:

```text
inputs
outputs
toolchain
policy
```

AXCRYPTO/AXTRUST performs cryptographic operations.

---

# 124. Build reproducibility verification

Command:

```text
axiom build --verify-reproducible
```

có thể execute equivalent rebuild and compare canonical output.

---

# 125. Build comparison

Output comparison:

```text
binary hash
section hash
symbol metadata
debug metadata
```

giúp xác định source of nondeterminism.

---

# 126. Distributed builds

AXBUILD có thể hỗ trợ:

```text
local scheduler
      ↓
remote workers
```

nhưng distributed build không phải requirement cho core compiler.

---

# 127. Remote worker

Worker request:

```text
inputs
toolchain identity
target
action
```

Worker returns:

```text
outputs
hashes
provenance
```

---

# 128. Worker trust

Remote worker output phải được verify.

Không tin worker chỉ vì worker thuộc repository/network.

---

# 129. Remote execution security

Remote build action capabilities phải explicit.

Secrets không được forward mặc định.

---

# 130. Build cancellation

Cancellation:

```text
BUILD_RUNNING
      ↓
CANCEL_REQUESTED
      ↓
workers stop
      ↓
BUILD_CANCELLED
```

Completed immutable artifacts vẫn valid.

---

# 131. Priority

Build requests có thể có priority:

```text
INTERACTIVE
NORMAL
BACKGROUND
CI
```

Priority không được phá dependency correctness.

---

# 132. Resource quotas

Build environment có thể giới hạn:

```text
CPU
RAM
disk
network
processes
```

AXSECURITY/AXCONFIG enforce.

---

# 133. Build daemon

Optional persistent daemon:

```text
AXBUILD daemon
```

Không cần thiết cho one-shot build.

---

# 134. CLI

Canonical commands:

```text
axiom init
axiom build
axiom rebuild
axiom clean
axiom test
axiom run
axiom plan
axiom graph
axiom cache
axiom target
axiom toolchain
axiom explain
```

---

# 135. Native API

Core:

```text
build_open()
build_close()

project_load()
project_validate()

workspace_open()
workspace_graph()

target_create()
target_validate()

build_plan()
build_execute()
build_cancel()

build_status()
build_diagnostics()

build_graph()
build_explain()

artifact_lookup()
artifact_store()

cache_lookup()
cache_store()
cache_gc()

rebuild_analyze()
reproducibility_verify()

toolchain_register()
toolchain_resolve()
```

---

# 136. Build request

```text
build_request {
    project
    target
    profile
    features
    lock_revision
    environment_snapshot
    reproducibility_mode
    cache_policy
    security_profile
}
```

---

# 137. Build result

```text
build_result {
    status
    outputs
    diagnostics
    graph_revision
    cache_statistics
    provenance
}
```

---

# 138. Build status

```text
CREATED
PLANNING
WAITING
RUNNING
VALIDATING
COMMITTING
SUCCEEDED
FAILED
CANCELLED
```

---

# 139. ABI

Native ABI:

```text
AXBUILD_ABI_1
```

ABI phải có:

- version;
- structure sizes;
- alignment;
- enum values;
- ownership rules;
- error model;
- thread safety;
- cancellation semantics.

---

# 140. Formal invariants

```text id="buildinv"
BUILD-INV-01
AXBUILD không phải runtime dependency của executable.

BUILD-INV-02
Project identity phải khác package/module/artifact identity.

BUILD-INV-03
Build graph phải deterministic.

BUILD-INV-04
Compilation dependency graph phải detect invalid cycles.

BUILD-INV-05
Source roots phải được xác định rõ ràng.

BUILD-INV-06
Undeclared source inputs không được silently ảnh hưởng strict build.

BUILD-INV-07
Build correctness không được phụ thuộc filesystem timestamps.

BUILD-INV-08
Build fingerprint phải bao gồm mọi semantic input cần thiết.

BUILD-INV-09
Compiler version/toolchain identity phải là build input.

BUILD-INV-10
Target và architecture phải là build inputs.

BUILD-INV-11
ABI changes phải có khả năng invalidate dependent artifacts.

BUILD-INV-12
Implementation-only changes không được buộc rebuild toàn graph khi interface contract không đổi.

BUILD-INV-13
Incremental invalidation phải giữ correctness.

BUILD-INV-14
Cache hit không được bypass artifact integrity validation.

BUILD-INV-15
Cache key phải collision-resistant theo AXCRYPTO policy.

BUILD-INV-16
Cached artifacts phải immutable theo content identity.

BUILD-INV-17
Failed build không được corrupt previous valid outputs.

BUILD-INV-18
Build output phải được staged trước activation khi atomicity yêu cầu.

BUILD-INV-19
Parallel scheduling không được thay đổi semantic build result.

BUILD-INV-20
Resource-aware scheduling không được vượt explicit build quotas.

BUILD-INV-21
Compiler invocation phải có explicit input/output contract.

BUILD-INV-22
Build environment phải có deterministic snapshot trong reproducible mode.

BUILD-INV-23
Hidden environment variables không được ảnh hưởng reproducible output.

BUILD-INV-24
Wall-clock time không được ảnh hưởng artifact identity trong reproducible mode.

BUILD-INV-25
Randomness không được ảnh hưởng reproducible output nếu seed không explicit.

BUILD-INV-26
Generated sources phải là explicit graph nodes.

BUILD-INV-27
Generated artifacts phải có deterministic dependency fingerprints.

BUILD-INV-28
Static và dynamic linking modes phải được biểu diễn rõ ràng.

BUILD-INV-29
Foreign dependencies phải được explicit declare.

BUILD-INV-30
Cross-target artifacts phải có target-specific identities.

BUILD-INV-31
SDK/sysroot changes phải có thể invalidate affected artifacts.

BUILD-INV-32
Remote cache output phải được integrity-check.

BUILD-INV-33
Remote execution không được mặc định receive secrets.

BUILD-INV-34
Build sandbox phải default-deny privileged resources khi policy yêu cầu.

BUILD-INV-35
Package resolution phải lấy dependency truth từ AXPACKAGE.

BUILD-INV-36
Security authorization phải lấy enforcement từ AXSECURITY.

BUILD-INV-37
Build diagnostics phải preserve actionable dependency/source context.

BUILD-INV-38
AXBUILD không được biến repository/network thành mandatory compiler dependency.

BUILD-INV-39
Reproducible verification phải có khả năng xác định output divergence.

BUILD-INV-40
AXBUILD chỉ orchestrate build; compiler, linker, package, storage, security và execution semantics thuộc subsystem tương ứng.
```

---

# 141. Definition of Done

`AXBUILD 5.0` được freeze khi có đầy đủ:

- project model;
- workspace;
- source graph;
- dependency graph;
- target model;
- toolchain model;
- build actions;
- deterministic graph;
- incremental compilation;
- interface hashing;
- ABI hashing;
- implementation hashing;
- build fingerprints;
- compiler cache;
- IR cache;
- object cache;
- link cache;
- cache hierarchy;
- remote cache;
- parallel scheduler;
- memory-aware scheduling;
- build sandbox;
- hermetic build;
- generated-source graph;
- static linking;
- dynamic linking;
- PE64;
- ELF;
- Mach-O;
- iOS;
- Android;
- WASM;
- cross compilation;
- resource builds;
- tests;
- PGO;
- LTO;
- release/size/speed profiles;
- build transactions;
- atomic activation;
- failure preservation;
- reproducible builds;
- deterministic archives;
- provenance;
- attestation;
- remote execution architecture;
- cancellation;
- quotas;
- IDE integration;
- language-server integration;
- package integration;
- compiler-server integration;
- security integration;
- storage integration;
- network integration;
- diagnostics;
- observability;
- logging;
- audit;
- native API;
- `AXBUILD_ABI_1`;
- 40 invariants.

**AXBUILD 5.0 → FROZEN.**

---

# BOOTSTRAP-769 — AXTOOLCHAIN

**Native Toolchain Description, Target ABI, SDK/Sysroot, Compiler/Linker/Assembler Coordination, Cross-Compilation, Platform Integration & Toolchain Reproducibility Runtime 5.0**

Sau `AXPACKAGE` định nghĩa **artifact được phân phối thế nào**, `AXBUILD` định nghĩa **graph được build thế nào**, bước kế tiếp phải đóng khung **toolchain mà AXBUILD thực sự sử dụng**:

```text
AXTOOLCHAIN
      │
      ├── target
      ├── architecture
      ├── ABI
      ├── object format
      ├── compiler
      ├── linker
      ├── assembler
      ├── sysroot
      ├── SDK
      ├── platform libraries
      ├── CPU features
      ├── debug/unwind format
      └── reproducibility identity
              │
              ▼
          AXBUILD
              │
              ▼
       AXCOMPILER / AXLINKER
              │
              ▼
      PE64 / ELF / Mach-O / WASM
```

`AXTOOLCHAIN` sẽ là lớp quan trọng để Axiom cuối cùng có thể **tự mô tả và tự bootstrap toàn bộ native compilation pipeline**, thay vì phụ thuộc vào một toolchain bên ngoài để duy trì compiler của chính Axiom.