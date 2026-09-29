# BOOTSTRAP-344 — AXIOM RELEASE ENGINEERING, CONTINUOUS QUALIFICATION & SELF-HOSTING TRUST ENGINE

Sau 343, Axiom đã có:

- specification có thể kiểm chứng;
- reference semantics;
- conformance suite;
- fuzzing;
- sanitizer;
- performance regression;
- ABI/FFI validation;
- bootstrap/self-hosting infrastructure.

Nhưng vẫn còn một lớp cuối cùng trước khi có thể coi compiler là **một sản phẩm compiler đáng tin cậy**:

> **Làm thế nào biến toàn bộ hệ thống kiểm chứng trên thành một quy trình release tự động, có thể chứng minh mỗi bản compiler phát hành đã vượt qua đầy đủ các điều kiện cần thiết?**

Đó là nhiệm vụ của 344.

---

# 1. Mục tiêu

344 xây dựng pipeline:

```text
Source Change
    ↓
Build
    ↓
Unit Tests
    ↓
Conformance
    ↓
Differential Validation
    ↓
Fuzz Regression
    ↓
Sanitizer
    ↓
ABI/FFI
    ↓
Cross Target
    ↓
Performance
    ↓
Binary Size
    ↓
Reproducibility
    ↓
Bootstrap
    ↓
Self-host
    ↓
Release Candidate
    ↓
Qualification
    ↓
Signed Release
```

Mục tiêu là **không có bước quan trọng nào chỉ phụ thuộc vào con người nhớ chạy**.

---

# 2. Release là một artifact có chứng cứ

Không coi:

```text
axiom-1.0.0.exe
```

là toàn bộ release.

Một release đầy đủ gồm:

```text
ReleaseArtifact {
    compiler
    standard_library
    runtime_components
    toolchain
    packages
    axif
    debug_symbols
    documentation
    conformance_certificate
    provenance
    signatures
}
```

---

# 3. Release Manifest

Mỗi release có:

```text
ReleaseManifest {
    release_id
    language_version
    compiler_version
    edition
    target_matrix
    source_fingerprint
    compiler_fingerprint
    conformance_fingerprint
    toolchain_fingerprint
    dependency_fingerprint
    artifact_fingerprints
    qualification_status
    provenance
    signatures
}
```

---

# 4. Release candidate

Không phát hành trực tiếp từ branch development.

Pipeline:

```text
development
    ↓
integration
    ↓
release branch
    ↓
release candidate
    ↓
qualification
    ↓
stable release
```

---

# 5. Release channels

Axiom hỗ trợ:

```text
nightly
dev
beta
rc
stable
lts
```

Mỗi channel có policy khác nhau.

---

# 6. Nightly

Nightly ưu tiên:

- fuzzing;
- performance;
- compiler stress;
- experimental features;
- target coverage.

Không nhất thiết phải đạt toàn bộ stable qualification.

---

# 7. Beta

Beta yêu cầu:

```text
Core conformance
Major target conformance
Regression clean
ABI validation
Reproducible build
```

---

# 8. Release Candidate

RC phải pass toàn bộ:

```text
Language Conformance
Compiler Validation
Target Qualification
ABI/FFI
Security
Fuzz Regression
Performance
Binary Size
Reproducibility
Bootstrap
```

trừ những mục được release policy ghi rõ là optional.

---

# 9. Stable release

Stable yêu cầu:

```text
No blocking qualification failures
```

và tất cả mandatory gates đều pass.

---

# 10. LTS

LTS không phải compiler khác.

Nó là release có:

```text
extended support policy
extended security fixes
ABI compatibility policy
longer regression corpus
```

---

# 11. Qualification profile

Mỗi release dùng:

```text
QualificationProfile {
    language
    targets
    editions
    optimization_levels
    runtime_profiles
    ffi_profiles
    abi_profiles
    sanitizer_profiles
    performance_policies
    security_policies
}
```

---

# 12. Qualification matrix

Ví dụ:

```text
                 Debug   Release   LTO   PGO
x86_64 Linux       ✓        ✓        ✓     ✓
x86_64 Windows     ✓        ✓        ✓
AArch64 Linux      ✓        ✓        ✓
AArch64 Android    ✓        ✓
WASM               ✓        ✓
```

Không phải mọi combination đều bắt buộc.

Matrix được policy định nghĩa rõ.

---

# 13. Gate model

Mỗi stage có:

```text
Gate {
    id
    input
    checks
    required
    threshold
    evidence
    status
}
```

