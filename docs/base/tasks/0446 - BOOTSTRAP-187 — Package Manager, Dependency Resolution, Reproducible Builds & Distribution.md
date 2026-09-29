# BOOTSTRAP-187 — Package Manager, Dependency Resolution, Reproducible Builds & Distribution
**FROZEN / COMPLETED**

Mục tiêu của phần này là hoàn thiện chuỗi:

```text
source
  ↓
package graph
  ↓
resolved dependencies
  ↓
.axmeta / cache
  ↓
object
  ↓
link
  ↓
native binary
```

và đảm bảo **package manager không trở thành runtime dependency**.

---

## 187.1. Package là đơn vị phân phối

Axiom phân biệt:

```text
Package
Module
Library
Binary
Artifact
Workspace
```

Package là đơn vị dependency/distribution.

Module là đơn vị source organization.

Library là artifact có thể link/use.

---

## 187.2. Package identity

Package identity gồm:

```text
PackageId =
    Name
    Version
    SourceIdentity
```

Ví dụ:

```text
crypto@2.4.1
```

không đồng nhất với:

```text
crypto@3.0.0
```

---

## 187.3. Source identity

Version không đủ xác định source.

Ví dụ:

```text
crypto@1.2.0
```

từ:

```text
registry A
git repository B
local path C
```

là các source identities khác nhau.

---

## 187.4. Package checksum

Resolved package có content fingerprint:

```text
PackageContentHash
```

được tính từ nội dung canonical của package.

---

## 187.5. Lockfile

Project có:

```text
axiom.lock
```

ghi:

```text
package
version
source
content hash
dependencies
features
target conditions
```

---

## 187.6. Lockfile là reproducibility contract

Khi lockfile tồn tại:

```text
axc build
```

không được tự ý chọn dependency version khác.

Muốn update:

```text
axc update
```

---

## 187.7. Semantic version resolution

Version resolution có thể theo:

```text
major.minor.patch
```

nhưng resolver phải dựa trên dependency constraint.

Ví dụ:

```text
^1.4
```

cho phép một range được định nghĩa rõ trong package specification.

---

## 187.8. Resolver deterministic

Cùng:

```text
manifest
lockfile
registry state
platform
features
```

phải tạo cùng dependency graph.

Không phụ thuộc thứ tự download.

---

## 187.9. Dependency graph

Graph:

```text
App
├── GUI
│   ├── Image
│   └── Font
└── Network
    └── TLS
```

mỗi node có package identity riêng.

---

## 187.10. Dependency cycles

Ordinary package dependency cycle:

```text
A → B → A
```

bị reject.

---

## 187.11. Cyclic runtime architecture

Nếu hai package cần nhau về logic, phải tách:

```text
A
B
Common
```

hoặc sử dụng interface boundary phù hợp.

Package resolver không giải quyết circular dependency bằng cách “cho qua”.

---

## 187.12. Dev dependency

Package có thể có:

```text
dependencies
dev-dependencies
build-dependencies
```

Dev dependency không xuất hiện trong final executable nếu không được sử dụng bởi production graph.

---

## 187.13. Build dependency

Build-time tool:

```text
code generator
IDL compiler
resource compiler
```

là build dependency, không phải runtime dependency.

---

## 187.14. Runtime dependency

Chỉ library thực sự được link/use mới trở thành runtime/native dependency.

---

## 187.15. Dependency graph ≠ link graph

Một package dependency có thể chỉ cung cấp:

```text
compile-time metadata
```

và không tạo native link dependency.

---

## 187.16. Comptime dependency

Package dùng:

```text
comptime
```

có thể cần compiler metadata nhưng không cần runtime code.

Đây là điểm giúp Axiom giữ binary nhỏ.

---

## 187.17. Feature resolution

Features phải được resolve trước semantic compilation:

```text
features
 ↓
conditional declarations
 ↓
API graph
 ↓
type checking
```

Không được để feature thay đổi giữa các module trong cùng package instance.

---

## 187.18. Feature unification

Trong một dependency graph, cùng một package instance phải có feature set xác định.

