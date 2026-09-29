# BOOTSTRAP-591 — PACKAGE REGISTRY, DEPENDENCY RESOLUTION & SUPPLY-CHAIN PLATFORM 5.0
## PACKAGE INDEX, VERSION SOLVER, LOCKFILE, SOURCE/BINARY PACKAGES, NATIVE LIBRARIES, TARGET VARIANTS, ABI COMPATIBILITY, CONTENT-ADDRESSED STORAGE, SIGNATURES, PROVENANCE, OFFLINE MIRRORS & REPRODUCIBLE DEPENDENCY GRAPH

**Trạng thái: COMPLETED / LOCKED**

`591` hoàn thiện tầng package ecosystem của Axiom.

Mục tiêu không chỉ là “package manager”, mà là một **dependency platform có khả năng xác định chính xác artifact nào được đưa vào build**, vì sao nó được chọn, artifact đó đến từ đâu, ABI nào, target nào, compiler/toolchain nào và có thể xác minh/rebuild hay không.

```text
                         AXIOM PACKAGE PLATFORM
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
          Registry             Local Cache          Mirror
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  ▼
                         Dependency Resolver
                                  │
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
                   Source       Binary       Native
                   Package      Package      Package
                     │            │            │
                     └────────────┼────────────┘
                                  ▼
                         Verified Package Graph
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
             Signature        Provenance            ABI
                │                 │                 │
                └─────────────────┼─────────────────┘
                                  ▼
                         Reproducible Build
```

---

# 591.1. Package là gì?

Package là đơn vị phân phối source/metadata/artifact của Axiom.

```text
Package {
    identity
    version
    metadata
    source
    artifacts
    dependencies
    targets
    ABI
    provenance
    signatures
}
```

---

# 591.2. Package identity

Identity gồm:

```text
namespace
name
publisher
```

Version không phải một phần của logical package identity.

---

# 591.3. Canonical package name

Tên package phải:

- case-normalized theo rule;
- Unicode-safe nhưng hạn chế ambiguity;
- không chứa path traversal;
- deterministic.

---

# 591.4. Package namespace

Hỗ trợ namespace để tránh collision:

```text
axiom.graphics
company.network
org.example.audio
```

---

# 591.5. Package version

Axiom sử dụng semantic versioning-compatible model nhưng resolver phải hoạt động trên **ordered version constraints**, không hardcode assumption rằng mọi publisher tuân thủ semver hoàn hảo.

---

# 591.6. Version tuple

Canonical:

```text
major
minor
patch
pre_release
build_metadata
```

---

# 591.7. Version ordering

Ordering phải deterministic và được định nghĩa trong package specification.

---

# 591.8. Package manifest

Ví dụ khái niệm:

```toml
[package]
name = "graphics"
version = "2.4.1"

[dependencies]
math = "^3.1"
image = ">=1.2,<2"

[targets]
windows-x86_64 = true
linux-x86_64 = true
```

Syntax cuối cùng có thể thay đổi; semantic model này là bắt buộc.

---

# 591.9. Manifest identity

Manifest canonical serialization phải có hash.

---

# 591.10. Package content hash

Package identity hoàn chỉnh:

```text
PackageIdentity {
    name
    version
    content_hash
}
```

---

# 591.11. Version không đủ để identify artifact

Hai package cùng version nhưng content khác nhau phải được coi là **hai content identities khác nhau**.

---

# 591.12. Immutable release

Một registry chuẩn không được overwrite artifact đã publish.

---

# 591.13. Mutable development package

Development channel có thể thay đổi nhưng không được dùng cho reproducible release nếu content hash không được pin.

---

# 591.14. Package channels

Có thể hỗ trợ:

```text
stable
beta
nightly
dev
```

Channel là metadata resolver, không thay thế version identity.

---

# 591.15. Registry

Registry cung cấp:

```text
package metadata
version index
artifact locations
signatures
provenance
```

---

# 591.16. Registry không phải source of truth duy nhất

Build phải có thể hoạt động từ:

```text
registry
mirror
local cache
local path
git-like source
archive
```

nếu policy cho phép.

---

# 591.17. Registry index

Index có thể lưu:

```text
package
version
targets
dependencies
artifact hashes
signatures
```

---

# 591.18. Sparse index

Client không bắt buộc tải toàn bộ registry.

---

# 591.19. Package metadata query

Client có thể query:

```text
package name
version range
target
feature
```

---

# 591.20. Registry protocol

Protocol phải hỗ trợ:

```text
metadata lookup
artifact lookup
download
signature retrieval
provenance retrieval
```

---

# 591.21. Registry independence

Compiler core không phụ thuộc registry.

---

# 591.22. Resolver

Resolver nhận:

```text
RootManifest
Toolchain
Target
FeatureSet
RegistryIndex
Lockfile
```

và tạo:

```text
ResolvedGraph
```

---

# 591.23. Dependency graph

```text
Application
├── A
│   ├── C
│   └── D
└── B
    └── C
```

---

# 591.24. Graph node

Mỗi node chứa:

```text
package
version
content_hash
source
target_variant
features
```

---

# 591.25. Graph edge

Edge chứa:

```text
dependency
version_constraint
features
target_condition
optional
```

---

# 591.26. Direct dependency

Dependency được khai báo trực tiếp bởi project.

---

# 591.27. Transitive dependency

Dependency đến từ package khác.

---

# 591.28. Dev dependency

Chỉ dùng cho:

```text
tests
benchmarks
development tools
```

---

