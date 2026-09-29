Tiếp tục.

# BOOTSTRAP-042 — Module, Package, Dependency & Build System Audit & Freeze

Đây là lớp biến Axiom từ **ngôn ngữ + compiler** thành một hệ sinh thái có thể tự build dự án thực tế.

Nguyên tắc chính:

> **Build system phải là một phần native của Axiom toolchain, nhưng không được trở thành một “ngôn ngữ build” thứ hai.**

Và:

> **Một project Axiom phải có thể build mà không cần CMake, Make, Cargo, npm, Python hay compiler bên thứ ba.**

---

# 1. Phân biệt 4 khái niệm

Axiom phải tách:

```text
Module
Package
Workspace
Artifact
```

### Module

Đơn vị namespace/biên biên dịch logic.

### Package

Đơn vị phân phối dependency.

### Workspace

Tập hợp nhiều package cùng phát triển/build.

### Artifact

Kết quả build:

```text
exe
static library
shared library
object
wasm
gpu binary
metadata
debug info
...
```

---

# 2. Module

Ví dụ:

```text
src/
    main.ax
    math.ax
    io.ax
```

Có thể:

```axiom
import math
import io
```

---

# 3. Module path

Tên module nên dựa trên package/module hierarchy thay vì filesystem tuyệt đối.

Ví dụ:

```text
app
app.math
app.io
```

Filesystem chỉ là mặc định mapping.

Điều này cho phép compiler sau này thay đổi source layout mà không phá semantic identity.

---

# 4. File không nhất thiết = module

Một module có thể được chia:

```text
math/
    vector.ax
    matrix.ax
```

và compiler xem:

```text
math
```

là module namespace.

Nhưng **không nên ép một module chỉ được tồn tại trong một file**.

---

# 5. Module declaration

Có thể có:

```axiom
module math.vector
```

hoặc compiler suy ra từ package layout.

Tôi nghiêng về:

> **Filesystem convention mặc định + explicit declaration chỉ khi cần.**

Giảm boilerplate.

---

# 6. Import

Ví dụ:

```axiom
import math.vector.Vector
```

hoặc:

```axiom
import math.vector
```

Không nên có quá nhiều biến thể syntax.

---

# 7. Import không chạy code

`import` chỉ có semantic:

```text
name resolution
dependency declaration
```

Không phải runtime loading.

---

# 8. Export

Ví dụ:

```axiom
pub fn add(...)
```

`pub` điều khiển module visibility.

Không đồng nghĩa native symbol export.

Đã chốt từ FFI:

```text
pub
≠
@export
```

---

# 9. Visibility levels

Core v1 chỉ cần:

```text
private
pub
```

Có thể có:

```text
pub(package)
```

sau, nhưng không nên tạo 5–7 visibility levels ngay từ đầu.

---

# 10. Package boundary

Package là đơn vị:

```text
name
version
source
dependencies
build configuration
targets
features
```

---

# 11. Package manifest

Axiom cần manifest native, ví dụ:

```text
axiom.toml
```

hoặc một format native khác.

Không cần quyết định syntax file ngay ở Core semantic.

Semantic cần freeze trước:

```text
PackageManifest
```

có các trường chuẩn.

---

# 12. Package identity

Package identity:

```text
name
+
version
+
source identity
```

không chỉ:

```text
folder name
```

---

# 13. Versioning

Axiom nên dùng semantic version:

```text
MAJOR.MINOR.PATCH
```

nhưng package resolver không nên chỉ dựa vào string comparison.

Version constraint phải có semantic model.

---

# 14. Dependency graph

Ví dụ:

```text
App
├── Math
│   └── Numeric
├── HTTP
│   ├── TLS
│   └── Async
└── UI
```

Compiler/build system xây DAG.

Nếu:

```text
A → B
B → A
```

thì:

- source module cycle có thể có quy tắc riêng;
- package dependency cycle mặc định reject.

---

# 15. Module cycle ≠ package cycle

Đây là distinction quan trọng.

Có thể cho phép:

```text
module A ↔ module B
```

nếu compiler xử lý declaration/import graph.

Nhưng package cycle:

```text
Package A → Package B
Package B → Package A
```

nên reject ở dependency resolver.

---

# 16. Dependency phases

Dependency có thể thuộc:

```text
runtime
build
comptime
test
dev
```

Không nên link mọi dependency vào executable.

---

# 17. Runtime dependency

Ví dụ:

```text
HTTP library
```

có code chạy trong application.

