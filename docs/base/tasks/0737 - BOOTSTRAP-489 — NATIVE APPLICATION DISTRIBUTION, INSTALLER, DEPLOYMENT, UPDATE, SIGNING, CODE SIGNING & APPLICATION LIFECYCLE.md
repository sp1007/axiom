# BOOTSTRAP-489 — NATIVE APPLICATION DISTRIBUTION, INSTALLER, DEPLOYMENT, UPDATE, SIGNING, CODE SIGNING & APPLICATION LIFECYCLE

**Trạng thái: COMPLETED / LOCKED**

489 hoàn thiện phần còn thiếu giữa **compiler/package ecosystem** và **ứng dụng native được người dùng cài đặt, chạy, cập nhật và gỡ bỏ**.

Điểm quan trọng: Axiom compiler tạo artifact; package system phân phối package; **deployment system** biến artifact thành sản phẩm có thể cài đặt.

```text id="9q4m7x"
Axiom Source
    ↓
Build Graph
    ↓
Native Artifact
    ↓
Application Bundle
    ↓
Manifest
    ↓
Sign
    ↓
Package
    ↓
Installer / Store / Archive
    ↓
Install
    ↓
Runtime
    ↓
Update / Rollback / Uninstall
```

---

## 489.1 — Build artifact ≠ application package

Phải phân biệt:

```text id="w6k2p8"
Object
Executable
Library
Application Bundle
Distribution Package
Installer
Update Package
```

---

## 489.2 — Application identity

Mỗi application có:

```text id="m3r8c1"
ApplicationId
PackageId
Version
Edition
BuildId
Publisher
Target
```

`ApplicationId` phải ổn định qua các phiên bản.

---

## 489.3 — Application manifest

Canonical concept:

```text id="x7n4q2"
ApplicationManifest {
    id
    version
    executable
    targets
    resources
    dependencies
    capabilities
    entrypoints
    permissions
    files
    signing
    update_policy
}
```

---

## 489.4 — Bundle

Bundle chứa executable và resources cần thiết:

```text id="p5w9m3"
Executable
Runtime Components
Resources
Libraries
Manifest
Metadata
```

---

## 489.5 — Runtime dependency closure

Deployment tooling phải xác định chính xác runtime components cần thiết.

Không được copy toàn bộ Axiom runtime vào application.

---

## 489.6 — Native library dependency

Bundle phải phân biệt:

- Axiom library;
- system library;
- platform framework;
- optional plugin.

---

## 489.7 — System dependencies

Dependencies có thể là:

```text id="c8r2k6"
bundled
system-provided
optional
platform-required
```

---

## 489.8 — Dependency validation

Installer/deployment tool phải kiểm tra target compatibility trước install.

---

## 489.9 — Platform package

Axiom có thể generate platform-specific packages:

```text id="f1m7x4"
Windows
Linux
macOS
iOS
Android
WASM/Web
```

---

## 489.10 — Windows deployment

Artifact có thể được packaged thành native Windows application package hoặc portable distribution.

Không yêu cầu một installer technology duy nhất trong language core.

---

## 489.11 — Linux deployment

Có thể hỗ trợ:

- portable directory;
- archive;
- native package integration;
- system package metadata.

---

## 489.12 — macOS deployment

Application bundle phải hỗ trợ executable/resources/framework metadata và signing requirements của platform.

---

## 489.13 — Mobile deployment

iOS/Android cần application manifest, resources, signing identity và platform packaging.

---

## 489.14 — WASM deployment

WASM package có:

```text id="u5p8q1"
wasm module
imports
exports
web assets
manifest
```

---

## 489.15 — Installer ≠ package

Package là artifact distribution format.

Installer là operation:

```text id="r3k9m6"
verify
→ prepare
→ install
→ register
→ finalize
```

---

## 489.16 — Installation transaction

Install phải atomic ở mức package state.

---

## 489.17 — Partial installation

Nếu install fail giữa chừng:

```text id="n8c4w2"
rollback
```

hoặc chuyển sang clearly marked incomplete state.

---

## 489.18 — Installation directories

Platform adapter quyết định location.

Không hard-code một filesystem layout vào language semantics.

---

## 489.19 — Per-user installation

Được hỗ trợ khi OS cho phép.

---

## 489.20 — System installation

Được hỗ trợ khi caller có quyền thích hợp.

---

## 489.21 — Portable application

Application có thể được phân phối mà không cần installer nếu target hỗ trợ.