# 591.29. Build dependency

Dùng để chạy build-time code generator/tool.

---

# 591.30. Host dependency

Dependency build trên host.

---

# 591.31. Target dependency

Dependency được compile cho target.

---

# 591.32. Host/target separation

Một package có thể tồn tại đồng thời:

```text
package X / host
package X / target
```

nhưng chúng là các graph nodes khác nhau.

---

# 591.33. Build-time tool

Build tool phải được resolve theo:

```text host target
```

không phải application target.

---

# 591.34. Target-specific dependency

Ví dụ:

```toml
[target.linux.dependencies]
epoll = "..."

[target.windows.dependencies]
win32 = "..."
```

---

# 591.35. Conditional dependency

Conditions có thể dựa trên:

```text target
architecture
OS
ABI
features
profile
```

---

# 591.36. Feature flags

Package có thể khai báo:

```text
features = [
    "tls",
    "gui",
    "simd"
]
```

---

# 591.37. Feature resolution

Feature graph phải deterministic.

---

# 591.38. Feature unification

Resolver phải định nghĩa rõ feature của cùng package khi nhiều dependency yêu cầu khác nhau.

---

# 591.39. Optional dependency

Optional dependency chỉ được đưa vào graph khi feature tương ứng được enable.

---

# 591.40. Default features

Package có thể có default features nhưng lockfile phải record effective feature set.

---

# 591.41. Version constraint

Resolver hỗ trợ:

```text
exact
range
caret
tilde
>=
<=
>
<
```

và canonical normalized representation.

---

# 591.42. Exact version

```text
=2.4.1
```

---

# 591.43. Version range

```text
>=2.0,<3.0
```

---

# 591.44. Multiple constraints

Các constraint trên cùng package phải được intersection.

---

# 591.45. Conflict

Nếu:

```text
A → C 1.x
B → C 2.x
```

và graph policy không cho phép coexistence:

```text
resolution failure
```

---

# 591.46. Multiple versions

Axiom có thể cho phép nhiều version của cùng package khi ABI/type identity isolation bảo đảm không gây ambiguity.

---

# 591.47. Type identity across versions

Hai version package khác nhau không mặc định có cùng type identity.

---

# 591.48. Public dependency

Nếu package expose type của dependency trong public API, dependency trở thành ABI/API-relevant.

---

# 591.49. Private dependency

Dependency chỉ dùng implementation có thể được private.

---

# 591.50. Dependency visibility

Metadata phải phân biệt:

```text
public
private
build
dev
```

---

# 591.51. API dependency closure

Compiler/package verifier phải detect public API phụ thuộc package chưa được khai báo public dependency.

---

# 591.52. ABI dependency closure

Native binary package phải record toàn bộ ABI-relevant dependencies.

---

# 591.53. Lockfile

Lockfile là kết quả canonical của resolver.

```text
Lockfile {
    packages[]
    versions[]
    hashes[]
    sources[]
    features[]
    targets[]
    toolchain
    registry
}
```

---

# 591.54. Lockfile authority

Khi lockfile tồn tại và policy yêu cầu locked build, resolver phải ưu tiên graph trong lockfile.

---

# 591.55. Lockfile update

Dependency update phải là explicit operation.

---

# 591.56. Frozen mode

```text
axiom build --locked
```

không được sửa lockfile.

---

# 591.57. Update mode

```text
axiom update
```

mới được phép resolve graph mới.

---

# 591.58. Minimal update

Có thể update một package mà không thay đổi các package không liên quan nếu constraints vẫn thỏa mãn.

---

# 591.59. Lockfile deterministic ordering

Package entries phải được sort canonical.

---

# 591.60. Lockfile hash

Lockfile có canonical hash để provenance.

---

# 591.61. Content-addressed storage

Cache sử dụng:

```text
hash → artifact
```

thay vì chỉ:

```text
name/version → artifact
```

---

# 591.62. CAS object

```text
CASObject {
    hash
    size
    type
    content
}
```

---

# 591.63. Hash algorithm

Axiom package platform phải có canonical cryptographic hash algorithm.

Có thể hỗ trợ nhiều algorithm trong tương lai, nhưng package identity phải ghi rõ algorithm.

---

# 591.64. CAS deduplication

Hai package chứa cùng object có thể share storage.

---

# 591.65. Package archive

Archive format phải deterministic:

```text
canonical paths
canonical ordering
canonical metadata
```

---

# 591.66. Archive timestamp

Reproducible package không được phụ thuộc filesystem timestamps.

---

# 591.67. Archive permissions

Permissions phải canonicalized theo target-independent policy.

---

# 591.68. Package extraction

Không được cho phép:

```text
../
absolute path
symlink escape
```

---

# 591.69. Symlink policy

Symlink trong package phải explicit và không được escape package root.

---

# 591.70. Package sandbox

Build-time tools không mặc định được quyền tùy ý vào toàn bộ host filesystem.

---

# 591.71. Build script

Nếu Axiom hỗ trợ build script:

```text
build script
   ↓
declared inputs
   ↓
declared outputs
```

phải được kiểm soát.

---

# 591.72. Hermetic build

Reproducible mode yêu cầu build action có input set xác định.

---

# 591.73. Undeclared input

Build tool truy cập undeclared external input phải:

```text
error
```

hoặc explicit non-hermetic warning theo profile.

---

# 591.74. Environment capture

Build action phải record environment variables thực sự ảnh hưởng build nếu được phép dùng.

---

# 591.75. Time/randomness