---

# 18. Build dependency

Ví dụ:

```text
code generator
bindgen
resource compiler
```

chỉ cần trong build.

Không xuất hiện trong final binary.

---

# 19. Comptime dependency

Nếu:

```text
comptime
```

đọc/gọi một package:

```text
Package A
   ↓
comptime Package B
```

B trở thành build/comptime dependency.

Runtime không nhất thiết cần B.

---

# 20. Test dependency

Test-only package:

```text
test framework
benchmark
mock
```

không vào production artifact.

---

# 21. Dependency feature

Không nên biến feature system thành một ngôn ngữ cấu hình phức tạp.

Có thể:

```text
features = ["gpu", "http"]
```

và compiler dùng:

```axiom
@cfg(feature = "gpu")
```

---

# 22. Feature semantics

Feature là:

> compile-time configuration choice.

Không phải runtime boolean.

---

# 23. Target configuration

Ví dụ:

```text
target = windows-x86_64
target = linux-aarch64
target = wasm32
```

Package có thể conditional:

```axiom
@cfg(target = "windows")
```

---

# 24. `@cfg` và `comptime`

Đã freeze:

```text
@cfg
```

→ chọn code/declaration.

```text
comptime
```

→ tính toán giá trị/generate declaration.

Không nhập hai cơ chế làm một.

---

# 25. Cross compilation

Axiom compiler phải hỗ trợ:

```text
host ≠ target
```

Ví dụ:

```text
Windows x86-64
        ↓
Android ARM64
```

---

# 26. Host / target

Compiler luôn phân biệt:

```text
Host
Target
```

và comptime execution mặc định chạy trên:

```text
Host
```

trừ khi explicit target/device execution.

---

# 27. Build target triple

Target configuration cần:

```text
architecture
OS
ABI
environment
features
```

Ví dụ conceptually:

```text
x86_64-linux-gnu
aarch64-windows
aarch64-android
wasm32-wasi
```

---

# 28. Target không phải package feature

Không dùng:

```text
feature = "linux"
```

để thay thế target.

Target là compiler configuration.

---

# 29. Build profiles

Core build system nên có:

```text
debug
release
```

đủ cho MVP.

Sau có thể:

```text
dev
release
size
speed
sanitize
profile
```

nhưng không nên tạo quá nhiều preset.

---

# 30. Optimization profile

Compiler flags có thể điều khiển:

```text
optimization level
debug info
overflow checks
panic strategy
LTO
CPU features
```

---

# 31. Semantic vs optimization config

Ví dụ:

```text
-O3
```

không được thay đổi semantics.

Nếu một flag thay đổi semantics:

```text
panic=abort
overflow=wrap
```

nó phải là explicit profile semantic choice.

---

# 32. Reproducible builds

Đây phải là mục tiêu first-class.

Cùng:

```text
source
dependencies
compiler
target
configuration
comptime inputs
```

→ artifact có thể reproducibly được tạo lại.

---

# 33. Comptime dependency tracking

BOOTSTRAP-037 đã freeze:

Nếu comptime đọc:

```text
file
environment
tool output
network
```

thì input phải được đưa vào dependency graph/cache identity.

---

# 34. Build cache

Compiler cần cache:

```text
source
AST/HIR
typed HIR
generic instances
comptime results
MIR
object
GPU binary
```

nhưng cache là implementation detail.

---

# 35. Cache correctness

Không được:

```text
source unchanged
```

mà giả định artifact luôn valid.

Cache key cần bao gồm:

```text
compiler semantic version
target
features
configuration
dependencies
comptime inputs
relevant compiler settings
```

---

# 36. Incremental compilation

Ví dụ:

```text
A
├── B
├── C
└── D
```

thay B:

```text
B recompiles
A rechecks affected interfaces
C/D không rebuild nếu semantic dependency không thay đổi
```

---

# 37. Interface artifact

Để làm incremental compilation tốt, package/module nên có semantic metadata:

```text
type information
public declarations
trait information
ABI information
comptime dependency information
```

Không cần parse toàn bộ source dependency mỗi lần.

---

# 38. AI-friendly metadata

Đây là điểm Axiom có thể vượt các toolchain cũ.

Mỗi artifact có thể có machine-readable metadata:

```text
symbols
types
traits
generic constraints
ownership properties
ABI
dependencies
diagnostics
source mappings
```

AI agent có thể query thay vì đọc hàng nghìn file.

---

# 39. Dependency lock

Production build cần lock file.

