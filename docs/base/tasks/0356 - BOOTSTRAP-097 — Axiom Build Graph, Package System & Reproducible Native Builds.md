# BOOTSTRAP-097 — Axiom Build Graph, Package System & Reproducible Native Builds

**Trạng thái: FROZEN**

Mục tiêu:

> **Build system phải nhanh, deterministic, incremental, cross-platform và đủ mạnh cho project rất lớn, nhưng không biến Axiom thành một hệ sinh thái build quá phức tạp.**

Axiom tách rõ:

```text
Language
Compiler
Package
Workspace
Build System
Linker
Runtime
```

Không để build system trở thành một phần bắt buộc của semantic Core.

---

# 1. Mô hình tổng thể

```text
Workspace
    │
    ├── Package A
    │     ├── Module
    │     ├── Dependencies
    │     └── Targets
    │
    ├── Package B
    │
    └── Package C
            │
            ▼
       Package Graph
            │
            ▼
       Build Graph
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
   Compile  Comptime  Link
      │       │       │
      └───────┼───────┘
              ▼
           Artifact
```

---

# 2. Package ≠ Module

Đã frozen từ BOOTSTRAP-042:

### Module

Đơn vị:

```text
namespace
name resolution
visibility
imports
```

### Package

Đơn vị:

```text
version
dependency
build configuration
artifact
distribution
```

Một package có thể chứa:

```text
src/
  lib.ax
  math.ax
  io.ax
  internal/
```

nhưng không có nghĩa mỗi file là một package.

---

# 3. Workspace

Workspace là tập hợp package cùng được phát triển/build:

```text
workspace/
    axiom.toml
    packages/
        compiler/
        std/
        linker/
        cli/
```

Workspace không tạo namespace runtime.

Nó chỉ là build/development boundary.

---

# 4. Package identity

Identity:

```text
PackageId =
    Name
    +
    Version
    +
    SourceIdentity
```

Ví dụ:

```text
math@1.4.0
```

khác:

```text
math@2.0.0
```

Hai version có thể cùng tồn tại trong dependency graph.

---

# 5. Không dùng filesystem path làm identity

Không:

```text
/path/a/math
```

là semantic identity.

Path chỉ là source location.

Điều này cho phép:

```text
cache relocation
vendoring
mirrors
archives
git checkout
```

mà không làm thay đổi package semantics.

---

# 6. Dependency graph

Ví dụ:

```text
app
├── ui
│   └── graphics
├── net
│   └── crypto
└── json
```

Compiler/build system xây:

```text
PackageGraph
```

và:

```text
BuildGraph
```

là hai graph khác nhau.

---

# 7. Package graph ≠ build graph

Package graph nói:

```text
A depends on B
```

Build graph nói:

```text
compile A
requires
metadata B
```

hoặc:

```text
link executable
requires
object A + object B
```

Một dependency có thể được dùng ở nhiều phase khác nhau.

---

# 8. Dependency phases

Axiom giữ:

```text
runtime
build
comptime
test/dev
```

Ví dụ:

```text
dependencies:
    json = ...
    
build-dependencies:
    codegen = ...

comptime-dependencies:
    schema = ...

dev-dependencies:
    test_framework = ...
```

---

# 9. Runtime dependency

```text
app
 → json
```

nếu app thực sự dùng JSON runtime.

Dependency này có thể dẫn đến:

```text
JSON code
```

trong executable.

---

# 10. Comptime dependency

Ví dụ:

```text
schema
```

chỉ được dùng:

```text
comptime
```

thì package đó không nhất thiết xuất hiện trong runtime binary.

Đây là điểm rất quan trọng.

```text
comptime dependency
≠
runtime dependency
```

---

# 11. Build dependency

Build tool có thể chạy trong quá trình build:

```text
schema compiler
resource generator
code generator
```

Nhưng kết quả runtime mới là:

```text
generated source
```

hoặc artifact.

Build tool không tự động được link vào executable.

---

# 12. Test dependency

Test package:

```text
test_framework
```

chỉ xuất hiện trong:

```text
axiom test
```

Không đi vào release artifact.

---

# 13. Dependency graph phải acyclic ở package level

Mặc định:

```text
A → B → C → A
```

→ lỗi.

Lý do:

- deterministic build;
- đơn giản hóa initialization;
- incremental compilation;
- package version resolution.

Module-level dependency có thể có những quan hệ phức tạp hơn trong cùng package, nhưng package graph không nên có cycle mặc định.

---

# 14. Feature

Feature là compile-time configuration:

```text
features:
    gpu
    unicode
    tls
```

Ví dụ:

```text
feature = "gpu"
```

có thể kích hoạt:

```text
@cfg(gpu)
```

Feature không phải runtime boolean.

---

# 15. Feature phải deterministic

Không được:

```text
feature enabled randomly
```

Build identity phải chứa feature set.

```text
BuildFingerprint =
    Source
    + Dependencies
    + Target
    + Features
    + Config
```

---

# 16. `@cfg` và `comptime`

Phân chia:

### `@cfg`

Chọn code:

```text
@cfg(target = "windows")
fn windows_impl() {}
```

### `comptime`

Tính toán:

```text
const BUFFER_SIZE = comptime compute_size();
```

Không biến `@cfg` thành một programming language.

---

# 17. Target triple

Axiom target phải có machine identity đầy đủ:

```text
architecture
vendor
OS
environment
ABI
features
```

Ví dụ khái niệm:

```text
x86_64-windows
x86_64-linux
aarch64-linux
aarch64-macos
wasm32-wasi
```

---

# 18. Host ≠ Target

Compiler chạy:

```text
host = x86_64-windows
```

nhưng build:

```text
target = aarch64-linux
```

là hoàn toàn hợp lệ.

Comptime/build tool mặc định chạy trên **host**.

Code runtime được compile cho **target**.

---

# 19. Host/Target split

```text
HOST
 ├── compiler
 ├── build tools
 └── comptime execution

TARGET
 ├── application
 ├── standard library
 └── runtime components
```

Đây là invariant cực kỳ quan trọng cho cross compilation.

---

# 20. Comptime cross-compilation

Ví dụ:

```text
const SIZE = comptime sizeof(TargetStruct);
```

`sizeof` phải dùng:

```text
target layout
```

chứ không dùng host layout.

Trong khi:

```text
comptime read_file()
```

chạy trên host filesystem.

Hai loại "environment" này phải tách.

---

# 21. Build environment

Build system tạo:

```text
BuildEnvironment
```

gồm:

```text
host
target
package
features
environment variables
tool capabilities
filesystem capabilities
```

Comptime chỉ được thấy capability mà package/build contract cấp.

---

# 22. Không để environment ngầm ảnh hưởng build

Ví dụ:

```text
PATH
HOME
USERNAME
current time
random number
```

không được tự động trở thành build input.

Nếu comptime truy cập:

```text
Environment
```

thì phải được khai báo/cấp capability.

---

# 23. Reproducible build

Mục tiêu:

```text
same source
+
same dependencies
+
same compiler semantics
+
same target
+
same config
+
same comptime inputs
```

→ cùng semantic artifact.

---

# 24. Content-addressed cache

Cache nên dùng:

```text
ContentHash
```

thay vì:

```text
filesystem path
```

Ví dụ:

```text
H(Source)
H(Dependencies)
H(Compiler)
H(Target)
H(Config)
```

→ ArtifactKey.

---

# 25. Artifact key

Khái niệm:

```text
ArtifactKey =
    SourceFingerprint
    + DependencyFingerprint
    + CompilerSemanticVersion
    + Target
    + Features
    + ComptimeInputs
    + BuildProfile
```

Nếu key giống:

```text
reuse artifact
```

---

# 26. Semantic fingerprint

Không hash mọi byte một cách mù quáng.

Compiler nên có:

```text
SemanticFingerprint
```

cho:

- public declarations;
- types;
- traits;
- ABI;
- repr;
- comptime dependencies;
- relevant attributes.