Build không được phụ thuộc thời gian/randomness trong reproducible mode nếu không được explicitly seeded.

---

# 591.76. Network access

Build-time package scripts mặc định không được network access trong hermetic mode.

---

# 591.77. Native binary package

Package có thể chứa precompiled native artifacts.

```text
native/
 └── target/
      ├── lib
      ├── symbols
      └── metadata
```

---

# 591.78. Native package identity

Native artifact phải gắn:

```text
target
ABI
architecture
compiler-independent ABI metadata
content_hash
```

---

# 591.79. Source package

Source package chứa:

```text
source
manifest
semantic metadata optional
resources
build metadata
```

---

# 591.80. Binary Axiom package

Binary package có thể chứa:

```text
Axiom object
Axiom IR/LTO artifact
semantic metadata
debug metadata
```

---

# 591.81. LTO package

Package có thể phân phối LTO-compatible artifact.

---

# 591.82. LTO compatibility

LTO artifact phải pin:

```text
IR schema
compiler compatibility
ABI
optimization contract
```

---

# 591.83. Object-only package

Package có thể phân phối `.axo` object-like artifacts.

---

# 591.84. Native static library package

Ví dụ:

```text
libfoo.a
```

phải đi cùng ABI metadata.

---

# 591.85. Native shared library package

Ví dụ:

```text
foo.dll
libfoo.so
libfoo.dylib
```

phải có target-specific metadata.

---

# 591.86. Import library

Windows package có thể chứa:

```text
foo.lib
foo.dll
```

và metadata liên quan.

---

# 591.87. Framework package

Apple target có thể package framework metadata/artifacts.

---

# 591.88. WASM package

WASM package có thể chứa:

```text
module.wasm
imports.json
exports.json
```

---

# 591.89. ABI manifest

Native package phải có:

```text
ABIManifest {
    target
    ABI
    architecture
    calling_conventions
    layout_hash
    symbol_abi
}
```

---

# 591.90. Layout compatibility

Nếu package expose struct ABI, package phải record layout identity.

---

# 591.91. Struct layout hash

Hash được tạo từ:

```text
field order
field type
offset
size
alignment
packing
```

---

# 591.92. Function ABI identity

Function identity gồm:

```text
calling convention
parameter ABI
return ABI
symbol ABI
```

---

# 591.93. ABI mismatch

Resolver/linker phải reject incompatible native package.

---

# 591.94. ABI evolution

ABI version change phải được phản ánh trong package metadata.

---

# 591.95. Target matrix

Một package có thể có:

```text
Package
 ├── source
 ├── linux-x64
 ├── windows-x64
 ├── macos-arm64
 ├── ios-arm64
 └── wasm32
```

---

# 591.96. Variant selection

Resolver chọn variant phù hợp target.

---

# 591.97. Variant fallback

Nếu binary variant không tồn tại:

```text
binary unavailable
```

hoặc build source nếu source variant được phép.

---

# 591.98. Source fallback policy

Fallback phải explicit theo package policy.

---

# 591.99. Target-specific source

Package có thể chứa:

```text
src/common
src/linux
src/windows
src/arch/x86_64
```

---

# 591.100. Source selection

Compiler chỉ compile source phù hợp target conditions.

---

# 591.101. Architecture specialization

Có thể chọn:

```text
generic
x86_64
x86_64-avx2
aarch64
```

---

# 591.102. CPU-specific packages

CPU-specific binary không được dùng nếu target feature set không tương thích.

---

# 591.103. Feature compatibility

Resolver phải kết hợp:

```text package feature
target feature
CPU feature
```

---

# 591.104. Package metadata schema

Schema phải versioned.

---

# 591.105. Schema compatibility

Client cũ phải reject schema mới không hiểu thay vì parse sai.

---

# 591.106. Registry namespace ownership

Publisher identity phải được xác minh theo registry trust model.

---

# 591.107. Package publisher

Metadata:

```text
Publisher {
    id
    display_name
    keys[]
}
```

---

# 591.108. Package signing

Publisher có thể sign:

```text package manifest
artifact hash
release metadata
```

---

# 591.109. Signature verification

Resolver phải verify signature trước khi package được đánh dấu trusted nếu policy yêu cầu.

---

# 591.110. Signature does not equal safety

Signature chỉ xác nhận publisher/key relationship.

Không tự động xác nhận source quality hoặc absence of bugs.

---

# 591.111. Trust policy

Project có thể yêu cầu:

```text
trusted publisher
trusted key
unsigned allowed
signed required
```

---

# 591.112. Key rotation

Publisher có thể rotate signing key.

---

# 591.113. Key revocation

Compromised key phải có revocation mechanism.

---

# 591.114. Transparency

Registry có thể lưu release transparency metadata.

---

# 591.115. Provenance

Package provenance phải record:

```text
source revision
build system
compiler
toolchain
target
dependencies
build recipe
```

---

# 591.116. Provenance graph

```text
Source
  ↓
Build Action
  ↓
Compiler
  ↓
Dependencies
  ↓
Artifact
```

---

# 591.117. Compiler trust integration

Provenance có thể reference compiler trust state `587`.

---

# 591.118. Trusted build

Package có thể được đánh dấu:

```text
source-verified
reproducible
bootstrap-verified
```

nhưng các trạng thái phải độc lập.

---

# 591.119. Reproducible package

Publisher có thể cung cấp rebuild instructions.

---

# 591.120. Independent rebuild

Consumer có thể rebuild package từ source và compare artifact hash.

