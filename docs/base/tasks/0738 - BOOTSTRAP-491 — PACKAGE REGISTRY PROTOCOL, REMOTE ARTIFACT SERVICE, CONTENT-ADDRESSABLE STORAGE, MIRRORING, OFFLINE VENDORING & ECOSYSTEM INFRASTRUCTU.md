# BOOTSTRAP-491 — PACKAGE REGISTRY PROTOCOL, REMOTE ARTIFACT SERVICE, CONTENT-ADDRESSABLE STORAGE, MIRRORING, OFFLINE VENDORING & ECOSYSTEM INFRASTRUCTURE

**Trạng thái: COMPLETED / LOCKED**

491 hoàn thiện tầng hạ tầng ecosystem phía trên 447/483/487/489.

Mục tiêu:

- package có thể publish/fetch;
- artifact có thể lưu trữ content-addressed;
- registry có metadata/API rõ ràng;
- mirror và offline vendoring;
- binary/source package;
- reproducible dependency resolution;
- không biến registry thành dependency bắt buộc của compiler;
- hỗ trợ nhiều registry độc lập.

Kiến trúc:

```text id="x8m4q2"
                    Axiom Package
                         │
                  Package Manifest
                         │
                ┌────────┴────────┐
                ↓                 ↓
           Source Package     Binary Package
                │                 │
                └────────┬────────┘
                         ↓
                 Registry Protocol
                         │
              ┌──────────┼──────────┐
              ↓          ↓          ↓
          Registry     Mirror     Local Cache
              │          │          │
              └──────────┼──────────┘
                         ↓
                Content Addressing
                         │
                    CAS Storage
```

---

## 491.1 — Registry ≠ Package Manager

Registry cung cấp package metadata/artifacts.

Package manager chịu:

- dependency resolution;
- selection;
- lock;
- fetch;
- cache;
- verification.

---

## 491.2 — Registry ≠ Compiler

Compiler không được hard-code một registry.

---

## 491.3 — Multiple registries

Project có thể sử dụng:

```text id="m6r2k8"
public registry
private registry
enterprise registry
local registry
air-gapped registry
```

---

## 491.4 — Package identity

Canonical identity:

```text id="p3n7x1"
Registry
Namespace
PackageName
```

Version là thuộc tính versioned release, không phải identity duy nhất.

---

## 491.5 — Package namespace

Registry phải tránh collision giữa package publishers.

---

## 491.6 — Package manifest

Manifest từ 447 được mở rộng:

```text id="q8w4c2"
PackageManifest {
    identity
    version
    edition
    dependencies
    features
    targets
    artifacts
    licenses
    provenance
    documentation
    source
    signatures
}
```

---

## 491.7 — Package version

Version phải deterministic và tuân policy đã định nghĩa ở 447/484.

---

## 491.8 — Immutable release

Một version đã publish không được silently thay đổi nội dung.

---

## 491.9 — Yank / withdraw

Registry có thể đánh dấu version không nên được chọn cho dependency mới.

Existing lockfiles vẫn có thể reference nếu policy cho phép.

---

## 491.10 — Delete policy

Registry policy có thể cho phép deletion nhưng ecosystem nên ưu tiên immutable retention.

---

## 491.11 — Content hash

Mỗi artifact có cryptographic content hash.

---

## 491.12 — CAS

Content-addressable storage:

```text id="w5m9r3"
hash(bytes) → object
```

---

## 491.13 — CAS immutability

Một hash không được map sang nội dung khác.

---

## 491.14 — Artifact types

CAS có thể lưu:

```text id="c7x2n8"
source archive
binary library
executable
documentation
metadata
debug symbols
SBOM-like inventory
```

---

## 491.15 — Manifest hash

Manifest có canonical serialization và hash.

---

## 491.16 — Package digest

Package release có root digest liên kết manifest + artifacts.

---

## 491.17 — Merkle structure

Registry có thể dùng Merkle trees để verify large package collections.

Không bắt buộc registry implementation.

---

## 491.18 — Artifact chunking

Large artifacts có thể chia chunks để transfer/resume.

---

## 491.19 — Chunk verification

Chunk phải verify trước khi ghép artifact.

---

## 491.20 — Resumable download