Ví dụ:

```text
axiom.lock
```

Lock chứa resolved dependency versions + integrity hashes.

---

# 40. Source integrity

Dependency nên có:

```text
source identity
content hash
version
```

Không chỉ version.

Ví dụ:

```text
foo 1.2.3
hash = ...
```

---

# 41. Dependency sources

Có thể hỗ trợ:

```text
registry
git
local path
archive
system
```

---

# 42. Registry

Axiom ecosystem có thể có:

```text
Axiom Package Registry
```

nhưng compiler không phụ thuộc registry.

---

# 43. Offline build

Nếu dependencies đã cache:

```text
axiom build --offline
```

có thể build không network.

---

# 44. Network không phải compiler requirement

Compiler không được tự động:

```text
download dependency
```

trong semantic compilation.

Build tool/resolver mới làm dependency acquisition.

---

# 45. Security

Package source phải có:

```text
hash
```

và tùy registry:

```text
signature
```

---

# 46. Comptime security

Package comptime code có khả năng:

```text
ReadFilesystem
ExecuteTool
Network
```

phải chịu capability system của BOOTSTRAP-037.

Dependency acquisition không cấp quyền arbitrary cho comptime.

---

# 47. Build script

Tôi **không khuyến nghị** đưa một `build.ax` unrestricted script vào Core ngay.

Nó dễ biến thành:

```text
Makefile + Python + shell
```

và phá reproducibility.

---

# 48. Thay thế build script

Build metadata declarative:

```text
sources
dependencies
generated outputs
native libraries
link settings
resources
targets
```

Còn các hành động đặc biệt:

```text
comptime
build tool
```

có capability rõ ràng.

---

# 49. Native library dependency

Manifest có thể:

```text
system_lib = ["user32"]
```

hoặc:

```text
native_lib = "foo"
```

nhưng link behavior thuộc target/build layer.

---

# 50. Static vs shared

Package có thể yêu cầu:

```text
static
shared
either
```

nếu ABI contract hỗ trợ.

---

# 51. Artifact kinds

Build system phải hiểu:

```text
Executable
StaticLibrary
SharedLibrary
Object
WasmModule
GpuBinary
Metadata
```

---

# 52. Package type

Package có thể là:

```text
library
binary
workspace
```

hoặc package chứa nhiều targets.

---

# 53. Multiple binaries

Một package có:

```text
bin/
    server.ax
    client.ax
```

được.

Không cần tạo package riêng cho mỗi executable.

---

# 54. Library entry point

Library không có `main`.

Executable target xác định:

```text
main
```

hoặc freestanding entry:

```text
@entry
```

system-level.

---

# 55. `main`

Hosted application:

```axiom
fn main() -> Result<(), Error> {
    ...
}
```

Compiler/system layer tạo startup glue nếu target cần.

---

# 56. Freestanding

Có thể:

```axiom
@freestanding
@entry
fn _start() -> never {
    ...
}
```

Không cần runtime.

Syntax attribute cuối cùng sẽ thuộc system profile.

---

# 57. Runtime selection

Build system phân tích dependency/features để link:

```text
allocator
panic
thread
async executor
TLS
GPU runtime
```

chỉ khi cần.

---

# 58. No monolithic runtime

Ví dụ chương trình:

```text
hello world
```

không dùng:

```text
async
GPU
threads
reflection
```

thì binary không tự nhiên chứa chúng.

---

# 59. Runtime components as libraries

Conceptually:

```text
libaxiom_alloc
libaxiom_panic
libaxiom_thread
libaxiom_async
libaxiom_gpu
...
```

hoặc compiler có thể statically embed các phần cần thiết.

Tên artifact không cần freeze.

---

# 60. Dependency graph + runtime graph

Có hai graph:

```text
Source Dependency Graph
Runtime Link Graph
```

Không được nhầm.

Một package có thể là build dependency nhưng không runtime dependency.

---

# 61. Package initialization

Không nên có global constructor magic như C++.

Global initialization phải explicit/deterministic.

Static values có compile-time initialization nếu có thể.

Runtime initialization nếu cần phải có semantics rõ.

---

# 62. Global state

Module-level static:

```axiom
static CONFIG: Config = ...
```

có program lifetime.

Thread local:

```axiom
@tls
static ...
```

có thread lifetime.

---

# 63. Package namespace

Package name không nên tự động trở thành runtime symbol prefix.

Namespace:

```text
package/module identity
```

khác:

```text
ABI symbol mangling.
```