Không để:

```text
A → lib(features=x)
B → lib(features=y)
```

rồi linker phải đoán semantics.

---

## 187.19. Feature variants

Nếu thực sự cần hai configuration khác nhau:

```text
lib@1 + feature-set-A
lib@1 + feature-set-B
```

phải trở thành hai package instances có identity riêng.

---

## 187.20. Target conditions

Dependency có thể:

```text
windows only
linux only
wasm only
gpu only
```

Resolver xử lý trước build.

---

## 187.21. Cross compilation

Một project có thể:

```text
host = Windows x64
target = Linux x64
```

Build dependency và target dependency phải được phân biệt.

---

## 187.22. Host vs target

Ví dụ:

```text
build generator
```

chạy trên host.

Code generated:

```text
```

chạy trên target.

Không được nhầm hai environment.

---

## 187.23. Build environment identity

Artifact identity chứa:

```text
HostTarget
Target
Compiler
Features
ComptimeInputs
```

khi chúng ảnh hưởng semantics/codegen.

---

## 187.24. Native target descriptor

Target descriptor:

```text
Target {
    OS
    Architecture
    ABI
    PointerWidth
    Endianness
    CPUFeatures
    ObjectFormat
}
```

---

## 187.25. Target triple

Axiom có thể hỗ trợ target triple/quadruple tương thích ecosystem:

```text
x86_64-windows-msvc
x86_64-linux-gnu
aarch64-linux
wasm32
```

nhưng target identity nội bộ nên semantic hơn string parsing đơn thuần.

---

## 187.26. SDK

Platform SDK là dependency ngoài:

```text
Windows SDK
Android NDK
Apple SDK
Vulkan SDK
```

Axiom build graph có thể reference chúng.

---

## 187.27. SDK không phải package runtime

SDK chỉ cung cấp:

```text
headers
libraries
metadata
tools
```

theo target.

Executable không chứa SDK manager.

---

## 187.28. System library

Ví dụ:

```text
libc
kernel32
user32
libm
```

là system dependencies.

Package manager không nhất thiết download chúng.

---

## 187.29. System dependency contract

Manifest có thể khai báo:

```text
system-library = "..." 
```

kèm:

```text
minimum version
ABI
required symbols
```

---

## 187.30. Optional system dependency

Ví dụ:

```text
GUI
 └── optional Vulkan
```

Nếu feature không dùng:

```text
Vulkan
```

không xuất hiện trong link graph.

---

## 187.31. Static vs dynamic

Package có thể cung cấp:

```text
static
dynamic
both
```

Build policy quyết định.

---

## 187.32. Link mode

Không nên hard-code:

```text
static = always
dynamic = always
```

vì platform policy khác nhau.

Manifest có thể yêu cầu:

```text
prefer-static
prefer-dynamic
static-only
dynamic-only
```

---

## 187.33. Native artifact

Package có thể phát hành:

```text
libfoo.axlib
libfoo.a
foo.lib
foo.dll
libfoo.so
```

theo target.

---

## 187.34. Axiom library artifact

Đề xuất:

```text
.axlib
.axmeta
```

Ví dụ:

```text
foo-2.1.0-x86_64-linux.axlib
foo-2.1.0-x86_64-linux.axmeta
```

---

## 187.35. `.axlib`

`.axlib` là package/library artifact semantic của Axiom.

Nó có thể chứa:

```text
native object
generic code metadata
optimization summaries
ABI metadata
link requirements
```

---

## 187.36. `.axmeta`

`.axmeta` là interface/compiler metadata.

Không nhất thiết chứa machine code.

---

## 187.37. Binary-only package

Có thể phát hành:

```text
foo.axlib
foo.axmeta
```

không phát hành source.

---

## 187.38. Source package

Cũng có:

```text
foo.axpkg
```

chứa source + manifest + metadata cần thiết.

---

## 187.39. Package format

Định dạng archive nên deterministic:

```text
manifest
source
metadata
licenses
checksums
native artifacts
```

với canonical ordering.

---

## 187.40. Package archive reproducibility

