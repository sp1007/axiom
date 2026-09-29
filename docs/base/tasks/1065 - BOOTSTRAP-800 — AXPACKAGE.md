# BOOTSTRAP-800 — AXPACKAGE
## Native Axiom Package & Dependency System, Package Identity, Semantic Versioning, Dependency Graph, Version Constraints, Lockfile, Registry, Source/Artifact Resolution, Repository Integration, Content-Addressed Package Cache, Platform/Target Variants, Feature Resolution, Reproducible Dependency Graph, Package Signing & Trust Boundary, Offline/Private Registry, Workspace/Monorepo Packages, Build Integration & Package ABI 5.0

**Status:** FROZEN — Architecture Specification v5.0  
**Namespace:** `AXPACKAGE`  
**ABI:** `AXPACKAGE_ABI_1`  
**Schema:** `AXPACKAGE_SCHEMA_1`  
**Lockfile:** `axiom.lock`  
**Package manifest:** `axiom.pkg`  

**Dependencies:**

```text
AXVCS
AXHISTORY
AXCOMPILER
AXBUILD
AXOBJECT
AXBINARY
AXABI
AXCRYPTO
AXTRUST
AXTEST
AXDOC
```

---

# 1. Mục tiêu

`AXPACKAGE` quản lý **dependency graph và package distribution**, không quản lý source history và không trở thành runtime của executable.

```text id="4b5q3c"
AXVCS
   │
   ▼
source/revision
   │
   ▼
AXPACKAGE
   │
   ├── resolve dependencies
   ├── lock versions
   ├── obtain source/artifacts
   ├── verify identity
   └── build graph
           │
           ▼
        AXBUILD
           │
           ▼
       AXCOMPILER
```

Executable cuối cùng:

```text id="r7v5b3"
Application
    ↓
linked native code
    ↓
NO PACKAGE MANAGER REQUIRED AT RUNTIME
```

---

# 2. Boundary

AXPACKAGE owns:

```text id="g7hj0w"
Package
PackageManifest
PackageIdentity
Dependency
Version
VersionConstraint
Resolution
Lockfile
Registry
PackageCache
Workspace
FeatureSet
TargetVariant
ArtifactSelection
TrustMetadata
```

Không owns:

```text id="d3d6f2"
source semantics       → AXCOMPILER
repository history     → AXHISTORY
repository storage     → AXVCS
build execution        → AXBUILD
binary linking         → AXLINKER
binary format          → AXBINARY
runtime                → AXRUNTIME
cryptographic primitive→ AXCRYPTO
```

---

# 3. Core principle

Package identity phải độc lập với:

```text id="lq6b2t"
local filesystem
registry URL
download URL
branch
current machine
```

Canonical identity:

```text id="w5m6d4"
PackageIdentity
    =
HASH(
    package_namespace,
    package_name,
    package_schema
)
```

Version và source revision là các thuộc tính khác nhau.

---

# 4. Package identity

```text id="z4j7bs"
PackageId {
    namespace
    name
}
```

Ví dụ:

```text id="t6p4j2"
axiom.graphics
axiom.http
company.database
```

---

# 5. Namespace

Namespace ngăn collision.

Có thể:

```text id="3w2qrx"
official
user
organization
domain
registry-assigned
```

Nhưng namespace không tự động chứng minh trust.

---

# 6. Package name

Tên package:

```text id="0v8rji"
UTF-8
case-normalized according to schema
```

Không được chứa path traversal semantics.

---

# 7. Package version

Axiom dùng version có cấu trúc:

```text id="k0q9sj"
Version {
    major
    minor
    patch
    prerelease[]
    build[]
}
```

---

# 8. Version semantics

Ba thành phần:

```text id="q1l7h2"
MAJOR
MINOR
PATCH
```

có ý nghĩa API compatibility theo package policy.

Không mặc định rằng mọi thay đổi code đều bắt buộc tăng MAJOR.

---

# 9. Pre-release

Ví dụ:

```text id="2y4d6m"
1.2.0-alpha
1.2.0-beta
1.2.0-rc.1
```

Pre-release không tự động được chọn khi một stable constraint không yêu cầu.

---

# 10. Build metadata

Build metadata:

```text id="v6m8a1"
1.2.0+build42
```

không được thay đổi package semantic version precedence.

---

# 11. Version ordering

Canonical ordering phải deterministic.

```text id="j2k7c1"
1.0.0-alpha
<
1.0.0-beta
<
1.0.0
```

---

# 12. Version constraint

```text id="b8d3q4"
VersionConstraint
```

supports:

```text id="z7p5a8"
EXACT
RANGE
CARET
TILDE
WILDCARD
SET
```

---

# 13. Exact constraint

```text id="s4e9n2"
=1.4.3
```

chỉ chấp nhận version tương ứng.

---

# 14. Range

Ví dụ:

```text id="2q8w6e"
>=1.2.0 <2.0.0
```

---

# 15. Caret

Ví dụ:

```text id="e4h7s1"
^1.4.0
```

có nghĩa theo compatibility policy của schema.

---

# 16. Tilde

```text id="m8v3x5"
~1.4.2
```

giới hạn patch/minor theo chuẩn Axiom.

---

# 17. Multiple constraints

```text id="a5p2s9"
>=1.0 <2.0
!=1.5.0
```

---

# 18. Dependency

```text id="r3v6k8"
Dependency {
    package_id
    constraint
    source
    features
    optional
    target_condition
}
```

---

# 19. Dependency source

```text id="n4c8y2"
Registry
Git/VCS
Path
Workspace
Archive
Artifact
Local
```

---

# 20. Registry dependency

```text id="x8q2m5"
source = registry
```

Registry trả metadata/package candidates.

---

# 21. VCS dependency

```text id="k5r9v3"
source = repository
repository_id
revision
constraint
```

AXVCS retrieves it.

---

# 22. Path dependency

```text id="j3w7p1"
path = "../common"
```

chỉ phù hợp local/workspace development.

Lockfile phải canonicalize identity.

---

# 23. Workspace dependency

Package có thể tham chiếu package cùng workspace:

```text id="u2f8n6"
workspace = true
```

Không cần network.

---

# 24. Archive dependency

```text id="p7x4s1"
archive {
    url
    digest
}
```

Digest bắt buộc nếu artifact được dùng trong reproducible build.

---

# 25. Artifact dependency

Có thể yêu cầu prebuilt binary:

```text id="q6n2v8"
artifact {
    target
    abi
    profile
    digest
}
```

---

# 26. Source versus artifact

Dependency có thể cung cấp:

```text id="g8d4m1"
SOURCE
ARTIFACT
SOURCE_WITH_CACHE
```

Policy xác định lựa chọn.

---

# 27. Default preference

Axiom mặc định ưu tiên:

```text id="w3p6q9"
source
```

khi cần reproducibility/portability và compiler/toolchain phù hợp.

Artifact có thể được dùng để giảm build time.

---

# 28. Package manifest

Minimal:

```text id="a8j3s6"
package {
    id
    version
    edition
    targets
    dependencies
    features
    exports
}
```

---

# 29. Package edition

```text id="m4c7x2"
edition = 1
```

Edition có thể thay đổi language/package defaults mà không thay đổi package identity.

---

# 30. Package metadata

Optional:

```text id="n8v2p5"
description
authors
license
homepage
repository
documentation
keywords
categories
```

Metadata không được ảnh hưởng source semantics trừ khi explicitly declared.

---

# 31. Package source root

Canonical:

```text id="z2f7m4"
src/
```

nhưng layout có thể cấu hình.

---

# 32. Package targets

```text id="h5q9s3"
library
binary
plugin
proc-tool
resource
```

---

# 33. Library package

Có thể tạo:

```text id="j8d4p6"
static library
dynamic library
Axiom module
C ABI library
```

---

# 34. Binary package

Binary package có:

```text id="c3m7x1"
target
ABI
binary format
artifact digest
```

---

# 35. Platform target

Ví dụ:

```text id="r7h2k9"
windows-x86_64
linux-x86_64
linux-aarch64
macos-x86_64
macos-aarch64
ios-aarch64
android-aarch64
wasm32
```

---

# 36. Target condition

Dependency có thể:

```text id="p1v6d8"
only on windows
only on linux
only on wasm
only when feature X
```

Condition được đánh giá statically.

---

# 37. Target normalization

Target phải được resolve thành canonical `TargetId` từ AXTOOLCHAIN.

Không dùng string tùy ý trong lockfile.

---

# 38. ABI condition

Dependency có thể yêu cầu:

```text id="b6m2r8"
ABI
calling convention
architecture
endianness
pointer width
```

AXABI xác nhận compatibility.

---

# 39. Feature

Package có:

```text id="s9x4c7"
Feature {
    name
    dependencies[]
    flags[]
}
```

---

# 40. Feature activation

Features là additive theo mặc định:

```text id="t3w8q1"
feature A
feature B
```

được union.

---

# 41. No hidden feature removal

Một dependency graph không được silently disable required feature.

---

# 42. Feature resolver

```text id="y5n2v7"
FeatureResolver
```

creates canonical:

```text id="e8p4k6"
FeatureSet
```

---

# 43. Optional dependency

```text id="q1m9s5"
optional = true
```

không được đưa vào graph build nếu feature/condition không activate.

---

# 44. Dependency graph

```text id="d4h7x9"
PackageGraph {
    nodes[]
    edges[]
}
```

---

# 45. Graph node

```text id="v8p3k1"
PackageNode {
    PackageId
    Version
    source
    features
}
```

---

# 46. Graph edge

