# BOOTSTRAP-113 — Build System, Package Graph & Artifact Model

**Trạng thái: FROZEN / COMPLETED**

Đây là tầng nối giữa **compiler** và **project thực tế**.

Mục tiêu không phải tạo một package manager quá phức tạp, mà là một hệ thống:

> **deterministic + incremental + cache-friendly + cross-platform + offline-capable + AI-readable.**

Kiến trúc tổng thể:

```text
Workspace
   ↓
Package Graph
   ↓
Dependency Resolution
   ↓
Build Graph
   ↓
CompilerDB / Cache
   ↓
Object / Library Artifacts
   ↓
Link Graph
   ↓
Executable
```

---

# 1. Phân biệt 6 khái niệm

Axiom phải giữ rõ:

```text
Module
Package
Workspace
Dependency
Artifact
Build
```

| Khái niệm | Ý nghĩa |
|---|---|
| Module | đơn vị source/resolution |
| Package | đơn vị phân phối/biên dịch |
| Workspace | tập package cùng phát triển |
| Dependency | quan hệ phụ thuộc |
| Artifact | sản phẩm build |
| Build | quá trình biến source/dependency thành artifact |

Không để package = module.

---

# 2. Package identity

Package không được định danh chỉ bằng tên.

```text
PackageId =
    Name
    + Version
    + SourceIdentity
```

Ví dụ:

```text
graphics
1.4.2
registry://...
```

khác với:

```text
graphics
1.4.2
git://...
```

nếu source identity khác.

Điều này rất quan trọng cho reproducible build.

---

# 3. Package manifest

Mỗi package có manifest:

```text
package.ax
```

Logical structure:

```text
package
├── name
├── version
├── edition
├── targets
├── dependencies
├── features
├── profiles
├── exports
└── build
```

Không nên biến manifest thành một ngôn ngữ lập trình thứ hai.

---

# 4. Dependency declaration

Ví dụ conceptual:

```text
dependencies:
    math = "1.4"
    graphics = "2.1"
```

Có thể chỉ định source:

```text
registry
git
path
local
system
binary
```

Nhưng dependency semantics vẫn thống nhất.

---

# 5. Dependency source

Axiom hỗ trợ:

```text
Registry
Git
Local path
Archive
Vendored
System
Binary artifact
```

Không bắt buộc registry trung tâm.

Một project có thể build hoàn toàn offline:

```text
project/
├── src/
├── deps/
└── cache/
```

---

# 6. Dependency graph

Ví dụ:

```text
App
├── Graphics
│   ├── Math
│   └── Image
└── Network
    └── TLS
```

Build system biến thành DAG:

```text
Math ─────┐
          ↓
Image ─→ Graphics ─┐
                   ↓
TLS ───→ Network ─→ App
```

Cycle:

```text
A → B → C → A
```

phải bị reject đối với package dependency.

---

# 7. Module cycle khác package cycle

Package:

```text
A → B → A
```

→ lỗi.

Nhưng module:

```text
module A imports B
module B imports A
```

có thể được hỗ trợ nếu declaration resolution cho phép.

Điều này đã phù hợp với `AMOD` trước đó.

---

# 8. Dependency scopes

Không phải dependency nào cũng giống nhau.

Axiom nên có:

```text
normal
build
test
bench
dev
system
```

Ví dụ:

```text
compiler dependency
```

không tự động xuất hiện trong runtime artifact.

---

# 9. Target-specific dependency

Ví dụ:

```text
Windows → windows-system
Linux   → linux-system
macOS   → mac-system
```

Graph:

```text
App
 ├── common
 └── @cfg(target=windows)
       └── windows-system
```

`@cfg` phải được áp dụng **trước dependency resolution cuối cùng**.

---

# 10. Feature system

Axiom cần feature nhưng phải tránh feature explosion.

Ví dụ:

```text
features:
    gpu
    tls
    async
```

Feature chỉ nên bật/tắt **build graph**, không thay đổi semantics của cùng một source theo cách không xác định.

