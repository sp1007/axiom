# BOOTSTRAP-339 — AXIOM NATIVE CODE SIGNING, BINARY INTEGRITY & TRUSTED DEPLOYMENT ENGINE

Sau 337–338, Axiom đã có:

- native binary hoàn chỉnh;
- debug/symbol artifacts;
- profiling/PGO;
- package/artifact identity;
- ABI và component contracts;
- build provenance và supply-chain trust.

Bước tiếp theo là biến artifact đó thành **một binary có thể xác minh nguồn gốc, tính toàn vẹn và trạng thái tin cậy khi triển khai**.

Nguyên tắc:

> **Build tạo ra artifact; signing chứng minh artifact; deployment xác minh artifact.**

Signing không được thay đổi semantics của chương trình.

---

## 1. Tách ba khái niệm

Axiom không được gộp:

```text
Integrity
Authenticity
Trust
```

### Integrity

Binary có bị thay đổi không?

```text
Hash(binary) == expected_hash
```

### Authenticity

Artifact được ký bởi identity nào?

```text
Signature
    ↓
SigningIdentity
```

### Trust

Identity/artifact đó có được policy hiện tại tin tưởng không?

```text
TrustPolicy(SigningIdentity, Artifact, Target)
```

Một binary có signature hợp lệ **không tự động có nghĩa là trusted**.

---

# 2. Signing không nằm trong compiler semantics

Pipeline:

```text
Source
 ↓
Compiler
 ↓
Object
 ↓
Link
 ↓
Final Binary
 ↓
Sign
 ↓
Deploy
```

Không:

```text
Source
 ↓
Compiler
 ↓
Sign từng MIR
```

Signing là post-build artifact operation, ngoại trừ những target yêu cầu platform-specific metadata trước bước ký.

---

# 3. Artifact identity

Binary phải có:

```text
ArtifactId
ContentHash
BuildId
TargetFingerprint
ABIFingerprint
SemanticFingerprint
```

Ví dụ:

```text
ArtifactIdentity {
    package
    version
    artifact_kind
    target
    abi
    content_hash
    build_id
}
```

---

# 4. Hashing

Axiom cần abstraction:

```text
HashAlgorithm
HashValue
Hasher
```

Không hard-code một thuật toán duy nhất.

Có thể hỗ trợ:

- SHA-256
- SHA-512
- SHA-3
- BLAKE3

Tùy trust/deployment profile.

---

# 5. Canonical artifact identity

Không được ký một metadata representation không ổn định.

Canonical form:

```text
CanonicalMetadata
      ↓
CanonicalSerialization
      ↓
Hash
      ↓
Signature
```

Các field phải có ordering deterministic.

---

# 6. Signature object

```text
Signature {
    algorithm
    key_id
    signature
    signed_hash
    metadata_version
}
```

Không nhúng private key vào artifact.

---

# 7. Signing identity

```text
SigningIdentity {
    identity_id
    algorithm
    public_key
    issuer
    validity
    capabilities
}
```

Identity có thể là:

```text
Developer
Organization
BuildSystem
ReleaseSystem
PlatformDistributor
```

---

# 8. Key rotation

Không được giả định một key tồn tại mãi.

```text
OldKey
   ↓
KeyRotationCertificate
   ↓
NewKey
```

Artifact cũ vẫn phải xác minh được nếu policy cho phép.

---

# 9. Revocation

Identity có thể bị thu hồi:

```text
Active
Revoked
Expired
Suspended
Compromised
```

Revocation policy target-specific.

---

# 10. Timestamp

Signature có thể chứa:

```text
SignedAt
```

nhưng timestamp không được mặc định là trusted time.

Có thể hỗ trợ:

```text
TrustedTimestamp
```

từ timestamp authority.

---

# 11. Reproducible build và signing

Signing phải **không phá reproducibility của unsigned binary**.

Ví dụ:

```text
build A
→ hash X

build B
→ hash X
```

