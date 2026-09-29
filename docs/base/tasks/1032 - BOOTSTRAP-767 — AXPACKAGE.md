# BOOTSTRAP-767 — AXPACKAGE

**Title:** Native Package, Module Artifact, Dependency, Manifest, Repository, Version Resolution, Installation, Cache, Upgrade & Reproducible Package Runtime 5.0  
**Namespace:** `AXPACKAGE`  
**Phase:** Axiom Civilization Runtime / Native Package & Distribution Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXPACKAGE` chuẩn hóa cách Axiom đóng gói, phân phối và quản lý:

- source modules;
- compiled modules;
- static libraries;
- dynamic libraries;
- executables;
- schemas;
- resources;
- documentation;
- metadata;
- platform artifacts;
- dependency declarations.

Mục tiêu quan trọng:

> **Package management là lớp phân phối, không phải điều kiện để compiler hoạt động.**

Axiom phải vẫn có thể:

```text
source
 ↓
axiom compiler
 ↓
native executable
```

hoàn toàn offline và không cần package repository.

---

# 2. Boundary

`AXPACKAGE` sở hữu:

- package identity;
- package manifest;
- module packaging;
- dependency graph;
- package versions;
- artifact variants;
- repository abstraction;
- local cache;
- installation;
- upgrade;
- rollback;
- lockfile;
- package integrity;
- package provenance metadata;
- reproducible package resolution.

Không sở hữu:

```text
compiler → AXCOMPILER
linker → AXBUILD / linker subsystem
runtime execution → AXPROCESS
authorization → AXSECURITY
identity → AXIDENTITY
network transport → AXNETWORK
storage primitives → AXSTORAGE
cryptographic primitives → AXCRYPTO
service discovery → AXREGISTRY
```

---

# 3. Architecture

```text id="pkgarch"
                    AXPACKAGE
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Manifest      Resolver       Repository
          │             │             │
          ▼             ▼             ▼
      Package ID    Dependency     Artifact
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                      Cache
                        │
                 ┌──────┴──────┐
                 ▼             ▼
              Install       Build
                 │             │
                 ▼             ▼
              Runtime      Compiler
```

---

# 4. Package identity

Canonical identity:

```text id="pkgid"
package_id {
    namespace
    name
    publisher
    identity
}
```

Package name không phải security identity.

---

# 5. Package name

Package name phải:

- UTF-8;
- normalized;
- namespace-qualified;
- case policy explicit;
- deterministic.

Ví dụ:

```text id="pkgname"
com.axiom.graphics
com.example.database
```

---

# 6. Package version

```text id="pkgver"
package_version {
    major
    minor
    patch
    pre_release
    build
}
```

Version comparison phải deterministic.

---

# 7. Package version vs ABI version

Phải phân biệt:

```text id="versions"
package version
API version
ABI version
schema version
artifact version
```

Package update không mặc nhiên có nghĩa ABI compatibility.

---

# 8. Manifest

Canonical manifest:

```text id="manifest"
package {
    identity
    version
    description
    license
    modules
    dependencies
    artifacts
    targets
    capabilities
    schemas
    resources
    metadata
}
```

---

# 9. Manifest format

Axiom nên có canonical binary manifest:

```text id="binmanifest"
AXPMANIFEST_1
```

và text representation để con người/AI chỉnh sửa.

Text format không phải canonical runtime ABI.

---

# 10. Manifest determinism

Equivalent manifests phải canonicalize thành cùng logical representation trước hashing/signing.

---

# 11. Package content

Một package có thể chứa:

```text id="content"
source
object
static_library
dynamic_library
executable
debug_symbols
schema
resource
documentation
compiler_metadata
AI_metadata
```

---

# 12. Artifact

Artifact descriptor:

```text id="artifact"
artifact {
    artifact_id
    kind
    target
    architecture
    abi
    content_hash
    size
    dependencies
}
```

---

# 13. Target triple

Artifact phải khai báo target:

```text id="target"
os
architecture
abi
environment
```

Ví dụ:

```text id="targets"
windows-x86_64
linux-x86_64
linux-arm64
macos-arm64
ios-arm64
android-arm64
wasm32
```

---

# 14. CPU features

Artifact có thể yêu cầu:

```text id="cpufeatures"
sse4
avx2
avx512
neon
```

Resolver phải tránh chọn artifact không chạy được trên target.

---

# 15. Feature variants

Package có thể có:

```text id="variants"
generic
optimized
debug
profile
gpu
nogpu
```

Resolver chọn variant dựa trên target/profile.

---

# 16. Dependency

Dependency:

```text id="dep"
dependency {
    package
    version_constraint
    features
    target
    optional
}
```

---

# 17. Dependency graph

```text id="graph"
Application
 ├── A
 │    ├── C
 │    └── D
 └── B
      └── C