Hai package build từ cùng content phải tạo cùng archive bytes trong reproducible mode.

Timestamp tùy tiện không được lọt vào content hash.

---

## 187.41. Source normalization

Không normalize source theo cách thay đổi semantics.

Fingerprint dựa trên canonical representation đã được định nghĩa.

---

## 187.42. Generated files

Generated code là một dependency của build graph.

Ví dụ:

```text
schema
 ↓
generator
 ↓
generated.ax
 ↓
compiler
```

---

## 187.43. Generated source fingerprint

Thay đổi generator hoặc input:

```text
GeneratedFingerprint changed
```

→ rebuild.

---

## 187.44. Comptime inputs

Như BOOTSTRAP-185 đã xác định, filesystem/environment/tool output dùng trong comptime phải trở thành build dependency.

---

## 187.45. Reproducible comptime

Build reproducible mode hạn chế:

```text
current time
random
network
environment
```

nếu chúng ảnh hưởng output.

---

## 187.46. Network trong build

Build mặc định không nên tùy tiện truy cập Internet.

Dependency acquisition thuộc package manager.

Comptime network là capability explicit.

---

## 187.47. Offline mode

```text
axc build --offline
```

không network.

Nếu dependency chưa có local:

```text
error: dependency unavailable
```

---

## 187.48. Frozen dependency cache

Cache local:

```text
~/.axiom/cache/
```

được content-addressed.

---

## 187.49. Content-addressed cache

Ví dụ:

```text
sha256/<hash>
```

thay vì:

```text
foo/latest/
```

---

## 187.50. Cache correctness

Cache hit chỉ hợp lệ nếu fingerprint đầy đủ:

```text
source
dependencies
compiler semantic version
target
features
comptime inputs
ABI
codegen configuration
```

---

## 187.51. Compiler cache

Cache chia:

```text
parse
resolve
typecheck
HIR
MIR
metadata
codegen
link
```

để incremental build.

---

## 187.52. Semantic cache

Nếu public API unchanged:

```text
.axmeta
```

có thể reuse.

---

## 187.53. Codegen cache

Nếu implementation unchanged và codegen config unchanged:

```text
object
```

có thể reuse.

---

## 187.54. Link cache

Executable cuối cùng có thể cache nếu:

```text
object graph
link flags
libraries
target
linker
```

không đổi.

---

## 187.55. Linker fingerprint

Link result identity phải bao gồm linker semantic/tool version khi output phụ thuộc vào nó.

---

## 187.56. Reproducible executable

Reproducible mode phải loại bỏ:

```text
build timestamps
random IDs
machine paths
nondeterministic ordering
```

khỏi semantic output hoặc canonicalize chúng.

---

## 187.57. Debug paths

Absolute source path không nên làm binary reproducibility bị phá nếu debug metadata có thể dùng:

```text
path remapping
```

---

## 187.58. Build ID

Executable có thể có:

```text
BuildId
```

nhưng BuildId phải được định nghĩa rõ:

```text
content identity
```

không phải random UUID.

---

## 187.59. Reproducible Build ID

Cùng inputs:

```text
same BuildId
```

trong reproducible mode.

---

## 187.60. Source verification

Lockfile có:

```text
content hash
```

để phát hiện source bị thay đổi.

---

## 187.61. Registry

Axiom registry chỉ là distribution service.

Compiler không phụ thuộc registry khi package đã được resolve/cache.

---

## 187.62. Multiple registries

Manifest có thể khai báo registry source.

Registry identity thuộc package source identity.

---

## 187.63. Private registry

Enterprise/self-hosted registry được hỗ trợ.

Không tạo semantic difference trong package.

---

## 187.64. Git dependency

Có thể:

```text
git = ...
revision = ...
```

nhưng lockfile phải pin revision/content.

---

## 187.65. Path dependency

Local:

```text
path = "../foo"
```

được phép.

Source content fingerprint vẫn cần tính.

---

## 187.66. Git branch không đủ

Không lock:

```text
branch = main
```

làm immutable dependency identity.

