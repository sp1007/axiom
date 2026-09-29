# BOOTSTRAP-331 — AXIOM BUILD SANDBOX, HERMETIC BUILD & SUPPLY-CHAIN TRUST ENGINE

Sau khi đã có **Package Manager-329** và **Standard Library-330**, bước tiếp theo cần giải quyết một vấn đề rất quan trọng:

> **Khi Axiom build một package, compiler phải biết chính xác package được phép làm gì, sử dụng dữ liệu nào, chạy công cụ nào, và binary được tạo ra có thể tin cậy đến mức nào.**

Nếu không thiết kế phần này ngay từ đầu, `comptime`, package build scripts, native dependencies và registry có thể trở thành một lỗ hổng lớn đối với mục tiêu **reproducible + secure + AI-friendly build** của Axiom.

---

# 1. Mục tiêu

BOOTSTRAP-331 xây dựng:

```text
Build Sandbox
Hermetic Build
Dependency Provenance
Artifact Verification
Supply-chain Trust
Reproducibility
Build Attestation
```

Mục tiêu cuối:

```text
Source
  ↓
Dependency Graph
  ↓
Verified Inputs
  ↓
Sandboxed Build
  ↓
Deterministic Compiler
  ↓
Verified Artifacts
  ↓
Attested Binary
```

Compiler phải có khả năng trả lời:

```text
Binary này được build từ source nào?
Dependency nào?
Version nào?
Compiler nào?
Target nào?
Comptime input nào?
Build script nào?
Native library nào?
Có network access không?
Có filesystem access không?
Có unsafe/FFI dependency nào?
Artifact có bị thay đổi không?
```

---

# 2. Phân biệt 4 loại trust

Không được gom tất cả thành một `trusted/untrusted`.

```text
Source Trust
Build Trust
Artifact Trust
Runtime Trust
```

Ví dụ:

```text
package được signed
```

chỉ chứng minh:

> artifact đến từ một identity cụ thể.

Nó **không chứng minh code an toàn**.

---

# 3. Trust model

Đề xuất:

```text
Local
Unverified
Verified
Signed
Trusted
System
```

Nhưng trust level chỉ là metadata.

Ví dụ:

```text
Signed + unsafe code
```

vẫn là unsafe code.

Do đó:

```text
Trust ≠ Safety
Trust ≠ Correctness
Trust ≠ Permission
```

Ba khái niệm phải độc lập.

---

# 4. Build Capability Model

Mỗi build có một capability set:

```text
BuildCapability
```

Ví dụ:

```text
ReadSource
ReadPackage
ReadMetadata
WriteArtifact
ReadFilesystem
WriteFilesystem
ExecuteTool
Network
Environment
Clock
Random
Process
GPU
Device
```

Mặc định:

```text
ReadSource
ReadPackage
ReadMetadata
WriteArtifact
```

Các capability khác phải explicit.

---

# 5. Build sandbox

Build process chạy trong sandbox logic:

```text
BuildSandbox {
    filesystem_policy
    network_policy
    process_policy
    environment_policy
    time_policy
    random_policy
    device_policy
    resource_limits
}
```

Compiler không mặc định cho package:

```text
network = allowed
```

hoặc:

```text
execute arbitrary process
```

---

# 6. Filesystem sandbox

Package build không được tự do truy cập filesystem của host.

Có các namespace:

```text
/source
/dependencies
/build
/output
/cache
```

Ví dụ:

```text
/source
```

read-only.

```text
/build
```

temporary.

```text
/output
```

artifact destination.

Host filesystem:

```text
/home/user
C:\Users\...
```

không tồn tại trong sandbox nếu chưa được cấp capability.

---

# 7. Không cho path escape

Các trường hợp:

```text
../secret
absolute host path
symlink escape
junction escape
mount escape
```

phải bị sandbox chặn.

Path normalization phải xảy ra **trước authorization**.

Không được:

```text
check(path)
→ resolve(path)
```

nếu resolve có thể thay đổi target.

Phải:

```text
canonicalize
→ resolve sandbox identity
→ authorize
→ access
```

---

# 8. Network

Build mặc định:

```text
Network = Denied
```

Nếu package cần network:

```text
capability.network
```

phải được khai báo.

Có thể giới hạn:

```text
domains
ports
protocols
```

Ví dụ:

```text
registry.example.com:443
```

thay vì:

```text
all network
```

---

# 9. Deterministic network

Ngay cả khi network được phép, build reproducibility không được phụ thuộc trực tiếp vào:

```text
latest URL
HTTP response
current API
remote timestamp
random server response
```

Nếu network input ảnh hưởng build:

```text
URL
content hash
retrieval timestamp
certificate/provenance
```

phải trở thành build input.

Tốt hơn:

```text
URL → downloaded artifact → content hash → build input
```

---

# 10. Environment

Build không được mặc định nhìn thấy:

```text
HOME
PATH
USERNAME
TEMP
CPU_COUNT
RANDOM
current directory
```

Toàn bộ environment phải được explicit.

Ví dụ:

```text
@build_env("TARGET")
@build_env("PROFILE")
```

Compiler-controlled variables được phân biệt với host environment.

---

# 11. Time

`current time` phá reproducibility.

Do đó build sandbox có:

```text
ClockPolicy
```

Các mode:

```text
Frozen
Deterministic
HostTime
Denied
```

Default:

```text
Frozen
```

Ví dụ:

```text
SOURCE_DATE_EPOCH
```

có thể trở thành explicit build input.

---

# 12. Randomness

Tương tự:

```text
Random
```

không được implicit.

Hai loại:

```text
DeterministicRandom(seed)
SecureRandom()
```

`SecureRandom` không phù hợp cho reproducible build.

Compiler phải biết sự khác biệt.

---

# 13. Process execution

Package build không được tùy ý:

```text
spawn("cmd.exe")
spawn("bash")
spawn("python")
```

Nếu cần:

```text
ExecuteTool
```

phải explicit.

Tool identity phải được fingerprint:

```text
ToolId
Version
ExecutableHash
Arguments
Environment
InputFiles
OutputFiles
```

---

# 14. Build script không phải magic

Nếu Axiom có build script:

```text
build.ax
```

nó phải được coi như một program có capability contract.

Ví dụ:

```text
BuildManifest {
    capabilities = [
        ReadFilesystem("schemas/"),
        ExecuteTool("protoc"),
    ]
}
```

Compiler biết trước build script có quyền gì.

---

# 15. Build manifest

Đề xuất:

```text
axiom.package
```

có:

```text
[build]
capabilities = [
    "read-source",
    "execute-tool:protoc"
]
```

Không cho build script tự cấp thêm quyền.

---

# 16. Capability escalation

Build script không thể:

```text
ReadFilesystem
```

rồi tự chuyển thành:

```text
Network
ExecuteTool
```

Capability phải:

```text
explicitly granted
```

và immutable trong quá trình build.

---

# 17. Hermetic build

Hermetic build nghĩa là:

> Kết quả build chỉ phụ thuộc vào những input được khai báo và fingerprint.

Formal model:

```text
Artifact =
F(
    Source,
    Dependencies,
    Compiler,
    Target,
    Features,
    ComptimeInputs,
    BuildInputs,
    ToolInputs,
    Configuration
)
```

Không phụ thuộc implicit:

```text
host state
current time
randomness
undeclared environment
undeclared files
undeclared network
```

---

# 18. Build fingerprint

Tạo:

```text
BuildFingerprint
```

bao gồm:

```text
CompilerSemanticVersion
CompilerBinaryHash
LanguageEdition
TargetFingerprint
SourceFingerprint
DependencyGraphFingerprint
FeatureFingerprint
ComptimeFingerprint
BuildScriptFingerprint
ToolchainFingerprint
SDKFingerprint
ConfigurationFingerprint
```

---

# 19. Content-addressed artifacts

Artifact nên được định danh bằng hash:

```text
ArtifactId = Hash(CanonicalArtifact)
```

Ví dụ:

```text
sha256:<digest>
```

Hash algorithm không nên hard-code forever.

Model:

```text
HashAlgorithm
HashValue
```

để sau này nâng cấp.

---

# 20. Dependency provenance

Mỗi dependency phải có:

```text
DependencyProvenance {
    package_id
    version
    source
    revision
    checksum
    registry
    signer
    trust
}
```

Không cho:

```text
"some package"
```

được resolve thành một artifact khác mà không thay đổi fingerprint.

---

# 21. Registry artifact verification

Khi tải package:

```text
Download
   ↓
Checksum
   ↓
Signature
   ↓
Metadata
   ↓
AXIF
   ↓
Target compatibility
   ↓
Artifact acceptance
```

Không:

```text
Download → execute
```

---

# 22. Signature

Signature bao phủ canonical artifact metadata:

```text
PackageIdentity
Version
ArtifactHash
AXIFHash
Target
ABI
DependencyLock
```

Không chỉ sign:

```text
zip file
```

vì metadata bên ngoài archive có thể bị thay đổi.

---

# 23. Key identity

Signer phải có identity:

```text
SignerId
KeyId
Algorithm
PublicKey
Signature
```

Rotation:

```text
old key → new key
```

phải có explicit trust transition.

Không tự động tin mọi key mới chỉ vì cùng package name.

---

# 24. Transparency

Registry có thể cung cấp:

```text
ArtifactLog
```

với append-only records.

Ví dụ:

```text
Package
Version
ArtifactHash
Signer
Timestamp
PreviousLogHash
```

Tạo hash chain:

```text
Hn = Hash(Hn-1 || Entry)
```

Mục tiêu là phát hiện:

```text
registry silently replaced artifact
```

---

# 25. Reproducible build

Có hai mức:

### Level 1 — Semantic reproducibility

Hai build tạo:

```text
same public semantic result
```

### Level 2 — Binary reproducibility

Hai build tạo:

```text
byte-identical artifact
```

Axiom nên hỗ trợ cả hai.

---

# 26. Binary nondeterminism

Compiler phải loại bỏ các nguồn nondeterminism như:

```text
hash-map iteration order
parallel task order
symbol numbering
temporary IDs
debug metadata ordering
section ordering
timestamp
random UUID
```

Canonical ordering phải được định nghĩa.

---

# 27. Parallel compiler

Compiler vẫn được phép parallel.

Ví dụ:

```text
Compile A
Compile B
Compile C
```

song song.

Nhưng kết quả:

```text
A+B+C
```

phải deterministic.

Do đó:

> Parallel execution order is not semantic order.

---

# 28. Reproducible debug information

Debug metadata cũng cần deterministic nếu yêu cầu reproducible binary.

Không được chứa:

```text
absolute host path
current timestamp
random IDs
machine username
```

trừ khi explicit.

Path mapping:

```text
/source/project
```

thay cho:

```text
C:\Users\Hung\Desktop\project
```

---

# 29. Build attestation

Sau build tạo:

```text
BuildAttestation
```

chứa:

```text
artifact_hash
source_hash
dependency_hash
compiler_hash
target
configuration
capabilities
tools
inputs
timestamp
signer
```

Attestation không thay đổi binary semantics.

---

# 30. Trusted build

Có thể có:

```text
BuildTrustLevel
```

ví dụ:

```text
Unknown
Local
Reproducible
Verified
Attested
Signed
```

Nhưng không dùng score/ranking.

Một artifact có thể:

```text
Signed = yes
Reproducible = no
Unsafe = yes
NetworkBuild = yes
```

Tooling phải hiển thị từng thuộc tính riêng.

---

# 31. Unsafe dependency report

Compiler/package manager phải có khả năng tạo:

```text
axiom audit
```

Ví dụ:

```text
Package: image.codec
Version: 2.1.0

Unsafe:
    12 functions

FFI:
    libjpeg

Build capabilities:
    ReadFilesystem
    ExecuteTool

Network:
    denied
```

Không biến thành một "security score".

---

# 32. Dependency graph security

Package graph:

```text
A
├── B
│   └── C
└── D
    └── C
```

Compiler có thể tính:

```text
UnsafeReachability
FfiReachability
NetworkCapabilityReachability
BuildToolReachability
NativeLibraryReachability
```

Điều này rất hữu ích cho AI agent.

AI có thể hỏi:

```text
"Dependency nào kéo FFI vào project?"
```

và compiler trả lời chính xác.

---

# 33. Capability closure

Nếu:

```text
A → B → C
```

và C yêu cầu:

```text
Network
```

thì build của A phải biết rằng dependency closure yêu cầu:

```text
Network
```

Không được ẩn capability ở package sâu.

---

# 34. Build policy

Project có thể đặt:

```text
BuildPolicy
```

Ví dụ:

```text
allow_network = false
allow_native_code = false
allow_ffi = false
allow_execute_tool = false
require_signed_dependencies = true
require_reproducible_dependencies = true
```

Compiler enforce trước khi build.

---

# 35. Enterprise / CI policy

CI có thể yêu cầu:

```text
all dependencies signed
all artifacts checksum verified
no undeclared network
no host filesystem access
reproducible build
fixed compiler version
fixed target SDK
```

Nhưng đây là policy layer, không phải language semantics.

---

# 36. Offline build

Một project đã resolve đầy đủ có thể:

```text
axiom build --offline
```

Không cần registry.

Nếu thiếu artifact:

```text
ERROR: missing declared build input
```

Không fallback sang network.

---

# 37. Air-gapped environment

Axiom phải hỗ trợ:

```text
offline registry mirror
local artifact store
preloaded SDK
local package cache
```

cho:

```text
embedded
military/industrial
enterprise
CI
restricted environments
```

mà không cần thay đổi language semantics.

---

# 38. Build cache security

Cache key:

```text
CacheKey =
Hash(
    SourceFingerprint,
    DependencyFingerprint,
    CompilerFingerprint,
    TargetFingerprint,
    FeatureFingerprint,
    ComptimeFingerprint,
    BuildInputFingerprint
)
```

Cache hit chỉ hợp lệ khi toàn bộ fingerprint khớp.

---

# 39. Remote build cache

Remote cache không được tin mù quáng.

Pipeline:

```text
Request artifact
        ↓
Receive artifact
        ↓
Verify ArtifactHash
        ↓
Verify BuildFingerprint
        ↓
Verify Attestation
        ↓
Accept
```

Remote cache không có quyền sửa semantic metadata.

---

# 40. Malicious artifact

Nếu hash sai:

```text
ArtifactHashMismatch
```

Nếu signature sai:

```text
SignatureInvalid
```

Nếu `.axif` không khớp binary:

```text
InterfaceArtifactMismatch
```

Nếu target sai:

```text
TargetMismatch
```

Nếu ABI sai:

```text
AbiMismatch
```

Tất cả phải là structured diagnostic.

---

# 41. `.axif` và attestation

`.axif` chứa:

```text
semantic interface
ABI
optimization summary
FFI
platform
```

Attestation chứa:

```text
how this artifact was produced
```

Không gộp hai khái niệm.

```text
.axif        = what the artifact means
attestation  = how the artifact was produced
```

---

# 42. Package lock

`axiom.lock` phải fingerprint:

```text
exact package
exact revision
exact artifact
exact checksum
exact dependency resolution
```

Nếu registry thay artifact cùng version:

```text
lockfile mismatch
```

không silently accept.

---

# 43. Compiler independence

Build sandbox phải không phụ thuộc vào:

```text
Docker
Bazel
Nix
Cargo
npm
Python
```

Các hệ thống này có thể được dùng làm integration layer.

Nhưng Axiom phải có semantic model riêng.

---

# 44. Build daemon

Có thể có:

```text
axiom-buildd
```

nhưng daemon không được trở thành semantic requirement.

Nó chỉ tối ưu:

```text
incremental build
cache
parallelism
distributed build
sandbox
```

Freestanding compiler vẫn phải có khả năng build trực tiếp.

---

# 45. Distributed compilation

Build graph có thể:

```text
Node A → compile package A
Node B → compile package B
Node C → link
```

Nhưng worker phải nhận:

```text
source/input hashes
compiler identity
target
capabilities
```

Worker không được tự ý đọc host state.

---

# 46. Build worker trust

Worker trả:

```text
Artifact
ArtifactHash
BuildFingerprint
Attestation
```

Coordinator verify trước khi accept.

Worker không cần được trust tuyệt đối.

Đây là nền tảng để sau này có distributed compilation.

---

# 47. Compiler database additions

Thêm:

```text
BuildSecurityDB
BuildSandboxDB
BuildInputDB
BuildProvenanceDB
ArtifactStoreDB
ArtifactTrustDB
SignatureDB
AttestationDB
ReproducibilityDB
BuildPolicyDB
ToolchainInputDB
```

---

# 48. Compiler APIs

```text
create_build_sandbox()
grant_build_capability()
revoke_build_capability()
check_build_policy()

compute_build_fingerprint()
compute_artifact_hash()

verify_artifact()
verify_signature()
verify_axif_artifact()

generate_attestation()
verify_attestation()

check_reproducibility()
compare_builds()

audit_dependency_graph()
audit_capabilities()
audit_unsafe_dependencies()

inspect_build_provenance()
inspect_artifact_provenance()

verify_remote_cache()
```

---

# 49. CLI

```text
axiom build
axiom build --offline
axiom build --sandbox=strict
axiom build --reproducible

axiom audit
axiom audit dependencies
axiom audit capabilities
axiom audit unsafe
axiom audit ffi

axiom artifact verify
axiom artifact inspect

axiom provenance
axiom provenance show

axiom reproducible
axiom reproducible compare

axiom trust
axiom trust verify
```

---

# 50. Compiler pipeline

Build security nằm trước compilation:

```text
Manifest
   ↓
Dependency Resolution
   ↓
Lock Verification
   ↓
Trust Verification
   ↓
Build Policy
   ↓
Sandbox Creation
   ↓
Input Materialization
   ↓
Comptime / Build Script
   ↓
Semantic Compilation
   ↓
Codegen
   ↓
Artifact
   ↓
Hash
   ↓
AXIF
   ↓
Attestation
   ↓
Artifact Store
```

Điểm quan trọng:

> **Compiler không được coi một file vừa xuất hiện trong build directory là trusted input chỉ vì build script tạo ra nó.**

Nó phải đi qua input provenance.

---

# 51. Invariants

```text
ABUILD-01
Builds must execute under an explicit capability policy.

ABUILD-02
Network access is denied by default.

ABUILD-03
Host filesystem access is denied by default.

ABUILD-04
Environment access is denied by default.

ABUILD-05
Time and randomness must be explicit build inputs.

ABUILD-06
Undeclared build inputs must not influence verified reproducible builds.

ABUILD-07
Build scripts cannot escalate capabilities.

ABUILD-08
Tool execution must be explicitly authorized.

ABUILD-09
Tool identity must be fingerprinted.

ABUILD-10
Dependency artifacts must be checksum verified.

ABUILD-11
Signature verification must cover canonical artifact identity.

ABUILD-12
Package trust must remain distinct from code safety.

ABUILD-13
Artifact provenance must remain distinct from semantic interface metadata.

ABUILD-14
AXIF must be verified against the artifact it describes.

ABUILD-15
Lockfiles must detect artifact replacement.

ABUILD-16
Parallel compilation must remain deterministic.

ABUILD-17
Cache hits require complete fingerprint compatibility.

ABUILD-18
Remote build workers must not be implicitly trusted.

ABUILD-19
Remote artifacts must be independently verified.

ABUILD-20
Build policy must be enforceable before execution.

ABUILD-21
Offline builds must never silently access the network.

ABUILD-22
Sandbox path traversal must not escape the declared filesystem namespace.

ABUILD-23
Capability closure through transitive dependencies must be observable.

ABUILD-24
Unsafe, FFI, native-code and network capabilities must be separately auditable.

ABUILD-25
Reproducibility must support semantic and binary verification modes.

ABUILD-26
Build attestation must identify compiler, target, source and dependency inputs.

ABUILD-27
Build provenance must survive artifact caching and distribution.

ABUILD-28
Compiler semantic correctness must not depend on a particular sandbox implementation.

ABUILD-29
Axiom must support secure builds without requiring Docker/Bazel/Nix/etc.

ABUILD-30
A sandbox restriction must never silently change program semantics; failure must be explicit.
```

---

# 52. Definition of Done

BOOTSTRAP-331 hoàn thành khi Axiom có:

- Build capability model.
- Hermetic build model.
- Filesystem sandbox.
- Network sandbox.
- Environment sandbox.
- Time/random policy.
- Tool execution policy.
- Build-script capability contract.
- Capability closure.
- Build fingerprint.
- Content-addressed artifact.
- Artifact checksum verification.
- Signature verification.
- Key identity/rotation.
- Dependency provenance.
- Build attestation.
- Semantic + binary reproducibility.
- Deterministic parallel compilation.
- Secure build cache.
- Remote build cache verification.
- Distributed build worker verification.
- Offline build.
- Air-gapped build.
- Build policy.
- Supply-chain audit.
- Unsafe/FFI/native dependency reachability.
- `.axif` ↔ artifact verification.
- `axiom.lock` integration.
- Package Manager integration.
- Comptime integration.
- Security-314 integration.
- ABI-324 integration.
- Component-325 integration.
- FFI-326 integration.
- Platform-327 integration.
- Target-328 integration.
- Standard Library-330 integration.
- Structured diagnostics.
- Machine-readable provenance.
- AI-readable security/build inspection.

### Nguyên tắc được khóa

> **Không có build input vô danh.**

và:

> **Không có quyền build ngầm.**

Một package Axiom có thể rất mạnh, có thể chạy comptime, gọi compiler tool, sinh code, dùng native library hoặc network — nhưng **mọi khả năng đó phải xuất hiện trong semantic/build provenance của package và có thể kiểm tra trước khi thực thi**.

Đây là nền tảng để Axiom sau này có thể xây dựng một hệ sinh thái package lớn mà vẫn giữ được mục tiêu **native, reproducible, self-hosted và có khả năng kiểm chứng bằng máy/AI**.