---

## 489.22 — File associations

Manifest có thể khai báo:

```text id="j4m7x2"
extensions
MIME types
URI schemes
```

---

## 489.23 — URL/deep-link activation

Application có thể khai báo URI schemes.

---

## 489.24 — Application capabilities

Manifest có thể khai báo:

```text id="z6p2n8"
filesystem
network
camera
microphone
GPU
location
notifications
```

Nhưng capability semantics phụ thuộc platform.

---

## 489.25 — Capability ≠ permission

Capability là application declaration.

Permission là OS/user policy.

---

## 489.26 — Permission state

Runtime phải có khả năng biểu diễn:

```text id="q8m3r5"
granted
denied
restricted
unknown
```

---

## 489.27 — Least privilege

Package không được tự động yêu cầu tất cả permissions.

---

## 489.28 — Resource declaration

469 resources phải được tích hợp vào bundle manifest.

---

## 489.29 — Resource integrity

Mỗi resource có thể có:

```text id="v1x7k4"
hash
size
type
```

---

## 489.30 — Compression

Package compression là distribution concern.

Không thay đổi runtime semantics.

---

## 489.31 — Executable signing

Native executable có thể được signed.

---

## 489.32 — Package signing

Package signature bảo vệ distribution artifact.

---

## 489.33 — Code signing ≠ package signing

Hai chữ ký có mục đích khác nhau:

```text id="s5n8q2"
Code signature
    → executable authenticity/integrity

Package signature
    → distribution artifact authenticity/integrity
```

---

## 489.34 — Publisher identity

Publisher identity phải explicit.

---

## 489.35 — Trust store

Trust anchors do platform/distribution policy quản lý.

Axiom không tự quyết định trust root toàn cầu.

---

## 489.36 — Signature verification

Verification phải kiểm tra:

- signature;
- artifact hash;
- signer;
- certificate/identity chain nếu platform dùng;
- validity policy.

---

## 489.37 — Expired signature

Expired certificate/signature policy phải được platform-aware.

---

## 489.38 — Revocation

Revocation có thể được kiểm tra nếu platform/distribution mechanism hỗ trợ.

---

## 489.39 — Offline verification

Signature verification cơ bản phải hoạt động offline khi trust material local.

---

## 489.40 — Timestamped signatures

Platform-specific timestamping có thể được hỗ trợ.

---

## 489.41 — Signing keys

Private signing keys không được đưa vào build artifact.

---

## 489.42 — Build/sign separation

Kiến trúc:

```text id="e3k7m1"
Build
 ↓
Artifact
 ↓
Review
 ↓
Sign
 ↓
Distribute
```

Signing không được silently mutate artifact.

---

## 489.43 — Reproducibility + signing

Signature metadata không được làm mất khả năng xác định underlying unsigned artifact.

---

## 489.44 — Update package

Update có thể chứa:

```text id="k8p4x2"
full package
delta package
resource-only update
```

---

## 489.45 — Delta update

Delta chỉ được apply khi base version/hash match.

---

## 489.46 — Update transaction

```text id="m6r1q9"
download
→ verify
→ stage
→ validate
→ switch
→ finalize
```

---

## 489.47 — Failed update

Nếu update fail, application phải giữ version cũ nếu platform cho phép.

---

## 489.48 — Rollback

Previous known-good version có thể được retained theo policy.

---

## 489.49 — Atomic version switch

Version mới chỉ trở thành active sau khi validation hoàn tất.

---

## 489.50 — Update channels

Có thể có:

```text id="x2c7n5"
stable
beta
nightly
custom
```

Channel là distribution policy, không phải language semantics.

---

## 489.51 — Update policy

Application manifest có thể khai báo:

```text id="j9m4w6"
manual
automatic
platform-managed
disabled
```

---

## 489.52 — No hidden network

Axiom runtime không tự động kiểm tra update.

Updater là explicit application/platform capability.

---

## 489.53 — Background update

Nếu platform hỗ trợ, updater có thể chạy background.

Không được biến thành mandatory runtime thread.

---

## 489.54 — Restart requirement

Update có thể yêu cầu restart.

State restoration tích hợp 468.

---

## 489.55 — Migration

Application data migration phải phân biệt:

```text id="q3n8p5"
application update
data schema migration
configuration migration
```

---

## 489.56 — Migration transaction

Data migration phải có recovery/rollback policy.

---

## 489.57 — Downgrade