Nếu implementation private thay đổi nhưng public semantic contract không đổi, downstream rebuild có thể được giảm.

---

# 27. Interface artifact `.axmeta`

Package/module có thể phát hành:

```text
.axmeta
```

chứa:

```text
public declarations
types
traits
generic definitions
ABI summary
representation contracts
semantic fingerprint
dependencies
```

Consumer không cần compile lại toàn bộ source dependency.

---

# 28. Private implementation changes

Ví dụ:

```text
pub fn foo() -> i32
```

implementation thay đổi:

```text
return x + 1
```

thành:

```text
return x + 2
```

nhưng public type/ABI không đổi.

Compiler có thể giữ:

```text
downstream HIR/type analysis
```

và chỉ rebuild phần machine/codegen cần thiết.

---

# 29. Public API change

Nếu đổi:

```text
fn foo(i32)
```

thành:

```text
fn foo(f64)
```

thì:

```text
SemanticFingerprint
```

thay đổi.

Downstream callers phụ thuộc `foo` phải invalidate.

---

# 30. Dependency fingerprint graph

Ví dụ:

```text
A
└── B
    └── C
```

Nếu C private implementation thay đổi:

```text
C fingerprint public = unchanged
```

thì:

```text
B semantic cache
A semantic cache
```

có thể tiếp tục dùng.

Đây là nền tảng incremental compilation lớn.

---

# 31. Build phases

Axiom build graph có các node:

```text
ResolvePackage
Fetch/LoadDependency
Parse
Resolve
TypeCheck
GenericSpecialize
Comptime
Codegen
ObjectWrite
Archive
Link
PostLink
```

Mỗi node có input/output fingerprint.

---

# 32. Parallel build

Nếu:

```text
A → C
B → C
```

A và B độc lập:

```text
A ─┐
   ├── C
B ─┘
```

có thể compile song song.

Không cần programmer điều khiển thread.

---

# 33. Build graph deterministic

Parallel:

```text
A
B
C
```

hay serial:

```text
A
→ B
→ C
```

phải cho cùng semantic result.

---

# 34. No hidden global build state

Build system không được phụ thuộc vào:

```text
global cache mutation
random temp paths
machine-specific state
```

theo cách làm thay đổi artifact.

---

# 35. Local cache

Mặc định:

```text
~/.axiom/cache
```

hoặc platform-equivalent.

Cache có thể xóa bất kỳ lúc nào.

Build system phải vẫn build đúng từ source.

---

# 36. Remote cache

Về sau có thể:

```text
remote artifact cache
```

Nhưng:

> **Remote cache là optimization, không phải semantic dependency.**

Không có network vẫn build được nếu dependencies đã có local.

---

# 37. Offline mode

```text
axiom build --offline
```

không được truy cập network.

Nếu dependency chưa có:

```text
diagnostic
```

không silently fetch.

---

# 38. Lock file

```text
axiom.lock
```

khóa:

```text
package
version
source
content hash
dependency resolution
```

Mục tiêu:

```text
same lock
→ same dependency graph
```

---

# 39. Source integrity

Dependency nên có:

```text
content hash
```

Ví dụ:

```text
sha256(...)
```

hoặc hash algorithm tương đương được Axiom chọn.

Lock file xác nhận content.

---

# 40. Registry không phải compiler

Package registry:

```text
distribution mechanism
```

không phải:

```text
language semantics
```

Compiler phải build từ:

```text
local source
cached source
vendored source
```

mà không cần registry server.

---

# 41. Git dependency

Có thể:

```text
git source
```

nhưng package identity vẫn phải cuối cùng resolve thành content identity/version contract.

Không để:

```text
git branch moving target
```

làm reproducible build bị phá.

Lock file phải pin commit/content.

---

# 42. Local dependency

Workspace:

```text
package A
package B
```

có thể dependency trực tiếp.

Build system không cần publish package để test A dùng B.

---

# 43. Vendoring

Có thể đưa dependency vào:

```text
vendor/
```

và build offline.

Vendor source vẫn giữ:

```text
package identity
content hash
```

---

# 44. Native library dependency

Axiom phải hỗ trợ:

```text
static library
shared library
object files
system libraries
frameworks
```

nhưng dependency phải explicit.

Ví dụ khái niệm:

```text
system-library:
    z
```

không có nghĩa compiler tự động link mọi thứ.

---

# 45. Không phụ thuộc C compiler

Một package native:

```text
libfoo.a
```

có thể link trực tiếp.

Axiom compiler không cần:

```text
gcc
clang
cl.exe
```

để tạo executable cuối cùng.

Điều này phù hợp mục tiêu self-host.

---

# 46. Bootstrap exception

Trong giai đoạn bootstrap:

```text
LLVM
LLD
system linker
```

có thể được sử dụng.

Nhưng:

> bootstrap dependency ≠ permanent language dependency.

Đã frozen từ BOOTSTRAP-060.

---

# 47. Static vs shared

Build system phân biệt:

```text
static
shared
```

### Static

Có thể dead-strip mạnh.

### Shared

Phải bảo toàn exported ABI.

---

# 48. Native target configuration

Target có:

```text
TargetSpec
```

gồm:

```text
pointer width
endianness
alignment
ABI
object format
calling convention
TLS model
atomic capabilities
SIMD features
OS
```

Compiler backend dùng TargetSpec.

Build system chỉ chọn target.

---

# 49. Cross compilation

Ví dụ:

```text
axiom build --target=aarch64-linux
```

Build graph:

```text
host compiler
      │
      ├── comptime host
      │
      └── target codegen
              ↓
          ARM64 object
              ↓
          ELF linker
```

---

# 50. Target linker

Axiom production compiler cuối cùng sẽ có:

```text
ELF linker
PE/COFF linker
Mach-O linker
WASM linker
```

nhưng build system chỉ gọi abstraction:

```text
Link(target, objects, libraries)
```

---

# 51. Build profile

Frozen concept:

```text
debug
release
size
speed
tiny
```

Build profile là input của fingerprint.

---

# 52. Debug artifact

Debug build có thể sinh:

```text
program
program.debug
```

hoặc platform-native debug format.

Debug metadata không cần nằm trong production binary.

---

# 53. Separate debug symbols

Build system hỗ trợ:

```text
--debug=external
```

để:

```text
binary
+
debug symbols
```

độc lập.

---

# 54. Test build

`axiom test` tạo test executable riêng.

Test dependencies:

```text
dev/test phase
```

không xâm nhập production artifact.

---

# 55. Benchmark build

`axiom bench` có thể chọn:

```text
release
PGO instrumentation
CPU feature
```

nhưng benchmark harness không trở thành runtime dependency của application.

---

# 56. Generated source

Comptime/build generation:

```text
schema
   ↓
comptime
   ↓
generated declarations
   ↓
normal HIR
```

Generated code phải quay lại pipeline bình thường:

```text
parse
resolve
typecheck
verify
codegen
```

Không có đường tắt.

---

# 57. Generated files fingerprint

Nếu:

```text
input schema
```

không đổi:

```text
generated source
```

không cần regenerate.

Build graph biết:

```text
Generator
+ Inputs
+ Tool version
```

---

# 58. Build tool capabilities

Build/comptime tool có thể yêu cầu:

```text
ReadSource
ReadMetadata
ReadFilesystem
WriteGenerated
ExecuteTool
Environment
Network
Time
Random
```

Đã frozen ở comptime architecture.

Build system cấp capability tương ứng.

---

# 59. Build sandbox

Default:

```text
no arbitrary network
no arbitrary environment
no arbitrary filesystem mutation
```

Nếu project cần:

```text
build capability
```

phải khai báo.

---

# 60. Hermetic build

Mục tiêu:

```text
source
+
declared dependencies
+
declared environment
```

là đủ để build.

Không dựa vào:

```text
random machine state
```

---

# 61. System dependencies

Không phải mọi build đều có thể hermetic tuyệt đối.

Ví dụ:

```text
Windows SDK
Linux kernel headers
Apple SDK
GPU driver SDK
```

được coi là:

```text
declared system dependency
```

Target environment fingerprint phải ghi nhận version/identity phù hợp.

---

# 62. SDK identity

Ví dụ iOS:

```text
Apple SDK version
target platform
architecture
ABI
```

là build input.

Không thể cache artifact iOS bất chấp SDK contract nếu ABI thay đổi.

---

# 63. Build environment manifest

Compiler có thể tạo:

```text
build-info
```

gồm:

```text
compiler version
target
SDK
features
dependencies
profile
comptime inputs
```

phục vụ reproducibility/debug.

---

# 64. Package manager không tự động sửa source

Nếu dependency conflict:

```text
A requires foo 1.x
B requires foo 2.x
```

build system phải resolve graph hoặc báo lỗi.

Không âm thầm sửa source/API.

---

# 65. Multiple versions

Cho phép:

```text
foo@1.x
foo@2.x
```

cùng dependency graph nếu semantics/package identity khác.

Nominal types từ hai versions không tự động tương thích.

---

# 66. Package aliases

Có thể:

```text
import foo1.Type
import foo2.Type
```

để phân biệt.

---

# 67. Feature unification

Nếu hai dependencies cùng package:

```text
foo
```

một bên yêu cầu:

```text
gpu
```

một bên không:

graph resolver phải có policy deterministic.

Không được tùy tiện tạo hai bản runtime package nếu package semantics không cho phép.

---

# 68. Feature conflict

Nếu:

```text
feature=A
feature=B
```

không tương thích:

```text
diagnostic
```

không silent resolution.

---

# 69. Build graph node identity

Mỗi node:

```text
BuildNodeId
```

được xác định bởi:

```text
phase
package
module
target
inputs
configuration
```

Có thể cache từng node.

---

# 70. Fine-grained incremental build

Thay vì:

```text
package changed
→ rebuild entire package
```

compiler có thể:

```text
source file
→ module
→ declaration
→ generic instance
→ object
```

invalidate chính xác hơn.

---

# 71. Tuy nhiên không over-fragment build graph

Nếu tạo hàng triệu node nhỏ:

```text
scheduler overhead
cache metadata
memory
```

có thể lớn.

Do đó compiler có cost model:

```text
fine-grained when beneficial
coarse-grained when cheap
```

---

# 72. Build batching

Các module nhỏ có thể compile batch:

```text
module A
module B
module C
```

trong cùng worker.

Giảm overhead process/task.

---

# 73. Compiler daemon

Axiom có thể có:

```text
axiom daemon
```

giữ:

```text
CompilerDB
TypeDB
PackageDB
cache
```

trong memory.

Lợi ích:

- IDE;
- incremental build;
- repeated commands;
- fast diagnostics.

Nhưng daemon không phải semantic requirement.

---

# 74. CLI không daemon vẫn phải hoạt động

```text
axiom build
```

phải chạy standalone.

Daemon chỉ là performance optimization.

---

# 75. IDE integration

CompilerDB/query architecture cho phép:

```text
go-to-definition
type-at-position
find-references
diagnostics
completion
rename
```

mà không cần IDE tự implement compiler semantics.

---

# 76. AI integration

Machine-readable output:

```text
--diagnostics=json
--build-graph=json
--explain-cache
--explain-opt
--explain-size
```

cho phép AI agent hiểu:

```text
why rebuild happened
why code exists
why optimization failed
which dependency caused invalidation
```

Đây là lợi thế lớn của Axiom.

---

# 77. Build failure taxonomy

Không trả về:

```text
Build failed
```

một cách chung chung.

Phân loại:

```text
PACKAGE_RESOLUTION
SOURCE_ERROR
TYPE_ERROR
TRAIT_ERROR
OWNERSHIP_ERROR
CAPABILITY_ERROR
COMPTIME_ERROR
CODEGEN_ERROR
ABI_ERROR
LINK_ERROR
TARGET_ERROR
ENVIRONMENT_ERROR
```

với stable diagnostic code.