Package manager nên hỗ trợ resume.

---

## 491.21 — Parallel download

Independent artifacts/chunks có thể download parallel.

---

## 491.22 — Network protocol

Protocol phải support:

```text id="r4m8q1"
metadata lookup
version query
artifact lookup
artifact download
upload
signature retrieval
documentation retrieval
```

---

## 491.23 — Protocol independence

Registry protocol không phụ thuộc một HTTP implementation cụ thể ở language core.

HTTP implementation có thể sử dụng 454.

---

## 491.24 — Authentication

Private registries có thể yêu cầu authentication.

---

## 491.25 — Authorization

Publisher permissions và reader permissions phải tách biệt.

---

## 491.26 — Anonymous public read

Public registry có thể cho anonymous read.

Policy registry quyết định.

---

## 491.27 — Credentials

Credentials không được lưu vào package manifest hoặc build artifacts.

---

## 491.28 — Credential provider

Package manager có thể lấy credential từ:

```text id="f6p2k9"
OS credential store
environment
external credential helper
```

---

## 491.29 — Credential logging

Credentials phải được redacted khỏi logs.

---

## 491.30 — Dependency resolution

Package manager phải resolve dependency graph deterministic.

---

## 491.31 — Lockfile

Lockfile lưu chính xác:

```text id="x1m7c4"
package
version
source registry
content hash
dependencies
```

---

## 491.32 — Registry substitution

Nếu cùng package/version nhưng content hash khác:

```text id="j8r3n5"
reject
```

---

## 491.33 — Lockfile integrity

Lockfile itself có thể được hashed/signed theo project policy.

---

## 491.34 — Source replacement

Registry mirror có thể serve same content hash.

---

## 491.35 — Mirror

Mirror chỉ là alternate source của immutable artifact.

---

## 491.36 — Mirror verification

Client verify artifact hash sau download.

---

## 491.37 — Mirror trust

Mirror không cần được trusted nếu content verification và signature verification đủ.

---

## 491.38 — Offline vendoring

Project có thể copy dependencies vào workspace:

```text id="u5q9m2"
vendor/
```

---

## 491.39 — Vendor mode

Vendor mode không được truy cập network.

---

## 491.40 — Air-gapped registry

Private registry có thể chạy hoàn toàn offline.

---

## 491.41 — Dependency source priority

Project có thể configure:

```text id="n2x8k6"
vendor
→ local
→ mirror
→ registry
```

---

## 491.42 — No hidden registry

Compiler không tự fetch package khi `build` nếu package resolution policy không cho phép.

---

## 491.43 — Explicit network fetch

Network fetch phải thuộc package-manager operation.

---

## 491.44 — Reproducible fetch

Package content phải được xác định bằng hash.

---

## 491.45 — Source package

Source package chứa:

- source;
- manifest;
- metadata;
- optional docs/tests.

---

## 491.46 — Binary package

Binary package có thể chứa precompiled:

- libraries;
- metadata;
- generics;
- target artifacts.

---

## 491.47 — Binary compatibility

Binary package phải match:

```text id="g3m8w1"
Axiom ABI
target
CPU features
compiler compatibility
stdlib
semantic metadata schema
```

---

## 491.48 — Generic metadata

447 precompiled generic instances tích hợp registry artifact model.

---

## 491.49 — Debug symbols

Debug symbols có thể được publish separately.

---

## 491.50 — Documentation

485 docs có thể được publish separately hoặc bundled.

---

## 491.51 — Artifact selection

Package manager chọn artifact theo:

```text id="p8r4m2"
host
target
architecture
ABI
features
profile
compiler compatibility
```

---

## 491.52 — Universal package

Package có thể chứa nhiều target artifacts.

---

## 491.53 — Missing artifact

Nếu binary artifact không tồn tại, package manager có thể fallback source build nếu source available.

---

## 491.54 — Source fallback

Source fallback phải obey lockfile/build environment.

---

## 491.55 — Build-from-source preference

Project policy có thể yêu cầu source-only builds.

---

## 491.56 — Binary-only policy

Enterprise/project policy có thể cấm source download.

---

## 491.57 — Registry metadata API

Conceptual:

```text id="q6n1x9"
get_package()
list_versions()
get_manifest()
get_artifact()
get_signature()
```