Status:

```text
PASS
FAIL
WARN
SKIPPED
NOT_APPLICABLE
BLOCKED
```

---

# 14. Không được dùng “green build” giả

Một pipeline chỉ được báo:

```text
QUALIFIED
```

khi **mọi mandatory gate** đã pass.

Nếu:

```text
Conformance = PASS
Performance = WARN
ABI = SKIPPED
```

thì:

```text
QUALIFIED = false
```

---

# 15. Evidence graph

Mỗi gate tạo evidence:

```text
Gate
 ↓
TestRun
 ↓
Artifact
 ↓
Fingerprint
 ↓
Environment
```

Tạo thành:

```text
QualificationEvidenceGraph
```

---

# 16. Evidence không thể bị sửa âm thầm

Evidence artifact phải:

- immutable;
- content-addressed;
- fingerprinted;
- có provenance.

Nếu kết quả bị thay đổi:

```text
old fingerprint != new fingerprint
```

---

# 17. Build provenance

Tận dụng 331:

```text
Source
Dependencies
Compiler
SDK
Toolchain
Configuration
Environment
```

được ghi đầy đủ.

---

# 18. Test provenance

Mỗi test run ghi:

```text
TestRun {
    suite
    suite_fingerprint
    compiler
    target
    environment
    seed
    configuration
    result
}
```

---

# 19. Fuzz provenance

341 đã có seed/corpus fingerprint.

344 đưa vào release evidence:

```text
FuzzCorpusFingerprint
FuzzDuration
Seeds
Mutations
Coverage
Failures
```

---

# 20. Performance provenance

342 cung cấp:

```text
BenchmarkSuiteFingerprint
HardwareFingerprint
BaselineFingerprint
ResultFingerprint
```

Release phải giữ chúng.

---

# 21. Reproducible release

Một release phải có thể build lại:

```text
Source + locked dependencies + compiler + target + configuration
```

để tạo cùng semantic artifact.

Nếu yêu cầu bit-for-bit:

```text
artifact hash == artifact hash
```

---

# 22. Bootstrap reproducibility

Compiler đặc biệt nhạy cảm.

Pipeline:

```text
Bootstrap Compiler
    ↓
Build Compiler A
    ↓
Build Compiler B using A
    ↓
Compare
```

---

# 23. Stage convergence

Có thể chạy:

```text
Stage0 → Stage1 → Stage2 → Stage3
```

Nếu:

```text
Stage2 == Stage3
```

về canonical compiler artifact/semantic fingerprint theo policy, bootstrap đã hội tụ.

---

# 24. Diverse bootstrap

Để giảm nguy cơ “trusting trust”:

```text
Bootstrap A
Bootstrap B
```

có thể được xây bởi các compiler khác nhau.

Sau đó:

```text
A → Compiler
B → Compiler
```

và so sánh.

---

# 25. Compiler self-build

Compiler phải có test:

```text
axiom build compiler/
```

bằng chính Axiom compiler.

Đây là một qualification gate.

---

# 26. Compiler self-test

Compiler sau khi tự build phải chạy:

```text
conformance
fuzz regression
sanitizer
performance
```

Không được coi:

```text
self-build succeeded
```

là đủ.

---

# 27. Compiler-of-compiler test

Test:

```text
C0 compiles C1
C1 compiles C2
C2 compiles C3
```

và kiểm tra:

```text
semantic equivalence
binary stability
bootstrap convergence
```

---

# 28. Release bisect

Nếu RC fail:

```text
RC
 ↓
qualification failure
 ↓
regression bisect
 ↓
suspected commit
 ↓
minimal reproducer
```

344 phải tự động tạo artifact để developer sửa.

---

# 29. Blocking vs non-blocking

Mỗi failure có severity:

```text
BLOCKER
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

Ví dụ:

```text
Core semantic miscompile = BLOCKER
Binary size +0.5% = policy-dependent
Documentation typo = LOW
```

---

# 30. Không được che failure

Developer có thể override một gate chỉ khi:

```text
explicit waiver
```

Waiver phải có:

```text
reason
owner
expiry
risk
issue
approver
```

---

# 31. Waiver hết hạn

Không cho:

```text
temporary waiver
```

trở thành vĩnh viễn.

Mỗi waiver có:

```text
expiration
```

và sẽ trở thành release blocker khi hết hạn.

---

# 32. Security gate

344 tích hợp 314/331:

```text
dependency audit
signature verification
provenance
unsafe surface
FFI surface
native code
supply chain
```

---

# 33. Unsafe surface report

Release có thể xuất:

```text
UnsafeSurfaceReport {
    unsafe_functions
    unsafe_blocks
    raw_pointer_operations
    FFI_boundaries
    privileged_capabilities
}
```

Không phải để cấm unsafe.

Mục đích là **biết chính xác trusted computing base**.

---

# 34. Compiler trusted computing base

Axiom nên theo dõi:

```text
TCB =
    parser
    resolver
    type system
    verifier
    optimizer
    backend
    object writer
    linker
    runtime components
