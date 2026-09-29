# BOOTSTRAP-329 — AXIOM PACKAGE MANAGER, REGISTRY & DEPENDENCY RESOLUTION ENGINE

Sau 328, Axiom đã có target matrix và cross-compilation. Bước tiếp theo là giải quyết **dependency/package ecosystem** ở cấp compiler/build system: package version, dependency graph, source/binary/semantic artifact, target-specific package, lockfile, registry, cache và reproducible builds.

Điểm quan trọng: **Package Manager không được trở thành một phần của ngôn ngữ Core.** Nó là infrastructure của hệ sinh thái.

---

## 1. Mục tiêu

Axiom cần một hệ thống có thể xử lý:

```text
project
 ├── local package
 ├── registry package
 ├── git/source dependency
 ├── binary package
 ├── system package
 └── platform-specific dependency
```

và tạo:

```text
Source
  ↓
Package Resolution
  ↓
Exact Dependency Graph
  ↓
Semantic Interface (.axif)
  ↓
Target-specific artifacts
  ↓
Build Graph
```

---

# 2. Package ≠ Library ≠ Module

Phải phân biệt rõ:

```text
Package
    ↓
Modules
    ↓
Library
    ↓
Binary / Component
```

### Package

Đơn vị dependency/version/distribution.

### Module

Đơn vị namespace/source organization.

### Library

Đơn vị link/semantic consumption.

### Component

Đơn vị runtime/dynamic boundary đã định nghĩa ở 325.

Một package có thể chứa:

```text
library
binary
tests
examples
.axif
source
assets
build metadata
```

---

# 3. Package identity

Không dùng tên package đơn thuần.

```text
PackageId {
    registry
    namespace
    name
}
```

Ví dụ:

```text
axiom.io/math
```

khác:

```text
github.com/foo/math
```

dù đều tên `math`.

Identity phải chống name collision.

---

# 4. Package manifest

Ví dụ:

```toml
[package]
name = "image"
version = "2.4.1"
edition = "1"

[targets]
supports = [
    "windows-x86_64",
    "linux-x86_64",
    "linux-aarch64"
]

[dependencies]
math = "^3.2"
codec = "1.7"

[features]
default = ["png"]
png = []
jpeg = []

[build]
library = true
```

Manifest phải là **data**, không phải code executable tùy ý.

---

# 5. Semantic package identity

Package fingerprint:

```text
PackageFingerprint =
    hash(
        package_id
        manifest
        source
        dependency_lock
        build_config
        compiler_semantic_version
    )
```

Nhưng binary artifact fingerprint phải bổ sung:

```text
TargetFingerprint
ABI
CPU features
runtime profile
optimization profile
```

---

# 6. Versioning

Dùng semantic versioning làm **compatibility convention**, nhưng compiler không được giả định:

```text
major == always breaking
```

Package có thể khai báo compatibility contract rõ ràng.

Ví dụ:

```text
API-compatible
ABI-compatible
semantic-compatible
target-compatible
```

---

# 7. Dependency requirement

Một dependency có thể khai báo:

```text
exact
compatible-range
branch
revision
path
workspace
registry
system
```

Ví dụ:

```toml
math = "3.2"
```

khác:

```toml
math = "=3.2.7"
```

và:

```toml
math = { git = "...", rev = "..." }
```

---

# 8. Lockfile

Build reproducibility yêu cầu:

```text
axiom.lock
```

ghi chính xác:

```text
package
version
source
revision
checksum
dependencies
target constraints
artifact fingerprint
```

Ví dụ:

```text
image@2.4.1
  source = registry:axiom.io
  checksum = ...
```

Build CI dùng lockfile phải resolve **chính xác cùng dependency graph**.

---

# 9. Dependency graph

Resolver tạo:

```text
DependencyGraph
```

node:

```text
PackageInstance
```

edge:

```text
DependencyEdge
```

Mỗi node có:

```text
package identity
version
features
target
ABI
semantic fingerprint
```

---

# 10. Version conflict

Ví dụ:

```text
A
 └── math 2.x

B
 └── math 3.x
```

Resolver không được tùy tiện chọn một version.

Có ba khả năng:

```text
same compatible instance
multiple versions
conflict
```

Nếu semantic/API incompatible nhưng package cho phép side-by-side:

```text
math@2
math@3
```

có thể coexist.

---

# 11. Package instance ≠ Package version

Một package version có thể có nhiều instance:

```text
math@3.2
 ├── feature=simd
 ├── feature=scalar
 ├── target=linux
 └── target=windows
```

Vì vậy identity build-level phải bao gồm:

```text
PackageInstanceId {
    PackageId
    Version
    FeatureSet
    Target
    ABI
}
```

---

# 12. Feature resolution

Feature phải được resolve trước semantic compilation.

Ví dụ:

```text
default
 ├── std
 └── png

minimal
 └── core
```

Feature graph phải hỗ trợ:

```text
feature A enables B
feature A enables dependency C
feature A conflicts B
```

Không để feature resolution thành một macro system.

---

# 13. Target-specific dependencies

Ví dụ:

```toml
[dependencies]
common = "1.0"

[target.windows.dependencies]
win32 = "4.0"

[target.linux.dependencies]
epoll = "2.1"
```

Resolver tạo graph riêng theo target.

```text
Common
   │
   ├── Windows → Win32
   │
   └── Linux → Epoll
```

---

# 14. Optional dependencies

Dependency có thể:

```text
optional = true
```

và chỉ được resolve nếu feature yêu cầu.

Điều này hỗ trợ binary nhỏ:

```text
CLI app
```

không tự kéo:

```text
GUI
GPU
Network
Unicode database
```

---

# 15. Source package và binary package

Axiom phải hỗ trợ hai dạng:

### Source

```text
.ax
.axif
manifest
```

### Binary

```text
.axif
.a
.lib
.so
.dll
.dylib
```

Binary package phải có semantic interface `.axif`.

Compiler không cần source nếu interface và required implementation artifact đầy đủ.

---

# 16. `.axif` là package interface

Một package binary nên expose:

```text
package.axif
```

chứa:

```text
public declarations
types
traits
generic constraints
ABI
ownership
effects
FFI
target
optimization summaries
security metadata
```

Do đó dependency resolution có thể diễn ra **trước khi tải source**.

---

# 17. Source privacy

Package không bắt buộc công khai implementation.

Có thể phân phối:

```text
library.axif
library.a
```

mà không có source.

Compiler vẫn biết:

```text
API
types
ABI
ownership
effects
target support
```

nhưng không biết implementation.

---

# 18. Registry

Registry không nên chỉ là file server.

Registry metadata:

```text
Package
Version
Manifest
Checksums
Targets
.axif
Artifacts
Signatures
Dependencies
Security advisories
```

Artifact:

```text
package
 ├── source
 ├── axif
 ├── windows-x64
 ├── linux-x64
 ├── linux-arm64
 └── wasm
```

---

# 19. Registry federation

Không ép chỉ có một registry toàn cầu.

Package source có thể là:

```text
official registry
private registry
company registry
local registry
git
filesystem
artifact server
```

Identity phải bao gồm registry namespace để tránh collision.

---

# 20. Package trust

Package metadata có:

```text
TrustLevel
```

ví dụ:

```text
Official
Verified
Signed
Unverified
Local
Foreign
```

Nhưng trust không đồng nghĩa code safe.

Một package signed vẫn có thể:

```text
unsafe
FFI
filesystem
network
process
```

Security subsystem phải xét **capabilities**, không chỉ chữ ký.

---

# 21. Package signature

Package artifact có thể được ký:

```text
Signature {
    signer
    algorithm
    key_id
    artifact_fingerprint
    timestamp
}
```

Signature phải bao phủ canonical metadata.

Không ký riêng binary rồi để manifest thay đổi.

---

# 22. Reproducibility

Package build identity phải bao gồm:

```text
source fingerprint
dependency lock
compiler version
target
features
comptime inputs
build scripts
SDK
```

Nếu một dependency binary được dùng:

```text
artifact checksum
```

phải được khóa.

---

# 23. Build scripts

Không nên có arbitrary build script mặc định.

Thay vào đó:

```text
BuildStep
```

phải khai báo capabilities:

```text
ReadSource
ReadPackage
WriteGenerated
ExecuteTool
Network
Environment
```

Tương thích trực tiếp với Comptime capability model.

Một package không thể âm thầm:

```text
download Internet
execute arbitrary program
đọc toàn bộ filesystem
```

trong reproducible build.

---

# 24. Generated source

Package có thể generate:

```text
generated.ax
generated.axif
generated bindings
```

nhưng generated declarations phải quay lại pipeline:

```text
Generate
 ↓
Parse
 ↓
Resolve
 ↓
Type Check
 ↓
Ownership
 ↓
Effect
 ↓
ABI
 ↓
Verify
```

Không có generated-code escape hatch.

---

# 25. System dependencies

Package có thể yêu cầu:

```text
system library
framework
SDK
tool
```

Ví dụ:

```toml
[system]
libraries = ["OpenSSL"]
```