sau đó:

```text
sign A
→ signed artifact
sign B
→ signed artifact
```

chữ ký có thể khác, nhưng underlying unsigned artifact identity vẫn giống nhau.

---

# 12. Signature envelope

Thiết kế:

```text
UnsignedArtifact
        │
        ▼
ArtifactDigest
        │
        ▼
SignatureEnvelope
        │
        ├── signer
        ├── algorithm
        ├── timestamp
        ├── metadata
        └── signature
```

---

# 13. Detached signature

Hỗ trợ:

```text
program.exe
program.exe.sig
```

Ưu điểm:

- không thay đổi binary;
- thuận tiện reproducible build;
- registry có thể lưu signature riêng.

---

# 14. Embedded signature

Một số platform yêu cầu signature nằm trong binary/container.

Axiom hỗ trợ:

```text
EmbeddedSignature
```

nhưng phải phân biệt:

```text
semantic binary
vs
platform signing envelope
```

---

# 15. Platform signing abstraction

```text
PlatformSigner {
    inspect_requirements()
    prepare()
    sign()
    verify()
}
```

Backend:

```text
PE/Authenticode
Mach-O/code signing
Apple bundle signing
Android APK/AAB signing
WASM signing/integrity metadata
Linux package signing
```

---

# 16. Windows

PE signing backend phải hiểu:

```text
PE/COFF
Authenticode
certificate chain
timestamp
catalog signing
```

Compiler không cần hiểu certificate internals trong Core.

---

# 17. Apple

Mach-O deployment có thể cần:

```text
Code Signature
Entitlements
Provisioning metadata
Bundle identity
```

Axiom chỉ cung cấp semantic artifact và platform signing contract.

Signing implementation thuộc deployment toolchain.

---

# 18. Android

Artifact có thể là:

```text
APK
AAB
Native .so
```

Cần phân biệt:

```text
Axiom binary identity
Android package identity
Android signing identity
```

---

# 19. Linux

Linux native executable không bắt buộc code signing.

Axiom không được tạo signature requirement giả tạo.

Có thể hỗ trợ:

```text
Detached signature
Package signature
Container signature
IMA/EVM integration
```

như deployment options.

---

# 20. WASM

WASM module có thể có:

```text
ModuleHash
Signature
CapabilityManifest
```

Host runtime xác minh trước khi load.

---

# 21. Binary integrity

Loader/deployer có thể kiểm tra:

```text
Hash
Signature
Target
ABI
BuildId
Dependencies
Capabilities
```

trước khi execute.

---

# 22. Dependency integrity

Không chỉ executable.

Dependency graph:

```text
App
├── libA
│   └── libC
└── libB
```

phải có thể xác minh từng artifact.

---

# 23. Dependency lock

`axiom.lock` đã tồn tại từ 329.

Deployment verifier phải kiểm tra:

```text
lock entry
      ↓
artifact identity
      ↓
content hash
      ↓
signature
```

---

# 24. Trust policy

Ví dụ:

```text
TrustPolicy {
    allowed_signers
    allowed_registries
    allowed_targets
    allowed_abis
    required_signatures
    revoked_keys
    minimum_security_level
}
```

---

# 25. Trust levels

Không dùng một boolean:

```text
trusted = true
```

Thay vào đó:

```text
Untrusted
Verified
Signed
TrustedPublisher
PlatformTrusted
LocallyTrusted
```

Trust level là policy result.

---

# 26. Capability verification

Artifact manifest có:

```text
requires:
    filesystem
    network
    gpu
```

Deployment policy có:

```text
allow:
    filesystem
    gpu
deny:
    network
```

Loader phải phát hiện mismatch trước execution nếu target/runtime hỗ trợ capability enforcement.

---

# 27. Security boundary

Signing không biến code thành safe code.

Một artifact:

```text
signed
```

vẫn có thể chứa:

```text
unsafe
FFI
native code
network
filesystem
```