---

# 78. Dependency resolution không phải compile

Nếu:

```text
foo@1.2
```

không tìm thấy:

```text
PACKAGE_NOT_FOUND
```

không phải:

```text
COMPILER_ERROR
```

Giúp AI agent tự xử lý chính xác.

---

# 79. Build cancellation

Build graph hỗ trợ:

```text
cancel
```

Các node đang chạy có thể dừng khi an toàn.

Cache artifact hoàn chỉnh vẫn giữ.

Không làm hỏng cache.

---

# 80. Build failure không corrupt cache

Artifact chỉ được commit vào cache sau:

```text
successful completion
+
integrity verification
```

Partial artifact không được coi là valid cache entry.

---

# 81. Atomic cache commit

```text
temporary artifact
      ↓
verify
      ↓
atomic rename/commit
```

Tránh cache corruption khi:

- crash;
- mất điện;
- process kill.

---

# 82. Reproducible timestamps

Artifact không nên embed:

```text
current wall-clock time
```

trừ khi explicit.

Build metadata dùng:

```text
source-controlled timestamp
```

hoặc deterministic epoch policy.

---

# 83. Randomness

Nếu compiler cần randomization cho hash/security:

nó không được làm output binary khác nhau nếu reproducibility yêu cầu.

Có thể dùng:

```text
deterministic seed
```

cho build-critical algorithms.

---

# 84. Parallel scheduling

Scheduler có thể:

```text
priority:
hot dependency
critical path
large package
cache miss
```

nhưng scheduling order không được ảnh hưởng artifact.

---

# 85. Critical path optimization

Build graph có thể tính:

```text
critical path
```

và ưu tiên node ảnh hưởng trực tiếp tới final link.

Điều này quan trọng hơn chỉ đơn giản:

```text
spawn maximum threads
```

---

# 86. Memory-aware scheduling

Compiler task lớn:

```text
huge generic package
```

không nên chạy đồng thời quá nhiều bản nếu RAM thấp.

Scheduler có thể giới hạn:

```text
memory budget
CPU budget
```

mà semantic result không đổi.

---

# 87. Local machine adaptation

Build system có thể tự điều chỉnh:

```text
parallelism
cache
memory pressure
```

nhưng không được thay đổi language semantics.

---

# 88. Build artifact hierarchy

Axiom phân biệt:

```text
Source
Metadata
IR Cache
Object
Static Library
Shared Library
Executable
Debug Symbols
GPU Binary
WASM Module
```

Mỗi artifact có fingerprint riêng.

---

# 89. Package output

Một package có thể tạo:

```text
library
executable
static library
shared library
GPU artifact
metadata
```

Không phải package nào cũng phải tạo executable.

---

# 90. Multi-target package

Một package có thể build:

```text
Windows
Linux
macOS
Android
iOS
WASM
```

từ cùng source.

`@cfg` + platform modules chọn implementation.

---

# 91. Platform abstraction

Standard library:

```text
std.fs
```

có API chung.

System implementation:

```text
sys.windows.fs
sys.linux.fs
sys.macos.fs
```

Build system chọn target implementation.

---

# 92. Không fork toàn bộ standard library

Platform differences nên được cô lập.

Không tạo:

```text
std-windows
std-linux
```

như hai ngôn ngữ khác nhau.

---

# 93. Native SDK integration

System package có thể khai báo:

```text
requires SDK
```

với:

```text
version constraint
headers/metadata
libraries
frameworks
link flags
```

Axiom không tự giả định tất cả hệ thống đều có libc.

---

# 94. C library integration

Có thể:

```text
extern "C"
```

và link:

```text
libc
```

nhưng đây là explicit dependency.

Axiom executable freestanding không cần libc.

---

# 95. Package build scripts

Axiom **không đưa một build scripting language unrestricted vào Core**.

Thay vào đó:

```text
declarative manifest
+
comptime/build capability
```

Build logic phức tạp có thể dần được viết bằng Axiom với sandbox/capability.

---

# 96. Không có `build.ax` tự do mặc định