Ví dụ:

```text
feature = gpu
```

có thể thêm module:

```text
gpu_backend
```

nhưng không nên làm:

```text
fn foo() 
```

có semantics hoàn toàn khác chỉ vì feature.

---

# 11. Profiles

Build profiles chuẩn:

```text
dev
release
size
debug
sanitize
bench
```

Có thể:

```text
release
    optimization = high

size
    optimization = size
    lto = true
    strip = true
```

Compiler optimization semantics vẫn phải giữ nguyên.

---

# 12. Optimization profile không phải language mode

Ví dụ:

```text
-O0
-O2
-O3
-size
```

không được thay đổi:

```text
ownership
Drop
Send
Share
atomic semantics
overflow semantics
```

Optimization chỉ thay đổi implementation.

---

# 13. Edition

Axiom nên có concept:

```text
edition
```

để language evolution không phá project cũ.

Ví dụ:

```text
edition = 0.1
```

sau này:

```text
edition = 0.2
```

Edition migration phải có tooling.

Không nên dùng version package để biểu diễn language edition.

---

# 14. Lockfile

Project cần lock dependency graph chính xác:

```text
axiom.lock
```

Nó ghi:

```text
Package
Version
Source
ContentHash
Dependencies
```

Mục tiêu:

```text
same lockfile
+
same compiler
+
same target
+
same build configuration
```

→ cùng semantic dependency graph.

---

# 15. Content-addressed dependency

Một package có thể định danh bằng:

```text
ContentHash
```

Ví dụ:

```text
SHA-256(source/package contents)
```

Điều này cho phép:

```text
cache/
  abcd.../
  91ef.../
  73aa.../
```

Không phụ thuộc tên file.

---

# 16. Artifact identity

Artifact:

```text
ArtifactId
```

nên dựa trên:

```text
SourceFingerprint
DependencyFingerprint
CompilerSemanticVersion
Target
ABI
Profile
Features
ComptimeInputs
CodegenConfiguration
```

Đây kế thừa trực tiếp `SemanticFingerprint` đã thiết kế.

---

# 17. Artifact categories

Chuẩn hóa:

```text
.axmeta
.axo
.axlib
.axexe
.axdylib
.axwasm
```

Tên extension cuối cùng có thể thay đổi, nhưng semantic categories phải tồn tại.

### Metadata

```text
.axmeta
```

### Object

```text
.axo
```

### Static library

```text
.axlib
```

### Executable

platform-native format:

```text
.exe
ELF
Mach-O
.wasm
```

---

# 18. `.axmeta`

Đây là artifact đặc biệt quan trọng cho Axiom và AI.

Nó chứa:

```text
public declarations
types
traits
generic signatures
ABI contracts
attributes
layout contracts
visibility
compiler metadata
dependency identity
```

Không cần source code đầy đủ.

Compiler package B có thể compile:

```text
import A
```

bằng:

```text
A.axmeta
```

mà không cần parse toàn bộ source A.

---

# 19. AI-readable metadata

`.axmeta` nên có machine-readable schema:

```text
DeclarationId
TypeId
TraitId
FunctionId
GenericInstanceId
ABI
Capabilities
Effects
Diagnostics
```

Điều này giúp AI tooling hiểu API mà không cần đọc toàn bộ source.

---

# 20. Incremental compilation

Nếu:

```text
A
B → A
C → B
D → C
```

và chỉ A thay đổi:

```text
A rebuild
B rebuild
C rebuild
D rebuild
```

chỉ khi semantic fingerprint của dependency thay đổi.

Nếu A thay đổi implementation nhưng public semantic interface không thay đổi:

```text
A rebuild
B/C/D
```

có thể không cần rebuild semantic artifacts.

---

# 21. Interface fingerprint

Mỗi module/package có:

```text
InterfaceFingerprint
```

dựa trên:

```text
public API
public types
traits
ABI
repr contracts
exported symbols
comptime-visible metadata
```