```

Không phải toàn bộ ecosystem đều có cùng mức trust.

---

# 35. Verified compiler boundary

Điểm quan trọng:

```text
Unverified input
       ↓
Compiler
       ↓
Verified MIR
       ↓
Verified transformations
       ↓
Machine code
```

Release qualification phải chứng minh pipeline này không bị bypass.

---

# 36. Pass qualification

Mỗi optimization pass có contract:

```text
PassContract {
    preconditions
    transformations
    preserved_invariants
    invalidated_analyses
}
```

344 yêu cầu release pipeline xác nhận:

```text
all mandatory pass contracts validated
```

---

# 37. Compiler configuration qualification

Không chỉ test default config.

Phải có profiles:

```text
Debug
Release
Size
Speed
LTO
PGO
Freestanding
Hosted
NoRuntime
Sanitized
```

---

# 38. Target qualification

Target profile bao gồm:

```text
OS
ABI
Architecture
PointerWidth
Endianness
AtomicCapabilities
SIMD
ObjectFormat
RuntimeProfile
```

---

# 39. Runtime qualification

Từng runtime component phải được kiểm thử độc lập:

```text
allocator
panic
thread
async
TLS
reflection
IO
GPU
```

Runtime không được vô tình kéo thêm dependency.

---

# 40. Runtime-free qualification

Một chương trình:

```text
freestanding / no-runtime
```

phải chứng minh binary không phụ thuộc runtime ngoài policy.

---

# 41. Binary dependency qualification

Sau linking:

```text
axiom inspect binary
```

phải kiểm tra:

```text
unexpected imports
unexpected libraries
unexpected runtime
unexpected symbols
```

---

# 42. Binary size release gate

Mỗi release có baseline:

```text
baseline artifact
```

và policy:

```text
max growth
max mapped growth
max startup regression
```

---

# 43. Performance release gate

Tương tự:

```text
baseline benchmark
```

với threshold riêng cho:

```text
compiler
runtime
application
startup
memory
```

---

# 44. Không dùng benchmark tổng hợp

Không tạo:

```text
Axiom Score = 93
```

Release report phải giữ metric độc lập.

---

# 45. Release report

Ví dụ:

```text
AXIOM 1.0.0 RC1

Language Conformance: PASS
Target Qualification: PASS
ABI: PASS
FFI: PASS
Fuzz Regression: PASS
Sanitizer: PASS
Reproducibility: PASS
Bootstrap: PASS

Compiler Time:
    +1.2%

Peak Memory:
    -4.8%

Binary Size:
    +0.3%

Runtime Benchmarks:
    mixed / see details
```

Không che trade-off bằng một score.

---

# 46. Release dashboard

Có thể cung cấp:

```text
Qualification
Performance
Binary Size
Fuzz
Conformance
Security
Bootstrap
```

với drill-down đến evidence.

---

# 47. Release manifest verification

Người dùng có thể:

```text
axiom release verify axiom-1.0.0
```

Compiler kiểm tra:

```text
signature
artifact hash
manifest
provenance
certificate
```

---

# 48. Release certificate

Ví dụ:

```text
AxiomReleaseCertificate {
    release
    specification
    compiler
    target_matrix
    conformance
    fuzz
    sanitizer
    performance
    reproducibility
    bootstrap
    signatures
}
```

---

# 49. Machine-readable release status

AI-agent có thể gọi:

```text
axiom release inspect --json
```

và nhận:

```text
{
  "qualified": true,
  "conformance": "pass",
  "bootstrap": "pass",
  "performance": "pass"
}
```

---

# 50. Release automation

Pipeline scheduler sử dụng 334:

```text
Build
 ├── Conformance
 ├── Fuzz
 ├── Sanitizer
 ├── ABI
 ├── Performance
 ├── Size
 ├── Reproducibility
 └── Bootstrap