Phải resolve tới commit/revision cụ thể.

---

## 187.67. Local unpublished package

Có thể build package chưa publish:

```text
workspace
path dependency
```

không cần registry.

---

## 187.68. Workspace

Monorepo:

```text
workspace
├── compiler
├── std
├── gui
├── tools
└── app
```

chia sẻ:

```text
lockfile
cache
build configuration
```

---

## 187.69. Workspace package identity

Mỗi package vẫn có identity riêng.

Workspace không biến chúng thành một package semantic khổng lồ.

---

## 187.70. Shared source

Không nên cho phép cùng một source file thuộc nhiều package identity mà không explicit.

Tránh duplicate semantic identities.

---

## 187.71. Package exports

Manifest có thể chỉ rõ:

```text
exports
modules
binaries
native libraries
```

---

## 187.72. Package visibility

Không phải file nào trong package cũng public.

Public API vẫn theo visibility rules của compiler.

---

## 187.73. Build script

Axiom có thể hỗ trợ build program:

```text
build.ax
```

nhưng phải coi nó là **external build execution**.

---

## 187.74. Build script sandbox

Build script mặc định có capabilities hạn chế:

```text
read package
write generated directory
inspect target
```

Network/tool execution phải explicit.

---

## 187.75. Build script reproducibility

Build script output phải được fingerprint.

---

## 187.76. Build script không chạy runtime

Sau build:

```text
build.ax
```

không được link vào executable trừ khi programmer explicit sử dụng code của nó.

---

## 187.77. Native build tools

Nếu package cần:

```text
protoc
shader compiler
resource compiler
```

đó là build tools.

Tool version phải tham gia build identity.

---

## 187.78. Shader build

GPU project:

```text
Axiom source
 ↓
shader generation
 ↓
SPIR-V / DXIL / Metal
```

artifact graph phải tracking shader compiler/version.

---

## 187.79. Resource compiler

GUI/assets:

```text
png
svg
font
shader
model
```

có thể là build inputs.

---

## 187.80. Embedded resources

Nếu resource được embed:

```text
resource hash
```

tham gia executable identity.

---

## 187.81. License metadata

Package distribution metadata có thể chứa:

```text
license
copyright
attribution
```

nhưng không ảnh hưởng program semantics.

---

## 187.82. Security signing

Package có thể được ký:

```text
PackageSignature
```

Signing không thay đổi PackageContentHash.

---

## 187.83. Signature verification

Tooling có thể yêu cầu:

```text
trusted registry
trusted publisher
signature required
```

---

## 187.84. Supply-chain policy

Project có thể policy:

```text
no unsigned dependency
allowlisted registries
locked source
offline only
```

---

## 187.85. Compiler trust

Compiler không mặc định coi package signature là semantic truth.

Signature chỉ xác thực origin/integrity.

---

## 187.86. Dependency provenance

Tooling có thể hiển thị:

```text
App
 ↓
GUI
 ↓
Image
 ↓
zlib
 ↓
system library
```

---

## 187.87. Dependency audit

CLI:

```text
axc tree
axc audit
axc why package
axc explain dependency
```

---

## 187.88. Unused dependency

Dependency không được dùng có thể warning:

```text
unused dependency
```

nhưng không phải compiler error mặc định.

---

## 187.89. Unused native library

Nếu library không tạo referenced symbols:

```text
linker section/symbol GC
```

có thể loại bỏ.

---

## 187.90. Runtime minimization

Package manager không quyết định runtime components.

Compiler/linker quyết định dựa trên actual references/effects.

---

## 187.91. Example

Project:

```text
App
├── std::io
├── math
└── gui
```

nhưng code chỉ dùng:

```text
math
```

thì final binary không cần:

```text
GUI runtime
```

chỉ vì dependency tồn tại.

---

## 187.92. Optional dependency

```text
gui = optional
```

không được link khi feature không activate.

---

## 187.93. Static initialization

Package không được mặc định có hidden global constructors.

Nếu cần initialization:

```text
explicit initialization
```

hoặc compiler-known mechanism.

Điều này giữ startup nhỏ và deterministic.

