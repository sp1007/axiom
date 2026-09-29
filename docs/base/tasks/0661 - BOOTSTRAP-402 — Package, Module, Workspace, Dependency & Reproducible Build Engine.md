# BOOTSTRAP-402 — Package, Module, Workspace, Dependency & Reproducible Build Engine

Đây là lớp hạ tầng rất quan trọng sau khi Core + Runtime model + OS/I/O/Network đã tương đối hoàn chỉnh.

Mục tiêu của task này là làm cho Axiom có **một hệ thống package/module/build đủ mạnh để xây những dự án lớn**, nhưng không biến compiler thành một hệ thống build mơ hồ kiểu “chạy một đống script rồi hy vọng kết quả giống nhau”.

Nguyên tắc:

> **Source code → Module → Package → Dependency Graph → Build Graph → Artifact**

và toàn bộ quá trình phải **deterministic, incremental, cacheable, reproducible và compiler-verifiable**.

---

# 1. Phân biệt 5 khái niệm

Axiom không được nhập nhằng:

```text
Module
   ↓
Package
   ↓
Workspace
   ↓
Dependency Graph
   ↓
Build Graph
```

### Module

Đơn vị namespace/compiler.

Ví dụ:

```text
axiom.collections.vector
axiom.collections.hashmap
axiom.net.http
```

Module không nhất thiết tương ứng 1 file.

### Package

Đơn vị phân phối.

Ví dụ:

```text
my_server
axiom_std
axiom_gui
axiom_ml
```

Một package có thể chứa nhiều module.

### Workspace

Tập hợp nhiều package cùng được phát triển/build.

```text
workspace/
    axiom_core/
    axiom_http/
    my_server/
    my_tests/
```

### Dependency Graph

Quan hệ:

```text
my_server
 ├── axiom_http
 │    ├── axiom_net
 │    └── axiom_crypto
 └── axiom_json
```

### Build Graph

Không chỉ package dependency.

Nó biểu diễn artifact thực tế:

```text
source
  ↓
parse
  ↓
HIR
  ↓
MIR
  ↓
object
  ↓
static library
  ↓
executable
```

Do đó:

> Dependency Graph trả lời **“cần gì?”**  
> Build Graph trả lời **“phải xây cái gì?”**

---

# 2. Module system

Module là namespace có identity rõ ràng.

Ví dụ:

```axiom
module axiom.math.vector
```

Import:

```axiom
import axiom.math.vector
```

hoặc:

```axiom
import axiom.math.vector.Vector
```

Export:

```axiom
export Vector
export dot
```

Không export thì symbol không public ra ngoài module.

---

# 3. Visibility

Core nên có ít mức visibility.

Đề xuất:

```text
private
module
package
public
```

Ý nghĩa:

| Visibility | Có thể truy cập |
|---|---|
| `private` | cùng declaration/container |
| `module` | trong module |
| `package` | toàn package |
| `public` | package khác |

Không cần một hệ thống hàng chục modifier.

Ví dụ:

```axiom
package axiom.math

struct Vector {
    public x: f32
    public y: f32

    private cached_length: f32
}
```

---

# 4. Re-export

Package/module có thể tái xuất API:

```axiom
export axiom.math.Vector
export axiom.math.Matrix
```

Cho phép:

```axiom
import axiom.math.Vector
```

thay vì buộc người dùng biết cấu trúc nội bộ.

Điều này đặc biệt quan trọng cho:

- API façade
- compatibility layer
- package refactoring.

---

# 5. Không cho global namespace

Axiom tuyệt đối không có:

```text
global namespace
global package search
global variables ảnh hưởng resolution
```

Tên phải resolve theo:

```text
Package
→ Module
→ Import
→ Namespace
→ Symbol
```

Điều này giúp compiler và AI agent dễ phân tích code.

---

# 6. Package identity

Package không được định danh chỉ bằng tên.

Identity:

```text
PackageIdentity =
    namespace
    + name
    + version
    + source identity
```

Ví dụ:

```text
org.axiom
axiom-http
3.2.1
```

Source identity có thể là:

```text
registry
git
path
archive
local
system
```