```

Resolver phải canonicalize shared dependencies.

---

# 18. Dependency cycle

Cycle:

```text id="cycle"
A → B
B → A
```

phải được detect.

Nếu package format cho phép cycles ở một số metadata-only dependency, semantics phải explicit.

---

# 19. Dependency kinds

```text id="depKinds"
BUILD
RUNTIME
OPTIONAL
DEV
TEST
TOOL
PLATFORM
```

---

# 20. Build dependency

Chỉ cần trong build graph.

Không tự đóng gói vào runtime artifact nếu không required.

---

# 21. Runtime dependency

Executable/dynamic library phải khai báo dependency runtime cần thiết.

---

# 22. Optional dependency

Optional dependency phải có explicit feature/condition.

Không silently resolve optional package thành mandatory runtime requirement.

---

# 23. Platform dependency

Ví dụ:

```text id="platformdep"
Windows-only
Linux-only
ARM64-only
```

Resolver đánh giá trước installation.

---

# 24. Feature flags

Package features:

```text id="features"
features {
    gui
    gpu
    sqlite
    networking
}
```

Feature resolution phải deterministic.

---

# 25. Feature unification

Nếu nhiều dependencies yêu cầu cùng package với features khác nhau:

```text id="unify"
A → C(feature-x)
B → C(feature-y)
```

resolver phải có defined unification semantics.

---

# 26. Feature conflict

Nếu:

```text id="conflict"
feature-x
feature-y
```

không compatible:

```text id="featureerror"
PACKAGE_FEATURE_CONFLICT
```

---

# 27. Lockfile

Reproducible builds cần:

```text id="lock"
axiom.lock
```

Lockfile pin:

- package;
- exact version;
- artifact hash;
- source/repository;
- dependency graph;
- features;
- target.

---

# 28. Lockfile purpose

Manifest:

```text id="manifest2"
what I need
```

Lockfile:

```text id="lock2"
exact resolution used
```

---

# 29. Lockfile determinism

Cùng:

```text manifest
+
lockfile
+
toolchain
+
target
```

phải resolve cùng package graph.

---

# 30. Repository

Repository abstraction:

```text id="repo"
repository {
    repository_id
    endpoint
    authority
    protocol
    capabilities
}
```

Repository không phải compiler dependency.

---

# 31. Repository types

```text id="repotypes"
LOCAL
FILESYSTEM
HTTP
NETWORK
GIT_LIKE
OBJECT_STORE
MIRROR
AIR_GAPPED
```

Protocol adapters thuộc package infrastructure.

---

# 32. Local repository

Offline:

```text id="localrepo"
./packages/
```

có thể resolve package mà không network.

---

# 33. Cache

Package cache:

```text id="cache"
repository
    ↓
download
    ↓
content-addressed cache
```

---

# 34. Content-addressed storage

Package artifacts được key bằng:

```text id="cas"
hash(content)
```

thay vì chỉ filename/version.

---

# 35. Deduplication

Nếu hai packages chứa cùng artifact:

```text id="dedup"
same content hash
      ↓
same stored blob
```

giảm disk usage.

---

# 36. Integrity

Artifact download:

```text id="integrity"
download
 ↓
hash
 ↓
expected hash
 ↓
accept/reject
```

---

# 37. Cryptographic hash

Integrity hash sử dụng primitive từ `AXCRYPTO`.

AXPACKAGE không tự phát minh hash algorithm.

---

# 38. Signature

Package có thể có:

```text id="signature"
package_signature {
    signer
    algorithm
    signature
    signed_manifest_hash
}
```

Signature verification dùng AXCRYPTO/AXTRUST.

---

# 39. Signature vs integrity

Hash:

```text id="hashvsig"
integrity
```

Signature:

```text id="sig"
integrity + signer authenticity
```

Không đánh đồng hai khái niệm.

---

# 40. Trust

Package signature có thể được kiểm tra:

```text id="trust"
signature
 ↓
AXTRUST
 ↓
