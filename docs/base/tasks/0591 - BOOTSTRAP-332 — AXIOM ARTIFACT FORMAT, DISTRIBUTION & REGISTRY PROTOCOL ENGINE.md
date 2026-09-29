# BOOTSTRAP-332 — AXIOM ARTIFACT FORMAT, DISTRIBUTION & REGISTRY PROTOCOL ENGINE

Sau 331, Axiom đã có **package resolution + trust + sandbox + provenance + reproducible build**. Bước tiếp theo là đặc tả sâu **cách artifact thực sự được đóng gói, lưu trữ, truyền tải và phân phối**.

Điểm quan trọng là không để Package Manager trở thành một hệ thống “download ZIP rồi chạy”. Axiom cần một artifact protocol đủ chặt để hỗ trợ:

- source package
- binary package
- `.axif`
- native libraries
- components/plugins
- debug symbols
- SDK
- cross-platform artifacts
- remote cache
- local cache
- registry mirror
- offline/air-gapped distribution

---

## 1. Mục tiêu

Kiến trúc:

```text
Package Source
      │
      ▼
Package Manifest
      │
      ▼
Artifact Builder
      │
      ├── Source Artifact
      ├── Binary Artifact
      ├── AXIF
      ├── Native Libraries
      ├── Debug Info
      └── Provenance
              │
              ▼
       Artifact Bundle
              │
       ┌──────┴──────┐
       ▼             ▼
    Registry       Local Store
       │             │
       └──────┬──────┘
              ▼
        Package Resolver
              │
              ▼
           Compiler
```

Artifact format phải độc lập với transport.

Có thể truyền bằng:

```text
HTTPS
filesystem
Git
S3-like storage
LAN mirror
USB/offline media
custom registry protocol
```

nhưng artifact semantics không thay đổi.

---

# 2. Phân biệt Package và Artifact

Đây là distinction bắt buộc.

### Package

Đơn vị logical:

```text
PackageId
Version
Manifest
Dependencies
Features
```

### Artifact

Một representation cụ thể của package:

```text
Target
ABI
Architecture
Optimization
Runtime
ArtifactKind
```

Một package có thể có nhiều artifact:

```text
myapp 1.4.0
 ├── linux-x86_64
 ├── linux-aarch64
 ├── windows-x86_64
 ├── macos-arm64
 └── wasm32
```

---

# 3. ArtifactKind

Đề xuất:

```text
Source
Binary
StaticLibrary
DynamicLibrary
Component
AXIF
DebugInfo
SDK
Tool
GeneratedSource
Resource
Bundle
```

Không được dùng filename extension làm semantic authority.

Ví dụ:

```text
foo.axif
```

không tự động được coi là AXIF nếu internal metadata nói khác.

---

# 4. Artifact Descriptor

Mỗi artifact có:

```text
ArtifactDescriptor {
    artifact_id
    package_id
    version

    kind
    target
    abi
    compiler
    language_edition

    semantic_fingerprint
    abi_fingerprint
    content_hash

    size
    compression

    dependencies
    capabilities

    provenance
    signatures
}
```

Descriptor được canonicalize trước khi hash/sign.

---

# 5. Content Addressing

Artifact storage ưu tiên:

```text
ArtifactId = Hash(canonical artifact content)
```

Ví dụ:

```text
artifact/
    sha256/
        ab/
            ab91...
```

Package/version chỉ là logical lookup.

Content hash mới là identity vật lý.

---

# 6. Immutable Artifact

Sau khi artifact đã publish:

```text
ArtifactId
```

không thể thay đổi.

Nếu nội dung thay đổi:

```text
old ArtifactId != new ArtifactId
```

Dù:

```text
PackageId
Version
Filename
```

giống nhau.

Registry không được phép silently overwrite artifact.

---

# 7. Package Version Index

Registry có index:

```text
PackageId
    ↓
Version
    ↓
ArtifactSet
```

Ví dụ:

```text
graphics@3.2.0
 ├── linux-x86_64 → hash A
 ├── windows-x86_64 → hash B
 └── macos-arm64 → hash C
```

Version metadata không chứa binary trực tiếp.