---

# 7. Manifest

Mỗi package có manifest.

Ví dụ khái niệm:

```text
package:
    name = "my_server"
    version = "1.0.0"

dependencies:
    axiom-http = "3.x"
    axiom-json = "2.x"

targets:
    executable = "server"
```

Manifest **không phải code**.

Nó là metadata để resolver/build engine xử lý.

---

# 8. Dependency resolution

Dependency phải resolve thành graph cụ thể.

Ví dụ:

```text
A → B >= 2.0
A → C >= 1.0
B → C 1.x
```

Resolver tạo:

```text
A
├── B 2.4.1
└── C 1.8.2
```

Không được để compiler tự động chọn dependency khác nhau tùy thời điểm build.

---

# 9. Lockfile

Build ứng dụng phải có dependency lock.

Ví dụ:

```text
axiom-http 3.2.1
sha256 = ...
source = ...
```

Lockfile đảm bảo:

```text
same source
+ same compiler
+ same target
+ same dependency lock
+ same build inputs
→ same semantic build
```

---

# 10. Multiple versions

Axiom nên cho phép hai version tồn tại nếu graph yêu cầu:

```text
App
├── LibA → Crypto 1.x
└── LibB → Crypto 2.x
```

Nhưng hai package/version phải có namespace identity khác nhau trong compiler.

Không được silently merge chúng.

Nếu ABI hoặc symbol conflict thì linker/build resolver phải phát hiện.

---

# 11. Circular dependency

Module cycle có thể tồn tại trong một số trường hợp.

Package dependency cycle thì mặc định:

```text
A → B
B → A
```

**reject**.

Lý do rất đơn giản:

- dependency graph dễ xây
- build ordering deterministic
- package initialization không mơ hồ
- cache invalidation đơn giản.

Module-level semantic cycle có thể được xử lý bằng declaration/import graph riêng.

---

# 12. Feature system

Package có thể có feature:

```text
features:
    gui
    gpu
    tls
    sqlite
```

Nhưng feature phải là **build configuration**, không được trở thành runtime magic.

Ví dụ:

```axiom
@cfg(feature = "gpu")
fn train_gpu(...)
```

Compiler resolve feature trước khi type-check toàn bộ configuration tương ứng.

---

# 13. Feature resolution phải deterministic

Không cho:

```text
package A bật gpu
package B tắt gpu
```

rồi compiler tự quyết định tùy thứ tự.

Feature graph phải được resolve thành một configuration duy nhất cho mỗi package instance.

Nếu có conflict:

```text
compile error
```

hoặc explicit feature unification rule.

Đề xuất:

> Feature của cùng một package instance được hợp nhất theo phép OR đối với feature bật/tắt đơn giản, nhưng các feature có semantic conflict phải khai báo conflict và resolver reject.

---

# 14. Source package và binary package

Axiom cần phân biệt:

```text
SourcePackage
BinaryPackage
SystemPackage
FfiPackage
```

Binary package có thể chứa:

```text
interface metadata
IR cache
object
static library
dynamic library
debug info
source map
```

---

# 15. Axiom Interface Artifact

Đây là phần rất quan trọng.

Một package không nhất thiết phải expose source.

Compiler cần một interface artifact chứa:

```text
public types
public functions
public traits
public constants
ABI
layout metadata cần thiết
generic metadata
visibility
effects
capabilities
compiler semantic version
```

Ví dụ:

```text
libfoo.axiom-interface
```

Compiler package khác có thể type-check mà không cần parse toàn bộ source của `foo`.

---

# 16. Generic code

Generic public API cần metadata đủ để compiler instantiate.

Ví dụ:

```axiom
public fn sort<T: Ord>(...)
```

Interface artifact phải giữ semantic information của generic declaration.

Implementation private không cần expose.

---

# 17. ABI compatibility

Package binary không được coi là tương thích chỉ vì:

```text
version giống
```

Compiler cần kiểm tra:

```text
Type layout
Calling convention
Symbol ABI
Generic ABI
Target ABI
Compiler ABI contract
```

Có thể có:

```text
source compatible
ABI compatible
binary compatible
```