---

## 491.58 — Search API

Registry có thể hỗ trợ:

```text id="v4m7p2"
name
namespace
keywords
target
feature
```

Search result không phải dependency resolution.

---

## 491.59 — Registry indexing

Registry index có thể be incremental.

---

## 491.60 — Package metadata schema

Schema phải versioned.

---

## 491.61 — Schema compatibility

New registry metadata không được silently reinterpret bởi old client.

---

## 491.62 — Registry API version

Protocol API version tách khỏi package version.

---

## 491.63 — Upload transaction

Publish flow:

```text id="s2x8m4"
validate
→ upload
→ verify
→ sign
→ publish
```

---

## 491.64 — Publish validation

Registry có thể validate:

- manifest;
- package name;
- version;
- artifact hashes;
- signatures;
- dependency metadata.

---

## 491.65 — Namespace ownership

Registry phải có ownership rules cho namespace.

---

## 491.66 — Package name squatting

Registry policy có thể có namespace reservation/ownership.

---

## 491.67 — Publisher identity

447 signing/provenance được tích hợp.

---

## 491.68 — Signature types

Có thể sign:

```text id="k5p1w8"
manifest
artifact
release
publisher metadata
```

---

## 491.69 — Signature verification

Client verify trước khi use theo configured trust policy.

---

## 491.70 — Transparency

Registry có thể publish immutable release log.

---

## 491.71 — Audit log

Publish/revoke/yank operations có audit trail.

---

## 491.72 — Malicious package

Registry infrastructure không thể đảm bảo package code không malicious.

Client phải có trust/provenance/policy layer.

---

## 491.73 — Vulnerability metadata

Registry có thể expose security advisories.

---

## 491.74 — Advisory ≠ compiler error

Security advisory không tự động biến thành language semantic failure.

---

## 491.75 — Dependency policy

Project có thể enforce:

```text id="z7m3q9"
allowed registries
allowed licenses
allowed publishers
minimum versions
blocked packages
```

---

## 491.76 — Policy evaluation

Policy evaluation phải deterministic.

---

## 491.77 — License policy

Có thể reject packages theo project license policy.

---

## 491.78 — Target policy

Project có thể restrict supported targets.

---

## 491.79 — Feature policy

Project có thể pin allowed dependency features.

---

## 491.80 — Dependency graph lock

Resolved dependency graph được ghi vào lockfile.

---

## 491.81 — Registry outage

Existing cached/vendor dependencies phải tiếp tục build offline.

---

## 491.82 — Cache corruption

Corrupt package cache phải fetch/rebuild lại.

---

## 491.83 — Registry migration

Project có thể chuyển registry nếu content hashes remain compatible.

---

## 491.84 — Namespace migration

Package rename/move cần explicit metadata redirect.

---

## 491.85 — Deprecation

Registry có thể mark package/version deprecated.

---

## 491.86 — Yank semantics

Yanked release không tự động invalidate existing lockfile.

---

## 491.87 — Version conflict

Resolver phải report exact dependency conflict.

---

## 491.88 — Feature conflict

Feature incompatibility phải được report machine-readable.

---

## 491.89 — Target conflict

Target-incompatible package phải fail resolution/build rõ ràng.

---

## 491.90 — Dependency cycles

Package dependency cycles phải obey 432 rules.

---

## 491.91 — Build dependencies

Build-time dependencies phải phân biệt runtime dependencies.

---

## 491.92 — Dev dependencies

Test/documentation dependencies có thể được phân loại riêng.

---

## 491.93 — Optional dependencies

Optional dependencies chỉ activate khi feature/config yêu cầu.

---

## 491.94 — Dependency provenance graph

Graph:

```text id="m8q2c5"
Package
 ↓
Dependency
 ↓
Registry
 ↓
Artifact
 ↓
Signature
 ↓
Source/Build provenance
```

---

## 491.95 — AI registry query

AI có thể query:

```text id="r5n1x7"
package_versions()
package_dependencies()
artifact_targets()
provenance()
signature()
documentation()
```

---

## 491.96 — AI dependency explanation

Tool có thể giải thích:

```text id="f4p8m2"
why package selected
why version selected
why rebuild required
why binary rejected
```

---