---

# 591.121. Reproducibility result

```text
match
mismatch
not-tested
```

---

# 591.122. Binary transparency

Package metadata có thể expose:

```text source_hash
artifact_hash
build_hash
toolchain_hash
```

---

# 591.123. Registry mirror

Mirror phải giữ nguyên:

```text package identity
content hash
signature
provenance
```

---

# 591.124. Mirror trust

Mirror không được tự sửa artifact.

---

# 591.125. Mirror verification

Client verify hash/signature sau download.

---

# 591.126. Multiple mirrors

Resolver có thể retry mirror khác nếu artifact hash không match.

---

# 591.127. Local registry

Developer có thể chạy local registry.

---

# 591.128. Enterprise/private registry

Registry có thể yêu cầu authentication.

---

# 591.129. Authentication boundary

Credential không được đưa vào compiler command line hoặc artifact metadata.

---

# 591.130. Offline mirror

Một mirror có thể export thành offline package repository.

---

# 591.131. Air-gapped package set

Có thể tạo:

```text
axiom bundle \
    project.lock \
    --offline
```

để gom toàn bộ dependency graph.

---

# 591.132. Bundle completeness

Bundle phải chứa mọi artifact cần để resolve locked graph.

---

# 591.133. Missing dependency preflight

Build offline phải kiểm tra completeness trước compile.

---

# 591.134. Package cache garbage collection

Cache GC chỉ được xóa object không còn referenced.

---

# 591.135. Reference counting in CAS

Logical references:

```text
lockfile
artifact
workspace
```

có thể giữ CAS objects alive.

---

# 591.136. Cache corruption

CAS object hash mismatch phải được quarantine/delete.

---

# 591.137. Partial download

Partial artifact không được xuất hiện như valid CAS object.

---

# 591.138. Atomic CAS commit

```text
download
 ↓
verify hash
 ↓
atomic rename
 ↓
index
```

---

# 591.139. Package extraction cache

Extracted source phải có content identity.

---

# 591.140. Source normalization

Package hash phải xác định rõ:

```text file bytes
metadata
archive representation
```

để tránh hash ambiguity.

---

# 591.141. Path canonicalization

Package paths dùng `/` canonical representation.

---

# 591.142. Case collision

Package không được chứa hai paths khác nhau chỉ khác case nếu target filesystem có thể gây collision.

---

# 591.143. Unicode path normalization

Package specification phải canonicalize hoặc reject ambiguous Unicode paths.

---

# 591.144. License metadata

Package manifest có thể record:

```text
license
license_files
notice
```

---

# 591.145. License không phải compiler semantics

License metadata không ảnh hưởng type checking/linking trừ khi policy toolchain yêu cầu.

---

# 591.146. Security advisory

Registry có thể cung cấp advisory:

```text
package
affected_versions
fixed_versions
severity
```

---

# 591.147. Advisory policy

Build system có thể:

```text
ignore
warn
fail
```

theo project policy.

---

# 591.148. Vulnerability identity

Security advisory có stable identifier.

---

# 591.149. Dependency audit

CLI:

```text
axiom audit
```

có thể báo:

```text
direct dependency
transitive dependency
version
advisory
```

---

# 591.150. Audit không thay đổi graph

Audit chỉ phân tích; không tự update dependency.

---

# 591.151. Dependency update

```text
axiom update package-name
```

là mutation transaction.

---

# 591.152. Update preview

Resolver phải có thể xuất diff:

```text
A 1.2 → 1.3
B unchanged
C 4.0 → 4.1
```

---

# 591.153. Semver compatibility warning

Nếu major version thay đổi, resolver có thể cảnh báo API compatibility risk.

---

# 591.154. API compatibility metadata

Package có thể cung cấp public API fingerprint.

---

# 591.155. ABI compatibility metadata

Native package có ABI fingerprint.

---

# 591.156. API diff

Tooling có thể compare:

```text public symbols
types
functions
traits
ABI
```

giữa package versions.

---

# 591.157. Breaking change declaration

Publisher có thể declare intended breaking change.

---

# 591.158. Resolver does not trust declaration blindly

Compiler vẫn kiểm tra ABI/type compatibility ở nơi có thể.

---

# 591.159. Dependency graph snapshot

Resolved graph có canonical serialization.

---

# 591.160. Graph hash

```text
DependencyGraphHash =
Hash(canonical resolved graph)
```

---

# 591.161. Build identity

Build identity bao gồm:

```text
source revision
dependency graph hash
toolchain hash
target
configuration
```

---

# 591.162. Artifact identity

Artifact identity:

```text
Artifact {
    build_id
    content_hash
}
```

---

# 591.163. Package reproducibility chain

```text
Source Hash
     ↓
Manifest Hash
     ↓
Dependency Graph Hash
     ↓
Toolchain Hash
     ↓
Build Action Hash
     ↓
Artifact Hash
```

---

# 591.164. Package graph and build graph

Package graph xác định **what**.

Build graph xác định **how**.

Hai graph liên kết bằng package artifact identity.

---

# 591.165. Build graph integration

`487/568` nhận resolved package graph làm input immutable.

---

# 591.166. No hidden dependency

Compiler không được tự động tìm package ngoài resolved graph.

---

# 591.167. Import resolution

`import foo` phải map tới package/module đã resolve.

---

# 591.168. Package/module distinction

Package là distribution unit.

Module là source semantic unit.

Một package có thể chứa nhiều modules.

---

# 591.169. Package namespace