```text id="m6q2t8"
DependencyEdge {
    from
    to
    constraint
    condition
    feature
}
```

---

# 47. Resolution

Resolution input:

```text id="s2k9f4"
root package
constraints
target
features
toolchain
registry state
lockfile
```

---

# 48. Resolution output

```text id="x7m4p2"
ResolvedGraph {
    nodes
    edges
    source identities
    artifact identities
}
```

---

# 49. Resolution must be deterministic

Same:

```text id="k8v3n6"
manifest
lockfile
registry snapshot
target
features
policy
```

→ same graph.

---

# 50. Registry freshness

Without lockfile, registry metadata can change.

Therefore reproducible builds require either:

```text id="u4q7m1"
lockfile
```

or immutable package references.

---

# 51. Lockfile

`axiom.lock` records exact resolved dependencies.

```text id="b2x8r5"
Lockfile {
    schema
    root
    packages[]
    sources[]
    checksums[]
    graph_hash
}
```

---

# 52. Lock entry

```text id="f9m3q6"
LockedPackage {
    PackageId
    version
    source
    revision
    digest
    dependencies[]
}
```

---

# 53. Lockfile source identity

For VCS:

```text id="q5v7n2"
repository_id
revision_id
```

For registry:

```text id="e3k8p1"
registry_id
package_version
content_digest
```

---

# 54. Lockfile integrity

`graph_hash` covers canonical dependency graph.

Any unauthorized change invalidates lock verification.

---

# 55. Frozen resolution

CI may use:

```text id="r4x9m7"
--locked
```

Meaning:

```text id="v2j6p8"
do not modify lockfile
```

---

# 56. Offline resolution

With complete cache:

```text id="z7c3n5"
resolve --offline
```

must work.

If required package is missing:

```text id="j1q8m4"
PACKAGE_NOT_CACHED
```

---

# 57. Package cache

Content-addressed:

```text id="p6v2s9"
PackageCache {
    content_digest
    package
    target
    artifact
}
```

---

# 58. Cache identity

Cache key must include all relevant inputs:

```text id="n3w8q5"
source digest
compiler version
compiler schema
target
ABI
features
profile
build flags
```

---

# 59. Source cache

Source package cache can deduplicate identical content across versions/registries.

---

# 60. Artifact cache

Compiled artifact cache belongs conceptually to AXBUILD but AXPACKAGE may provide package-scoped storage.

No confusion between:

```text id="q8f4m2"
package content identity
```

and:

```text id="y5v7k1"
build artifact identity
```

---

# 61. Registry

Registry API:

```text id="h2n6r9"
publish
query
resolve
download
metadata
yank
unpublish-policy
```

---

# 62. Registry neutrality

Axiom core must not require a single central registry.

Possible:

```text id="s5m8q2"
public registry
private registry
LAN registry
filesystem registry
VCS repository
```

---

# 63. Registry identity

```text id="c9v4x7"
RegistryId
```

is separate from PackageId.

Same package can be mirrored.

---

# 64. Mirror

Mirror:

```text id="k3p8n1"
Registry A
    ↓
Registry B
```

must preserve package content digest.

---

# 65. Package content identity

```text id="m7q2v5"
PackageContentId =
HASH(
    canonical package tree
)
```

This allows mirrors without changing identity.

---

# 66. Package version identity

```text id="x4n9s6"
PackageVersionId {
    PackageId
    Version
    ContentId
}
```

---

# 67. Same version, different content

If:

```text id="r8c3p1"
1.2.0
```

is published with different content:

```text id="z5m7q2"
content digest differs
```

they are distinct package contents.

Registry policy should reject version mutation for immutable releases.

---

# 68. Yank

Package version may be:

```text id="j6v4n8"
AVAILABLE
YANKED
WITHDRAWN
```

Yank should not invalidate existing lockfiles automatically.

---

# 69. Existing lockfile

If package was previously locked:

```text id="t2p9m5"
lockfile → exact content
```

it remains usable if repository policy permits.

---

# 70. Dependency source priority

Resolver policy may define:

```text id="u7x3q8"
workspace
local
lockfile
registry
VCS
```

but priority must be explicit.

---

# 71. Dependency conflict

Example:

```text id="q5n8m2"
A → lib ^1
B → lib ^2
```

Resolver may report:

```text id="k9r4p7"
VERSION_CONFLICT
```

unless compatible graph resolution exists.

---

# 72. Multiple versions

Axiom may allow multiple versions of the same package:

```text id="e2m6s9"
lib@1.5
lib@2.1
```

when their symbol namespaces can remain distinct.

---

# 73. Package namespace isolation

Each package version has module identity:

```text id="f4q8v1"
PackageId + Version
```

to avoid symbol collisions where necessary.

---

# 74. Dependency alias

Manifest can alias:

```text id="w3p7n5"
database_v1 = database@1
database_v2 = database@2
```