## 491.97 — No opaque resolver

Resolver decisions phải machine-readable.

---

## 491.98 — Build integration

491 integrates:

```text id="x3m7q9"
447 Package Ecosystem
483 Toolchain
487 Build Graph
489 Deployment
```

---

## 491.99 — Performance

Registry/client phải support:

- compression;
- parallel downloads;
- local cache;
- delta transfer;
- resumable transfer.

---

## 491.100 — Hard invariants

1. Registry khác package manager.
2. Registry khác compiler.
3. Multiple registries được hỗ trợ.
4. Package identity ổn định.
5. Namespace được hỗ trợ.
6. Manifest structured.
7. Published version immutable.
8. Yank được hỗ trợ.
9. CAS được hỗ trợ.
10. Artifact content hash được yêu cầu.
11. CAS mapping immutable.
12. Multiple artifact types được hỗ trợ.
13. Manifest có canonical hash.
14. Package root digest được hỗ trợ.
15. Merkle verification có thể được hỗ trợ.
16. Large artifacts có chunking.
17. Chunks được verify.
18. Download resumable.
19. Parallel transfer được hỗ trợ.
20. Registry protocol có metadata/artifact/signature operations.
21. Protocol không bị khóa vào language core HTTP implementation.
22. Private registry authentication được hỗ trợ.
23. Authorization được phân biệt.
24. Credentials không nằm trong artifacts.
25. Credential provider được hỗ trợ.
26. Credentials được redacted khỏi logs.
27. Dependency resolution deterministic.
28. Lockfile chứa content hashes.
29. Content mismatch phải reject.
30. Mirror được hỗ trợ.
31. Mirror content phải verify.
32. Offline vendoring được hỗ trợ.
33. Air-gapped registry được hỗ trợ.
34. Source priority explicit.
35. Compiler không implicit fetch registry.
36. Network package fetch là explicit.
37. Source packages được hỗ trợ.
38. Binary packages được hỗ trợ.
39. Binary compatibility được verify.
40. Generic metadata được hỗ trợ.
41. Debug artifacts có thể publish riêng.
42. Documentation có thể publish.
43. Artifact selection target-aware.
44. Multi-target package được hỗ trợ.
45. Source fallback được hỗ trợ.
46. Source-only policy được hỗ trợ.
47. Binary-only policy được hỗ trợ.
48. Registry metadata API versioned.
49. Search tách khỏi resolution.
50. Registry index incremental.
51. Publish là transactional.
52. Publish validation được hỗ trợ.
53. Namespace ownership explicit.
54. Publisher identity được hỗ trợ.
55. Artifact signatures được hỗ trợ.
56. Signature verification client-side.
57. Transparency log có thể được hỗ trợ.
58. Audit log được hỗ trợ.
59. Registry không tuyên bố package code safe chỉ từ publication.
60. Security advisories được hỗ trợ.
61. Advisory không tự động là compiler semantic error.
62. Dependency policies được hỗ trợ.
63. Policy evaluation deterministic.
64. License policies được hỗ trợ.
65. Target policies được hỗ trợ.
66. Feature policies được hỗ trợ.
67. Lockfile graph deterministic.
68. Cached dependencies hoạt động offline.
69. Corrupt cache không làm sai build.
70. Registry migration được hỗ trợ.
71. Package rename/move có explicit migration.
72. Deprecation metadata được hỗ trợ.
73. Yank không tự động break existing lockfiles.
74. Resolver conflicts machine-readable.
75. Feature conflicts machine-readable.
76. Target conflicts machine-readable.
77. Package cycles obey dependency rules.
78. Build/dev/runtime dependencies được phân biệt.
79. Optional dependencies explicit.
80. Provenance graph được hỗ trợ.
81. AI registry queries được hỗ trợ.
82. Resolver explanation machine-readable.
83. Registry client performance được tối ưu.
84. Registry không phải mandatory online service.
85. Package manager không phải compiler backend.
86. Package artifacts không chứa signing private keys.
87. Remote artifact không được trusted chỉ dựa URL.
88. Content hash là integrity anchor.
89. Signature là authenticity/trust evidence, không phải correctness proof.
90. **Axiom ecosystem phải có registry protocol mở và content-addressed artifact infrastructure, nhưng project vẫn phải build được hoàn toàn offline từ vendor/cache/lockfile mà không phụ thuộc vào một registry hay server trung tâm duy nhất.**