Do đó:

```text
Signature ≠ Safety
```

---

# 28. Provenance

Artifact nên liên kết tới:

```text
SourceFingerprint
DependencyFingerprint
CompilerFingerprint
TargetFingerprint
BuildFingerprint
```

Nhờ đó có thể trả lời:

> Binary này được tạo từ đâu?

---

# 29. Build attestation

Ví dụ:

```text
Attestation {
    source
    dependencies
    compiler
    target
    build_policy
    sandbox
    reproducibility
}
```

Attestation khác signature:

```text
Signature → ai ký
Attestation → artifact được tạo như thế nào
```

---

# 30. Trusted build

Có thể có policy:

```text
RequireReproducibleBuild
RequireSignedCompiler
RequireTrustedBuilder
RequireLockedDependencies
RequireVerifiedArtifacts
```

---

# 31. Compiler trust

Compiler binary cũng là artifact.

Do đó bootstrap chain:

```text
Compiler A
    ↓ builds
Compiler B
    ↓ builds
Application
```

có thể được attested.

Điều này rất quan trọng cho self-hosting.

---

# 32. Bootstrap trust chain

Axiom có thể tạo:

```text
BootstrapCompiler
       ↓
AxiomCompiler
       ↓
AxiomCompiler'
```

và so sánh:

```text
semantic identity
binary identity
build provenance
```

---

# 33. Self-host verification

Sau khi Axiom compiler self-host:

```text
Compiler_v1
    ↓
build compiler_v2

Compiler_v2
    ↓
build compiler_v3
```

có thể thực hiện bootstrap consistency checking.

---

# 34. Binary transparency

Registry/deployment system có thể lưu:

```text
ArtifactHash
Signer
Timestamp
Provenance
Revocation
```

trong append-only transparency log.

Không bắt buộc Core.

---

# 35. Transparency log

```text
Artifact
   ↓
Hash
   ↓
TransparencyEntry
```

Có thể dùng Merkle tree:

```text
leaf
 ├── leaf
 └── leaf
       ↓
      root
```

---

# 36. Offline verification

Verifier phải hoạt động offline khi có:

```text
artifact
signature
public key
policy
metadata
```

Không được mặc định cần Internet.

---

# 37. Air-gapped deployment

Trong môi trường bảo mật:

```text
No Network
```

vẫn phải:

```text
verify artifact
verify dependencies
verify signatures
verify provenance
```

---

# 38. Deployment manifest

Axiom định nghĩa:

```text
DeploymentManifest {
    application_id
    version
    target
    artifacts[]
    dependencies[]
    capabilities[]
    entrypoints[]
    resources[]
    signing_requirements
}
```

---

# 39. Bundle

Deployment bundle có thể chứa:

```text
Application
├── executable
├── dynamic libraries
├── resources
├── manifest
├── signatures
├── provenance
└── debug references
```

Debug information không cần nhúng vào production bundle.

---

# 40. Resource integrity

Resources cũng phải có:

```text
ResourceId
ContentHash
```

Ví dụ:

```text
icon
shader
model
config
localization
```

---

# 41. Runtime-loaded resources

Nếu chương trình load resource động:

```text
load("shader.bin")
```

compiler/deployment system có thể khai báo:

```text
ResourceDependency
```

để tránh deployment bỏ sót.

---

# 42. Dynamic plugins

325 đã định nghĩa plugin/component.

339 bổ sung:

```text
Plugin artifact
→ signature
→ trust policy
→ capability policy
→ ABI validation
```

Không được load plugin chỉ vì filename đúng.

---

# 43. Hot reload

Hot-reload component phải xác minh:

```text
new binary
signature
ABI
component version
capability policy
```

trước khi thay thế generation cũ.

---

# 44. Update

Update pipeline:

```text
Existing
   ↓
Download
   ↓
Verify hash
   ↓
Verify signature
   ↓
Verify target/ABI
   ↓
Verify dependencies
   ↓
Verify policy
   ↓
Install
   ↓
Activate
```