trusted / untrusted
```

AXPACKAGE không tự định nghĩa global trust policy.

---

# 41. Package provenance

Manifest có thể chứa:

```text id="provenance"
source_revision
build_id
builder
toolchain
target
build_timestamp
dependencies
```

---

# 42. Reproducible builds

Build metadata phải hỗ trợ:

```text id="repro"
source
toolchain
compiler version
flags
dependency lock
target
```

để reproduce artifact.

---

# 43. Build timestamp

Nếu artifact cần reproducibility:

```text id="buildtime"
```

timestamp phải được normalized hoặc excluded khỏi content identity.

---

# 44. Build environment

Package provenance có thể record:

```text id="env"
compiler
linker
target
feature set
environment profile
```

Không bắt buộc record secret environment variables.

---

# 45. Artifact hash

Artifact identity:

```text id="arthash"
artifact_id
content_hash
```

không phụ thuộc URL download location.

---

# 46. Package hash

Canonical package identity hash:

```text id="pkghash"
canonical_manifest
+
artifact references
+
metadata
```

---

# 47. Installation

Canonical flow:

```text id="install"
manifest
 ↓
resolve
 ↓
verify
 ↓
download
 ↓
integrity check
 ↓
stage
 ↓
activate
```

---

# 48. Atomic installation

Không expose half-installed package.

```text id="atomicinstall"
staging
 ↓
validate
 ↓
commit
 ↓
active
```

---

# 49. Installation generations

Package installation state:

```text id="gen"
generation
revision
```

giúp rollback và concurrent readers.

---

# 50. Rollback

```text id="rollback"
current v2
    ↓
rollback
    ↓
v1
```

Rollback phải atomic.

---

# 51. Upgrade

```text id="upgrade"
v1
 ↓
resolve v2
 ↓
verify
 ↓
stage
 ↓
compatibility validation
 ↓
activate v2
```

---

# 52. Failed upgrade

Nếu activation fail:

```text id="failupgrade"
v1 remains active
```

không để package manager ở trạng thái partial.

---

# 53. Uninstall

Uninstall chỉ được remove package khi dependency graph không còn yêu cầu nó hoặc caller explicit force semantics được authorized.

---

# 54. Orphan packages

Cache có thể giữ artifact không còn referenced.

Garbage collection của package cache:

```text id="pkgcachegc"
roots
 ↓
mark referenced
 ↓
remove unreferenced
```

Không phải language GC.

---

# 55. Offline build

Axiom compiler phải support:

```text id="offline"
axiom build --offline
```

với tất cả dependencies đã cache.

---

# 56. No-network compiler

Compiler phải có mode:

```text id="nonet"
network = disabled
```

và không tự truy cập Internet.

---

# 57. Build isolation

Package build scripts không được mặc định có unrestricted:

- network;
- filesystem;
- process;
- device.

Capability policy quyết định.

---

# 58. Build scripts

Package có thể cần native build steps.

Nếu hỗ trợ:

```text id="buildscript"
build_script
```

nó phải là explicit package component.

---

# 59. Build script security

Build script execution thuộc AXSECURITY sandbox.

Không mặc định chạy arbitrary package code với developer privileges.

---

# 60. Package resources

Resources:

```text id="resources"
icons
fonts
models
schemas
translations
templates
```

có manifest declarations.

---

# 61. Runtime resource access

Package resource API:

```text id="resource"
package_resource_open()
package_resource_read()
```

Storage implementation thuộc AXSTORAGE.

---

# 62. Module layout

Package có thể chứa:

```text id="modulelayout"
src/
modules/
include/
lib/
bin/
resources/
schemas/
docs/
```

Nhưng layout vật lý không được là ABI requirement.

---

# 63. Module identity

Module identity:

```text id="moduleid"
module_id {
    package_id
    module_name
    version
}
```

---

# 64. Module imports

Axiom source:

```text id="import"
import com.example.math
```

compiler có thể resolve thông qua package graph.

---

# 65. Explicit imports

Import phải resolve tới exact module identity trong build graph.

Không tự import arbitrary package found trên machine.

---

# 66. Package scope

Build environment nên expose only declared dependencies.

```text id="scope"
package A
 └── declared dependency B