```

Các nhánh độc lập chạy song song.

---

# 51. Resource-aware release

Fuzzing có thể dùng:

```text
CPU
RAM
GPU
disk
```

Benchmark cần hardware reservation.

Conformance có thể chạy parallel.

Tất cả đi qua **BuildScheduler**, không tạo scheduler riêng.

---

# 52. Failure cache

Nếu một gate đã pass với cùng fingerprint:

```text
same inputs
same compiler
same suite
same environment
```

có thể reuse evidence nếu policy cho phép.

---

# 53. Qualification cache

Nhưng security-sensitive gates có thể yêu cầu rerun.

Ví dụ:

```text
signature verification
reproducibility
bootstrap
```

policy quyết định cache được hay không.

---

# 54. Release rollback

Nếu stable release phát hiện blocker:

```text
Release
 ↓
Revoked
```

nhưng không xóa artifact.

Artifact vẫn tồn tại với:

```text
RevocationStatus
```

---

# 55. Security advisory linkage

Release có thể liên kết:

```text
SecurityIssue
AffectedVersions
FixedVersion
Mitigation
```

---

# 56. ABI compatibility gate

Nếu release thay đổi ABI:

```text
Old Stable ABI
       ↓
New Stable ABI
       ↓
ABI Diff
```

must pass explicit policy.

---

# 57. Language compatibility gate

Tương tự:

```text
Source compatibility
Semantic compatibility
ABI compatibility
Binary compatibility
```

được đánh giá riêng.

---

# 58. Breaking-change gate

Nếu thay đổi Core semantics:

```text
LanguageEdition++
```

hoặc cơ chế versioning tương ứng phải được kích hoạt.

Compiler không được âm thầm thay đổi semantics của code cũ.

---

# 59. Release notes generated from semantic diff

Từ:

```text
SpecDiff
APIDiff
ABIDiff
BehaviorDiff
```

có thể sinh:

```text
Breaking Changes
New Features
Behavior Changes
Deprecations
Target Changes
Performance Changes
```

---

# 60. Deprecation lifecycle

Axiom cần:

```text
Active
Deprecated
SoftRemoved
Removed
```

Compiler warning phải machine-readable.

---

# 61. Release stability window

Trước stable:

```text
RC1
RC2
RC3
```

chỉ tạo RC mới khi cần.

Không thay đổi semantics lớn giữa RC nếu không có lý do release-blocking.

---

# 62. Canary testing

Có thể phát hành compiler tới một tập benchmark/corpus nhỏ trước:

```text
Canary
```

sau đó mở rộng:

```text
Expanded
Full
Release
```

---

# 63. Ecosystem qualification

Sau khi package manager ổn định, Axiom có thể chạy:

```text
TopPackages
RealWorldProjects
```

để kiểm tra:

- source compatibility;
- compile performance;
- binary compatibility;
- standard library compatibility.

---

# 64. Real-world corpus

Corpus nên gồm:

```text
compiler itself
standard library
runtime
tools
sample applications
large applications
FFI projects
GPU projects
```

Không chỉ toy programs.

---

# 65. Ecosystem break detector

Khi compiler mới:

```text
Project A PASS
Project B FAIL
Project C PASS
```

system phải phân loại:

```text
CompilerRegression
ProjectBug
SpecificationChange
IntentionalBreakingChange
DependencyIssue
EnvironmentIssue
```

---

# 66. Compiler release confidence

Không tạo một score.

Thay vào đó:

```text
QualificationState {
    language
    targets
    abi
    security
    fuzz
    performance
    reproducibility
    bootstrap
}
```

mỗi field có trạng thái riêng.

---

# 67. Compiler Release DB

Thêm:

```text
ReleaseDB
ReleaseManifestDB
ReleasePipelineDB
QualificationDB
GateDB
EvidenceDB
WaiverDB
ReleaseArtifactDB
ReleaseSignatureDB
ReleaseProvenanceDB
ReleaseHistoryDB
CompatibilityDB
BootstrapQualificationDB
```

---

# 68. Implementation tree

```text
tools/
└── release/
    ├── manifest/
    ├── pipeline/
    ├── qualification/
    ├── gates/
    ├── evidence/
    ├── certificates/
    ├── bootstrap/
    ├── compatibility/
    ├── performance/
    ├── conformance/
    ├── fuzz/
    ├── sanitizer/
    ├── security/
    ├── reproducibility/
    ├── signing/
    ├── rollback/
    ├── canary/
    ├── ecosystem/
    └── reporting/