**BOOTSTRAP-491 hoàn tất / LOCKED.**

---

# BOOTSTRAP-492 — PACKAGE RESOLUTION 2.0, FEATURE RESOLUTION, SEMVER, WORKSPACE DEPENDENCIES, MONOREPO & REPRODUCIBLE DEPENDENCY SELECTION

492 đi sâu vào **bộ máy chọn dependency**. Đây là phần cần tách biệt với registry 491.

Mục tiêu:

```text id="c4m8x2"
Manifest
   ↓
Requirements
   ↓
Version Solver
   ↓
Feature Solver
   ↓
Target Constraints
   ↓
Dependency Graph
   ↓
Lockfile
   ↓
Build Graph
```

---

## 492.1 — Resolver ≠ Registry

Resolver có thể hoạt động hoàn toàn offline nếu metadata đã tồn tại.

---

## 492.2 — Version requirement

Dependency có thể khai báo range:

```text id="r7n2p5"
exact
compatible
range
branch/revision
path
workspace
```

---

## 492.3 — Exact version

Ví dụ:

```text
version = "1.4.2"
```

---

## 492.4 — Version range

Resolver phải có deterministic semantics cho ranges.

---

## 492.5 — Semantic versioning

Major/minor/patch semantics từ 447 được dùng khi package chọn SemVer.

---

## 492.6 — Pre-release

Pre-release versions phải có ordering explicit.

---

## 492.7 — Build metadata

Build metadata không được làm thay đổi precedence nếu tuân SemVer.

---

## 492.8 — Multiple versions

Dependency graph có thể chứa nhiều versions của cùng package nếu API/runtime policy cho phép.

---

## 492.9 — Version unification

Resolver có thể unify compatible requirements.

Không được unify nếu làm thay đổi semantics.

---

## 492.10 — Conflict

Nếu requirements không có common compatible version:

```text id="m3x8q1"
resolution failure
```

---

## 492.11 — Conflict explanation

Resolver phải xuất:

```text id="p6r2n9"
root requirement
→ dependency chain
→ conflicting requirements
```

---

## 492.12 — Deterministic solver

Cùng manifest + metadata + lock state phải produce cùng solution.

---

## 492.13 — Solver ordering

Solver không được phụ thuộc hash-map iteration order.

---

## 492.14 — Feature flags

Feature resolution là explicit.

---

## 492.15 — Feature activation

Feature có thể activate dependency:

```text id="k8w4m1"
feature gui
 → gui-package
```

---

## 492.16 — Default features

Package có thể define default features.

Project có thể disable nếu policy cho phép.

---

## 492.17 — Feature unification

Nếu nhiều dependents request same package features, resolver phải có defined unification semantics.

---

## 492.18 — Feature conflict

Mutually exclusive features phải được khai báo.

---

## 492.19 — Weak features

Có thể hỗ trợ feature dependencies chỉ activate khi parent feature active.

---

## 492.20 — Target conditions

Dependencies có thể conditional theo target:

```text id="f5q9c3"
target.os == "windows"
```

---

## 492.21 — Build dependencies

Target-specific build dependencies được resolve riêng.

---

## 492.22 — Platform dependency

Ví dụ Windows-only dependency không được đưa vào Linux graph.

---

## 492.23 — Optional dependencies

Optional package chỉ xuất hiện khi activated.

---

## 492.24 — Dev dependency

Dev-only dependency không đi vào production artifact closure.

---

## 492.25 — Build dependency

Build script dependency không tự trở thành runtime dependency.

---

## 492.26 — Proc/generator dependency

Code generators phải được classify riêng.

---

## 492.27 — Dependency classes

Canonical:

```text id="x7m2q8"
normal
optional
dev
build
generator
target-specific
```

---

## 492.28 — Path dependencies

Local path dependencies được hỗ trợ.

---

## 492.29 — Workspace dependencies

Workspace member có thể depend trực tiếp member khác.

---

## 492.30 — Workspace identity

Workspace package vẫn có package identity riêng.

---

## 492.31 — Monorepo

Nhiều package có thể cùng repository.