Downgrade có thể bị từ chối nếu data schema không backward-compatible.

---

## 489.58 — Uninstall

Uninstall phải phân biệt:

```text id="w5m2x8"
program files
user data
cache
configuration
logs
shared data
```

---

## 489.59 — User data preservation

Uninstall không được silently destroy user data nếu platform policy không yêu cầu.

---

## 489.60 — Shared dependencies

Uninstaller không được xóa shared components đang được application khác sử dụng.

---

## 489.61 — Orphan detection

Package manager có thể detect unused dependencies.

---

## 489.62 — Application lifecycle

489 integrates 468:

```text id="u8r4k1"
Install
→ First Launch
→ Active
→ Suspended
→ Updated
→ Active
→ Uninstall
```

---

## 489.63 — First launch

First launch có thể initialize:

- configuration;
- user directories;
- caches;
- databases.

---

## 489.64 — Crash during first launch

Initialization phải recoverable.

---

## 489.65 — Resource registration

Installed resources phải map về 469 ResourceId.

---

## 489.66 — Runtime search path

Resource/library lookup phải deterministic.

---

## 489.67 — Library loading

Dynamic libraries phải validate architecture/ABI before load.

---

## 489.68 — Plugin loading

Plugins là explicit capability.

Không tự động load arbitrary libraries từ working directory.

---

## 489.69 — Plugin trust

Untrusted plugins phải có isolation mechanism nếu application yêu cầu security.

---

## 489.70 — Executable permissions

Installer không được biến arbitrary data thành executable.

---

## 489.71 — File permission preservation

Platform package có thể preserve required permission metadata.

---

## 489.72 — Symlink handling

Installer phải có explicit symlink policy để tránh path traversal.

---

## 489.73 — Path traversal

Archive extraction phải reject paths escaping installation root.

---

## 489.74 — Archive bomb

Installer phải có resource limits.

---

## 489.75 — Package integrity

Package phải verify size/hash trước và trong extraction khi cần.

---

## 489.76 — Dependency provenance

447 metadata được carry vào deployment manifest.

---

## 489.77 — SBOM-like inventory

Package có thể export machine-readable component inventory:

```text id="c6n1x8"
component
version
hash
license
provenance
```

---

## 489.78 — License metadata

Package ecosystem có thể carry license metadata.

Language core không áp đặt một license model.

---

## 489.79 — Vulnerability metadata

Distribution tooling có thể consume external vulnerability databases.

Không tự động biến vulnerability metadata thành compiler semantics.

---

## 489.80 — Update security

Unsigned/untrusted updates phải bị reject theo configured policy.

---

## 489.81 — Rollback security

Rollback target cũng phải verify signature/integrity.

---

## 489.82 — Reproducible deployment

Deployment package có thể reproducibly generated từ cùng application bundle.

---

## 489.83 — Package timestamp normalization

Archive metadata timestamps có thể normalize.

---

## 489.84 — File ordering

Package file ordering phải deterministic.

---

## 489.85 — Compression determinism

Nếu deterministic mode bật, compressor configuration phải fixed.

---

## 489.86 — Deployment manifest hash

Manifest có canonical serialization để hashing/signing.

---

## 489.87 — Application identity continuity

Update không được vô tình tạo application identity mới.

---

## 489.88 — Version comparison

Version ordering phải dùng semantic version policy đã định nghĩa.

---

## 489.89 — Platform version

Platform/OS version phải tách khỏi application version.

---

## 489.90 — Compatibility declaration

Manifest có thể khai báo:

```text id="p7m3x9"
minimum_os
maximum_tested_os
required_arch
required_cpu_features
required_sdk
```

---

## 489.91 — CPU feature compatibility

Application package có thể có multiple binaries:

```text id="r5k8c2"
baseline
SSE/AVX
ARM feature variants
```

Runtime dispatch 458 chọn implementation phù hợp khi semantics cho phép.

---

## 489.92 — Multi-architecture bundle

Một package có thể chứa nhiều architectures.

---

## 489.93 — Architecture mismatch

Installer phải reject incompatible executable thay vì cài rồi fail mơ hồ.

---

## 489.94 — Native artifact inspection

Deployment tooling có thể inspect:

```text id="x1q6n4"
architecture
ABI
imports
exports
runtime components
signatures
dependencies
```

---

## 489.95 — Deployment diagnostics

Errors phải machine-readable:

```text id="d8m2w7"
E489xxx
```