---

# 8. Target Artifact Selection

Resolver chọn artifact theo:

```text
TargetSpec
ABI
CPU features
Runtime profile
Build profile
Artifact kind
```

Không được chọn chỉ dựa trên:

```text
os
architecture
```

Ví dụ hai binary đều:

```text
linux-x86_64
```

nhưng một binary yêu cầu:

```text
AVX2
```

còn binary kia không.

Đây là hai artifact khác nhau về target compatibility.

---

# 9. Universal Artifact

Axiom có thể hỗ trợ bundle:

```text
UniversalArtifact
```

chứa:

```text
linux-x86_64
linux-aarch64
...
```

Nhưng mỗi embedded artifact vẫn có identity riêng.

```text
UniversalHash
    ├── ArtifactHash A
    ├── ArtifactHash B
    └── ArtifactHash C
```

---

# 10. Artifact Bundle

Một binary package có thể có:

```text
bundle/
    manifest
    axif/
    binary/
    debug/
    native/
    provenance/
    signatures/
```

Nhưng bundle layout chỉ là packaging detail.

Semantic metadata phải có canonical representation riêng.

---

# 11. Compression

Compression không được thay đổi artifact identity.

Ví dụ:

```text
foo.bin
foo.bin.zstd
foo.bin.gz
```

đều có thể giải nén thành:

```text
ArtifactHash = H(binary)
```

Transport encoding có hash riêng nếu cần.

Do đó:

```text
ContentIdentity
```

khác:

```text
TransportIdentity
```

---

# 12. Chunking

Artifact lớn có thể chia chunk:

```text
Artifact
 ├── chunk 0
 ├── chunk 1
 ├── chunk 2
 └── ...
```

Manifest:

```text
ChunkManifest {
    chunk_size
    chunk_hashes
    merkle_root
}
```

Cho phép:

- resume download
- parallel download
- partial verification
- deduplication

---

# 13. Merkle Tree

Artifact lớn nên hỗ trợ Merkle structure:

```text
          Root
        /      \
      H01      H23
     /  \     /  \
   H0   H1   H2   H3
```

Cho phép verify một phần artifact mà không cần hash toàn bộ lại.

---

# 14. Registry Protocol

Registry không chỉ là HTTP server.

Semantic protocol:

```text
ResolvePackage
GetManifest
GetArtifactDescriptor
GetArtifact
GetAXIF
GetSignature
GetAttestation
PublishArtifact
QueryVersions
QueryTargets
```

Transport layer có thể là:

```text
HTTP
HTTPS
local filesystem
IPC
```

---

# 15. Registry API

Ví dụ conceptual:

```text
GET /package/<id>
GET /package/<id>/versions
GET /artifact/<hash>
GET /artifact/<hash>/metadata
GET /artifact/<hash>/axif
GET /artifact/<hash>/attestation
```

Nhưng URL không phải semantic contract.

Registry implementation có thể sử dụng protocol khác.

---

# 16. Registry Discovery

Project có thể chỉ định:

```text
registry = "official"
```

hoặc:

```text
registry = "company"
```

Identity phải bao gồm registry namespace:

```text
RegistryNamespace + PackageName
```

Tránh collision:

```text
registryA/foo
registryB/foo
```

---

# 17. Registry Mirror

Mirror:

```text
Official Registry
       │
       ▼
Company Mirror
       │
       ▼
Developer
```

Mirror không được thay đổi:

```text
ArtifactHash
AXIF
Signature
Provenance
```

Nó chỉ thay đổi transport/location.

---

# 18. Mirror Trust

Client có thể yêu cầu:

```text
MirrorPolicy {
    require_origin_signature = true
}
```

Khi đó mirror không cần được tin tuyệt đối.

Client chỉ cần tin:

```text
origin signer
```

và verify content hash.

---

# 19. Offline Registry

Một registry có thể được export:

```text
axiom registry export
```

thành:

```text
registry.bundle
```

Bao gồm:

```text
package index
manifests
artifacts
AXIF
signatures
attestations
```

Sau đó:

```text
axiom registry import registry.bundle
```

trên máy không có internet.