là ba khái niệm khác nhau.

---

# 18. Build Graph

Đây là trung tâm của Build Engine.

Mỗi node:

```text
BuildNode {
    inputs
    action
    target
    environment
    dependencies
    outputs
}
```

Ví dụ:

```text
Parse(foo.ax)
    ↓
HIR(foo)
    ↓
TypedHIR(foo)
    ↓
MIR(foo)
    ↓
Object(foo.o)
```

Sau đó:

```text
Object(foo.o)
Object(bar.o)
libaxiom.a
    ↓
Link
    ↓
app.exe
```

---

# 19. CompilerDB tích hợp trực tiếp

Không xây build system tách biệt hoàn toàn khỏi compiler.

CompilerDB trở thành một phần của build graph.

Ví dụ:

```text
SourceDB
ModuleDB
PackageDB
HIRDB
TypeDB
MIRDB
ArtifactDB
BuildGraphDB
```

Một thay đổi source:

```text
foo.ax
```

chỉ invalidate các query/artifact thực sự phụ thuộc vào semantic output của `foo`.

---

# 20. Semantic incremental compilation

Không chỉ:

```text
file timestamp changed
→ rebuild
```

Mà:

```text
source
→ syntax fingerprint
→ declaration fingerprint
→ type fingerprint
→ semantic fingerprint
→ MIR fingerprint
```

Ví dụ thay đổi comment:

```axiom
// hello
fn add(a: i32, b: i32) -> i32
```

thành:

```axiom
// this function adds two integers
fn add(a: i32, b: i32) -> i32
```

không được rebuild code generation nếu comment không ảnh hưởng artifact.

---

# 21. Fingerprint

Mỗi semantic node có fingerprint.

Khái niệm:

```text
Fingerprint =
    hash(
        semantic input
        + dependency fingerprints
        + compiler semantic version
        + target
        + relevant configuration
    )
```

Không hash bừa toàn bộ filesystem.

---

# 22. Content-addressed cache

Artifact cache:

```text
cache/
    <fingerprint>
        artifact
        metadata
```

Nếu fingerprint giống:

```text
cache hit
```

Không cần compile lại.

---

# 23. Cache correctness

Compiler **không được** coi cache hit chỉ dựa trên filename.

Cache key phải chứa đủ semantic inputs.

Ví dụ:

```text
source fingerprint
dependency fingerprints
compiler version
target triple
CPU features
optimization profile
features
ABI mode
comptime inputs
```

---

# 24. Comptime integration

Đây là chỗ BOOTSTRAP-402 liên kết trực tiếp với Comptime.

Nếu:

```axiom
comptime read_source(...)
```

phụ thuộc file:

```text
schema.json
```

thì:

```text
schema.json
```

phải trở thành BuildGraph dependency.

Nếu file đổi:

```text
comptime output invalid
→ downstream rebuild
```

Không được cache sai.

---

# 25. Generated source

Generated code phải có provenance.

Ví dụ:

```text
generated:
    source = schema.json
    generator = schema_codegen
    generator_version = ...
```

Compiler phải biết:

```text
generated declaration
← generator
← input
```

Không coi generated source là một file “từ trên trời rơi xuống”.

---

# 26. Hermetic build

Axiom nên có hai profile:

### Normal

Cho phép môi trường hệ thống.

### Hermetic

Build chỉ được nhìn thấy những input được khai báo.

Ví dụ:

```text
source
dependency
compiler
SDK
comptime input
environment declaration
```

Ngoài danh sách → inaccessible.

Điều này rất quan trọng cho reproducible build.

---

# 27. Reproducible build

Cùng semantic inputs phải tạo cùng artifact semantic.

Compiler phải loại bỏ các nguồn nondeterminism không cần thiết:

```text
filesystem traversal order
hash-map iteration
thread scheduling
timestamps
random IDs
absolute paths
machine-local paths
```

Debug metadata có thể chứa machine-specific information nếu profile cho phép, nhưng reproducible profile phải canonicalize chúng.

---

# 28. Build profiles

Core nên định nghĩa một số profile chuẩn:

```text
debug
release
size
speed
test
sanitize
freestanding
```

Profile chỉ là tập compiler configuration.

Không biến profile thành ngôn ngữ riêng.

---

# 29. Target model

Target phải explicit:

```text
x86_64-windows
x86_64-linux
aarch64-linux
aarch64-macos
wasm32
...
```

Target chứa:

```text
architecture
OS
ABI
object format
calling convention
CPU baseline
endianness
pointer width
features
link model
```

---

# 30. Cross compilation

Host:

```text
Windows x86_64
```

Target:

```text
Linux ARM64
```

không được yêu cầu chạy binary target trên host để compile.

Build graph phải phân biệt:

```text
host execution
target compilation
target linking
```

Đặc biệt quan trọng với `comptime`.

---

# 31. Host/target comptime

Comptime code mặc định chạy trên **host compiler environment**, nhưng output phải được kiểm soát để tạo artifact target.

Ví dụ:

```text
comptime generate_tables()
```

không được vô tình lấy:

```text
sizeof(pointer)
```

của host nếu semantic intent là target.

Các intrinsic target-dependent phải explicit:

```text
target.size_of::<T>()
```

hoặc compiler context tương đương.

---

# 32. Build script

Không nên có “shell script build” là cơ chế chính.

Axiom nên có:

```text
comptime build
```

hoặc build declaration có typed API.

Ví dụ:

```text
generate:
    input = "schema.json"
    output = "schema.generated.ax"
```

Build system hiểu dependency trực tiếp.

Shell/tool execution vẫn được phép thông qua capability:

```text
ExecuteTool
```

nhưng phải explicit.

---

# 33. Không cho build script phá hermeticity

Một build action gọi:

```text
curl ...
```

không được tự động trở thành dependency vô hình.

Hermetic mode:

```text
Network capability = denied
```

hoặc phải khai báo dependency/network input.

---

# 34. Static/Dynamic library

Build artifact kinds:

```text
Executable
StaticLibrary
DynamicLibrary
Object
Interface
DebugInfo
Resource
GeneratedSource
Package
```

Ví dụ:

```text
libfoo.a
foo.dll
libfoo.so
foo.exe
foo.axiom-interface
```

Compiler/linker cần metadata ownership và ABI.

---

# 35. System libraries

FFI package có thể khai báo:

```text
system library
```

Ví dụ:

```text
libc
kernel32
user32
Metal
Vulkan
```

Nhưng package metadata phải nói rõ:

```text
library name
target condition
ABI
link mode
required symbols
SDK requirement
```

Không để linker “tự đoán”.

---

# 36. Vendoring

Dependency có thể được vendor vào workspace:

```text
vendor/
    axiom-http/
    axiom-json/
```

Build offline vẫn phải hoạt động.

Dependency identity vẫn giữ nguyên.

---

# 37. Registry

Axiom không nên hard-code một registry duy nhất.

Architecture:

```text
PackageSource
    ├── Registry
    ├── Git
    ├── Path
    ├── Archive
    ├── LocalCache
    └── Vendor
```

Registry server chỉ là implementation.

---

# 38. Package trust

Tích hợp với Security model:

```text
PackageSignature
DependencyTrust
Provenance
```

Package có thể được:

```text
unsigned
signed
trusted
pinned
```

Security policy quyết định build có chấp nhận package hay không.

---

# 39. Build provenance

Artifact nên có metadata:

```text
artifact hash
source hash
dependency hashes
compiler version
target
build profile
features
comptime inputs
package signatures
```

Có thể strip metadata khỏi binary release nếu muốn, nhưng build system vẫn phải giữ provenance bên ngoài.

---

# 40. Parallel build

Build graph là DAG nên compiler/build engine có thể chạy:

```text
A ─┐
B ─┼→ D
C ─┘
```

song song.

CompilerDB cũng có thể compile independent modules đồng thời.

Không được để concurrency làm thay đổi semantic result.

---

# 41. Build cancellation

Nếu user nhấn cancel:

```text
Build → Cancelling
```

phải:

- ngừng node chưa chạy
- cancel node hỗ trợ cancellation
- không tạo artifact “nửa vời”
- không corrupt cache
- giữ artifact cũ hợp lệ.

Cache publication phải atomic.

---

# 42. Atomic artifact publication

Không:

```text
write cache/foo.o
```

trực tiếp.

Mà:

```text
temporary artifact
    ↓
verify
    ↓
atomic publish
```

Nếu compiler crash giữa chừng:

```text
cache vẫn valid
```

---

# 43. Compiler daemon

Axiom có thể có:

```text
axiom build
axiom check
axiom watch
axiom test
```

Compiler daemon giữ:

```text
CompilerDB
AST
HIR
types
MIR
fingerprints
cache metadata
```

trong memory.

Nhờ đó incremental rebuild rất nhanh.

---

# 44. Watch mode

Khi:

```text
foo.ax thay đổi
```

daemon:

```text
filesystem event
→ invalidate affected queries
→ rebuild affected graph
→ report diagnostics
```

Không restart compiler toàn bộ.

---

# 45. Build verification

Trước khi artifact được cache/publish:

```text
Source validity
Module resolution
Type validity
Ownership validity
Capability validity
Effect validity
MIR validity
ABI validity
Target validity
Artifact validity
```

phải pass.

---

# 46. CompilerDB mới

BOOTSTRAP-402 bổ sung nhóm database:

```text
PackageDB
PackageIdentityDB
PackageVersionDB
PackageManifestDB
PackageDependencyDB
DependencyConstraintDB
DependencyResolutionDB
DependencyLockDB

WorkspaceDB
WorkspaceMemberDB

ModuleDB
ModulePathDB
ModuleImportDB
ModuleExportDB
ModuleVisibilityDB
ReExportDB
NamespaceDB
SymbolExportDB

BuildGraphDB
BuildNodeDB
BuildEdgeDB
BuildActionDB
BuildProfileDB
BuildTargetDB
BuildFeatureDB

BuildArtifactDB
BuildArtifactKindDB
BuildFingerprintDB
BuildCacheDB
BuildCacheKeyDB

IncrementalBuildDB
BuildInvalidationDB
BuildParallelDB
BuildCancellationDB

ReproducibleBuildDB
HermeticBuildDB
BuildSandboxDB

BuildProvenanceDB
PackageSignatureDB
DependencyTrustDB

RegistryDB
PackageSourceDB
VendoredPackageDB
OfflineBuildDB

FfiPackageDB
SystemSdkDB
LinkDependencyDB

StaticLibraryDB
DynamicLibraryDB
PackageAbiDB
PackageCompatibilityDB

CompilerDaemonDB
WatchBuildDB

BuildDiagnosticDB
BuildVerificationDB
```

---

# 47. Build IR

Không nên nhồi package/build semantics vào runtime MIR.

Tạo compiler-level IR:

## ABUILD

Ví dụ operations:

```text
PACKAGE_RESOLVE
MODULE_RESOLVE
MODULE_IMPORT
MODULE_EXPORT

DEPENDENCY_RESOLVE
DEPENDENCY_LOCK
FEATURE_RESOLVE

BUILD_NODE
BUILD_DEPENDENCY
BUILD_FINGERPRINT

BUILD_CACHE_LOOKUP
BUILD_CACHE_STORE

BUILD_GENERATE
BUILD_COMPILE
BUILD_LINK

BUILD_VERIFY
BUILD_SIGN
BUILD_PUBLISH
```

ABUILD không bao giờ xuất hiện trong executable.

---

# 48. Proof system

Các proof mới:

```text
ModuleResolutionProof
ModuleVisibilityProof
ImportProof
ExportProof
PackageIdentityProof
DependencyResolutionProof
DependencyLockProof
FeatureResolutionProof
BuildGraphProof
BuildDependencyProof
BuildFingerprintProof
IncrementalInvalidationProof
CacheValidityProof
ReproducibleBuildProof
HermeticBuildProof
BuildSandboxProof
GeneratedSourceProvenanceProof
PackageSignatureProof
DependencyTrustProof
AbiCompatibilityProof
LinkDependencyProof
CrossTargetProof
BuildParallelProof
BuildCancellationProof
BuildArtifactProof
OfflineBuildProof
VendoringProof
RegistryIntegrityProof
CompilerDaemonProof
BuildVerificationProof
```