Không dựa đơn giản trên:

```text
entire source hash
```

---

# 22. Implementation fingerprint

Riêng codegen:

```text
ImplementationFingerprint
```

bao gồm:

```text
private implementation
optimization
target
CPU features
LTO configuration
```

Nhờ vậy compiler phân biệt:

```text
interface unchanged
implementation changed
```

với:

```text
public API changed
```

---

# 23. Build graph

Build graph node:

```text
Source
Module
Package
Comptime
GenericInstance
Object
Library
Executable
```

Edge:

```text
depends-on
generates
imports
links
```

Ví dụ:

```text
A.ax
 ↓
A.HIR
 ↓
A.MIR
 ↓
A.o
 ↓
libA
 ↓
app
```

---

# 24. Parallel build

Build graph là DAG nên:

```text
A
B
C
```

không phụ thuộc nhau có thể compile song song.

Compiler scheduler:

```text
ready queue
    ↓
worker pool
    ↓
completed nodes
    ↓
unlock dependents
```

Kết quả deterministic.

---

# 25. Build determinism

Thứ tự:

```text
parallel compilation
```

không được ảnh hưởng:

```text
symbol identity
layout
semantic resolution
output behavior
```

Nếu hai build chạy với cùng inputs:

```text
A → B
```

và:

```text
B → A
```

thì artifact semantic phải tương đương.

---

# 26. Cache hierarchy

Axiom nên có nhiều tầng:

```text
L1
in-memory compiler cache

L2
local disk cache

L3
workspace cache

L4
shared/remote cache
```

Remote cache **optional**.

Không được biến thành dependency của build system.

---

# 27. Cache artifact validation

Không tin cache chỉ vì filename.

Mỗi artifact có:

```text
ArtifactHeader
{
    magic
    format_version
    compiler_semantic_version
    target
    fingerprint
}
```

Nếu mismatch:

```text
cache miss
```

Không cố sử dụng artifact cũ.

---

# 28. Build cache không thay đổi semantics

Cache hit:

```text
compile(source)
```

và cache miss:

```text
compile(source)
```

phải cho cùng semantic result.

---

# 29. Build scripts

Axiom không nên mặc định cho phép arbitrary script chạy với full quyền hệ thống.

Build-time code nên đi qua model:

```text
comptime
+
explicit build capabilities
```

Ví dụ:

```text
ReadSource
GenerateFile
ExecuteTool
Environment
Network
```

giống mô hình comptime đã khóa.

---

# 30. Generated source

Nếu build step sinh source:

```text
generated/
```

thì generated declarations phải đi qua:

```text
parse
resolve
typecheck
ownership verification
ABI verification
```

Không có đường tắt.

---

# 31. Build-time external tools

Nếu cần:

```text
protoc
shader compiler
resource compiler
code generator
```

thì dependency phải khai báo rõ:

```text
build tool dependency
```

Build identity phải bao gồm:

```text
tool version
tool identity
tool inputs
```

---

# 32. No hidden environment dependency

Không được để:

```text
build hôm nay
```

phụ thuộc ngẫu nhiên vào:

```text
PATH
current directory
random environment variable
system clock
```

trừ khi manifest explicitly yêu cầu.

---

# 33. Reproducible build

Có hai mode:

```text
normal
reproducible
```

Reproducible mode kiểm soát:

```text
timestamps
paths
randomness
environment
dependency order
parallel scheduling
tool versions
```

---

# 34. Offline build

Nếu dependencies đã được vendored/cache:

```text
ax build --offline
```

không truy cập network.

Comptime:

```text
Network capability
```

cũng phải bị chặn nếu offline mode.

---

# 35. Vendoring

Có thể:

```text
ax vendor
```

→

```text
vendor/
```

Build sử dụng:

```text
vendor/
```

thay vì registry/network.

Đặc biệt hữu ích cho:

- embedded;
- enterprise;
- air-gapped;
- reproducible builds.