```

A không tự access package C chỉ vì C nằm global cache.

---

# 67. Dependency isolation

Dependency graph xác định visible modules.

Giảm accidental transitive coupling.

---

# 68. Private dependency

Manifest:

```text id="private"
private dependency
```

không export dependency tới consumer.

---

# 69. Public dependency

Package API có thể expose type từ dependency.

Khi đó dependency có thể cần public/exported dependency semantics.

---

# 70. ABI closure

Native binary cần xác định complete runtime ABI closure:

```text id="abi"
application
 ↓
library A
 ↓
library B
 ↓
platform ABI
```

Package resolver phải đảm bảo required artifacts exist.

---

# 71. Static linking

Package manager cung cấp static artifact:

```text id="staticlib"
libA.axlib
```

Compiler/linker trực tiếp link.

---

# 72. Dynamic linking

Package cung cấp:

```text id="dynamic"
libA.dll
libA.so
libA.dylib
```

platform-specific artifact.

---

# 73. PE64

Windows package target phải support:

```text id="pe64"
PE64 executable
PE64 DLL
import/export metadata
```

---

# 74. ELF

Linux:

```text id="elf"
ELF executable
shared object
static archive
```

---

# 75. Mach-O

Apple:

```text id="macho"
Mach-O executable
dylib
framework-compatible artifacts
```

---

# 76. iOS

iOS artifacts có thể cần:

- architecture;
- signing metadata;
- entitlements;
- platform SDK compatibility.

Signing/security semantics thuộc appropriate platform/AXSECURITY integration.

---

# 77. Android

Android artifacts có thể include:

```text id="android"
native libraries
application package components
ABI variants
```

Exact Android packaging adapter không phải AXPACKAGE core.

---

# 78. WASM

WASM package artifact:

```text id="wasm"
wasm module
imports
exports
target ABI
```

---

# 79. Cross compilation

Một package có thể chứa multiple artifacts:

```text id="cross"
package
 ├── windows-x86_64
 ├── linux-x86_64
 ├── linux-arm64
 ├── macos-arm64
 └── wasm32
```

Resolver chọn artifact phù hợp.

---

# 80. Source distribution

Package có thể distribute source-only:

```text id="sourcepkg"
source package
```

Compiler compile locally.

---

# 81. Binary distribution

Package có thể distribute precompiled native artifact.

Không bắt buộc consumer có compiler.

---

# 82. Mixed package

```text id="mixed"
source
+
precompiled artifacts
```

cho fallback:

```text target artifact available
 → use binary
else
 → compile source
```

Policy phải explicit.

---

# 83. Compiler cache

AXPACKAGE có thể feed compiler artifact cache:

```text id="compilecache"
package artifact
 ↓
compiler cache
 ↓
reuse
```

Content identity phải immutable.

---

# 84. Incremental compilation

Package metadata có thể giúp compiler detect:

```text id="incr"
source unchanged
dependency ABI unchanged
```

→ reuse compiled artifact.

---

# 85. ABI hash

Compiled module metadata:

```text id="abihash"
source/interface
 ↓
ABI hash
```

Dependency ABI hash changes → dependent module may need rebuild.

---

# 86. Interface hash

Axiom can distinguish:

```text id="ifacehash"
source hash
interface hash
ABI hash
code hash
```

cho incremental build.

---

# 87. Package cache hierarchy

```text id="cachehier"
project cache
      ↓
user cache
      ↓
machine cache
      ↓
repository
```

Resolution order explicit.

---

# 88. Cache trust

Cached artifact vẫn phải verify hash/signature according to policy.

Không coi local cache là trusted chỉ vì local.

---

# 89. Repository mirrors

Repository có thể có mirrors:

```text id="mirror"
primary
 ├── mirror A
 ├── mirror B
 └── mirror C