---

## 187.94. Package startup

Không có:

```text
package constructor registry
```

toàn cục.

---

## 187.95. Plugin exception

Plugin system có thể có explicit initialization contract:

```text
load
initialize
use
shutdown
unload
```

---

## 187.96. Package-level comptime

Package có thể generate declarations tại compile time nhưng generated output phải đi qua normal compiler pipeline.

---

## 187.97. Dependency metadata

Dependent compiler cần:

```text
public API
traits
generic metadata
ABI
effects
FFI contracts
target conditions
```

chứ không nhất thiết cần source.

---

## 187.98. Binary-only generic package

Nếu package muốn downstream generic specialization, nó phải export generic metadata/code representation phù hợp.

---

## 187.99. ABI-only binary

Nếu package chỉ expose concrete ABI functions:

```text
minimal metadata
```

là đủ.

---

## 187.100. Distribution tiers

Có thể có:

```text
source package
binary package
development package
runtime package
```

nhưng runtime package chỉ tồn tại khi application thực sự cần.

---

## 187.101. SDK package

Platform SDK có thể được represented như package metadata:

```text
windows.sdk
android.sdk
apple.sdk
```

nhưng actual SDK files có thể do system cung cấp.

---

## 187.102. Vendor mode

```text
axc vendor
```

copy dependency sources/artifacts vào project:

```text
vendor/
```

để build offline hoàn toàn.

---

## 187.103. Vendored dependencies

Vendor lock:

```text
source
hash
version
```

không phụ thuộc registry availability.

---

## 187.104. Hermetic build

Build hermetic có:

```text
fixed source
fixed compiler
fixed target
fixed dependencies
fixed tools
fixed environment
```

---

## 187.105. Reproducible ≠ hermetic

Reproducible:

```text
same declared inputs
→ same result
```

Hermetic:

```text
undeclared external state
→ cannot affect result
```

Axiom hỗ trợ cả hai profile.

---

## 187.106. Build profiles

Đề xuất:

```text
dev
release
size
debug
reproducible
freestanding
```

---

## 187.107. Size profile

```text
axc build --profile size
```

ưu tiên:

```text
dead stripping
runtime elimination
LTO
function/data sections
compression where appropriate
```

nhưng không thay đổi semantics.

---

## 187.108. Fast build profile

```text
dev
```

có thể giảm:

```text
LTO
whole-program optimization
```

để compile nhanh.

---

## 187.109. Release profile

Ưu tiên:

```text
optimization
LTO
specialization
vectorization
```

---

## 187.110. Reproducible profile

Không cho phép nondeterministic codegen decisions nếu chúng ảnh hưởng output identity.

---

## 187.111. PGO

Profile data là build input:

```text
profile fingerprint
```

tham gia artifact identity.

---

## 187.112. Cache + PGO

Không reuse optimized artifact nếu profile thay đổi.

---

## 187.113. Compiler version

Compiler semantic version tham gia cache identity.

Compiler bugfix không ảnh hưởng semantics vẫn có thể invalidation rộng hơn nếu codegen output có thể thay đổi.

---

## 187.114. Semantic compiler version

Phân biệt:

```text
CompilerVersion
CompilerSemanticVersion
CodegenVersion
```

để cache chính xác.

---

## 187.115. Bootstrap compiler

Trong bootstrap:

```text
Axiom compiler
→ LLVM/LLD
```

có thể là build tool.

---

## 187.116. Self-hosted compiler

Sau self-host:

```text
Axiom compiler
→ Axiom compiler
```

không cần third-party compiler để build compiler release.

---

## 187.117. Trust bootstrap

Bootstrap chain cần có:

```text
Stage0
 ↓
Stage1
 ↓
Stage2
```

và compiler output có thể được kiểm tra bằng reproducible/deterministic build.

---

## 187.118. Compiler bootstrap artifact

Stage compiler được xem là build dependency, không phải runtime dependency của user application.

---

## 187.119. Package manager implementation

Package manager ban đầu có thể viết bằng:

```text
Rust/C++/Go/etc.
```