---

## 489.96 — AI deployment query

AI có thể query:

```text id="n4p8c1"
package_dependencies()
required_capabilities()
target_compatibility()
signature_status()
update_path()
bundle_contents()
```

---

## 489.97 — Installer logs

Installer sử dụng structured logging 475.

---

## 489.98 — Deployment tracing

489 có thể tích hợp 481 để đo:

- install time;
- extraction time;
- update time;
- download;
- verification.

---

## 489.99 — Deployment testing

Test cases:

```text id="k2r7m5"
install
upgrade
downgrade
rollback
uninstall
interrupted install
corrupt package
wrong architecture
invalid signature
missing dependency
```

---

## 489.100 — Hard invariants

1. Artifact khác application package.
2. Application identity ổn định.
3. Manifest là structured metadata.
4. Bundle chứa executable/resources cần thiết.
5. Runtime closure được tính.
6. System dependencies được phân biệt.
7. Target compatibility được validate.
8. Platform packaging được hỗ trợ.
9. Installer khác package.
10. Installation transactional.
11. Partial installation không được giả dạng successful install.
12. Portable deployment được hỗ trợ.
13. File associations explicit.
14. URI activation explicit.
15. Capabilities explicit.
16. Capability khác permission.
17. Permission state được biểu diễn.
18. Least privilege được khuyến khích ở packaging policy.
19. Resource manifest tích hợp 469.
20. Resource integrity được hỗ trợ.
21. Code signing được hỗ trợ.
22. Package signing được hỗ trợ.
23. Code signing khác package signing.
24. Publisher identity explicit.
25. Trust roots không hard-code vào language.
26. Signature verification được hỗ trợ.
27. Offline verification được hỗ trợ.
28. Private signing keys không nằm trong artifacts.
29. Build và signing tách biệt.
30. Signing không silently mutate payload.
31. Update packages được hỗ trợ.
32. Delta update base hash phải match.
33. Update có transaction.
34. Failed update không được silently activate.
35. Rollback được hỗ trợ.
36. Version switching atomic.
37. Update channels là policy.
38. Runtime không tự update.
39. Background updater không mandatory.
40. Restart semantics tích hợp 468.
41. Data migration tách khỏi binary update.
42. Migration có recovery policy.
43. Downgrade phải kiểm tra data compatibility.
44. Uninstall phân biệt application/user data.
45. User data không bị silently destroy.
46. Shared dependencies không bị xóa sai.
47. Plugin loading explicit.
48. Arbitrary libraries không được tự động load.
49. Executable permissions được kiểm soát.
50. Symlink extraction có policy.
51. Path traversal phải bị ngăn.
52. Archive resource exhaustion phải được giới hạn.
53. Package integrity được verify.
54. Dependency provenance được giữ.
55. Component inventory được hỗ trợ.
56. License metadata được hỗ trợ.
57. External vulnerability metadata có thể integrate.
58. Update security được verify.
59. Rollback target cũng được verify.
60. Deployment có thể reproducible.
61. Archive timestamps có thể normalize.
62. File ordering deterministic.
63. Manifest serialization canonical.
64. Application identity continuity được bảo đảm.
65. Application version khác platform version.
66. Compatibility requirements được khai báo.
67. CPU feature variants được hỗ trợ.
68. Multi-architecture packages được hỗ trợ.
69. Architecture mismatch được detect trước execution.
70. Native artifacts có thể inspect.
71. Deployment diagnostics machine-readable.
72. AI deployment queries được hỗ trợ.
73. Installer logs structured.
74. Deployment performance được measurable.
75. Install/update/uninstall failure cases được test.
76. Deployment không yêu cầu GC.
77. Deployment không yêu cầu external compiler.
78. Runtime không tự động tải network resource.
79. Platform-specific behavior nằm ở platform layer.
80. **Axiom deployment phải đưa native artifacts tới người dùng một cách có thể kiểm chứng, transactional và rollback được, trong khi compiler/runtime không bị biến thành một updater, installer hoặc store service bắt buộc.**

**BOOTSTRAP-489 hoàn tất / LOCKED.**

---

# BOOTSTRAP-490 — APPLICATION SECURITY, SANDBOXING, CAPABILITY SYSTEM, PROCESS ISOLATION, PLUGIN TRUST & SECURE IPC

490 mở rộng 445 từ **memory/language safety** sang **application-level security architecture**.

Mục tiêu là cho phép Axiom xây được:

- desktop apps;
- servers;
- plugins;
- sandboxed applications;
- WASM applications;
- helper processes;

mà không biến mọi application thành sandbox hoặc ép runtime phải có security overhead.

```text id="m8q3v7"
Application
    │
    ├── Trusted Code
    │
    ├── Untrusted Plugin
    │
    ├── Helper Process
    │
    └── Sandboxed Module
            │
            ↓
       Capability Boundary
            │
      ┌─────┼─────┐
      ↓     ↓     ↓
     IPC   Files  Network
```

---

## 490.1 — Language safety ≠ application security

```text id="c5r8n2"
Language Safety
    → memory/type/ownership correctness

Application Security
    → trust boundaries/capabilities/isolation
```

---

## 490.2 — Trust domains

Application có thể chia thành:

```text id="p7m1x9"
trusted
semi-trusted
untrusted
```

---

## 490.3 — Process isolation

OS process là isolation primitive mạnh.

Axiom không giả định mọi module cùng trust domain.

---

## 490.4 — In-process plugin

In-process plugin mặc định nằm cùng trust boundary với host.

Không coi dynamic library là sandbox.

---

## 490.5 — Out-of-process plugin

Untrusted plugin nên chạy process riêng.

---

## 490.6 — WASM sandbox

WASM có thể làm isolation boundary khi platform runtime hỗ trợ.

---

## 490.7 — Capability model

Capability biểu diễn quyền thực tế:

```text id="x4n8q2"
Capability {
    kind
    scope
    authority
    lifetime
}
```

---

## 490.8 — Capability types

Ví dụ:

```text id="j6r2m5"
FileCapability
NetworkCapability
ProcessCapability
WindowCapability
GPUCapability
DeviceCapability
```

---

## 490.9 — Ambient authority

Axiom không nên mặc định cấp mọi authority cho library/module.

---

## 490.10 — Explicit authority

API có thể yêu cầu capability:

```text id="w8p3k1"
read(file_cap, path)
```

---

## 490.11 — Capability delegation

Một component có thể truyền capability cho component khác.

---

## 490.12 — Capability attenuation

Capability có thể được giới hạn scope.

Ví dụ:

```text id="r5m9c2"
filesystem root = /app/data
```

thay vì toàn filesystem.

---

## 490.13 — Capability revocation

Capabilities có thể có lifetime/revocation semantics.

---

## 490.14 — Capability ownership

Capability là resource theo 423 nếu nó sở hữu OS handle.

---

## 490.15 — Capability duplication

Duplication phải explicit nếu underlying authority cho phép.

---

## 490.16 — Capability transfer

Transfer giữa threads/processes phải tuân ownership/concurrency rules.

---

## 490.17 — Process capability passing

OS handle passing/IPC có thể truyền authority.

---

## 490.18 — IPC security

IPC endpoint phải có identity/authentication hoặc OS authorization mechanism phù hợp.

---

## 490.19 — Local IPC

Supported primitives:

```text id="n3x7q8"
pipe
named pipe
Unix socket
shared memory
socket
OS message port
```

---

## 490.20 — IPC message validation

Mọi external IPC data là untrusted.

---

## 490.21 — Serialization safety

Deserialize phải bounds-check và enforce resource limits.

---

## 490.22 — No arbitrary deserialization execution

Data decoding không được tự động execute code.

---

## 490.23 — Shared memory

Shared memory phải explicit.

---

## 490.24 — Shared memory synchronization

Concurrent access phải dùng defined synchronization protocol.

---

## 490.25 — Shared memory layout

Cross-process shared structures cần stable representation:

```text id="f7m2k9"
@repr(C)
fixed-width types
explicit endian
version
```

---

## 490.26 — Shared memory versioning

Protocol phải có versioning.

---

## 490.27 — Network trust

Network input luôn được coi là untrusted.

---

## 490.28 — TLS integration

454 TLS provider có thể bảo vệ network channels.

---

## 490.29 — Authentication

Authentication là protocol/library concern.

---

## 490.30 — Authorization

Authorization phải được phân biệt với authentication.

---

## 490.31 — Secret handling

Secrets không nên nằm trong ordinary String nếu API có secure-memory abstraction.

---

## 490.32 — Secure memory

Secure-memory type có thể hỗ trợ:

- zeroization;
- restricted debugging;
- non-swappable memory khi OS hỗ trợ.

Không có guarantee tuyệt đối.

---