```

Resolver có thể fallback.

---

# 90. Mirror integrity

Mirror không thay đổi artifact identity.

Content hash/signature phải match expected package.

---

# 91. Repository authentication

Private repository authentication thuộc AXAUTH/AXIDENTITY.

AXPACKAGE chỉ consume credential/session interface.

---

# 92. Repository authorization

Whether user may download package:

```text id="repoauth"
AXSECURITY
```

Không do package resolver tự quyết định.

---

# 93. Package access control

Private packages có:

```text id="privatepkg"
namespace
publisher
access policy
```

AXSECURITY enforce.

---

# 94. Dependency confusion protection

Resolver phải phân biệt:

```text id="namespaceauthority"
canonical package namespace
repository authority
```

Không tự thay một package private bằng public package cùng display name.

---

# 95. Namespace pinning

Lockfile có thể pin:

```text id="pin"
package identity
authority
artifact hash
```

giảm ambiguity.

---

# 96. Package replacement

A package replacement phải tạo new revision/version identity hoặc explicit authorized replacement.

Không silently overwrite immutable artifact under same content identity.

---

# 97. Immutability

Published package artifact:

```text id="immutable"
package version
+
content hash
```

nên immutable.

Mutable repository metadata không được làm artifact content mutable.

---

# 98. Yank/deprecate

Package version có thể:

```text id="yank"
ACTIVE
DEPRECATED
YANKED
```

Yanked version vẫn có thể be installed by exact lockfile if policy permits.

---

# 99. Security advisory

Package metadata có thể link tới:

```text id="advisory"
security advisory
```

AXPACKAGE có thể expose information.

Security decision thuộc AXSECURITY/policy tooling.

---

# 100. Vulnerability metadata

Package metadata:

```text id="vuln"
component
affected_versions
fixed_versions
advisory_id
```

không tự block installation unless security policy says so.

---

# 101. License metadata

Manifest:

```text id="license"
license_id
license_text/reference
```

Package manager may validate required license metadata.

Legal interpretation không thuộc AXPACKAGE.

---

# 102. Provenance chain

```text id="provchain"
source
 ↓
compiler
 ↓
dependencies
 ↓
artifact
 ↓
package
 ↓
publisher
```

Metadata có thể preserve provenance.

---

# 103. Build attestation

Package có thể include:

```text id="attest"
build_attestation
```

Signature/trust verification thuộc AXCRYPTO/AXTRUST.

---

# 104. Reproducibility verification

Tool:

```text id="verifyrepro"
package_reproduce()
```

có thể build lại và compare:

```text artifact hash
```

hoặc documented reproducibility equivalence.

---

# 105. Reproducible metadata

Non-deterministic metadata phải được excluded/normalized:

- timestamps;
- local paths;
- machine-specific IDs;
- random build IDs.

---

# 106. Build IDs

Artifact vẫn có thể có unique build ID.

Reproducible build phải distinguish:

```text content identity
```

và:

```text diagnostic build identity
```

---

# 107. Debug symbols

Package có thể ship:

```text id="debug"
debug_symbols
source_map
unwind_metadata
```

AXDIAGNOSTICS consume them.

---

# 108. AI metadata

Package có thể ship:

```text id="aimeta"
API descriptions
type metadata
examples
capabilities
documentation
source relationships
```

AI tooling can discover package APIs without parsing arbitrary binaries.

---

# 109. AI package generation

AI can generate:

- manifest;
- dependency declarations;
- lockfile proposals;
- package documentation.

Compiler validates them.

AI output không bypass package verification.

---

# 110. Package execution

Package installation không tự execute package code.

Executable execution là explicit application/process operation.

---

# 111. Post-install hooks

Nếu supported, hooks phải:

- explicit;
- sandboxed;
- capability constrained;
- auditable.

Không chạy arbitrary post-install code by default.

---

# 112. Package lifecycle

```text id="lifecycle"
DISCOVERED
   ↓
RESOLVED
   ↓
DOWNLOADED
   ↓
VERIFIED
   ↓
STAGED
   ↓
INSTALLED
   ↓
ACTIVE
   ↓
DEPRECATED
   ↓
REMOVED
```

---

# 113. Transaction

Installation transaction:

```text id="transaction"
begin
 ↓
resolve
 ↓
fetch
 ↓
verify
 ↓
stage
 ↓
commit
```

Failure:

```text id="rollback"
abort
 ↓