---

# 64. Dependency version conflict

Ví dụ:

```text
A → foo 1.x
B → foo 2.x
```

resolver có thể cho phép hai major versions nếu package identity khác.

Compiler phải giữ type identity tách biệt.

---

# 65. Type identity across versions

```text
foo@1::User
```

và:

```text
foo@2::User
```

là hai nominal types.

Không tự động compatible.

---

# 66. Dependency alias

Build metadata có thể:

```text
foo_v1
foo_v2
```

để resolve conflict.

Source-level alias chỉ là namespace convenience.

---

# 67. Public dependency

Nếu public API của package A chứa type của package B:

```text
A::fn() -> B::Type
```

B trở thành:

```text
public API dependency
```

và phải được ghi trong package metadata.

---

# 68. Private dependency

Nếu B chỉ dùng internally:

```text
A source
  ↓
B
```

B không nhất thiết expose ra API.

Điều này giúp dependency graph tối ưu.

---

# 69. ABI dependency

Nếu shared library A export symbol dùng ABI của B:

```text
B
```

phải là runtime dependency nếu cần.

---

# 70. Comptime generated API

Nếu package A generate code dựa trên B:

```text
B
```

có thể là build/comptime dependency ngay cả khi không runtime-linked.

---

# 71. Package build order

Resolver tạo DAG:

```text
dependency
    ↓
comptime/build
    ↓
source compile
    ↓
link
```

Các node độc lập có thể build song song.

---

# 72. Parallel compilation

Compiler có thể parallel:

```text
module A ─┐
module B ─┼→ HIR
module C ─┘
```

Comptime independent tasks cũng có thể parallel theo BOOTSTRAP-037.

---

# 73. Determinism

Parallel build không được thay đổi semantic output.

```text
build parallel
≈
build serial
```

về semantics.

---

# 74. Build graph fingerprint

Mỗi artifact có fingerprint dựa trên:

```text
source
dependency fingerprints
compiler semantic version
target
profile
features
comptime inputs
ABI
```

---

# 75. Artifact cache

Cache có thể:

```text
local
shared
remote
```

nhưng remote cache là optional.

---

# 76. Remote cache security

Remote artifact phải verify:

```text
fingerprint
target
compiler version
integrity
```

không tin filename.

---

# 77. Build environment

Reproducible build không nên phụ thuộc vô thức vào:

```text
current directory
PATH
HOME
environment variables
current time
randomness
```

Nếu comptime cần chúng:

```text
capability + dependency tracking
```

---

# 78. Environment variables

Build system có thể explicit:

```text
env("CC")
```

nhưng giá trị phải trở thành build input nếu ảnh hưởng output.

---

# 79. Compiler version

Compiler semantic version phải nằm trong cache identity.

Không:

```text
compiler 1.0
compiler 1.1
```

dùng cùng semantic cache nếu compiler behavior có thể khác.

---

# 80. Language version

Tách:

```text
language version
compiler version
ABI version
```

Ví dụ:

```text
Axiom language 1.2
compiler 1.8
Axiom ABI 3
```

---

# 81. Workspace

Workspace:

```text
workspace/
├── app/
├── engine/
├── tools/
└── libs/
```

cho phép share:

```text
lock
cache
target
configuration
```

---

# 82. Workspace không phải package

Một workspace có nhiều package.

Một package có thể tồn tại độc lập.

---

# 83. Monorepo

Workspace tự nhiên hỗ trợ monorepo.

Không cần package manager ngoài.

---

# 84. Source layout

Mặc định có thể:

```text
src/
tests/
examples/
assets/
```

nhưng đây là convention, không phải language semantics.

---

# 85. Test

Build system nhận:

```text
@test
```

từ BOOTSTRAP-036.

Test target không link vào production executable.

---

# 86. Benchmark

```text
@bench
```

tương tự.

Benchmark infrastructure có thể là package/tooling layer.

---

# 87. Examples

Examples có thể compile như executable targets nhưng không phải production targets.

---

# 88. Generated files

Comptime-generated outputs phải nằm trong compiler-managed generated area.

Không để:

```text
src/
```

bị sửa ngẫu nhiên rồi compiler không biết dependency.

---

# 89. Generated artifact identity

Generated source phụ thuộc vào:

```text
generator source
inputs
compiler version
comptime capabilities
```

---

# 90. Package publishing

Package publish artifact có thể chứa:

```text
source
manifest
lock metadata
semantic metadata
docs
debug/source optionally
```

