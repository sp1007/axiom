# BOOTSTRAP-406 — Package Registry, Dependency Trust, Distribution, ABI/Artifact Ecosystem & Extension Model

Đây là bước tiếp theo sau **Package/Build (402)**, **Testing/Diagnostics (403)**, **Metaprogramming (404)** và **IDE/AI (405)**.

Mục tiêu của 406 là hoàn thiện **hệ sinh thái phân phối của Axiom**: từ một package trên máy lập trình viên → package registry → dependency resolution → artifact/cache → kiểm tra tính toàn vẹn → ký/xác thực → sử dụng binary/source → plugin/extension.

Điểm quan trọng: **package ecosystem không được trở thành một runtime hay một phần bắt buộc của ngôn ngữ**.

---

# 1. Mục tiêu kiến trúc

Axiom phải hỗ trợ đồng thời:

```text
Local source package
       │
       ├── local dependency
       ├── workspace dependency
       ├── path dependency
       ├── git/source dependency
       ├── registry package
       ├── binary package
       └── system/FFI package
```

và:

```text
Package
   ↓
Registry
   ↓
Resolution
   ↓
Verification
   ↓
Source / Interface / Binary Artifact
   ↓
CompilerDB / BuildGraph
   ↓
Final Artifact
```

Registry **không được trở thành một thành phần bắt buộc của compiler**.

Axiom phải có thể build:

```text
axiom build --offline
```

và thậm chí:

```text
axiom build --freestanding
```

mà không cần truy cập registry.

---

# 2. Phân biệt các khái niệm

Axiom phải phân biệt rõ:

```text
Package
Module
Artifact
Interface
Registry
Repository
Dependency
Plugin
Extension
Tool
Runtime
```

Không được gom tất cả thành "library".

### Package

Đơn vị phân phối source/interface/binary.

### Module

Đơn vị namespace/compiler.

### Artifact

Kết quả build.

Ví dụ:

```text
libfoo.axlib
foo.exe
foo.dll
foo.so
foo.dylib
foo.a
foo.o
foo.wasm
```

### Interface

Thông tin compiler cần để sử dụng package mà không cần toàn bộ source.

### Registry

Dịch vụ lưu package và metadata.

### Repository

Nguồn package có thể là:

```text
registry
git
filesystem
HTTP
vendor directory
local cache
```

### Plugin

Code mở rộng chạy **ngoài semantic core**, với ABI/capability rõ ràng.

---

# 3. Package Identity

Package identity không chỉ là:

```text
name + version
```

Mà phải bao gồm:

```text
PackageIdentity =
    namespace
    name
    version
    source identity
```

Ví dụ:

```text
org.example.math@1.4.2
```

Source identity có thể là:

```text
registry digest
git commit
content hash
local immutable identity
```

Do đó:

```text
foo@1.2.0
```

từ hai source khác nhau không nhất thiết là cùng package.

---

# 4. Package Manifest

Manifest phải là dữ liệu có schema rõ ràng.

Ví dụ:

```text
package {
    name = "image"
    version = "2.4.0"

    targets = [
        "library"
    ]

    dependencies = {
        math = "^1.8"
        codec = "^3.1"
    }

    features = [
        "png",
        "jpeg",
        "gpu"
    ]
}
```

Compiler không nên parse manifest bằng một ngôn ngữ script tùy ý.

Manifest phải:

- deterministic
- typed
- versioned
- machine-readable
- dễ cache
- dễ phân tích bởi AI

---

# 5. Dependency Sources

Core ecosystem hỗ trợ:

```text
path
git
registry
archive
binary
system
vendor
workspace
```

Ví dụ:

```text
dependencies = {
    foo = {
        source = "registry"
        version = "^2.1"
    }

    bar = {
        source = "git"
        revision = "..."
    }

    local = {
        source = "path"
        path = "../local"
    }
}
```

---

# 6. Dependency Resolution

Resolution phải deterministic.

Nếu:

```text
A → B ^1.0
A → C ^1.0
C → B ^1.5
```

compiler phải xác định chính xác graph.

Nếu có thể dùng:

```text
B 1.7
```

cho cả hai thì có thể unify.

Nếu không:

```text
B 1.2
B 2.0
```

có thể cùng tồn tại nếu package identity khác version và semantic model cho phép.