---

# 36. Registry

Registry là **transport/distribution service**, không phải language primitive.

Một package registry cung cấp:

```text
name
versions
metadata
artifact/source
hash
signature
```

Có thể tồn tại nhiều registry:

```text
official
private
local
enterprise
```

---

# 37. Package versioning

Dùng semantic versioning làm mặc định:

```text
MAJOR.MINOR.PATCH
```

nhưng resolver không được chỉ dựa vào string.

Nó cần hiểu:

```text
compatibility range
```

và dependency constraints.

---

# 38. Version resolution

Ví dụ:

```text
App
├── A requires Math ^1.2
└── B requires Math ^1.4
```

resolver có thể chọn:

```text
Math 1.8
```

nếu thỏa cả hai.

Nếu:

```text
A requires Math 1.x
B requires Math 2.x
```

thì:

```text
resolution conflict
```

Không âm thầm chọn một phiên bản.

---

# 39. Multiple versions

Axiom nên cho phép nhiều phiên bản package nếu cần:

```text
App
├── A → Math 1.x
└── B → Math 2.x
```

Nhưng compiler phải giữ identity:

```text
Math@1
Math@2
```

không thể coi là cùng type namespace.

---

# 40. Dependency identity và type identity

Điều này cực kỳ quan trọng.

```text
Vec<T> from math@1
```

khác:

```text
Vec<T> from math@2
```

dù source giống nhau.

Type identity phải bao gồm package identity khi cần.

---

# 41. System dependencies

Ví dụ:

```text
libc
CUDA
Metal
DirectX
Win32
```

được biểu diễn:

```text
system dependency
```

chứ không phải package source thông thường.

Build system cần biết:

```text
required symbols
ABI
version constraint
platform
```

---

# 42. Binary dependency

Có thể phụ thuộc vào binary artifact:

```text
foo.axlib
```

không có source.

Artifact phải cung cấp:

```text
.axmeta
ABI
target
architecture
link requirements
```

Nếu metadata không phù hợp:

```text
binary compatibility error
```

---

# 43. ABI compatibility

Package update không chỉ kiểm tra API.

Phải kiểm tra:

```text
type identity
layout
repr
calling convention
symbol
alignment
error ABI
FFI ABI
```

Đây là lý do `.axmeta` quan trọng.

---

# 44. Build profiles + target matrix

Ví dụ:

```text
targets:
    x86_64-linux
    x86_64-windows
    aarch64-linux
    aarch64-macos
```

profiles:

```text
debug
release
size
```

Build graph tạo:

```text
target × profile
```

nhưng cache identity giữ chúng tách biệt.

---

# 45. Workspace

Workspace:

```text
workspace/
├── app/
├── core/
├── graphics/
└── tools/
```

các package local có thể share:

```text
CompilerDB
cache
dependency graph
build graph
```

Nhưng mỗi package vẫn giữ identity độc lập.

---

# 46. Workspace dependency

Ví dụ:

```text
app
 └── path = "../core"
```

được resolve thành:

```text
PackageId(core, local-source-identity)
```

không phải copy package.

---

# 47. Artifact promotion

Build:

```text
workspace
```

có thể tạo:

```text
local artifact
```

Sau đó publish:

```text
registry artifact
```

Artifact identity vẫn phải giữ hash/semantic identity.

---

# 48. Build output isolation

Không trộn:

```text
debug/
release/
different targets/
different architectures/
```

Ví dụ:

```text
build/
├── debug/
│   └── x86_64-linux/
└── release/
    └── x86_64-linux/
```

---

# 49. Compiler cache vs package cache

Phải tách:

```text
Package Cache
```

và:

```text
Compiler Incremental Cache
```

Package cache:

```text
downloaded dependencies
```

Compiler cache:

```text
HIR
MIR
metadata
object
```

Không trộn hai lifecycle.

---

# 50. Build daemon

Axiom có thể hỗ trợ build daemon:

```text
ax build --daemon
```