---

# 75. Cyclic dependencies

Default package graph should reject cycles:

```text id="y8m2c6"
A → B → A
```

unless explicitly supported by package architecture.

---

# 76. Why

Cycles complicate:

```text id="b5r9q3"
build ordering
initialization
ABI
package publication
```

---

# 77. Build graph

AXPACKAGE emits:

```text id="v6n1k8"
PackageGraph
```

AXBUILD transforms this into build graph.

---

# 78. Package initialization

Package manager does not define runtime initialization.

AXCOMPILER/AXRUNTIME define program semantics.

---

# 79. Native linking

Package may provide:

```text id="c2x7m4"
static library
dynamic library
native object
```

AXLINKER handles linking.

---

# 80. Native dependency metadata

```text id="p9q5v2"
NativeDependency {
    target
    ABI
    symbols
    library
    linkage
}
```

---

# 81. C ABI package

A package can expose:

```text id="j4m8s6"
extern "C"
```

interfaces.

AXABI validates the interface.

---

# 82. System libraries

Platform system libraries are not packages unless explicitly wrapped.

Example:

```text id="w8n3q1"
Windows API
POSIX
libSystem
Android NDK API
```

are platform SDK dependencies.

AXTOOLCHAIN supplies them.

---

# 83. SDK dependency

```text id="z6p2r9"
SdkDependency {
    sdk_id
    version_constraint
}
```

---

# 84. Package + SDK

Resolver must distinguish:

```text id="f1m7x5"
package dependency
```

from:

```text id="q3v8n2"
platform SDK dependency
```

---

# 85. Cross compilation

Resolution must use:

```text id="r5k9m3"
host target
target target
```

separately.

Build tools run on host.

Package code targets target.

---

# 86. Build dependency

Some packages provide host tools:

```text id="n8q4p1"
build-dependency
```

These target host.

---

# 87. Host/target graph

```text id="d6x2m7"
HOST
 └── build tools
       ↓
TARGET
 └── application dependencies
```

---

# 88. Feature + target

Feature resolution happens before target-specific artifact selection where possible.

---

# 89. Target artifact selection

```text id="u5m9q3"
Package
 ↓
TargetId
 ↓
ABI
 ↓
Profile
 ↓
Artifact
```

---

# 90. Debug/release

Package artifact variants may include:

```text id="v7p3k1"
debug
release
profile-custom
```

Source packages remain independent.

---

# 91. Static/dynamic selection

Manifest may request:

```text id="x9n4m6"
static
dynamic
either
```

AXLINKER determines final linking.

---

# 92. Runtime dependency rule

Dynamic package libraries may be runtime dependencies if explicitly selected.

But package manager itself must never be required merely to load them.

---

# 93. Package installation

Installation means populating:

```text id="k2q7v5"
cache
registry metadata
source store
artifact store
```

not modifying the global OS runtime.

---

# 94. Global package state

Avoid mandatory global mutable installation state.

Prefer:

```text id="h8m3p9"
project-local cache
user cache
content-addressed shared cache
```

---

# 95. Workspace

```text id="c4v7n2"
Workspace {
    root
    members[]
    shared_dependencies
}
```

---

# 96. Workspace package identity

Members retain independent PackageId.

Workspace membership does not merge package identity.

---

# 97. Monorepo

AXVCS repository may contain:

```text id="s6q1m8"
workspace/
 ├── compiler/
 ├── runtime/
 ├── std/
 ├── gui/
 └── tools/
```

Each can be package.

---

# 98. Workspace lock

One lockfile can resolve all members.

---

# 99. Shared dependency

Workspace resolver may unify compatible versions.

If not compatible, multiple versions remain explicit.

---

# 100. Package publication

Pipeline:

```text id="j8r3p6"
workspace package
 ↓
validate manifest
 ↓
validate source
 ↓
build
 ↓
test
 ↓
generate metadata
 ↓
canonicalize
 ↓
hash
 ↓
sign
 ↓
publish
```

---

# 101. Publication validation

Must verify:

```text id="m4x7q2"
PackageId
Version
manifest
tree
dependencies
target metadata
license metadata if required
content digest
```

---

# 102. Publication immutability

Recommended default:

```text id="n6p2v9"
PackageVersionContent
```

is immutable after publication.

---

# 103. Package signing

Signature boundary:

```text id="r1m8q5"
AXPACKAGE
   ↓
AXTRUST
   ↓
AXCRYPTO
```

---

# 104. Signature payload

Sign canonical:

```text id="z7c4m2"
PackageId
Version
ContentId
metadata
```

according to schema.

---

# 105. Signature does not imply safety

Valid signature means identity/authenticity according to trust policy.

It does not prove:

```text id="u9p5x3"
bug-free
secure
correct
compatible
```

---

# 106. Trust policy

Consumers may configure:

```text id="g2m7q8"
ALLOW_UNSIGNED
REQUIRE_SIGNED
TRUST_NAMESPACE
TRUST_KEY
TRUST_REGISTRY
```

---

# 107. Dependency trust

Each dependency can have independent trust state.

---

# 108. Untrusted package

Fetching an untrusted package must not execute:

```text id="f5n1k9"
build scripts
install hooks
generators
arbitrary executables
```

---

# 109. Build scripts

If Axiom later supports build scripts:

```text id="s8q3v6"
AXBUILD
```

owns execution and sandboxing.

AXPACKAGE only declares them.

---

# 110. Default package build

Preferred default:

```text id="x4m9p2"
declarative build metadata
```

rather than arbitrary scripts.

---

# 111. Package manifest parser

Must reject:

```text id="b7r3n5"
duplicate keys
invalid IDs
invalid versions
path traversal
invalid UTF-8
unknown mandatory fields
```

---

# 112. Registry security

Registry responses are untrusted until:

```text id="q6v2m8"
schema validation
content hash
signature policy
```

pass.

---

# 113. Download security

Downloads use:

```text id="n3x8p5"
streaming
bounded buffers
digest verification
size limits
```

---

# 114. Archive extraction

Archives must reject:

```text id="h1m7q4"
../
absolute paths
symlink escapes
duplicate conflicting files
oversized expansion
```

---

# 115. Zip bomb / archive bomb

Expansion ratio and total extracted size are bounded.

---

# 116. Registry metadata cache

Metadata cache may be stale.

Cache entries include:

```text id="c5v9n2"
registry_id
query
timestamp
etag/version
```

---

# 117. Reproducibility

Build should record:

```text id="p8q3m6"
package graph hash
toolchain fingerprint
target
ABI
features
source digests
artifact digests
```

---

# 118. Build manifest

AXPACKAGE can produce:

```text id="y4m7r1"
ResolvedDependencyManifest
```

for AXBUILD.

---

# 119. SBOM-like metadata

Optional dependency inventory:

```text id="x6n2p8"
Package
Version
Source
Digest
License metadata
```

No runtime overhead.

---

# 120. Dependency provenance

Record:

```text id="k9q4v3"
registry
repository
revision
content digest
signature
```

---

# 121. Package update

Update operation:

```text id="u5m8x2"
inspect constraints
current lock
available candidates
impact
resolve
update lock
```

---

# 122. Selective update

```text id="f3p7n9"
update package A
```

should avoid unrelated dependency changes unless required by graph constraints.

---

# 123. Minimal update

Resolver attempts to minimize graph churn subject to constraints and policy.

This is a deterministic policy, not an optimization guarantee.

---

# 124. Dependency impact

AXPACKAGE can expose:

```text id="r8m2q5"
added
removed
upgraded
downgraded
source_changed
artifact_changed
```

---

# 125. API impact

AXDIFF can analyze package API changes between versions.

AXPACKAGE consumes the result.

---

# 126. ABI impact

AXABI analyzes native compatibility.

AXPACKAGE records:

```text id="v1q7m4"
ABIImpact
```

where available.

---

# 127. Breaking dependency update

Resolver can enforce policy:

```text id="p6n3x8"
deny ABI breaking update
```

if requested.

Policy belongs to project configuration.

---

# 128. Package deprecation

Metadata:

```text id="j4r9m2"
deprecated
replacement
reason
```

is descriptive metadata.

Resolver may warn.

---

# 129. Package removal

A removed package must not break an existing lockfile if its immutable content remains locally available.

---

# 130. Registry outage

With complete lock/cache:

```text id="s8m4q1"
offline build
```

should work.

---

# 131. Partial cache

If package unavailable:

```text id="z2p7n5"
MISSING_PACKAGE_CONTENT
```

must identify exact package/version/content digest.

---

# 132. Network retry

Transfers support:

```text id="q5x9m3"
resume
retry
backoff
checksum
```

without duplicating cached content.

---

# 133. Parallel downloads

Independent package content may download concurrently.

---

# 134. Deterministic extraction

Package tree extraction must canonicalize file metadata relevant to source identity.

---

# 135. File timestamps

Download/extraction timestamps must not affect PackageContentId.

---

# 136. Package cache GC

Cache GC is reachability-based from:

```text id="n7m2p8"
active lockfiles
projects
pins
recent operations
```

---

# 137. Cache eviction

Evicting cache must never alter:

```text id="x3q6v1"
PackageId
ContentId
Lockfile
RevisionId
```

---

# 138. Shared cache concurrency

Multiple builds can read same immutable package simultaneously.

Writers publish cache entries atomically.

---

# 139. Cache poisoning protection

Before accepting cached package:

```text id="f8m3q7"
expected ContentId
actual hash
```

must match.

---

# 140. Package graph fingerprint