cleanup staging
```

---

# 114. Concurrent installation

Two package operations modifying same environment phải có transaction conflict detection.

Không overwrite state silently.

---

# 115. Environment profiles

AXCONFIG có thể define:

```text id="envprofiles"
development
testing
production
embedded
offline
```

Package resolver có thể use profile constraints.

---

# 116. Package environment

Installed package set:

```text id="environment"
environment {
    environment_id
    target
    packages
    lock_revision
}
```

---

# 117. Immutable environment

Production environment có thể be represented as:

```text id="immutableenv"
lockfile
+
package hashes
```

để deployment reproducibility.

---

# 118. Deployment bundle

AXPACKAGE có thể produce:

```text id="bundle"
deployment_bundle
```

gồm:

- executable;
- dynamic libraries;
- resources;
- manifests;
- licenses;
- provenance;
- lockfile.

---

# 119. Self-contained deployment

Application có thể đóng gói tất cả runtime dependencies.

Không cần package manager runtime.

---

# 120. System package

OS-level packages có thể be represented, nhưng native OS installer integration là adapter.

---

# 121. Embedded profile

Embedded target có thể use:

```text id="embedded"
source + selected artifacts
```

không cần repository runtime.

---

# 122. Minimal package metadata

Tiny binaries không cần carry entire package manager metadata.

Compiler can strip package metadata after build.

---

# 123. Package metadata retention

Build can select:

```text id="retain"
NONE
MINIMAL
DEBUG
FULL
AI
```

---

# 124. Binary size

AXPACKAGE không được ép runtime executable chứa:

- repository clients;
- dependency solver;
- manifest parser;

trừ khi application explicitly links those APIs.

---

# 125. No runtime package manager

Core Axiom application execution:

```text id="noruntimepkg"
.exe
 ↓
OS/runtime
```

không cần AXPACKAGE service.

---

# 126. Native compiler independence

Package manager failure không được làm compiler unable to compile source already available locally.

---

# 127. Dependency resolver

Resolver phải deterministic:

```text id="resolver"
input:
manifest
lockfile
repositories
target
features
policy
 ↓
resolved graph
```

---

# 128. Resolver conflict

Resolution conflict phải produce explainable graph:

```text id="conflictgraph"
A requires C >= 2
B requires C < 2
```

→ explicit conflict.

---

# 129. Resolver diagnostics

Error nên include:

- dependency path;
- constraints;
- selected versions;
- rejected candidates;
- target mismatch;
- feature conflicts.

---

# 130. Backtracking

Resolver có thể sử dụng:

```text id="backtracking"
constraint solving
```

nhưng phải bounded và deterministic.

---

# 131. Resolution performance

Local lockfile install should be near:

```text id="fastresolve"
O(number_of_packages)
```

với indexed metadata.

---

# 132. Parallel downloads

Independent artifacts có thể download parallel.

Security/integrity verification remains per artifact.

---

# 133. Content streaming

Large artifacts có thể stream:

```text id="stream"
repository
 ↓
AXSTREAM
 ↓
hash
 ↓
disk
```

không yêu cầu giữ toàn bộ artifact trong RAM.

---

# 134. Resume

Large downloads có thể support resumable transfer nếu repository protocol supports it.

Final content hash still mandatory.

---

# 135. Compression

Package archive may use compression.

Compression does not change artifact content identity after decompression.

---

# 136. Archive safety

Package extractor phải chống:

- path traversal;
- absolute-path writes;
- symlink escape;
- resource explosion.

AXSECURITY/storage sandbox enforce.

---

# 137. File permissions

Package manifest có thể declare permissions, nhưng installation must constrain them according to target platform/security policy.

---

# 138. Native library loading

Dynamic library package metadata must specify:

```text id="dynload"
ABI
architecture
dependencies
entrypoints
```

Actual loading thuộc AXPROCESS/native loader.

---

# 139. Symbol exports

Package metadata can describe exports.

Linker owns actual symbol resolution.

---

# 140. Formal invariants

```text id="pkginv"
PKG-INV-01
Package identity phải khác resource/runtime identity.

PKG-INV-02
Package version phải có deterministic comparison semantics.

PKG-INV-03
Package version không mặc định đồng nghĩa ABI compatibility.

PKG-INV-04
API, ABI, schema và artifact versions phải được phân biệt.

PKG-INV-05
Manifest phải có canonical representation.

PKG-INV-06
Equivalent manifests phải canonicalize deterministically.

PKG-INV-07
Artifact identity phải gắn với content integrity.

PKG-INV-08
Published immutable artifact không được silently mutate.

PKG-INV-09
Artifact hash phải được verify trước activation.

PKG-INV-10
Signature và hash phải được phân biệt.

PKG-INV-11
Trust decision phải thuộc AXTRUST/AXSECURITY.

PKG-INV-12
Package download không mặc định grant execution authority.

PKG-INV-13
Package installation phải atomic.

PKG-INV-14
Failed installation không được expose partial active state.

PKG-INV-15
Upgrade phải có rollback-safe semantics.

PKG-INV-16
Dependency graph phải được validate.

PKG-INV-17
Dependency cycles phải được phát hiện khi graph semantics yêu cầu DAG.

PKG-INV-18
Dependency constraints phải resolve deterministic.