để giữ:

```text
CompilerDB
type cache
incremental state
```

trong memory.

Nhưng daemon **optional**.

Build không được phụ thuộc daemon để đúng.

---

# 51. AI-oriented build graph

Build system nên xuất:

```text
ax build --explain
```

ví dụ:

```text
Rebuilt:
  graphics/src/color.ax
Reason:
  InterfaceFingerprint changed

Not rebuilt:
  math
Reason:
  dependency interface unchanged
```

AI agent có thể hiểu chính xác tại sao compiler rebuild.

---

# 52. Structured build diagnostics

Không chỉ:

```text
"rebuilding..."
```

mà có:

```text
BuildEvent {
    node
    state
    reason
    dependencies
    cache_hit
    fingerprint
    duration
}
```

Đây rất hữu ích cho agent tự động.

---

# 53. Build graph persistence

Build graph có thể lưu:

```text
.axbuild
```

hoặc database tương đương.

Nó cho phép incremental build sau khi process compiler kết thúc.

---

# 54. Package security

Package manager phải hỗ trợ:

```text
hash verification
signature verification
source identity
registry identity
```

Nhưng không biến signature thành language semantics.

Security policy thuộc build/distribution layer.

---

# 55. Dependency trust levels

Có thể có:

```text
trusted
verified
unverified
local
system
```

Build policy có thể:

```text
--require-signatures
--offline
--allow-unverified
```

Nhưng compiler semantic layer không biết “package này đáng tin” theo nghĩa logic.

---

# 56. Package capabilities

Package không tự động được:

```text
network
filesystem
execute arbitrary tool
```

chỉ vì nó được build.

Build-time capabilities phải được manifest/request khai báo.

Runtime permissions vẫn là OS/security concern.

---

# 57. Package build scripts và comptime

Ưu tiên:

```text
comptime
```

cho generated declarations.

Chỉ dùng external build tool khi cần tương tác ngoài compiler.

Ví dụ:

```text
shader compilation
native resource embedding
platform SDK generation
```

---

# 58. Compiler/package separation

Compiler chịu:

```text
syntax
types
semantics
MIR
optimization
codegen
```

Build system chịu:

```text
dependency resolution
file graph
package graph
cache
artifact graph
tool invocation
```

Linker chịu:

```text
symbols
relocations
binary layout
```

Không trộn ba tầng.

---

# 59. Build invariants

### `ABUILD-20`
Module identity is distinct from package identity.

### `ABUILD-21`
Package identity includes source identity.

### `ABUILD-22`
Dependency resolution produces an explicit graph.

### `ABUILD-23`
Package dependency cycles are rejected.

### `ABUILD-24`
Module cycles may be supported independently of package cycles.

### `ABUILD-25`
Target-specific dependencies are resolved before final build graph construction.

### `ABUILD-26`
Build profiles do not change language semantics.

### `ABUILD-27`
Lockfiles identify an exact dependency graph.

### `ABUILD-28`
Dependency content may be content-addressed.

### `ABUILD-29`
Artifact identity includes all semantic build inputs.

### `ABUILD-30`
Interface fingerprints are distinct from implementation fingerprints.

### `ABUILD-31`
Implementation-only changes need not invalidate dependents whose interface is unchanged.

### `ABUILD-32`
Cache hits and cache misses must produce equivalent semantics.

### `ABUILD-33`
Parallel builds must be deterministic.

### `ABUILD-34`
Build scripts cannot silently access undeclared external capabilities.

### `ABUILD-35`
Generated source re-enters normal compiler verification.

### `ABUILD-36`
Offline mode prohibits undeclared network access.

### `ABUILD-37`
Vendored dependencies are first-class build inputs.

### `ABUILD-38`
Binary dependencies must expose compatible metadata and ABI contracts.

### `ABUILD-39`
Package version identity is distinct from language edition.

### `ABUILD-40`
Multiple package versions may coexist when their identities differ.