Không:

```text
build.ax
→ execute arbitrary OS commands
```

mà không có declaration.

Điều này tránh build system trở thành:

```text
arbitrary code execution
```

mặc định.

---

# 97. Tool execution

Nếu build thực sự cần tool:

```text
ExecuteTool
```

phải được cấp.

Ví dụ:

```text
shader compiler
resource compiler
IDL generator
```

Build graph phải biết tool version/input/output.

---

# 98. Tool fingerprint

Một generated artifact phụ thuộc:

```text
Tool identity
Tool version
Tool arguments
Input files
Target
```

Nếu tool đổi:

```text
invalidate
```

---

# 99. Build outputs không được implicit

Generator phải khai báo output:

```text
generated/foo.ax
generated/bar.ax
```

Build system có thể theo dõi dependency chính xác.

---

# 100. Frozen invariants

### Package

**ABUILD2-20 — Package Identity Is Independent Of Filesystem Path**

**ABUILD2-21 — Package Identity Includes Version And Source Identity**

**ABUILD2-22 — Package Graph And Build Graph Are Distinct**

**ABUILD2-23 — Package Dependencies Are Phase-Qualified**

**ABUILD2-24 — Runtime Dependencies Are Distinct From Comptime Dependencies**

**ABUILD2-25 — Build Dependencies Are Distinct From Runtime Dependencies**

**ABUILD2-26 — Test Dependencies Are Not Production Dependencies**

---

### Resolution

**ABUILD2-27 — Package Resolution Is Deterministic**

**ABUILD2-28 — Package Cycles Are Rejected By Default**

**ABUILD2-29 — Multiple Package Versions May Coexist**

**ABUILD2-30 — Nominal Types From Different Package Versions Are Distinct**

**ABUILD2-31 — Lock Files Pin Dependency Content**

**ABUILD2-32 — Dependency Integrity Is Content-Based**

---

### Features

**ABUILD2-33 — Features Are Compile-Time Configuration**

**ABUILD2-34 — Feature Configuration Is Part Of Build Identity**

**ABUILD2-35 — Feature Resolution Is Deterministic**

**ABUILD2-36 — Feature Conflicts Produce Diagnostics**

---

### Cross compilation

**ABUILD2-37 — Host And Target Are Distinct**

**ABUILD2-38 — Comptime Executes In The Host Environment**

**ABUILD2-39 — Target Layout Is Used For Target-Specific Comptime Semantics**

**ABUILD2-40 — Cross Compilation Is A First-Class Build Mode**

**ABUILD2-41 — Target Identity Includes ABI-Relevant Properties**

---

### Incremental build

**ABUILD2-42 — Build Nodes Have Stable Input Identity**

**ABUILD2-43 — Build Artifacts Are Content-Addressable**

**ABUILD2-44 — Semantic Fingerprints Drive Incremental Invalidation**

**ABUILD2-45 — Private Implementation Changes Need Not Invalidate Unaffected Consumers**

**ABUILD2-46 — Public Semantic Changes Invalidate Dependent Consumers**

**ABUILD2-47 — Cache Entries Must Be Validated Before Reuse**

---

### Reproducibility

**ABUILD2-48 — Build Inputs Must Be Explicitly Identifiable**

**ABUILD2-49 — Undeclared Environment State Must Not Affect Reproducible Builds**

**ABUILD2-50 — Comptime External Inputs Are Build Dependencies**

**ABUILD2-51 — Tool Versions Are Build Inputs When Tool Output Is Used**

**ABUILD2-52 — Parallel Build Must Be Semantically Equivalent To Serial Build**

**ABUILD2-53 — Build Output Must Not Depend On Unspecified Wall-Clock Time**

---

### Cache

**ABUILD2-54 — Local Cache Is An Optimization, Not A Semantic Requirement**

**ABUILD2-55 — Remote Cache Is An Optimization, Not A Semantic Requirement**

**ABUILD2-56 — Offline Build Must Never Silently Access Network**

**ABUILD2-57 — Failed Builds Must Not Produce Valid Cache Entries**