Module path phải canonicalize cùng package identity.

---

# 591.170. Public API export

Package có thể chỉ export một subset modules.

---

# 591.171. Package prelude

Nếu có prelude, nó phải explicit trong package metadata.

---

# 591.172. Package initialization

Native/runtime initialization phải được biểu diễn trong dependency graph.

---

# 591.173. Native link ordering

Package metadata có thể khai báo native link requirements nhưng linker vẫn quyết định final deterministic ordering.

---

# 591.174. Link search path isolation

Package không được tự ý inject host library search paths.

---

# 591.175. System libraries

System libraries được reference bằng target SDK identity.

---

# 591.176. System package

Platform library có thể được model như package đặc biệt:

```text
platform.windows.kernel32
platform.linux.libc
```

---

# 591.177. Platform package trust

Platform packages inherit SDK trust/provenance.

---

# 591.178. FFI package

FFI package có:

```text
Axiom declarations
ABI metadata
native artifact
```

---

# 591.179. FFI ABI verification

Build phải kiểm tra declaration ABI với native package metadata nếu metadata có đủ thông tin.

---

# 591.180. Unsafe FFI

Nếu verification không đủ:

```text
unsafe extern
```

phải được yêu cầu theo policy.

---

# 591.181. Package target matrix validation

Publisher tooling phải có thể validate:

```text
all declared target variants
```

---

# 591.182. Partial target support

Package có thể chỉ support một subset target.

---

# 591.183. Unsupported target error

Error phải nêu:

```text package
target
available targets
```

---

# 591.184. Cross compilation package

Source package phải có thể được build trên host khác target.

---

# 591.185. Build dependency cross compilation

Build tool được build cho host, application code cho target.

---

# 591.186. Proc/build plugin

Nếu package cung cấp code generator:

```text
generator = host artifact
generated code = target source
```

---

# 591.187. Generator trust

Generator phải chịu supply-chain policy giống package khác.

---

# 591.188. Generator determinism

Reproducible mode yêu cầu generator deterministic.

---

# 591.189. Generator output identity

Generated output được hash và đưa vào build graph.

---

# 591.190. Package build sandbox

Build scripts/generators có thể được giới hạn:

```text filesystem
network
environment
process
```

---

# 591.191. Capability declaration

Package build tool khai báo capability:

```text
filesystem-read
filesystem-write
network
process
```

---

# 591.192. Permission escalation

Build tool không được tự nâng capability.

---

# 591.193. User approval

Non-hermetic package build có thể yêu cầu explicit approval.

---

# 591.194. Package policy

Project có policy:

```toml
[security]
require_signatures = true
allow_network_build = false
allow_unsigned = false
```

---

# 591.195. Policy inheritance

Workspace policy có thể áp dụng xuống package graph.

---

# 591.196. Policy override

Dependency không được override policy của root project.

---

# 591.197. Registry selection

Project có thể pin registry:

```text
registry = "official"
```

hoặc private registry.

---

# 591.198. Registry priority

Nếu nhiều registry:

```text explicit registry
>
project registry
>
workspace registry
>
global registry
```

---

# 591.199. Dependency confusion protection

Package identity phải bao gồm registry/namespace provenance khi policy yêu cầu để tránh package cùng tên từ registry khác bị thay thế ngoài ý muốn.

---

# 591.200. Final package architecture

```text id="pkgfinal591"
                        PROJECT
                           │
                           ▼
                    Root Manifest
                           │
                           ▼
                    Version Resolver
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
          Registry Index           Lockfile
               │                       │
               └───────────┬───────────┘
                           ▼
                    Resolved Graph
                           │
                ┌──────────┼──────────┐
                ▼          ▼          ▼
             Source     Binary      Native
                │          │          │
                └──────────┼──────────┘
                           ▼
                         CAS
                           │
                     Verification
                           │
          ┌────────┬───────┼───────┬────────┐
          ▼        ▼       ▼       ▼        ▼
        Hash    Signature ABI  Provenance Policy
          │        │       │       │        │
          └────────┴───────┼───────┴────────┘
                           ▼
                    Build Graph 487/568
                           │
                           ▼
                    Native Artifact
```

---

# 591.201. CLI contract

Toolchain phải cung cấp tối thiểu:

```text
axiom pkg search <name>
axiom pkg info <name>
axiom pkg add <name>
axiom pkg remove <name>
axiom pkg update
axiom pkg tree
axiom pkg verify
axiom pkg cache
axiom pkg bundle
axiom audit
```

Tên command có thể được gom lại thành `axiom package`, nhưng semantic operations trên phải tồn tại.

---

# 591.202. Machine-readable output

Mọi package operation phải có:

```text
--json
```

hoặc canonical machine-readable equivalent.

---

# 591.203. Resolver diagnostics

Conflict phải hiển thị dependency chain:

```text
App
 ├── A requires C >=2
 └── B requires C <2

Resolution conflict: C
```

---

# 591.204. Minimal conflict explanation

Không chỉ báo:

```text
dependency resolution failed
```

mà phải cho biết path gây conflict.

---

# 591.205. Solver determinism

Cùng:

```text graph
constraints
registry snapshot
policy
```

phải tạo cùng resolution.

---

# 591.206. Registry snapshot

Reproducible resolution phải có registry metadata snapshot hoặc immutable package index identity.

---

# 591.207. Registry mutation safety

Nếu registry thay đổi sau lockfile creation, locked build không được tự chọn package mới.

---

# 591.208. Package deletion