---

# 7. Dependency Graph ≠ Build Graph

Tiếp tục nguyên tắc 402:

```text
Dependency Graph
```

trả lời:

> package nào phụ thuộc package nào?

Trong khi:

```text
Build Graph
```

trả lời:

> artifact nào cần được tạo từ input nào?

Ví dụ:

```text
A
├── B
└── C
```

không có nghĩa compiler chỉ có ba node.

BuildGraph có thể là:

```text
B source
 ↓
B interface
 ↓
B object
 ↓
B library
 ↓
A compile
 ↓
A link
```

---

# 8. Interface Artifact

Đây là thành phần rất quan trọng.

Package binary nên có:

```text
foo.axiface
```

chứa:

```text
public types
public functions
public traits
public constants
generic definitions/metadata
ABI
calling convention
layout information
effects
capabilities
compiler semantic version
target information
```

Compiler có thể compile:

```text
import foo
```

mà không cần load toàn bộ implementation.

---

# 9. Source Compatibility

Phải phân biệt:

### Source compatibility

Code client vẫn compile.

### Semantic compatibility

Behavior được đảm bảo theo contract.

### ABI compatibility

Binary gọi nhau được.

### Binary compatibility

Artifact cũ tiếp tục hoạt động với artifact mới.

### Interface compatibility

Interface metadata vẫn tương thích.

Không được coi:

```text
same API
```

là đồng nghĩa với:

```text
same ABI
```

---

# 10. Semantic Versioning

Registry có thể sử dụng SemVer:

```text
MAJOR.MINOR.PATCH
```

nhưng compiler không được mù quáng tin rằng:

```text
1.3 → 1.4
```

luôn compatible.

Axiom nên có:

```text
interface compatibility checker
```

để kiểm tra thay đổi thực tế.

Ví dụ:

```text
axiom package diff foo@1.2 foo@1.3
```

có thể báo:

```text
Added public function
Compatible

Changed struct layout
ABI breaking

Removed trait method
Source breaking
```

---

# 11. Package Lock

Build reproducibility cần lockfile:

```text
axiom.lock
```

Lock phải chứa ít nhất:

```text
package identity
resolved version
source identity
content digest
dependency resolution
features
target-specific resolution
```

Không lock chỉ bằng version.

Ví dụ:

```text
foo 1.4.2
sha256 = ...
source = registry://...
```

---

# 12. Content Integrity

Mọi artifact/package tải về phải có content identity.

Ví dụ:

```text
PackageDigest
ArtifactDigest
InterfaceDigest
SourceDigest
```

Compiler không được tin:

```text
filename
version string
URL
```

là bằng chứng identity.

---

# 13. Package Signing

Axiom ecosystem hỗ trợ chữ ký số.

Model:

```text
Package
   ↓
Digest
   ↓
Signature
   ↓
Publisher Identity
```

Có thể:

```text
verify package
```

trước khi compiler sử dụng.

Nhưng:

> **Signature xác nhận nguồn gốc/integrity, không xác nhận code an toàn.**

Package ký bởi publisher vẫn có thể chứa bug.

---

# 14. Trust Model

Trust phải có nhiều tầng:

```text
UNTRUSTED
VERIFIED
SIGNED
TRUSTED_PUBLISHER
LOCAL_TRUST
SYSTEM_TRUST
```

Không biến signature thành:

```text
"đã ký = an toàn"
```

---

# 15. Dependency Policy

Project có thể đặt policy:

```text
dependencies {
    allow_unsigned = false
    allow_git = false
    allow_binary = false
}
```

hoặc:

```text
trusted_publishers = [...]
```

Compiler/build engine thực hiện policy.

---

# 16. Reproducible Artifact

Một package binary cần có metadata:

```text
compiler semantic version
target
optimization
features
dependencies
interface hash
source hash
build configuration
```

Artifact identity:

```text
ArtifactIdentity =
    package identity
    target
    compiler semantic version
    configuration
    dependency identities
    source/interface fingerprints
```

---

# 17. Binary Cache

402 đã định nghĩa content-addressed build cache.

406 mở rộng thành:

```text
Local Cache
Remote Cache
Registry Artifact Cache
CI Cache
Shared Organization Cache
```

