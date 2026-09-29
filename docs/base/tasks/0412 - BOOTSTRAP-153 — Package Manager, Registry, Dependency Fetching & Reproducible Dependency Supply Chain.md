# BOOTSTRAP-153 — Package Manager, Registry, Dependency Fetching & Reproducible Dependency Supply Chain
**STATUS: FROZEN / COMPLETED**

> **Package là đơn vị phân phối; dependency là đầu vào của build; không dependency nào được phép âm thầm trở thành một phần bắt buộc của compiler, runtime hoặc toolchain.**

153 chốt lớp còn thiếu giữa `package.ax` và `BuildPlan`, đặc biệt để Axiom vừa có hệ sinh thái package hiện đại vừa giữ được mục tiêu **self-contained / reproducible / native / không phụ thuộc third-party compiler**.

---

## 1. Phân loại dependency

Axiom phải phân biệt rõ:

```text id="dep01"
Source Dependency
Binary Dependency
System Dependency
Build Dependency
Compiler Dependency
Runtime Dependency
Tool Dependency
```

Đây là distinction rất quan trọng.

### Source dependency

```text
my_app
  ↓
foo package source
```

Compiler biên dịch source của `foo`.

### Binary dependency

```text
my_app
  ↓
foo.axlib
```

Không cần source.

### System dependency

Ví dụ:

```text
Windows API
Linux kernel interface
Metal
Android NDK ABI
```

Không phải Axiom package.

### Build dependency

Chỉ cần trong quá trình build.

```text
code generator
asset compiler
schema generator
```

Không đi vào final binary nếu không cần.

### Runtime dependency

Ví dụ:

```text
Axiom async runtime
GPU runtime
Unicode database
```

chỉ được link nếu chương trình thực sự yêu cầu.

---

# 2. Compiler dependency

Đây là loại cần cấm trong production architecture:

```text id="dep02"
Axiom package
   ↓
requires GCC to compile
```

Không được coi đó là dependency bình thường.

Axiom package có thể **gọi tool bên ngoài** nếu developer explicitly yêu cầu trong build system, nhưng đó là:

```text
External Build Tool
```

không phải:

```text
Axiom Compiler Dependency
```

---

# 3. Dependency Graph

Package graph:

```text id="dep03"
App
├── graphics
│   ├── math
│   └── image
├── network
│   └── crypto
└── ui
    └── graphics
```

Resolver canonicalize thành DAG.

```text
PackageGraph
```

không được phụ thuộc vào filesystem traversal order.

---

# 4. Package Identity

Package identity:

```text id="dep04"
PackageIdentity {
    name
    version
    source_identity
}
```

Không chỉ:

```text
name + version
```

Ví dụ hai Git repository khác nhau cùng:

```text
foo 1.2.0
```

không được coi là cùng package.

---

# 5. Source Identity

Có thể:

```text id="dep05"
Registry
Git
Local
Archive
Vendored
Path
```

Mỗi source tạo:

```text id="dep06"
SourceIdentity
```

Ví dụ:

```text
registry + package hash
git + repository + commit
archive + content hash
local + canonical content identity
```

---

# 6. Lockfile

`axiom.lock` là **build resolution snapshot**.

Ví dụ khái niệm:

```text id="dep07"
foo
  version = 1.4.2
  source = registry
  checksum = ...

bar
  version = 0.8.1
  source = git
  revision = ...
```

Build production không được tự động đổi dependency chỉ vì registry có version mới.

---

# 7. Semantic Dependency Identity

Một dependency cache phải phân biệt:

```text id="dep08"
PackageIdentity
+
SourceContentHash
+
PublicInterfaceFingerprint
+
CompilerSemanticVersion
+
Target
+
ABI
```

Không nên cache chỉ dựa trên package version.

---

# 8. Registry

Registry chỉ là:

```text id="dep09"
distribution mechanism
```

không phải semantic authority.

Package tải về phải kiểm tra:

```text id="dep10"
manifest
content hash
signature
dependency metadata
target compatibility
ABI metadata
```

---

# 9. Content-addressed storage

Package cache nên dùng:

```text id="dep11"
ContentHash → PackageContent
```

Ví dụ:

```text
sha256:abc...
```

Một package giống hệt về content:

```text
→ dùng chung storage
```

---

# 10. Không tin tên file

Không được:

```text id="dep12"
foo-1.2.3.zip
```

→ mặc nhiên tin là `foo 1.2.3`.

Phải xác minh:

```text
manifest
+
content hash
```

---

# 11. Package Manifest

`package.ax` là source-of-truth cho package.

Khái niệm:

```text id="dep13"
package {
    name
    version
    edition
    targets
    dependencies
    features
    build
    exports
}
```

Không nên nhồi toàn bộ build logic vào manifest.

---

# 12. Features

Axiom nên có feature mechanism:

```text id="dep14"
features:
    gpu
    unicode
    tls
    image_png
```

Ví dụ:

```text id="dep15"
graphics
├── core
├── gpu
└── vulkan
```

Feature selection ảnh hưởng BuildGraph.

---

# 13. Feature unification

Trong cùng dependency graph:

```text id="dep16"
A → foo(features = [gpu])
B → foo(features = [unicode])
```

Resolver có thể hợp nhất:

```text id="dep17"
foo
features = [gpu, unicode]
```

nhưng phải deterministic.

---

# 14. Optional dependency

Ví dụ:

```text id="dep18"
image
 ├── core
 ├── png optional
 └── jpeg optional
```

Nếu không enable:

```text id="dep19"
png package
```

không xuất hiện trong graph.

---

# 15. Target-specific dependency

Ví dụ:

```text id="dep20"
Windows → win32
Linux   → linux
Android → android
```

Resolution phải diễn ra cùng target configuration:

```text
Target
 ↓
@cfg
 ↓
Dependency resolution
```

Không được resolve tất cả rồi mới loại bỏ một cách mơ hồ.

---

# 16. Host vs Target dependency

Đặc biệt:

```text id="dep21"
Host dependency
Target dependency
```

phải tách.

Ví dụ cross compile:

```text
Host = Windows
Target = Android
```

generator chạy trên:

```text
Windows
```

nhưng generated Axiom code chạy trên:

```text
Android
```

---

# 17. Build dependency

Một build dependency:

```text id="dep22"
app
 ↓
asset_codegen
```

chỉ tồn tại trong BuildGraph.

Nếu code generator không cần runtime:

```text id="dep23"
asset_codegen
```

không được link vào application.

---

# 18. Tool dependency

Có thể package yêu cầu:

```text id="dep24"
shader compiler
protobuf generator
asset converter
```

nhưng phải khai báo:

```text
ToolDependency
```

và environment requirement.

Build phải fail rõ ràng nếu tool thiếu.

Không được silently fallback sang compiler khác.

---

# 19. External tool trust

External tool output phải được coi là:

```text id="dep25"
untrusted generated input
```

Nếu tạo Axiom source:

```text
generated source
 ↓
normal parser
 ↓
resolver
 ↓
type checker
 ↓
verification
```

Không được bypass compiler.

---

# 20. Binary Dependency

Axiom cho phép:

```text id="dep26"
.axo
.axlib
.dll
.so
.dylib
.framework
```

tùy platform.

Nhưng binary dependency phải có metadata:

```text
target
architecture
ABI
exports
imports
dependencies
representation contracts
```

---

# 21. `.axmeta`

Binary/source package có thể cung cấp:

```text id="dep27"
foo.axmeta
foo.axlib
```

`.axmeta` chứa thông tin cần cho downstream compiler:

```text
public declarations
types
traits
generic metadata
ABI
exports
effects
relevant semantic summaries
```

Không cần parse source.

---

# 22. ABI Compatibility

Một binary package chỉ reusable nếu:

```text id="dep28"
target compatible
ABI compatible
compiler semantic requirements compatible
representation contracts compatible
```

Nếu không:

```text
E_ABI_INCOMPATIBLE
```

Không cố link rồi hy vọng chạy được.

---

# 23. Stable ABI

Không phải mọi Axiom package đều phải có stable ABI.

Mặc định:

```text id="dep29"
Axiom internal ABI
```

có thể thay đổi giữa compiler versions.

Nếu package muốn binary distribution lâu dài:

```text
stable ABI contract
```

phải được explicit.

---

# 24. Source package vs binary package

Có ba mode:

```text id="dep30"
Source
Binary
Hybrid
```

### Source

Compiler có source.

### Binary

Compiler nhận:

```text
.axmeta + .axo/.axlib
```

### Hybrid

Có binary artifact nhưng source/debug có thể được phân phối tùy package.

---

# 25. Dependency provenance

Build phải biết:

```text id="dep31"
package
version
source
hash
publisher
dependencies
```

để có:

```text
axc inspect dependencies
```

---

# 26. Supply-chain integrity

Axiom package manager nên hỗ trợ:

```text id="dep32"
content hash
publisher signature
lockfile verification
trusted source policy
```

Nhưng signature không thay thế hash.

```text
Signature → authenticity
Hash      → content identity
```

---

# 27. Offline build

Sau khi dependencies đã cache:

```text id="dep33"
axc build --offline
```

không được truy cập network.

Nếu thiếu package:

```text
E_DEPENDENCY_NOT_CACHED
```

thay vì tự tải.

---

# 28. Vendoring

Có thể:

```text id="dep34"
axc vendor
```

để tạo:

```text
vendor/
```

Build sau đó:

```text
registry
   ↓
vendor
```

không cần internet.

---

# 29. Workspace

Workspace:

```text id="dep35"
workspace/
├── package-a
├── package-b
└── package-c
```

Các package local vẫn giữ identity riêng.

Workspace không biến chúng thành một package.

---

# 30. Multiple versions

Có thể:

```text id="dep36"
A → foo 1.x
B → foo 2.x
```

Graph:

```text
App
├── foo@1
└── foo@2
```

Không ép mọi package vào một version nếu semver không tương thích.

---

# 31. Dependency cycle

Package cycle:

```text id="dep37"
A → B
B → A
```

→ reject.

Lý do không chỉ build complexity mà còn để:

```text
artifact
initialization
ownership of package interfaces
```

có dependency direction rõ ràng.

---

# 32. Version semantics

Package version:

```text id="dep38"
MAJOR.MINOR.PATCH
```

nên biểu diễn compatibility intent.

Nhưng compiler không được tin semver tuyệt đối.

Một package tuyên bố:

```text
1.2.3
```

vẫn phải compile/type-check hoặc dùng valid `.axmeta`.

---

# 33. Edition

Edition là:

```text id="dep39"
language surface compatibility
```

khác với package version.

Ví dụ:

```text
package version = 3.1.0
edition = 2028
```

Compiler có thể hỗ trợ nhiều edition.

---

# 34. Compiler version compatibility

Package có thể khai báo:

```text id="dep40"
requires_axiom >= X
```

Nhưng cần phân biệt:

```text
language compatibility
ABI compatibility
compiler implementation compatibility
```

---

# 35. Dependency build isolation

Mỗi package build có:

```text id="dep41"
source root
environment
features
target
profile
```

được xác định rõ.

Không để package A vô tình đọc file riêng của package B.

---

# 36. Build script capability

Build script nếu tồn tại phải chịu capability model:

```text id="dep42"
ReadSource
WriteGenerated
ExecuteTool
Environment
Network
```

Tương tự comptime.

Không mặc định:

```text
full filesystem access
```

---

# 37. Reproducible dependency resolution

Cùng:

```text id="dep43"
axiom.lock
registry snapshot
source content
compiler
target
```

→ dependency graph phải giống nhau.

Registry hiện tại thay đổi không được làm build đã lock thay đổi.

---

# 38. Registry snapshot

Đối với build reproducibility cao, có thể lưu:

```text id="dep44"
registry snapshot identity
```

hoặc content-addressed index.

Không nhất thiết tải toàn bộ registry.

---

# 39. Dependency cache hierarchy

Mở rộng cache trước:

```text id="dep45"
L0 memory
L1 query
L2 package source
L3 package build
L4 object
L5 final artifact
```

Package source cache phải độc lập object cache.

---

# 40. Package extraction security

Archive package không được phép:

```text id="dep46"
escape extraction directory
```

hoặc tự ghi file ngoài package root.

Path phải canonicalize và validate trước extraction.

---

# 41. Package metadata validation

Resolver phải validate:

```text id="dep47"
package name
version
dependencies
targets
features
manifest schema
hash
```

trước khi đưa vào BuildGraph.

---

# 42. Dependency conflict diagnostics

Ví dụ:

```text
A → foo ^1.2
B → foo ^2.0
```

Compiler không nên chỉ báo:

```text
dependency conflict
```

mà phải cho graph:

```text id="dep48"
foo@1.x required by A
foo@2.x required by B
```

AI agent có thể trực tiếp xử lý.

---

# 43. Dependency graph inspection

CLI:

```text id="dep49"
axc inspect dependencies
axc inspect dependencies --tree
axc inspect dependencies --why foo
axc inspect dependencies --features
axc inspect dependencies --licenses
axc inspect dependencies --sources
```

---

# 44. “Why dependency exists?”

Một chức năng rất hữu ích:

```text
axc inspect dependencies --why crypto
```

trả:

```text
app
 └─ network
     └─ tls
         └─ crypto
```

Điều này đặc biệt hữu ích để giảm:

```text
binary size
compile time
attack surface
```

---

# 45. Dependency elimination

Nếu dependency chỉ được enable nhưng không có symbol/code reachable:

```text
dependency
 ↓
no reachable artifact
```