PKG-INV-19
Lockfile phải pin exact resolution khi reproducibility yêu cầu.

PKG-INV-20
Lockfile phải preserve artifact integrity identity.

PKG-INV-21
Feature resolution phải deterministic.

PKG-INV-22
Feature conflicts phải được explicit detect.

PKG-INV-23
Target-incompatible artifact không được selected.

PKG-INV-24
Architecture-incompatible artifact không được selected.

PKG-INV-25
Private package không được silently substitute bằng public package cùng display name.

PKG-INV-26
Repository không phải compiler/runtime dependency bắt buộc.

PKG-INV-27
Offline build phải hoạt động khi dependencies cần thiết đã available locally.

PKG-INV-28
Compiler không được tự truy cập network ngoài explicit package-resolution operation.

PKG-INV-29
Build scripts không được mặc định có unrestricted privileges.

PKG-INV-30
Package extraction phải chống path traversal và unsafe filesystem escape.

PKG-INV-31
Cache phải verify integrity trước trust.

PKG-INV-32
Cache garbage collection không được remove live dependency.

PKG-INV-33
Static package artifacts phải có thể link trực tiếp mà không cần package runtime.

PKG-INV-34
Dynamic package artifacts phải khai báo ABI/target requirements.

PKG-INV-35
Runtime executable không mặc định phải chứa package manager.

PKG-INV-36
Package metadata không được bắt buộc làm runtime overhead.

PKG-INV-37
Reproducible build metadata phải loại bỏ hoặc normalize machine-specific nondeterminism.

PKG-INV-38
AI-generated package metadata phải được compiler/resolver validate.

PKG-INV-39
AXPACKAGE không được bypass AXIDENTITY, AXTRUST hoặc AXSECURITY.

PKG-INV-40
AXPACKAGE chỉ quản lý packaging, dependency, distribution và installation; compiler, linker, execution, authorization và cryptography thuộc subsystem tương ứng.
```

---

# 141. Definition of Done

`AXPACKAGE 5.0` được freeze khi Axiom có:

- package identity;
- namespace;
- package version;
- manifest;
- canonical manifest;
- artifact model;
- target variants;
- CPU feature variants;
- dependencies;
- dependency graph;
- dependency constraints;
- feature resolution;
- lockfile;
- repository abstraction;
- local repository;
- remote repository;
- content-addressed cache;
- artifact hashing;
- package signatures;
- provenance;
- reproducible build metadata;
- source packages;
- binary packages;
- mixed packages;
- module packaging;
- static libraries;
- dynamic libraries;
- PE64;
- ELF;
- Mach-O;
- iOS;
- Android;
- WASM;
- cross-compilation artifacts;
- resource packaging;
- compiler cache;
- ABI/interface hashes;
- installation transactions;
- atomic activation;
- upgrade;
- rollback;
- uninstall;
- cache GC;
- offline mode;
- repository mirrors;
- download resume;
- streaming;
- archive safety;
- package lifecycle;
- deployment bundles;
- immutable environments;
- dependency isolation;
- build-script sandboxing;
- security integration;
- trust integration;
- identity integration;
- network integration;
- storage integration;
- time integration;
- config integration;
- diagnostics;
- observability;
- logging;
- audit;
- AI metadata;
- compiler integration;
- native ABI;
- native APIs;
- 40 invariants.

**AXPACKAGE 5.0 → FROZEN.**

---

# BOOTSTRAP-768 — AXBUILD

**Native Build Graph, Project Model, Compilation Orchestration, Incremental Build, Artifact Cache, Link Planning, Cross-Compilation & Reproducible Build Runtime 5.0**

Đây là bước tiếp theo hợp lý vì `AXPACKAGE` vừa xác định **package/artifact/dependency**, nhưng vẫn còn một lớp quan trọng:

```text id="buildnext"
source
  │
  ▼
project
  │
  ▼
AXBUILD
  ├── dependency graph
  ├── source graph
  ├── incremental analysis
  ├── compiler scheduling
  ├── artifact cache
  ├── linker planning
  ├── target selection
  ├── parallel build
  ├── reproducibility
  └── final artifact
          │
          ▼
       PE64 / ELF / Mach-O / WASM
```

`AXBUILD` sẽ đặc biệt đóng khung mục tiêu trước đó của Axiom: **build nhanh như hệ thống native hiện đại nhưng không biến build system thành một dependency/runtime bắt buộc của executable**.