Registry có thể tombstone package nhưng locked artifacts đã cache vẫn phải build được nếu policy cho phép.

---

# 591.209. Yanked release

Version có thể bị yanked khỏi resolver mới nhưng không làm invalid lockfile cũ.

---

# 591.210. Package deprecation

Deprecation là metadata; không tự động thay dependency.

---

# 591.211. Package ownership transfer

Transfer phải preserve package identity và provenance chain.

---

# 591.212. Publisher key transition

Ownership/key changes phải có signed transition metadata.

---

# 591.213. Package recovery

Nếu registry unavailable:

```text
lockfile
+
local CAS
+
offline bundle
```

phải đủ để build.

---

# 591.214. Cache trust

Local cache không được mặc định trusted chỉ vì artifact đã tồn tại.

Hash/signature/provenance policy vẫn áp dụng.

---

# 591.215. Dependency quarantine

Artifact verification fail phải chuyển vào quarantine, không đưa vào active cache.

---

# 591.216. Package malware boundary

Package platform phải có security scanning integration point, nhưng scanner không trở thành semantic dependency của compiler.

---

# 591.217. Static package analysis

Package verifier có thể chạy:

```text
manifest validation
ABI validation
artifact validation
dependency audit
permission analysis
```

---

# 591.218. Runtime package metadata

Package có thể khai báo runtime requirements:

```text
threads
filesystem
network
GPU
GUI
```

---

# 591.219. Capability-aware dependency

Package có thể yêu cầu capability, và target/runtime phải satisfy trước build.

---

# 591.220. Final dependency closure

Resolved project phải có closure đầy đủ:

```text
source
build tools
runtime
native libraries
SDK
target
```

---

# 591.221. Package graph immutability

Sau khi build action bắt đầu, resolved dependency graph của action không được thay đổi.

---

# 591.222. Concurrent package operations

Hai process có thể cùng tải package nhưng CAS phải remain atomic và corruption-safe.

---

# 591.223. Lock contention

Package manager phải tránh global lock quá rộng; chỉ lock metadata/index/object đang mutate.

---

# 591.224. Package garbage collection safety

GC không được xóa object đang được build action sử dụng.

---

# 591.225. Build lease

Build action có thể giữ lease/reference trên CAS objects.

---

# 591.226. Remote cache

Remote CAS có thể được dùng cho package artifacts nhưng phải verify content hash.

---

# 591.227. Remote package artifact

Remote artifact không được trusted chỉ vì URL đúng.

---

# 591.228. Transport security

Registry transport có thể dùng TLS nhưng artifact integrity vẫn phải verify bằng content hash/signature.

---

# 591.229. Package metadata cache

Metadata cache phải có expiration/revalidation policy.

---

# 591.230. Locked build metadata

Locked build phải tránh phụ thuộc metadata mutable ngoài lockfile.

---

# 591.231. Package source archive

Source archive phải giữ nguyên source hash sau extraction.

---

# 591.232. Source-to-binary provenance

Binary package có thể record source package identity.

---

# 591.233. Binary-only package

Binary-only package phải được phép nhưng provenance có thể thiếu source rebuild capability.

---

# 591.234. Trust state

Package trust state:

```text
Unknown
VerifiedHash
SignatureVerified
ProvenanceVerified
ReproduciblyVerified
Revoked
```

---

# 591.235. Trust monotonicity

Verification state không được tự nâng cấp chỉ vì package được tải nhiều lần.

---

# 591.236. Revocation precedence

`Revoked` luôn override trust states thấp hơn.

---

# 591.237. Dependency trust policy

Root project có thể yêu cầu:

```text
all packages signed
```

hoặc chỉ trust selected namespaces.

---

# 591.238. Native code warning

Package chứa native code phải được distinguish với pure Axiom source package.

---

# 591.239. Native package permissions

Project có thể policy:

```text
allow_native = false
```

cho sandboxed environments.

---

# 591.240. Source package compilation

Nếu native artifact không phù hợp target nhưng source tồn tại, resolver có thể chọn source build theo policy.

---

# 591.241. Binary preference

Có thể prefer prebuilt binary để giảm build time.

---

# 591.242. Reproducible source preference

Release verification environment có thể prefer source build để verify publisher artifact.

---

# 591.243. Package optimization

Resolver có thể chọn artifact:

```text
debug
release
size
speed
```

theo build profile.

---

# 591.244. Optimization variant identity

Optimization variant phải là artifact metadata, không phải implicit mutable state.

---

# 591.245. Debug package selection

Debug build phải resolve matching debug artifacts.

---

# 591.246. Symbol package

Native package có thể tách:

```text
binary
symbols
source
```

---

# 591.247. Debug/source association

Symbol/source package phải reference exact build identity.

---

# 591.248. Package resource files

Resources có thể được package nhưng phải có target-aware packaging rules.

---

# 591.249. Generated assets

Generated resources phải có deterministic generator identity.

---

# 591.250. Package publication pipeline

```text
Source
 ↓
Validate
 ↓
Build
 ↓
Test
 ↓
ABI/API check
 ↓
Generate provenance
 ↓
Hash
 ↓
Sign
 ↓
Publish
```

---

# 591.251. Publication validation

Registry client phải refuse publish nếu package manifest inconsistent.

---

# 591.252. Package certification

Certification có thể là external metadata, không phải language semantic.

---

# 591.253. Package compatibility matrix

Publisher có thể publish:

```text
package × target × compiler ABI
```

matrix.

---

# 591.254. Compiler minimum version