Không nhất thiết publish build output cho mọi target.

---

# 91. Binary package

Có thể về sau phân phối:

```text
precompiled library
```

với ABI metadata.

Nhưng source package vẫn là ecosystem foundation.

---

# 92. Cross-platform package

Package có thể có:

```text
platform-specific source
platform-specific dependency
platform-specific ABI
```

thông qua target/config selection.

---

# 93. Native source

Một package có thể chứa:

```text
Axiom
C
assembly
GPU kernel
```

nhưng native source là system/build layer.

---

# 94. C source dependency

Axiom có thể build C source trong bootstrap/tooling ecosystem nếu muốn.

Nhưng:

> **đây không biến C compiler thành dependency của Axiom language.**

Một package C chỉ được build nếu target environment/toolchain cung cấp C compiler, hoặc Axiom sau này có C compiler riêng.

---

# 95. Long-term self-hosting

Cuối cùng:

```text
Axiom compiler
Axiom linker
Axiom assembler/encoder
Axiom package manager
Axiom build system
```

có thể được viết bằng Axiom.

---

# 96. Không cần build language riêng

Tôi không muốn:

```text
Axiom
+
AxiomBuildLanguage
+
AxiomPackageLanguage
+
AxiomConfigLanguage
```

Đây là complexity không cần thiết.

---

# 97. Declarative manifest + CLI

Mô hình nên là:

```text
axiom.toml
        +
axiom CLI
        +
compiler
        +
linker
```

Đủ mạnh.

---

# 98. CLI concept

Core commands:

```text
axiom new
axiom build
axiom run
axiom test
axiom bench
axiom check
axiom clean
axiom fetch
axiom update
axiom package
```

Không cần freeze toàn bộ CLI ngay.

---

# 99. `check`

```text
axiom check
```

nên chạy:

```text
parse
resolve
type check
ownership
capability
concurrency
comptime validation
```

nhưng không link executable.

---

# 100. Build model đã freeze

Tóm lại:

```text
Source
  ↓
Module Graph
  ↓
Package Graph
  ↓
Comptime / Build Dependencies
  ↓
Typed Compilation
  ↓
MIR
  ↓
Target Compilation
  ↓
Artifacts
  ↓
Link
```

---

# 101. Invariants — BOOTSTRAP-042