```text id="k2v9n4"
GraphHash =
HASH(
    canonical packages
    canonical edges
    features
    target
    policy
)
```

---

# 141. Reproducible resolution

The lockfile should contain `GraphHash`.

AXBUILD can verify it before building.

---

# 142. Package build fingerprint

```text id="r6x3m8"
PackageBuildFingerprint =
HASH(
    content
    compiler
    toolchain
    target
    ABI
    features
    build configuration
)
```

---

# 143. Artifact cache

AXBUILD may use the fingerprint as cache key.

---

# 144. Package source patching

Local package development can apply AXPATCH to dependency source.

Such overrides must be explicit.

---

# 145. Dependency override

Manifest:

```text id="j7m4q9"
override package A → local path
```

must not silently affect production lockfile.

---

# 146. Patch dependency

Optional:

```text id="p2n8v5"
patch package X with local repository/revision
```

for development/testing.

---

# 147. Lockfile override recording

Lockfile must record overrides if they are part of reproducible resolution.

---

# 148. VCS revision pin

For development dependency:

```text id="x9q3m6"
repository_id
revision_id
```

is preferable to mutable branch.

---

# 149. Branch dependencies

Allowed:

```text id="c5r8v2"
branch = dev
```

but not reproducible without lock resolution.

Lockfile records exact RevisionId.

---

# 150. Tag dependencies

Tag is a mutable ref unless repository policy makes tags immutable.

Lockfile should still record resolved RevisionId.

---

# 151. Registry package + VCS provenance

A package may originate from VCS and be published to registry.

Record both:

```text id="n4p7x2"
registry content
source revision
```

when available.

---

# 152. Package source integrity

A source package's canonical tree hash must match declared ContentId.

---

# 153. Package metadata integrity

Manifest belongs inside canonical package content unless explicitly declared external.

---

# 154. Package docs

AXDOC can generate documentation from package source.

AXPACKAGE provides package metadata/navigation.

---

# 155. Package examples

Examples can be tested through AXTEST.

AXPACKAGE declares them; AXTEST executes them.

---

# 156. Package tests

Test dependencies may be separated:

```text id="v8m2q5"
normal dependency
dev dependency
test dependency
build dependency
```

---

# 157. Dev dependency

Not linked into production target unless explicitly referenced.

---

# 158. Build dependency

Runs on host when AXBUILD requires it.

---

# 159. Target dependency

Compiled for target.

---

# 160. Dependency kinds

Canonical:

```text id="q3x7n1"
NORMAL
OPTIONAL
DEV
TEST
BUILD
PROC_TOOL
TARGET_NATIVE
```

---

# 161. Procedure tools

Code generation tools must be explicit and sandbox-controlled.

---

# 162. Package plugins

Plugin packages are ordinary packages with explicit ABI:

```text id="m9p4v6"
PluginAbi
```

No implicit dynamic loading.

---

# 163. Plugin security

Plugin execution is controlled by AXBUILD/AXRUNTIME/AXTRUST policies.

---

# 164. Package registry protocol

Protocol should support:

```text id="s2n8q5"
resolve
metadata
download
publish
signature
capability negotiation
```

---

# 165. Protocol version

```text id="x7m3p9"
AXPACKAGE_PROTOCOL_1
```

separate from package schema.

---

# 166. Registry pagination

Large registries require:

```text id="k4q8v2"
cursor
limit
continuation token
```

---

# 167. Search

Search is metadata discovery.

It must not affect deterministic resolution once lockfile/candidates are fixed.

---

# 168. Candidate selection

Resolver sees:

```text id="p5n9x3"
available versions
constraints
yanked state
target
features
policy
```

---

# 169. Candidate ordering

Selection must be deterministic.

Default policy can prefer highest compatible stable version, but project policy may specify another deterministic strategy.

---

# 170. No hidden network

Normal compile of a locked project should not silently contact network if required dependencies are cached.

Network access must be an explicit build/resolution policy.

---

# 171. Air-gapped build

Complete package cache + lockfile + toolchain/sysroot should permit:

```text id="w8r2m6"
no network
```

build.

---

# 172. Enterprise/private registry

Private registry uses same canonical package model.

Authentication is transport/trust concern.

---

# 173. Credential security

Credentials must not appear in:

```text id="y5q8n2"
PackageId
ContentId
GraphHash
lockfile
build artifact metadata
```

unless explicitly intended.

---

# 174. URL redaction

Lockfile should prefer:

```text id="m3v7p9"
RegistryId
```

over embedding credentials-bearing URLs.

---

# 175. Reproducible package publication

Publishing same canonical package content must yield same ContentId.

---

# 176. Package archive format

Archive is transport format.

Canonical package identity comes from canonical package tree, not archive byte ordering.

---

# 177. Archive determinism

If deterministic archive is requested:

```text id="q2x6n8"
file ordering
metadata normalization
compression settings
```