**ABUILD2-58 — Cache Commit Must Be Atomic**

---

### Build tools

**ABUILD2-59 — Build Tools Require Explicit Capabilities**

**ABUILD2-60 — Arbitrary Tool Execution Is Not Implicit**

**ABUILD2-61 — Generated Outputs Must Be Declared**

**ABUILD2-62 — Generated Code Re-enters Normal Compiler Verification**

---

### Native dependencies

**ABUILD2-63 — Native Libraries Are Explicit Dependencies**

**ABUILD2-64 — Static And Shared Dependencies Are Distinct**

**ABUILD2-65 — System SDKs Are Explicit Target Inputs**

**ABUILD2-66 — Axiom Does Not Require A C Compiler For Final Native Linking**

---

### Architecture

**ABUILD2-67 — Build System Does Not Define Language Semantics**

**ABUILD2-68 — Compiler Can Operate Without A Build Daemon**

**ABUILD2-69 — Build Daemons Are Performance Optimizations**

**ABUILD2-70 — Build Scheduling Must Not Affect Semantics**

**ABUILD2-71 — Build Graph Granularity Is An Optimization Decision**

**ABUILD2-72 — Build System Must Remain Usable Without A Global Runtime**

---

# 101. Kiến trúc build cuối cùng

Axiom hiện có:

```text
                 Workspace
                     │
                     ▼
               Package Graph
                     │
                     ▼
                Build Graph
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Package       Comptime     Build Tool
     Compile       Evaluation   Execution
        │            │            │
        └────────────┼────────────┘
                     ▼
               Semantic Cache
                     │
                     ▼
               Generic Instances
                     │
                     ▼
                  Objects
                     │
                     ▼
                Link Graph
                     │
                     ▼
              Whole Program Opt
                     │
                     ▼
                Final Binary
```

Điểm rất quan trọng là **cache nằm xuyên suốt pipeline**, không chỉ cache object cuối cùng.

---

# 102. Axiom build architecture hiện có một tính chất rất mạnh

Một project lớn có thể đi theo:

```text
Source
  ↓
Semantic fingerprint
  ↓
Cache hit?
 ├── YES → reuse
 └── NO
      ↓
   compile
      ↓
   cache
```

Ví dụ người dùng sửa một dòng trong:

```text
gui/button.ax
```

thì không nhất thiết:

```text
compiler
stdlib
network
graphics
app
```

đều phải rebuild.

Build graph + semantic fingerprint xác định chính xác phạm vi invalidation.

---

# 103. Điều này cũng giải quyết một vấn đề của AI agent

AI agent làm project Axiom thường xuyên có thể:

```text
edit file
→ axiom check
→ axiom test
→ axiom build
```

nhưng compiler daemon/cache sẽ giữ:

```text
CompilerDB
TypeDB
GenericDB
semantic cache
object cache
```

nên vòng lặp:

```text
AI edit
→ compile
→ inspect diagnostic
→ fix
```

có thể rất nhanh.

Đây sẽ là một thành phần quan trọng của **Axiom AI-first developer experience** nhưng không đưa AI vào semantic compiler.

---

# 104. Bước tiếp theo

Sau 097, phần **package/build/cache/reproducibility** đã đủ nền tảng. Bước hợp lý tiếp theo là quay xuống một vấn đề cực kỳ quan trọng mà Axiom vẫn chưa khóa hoàn toàn:

# **BOOTSTRAP-098 — Axiom Module System, Name Resolution, Visibility & Import Architecture**

Sẽ chốt sâu:

```text
module
namespace
import
export
pub
private
package visibility
re-export
alias
name collision
cyclic module dependencies
initialization
qualified names
method lookup
trait lookup
extension methods
generic lookup
prelude
source/file mapping
```

Đặc biệt phải giải quyết sao cho:

> **Axiom có thể có hàng triệu symbol trong một project lớn nhưng name resolution vẫn deterministic, nhanh, incremental và không tạo ra hệ thống import rối rắm như một số ngôn ngữ hiện đại.**