---

# 20. Registry Snapshot

Registry snapshot có:

```text
SnapshotId
Timestamp
RootHash
PackageIndexHash
Signature
```

Build reproducibility có thể khóa:

```text
RegistrySnapshotId
```

thay vì phụ thuộc registry mutable state.

---

# 21. Registry không quyết định semantic truth

Registry nói:

> artifact này tồn tại.

Compiler quyết định:

> artifact này có tương thích semantic/ABI/target hay không.

Do đó pipeline:

```text
Registry
    ↓
Artifact
    ↓
Hash Verification
    ↓
AXIF Verification
    ↓
ABI Verification
    ↓
Target Verification
    ↓
Compiler Acceptance
```

---

# 22. Source Distribution

Source package cần canonical archive.

Không được để:

```text
file ordering
directory metadata
timestamp
filesystem permissions
```

làm source fingerprint thay đổi ngoài ý muốn.

Source artifact canonicalization phải quy định:

```text
path encoding
path ordering
newline handling
metadata
permissions
symlinks
special files
```

---

# 23. Symlink

Source package mặc định không cho symlink escape.

Ví dụ:

```text
package/
   src/
      link -> /etc/passwd
```

phải bị reject hoặc encode như explicit foreign object.

Không được resolve symlink ra ngoài package root trong hermetic build.

---

# 24. Generated Source

Generated source là artifact riêng:

```text
GeneratedSource
```

phải có provenance:

```text
GeneratedBy
GeneratorVersion
GeneratorHash
InputHashes
Configuration
```

Ví dụ:

```text
schema.proto
    ↓
protoc
    ↓
generated.ax
```

Compiler phải biết mối quan hệ này.

---

# 25. Native Library Artifact

Package có thể chứa:

```text
libfoo.a
foo.dll
libfoo.so
foo.dylib
```

nhưng phải có:

```text
NativeLibraryContract
```

gồm:

```text
target
ABI
symbol set
dependencies
runtime requirements
license metadata
FFI contract
```

Không được load native library chỉ vì filename phù hợp.

---

# 26. `.axif` distribution

Binary package tối thiểu phải có:

```text
binary
AXIF
```

nếu muốn được compiler sử dụng như binary dependency.

`.axif` phải fingerprint artifact mà nó mô tả.

```text
AXIF.artifact_hash
==
Binary.artifact_hash
```

nếu contract yêu cầu exact binary pairing.

---

# 27. Debug artifact

Debug symbols có thể phân phối riêng:

```text
Binary
DebugInfo
```

liên kết bằng:

```text
ArtifactId
DebugFingerprint
```

Production binary không cần mang toàn bộ debug information.

---

# 28. Source server

Debug information có thể trỏ đến source artifact:

```text
SourceArtifactHash
```

Debugger tải source tương ứng từ:

```text
local cache
registry
symbol server
```

không phụ thuộc path trên máy build.

---

# 29. Component distribution

Component-325 sử dụng artifact format:

```text
Component
    + AXIF
    + ComponentManifest
    + ABI
    + SecurityMetadata
```

Component identity không phụ thuộc filename.

---

# 30. Plugin distribution

Plugin package phải khai báo:

```text
PluginContract {
    component_id
    version
    ABI
    target
    capabilities
    lifecycle
    entrypoints
}
```

Loader không được load arbitrary binary rồi cast function pointer.

---

# 31. SDK artifact

SDK package có thể chứa:

```text
headers/      // nếu FFI
axif/
libraries/
tools/
platform metadata
```

Nhưng SDK identity phải bao gồm:

```text
Target
SDKVersion
ABI
PlatformVersion
```

---

# 32. Tool artifact

Axiom toolchain có thể phân phối compiler tools:

```text
axiomc
axiom-link
axiom-fmt
axiom-lsp
```

Tool artifact cũng dùng content-addressed storage.

Điều này cho phép:

```text
compiler version pinning
```

trong reproducible builds.

---

# 33. Artifact Garbage Collection

Local artifact store sẽ tích tụ artifact.

Cần GC:

```text
LiveRoots
   ↓
Reachability
   ↓
UnreachableArtifacts
   ↓
Garbage Collection
```