Nhưng tất cả dùng cùng semantic identity.

Ví dụ:

```text
Source
 ↓
Semantic Fingerprint
 ↓
Cache Key
 ↓
Artifact
```

Nếu compiler semantic version thay đổi:

```text
cache miss
```

nếu thay đổi có khả năng ảnh hưởng artifact.

---

# 18. Remote Cache

Build có thể:

```text
compile
 ↓
check local cache
 ↓
check remote cache
 ↓
download verified artifact
```

Remote cache không được tự động tin tưởng.

Phải verify:

```text
digest
target
interface
compiler compatibility
dependency identity
```

---

# 19. Source Distribution

Package registry có thể cung cấp:

```text
source package
```

Ví dụ:

```text
foo-1.4.2.axpkg
```

Compiler có thể:

```text
download
verify
extract
index
compile
cache
```

---

# 20. Binary Distribution

Có thể phân phối:

```text
foo.axlib
foo.a
foo.so
foo.dll
foo.dylib
```

kèm:

```text
foo.axiface
```

Ví dụ:

```text
foo/
├── package.meta
├── interface.axiface
├── libfoo.axlib
└── debug/
```

Binary package phải khai báo:

```text
target
ABI
CPU features
OS
architecture
pointer width
calling convention
```

---

# 21. Multi-target Package

Một package có thể chứa nhiều artifact:

```text
foo/
├── linux-x64/
├── linux-arm64/
├── windows-x64/
├── macos-arm64/
└── wasm32/
```

Resolution chọn artifact dựa trên:

```text
TargetTriple
ABI
CPU baseline
features
link mode
```

Không được chọn chỉ dựa trên OS.

---

# 22. Plugin Architecture

Đây là nơi cần cực kỳ cẩn thận.

Plugin **không được phép trực tiếp sửa compiler semantic state**.

Không:

```text
Plugin → mutate MIR
Plugin → disable ownership verifier
Plugin → modify type system
```

Thay vào đó:

```text
Plugin
  ↓
Typed Extension API
  ↓
Compiler
```

---

# 23. Plugin ABI

Plugin API phải versioned:

```text
Axiom Plugin ABI v1
```

Plugin khai báo:

```text
plugin {
    name = "..."
    version = "..."
    abi = 1
}
```

Compiler kiểm tra:

```text
ABI compatibility
capabilities
target
compiler API version
```

---

# 24. Plugin Capability

Plugin phải khai báo capability.

Ví dụ:

```text
ReadSemanticModel
GenerateDeclarations
ReadDiagnostics
RegisterAnalyzer
RegisterFormatter
RegisterCodeAction
ReadFilesystem
ExecuteProcess
Network
```

Không được mặc định có toàn quyền.

---

# 25. Extension Categories

Nên chia thành:

```text
Analyzer
Formatter
Linter
Code Generator
Derive Provider
IDE Extension
Debugger Extension
Profiler Extension
Build Extension
Target Backend
Tool
```

Các loại này có quyền khác nhau.

---

# 26. Compiler Plugin vs Library

Cần phân biệt rất rõ.

Library:

```text
Axiom source
 ↓
compiler
 ↓
application
```

Plugin:

```text
Axiom compiler
 ↓
plugin ABI
 ↓
compiler extension
```

Plugin không phải dependency runtime của application.

---

# 27. Backend Plugin

Target backend có thể là extension cấp thấp:

```text
Axiom
 ↓
LIR
 ↓
Target Backend
 ↓
Machine Code
```

Nhưng backend API phải ổn định và được compiler kiểm soát.

Trong giai đoạn đầu compiler có thể sử dụng backend ngoài.

Trong self-host:

```text
Axiom compiler
 ↓
Axiom LIR
 ↓
Axiom backend
```

---

# 28. Registry Architecture

Registry nên có protocol độc lập:

```text
Client
   ↓
Registry API
   ├── Package Metadata
   ├── Package Versions
   ├── Source Artifact
   ├── Interface Artifact
   ├── Binary Artifact
   ├── Signature
   └── Documentation
```

Registry không quyết định semantics của compiler.

---

# 29. Private Registry

Phải hỗ trợ:

```text
public registry
private registry
enterprise registry
local registry
offline registry
```

Ví dụ:

```text
registry.company.local
```