thì final linker có thể loại bỏ phần runtime/code tương ứng.

Package presence ≠ final binary presence.

---

# 46. License metadata

Package metadata có thể chứa:

```text
license
license_files
source
publisher
```

để tooling kiểm tra compliance.

Nhưng license policy không thuộc semantic compiler.

---

# 47. Security policy

Project có thể đặt:

```text
dependency policy
```

ví dụ:

```text
allow registry X
deny unsigned package
allow only vendored dependencies
```

Driver enforcement, không phải language semantics.

---

# 48. Trusted vs untrusted package

Không cần đưa “trust” vào type system.

Package manager có:

```text
TrustedSourcePolicy
```

Compiler vẫn compile semantics bình thường.

---

# 49. No hidden dependency

Build output phải có manifest dependency report:

```text id="dep50"
Direct dependencies
Transitive dependencies
Build dependencies
Runtime components
System dependencies
```

Không được có:

```text
mysterious implicit package
```

ngoài compiler-defined standard/prelude/system contracts.

---

# 50. Standard library

`std` là package đặc biệt ở distribution layer nhưng **không phá package model**.

Ví dụ:

```text
std::core
std::alloc
std::collections
std::io
std::thread
```

Compiler biết một số primitive traits/intrinsics, nhưng phần lớn std vẫn là source/package.

---

# 51. Compiler builtin ≠ std package

Ví dụ:

```text
Copy
Drop
Send
Share
```

compiler hiểu semantic property.

Nhưng API sử dụng chúng vẫn có thể nằm trong:

```text
std::core
```

Đây là distinction quan trọng để tránh biến toàn bộ std thành compiler magic.

---

# 52. Package → Runtime

Package:

```text
network
```

có thể yêu cầu:

```text
IO
```

Package:

```text
async_net
```

có thể yêu cầu:

```text
IO
ASYNC
```

Runtime resolver hợp nhất:

```text
IO
ASYNC
```

không link component hai lần.

---

# 53. Package → System API

Một package có thể dùng:

```text
extern
```

với OS API.

Metadata phải ghi:

```text
SystemDependency {
    platform
    abi
    symbols
}
```

Linker sau đó giải quyết.

---

# 54. Binary package portability

Một `.axlib` không nên được coi là universal.

Metadata phải xác định:

```text
architecture
OS
ABI
CPU feature minimum
endianness
pointer width
runtime requirements
```

Ví dụ:

```text
x86_64-linux-gnu
```

không đồng nghĩa:

```text
x86_64-windows
```

---

# 55. Dependency ABI boundary

Khi binary package vượt ABI boundary:

```text
Source
   ↓
Package ABI
   ↓
Binary
```

mọi loại không có stable ABI phải bị reject nếu không có representation contract.

---

# 56. Source package reproducibility

Package source archive nên canonicalize:

```text
file ordering
path normalization
metadata
line endings policy
content hashing
```

để content identity không phụ thuộc filesystem.

---

# 57. Registry transport

Registry protocol chỉ chịu trách nhiệm:

```text
discover
download
publish
```

Compiler không phụ thuộc HTTP implementation cụ thể.

Có thể:

```text
registry
mirror
local registry
offline registry
```

mà BuildGraph không thay đổi.

---

# 58. Dependency fetch pipeline

```text id="dep51"
Manifest
   ↓
Lockfile
   ↓
Resolver
   ↓
Cache lookup
   ↓
Local source?
   ├── yes → verify
   └── no
         ↓
      Registry/Git
         ↓
      Download
         ↓
      Hash verify
         ↓
      Metadata verify
         ↓
      Cache
```

---

# 59. Package compilation pipeline

```text id="dep52"
Package
 ↓
Manifest
 ↓
Dependencies
 ↓
Target/Features
 ↓
Module Graph
 ↓
CompilerDB
 ↓
Verification
 ↓
Object
 ↓
Package Artifact
```

---

# 60. Final artifact provenance

Executable nên có optional build metadata:

```text id="dep53"
BuildIdentity
CompilerVersion
Target
ABI
Profile
DependencyRootHash
SourceRootHash
```

Có thể strip khỏi release binary nếu không cần.

---

# 61. Invariants

Đóng băng:

### `APKG-20`
Package identity is distinct from package name.

### `APKG-21`
Package identity includes source identity.

### `APKG-22`
Locked builds use exact resolved dependency identities.

### `APKG-23`
Dependency resolution is deterministic.

### `APKG-24`
Package graphs are acyclic.

### `APKG-25`
Module cycles remain distinct from package cycles.

### `APKG-26`
Source, binary, system, build and runtime dependencies are distinct categories.