Roots gồm:

```text
lockfiles
installed packages
active builds
debug sessions
components
explicit pins
```

Không xóa artifact đang được referenced.

---

# 34. Artifact leases

Build đang chạy có thể giữ:

```text
ArtifactLease
```

để GC không xóa dependency đang sử dụng.

Lease không phải ownership của artifact content.

Nó chỉ ngăn reclamation.

---

# 35. Content deduplication

Hai package:

```text
A → lib/common
B → lib/common
```

nếu binary giống nhau:

```text
same ArtifactHash
```

chỉ lưu một bản.

---

# 36. Delta transfer

Có thể hỗ trợ:

```text
Artifact A
     ↓
delta
     ↓
Artifact B
```

nhưng delta chỉ là transport optimization.

Sau khi apply:

```text
Hash(result) == expected ArtifactHash
```

Nếu không:

```text
reject
```

---

# 37. Registry publication transaction

Publish không được thực hiện kiểu:

```text
upload file
update index
hope success
```

Phải transactional:

```text
Upload
 ↓
Verify
 ↓
Validate AXIF
 ↓
Validate signatures
 ↓
Validate dependencies
 ↓
Commit artifact
 ↓
Publish index
```

Nếu failure:

```text
artifact remains unpublished
```

---

# 38. Version yanking

Package version có thể bị:

```text
yanked
```

nhưng artifact immutable.

Yank nghĩa:

> Không chọn version này trong resolution mới.

Không nghĩa:

> Xóa artifact khỏi lịch sử.

Lockfile đang sử dụng version đó vẫn có thể resolve nếu policy cho phép.

---

# 39. Security revocation

Signature/key có thể bị revoke.

Registry có:

```text
RevocationRecord
```

nhưng build reproducibility phải phân biệt:

```text
artifact was valid when built
```

với:

```text
artifact is currently trusted
```

Do đó attestation timestamp và trust policy phải độc lập.

---

# 40. Licensing metadata

Artifact descriptor có thể chứa:

```text
LicenseMetadata
Copyright
Notice
SourceAvailability
Redistribution
```

Compiler không nhất thiết enforce legal semantics.

Package tooling có thể audit.

---

# 41. Artifact metadata cho AI

AI tooling có thể query:

```text
artifact.inspect()
```

và nhận:

```text
Package
Version
Targets
ABI
Dependencies
Capabilities
Unsafe
FFI
NativeLibraries
BuildTools
Source
Compiler
License
Signer
Provenance
```

Đây là một điểm rất phù hợp với mục tiêu **AI-friendly ecosystem** của Axiom.

---

# 42. Compiler/registry separation

Compiler không nên chứa logic registry-specific.

Kiến trúc:

```text
Registry Client
      ↓
Artifact Resolver
      ↓
Artifact Store
      ↓
Compiler
```

Compiler chỉ nhận verified artifact.

---

# 43. Artifact Store API

```text
put_artifact()
get_artifact()
has_artifact()
delete_artifact()
pin_artifact()
unpin_artifact()

verify_artifact()
verify_manifest()
verify_axif()

get_descriptor()
get_provenance()
get_attestation()

acquire_lease()
release_lease()

gc()
```

---

# 44. Registry Client API

```text
resolve_package()
query_versions()
fetch_manifest()
fetch_descriptor()
fetch_artifact()
fetch_axif()
fetch_signature()
fetch_attestation()

publish_artifact()
publish_metadata()

sync_snapshot()
verify_registry_snapshot()
```

---

# 45. Registry protocol layers

```text
┌──────────────────────────┐
│ Package Semantics        │
├──────────────────────────┤
│ Artifact Protocol        │
├──────────────────────────┤
│ Trust / Signature        │
├──────────────────────────┤
│ Snapshot / Index         │
├──────────────────────────┤
│ Transport                │
└──────────────────────────┘
```

Mỗi tầng độc lập.

---

# 46. Implementation tree