## 490.33 — Key material

Cryptographic keys từ 456 phải có explicit lifecycle.

---

## 490.34 — Logging secrets

475 redaction phải integrate với security metadata.

---

## 490.35 — Command execution

Process spawning phải require explicit Process capability trong capability-aware APIs.

---

## 490.36 — Shell execution

Shell invocation phải explicit và không được mặc định interpolate untrusted strings.

---

## 490.37 — Path security

File APIs phải có safe path resolution options.

---

## 490.38 — Symlink attacks

Security-sensitive APIs có thể yêu cầu no-follow / beneath-root semantics nếu OS hỗ trợ.

---

## 490.39 — Temporary files

Secure temporary resources phải được tạo bằng OS-safe primitives.

---

## 490.40 — Environment variables

Environment là untrusted configuration boundary trong security-sensitive contexts.

---

## 490.41 — Dynamic library loading

Loading arbitrary dynamic libraries là security-sensitive operation.

---

## 490.42 — Plugin manifest

Plugin manifest có thể khai báo:

```text id="q2w8m4"
identity
version
ABI
capabilities
entrypoints
signature
```

---

## 490.43 — Plugin ABI

451 ABI/FFI rules apply.

---

## 490.44 — Plugin ABI compatibility

Host phải verify plugin ABI trước load.

---

## 490.45 — Plugin lifecycle

```text id="v6n3r9"
discover
→ verify
→ load
→ initialize
→ run
→ shutdown
→ unload
```

---

## 490.46 — Plugin unload

Host phải không còn live callbacks/resources trước unload.

---

## 490.47 — Callback safety

Foreign/plugin callbacks phải obey ownership/thread/reentrancy rules.

---

## 490.48 — Plugin crash

In-process plugin crash có thể crash host.

Out-of-process plugin cho phép fault isolation.

---

## 490.49 — Plugin recommendation

Tooling không được tự động coi plugin là trusted chỉ vì package tồn tại.

---

## 490.50 — Signature verification

Plugin package/executable signatures có thể được verified trước load.

---

## 490.51 — Signature ≠ safe

Valid signature chứng minh identity/integrity theo trust policy, không chứng minh code không có bug.

---

## 490.52 — Sandboxed plugin

Sandbox policy có thể restrict:

```text id="k7m1p4"
filesystem
network
process
GPU
device
IPC
```

---

## 490.53 — Sandbox implementation

Platform mechanisms:

- process sandbox;
- OS security policy;
- WASM;
- container-like isolation;
- job/object restrictions.

---

## 490.54 — No universal sandbox

Language core không quy định một sandbox implementation duy nhất.

---

## 490.55 — Security policy

Security policy có thể be:

```text id="z4r8n2"
deny
allow
prompt
inherit
```

---

## 490.56 — Capability manifest

Application package 489 có thể declare requested capabilities.

---

## 490.57 — User consent

Platform có thể request user permission.

Axiom language semantics không tự động assume consent.

---

## 490.58 — Permission revocation

Application phải handle permission revoked/restricted.

---

## 490.59 — Fail closed

Security-sensitive operation nên return explicit failure nếu capability unavailable.

---

## 490.60 — No privilege escalation

Capability system không tự cấp authority cao hơn authority holder.

---

## 490.61 — Confused deputy

API thiết kế phải tránh library sử dụng host authority thay caller intent một cách hidden.

---

## 490.62 — Authority provenance

Security metadata có thể track:

```text id="m9x2c5"
who created capability
who delegated it
who consumed it
```

---

## 490.63 — Security graph

```text id="p4k7w1"
Principal
 ↓
Capability
 ↓
Resource
 ↓
Operation
```

---

## 490.64 — AI security query

AI có thể query:

```text id="c8n3q6"
security_boundary()
capabilities(symbol)
capability_flow()
unsafe_sites()
external_inputs()
plugin_trust()
```

---

## 490.65 — External input graph

445 + 454 + 455 + 490 có thể track:

```text id="u2m8r4"
Network
File
IPC
Plugin
User Input
   ↓
Parser
   ↓
Validation
   ↓
Trusted State
```

---

## 490.66 — Taint integration

478 static analyzer có thể propagate taint labels.

---

## 490.67 — Sanitizer integration

480 can detect some runtime violations.

---

## 490.68 — Contract integration

479 contracts có thể validate security preconditions.

---

## 490.69 — Authentication state

Authentication state phải không được confused với authorization capability.