---

# 45. Atomic update

Không được để application rơi vào trạng thái:

```text
half old
half new
```

Deployment manager dùng:

```text
staged install
→ verify
→ atomic activation
```

---

# 46. Rollback

Nếu update thất bại:

```text
Version N
Version N+1
```

có thể quay lại:

```text
Version N
```

nếu artifact cũ vẫn còn hợp lệ.

---

# 47. Anti-downgrade

Policy có thể yêu cầu:

```text
minimum_version
```

để ngăn cài artifact cũ đã có vulnerability.

---

# 48. Revoked artifact

Artifact có thể bị revoke dù signature vẫn cryptographically valid.

Ví dụ:

```text
Signature = valid
Trust policy = revoked
```

→ deployment reject.

---

# 49. Vulnerability metadata

Deployment system có thể nhận:

```text
Artifact
Dependency
VulnerabilityDatabase
```

nhưng vulnerability policy thuộc deployment/security tooling, không phải language semantics.

---

# 50. Debug artifact relationship

Production binary:

```text
program.exe
```

Debug:

```text
program.axdbg
```

Mapping:

```text
BuildId
DebugFingerprint
```

Deployment không cần ship debug artifact cho end user.

---

# 51. Crash verification

Crash dump:

```text
BuildId
```

→ tìm đúng:

```text
program.axdbg
```

→ symbolicate.

Không được dùng nhầm debug information của binary khác.

---

# 52. Profile artifact relationship

Tương tự:

```text
program.exe
program.axdbg
program.axprof
```

đều liên kết qua:

```text
BuildId
```

---

# 53. Artifact graph

339 hoàn thiện graph:

```text
                 Source
                   │
                   ▼
                Build
                   │
             ┌─────┴─────┐
             ▼           ▼
          Binary       AXIF
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
    Debug  Profile Signature
                    │
                    ▼
                 Deploy
```

---

# 54. Verification pipeline

Deployment verifier:

```text
Read Manifest
      ↓
Check Artifact Hash
      ↓
Check Signature
      ↓
Check Signer Trust
      ↓
Check Target
      ↓
Check ABI
      ↓
Check Dependencies
      ↓
Check Capabilities
      ↓
Check Revocation
      ↓
Check Policy
      ↓
Accept / Reject
```

---

# 55. Failure categories

Không trả về một lỗi:

```text
invalid binary
```

Mà phân loại:

```text
HashMismatch
InvalidSignature
UnknownSigner
ExpiredIdentity
RevokedIdentity
TargetMismatch
ABIMismatch
DependencyMismatch
CapabilityViolation
PolicyViolation
CorruptManifest
UnsupportedFormat
```

---

# 56. Machine-readable verification

API:

```text
verify_artifact()
verify_signature()
verify_manifest()
verify_dependencies()
verify_target()
verify_abi()
verify_capabilities()
evaluate_trust()
evaluate_deployment_policy()
```

Result:

```text
VerificationReport
```

---

# 57. Human diagnostics

Ví dụ:

```text
AXDPL-104

Artifact rejected.

Reason:
  target architecture mismatch

Artifact:
  x86_64-linux

Required:
  aarch64-linux
```

AI tooling có thể đọc cùng structured diagnostic.

---

# 58. CLI

```text
axiom sign
axiom verify
axiom trust
axiom provenance

axiom deploy verify
axiom deploy inspect
axiom deploy package
axiom deploy install
axiom deploy update
axiom deploy rollback

axiom artifact hash
axiom artifact identity
axiom artifact attest
```

---

# 59. CompilerDB additions

```text
DeploymentDB
SigningDB
IdentityDB
KeyMetadataDB
TrustDB
VerificationDB
RevocationDB
AttestationDB
ManifestDB
BundleDB
UpdateDB
TransparencyDB
```