Resolver phải kiểm tra target:

```text
Linux → libssl.so
Windows → ...
```

Không resolve system dependency theo host.

---

# 26. Native library package

Ví dụ:

```text
openssl.axpkg
```

có:

```text
openssl.axif
linux-x86_64/libssl.so
linux-aarch64/libssl.so
windows-x86_64/ssleay.lib
```

và FFI contract.

Package manager chọn đúng artifact.

---

# 27. Dependency capability requirements

Package có thể khai báo:

```text
requires:
    filesystem
    network
    threads
```

Build system dùng information này để:

- security analysis
- freestanding validation
- WASM compatibility
- mobile sandbox validation
- component loading

---

# 28. Circular dependencies

Package graph phải là DAG ở mức package initialization/link semantics.

Nếu:

```text
A → B
B → A
```

resolver phải phân biệt:

```text
type-only dependency
compile-time dependency
link dependency
runtime dependency
```

Một cycle ở metadata/type level có thể hợp lệ.

Một cycle initialization có thể không.

Không dùng một quy tắc đơn giản cho tất cả.

---

# 29. Workspace

Nhiều package có thể nằm trong một workspace:

```text
workspace
├── compiler
├── std
├── runtime
├── cli
└── tools
```

Workspace cho phép:

```text
shared lockfile
shared source cache
incremental compilation
local package references
```

nhưng mỗi package vẫn có identity riêng.

---

# 30. Package overlays

Cho development:

```text
dependency foo
```

có thể redirect:

```text
registry → local path
```

nhưng fingerprint phải thay đổi.

Không được coi local replacement tương đương binary registry artifact.

---

# 31. Dependency patches

Hỗ trợ:

```toml
[patch]
foo = { path = "../foo" }
```

Resolver ghi rõ override trong lockfile.

Build artifact phải chứa provenance:

```text
foo
source = local override
```

---

# 32. Semantic compatibility checking

Resolver có thể so sánh `.axif`:

```text
old.axif
new.axif
```

và biết:

```text
API compatible
semantic compatible
ABI compatible
target compatible
```

Điều này dùng trực tiếp ABI-324.

Ví dụ:

```text
function added
```

có thể compatible.

Trong khi:

```text
struct field layout changed
```

có thể phá ABI nếu type stable.

---

# 33. Dependency selection algorithm

Resolver thực hiện:

```text
1. Parse manifests
2. Identify package roots
3. Resolve source/registry identity
4. Apply target constraints
5. Apply feature constraints
6. Select versions
7. Detect conflicts
8. Resolve package instances
9. Validate .axif compatibility
10. Validate system requirements
11. Generate lock graph
12. Compute fingerprints
13. Produce BuildGraph
```

Sau bước 13 mới chuyển sang compiler BuildGraph-305.

---

# 34. Package cache

Cache hierarchy:

```text
Global Cache
    │
    ├── Source
    ├── Metadata
    ├── .axif
    ├── Object
    ├── Library
    └── Final Artifact
```

Key bằng content/semantic fingerprints.

Cache corruption:

```text
checksum mismatch
```

→ discard + reacquire/rebuild.

---

# 35. Remote cache

Cho phép:

```text
Developer
    ↓
Remote Cache
    ↓
.axif/object/artifact
```

Nhưng remote artifact phải verify:

```text
content hash
semantic fingerprint
target fingerprint
compiler version
signature if required
```

Không tin cache chỉ vì server trả HTTP 200.

---

# 36. Dependency graph và AI tooling

`.axif` + package metadata cho phép AI/compiler tooling hỏi:

```text
package API
package dependencies
unsafe surface
FFI surface
platform requirements
capabilities
ABI requirements
public types
trait relations
```

mà không cần đọc toàn bộ source.

Điều này đặc biệt phù hợp với mục tiêu Axiom là **AI-friendly language**.

---

# 37. Package documentation metadata

Package có thể expose machine-readable:

```text
API
Examples
Docs
Safety contracts
Performance notes
Platform restrictions
```

nhưng documentation không được trở thành semantic authority.

Semantic truth vẫn là:

```text
compiler specification
.axif
verified declarations
```

---

# 38. Compiler architecture

Thêm:

```text
compiler/package/
    manifest/
        manifest.ax
        parser.ax
        validator.ax

    identity/
        package_id.ax
        package_instance.ax
        fingerprint.ax

    registry/
        registry_client.ax
        registry_index.ax
        artifact_store.ax

    resolve/
        resolver.ax
        version_solver.ax
        feature_solver.ax
        target_solver.ax
        conflict_solver.ax

    lock/
        lockfile.ax
        lock_resolver.ax

    cache/
        package_cache.ax
        artifact_cache.ax
        remote_cache.ax

    trust/
        signature.ax
        provenance.ax
        trust_policy.ax

    build/
        package_build.ax
        build_script.ax
```