```text
compiler/
└── artifact/
    ├── descriptor/
    ├── format/
    ├── canonical/
    ├── hash/
    ├── chunk/
    ├── merkle/
    ├── verify/
    ├── provenance/
    └── debug/

tools/
└── registry/
    ├── client/
    ├── protocol/
    ├── index/
    ├── snapshot/
    ├── publish/
    └── mirror/

runtime/
└── artifact/
    ├── store/
    ├── cache/
    ├── lease/
    └── gc/
```

---

# 47. CompilerDB additions

```text
ArtifactDB
ArtifactDescriptorDB
ArtifactStoreDB
ArtifactIndexDB
ArtifactHashDB
ArtifactChunkDB
ArtifactProvenanceDB
RegistryDB
RegistrySnapshotDB
RegistryTrustDB
NativeArtifactDB
DebugArtifactDB
```

---

# 48. Invariants

```text
AART-01
Artifact identity is content-addressed.

AART-02
Published artifacts are immutable.

AART-03
Package identity and artifact identity are distinct.

AART-04
Artifact target compatibility is explicit.

AART-05
Artifact ABI compatibility is explicit.

AART-06
AXIF must be cryptographically or semantically bound to the artifact it describes.

AART-07
Transport encoding must not alter artifact identity.

AART-08
Compression must not alter artifact identity.

AART-09
Chunk verification must reconstruct the exact expected artifact.

AART-10
Registry mirrors must not silently modify artifacts.

AART-11
Origin signatures must remain verifiable through mirrors.

AART-12
Offline registry snapshots must be independently verifiable.

AART-13
Source archives must have canonical representation.

AART-14
Generated source must carry generator/input provenance.

AART-15
Native libraries require explicit target and ABI contracts.

AART-16
Debug artifacts must be independently addressable.

AART-17
Component artifacts must expose component contracts.

AART-18
Plugin binaries must not be loaded solely by filename convention.

AART-19
Artifact GC must respect live references and leases.

AART-20
Delta transfer must be verified against the final artifact hash.

AART-21
Registry publication must be transactional.

AART-22
Yanking must not mutate immutable artifact content.

AART-23
Revocation must be distinguishable from historical build validity.

AART-24
Artifact metadata must be deterministic.

AART-25
Registry transport must not become part of compiler semantic correctness.

AART-26
Compiler must consume verified artifacts rather than arbitrary registry responses.

AART-27
Artifact provenance must survive caching and mirroring.

AART-28
Universal bundles must preserve identity of each target artifact.

AART-29
Artifact security metadata must not be conflated with language safety.

AART-30
All artifact representations must ultimately resolve to a verifiable semantic identity.
```

---

# 49. Definition of Done

BOOTSTRAP-332 hoàn thành khi Axiom có:

- Canonical Artifact Format.
- Artifact Descriptor.
- Content-addressed identity.
- Immutable artifact model.
- Artifact kinds.
- Target-specific artifact selection.
- Universal/fat artifact.
- Chunk/Merkle verification.
- Compression-independent identity.
- Source archive canonicalization.
- Generated-source provenance.
- Native-library artifact contract.
- `.axif` artifact binding.
- Debug artifact model.
- Component/plugin artifact model.
- SDK/tool artifact model.
- Local Artifact Store.
- Artifact leases.
- Artifact GC.
- Deduplication.
- Delta transfer.
- Registry protocol.
- Registry index.
- Registry snapshot.
- Registry mirror.
- Offline registry.
- Transactional publication.
- Yank/revocation semantics.
- Signature integration.
- Provenance integration.
- Attestation integration.
- Package Manager integration.
- Build Sandbox integration.
- ABI integration.
- FFI integration.
- Component integration.
- Cross-target integration.
- AI-readable artifact inspection.
- Deterministic canonical metadata.

### Nguyên tắc khóa

> **Package là identity logic; Artifact là một realization cụ thể của package; Hash là identity của realization; Registry chỉ là phương tiện phân phối.**

Nhờ vậy Axiom không bị phụ thuộc vào một registry cụ thể. Một package có thể được lấy từ internet, mirror nội bộ, cache, filesystem hoặc USB, nhưng compiler vẫn nhìn thấy **cùng một semantic artifact identity** và có thể tự xác minh trước khi sử dụng.