---

## 492.32 — Workspace lockfile

Workspace có thể share lockfile.

---

## 492.33 — Partial builds

Build một package không nhất thiết build toàn workspace.

---

## 492.34 — Workspace graph

```text id="j4p8n1"
workspace
 ├── app
 ├── core
 ├── gui
 └── tools
```

---

## 492.35 — Cycles

Package dependency cycles phải bị reject trừ khi một cơ chế đặc biệt được định nghĩa rõ.

---

## 492.36 — Target graph

Dependency graph có thể differ theo target.

---

## 492.37 — Feature graph

Graph phải record feature activation provenance.

---

## 492.38 — Resolver provenance

Mỗi selected package có:

```text id="q2m7x6"
selected_by
requirements
features
target
registry
```

---

## 492.39 — Lockfile

Lockfile canonical data:

```text id="w8n3r5"
package identity
version
source
content hash
dependencies
features
target conditions
```

---

## 492.40 — Lockfile generation

`axiom package lock` có thể regenerate lockfile.

---

## 492.41 — Frozen lock

CI có thể yêu cầu:

```text id="s6x1p9"
no lockfile changes
```

---

## 492.42 — Lock update

Package update phải explicit.

---

## 492.43 — Minimal update

Tool có thể update only selected dependency and affected graph.

---

## 492.44 — Full update

Có thể update toàn dependency graph.

---

## 492.45 — Update policy

Project có thể restrict update range.

---

## 492.46 — Security update

Security advisory có thể trigger candidate update.

Resolver vẫn phải tuân policy.

---

## 492.47 — Yanked versions

Resolver không chọn yanked versions cho new resolution nếu policy cấm.

---

## 492.48 — Existing lock

Existing lockfile có thể continue using yanked version nếu package vẫn available.

---

## 492.49 — Offline resolution

Resolver phải hoạt động nếu tất cả required metadata local.

---

## 492.50 — Missing metadata

Resolver báo chính xác package metadata nào thiếu.

---

## 492.51 — Registry priority

Registry priority explicit, deterministic.

---

## 492.52 — Source replacement

Mirror/vendor source có thể replace registry source khi content hash match.

---

## 492.53 — Dependency override

Development override có thể redirect dependency.

---

## 492.54 — Override provenance

Override phải xuất hiện trong lock/build explanation.

---

## 492.55 — Patch dependencies

Patch mechanism có thể thay package source/version cho development.

---

## 492.56 — Patch safety

Patch không được silently apply trong release ngoài declared configuration.

---

## 492.57 — Git/revision dependencies

Có thể reference immutable commit/revision.

---

## 492.58 — Branch dependencies

Branch dependency không reproducible tuyệt đối.

Project phải lock resolved revision.

---

## 492.59 — Tag dependencies

Tag cũng phải resolve thành immutable revision/hash trong lockfile.

---

## 492.60 — Path reproducibility

Path dependencies trong published package phải có publish-safe behavior.

---

## 492.61 — Workspace publish

Workspace package publish phải loại bỏ local-only dependency references.

---

## 492.62 — Package rename

Renamed packages phải có explicit migration metadata.

---

## 492.63 — Alias

Dependency alias có thể map local name → package identity.

---

## 492.64 — Duplicate package names

Aliases giúp tránh local namespace collision.

---

## 492.65 — Dependency namespace

Package namespace và local dependency name là hai khái niệm khác nhau.

---

## 492.66 — Version source selection

Resolver phải ưu tiên lockfile content hash.

---

## 492.67 — Binary/source selection

Project có thể policy:

```text id="n4x8m2"
prefer-binary
prefer-source
source-only
binary-only
```

---

## 492.68 — ABI compatibility

Binary selection phải verify ABI.

---

## 492.69 — Compiler compatibility

Binary selection phải verify compiler/metadata compatibility.

---

## 492.70 — CPU feature compatibility

Binary artifact phải match required CPU features.

---

## 492.71 — Stdlib compatibility

Binary package phải match compatible Axiom stdlib ABI/semantic identity.

---

## 492.72 — Generic compatibility

Precompiled generics phải match generic metadata/compiler constraints.

---

## 492.73 — Target runtime

Runtime profile/capability requirements phải được resolve.