must be canonical.

---

# 178. Package ABI

`AXPACKAGE_ABI_1` exposes opaque interfaces:

```text id="j8m4r7"
PackageHandle
ManifestHandle
DependencyHandle
ResolverHandle
RegistryHandle
CacheHandle
WorkspaceHandle
ResolutionHandle
```

---

# 179. ABI stability

Internal resolver algorithm may change without ABI break.

---

# 180. Package schema

`AXPACKAGE_SCHEMA_1` defines:

```text id="p4n9x2"
manifest
version
dependency
lockfile
package content metadata
registry metadata
artifact metadata
```

---

# 181. Lockfile schema migration

Future:

```text id="v7q3m5"
axiom.lock v1
    ↓
migration
    ↓
v2
```

must preserve resolved package identities.

---

# 182. Resolver API

```text id="c8m2x6"
resolve(
    Manifest,
    Lockfile?,
    Target,
    FeatureSet,
    ResolutionPolicy
)
```

---

# 183. Lock API

```text id="n5r8p1"
read_lockfile()
verify_lockfile()
write_lockfile()
update_lockfile()
freeze_resolution()
```

---

# 184. Registry API

```text id="q7m3v9"
query_packages()
get_metadata()
get_content()
publish_package()
get_signature()
```

---

# 185. Cache API

```text id="x4p8n2"
has_content()
read_content()
write_content()
has_artifact()
read_artifact()
gc_cache()
```

---

# 186. Workspace API

```text id="m6q1r7"
load_workspace()
list_members()
resolve_workspace()
publish_member()
```

---

# 187. Dependency graph API

```text id="z8v3p5"
graph_packages()
graph_dependencies()
topological_order()
detect_cycles()
compute_graph_hash()
```

---

# 188. Target API

```text id="j2n7x4"
select_target()
select_artifact()
validate_abi()
```

---

# 189. Package inspect

```text id="f5m9q3"
inspect_package()
inspect_manifest()
inspect_dependencies()
inspect_content()
```

---

# 190. Package verification

```text id="w7p2n8"
verify_package()
verify_signature()
verify_content()
verify_lock()
```

---

# 191. AXBUILD integration

AXBUILD receives:

```text id="r3x8m5"
ResolvedGraph
PackageSources
ArtifactCandidates
BuildFingerprint
```

and owns actual compilation.

---

# 192. AXCOMPILER integration

Compiler receives source/module dependencies already resolved.

It must not query registries itself.

---

# 193. AXIDE integration

IDE can display:

```text id="k6q4p9"
dependency graph
updates
outdated versions
source locations
package provenance
ABI impact
```

---

# 194. AXHISTORY integration

Package changes can reference:

```text id="x2m8v5"
RevisionId
PackageVersionId
Dependency graph changes
```

---

# 195. AXDIFF integration

Package update can generate:

```text id="p7n3q6"
API diff
ABI diff
dependency diff
source diff
```

between locked versions.

---

# 196. AXTEST integration

Dependency resolution tests:

```text id="y4m8r2"
conflict
cycle
feature
target
lock
offline
registry
signature
cache
```

---

# 197. AXCRYPTO integration

AXPACKAGE calls:

```text id="n8q2v7"
hash
verify_signature
```

through AXCRYPTO.

It never implements cryptographic primitives.

---

# 198. AXTRUST integration

Trust policy:

```text id="c5x9m3"
is_package_trusted()
is_signer_trusted()
is_registry_trusted()
```

belongs to AXTRUST.

---

# 199. 40 invariants

### PKG-INV-01
Package identity is deterministic.

### PKG-INV-02
Package content identity is content-addressed.

### PKG-INV-03
Registry identity is separate from package identity.

### PKG-INV-04
Package version ordering is deterministic.

### PKG-INV-05
Dependency constraints are explicit.

### PKG-INV-06
Resolved dependency graphs are deterministic.

### PKG-INV-07
Lockfiles record exact resolved content.

### PKG-INV-08
Lockfile graph hashes are deterministic.

### PKG-INV-09
A locked build does not silently change dependencies.

### PKG-INV-10
Offline resolution does not contact the network.

### PKG-INV-11
Missing cached content is reported explicitly.

### PKG-INV-12
Cache entries are content-verified.

### PKG-INV-13
Package archives do not define semantic identity.

### PKG-INV-14
Archive extraction is sandboxed.

### PKG-INV-15
Path traversal is rejected.

### PKG-INV-16
Untrusted package contents do not execute automatically.

### PKG-INV-17
Build-script execution belongs to AXBUILD.

### PKG-INV-18
Package resolution does not execute application code.

### PKG-INV-19
Package manager is never a runtime dependency.

### PKG-INV-20
Host and target dependency graphs are distinguished.

### PKG-INV-21
Target-specific artifacts require target compatibility.

### PKG-INV-22
Native artifacts require ABI compatibility.