### `APKG-27`
Compiler dependencies are not implicit package dependencies.

### `APKG-28`
Runtime dependencies are not equivalent to compiler dependencies.

### `APKG-29`
Build dependencies are excluded from runtime unless explicitly required.

### `APKG-30`
Target-specific dependencies are resolved against the selected target.

### `APKG-31`
Host and target dependencies are distinct.

### `APKG-32`
Features participate deterministically in dependency resolution.

### `APKG-33`
Optional dependencies are absent when not selected.

### `APKG-34`
Multiple incompatible package versions may coexist when graph semantics permit.

### `APKG-35`
Content hashes establish package content identity.

### `APKG-36`
Package names and filenames cannot substitute for content verification.

### `APKG-37`
Binary dependencies require compatible target and ABI metadata.

### `APKG-38`
`.axmeta` provides downstream semantic metadata for binary packages.

### `APKG-39`
Stable binary compatibility requires an explicit ABI contract.

### `APKG-40`
External tool output is untrusted generated input.

### `APKG-41`
Generated source re-enters the normal compiler pipeline.

### `APKG-42`
Package build capabilities are explicit.

### `APKG-43`
Offline mode performs no network dependency fetch.

### `APKG-44`
Vendored dependencies preserve dependency identity.

### `APKG-45`
Remote package content must be verified before use.

### `APKG-46`
Cache is not a semantic authority.

### `APKG-47`
Package extraction cannot escape its designated directory.

### `APKG-48`
Dependency provenance is inspectable.

### `APKG-49`
Dependency conflict diagnostics expose the dependency path.

### `APKG-50`
Unused dependency code may be removed from the final artifact.

### `APKG-51`
Package presence does not imply runtime presence.

### `APKG-52`
Standard library distribution does not require semantic compiler magic for ordinary APIs.

### `APKG-53`
Runtime components are resolved from actual package/program requirements.

### `APKG-54`
System dependencies remain target-specific.

### `APKG-55`
Binary artifacts are reusable only under compatible representation/ABI contracts.

### `APKG-56`
Dependency resolution cannot change language semantics.

### `APKG-57`
Package metadata cannot bypass compiler verification.

### `APKG-58`
Reproducible builds require deterministic dependency resolution.

### `APKG-59`
Dependency security policy is separate from language semantics.

### `APKG-60`
The final executable must have inspectable dependency provenance.

---

# Một điểm rất đáng chú ý

Đến đây Axiom đã có một mô hình khá sạch:

```text
                PACKAGE
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
      SOURCE     BINARY     SYSTEM
        │          │          │
        └──────┬───┘          │
               ↓              │
          COMPILER            │
               ↓              │
             OBJECT           │
               └──────┬───────┘
                      ↓
                    LINK
                      ↓
                 RUNTIME
                      ↓
                  BINARY
```

Và đặc biệt:

```text
Package dependency
        ≠
Compiler dependency
        ≠
Runtime dependency
        ≠
System dependency
```

Điều này bảo vệ trực tiếp mục tiêu ban đầu của Axiom.

---

# BOOTSTRAP-154 — FFI, C ABI, System ABI & Foreign Function Interface Safety

Đây là bước tiếp theo rất quan trọng.

Axiom muốn **không phụ thuộc third-party library**, nhưng không có nghĩa là phải tự viết lại toàn bộ thế giới. Nó cần khả năng gọi:

```text
Windows API
Linux syscalls
POSIX libraries
C libraries
C++
Objective-C / Swift ecosystem ở mức ABI phù hợp
Android NDK
GPU APIs
```

và cho phép ngôn ngữ khác gọi ngược Axiom.

Kiến trúc sẽ là:

```text
Axiom
   ↓
FFI Contract
   ↓
ABI Classification
   ↓
Representation Contract
   ↓
Foreign Declaration
   ↓
ABI MIR
   ↓
LIR
   ↓
Object
   ↓
System / Foreign Library
```

Đặc biệt sẽ chốt:

- `extern "C"`
- System ABI
- calling convention
- C-compatible structs/enums
- string/pointer ownership
- allocator boundary
- callback/function pointer
- variadic functions
- opaque handles
- `@repr(C)`
- error ABI
- thread/async FFI
- GPU FFI
- foreign memory
- foreign exceptions/unwind
- safety contracts
- symbol import/export
- dynamic loading
- ABI versioning

Đây là nơi Axiom sẽ phải **rất mạnh ở low-level**, nhưng vẫn giữ nguyên triết lý: **programmer không phải gánh pointer/lifetime complexity nếu compiler có thể quản lý nó.**