Package có thể khai báo minimum compiler version.

---

# 591.255. Compiler maximum compatibility

Package có thể khai báo tested compiler range.

---

# 591.256. Language edition

Package phải declare language edition.

---

# 591.257. Edition migration

Dependency package có thể sử dụng edition khác với root project nếu compiler supports multi-edition compilation.

---

# 591.258. Package API documentation

Registry metadata có thể link generated API docs.

---

# 591.259. Semantic metadata package

Package có thể ship precomputed semantic metadata để IDE không cần parse source.

---

# 591.260. Semantic metadata trust

Semantic metadata phải được associate với exact package content hash.

---

# 591.261. AI package metadata

Package có thể ship machine-readable:

```text
API graph
examples
capabilities
constraints
```

nhưng metadata không được override compiler semantics.

---

# 591.262. AI package discovery

AI tooling có thể query package semantic metadata thay vì đọc toàn bộ source.

---

# 591.263. Package usage analysis

IDE có thể hiển thị:

```text
which APIs used
which dependency introduced
```

---

# 591.264. Unused dependency

Analyzer có thể detect dependency không được sử dụng.

---

# 591.265. Dependency pruning

Removal phải là explicit refactoring.

---

# 591.266. Dependency impact graph

IDE có thể show:

```text
package X
 ↓
modules
 ↓
symbols
 ↓
application
```

---

# 591.267. License impact graph

Tooling có thể trace license metadata qua dependency graph.

---

# 591.268. Security impact graph

Tương tự cho advisories.

---

# 591.269. Supply-chain report

`axiom audit --json` có thể xuất:

```text
package
version
hash
source
publisher
signature
provenance
advisories
```

---

# 591.270. SBOM integration

Package platform có thể export SBOM nhưng SBOM format không được trở thành compiler core dependency.

---

# 591.271. Package archive portability

Package archive phải có thể chuyển giữa OS mà không phụ thuộc filesystem semantics của host.

---

# 591.272. Native artifact portability

Native artifact chỉ valid cho target/ABI tương ứng.

---

# 591.273. Universal package

Một package có thể chứa nhiều target variants.

---

# 591.274. Universal package verification

Mỗi variant phải verify độc lập.

---

# 591.275. Package signing scope

Signature có thể cover:

```text entire package
individual artifact
manifest
provenance
```

Scope phải explicit.

---

# 591.276. Signature algorithm agility

Package format phải cho phép thay signing algorithm mà không thay semantic package model.

---

# 591.277. Hash algorithm agility

Tương tự content hash.

---

# 591.278. Registry API versioning

Registry protocol có version độc lập với package schema.

---

# 591.279. Client compatibility

Client cũ phải gracefully reject unsupported registry protocol features.

---

# 591.280. Package platform API

Core API:

```text
PackageIndex
PackageResolver
PackageStore
PackageVerifier
PackageRegistry
PackageBuilder
PackagePublisher
```

---

# 591.281. PackageStore

Quản lý:

```text
download
extract
CAS
GC
verification
```

---

# 591.282. PackageResolver

Chỉ quyết định graph.

Không tự compile package.

---

# 591.283. PackageBuilder

Biến resolved package thành build actions.

---

# 591.284. PackageVerifier

Kiểm tra:

```text
hash
signature
manifest
ABI
target
provenance
```

---

# 591.285. PackagePublisher

Đóng gói và publish artifact.

---

# 591.286. RegistryServer

Official/private registry có thể implement:

```text
index
artifact store
signature store
provenance store
```

---

# 591.287. Registry database

Metadata database không cần lưu toàn bộ artifact bytes nếu artifact store riêng.

---

# 591.288. Artifact CDN

Artifact có thể được serve từ CDN miễn content hash được verify.

---

# 591.289. Download resume

Large package downloads phải hỗ trợ resume.

---

# 591.290. Download integrity

Resume phải verify final content hash.

---

# 591.291. Parallel download

Resolver/store có thể tải nhiều artifacts song song.

---

# 591.292. Resource-aware download

Bandwidth/CPU/storage limits phải configurable.

---

# 591.293. Package prefetch

IDE có thể prefetch dependencies nhưng không được mutate locked graph.

---

# 591.294. Background resolution

IDE có thể resolve metadata background.

---

# 591.295. Background download

Background downloads phải respect network/privacy policy.

---

# 591.296. Package update notification

IDE có thể thông báo package update nhưng không tự động mutate dependencies.

---

# 591.297. Dependency lock regeneration

Lockfile regeneration phải deterministic.

---

# 591.298. Lockfile conflict

Concurrent lockfile modifications phải detect.

---

# 591.299. Workspace package

Workspace package có thể được reference bằng path nhưng release package phải canonicalize thành package identity.

---

# 591.300. Path dependency

Path dependency:

```text
path = "../core"
```

phù hợp development nhưng release/reproducible build phải record content identity.

---

# 591.301. Git-like dependency

Nếu hỗ trợ source repository dependency, phải record:

```text
repository identity
revision
content hash
```

---

# 591.302. Floating branch dependency

Không được dùng cho reproducible locked build.

---

# 591.303. Local override

Developer có thể override dependency:

```text
[patch]
```

nhưng build identity phải record override.

---

# 591.304. Override provenance

Artifact được build từ override không được masquerade thành official package artifact.

---

# 591.305. Dependency graph visualization

IDE phải visualize:

```text
direct
transitive
host
target
optional
native
```

---

# 591.306. Circular dependency