### PKG-INV-23
Source and artifact identities are distinct.

### PKG-INV-24
Package cache eviction does not alter package identity.

### PKG-INV-25
Multiple compatible package versions may coexist when policy permits.

### PKG-INV-26
Dependency cycles are rejected by default.

### PKG-INV-27
Feature activation is explicit.

### PKG-INV-28
Optional dependencies are not silently activated.

### PKG-INV-29
VCS dependencies are pinned by immutable revision in reproducible lockfiles.

### PKG-INV-30
Mutable tags/branches do not masquerade as immutable dependency identities.

### PKG-INV-31
Package signatures are delegated to AXCRYPTO/AXTRUST.

### PKG-INV-32
Valid signatures do not imply code correctness.

### PKG-INV-33
Credential data is excluded from package identity.

### PKG-INV-34
Registry mirrors preserve package content identity.

### PKG-INV-35
Package publication is deterministic.

### PKG-INV-36
Package graph changes are inspectable.

### PKG-INV-37
API and ABI impact are separately represented.

### PKG-INV-38
Package resolution does not own compiler semantics.

### PKG-INV-39
AI cannot silently modify dependency resolution or lockfiles.

### PKG-INV-40
AXPACKAGE does not invent repository/history semantics.

---

# 200. Definition of Done

`AXPACKAGE 5.0` hoàn thành khi có:

- [x] Package identity.
- [x] Package content identity.
- [x] Manifest.
- [x] Version model.
- [x] Version constraints.
- [x] Dependency graph.
- [x] Features.
- [x] Target conditions.
- [x] Host/target dependency distinction.
- [x] Registry abstraction.
- [x] VCS dependency.
- [x] Workspace.
- [x] Monorepo support.
- [x] Lockfile.
- [x] Graph fingerprint.
- [x] Source cache.
- [x] Artifact cache boundary.
- [x] Offline resolution.
- [x] Partial cache.
- [x] Registry mirror.
- [x] Package signing boundary.
- [x] Trust boundary.
- [x] Secure archive extraction.
- [x] Untrusted-package protection.
- [x] Native artifact selection.
- [x] ABI compatibility boundary.
- [x] AXBUILD integration.
- [x] AXCOMPILER integration.
- [x] AXVCS integration.
- [x] AXHISTORY integration.
- [x] AXDIFF integration.
- [x] AXTEST integration.
- [x] AXIDE integration.
- [x] Deterministic resolution.
- [x] Reproducible builds metadata.
- [x] Package cache GC.
- [x] Resource limits.
- [x] `AXPACKAGE_ABI_1`.
- [x] `AXPACKAGE_SCHEMA_1`.
- [x] 40 `PKG-INV`.

**AXPACKAGE 5.0 — FROZEN.**

---

# Chuỗi dependency của Axiom hiện tại

Sau `AXVCS → AXPATCH → AXPACKAGE`, boundary đã trở nên khá rõ:

```text id="r9c5t2"
                    AXCOMPILER
                         │
                 semantic model
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           AXDIFF     AXPATCH    AXDOC
              │          │
              └────┬─────┘
                   ▼
                AXMERGE
                   │
                   ▼
               AXHISTORY
                   │
                   ▼
                 AXVCS
                   │
                   ▼
              AXPACKAGE
                   │
                   ▼
                AXBUILD
                   │
          ┌────────┴────────┐
          ▼                 ▼
      AXCOMPILER         AXLINKER
                            │
                            ▼
                         AXBINARY
```

Đặc biệt:

```text
AXVCS     = source/revision storage + synchronization
AXPACKAGE = dependency resolution + distribution
AXBUILD   = build graph + execution
AXCOMPILER= language semantics + compilation
AXLINKER  = native binary composition
```

Không có package manager nào nằm trong executable runtime.

---

# BOOTSTRAP-801 — AXBUILD

**Native Axiom Deterministic Build System, Semantic Build Graph, Incremental Compilation, Content-Addressed Build Cache, Dependency-Aware Scheduling, Host/Target Build Separation, Reproducible Native Builds, Cross Compilation, Profile/Optimization Configuration, PGO/LTO Integration, Package/Repository Integration, Parallel Build Execution, Build Sandbox, Artifact Graph, Build Manifest, Remote Cache, Distributed Build Boundary, Crash Recovery & Build ABI 5.0**

Đây là bước tiếp theo tự nhiên:

```text
AXVCS
   ↓ source/revision
AXPACKAGE
   ↓ resolved dependency graph
AXBUILD
   ↓ deterministic build graph
AXCOMPILER / AXASSEMBLER / AXLINKER
   ↓
AXBINARY
```

và `AXBUILD` sẽ là lớp quyết định **chính xác cái gì cần build lại, cái gì có thể lấy từ cache, thứ tự build, mức song song và cách tái lập cùng một native artifact**.