---

## 492.74 — Feature-to-artifact mapping

Feature activation có thể thay đổi artifact closure.

---

## 492.75 — Resolver explanation

Canonical:

```text id="u7m3q9"
why_selected(package)
why_feature_enabled(package, feature)
why_version(package)
why_binary(package)
why_rebuilt(package)
```

---

## 492.76 — AI dependency analysis

AI có thể query toàn dependency graph mà không cần parse tất cả manifests manually.

---

## 492.77 — Dependency graph export

Formats:

```text id="p8c4m1"
JSON
DOT
lockfile
human-readable
```

---

## 492.78 — Graph determinism

Graph serialization phải deterministic.

---

## 492.79 — Resolver cache

Resolution results có thể cache bằng hash của:

```text id="x5n2r7"
manifests
metadata
lockfile
configuration
target
features
```

---

## 492.80 — Resolver cache correctness

Stale metadata không được produce invalid dependency solution.

---

## 492.81 — Registry metadata freshness

Metadata cache có expiration/update policy nhưng lockfile remains correctness anchor.

---

## 492.82 — Workspace member discovery

Workspace membership phải deterministic.

---

## 492.83 — Package discovery

Implicit package discovery không được scan arbitrary filesystem outside project roots.

---

## 492.84 — Build scripts

Build dependencies resolved before build-script execution.

---

## 492.85 — Generator isolation

Generators run according to 487 hermetic rules.

---

## 492.86 — Dependency feature provenance

Compiler/AI có thể biết feature nào activated dependency.

---

## 492.87 — Dependency API graph

446 metadata có thể link package dependency → exported symbols.

---

## 492.88 — API impact

486 can analyze package updates against dependent source.

---

## 492.89 — ABI impact

447 ABI compatibility checker integrates resolver.

---

## 492.90 — Documentation impact

485 documentation dependencies can be tracked.

---

## 492.91 — Security policy

490 trust policies can restrict package sources/publishers/capabilities.

---

## 492.92 — Deployment integration

489 can consume resolved production dependency closure.

---

## 492.93 — Build graph integration

487 receives exact resolved graph rather than re-solving during compilation.

---

## 492.94 — Reproducible dependency closure

Lockfile + content hashes must identify complete production dependency closure.

---

## 492.95 — Development closure

Dev/build/generator dependencies must be distinguishable from production closure.

---

## 492.96 — Dependency pruning

Unused optional dependencies should not enter artifact closure.

---

## 492.97 — Duplicate artifact deduplication

Same content hash may be stored once.

---

## 492.98 — Resolution diagnostics

Errors must identify:

```text id="m1q7x8"
root
chain
constraint
candidate
reason
```

---

## 492.99 — No arbitrary solver heuristics

Tie-breaking must be deterministic and documented.

---

## 492.100 — Hard invariants