---

## 490.70 — Session capability

Capabilities có thể expire with session.

---

## 490.71 — Time-bound authority

Capability có thể gắn Deadline từ 474.

---

## 490.72 — Rate limits

Security APIs có thể expose resource/rate limits.

---

## 490.73 — Resource exhaustion

Sandbox must limit:

```text id="r8k2m6"
memory
CPU
threads
file descriptors
disk
network
message size
```

khi platform hỗ trợ.

---

## 490.74 — Denial-of-service

Network/storage/parser APIs phải expose resource-limit mechanisms.

---

## 490.75 — IPC message size

Maximum message size phải explicit hoặc bounded.

---

## 490.76 — Recursion/resource limits

Untrusted parsers có thể enforce depth/size limits.

---

## 490.77 — Compression bomb

Decompression APIs phải hỗ trợ output/resource limits.

---

## 490.78 — Archive extraction

489 installer security rules áp dụng.

---

## 490.79 — Browser/WASM security

WASM application capabilities phụ thuộc browser imports/permissions.

---

## 490.80 — Native application

Native Axiom application không tự nhiên trở thành sandbox.

---

## 490.81 — Security profile

Build/deployment có thể select:

```text id="f5q1n8"
normal
hardened
sandboxed
high-assurance
```

---

## 490.82 — Hardened profile

Có thể enable:

- CFI;
- stack protection;
- W^X;
- hardened allocator;
- additional checks.

---

## 490.83 — Security profile ≠ semantics

Security profile không được silently alter normal language semantics.

---

## 490.84 — Reproducibility

Security hardening configuration trở thành build input.

---

## 490.85 — Secure update

489 update verification phải integrate security policy.

---

## 490.86 — Rollback protection

Application có thể enforce minimum supported version để tránh downgrade attacks.

---

## 490.87 — Key rotation

Package/plugin signing infrastructure phải hỗ trợ key rotation.

---

## 490.88 — Trust revocation

Revoked publisher/plugin phải có mechanism để reject future loads.

---

## 490.89 — Audit trail

Security-sensitive operations có thể emit structured audit records.

---

## 490.90 — Privacy

Audit records không được tự động chứa secrets hoặc sensitive payloads.

---

## 490.91 — No automatic telemetry

Security events không được tự động upload.

---

## 490.92 — Secure defaults

Security-sensitive APIs phải default về conservative behavior nếu không gây hidden compatibility surprises.

---

## 490.93 — Unsafe escape hatch

Unsafe APIs vẫn có thể bypass some safety constraints nhưng không bypass OS authorization.

---

## 490.94 — Kernel/driver mode

Freestanding/kernel code có thể không có ordinary capability runtime.

---

## 490.95 — Embedded

Embedded security policy có thể map capability abstraction tới hardware/RTOS mechanisms.

---

## 490.96 — Capability-less applications

Ordinary applications có thể sử dụng traditional OS APIs mà không bắt buộc capability wrapper.

---

## 490.97 — Zero overhead principle

Capability metadata không được tạo runtime overhead khi application không sử dụng capability/security framework.

---

## 490.98 — Security testing

Tests phải bao gồm:

```text id="x7m2q8"
invalid capability
revoked capability
malformed IPC
oversized message
invalid signature
plugin ABI mismatch
sandbox escape attempt
path traversal
resource exhaustion
```

---

## 490.99 — Fuzzing

435 fuzzing framework phải được dùng cho:

- protocol parsers;
- package parsers;
- manifest parser;
- plugin loader;
- IPC serialization;
- capability policy parser.

---

## 490.100 — Security diagnostics

Machine-readable:

```text id="s4p8n1"
E490xxx
```

---

## 490.101 — Hard invariants