---

# 49. Invariants — ABUILD-01 → ABUILD-30

### Package / Module

**ABUILD-01** — Package identity phải deterministic.

**ABUILD-02** — Module resolution phải deterministic.

**ABUILD-03** — Không có implicit global namespace.

**ABUILD-04** — Visibility violation phải bị reject compile-time.

**ABUILD-05** — Re-export không được phá visibility.

### Dependency

**ABUILD-06** — Dependency graph phải resolve thành graph xác định.

**ABUILD-07** — Lockfile phải pin dependency identity.

**ABUILD-08** — Dependency cycle bị reject ở package graph.

**ABUILD-09** — Multiple package versions phải có identity phân biệt.

**ABUILD-10** — Feature resolution phải deterministic.

### Build graph

**ABUILD-11** — Build graph phải là DAG đối với build actions.

**ABUILD-12** — Mọi artifact phải có declared inputs.

**ABUILD-13** — Mọi dependency của artifact phải được biểu diễn trong graph.

**ABUILD-14** — Build action không được có implicit semantic input.

**ABUILD-15** — Build cancellation không được làm cache invalid.

### Incremental

**ABUILD-16** — Fingerprint phải phụ thuộc đầy đủ semantic inputs.

**ABUILD-17** — Cache hit chỉ hợp lệ khi fingerprint khớp.

**ABUILD-18** — Semantic-independent source change không được bắt buộc rebuild downstream.

**ABUILD-19** — Semantic-dependent change phải invalidate artifact liên quan.

**ABUILD-20** — Cache publication phải atomic.

### Reproducibility

**ABUILD-21** — Hermetic build không được đọc undeclared input.

**ABUILD-22** — Reproducible build không phụ thuộc nondeterminism không được khai báo.

**ABUILD-23** — Comptime external input phải xuất hiện trong dependency graph.

**ABUILD-24** — Generated artifact phải có provenance.

**ABUILD-25** — Cross-target build phải phân biệt host và target semantics.

### ABI / Security / Artifact

**ABUILD-26** — Binary package phải có đủ interface metadata để kiểm tra compatibility.

**ABUILD-27** — Link dependency phải được khai báo rõ.

**ABUILD-28** — Package trust/signature policy phải được enforce trước publish/use theo profile.

**ABUILD-29** — Artifact cache chỉ chứa artifact đã pass verification.

**ABUILD-30** — Cùng semantic inputs phải tạo cùng semantic build result.

---

# 50. Kiến trúc tổng thể sau BOOTSTRAP-402

Axiom hiện có pipeline ngày càng rõ:

```text
                    ┌───────────────┐
                    │   Workspace   │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │    Package    │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │ Module / API  │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │ Dependency DB │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  CompilerDB   │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │   Build Graph │
                    └───────┬───────┘
                            │
          ┌─────────────────┼──────────────────┐
          ▼                 ▼                  ▼
       Package A         Package B         Package C
          │                 │                  │
          └─────────────────┼──────────────────┘
                            ▼
                         HIR/MIR
                            │
                            ▼
                       Object Files
                            │
                            ▼
                    Static/Dynamic Lib
                            │
                            ▼
                        Executable
```

Điểm quan trọng nhất của thiết kế này là **Build Engine không phải một chương trình bên ngoài compiler**. Nó dùng chung `CompilerDB`, fingerprint, semantic dependency và verification infrastructure.

Nhờ vậy Axiom có thể đạt mục tiêu rất quan trọng:

> **Một thay đổi nhỏ trong project lớn chỉ làm compiler tính lại phần semantic thực sự bị ảnh hưởng, thay vì rebuild cả project.**

Và đây cũng là nền tảng để sau này Axiom có **package manager + IDE + language server + compiler daemon + AI coding agent** cùng nhìn vào **một semantic graph duy nhất**, thay vì mỗi công cụ tự phân tích source theo một cách khác nhau.