```text
ABUILD-20   Module identity is distinct from filesystem identity.
ABUILD-21   Package identity is distinct from module identity.
ABUILD-22   Workspace identity is distinct from package identity.
ABUILD-23   Artifact identity is distinct from source identity.
ABUILD-24   Import is a compile-time dependency operation.
ABUILD-25   Import does not imply runtime initialization.
ABUILD-26   Visibility is distinct from binary symbol export.
ABUILD-27   pub does not imply @export.
ABUILD-28   Package dependencies form an explicit dependency graph.
ABUILD-29   Package dependency cycles are rejected by default.
ABUILD-30   Module dependency cycles are a separate semantic concern.
ABUILD-31   Runtime dependencies are distinct from build dependencies.
ABUILD-32   Build dependencies are not automatically runtime dependencies.
ABUILD-33   Comptime dependencies are tracked explicitly.
ABUILD-34   Test dependencies are not production dependencies.
ABUILD-35   Feature configuration is compile-time configuration.
ABUILD-36   Target configuration is distinct from package features.
ABUILD-37   Host and target environments are distinct.
ABUILD-38   Cross compilation is a first-class build operation.
ABUILD-39   Build profiles may affect optimization and explicit semantic policy.
ABUILD-40   Optimization settings cannot silently change language semantics.
ABUILD-41   Reproducible builds track all semantic build inputs.
ABUILD-42   Comptime external inputs participate in dependency identity.
ABUILD-43   Compiler semantic version participates in artifact identity.
ABUILD-44   Language version is distinct from compiler version.
ABUILD-45   ABI version is distinct from language version.
ABUILD-46   Incremental compilation preserves semantic equivalence.
ABUILD-47   Cache validity is determined by semantic fingerprints.
ABUILD-48   Cache filenames are never sufficient for artifact identity.
ABUILD-49   Generated outputs are dependency-tracked.
ABUILD-50   Generated declarations are normally re-verified.
ABUILD-51   Dependency resolution is deterministic.
ABUILD-52   Parallel compilation does not change semantic results.
ABUILD-53   Offline builds are supported when dependencies are available locally.
ABUILD-54   Network access is not required by the compiler itself.
ABUILD-55   Dependency acquisition is separate from semantic compilation.
ABUILD-56   Dependency integrity may be verified by content hash.
ABUILD-57   Dependency version alone is insufficient for content identity.
ABUILD-58   Public API dependencies are explicitly represented.
ABUILD-59   Private dependencies need not become public API dependencies.
ABUILD-60   Generic instantiation metadata participates in incremental compilation.
ABUILD-61   Comptime results participate in incremental invalidation.
ABUILD-62   Target-specific code is selected before invalid code is compiled.
ABUILD-63   @cfg selects declarations/code; comptime computes values/generates declarations.
ABUILD-64   Package configuration cannot bypass language safety rules.
ABUILD-65   Build scripts cannot bypass comptime capability restrictions.
ABUILD-66   Native libraries require explicit linkage metadata.
ABUILD-67   Static and shared linking are distinct artifact operations.
ABUILD-68   Runtime components are linked only when required.
ABUILD-69   Axiom has no mandatory monolithic runtime.
ABUILD-70   Runtime-free programs remain valid Axiom programs.
ABUILD-71   Axiom does not require a C compiler for semantic compilation.
ABUILD-72   C toolchains may be optional interoperability dependencies.
ABUILD-73   Axiom native object formats are first-class targets.
ABUILD-74   Build metadata is machine-readable.
ABUILD-75   Build diagnostics are machine-readable.
ABUILD-76   AI tooling may consume compiler/package metadata without parsing source trees.
ABUILD-77   Package namespaces do not determine native symbol names.
ABUILD-78   Native symbol naming follows explicit ABI rules.
ABUILD-79   Multiple package versions may coexist when identity differs.
ABUILD-80   Nominal type identity does not silently cross package versions.
ABUILD-81   A workspace may contain multiple independent packages.
ABUILD-82   A package may contain multiple build targets.
ABUILD-83   Examples/tests/benchmarks need not enter production artifacts.
ABUILD-84   Generated source is compiler-managed when produced by comptime.
ABUILD-85   Build artifacts can be independently cached.
ABUILD-86   Remote caches are optional.
ABUILD-87   Remote artifacts require integrity verification.
ABUILD-88   Build environment inputs are explicit when semantically relevant.
ABUILD-89   Environment/time/random/network inputs can invalidate reproducibility.
ABUILD-90   Build configuration cannot alter ownership or capability semantics.
ABUILD-91   Package manager behavior is separate from language semantics.
ABUILD-92   Manifest syntax is separate from language syntax.
ABUILD-93   The build system does not constitute a second programming language.
ABUILD-94   Declarative configuration is preferred over unrestricted build scripting.
ABUILD-95   Build tools may be capability-restricted.
ABUILD-96   Compiler, linker, and package resolver may eventually be self-hosted in Axiom.
ABUILD-97   Self-hosting does not require C ABI internally.
ABUILD-98   Axiom ABI and C ABI remain distinct.
ABUILD-99   Target system libraries are platform dependencies, not compiler dependencies.
ABUILD-100  The complete build graph is reproducible and inspectable.
```

---

## Kiến trúc Axiom lúc này

Chúng ta đã có chuỗi khá hoàn chỉnh:

```text
                         AXIOM
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
      Types            Ownership         Capabilities
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                  Concurrency / Async
                           │
                      GPU / Device
                           │
                     FFI / Native
                           │
                  Module / Package
                           │
                    Build / Link
                           │
                ┌──────────┴──────────┐
                │                     │
             Native                WASM
          PE/ELF/Mach-O             ...
```

Điểm quan trọng là **mọi lớp mới đều tái sử dụng semantic nền**, thay vì tạo một cơ chế riêng.

### Chuỗi tiếp theo

Sau BOOTSTRAP-042, phần đáng làm tiếp theo là:

**BOOTSTRAP-043 — Compiler IR / MIR / LIR / Codegen Boundary Audit & Freeze**

Phần này sẽ là một trong những phần quan trọng nhất của toàn bộ Axiom, vì nó quyết định cách biến:

```text
Axiom source
    ↓
HIR
    ↓
Typed HIR
    ↓
MIR
    ↓
Verified MIR
    ↓
Semantic Optimization
    ↓
ABI MIR
    ↓
Axiom LIR
    ↓
Machine IR
    ↓
Machine Code
    ↓
Object
    ↓
Executable
```

thành compiler thực sự có thể **nhanh, nhỏ, self-host và không cần LLVM về lâu dài**.