1. Resolver khác registry.
2. Resolver offline hoạt động khi metadata đủ.
3. Version requirements có semantics deterministic.
4. Exact versions được hỗ trợ.
5. Version ranges được hỗ trợ.
6. SemVer được hỗ trợ.
7. Pre-release ordering explicit.
8. Build metadata semantics explicit.
9. Multiple versions có thể coexist.
10. Version unification không được đổi semantics.
11. Conflicts fail clearly.
12. Conflict explanation có dependency chain.
13. Solver deterministic.
14. Solver không phụ thuộc hash iteration order.
15. Features explicit.
16. Default features được hỗ trợ.
17. Feature unification có semantics rõ.
18. Feature conflicts được detect.
19. Target conditions được hỗ trợ.
20. Build dependencies được phân biệt.
21. Platform dependencies được hỗ trợ.
22. Optional dependencies explicit.
23. Dev dependencies không vào production closure mặc định.
24. Build dependencies không tự thành runtime dependencies.
25. Generator dependencies được phân loại.
26. Dependency classes canonical.
27. Path dependencies được hỗ trợ.
28. Workspace dependencies được hỗ trợ.
29. Monorepo được hỗ trợ.
30. Workspace lockfile được hỗ trợ.
31. Partial workspace build được hỗ trợ.
32. Workspace graph deterministic.
33. Cycles được xử lý theo rules rõ ràng.
34. Target graph được hỗ trợ.
35. Feature provenance được lưu.
36. Selected package có provenance.
37. Lockfile có content hashes.
38. Lockfile generation deterministic.
39. Frozen lock mode được hỗ trợ.
40. Dependency update explicit.
41. Minimal update được hỗ trợ.
42. Full update được hỗ trợ.
43. Update policy configurable.
44. Security advisories không bypass resolver policy.
45. Yank semantics rõ.
46. Existing lockfile có thể preserve yanked dependency khi policy cho phép.
47. Offline resolution được hỗ trợ.
48. Missing metadata diagnostics rõ.
49. Registry priority deterministic.
50. Mirror/vendor replacement phải hash-match.
51. Development overrides explicit.
52. Override provenance được ghi.
53. Patch dependencies explicit.
54. Release build không silently inherit dev patches.
55. Revision dependencies được hỗ trợ.
56. Branch dependencies phải lock revision.
57. Tag dependencies phải lock immutable revision.
58. Path dependencies publish-safe.
59. Workspace publishing validate local references.
60. Package rename có migration.
61. Dependency alias được hỗ trợ.
62. Local dependency name khác package identity.
63. Lockfile hash là selection anchor.
64. Binary/source preference configurable.
65. ABI compatibility được verify.
66. Compiler compatibility được verify.
67. CPU features được verify.
68. Stdlib compatibility được verify.
69. Generic compatibility được verify.
70. Runtime capability requirements được resolve.
71. Feature-to-artifact changes được tracked.
72. Resolver explanation được hỗ trợ.
73. AI dependency analysis được hỗ trợ.
74. Graph export deterministic.
75. Resolver cache được hỗ trợ.
76. Resolver cache correctness được bảo đảm.
77. Metadata freshness không phá lockfile correctness.
78. Workspace discovery deterministic.
79. Package discovery bounded.
80. Build scripts resolve dependencies trước execution.
81. Generator isolation tích hợp 487.
82. Feature provenance queryable.
83. Dependency API graph tích hợp 446.
84. API impact tích hợp 486.
85. ABI impact tích hợp 447.
86. Documentation dependency impact tích hợp 485.
87. Security policy tích hợp 490.
88. Deployment closure tích hợp 489.
89. Build graph nhận resolved graph.
90. Production dependency closure reproducible.
91. Development dependency closure được phân biệt.
92. Optional dependency pruning được hỗ trợ.
93. Same-content artifacts được deduplicate.
94. Resolution diagnostics machine-readable.
95. Tie-breaking deterministic.
96. Resolver không dựa hidden network.
97. Resolver không tự thay đổi lockfile trong build thường.
98. Package manager/compiler boundaries được giữ.
99. Dependency selection phải explainable cho developer và AI.
100. **Axiom dependency resolution phải biến một tập manifest + policy + metadata thành một dependency closure deterministic, reproducible và explainable; lockfile/content hash là correctness anchor, còn registry, mirror, binary cache và network chỉ là các nguồn cung cấp dữ liệu.**

**BOOTSTRAP-492 hoàn tất / LOCKED.**

---

# TIẾN ĐỘ

```text
479  Contracts / Design-by-Contract                  LOCKED
480  Sanitizers / Runtime Validation                 LOCKED
481  Profiling / Tracing                             LOCKED
482  Self-hosting / Bootstrap Trust                  LOCKED
483  Toolchain / Cross Compilation                   LOCKED
484  Language Evolution / Editions                  LOCKED
485  Documentation / Knowledge Graph                 LOCKED
486  Semantic Refactoring / Change Impact            LOCKED
487  Build Graph / Hermetic / Remote Cache            LOCKED
488  Staged Bootstrap / Self-hosting Compiler         LOCKED
489  Native Distribution / Installer / Updates        LOCKED
490  Application Security / Sandbox / Capabilities   LOCKED
491  Registry / CAS / Mirrors / Offline Vendor        LOCKED
492  Dependency Resolution / Workspace / Features     LOCKED
```

**Task kế tiếp: `BOOTSTRAP-493 — PACKAGE ABI, BINARY INTERFACE DISTRIBUTION, PRECOMPILED GENERICS, MODULE INTERFACE FILES & FAST BINARY CONSUMPTION`.**