---

# 60. Implementation tree

```text
compiler/
└── deployment/
    ├── artifact/
    ├── manifest/
    ├── signing/
    ├── verification/
    ├── identity/
    ├── trust/
    ├── provenance/
    ├── attestation/
    ├── revocation/
    ├── transparency/
    ├── bundle/
    ├── update/
    ├── rollback/
    └── platform/
        ├── windows/
        ├── apple/
        ├── android/
        ├── linux/
        └── wasm/
```

---

# 61. Invariants

```text
ADPL-01
Signing must never alter program semantics.

ADPL-02
Integrity, authenticity and trust are distinct concepts.

ADPL-03
A valid signature does not imply language-level safety.

ADPL-04
Unsigned artifacts remain valid artifacts unless deployment policy requires signing.

ADPL-05
Signature verification must use canonical artifact identity.

ADPL-06
Private signing keys must never be embedded in compiler artifacts.

ADPL-07
Artifact identity must be independent of signature identity.

ADPL-08
Reproducible unsigned builds must remain reproducible after introducing signing.

ADPL-09
Target mismatch must be detected before deployment.

ADPL-10
ABI mismatch must be detected before deployment.

ADPL-11
Dependency identity must be verified independently.

ADPL-12
Capability requirements must be explicit.

ADPL-13
Revoked identities/artifacts must obey deployment policy.

ADPL-14
Offline verification must be supported.

ADPL-15
Air-gapped deployment must not require network access.

ADPL-16
Dynamic components must undergo signature and ABI verification.

ADPL-17
Hot reload must verify the new component before activation.

ADPL-18
Updates must support transactional activation.

ADPL-19
Rollback must restore a previously verified artifact.

ADPL-20
Debug artifacts must be bound to the exact binary identity.

ADPL-21
Profile artifacts must be bound to the exact compatible binary identity.

ADPL-22
Provenance is distinct from cryptographic signature.

ADPL-23
Trust is a policy decision, not a cryptographic primitive.

ADPL-24
Deployment verification must produce structured machine-readable diagnostics.

ADPL-25
Platform signing mechanisms must remain outside Core language semantics.
```

---

# 62. Definition of Done

BOOTSTRAP-339 hoàn thành khi Axiom có:

- canonical artifact identity;
- cryptographic hashing;
- detached signatures;
- embedded signatures;
- signing identity;
- key rotation;
- revocation;
- timestamping;
- artifact verification;
- dependency verification;
- trust policies;
- capability policies;
- build provenance;
- build attestation;
- deployment manifests;
- application bundles;
- resource integrity;
- plugin signing;
- component signing;
- hot-reload verification;
- atomic update;
- rollback;
- anti-downgrade;
- offline verification;
- air-gapped verification;
- transparency-log integration;
- Windows signing backend;
- Apple signing backend;
- Android signing backend;
- Linux deployment signing;
- WASM integrity/signing;
- debug/profile artifact identity;
- self-host compiler trust chain;
- machine-readable verification;
- AI-readable deployment diagnostics.

---

## Kiến trúc sau 339

Lúc này chuỗi artifact của Axiom khá hoàn chỉnh:

```text
                    SOURCE
                      │
                      ▼
                 AXIOM BUILD
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       BINARY       .AXIF       DEBUG
          │                       │
          │                       └── .AXDBG
          │
          ├────────── PROFILE
          │             └── .AXPROF
          │
          ▼
      SIGN / ATTEST
          │
          ▼
      VERIFY / TRUST
          │
          ▼
       DEPLOY
          │
          ▼
        RUN
          │
          ▼
      PROFILE
          │
          └──────────────► PGO
                              │
                              ▼
                           REBUILD
```

Điểm quan trọng là từ đây Axiom không còn chỉ là **một compiler tạo native executable**, mà đã có một **chuỗi tin cậy hoàn chỉnh từ source → build → artifact → verification → deployment → runtime feedback**.