nhưng cuối cùng có thể self-host bằng Axiom.

Không ảnh hưởng language semantics.

---

## 187.120. Package manager executable

`ax` / `axc` không được link vào application.

---

## 187.121. Final build chain

```text
ax manifest
     ↓
resolver
     ↓
lockfile
     ↓
package graph
     ↓
CompilerDB
     ↓
.axmeta
     ↓
MIR
     ↓
codegen
     ↓
linker
     ↓
app.exe
```

---

# 187.122. Package manager và compiler phải tách

Đây là quyết định quan trọng.

```text
Package Manager
    = dependency/distribution

Compiler
    = semantic compilation

Linker
    = binary composition
```

Không gộp thành một giant runtime system.

---

# 187.123. Dependency resolution không thay đổi semantics

Resolver chọn package instance.

Compiler quyết định semantics của package instance.

---

# 187.124. Package metadata không được override source semantics

Manifest không thể nói:

```text
T behaves like U
```

nếu source/compiler không chứng minh điều đó.

---

# 187.125. Build manifest không phải programming language

Manifest chỉ mô tả:

```text
dependencies
features
targets
artifacts
build configuration
```

Không nên trở thành một ngôn ngữ Turing-complete khác.

---

# 187.126. Build configuration determinism

Cùng manifest + lockfile + inputs:

```text
same dependency graph
```

---

# 187.127. Artifact identity

Artifact fingerprint:

```text
ArtifactId =
    PackageContentHash
    DependencyGraphFingerprint
    CompilerSemanticVersion
    Target
    ABI
    Features
    ComptimeInputs
    BuildProfile
    CodegenFingerprint
```

---

# 187.128. Cache correctness invariant

Không được cache-hit chỉ vì:

```text
package name + version
```

---

# 187.129. Source authenticity

Hash xác định content.

Signature xác định publisher/trust.

Hai khái niệm khác nhau.

---

# 187.130. Distribution independence

Executable:

```text
app.exe
```

không cần:

```text
axiom package manager
axiom registry
lockfile
```

để chạy.

---

# 187.131. Runtime independence

Package manager không được tạo:

```text
package runtime
```

---

# 187.132. Minimal deployment

Application có thể được deploy chỉ với:

```text
app.exe
```

hoặc:

```text
app
+ explicitly required dynamic libraries
```

---

# 187.133. Container deployment

Container có thể copy:

```text
binary
required dynamic libs
assets
```

không cần package manager.

---

# 187.134. Static deployment

Nếu target/platform cho phép:

```text
single binary
```

là mục tiêu hợp lệ.

---

# 187.135. Cross-platform package

Một package có thể chứa artifacts:

```text
windows/x64
linux/x64
linux/arm64
macos/arm64
wasm
```

nhưng resolver chỉ chọn target phù hợp.

---

# 187.136. Artifact selection

Không download toàn bộ platform artifacts nếu registry có thể cung cấp target-specific package.

---

# 187.137. Dependency pruning

Feature/target resolution xảy ra trước build để giảm dependency graph.

---

# 187.138. Build graph pruning

Unused packages không được compile.

---

# 187.139. Module pruning

Unused modules có thể không được semantic compile nếu không reachable.

---

# 187.140. Declaration pruning

Unused declarations:

```text
DCE
```

ở compiler/linker.

---

# 187.141. Package ≠ runtime component

Đây là một trong những nguyên tắc quan trọng nhất:

```text
dependency graph
    X
runtime graph
```

không phải cùng một graph.

---

# 187.142. Package graph → compiler graph

Compiler chỉ nhận những package instances cần thiết cho target/profile.

---

# 187.143. Foreign dependency

FFI package:

```text
foo-ffi
```

có thể chỉ chứa:

```text
.axffi
.axmeta
```

và link tới system library.

---

# 187.144. Native binary fingerprint

Native library content hash tham gia dependency identity.

Nếu:

```text
libfoo.so
```

thay đổi:

```text
ABI dependency may have changed
```

build system phải invalidate artifact phù hợp.

---