### `ABUILD-41`
Package dependency resolution cannot silently substitute incompatible versions.

### `ABUILD-42`
System dependencies are explicit.

### `ABUILD-43`
Compiler caches are distinct from package distribution caches.

### `ABUILD-44`
Build daemon use is optional.

### `ABUILD-45`
Build explanations are machine-readable.

### `ABUILD-46`
Build graph state is inspectable.

### `ABUILD-47`
Artifact metadata is sufficient to reject incompatible reuse.

### `ABUILD-48`
Package management is independent of language semantics.

### `ABUILD-49`
Axiom does not require a centralized package registry.

### `ABUILD-50`
Axiom supports reproducible builds.

### `ABUILD-51`
Axiom supports fully offline builds when dependencies are available locally.

### `ABUILD-52`
The build system does not implicitly link unused runtime components.

### `ABUILD-53`
Comptime dependencies participate in build identity.

### `ABUILD-54`
External tool dependencies participate in build identity.

### `ABUILD-55`
Package metadata is consumable by compiler and AI tooling.

### `ABUILD-56`
A build artifact cannot be reused across incompatible target/ABI configurations.

### `ABUILD-57`
The build graph remains independent from the linker implementation.

---

# 60. Toàn bộ Axiom toolchain hiện tại

Sau BOOTSTRAP-113, kiến trúc đã có:

```text
                    AXIOM
                      │
        ┌─────────────┴─────────────┐
        │                           │
     Language                    Toolchain
        │                           │
        ▼                           ▼
   AST/HIR/MIR                Build System
        │                           │
   Verification                Package Graph
        │                           │
    Optimization               Cache
        │                           │
       ABI                    Artifacts
        │                           │
       LIR                          │
        │                           │
    Machine IR                     │
        │                           │
   Object Writer ◄─────────────────┘
        │
      Linker
        │
 Runtime Composition
        │
 Platform System Layer
        │
      Native OS
```

Đến đây, **compiler architecture, native backend, object/linker, runtime composition, bootstrap và build/package system** đã tạo thành một chuỗi khá hoàn chỉnh.

---

# BOOTSTRAP-114 — Standard Library Architecture

Task kế tiếp nên khóa **Standard Library**, nhưng theo một nguyên tắc rất quan trọng:

> **Stdlib không được trở thành “ngôn ngữ thứ hai” và cũng không được biến mọi tính năng thành runtime bắt buộc.**

Kiến trúc dự kiến:

```text
Axiom Core
    │
    ├── Language primitives
    │
    └── Standard Library
          ├── core
          ├── alloc
          ├── collections
          ├── string
          ├── unicode
          ├── io
          ├── fs
          ├── net
          ├── process
          ├── sync
          ├── thread
          ├── async
          ├── time
          ├── random
          ├── math
          ├── crypto
          ├── os
          ├── gpu
          └── ffi
```

Task 114 sẽ đặc biệt phải giải quyết:

- `core` thực sự chứa gì;
- `alloc` có bắt buộc không;
- `Vec`, `String`, `Box`, `Arc`, `Rc`;
- `Option`, `Result` thuộc Core hay stdlib;
- collections;
- iterator;
- string/UTF-8;
- Unicode;
- filesystem/network;
- thread/sync;
- async;
- process;
- time/random;
- math/SIMD;
- FFI;
- OS abstraction;
- GPU/tensor;
- logging;
- serialization;
- testing;
- không kéo runtime không cần thiết;
- API design nhất quán với `view<T>` / `mut_view<T>`;
- zero-cost abstractions;
- `no_std` tương đương nhưng theo mô hình Axiom riêng;
- và quan trọng nhất: **ranh giới chính xác giữa Core Language, Compiler Builtin, Runtime Component và Standard Library**.

Đây sẽ là task lớn tiếp theo vì sau khi khóa stdlib, chúng ta mới có thể bắt đầu chuyển toàn bộ kiến trúc Axiom thành **implementation roadmap cụ thể**.