1. Application security khác language safety.
2. Trust domains được hỗ trợ.
3. Process isolation là security boundary.
4. In-process plugin không phải sandbox.
5. Out-of-process plugin được hỗ trợ.
6. WASM sandbox được hỗ trợ.
7. Capability model được hỗ trợ.
8. Capability có kind/scope/authority/lifetime.
9. File/network/process capabilities được hỗ trợ.
10. Ambient authority không phải requirement.
11. Explicit authority được hỗ trợ.
12. Capability delegation được hỗ trợ.
13. Capability attenuation được hỗ trợ.
14. Capability revocation được hỗ trợ.
15. Capability ownership tích hợp 423.
16. Capability transfer obey concurrency/ownership.
17. IPC có security boundary.
18. IPC data là untrusted.
19. Serialization có bounds/resource validation.
20. Deserialization không tự execute code.
21. Shared memory explicit.
22. Shared memory synchronization explicit.
23. Shared memory representation stable khi cross-process.
24. Shared memory versioned.
25. Network input untrusted.
26. TLS tích hợp 454.
27. Authentication khác authorization.
28. Secrets có lifecycle rõ.
29. Secure memory abstraction được hỗ trợ.
30. Key material lifecycle explicit.
31. Logs phải hỗ trợ secret redaction.
32. Process execution cần explicit authority trong capability APIs.
33. Shell execution explicit.
34. Untrusted path có safe resolution.
35. Symlink attacks được address.
36. Secure temporary files được hỗ trợ.
37. Environment là trust boundary.
38. Dynamic library loading là security-sensitive.
39. Plugin manifest có identity/version/ABI/capabilities.
40. Plugin ABI được verify.
41. Plugin lifecycle explicit.
42. Plugin unload phải đảm bảo callbacks/resources.
43. In-process plugin crash boundary được phân biệt.
44. Plugin signature có thể verify.
45. Signature không phải proof of safety.
46. Sandboxed plugins được hỗ trợ.
47. Sandbox implementation platform-specific.
48. Không có universal sandbox trong language core.
49. Security policies explicit.
50. Package capabilities tích hợp 489.
51. Permission khác capability.
52. Permission revocation được handle.
53. Security operation failure explicit.
54. Capability không tự escalate privilege.
55. Confused deputy risks được address.
56. Capability provenance có thể track.
57. Security graph được hỗ trợ.
58. AI security queries được hỗ trợ.
59. External input flow có thể track.
60. Taint analysis tích hợp 478.
61. Sanitizer evidence tích hợp 480.
62. Contracts tích hợp 479.
63. Authentication state không thay authorization.
64. Session-bound capabilities được hỗ trợ.
65. Time-bound capabilities có thể dùng Deadline.
66. Resource/rate limits được hỗ trợ.
67. Sandbox resource limits được hỗ trợ khi platform cho phép.
68. IPC message sizes phải bounded/explicit.
69. Parser depth/resource limits được hỗ trợ.
70. Decompression resource limits được hỗ trợ.
71. Archive extraction security được tích hợp.
72. WASM permissions explicit.
73. Native application không mặc định sandbox.
74. Security profiles được hỗ trợ.
75. Hardened profile có thể enable platform protections.
76. Security profile không silently thay semantics.
77. Security config là build input.
78. Secure update tích hợp 489.
79. Rollback protection có thể được hỗ trợ.
80. Signing key rotation được hỗ trợ.
81. Publisher/plugin revocation được hỗ trợ.
82. Security audit records được hỗ trợ.
83. Audit records không leak secrets.
84. Security telemetry không tự động upload.
85. Security-sensitive APIs có conservative defaults.
86. Unsafe không bypass OS authorization.
87. Kernel/embedded có thể dùng security model riêng.
88. Capability framework không bắt buộc cho ordinary native APIs.
89. Unused security framework không gây hidden runtime overhead.
90. Security tests bao phủ capability/IPC/plugin/sandbox/path/resource cases.
91. Fuzzing tích hợp security parsers.
92. Security diagnostics machine-readable.
93. Security evidence phân biệt static/runtime/test evidence.
94. Không tuyên bố sandbox an toàn tuyệt đối.
95. Không coi signature là correctness proof.
96. Không coi sanitizer absence là security proof.
97. Security boundary phải có provenance.
98. AI không được tự suy luận trust chỉ từ package existence.
99. Security policy phải có source/provenance rõ.
100. **Axiom phải cho phép xây dựng cả ứng dụng native truyền thống lẫn hệ thống có trust boundary mạnh, bằng cách đưa capability, process isolation, sandbox, secure IPC và plugin trust thành các lớp explicit; application không sử dụng chúng không phải trả hidden runtime cost.**

**BOOTSTRAP-490 hoàn tất / LOCKED.**

---

# TIẾN ĐỘ HIỆN TẠI

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
```

**Task kế tiếp: `BOOTSTRAP-491 — PACKAGE REGISTRY PROTOCOL, REMOTE ARTIFACT SERVICE, CONTENT-ADDRESSABLE STORAGE, MIRRORING, OFFLINE VENDORING & ECOSYSTEM INFRASTRUCTURE`.**