Package cycle phải được phát hiện.

---

# 591.307. Allowed cycles

Nếu package model cho phép một số cycle, build graph phải distinguish package cycle với module cycle.

---

# 591.308. Build cycle diagnostics

Cycle report phải show complete path.

---

# 591.309. Package initialization cycle

Runtime initialization dependencies phải được validate riêng.

---

# 591.310. Dependency order

Resolver output order canonical nhưng build scheduler có thể parallelize independent nodes.

---

# 591.311. Rebuild minimization

Package graph change chỉ invalidate affected build nodes.

---

# 591.312. Package ABI change

ABI change phải invalidate dependent native artifacts.

---

# 591.313. Source implementation change

Nếu public ABI không đổi, binary cache có thể reuse theo policy.

---

# 591.314. Semantic API fingerprint

Package build metadata có thể record public API fingerprint.

---

# 591.315. ABI fingerprint

Native package record ABI fingerprint.

---

# 591.316. Cache correctness

Cache reuse phải dựa trên complete input identity, không chỉ package version.

---

# 591.317. No stale artifact substitution

Artifact từ target/configuration khác không được reuse.

---

# 591.318. Final package build pipeline

```text
Manifest
   ↓
Normalize
   ↓
Resolve
   ↓
Lock
   ↓
Verify
   ↓
Fetch
   ↓
Materialize
   ↓
Build Graph
   ↓
Compile
   ↓
Link
   ↓
Verify Artifact
```

---

# 591.319. FINAL HARD INVARIANTS

### Invariant 1 — immutable identity

> Package version không đủ để xác định artifact; content identity phải được bảo toàn.

### Invariant 2 — deterministic resolution

> Cùng package constraints, registry snapshot, policy và target phải tạo cùng resolved graph.

### Invariant 3 — locked build

> Locked build không được tự thay đổi dependency graph.

### Invariant 4 — target isolation

> Artifact chỉ được sử dụng khi target/architecture/ABI tương thích.

### Invariant 5 — no hidden dependency

> Compiler/build graph không được tự động lấy dependency ngoài resolved graph.

### Invariant 6 — source/binary equivalence

> Source package và prebuilt binary package phải có identity/provenance rõ ràng; binary không được giả dạng source-built artifact nếu provenance không chứng minh được.

### Invariant 7 — CAS integrity

> Artifact chỉ được đưa vào CAS sau khi content hash được xác minh.

### Invariant 8 — signature separation

> Signature xác thực publisher/key; hash xác thực content; provenance xác định build origin. Ba khái niệm không được nhập làm một.

### Invariant 9 — policy inheritance

> Dependency không được tự hạ security/reproducibility policy của root project.

### Invariant 10 — hermeticity

> Reproducible build phải có input closure xác định và không phụ thuộc undeclared host state.

### Invariant 11 — native ABI

> Native package phải mang đủ metadata để linker/compiler có thể xác định target và ABI compatibility.

### Invariant 12 — offline

> Locked dependency graph có đầy đủ local artifacts phải build được mà không cần registry/network.

### Invariant 13 — provenance

> Mỗi release artifact có thể truy ngược tới source/build/toolchain/dependency identity nếu publisher khai báo provenance.

### Invariant 14 — cache correctness

> Không được reuse artifact chỉ vì package name/version giống nhau.

### Invariant 15 — resolver/build separation

> Resolver quyết định dependency graph; build engine thực thi graph; compiler không được tự quyết định dependency resolution.

---

# 591 — LOCKED

Chuỗi hiện tại đã đạt:

```text
587  Bootstrap Trust
 ↓
588  Toolchain / SDK
 ↓
589  Native Debugger
 ↓
590  Unified IDE
 ↓
591  Package Ecosystem
```

Axiom bây giờ không còn chỉ là một language/compiler specification. Nó đã có kiến trúc cho một **complete native development platform**:

```text
                 ┌─────────────────────────┐
                 │       AXIOM PLATFORM    │
                 └────────────┬────────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
   Language               Compiler               Runtime
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              ▼
                         Toolchain
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                   SDK      Linker    Debugger
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                             IDE
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
             Package        Build           AI
             Registry       Graph        Workspace
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                       Native Applications
```

# NEXT — BOOTSTRAP-592

## DISTRIBUTED PACKAGE BUILD & BINARY CACHE PLATFORM 5.0
### REMOTE PACKAGE BUILDS, CONTENT-ADDRESSED BUILD CACHE, PREBUILT ARTIFACT DISTRIBUTION, TRUSTED REMOTE WORKERS, CACHE VALIDATION, CROSS-TARGET ARTIFACT REUSE, BUILD FARM, PRIORITY SCHEDULING & ZERO-REBUILD DEVELOPMENT

```text
                         Axiom Build
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
                Local DAG        Remote DAG
                    │                 │
                    └────────┬────────┘
                             ▼
                    Content-Addressed Cache
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
        Local Cache      Remote Cache      Package Cache
             │               │                │
             └───────────────┼────────────────┘
                             ▼
                       Verified Artifact
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
          Compiler         Linker          Packager
             │               │                │
             └───────────────┼────────────────┘
                             ▼
                       Final Artifact
```

`592` sẽ tập trung vào một mục tiêu quan trọng còn thiếu: **sau khi package graph đã deterministic ở `591`, làm thế nào Axiom có thể build cực nhanh bằng cache và remote workers mà vẫn giữ nguyên các invariant về reproducibility, trust, target isolation và compiler verification của `567`, `587` và `591`.`