CompilerDB:

```text
PackageManifestDB
PackageIdentityDB
PackageRegistryDB
PackageResolutionDB
PackageLockDB
PackageCacheDB
PackageTrustDB
```

---

# 39. API chính

```text
load_manifest()
validate_manifest()

resolve_package()
resolve_version()
resolve_features()
resolve_target_variant()

check_dependency_conflict()
check_package_compatibility()

load_axif()
validate_package_axif()

compute_package_fingerprint()
compute_instance_fingerprint()

read_lockfile()
write_lockfile()
verify_lockfile()

fetch_package()
verify_package()
verify_signature()

query_registry()
publish_package()

query_package_api()
query_package_capabilities()
query_package_targets()

build_package()
build_workspace()
```

CLI:

```text
axiom package init
axiom package add
axiom package remove
axiom package update
axiom package resolve
axiom package build
axiom package publish
axiom package inspect
axiom package tree
axiom package verify
axiom package audit
axiom package cache
```

---

# 40. Package manifest nên giữ nhỏ

Không biến manifest thành một programming language.

Nó chỉ nên mô tả:

```text
identity
version
dependencies
features
targets
artifacts
capabilities
build requirements
exports
```

Logic phức tạp phải nằm trong compiler/package engine.

---

# 41. Invariants

```text
APKG-01
Package identity must be globally unambiguous within a registry namespace.

APKG-02
Package version does not by itself guarantee semantic compatibility.

APKG-03
Exact dependency resolution must be reproducible.

APKG-04
Lockfile records the complete resolved dependency graph.

APKG-05
Dependency resolution is target-aware.

APKG-06
Dependency resolution is feature-aware.

APKG-07
Host platform must never determine target dependency selection.

APKG-08
Binary packages must provide sufficient semantic interface metadata.

APKG-09
.axif is the semantic interface authority for binary Axiom packages.

APKG-10
Foreign libraries must declare FFI contracts.

APKG-11
System libraries are target-specific dependencies.

APKG-12
Package capabilities are explicit.

APKG-13
Build capabilities are explicit.

APKG-14
Arbitrary build-script capabilities are not granted implicitly.

APKG-15
Package signatures cover canonical package identity and artifact metadata.

APKG-16
Checksums are verified before trusting cached/fetched artifacts.

APKG-17
Cache identity includes semantic and target fingerprints.

APKG-18
Local overrides are represented explicitly in provenance.

APKG-19
Dependency cycles are classified by semantic dependency kind.

APKG-20
Type-only cycles may be valid when initialization/link semantics remain valid.

APKG-21
Multiple versions may coexist only when package/module identity prevents ambiguity.

APKG-22
Feature resolution occurs before final semantic compilation.

APKG-23
Unused optional dependencies must not enter the final build graph.

APKG-24
Package target requirements must be validated before code generation.

APKG-25
Package ABI requirements must be validated before linking.

APKG-26
Package capability requirements participate in security analysis.

APKG-27
Package platform requirements participate in target compatibility.

APKG-28
Generated package code enters normal compiler verification.

APKG-29
Package metadata must be deterministic and canonical.

APKG-30
A package manager must never silently substitute a semantically different artifact.
```

---

# 42. Kiến trúc ecosystem sau task này

Axiom hiện có chuỗi khá hoàn chỉnh:

```text
324  ABI
 ↓
325  Component / Plugin
 ↓
326  FFI
 ↓
327  Platform / OS
 ↓
328  Cross Target
 ↓
329  Package / Dependency
 ↓
Build Graph
 ↓
Compiler
 ↓
Native Artifact
```

Và quan trọng nhất:

```text
                Package
                   │
             Dependency Graph
                   │
          ┌────────┴────────┐
          │                 │
       Semantic          Target
       Interface         Variant
        (.axif)             │
          │                 │
          └────────┬────────┘
                   ▼
              Build Graph
                   │
             Verified MIR
                   │
              Native Code
```

Như vậy Axiom không chỉ là một compiler có ngôn ngữ mới, mà bắt đầu hình thành **một ecosystem hoàn chỉnh**, trong đó package manager, `.axif`, ABI, FFI, platform và compiler đều dùng chung một semantic model thay vì mỗi subsystem tự phát triển một hệ thống type/dependency riêng.