# 187.145. ABI validation

Nếu `.axmeta` có ABI fingerprint của native dependency, build system có thể detect mismatch sớm.

---

# 187.146. System library uncertainty

Nếu system library do OS cung cấp và version không cố định, reproducibility tuyệt đối cần:

```text
SDK/sysroot pinning
```

---

# 187.147. Sysroot

Cross compilation nên hỗ trợ pinned:

```text
sysroot
SDK
headers
libraries
```

---

# 187.148. Reproducible native linking

Để reproducible binary, cần cố định:

```text
linker
sysroot
native libs
target
```

---

# 187.149. Build manifest example

Conceptual:

```text
package:
    name = "app"
    version = "1.0.0"

dependencies:
    gui = "2.1"
    image = "1.4"

features:
    gpu = []

targets:
    windows:
        system = ["user32"]
```

Đây chỉ là minh họa semantic model; syntax manifest sẽ được chốt ở build-system specification riêng.

---

# 187.150. Lockfile example

Conceptual:

```text
gui 2.1.3
source = registry:main
hash = ...

image 1.4.2
source = registry:main
hash = ...
```

---

# 187.151. Build command model

Core commands nên xoay quanh:

```text
ax init
ax build
ax run
ax test
ax check
ax update
ax fetch
ax clean
ax tree
ax vendor
ax package
ax publish
```

Compiler primitive vẫn có thể:

```text
axc compile
axc link
```

---

# 187.152. `check`

```text
ax check
```

thực hiện:

```text
parse
resolve
typecheck
ownership verification
```

nhưng không nhất thiết codegen/link.

---

# 187.153. `build`

Full:

```text
check
→ codegen
→ link
```

---

# 187.154. `run`

Build nếu cần rồi execute target.

---

# 187.155. `test`

Tests là package/build profile đặc biệt.

Không phải runtime framework bắt buộc của production binary.

---

# 187.156. Toolchain manifest

Project có thể pin:

```text
Axiom compiler channel/version
```

để reproducible builds.

---

# 187.157. Toolchain isolation

Compiler installation:

```text
system
user
project-local
CI
```

độc lập package graph.

---

# 187.158. Offline bootstrap

Một project đã vendor đầy đủ có thể:

```text
ax build --offline
```

không network.

---

# 187.159. Air-gapped build

Axiom phải hỗ trợ môi trường:

```text
no Internet
no registry
```

nếu toàn bộ inputs đã được vendor/cache.

---

# 187.160. Final invariant set

### Package Identity

- **APKG-20** — Package identity is distinct from module identity.
- **APKG-21** — Package identity includes source identity.
- **APKG-22** — Different package versions have distinct semantic identities.
- **APKG-23** — Package content is content-addressable.
- **APKG-24** — Re-export does not create a new package/type identity.

### Dependency Resolution

- **ADEP-20** — Dependency resolution is deterministic.
- **ADEP-21** — Resolved dependencies are pinned by lockfile when reproducibility is requested.
- **ADEP-22** — Cyclic ordinary package dependencies are rejected.
- **ADEP-23** — Feature resolution occurs before semantic compilation.
- **ADEP-24** — Host and target dependency environments are distinct.
- **ADEP-25** — Target-specific dependencies participate only in compatible target graphs.
- **ADEP-26** — Dependency graph and runtime/link graph are distinct.
- **ADEP-27** — Unused dependencies do not automatically become runtime dependencies.

### Build

- **ABUILD-20** — Build configuration is not part of runtime semantics.
- **ABUILD-21** — Build-time tools are not runtime dependencies unless explicitly linked.
- **ABUILD-22** — Generated code participates in the build dependency graph.
- **ABUILD-23** — Comptime external inputs participate in build identity.
- **ABUILD-24** — Build artifacts are invalidated when any semantic input changes.
- **ABUILD-25** — Offline builds cannot silently access the network.
- **ABUILD-26** — Reproducible mode requires deterministic declared inputs.
- **ABUILD-27** — Hermetic mode rejects undeclared external influences.
- **ABUILD-28** — PGO data participates in artifact identity.