có thể chứa package nội bộ.

---

# 30. Vendor Mode

Project phải có thể đóng gói dependency:

```text
vendor/
    foo/
    bar/
    codec/
```

sau đó:

```text
axiom build --offline
```

không cần network.

Đây rất quan trọng cho:

- embedded
- secure build
- CI
- reproducible build
- air-gapped environment.

---

# 31. Dependency Overrides

Development cần:

```text
override foo → ../foo
```

nhưng override phải được biểu diễn rõ trong BuildGraph.

Không được để:

```text
local filesystem
```

âm thầm thay đổi dependency identity.

---

# 32. Workspace

Workspace có thể chứa:

```text
workspace
├── compiler
├── std
├── runtime
├── cli
├── gui
└── tools
```

Package trong cùng workspace có thể dùng semantic dependency trực tiếp.

Compiler tránh rebuild nếu semantic fingerprint không thay đổi.

---

# 33. Package Documentation

Interface artifact có thể chứa:

```text
doc comments
examples
API metadata
source locations
semantic signatures
```

IDE/AI đọc interface trực tiếp.

Không cần parse source nếu package chỉ được phân phối binary.

---

# 34. AI Package Interface

Đây là điểm nối với 405.

Package nên cung cấp:

```text
AISchema
```

cho phép AI query:

```text
What functions exist?
What type implements Trait X?
Which API returns Result?
Which functions require capability Y?
Which API is async?
Which types own storage?
```

AI không cần đọc hàng nghìn file source.

---

# 35. Package Security Metadata

Package metadata có thể chứa:

```text
license
publisher
signature
source repository
provenance
build provenance
dependencies
permissions/capabilities
```

Nhưng compiler phải phân biệt:

```text
metadata claim
compiler-verified fact
publisher assertion
```

Ví dụ:

```text
publisher says: "no network"
```

không đồng nghĩa:

```text
compiler proves: no network
```

---

# 36. Package Provenance

Build provenance:

```text
Source
 ↓
Dependencies
 ↓
Compiler
 ↓
Configuration
 ↓
Build
 ↓
Artifact
```

được lưu thành graph.

Có thể truy vấn:

```text
axiom package provenance foo
```

và biết artifact được tạo từ đâu.

---

# 37. Plugin Isolation

Plugin có thể chạy:

```text
in-process
sandboxed process
remote service
```

mặc định nên ưu tiên:

```text
sandboxed
```

đối với plugin không trusted.

Plugin crash không được làm compiler mất trạng thái semantic database nếu có thể tránh.

---

# 38. Không để Ecosystem phá Core

Đây là invariant kiến trúc quan trọng nhất:

```text
Core Language
       ↑
Compiler
       ↑
Package ecosystem
       ↑
Registry
```

Không:

```text
Registry
   ↓
thay đổi semantics
```

Không package nào được:

```text
disable safety
change ownership rules
change primitive semantics
change ABI silently
```

---

# 39. CompilerDB mở rộng

406 bổ sung:

```text
PackageRegistryDB
PackageSourceDB
PackageArtifactDB
PackageInterfaceDB
PackageSignatureDB
PackageTrustDB
PackagePolicyDB

DependencyResolutionDB
ArtifactResolutionDB
RemoteCacheDB
PackageProvenanceDB

PluginDB
PluginManifestDB
PluginCapabilityDB
PluginABI DB
PluginSandboxDB

CompatibilityDB
DistributionDB
```

Tất cả phải kết nối với:

```text
CompilerDB
BuildGraphDB
DependencyGraphDB
SemanticSnapshotDB
AISemanticDB
```

---

# 40. Ecosystem IR

Có thể định nghĩa:

## APKG — Axiom Package IR

Biểu diễn:

```text
Package
Identity
Version
Source
Dependency
Feature
Target
Interface
Artifact
Signature
Trust
Provenance
```

và:

## AEXT — Axiom Extension IR

Biểu diễn:

```text
Plugin
ABI
Capabilities
Entry points
Extension points
Version
Sandbox policy
```

---

# 41. Proof Model

Package ecosystem cũng phải có proof.

Ví dụ:

```text
PackageIdentityProof
DependencyResolutionProof
PackageIntegrityProof
SignatureVerificationProof
TrustPolicyProof
InterfaceCompatibilityProof
ABICompatibilityProof
ArtifactCompatibilityProof
CacheValidityProof
ProvenanceProof
PluginABIProof
PluginCapabilityProof
PluginIsolationProof
```

Compiler/BuildDB lưu chúng như semantic facts.

---

# 42. Các invariant bắt buộc

Đóng băng bộ invariant:

### APKG-01
Package identity phải deterministic.

### APKG-02
Source identity phải phân biệt với package version.

### APKG-03
Dependency resolution phải deterministic.

### APKG-04
Lockfile phải đủ để tái tạo dependency resolution.

### APKG-05
Dependency Graph và Build Graph phải độc lập.

### APKG-06
Artifact identity phải deterministic.

### APKG-07
Artifact cache phải content/semantic-addressed.

### APKG-08
Cache không được dùng artifact không tương thích compiler semantic version.

### APKG-09
Interface artifact phải có semantic identity.

### APKG-10
Binary package phải khai báo target/ABI.

### APKG-11
Source compatibility và ABI compatibility là hai khái niệm riêng.

### APKG-12
Registry không được quyết định language semantics.

### APKG-13
Compiler phải hỗ trợ offline package resolution.

### APKG-14
Vendor mode phải tái tạo được dependency graph.

### APKG-15
Package digest phải xác định chính xác nội dung package.

### APKG-16
Signature phải xác minh trên digest cụ thể.

### APKG-17
Signature không được coi là bằng chứng code correctness.

### APKG-18
Trust policy phải độc lập với package metadata.

### APKG-19
Remote cache phải được integrity-check.

### APKG-20
Binary artifact phải được kiểm tra target compatibility.

### APKG-21
Plugin ABI phải versioned.

### APKG-22
Plugin capability phải explicit.

### APKG-23
Plugin không được bypass semantic verification.

### APKG-24
Plugin không được sửa ownership semantics.

### APKG-25
Plugin không được sửa type-system semantics.

### APKG-26
Plugin không được tự ý thay đổi ABI.

### APKG-27
Plugin failure không được làm thay đổi program semantics.

### APKG-28
Generated code từ plugin phải quay lại compiler verification pipeline.

### APKG-29
Package provenance phải có thể truy nguyên artifact → inputs.

### APKG-30
Package ecosystem phải là extension của compiler/build architecture, không phải một runtime bắt buộc.

---

# 43. Kiến trúc tổng thể sau BOOTSTRAP-406

Axiom lúc này có một chuỗi rất rõ:

```text
                         ┌──────────────────────┐
                         │     Registry         │
                         │ source/binary/signing│
                         └──────────┬───────────┘
                                    │
                                    ▼
┌──────────┐      ┌───────────────────────────┐
│ Workspace│─────▶│ Package / Dependency DB  │
└──────────┘      └─────────────┬─────────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │    BuildGraph      │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │    CompilerDB      │
                     └─────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
          Compiler          IDE/AI           Plugins
              │                │                │
              ▼                ▼                ▼
           Artifact         Semantic         Extensions
              │
              ▼
       Cache / Distribution
```

Điểm quan trọng là **mọi đường đều quay về CompilerDB + BuildGraph + Verification**, thay vì tạo các hệ thống semantics riêng biệt.

---

## Kết luận của BOOTSTRAP-406

Sau 402–406, Axiom đã có:

```text
Core Language
Memory / Ownership
Concurrency
GPU
Scientific Computing
I/O
Storage
Networking
Package / Build
Testing / Debugging
Metaprogramming
IDE / AI
Distribution / Registry
Plugin / Extension
```

và nguyên tắc xuyên suốt là:

> **Compiler là nguồn sự thật duy nhất về semantics.**

Package manager, IDE, AI, registry, plugin và build cache đều phải **hỏi compiler hoặc CompilerDB**, không được tự xây một semantic model thứ hai.

### Trạng thái
**BOOTSTRAP-406: SPECIFIED / FROZEN**

Bước kế tiếp hợp lý là đi xuống **chính nội bộ compiler**: thiết kế **CompilerDB + query engine + incremental compilation + dependency/fingerprint engine** ở mức đủ chi tiết để bắt đầu implement compiler thật, thay vì tiếp tục mở rộng thêm các domain ứng dụng.