compiler/
└── release/
    ├── qualification/
    ├── provenance/
    ├── compatibility/
    └── diagnostics/
```

---

# 69. CLI

```text
axiom release build
axiom release candidate
axiom release qualify
axiom release verify
axiom release inspect
axiom release diff
axiom release sign
axiom release publish
axiom release revoke
axiom release rollback
```

Qualification:

```text
axiom qualify compiler
axiom qualify target
axiom qualify bootstrap
axiom qualify release
axiom qualify ecosystem
```

Evidence:

```text
axiom evidence inspect
axiom evidence verify
axiom evidence diff
```

---

# 70. Invariants

```text
AREL-01
A release must have a complete immutable manifest.

AREL-02
Every mandatory qualification gate must pass before stable release.

AREL-03
Skipped mandatory gates invalidate qualification.

AREL-04
Qualification evidence must be fingerprinted.

AREL-05
Release artifacts must be content-addressed.

AREL-06
Release provenance must identify compiler, source, dependencies, target and toolchain.

AREL-07
Conformance results must identify the exact specification and test-suite versions.

AREL-08
Fuzz qualification must identify corpus and execution configuration.

AREL-09
Performance qualification must identify hardware and benchmark baselines.

AREL-10
Reproducibility qualification must identify all declared build inputs.

AREL-11
Bootstrap qualification must verify stage convergence according to the release policy.

AREL-12
Self-hosting must not bypass ordinary conformance qualification.

AREL-13
Release gates must distinguish BLOCKING and NON-BLOCKING findings.

AREL-14
Waivers must be explicit, traceable and expirable.

AREL-15
A waiver must never silently convert a failure into success.

AREL-16
Stable releases must preserve declared language compatibility guarantees.

AREL-17
ABI changes must pass explicit ABI compatibility policy.

AREL-18
Unexpected runtime or native dependencies must fail the relevant release profile.

AREL-19
Release signatures must cover canonical release identity.

AREL-20
Revoked releases remain identifiable and auditable.

AREL-21
Release qualification must be reproducible.

AREL-22
Qualification caches must be fingerprint validated.

AREL-23
Release reports must preserve independent performance and size metrics.

AREL-24
No aggregate quality score may replace individual qualification dimensions.

AREL-25
A stable release must have a machine-readable qualification state.

AREL-26
Self-hosted compiler artifacts must retain provenance to the bootstrap chain.

AREL-27
Compiler release automation must use the global build scheduler.

AREL-28
Release failures must produce machine-readable diagnostic evidence.

AREL-29
Breaking language changes must be explicitly versioned.

AREL-30
Release engineering must never modify language semantics implicitly.
```

---

# 71. Definition of Done

BOOTSTRAP-344 hoàn thành khi Axiom có:

- release manifest;
- release channels;
- release candidate pipeline;
- qualification matrix;
- mandatory quality gates;
- immutable evidence;
- test/fuzz/performance provenance;
- reproducible release;
- bootstrap convergence;
- self-host qualification;
- diverse bootstrap support;
- security qualification;
- ABI compatibility gate;
- language compatibility gate;
- binary dependency validation;
- runtime-free validation;
- performance/size release gates;
- waiver system;
- release certificates;
- signing;
- revocation;
- rollback;
- canary testing;
- ecosystem qualification;
- machine-readable release status;
- automatic release report;
- complete release audit trail.

---

# 72. Kiến trúc Axiom sau 344

Đến đây pipeline phát triển compiler đã trở thành một hệ thống khép kín:

```text
                 ┌──────────────────┐
                 │ Axiom Spec       │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Reference Model  │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Axiom Compiler   │
                 └────────┬─────────┘
                          ↓
       ┌──────────────────┼───────────────────┐
       ↓                  ↓                   ↓
 Conformance           Fuzzing           Performance
       ↓                  ↓                   ↓
       └──────────────────┼───────────────────┘
                          ↓
                 ┌──────────────────┐
                 │ Qualification    │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Bootstrap        │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Self-hosting     │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Release          │
                 └──────────────────┘
```

Điểm quan trọng nhất của 344 là:

> **Axiom compiler không còn chỉ là một chương trình được build; nó trở thành một artifact có thể chứng minh được nguồn gốc, mức độ conformance, kết quả kiểm thử, performance, reproducibility và bootstrap chain.**

Đây là lớp rất quan trọng để biến Axiom từ **một thiết kế compiler** thành **một hệ sinh thái compiler có khả năng tự duy trì và phát hành đáng tin cậy**.