### Cache

- **ACACHE-20** — Cache identity is content/semantic based.
- **ACACHE-21** — Package name/version alone is insufficient for cache identity.
- **ACACHE-22** — Compiler semantic version participates in semantic artifact identity.
- **ACACHE-23** — Target, ABI, features, and relevant codegen configuration participate in artifact identity.
- **ACACHE-24** — Cache reuse cannot change program semantics.
- **ACACHE-25** — Incremental artifacts retain source/semantic provenance.

### Distribution

- **ADIST-20** — Package manager is not a runtime dependency.
- **ADIST-21** — Executables can run without access to the package registry.
- **ADIST-22** — Package signatures verify origin/integrity but do not override compiler semantics.
- **ADIST-23** — Source hash and publisher signature are distinct concepts.
- **ADIST-24** — Binary-only packages are supported.
- **ADIST-25** — Native system libraries are explicit dependencies.
- **ADIST-26** — Static/dynamic linking is an explicit build policy.
- **ADIST-27** — Distribution artifacts may be target-specific.
- **ADIST-28** — Vendored dependencies support air-gapped/offline builds.

### Minimal Runtime

- **ARUNTIMEPKG-20** — Package dependencies do not imply runtime components.
- **ARUNTIMEPKG-21** — Unused runtime components are removable.
- **ARUNTIMEPKG-22** — Package tooling is never implicitly linked into application binaries.
- **ARUNTIMEPKG-23** — Application deployment contains only explicitly required runtime/native dependencies.

---

# BOOTSTRAP-187 đã hoàn tất

Đến đây Axiom đã có gần như toàn bộ **vertical architecture** từ source tới binary:

```text
                    AXIOM
                      │
             ┌────────┴────────┐
             │                 │
        Language Core       Ecosystem
             │                 │
       Type / Trait       Package Manager
             │             Dependency Graph
 Ownership / Capability       Lockfile
             │             Reproducible Build
       MIR / Verify              │
             │                   │
       Optimization              │
             │                   │
       ABI / LIR                 │
             └─────────┬─────────┘
                       ↓
                Native Backend
                       ↓
                Object Writer
                       ↓
                    Linker
                       ↓
                EXE / ELF / Mach-O
                       ↓
                 Minimal Runtime
```

---

# BOOTSTRAP-188 — Testing, Conformance, Formal Semantics & Compiler Correctness

Bước tiếp theo nên đi vào một phần cực kỳ quan trọng trước khi tiếp tục mở rộng tính năng:

> **Làm thế nào để chứng minh compiler Axiom không âm thầm biến một chương trình hợp lệ thành chương trình có semantics sai sau hàng trăm optimization pass?**

Đây không chỉ là unit test.

Ta cần chốt:

```text
Language Specification
        ↓
Reference Semantics
        ↓
Conformance Suite
        ↓
Compiler
        ↓
MIR Verification
        ↓
Optimization Validation
        ↓
Backend Validation
        ↓
Differential Testing
        ↓
Fuzzing
        ↓
Translation Validation
        ↓
Binary Execution Tests
```

Đặc biệt BOOTSTRAP-188 sẽ phải giải quyết những vấn đề rất khó:

- semantic oracle của Axiom
- executable specification
- reference interpreter
- MIR interpreter
- compiler self-check
- AST/HIR/MIR differential testing
- property-based testing
- fuzzing parser/typechecker/borrow-capability verifier
- ownership adversarial tests
- concurrency litmus tests
- memory-model tests
- async state-machine tests
- GPU legality tests
- FFI ABI tests
- cross-target conformance
- optimizer miscompilation detection
- Alive-style IR validation
- translation validation
- randomized compiler testing
- metamorphic testing
- deterministic compiler testing
- bootstrap compiler comparison
- self-host compiler validation
- **“unsafe” không được trở thành vùng không thể test**
- và cuối cùng là **Axiom Language Conformance Suite v0.1**.

Đây sẽ là lớp bảo vệ cuối cùng trước khi Axiom tiếp tục đi vào những subsystem lớn hơn.