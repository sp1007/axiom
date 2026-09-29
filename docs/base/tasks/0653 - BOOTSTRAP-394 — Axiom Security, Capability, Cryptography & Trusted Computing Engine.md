# BOOTSTRAP-394 — Axiom Security, Capability, Cryptography & Trusted Computing Engine

Sau **393 — Distributed Systems**, bước tiếp theo nên khóa một vấn đề nền tảng còn thiếu: **security semantics**.

Không nên chỉ có “thư viện crypto”. Axiom cần một mô hình để compiler hiểu được:

> **Dữ liệu nào được phép truy cập, resource nào được phép sử dụng, code nào đáng tin cậy, boundary nào cần kiểm tra, và security property nào có thể được chứng minh hoặc tối ưu.**

Mục tiêu là security **không biến thành runtime overhead bắt buộc**.

---

# 1. Ba tầng Security

Phân biệt:

```text
Memory Safety
     ↓
Resource / Capability Security
     ↓
Cryptographic Security
```

Ví dụ:

- `view<T>` → memory capability.
- file handle → resource capability.
- encryption key → cryptographic capability.

Không gom tất cả thành một cơ chế.

---

# 2. Capability-Based Security

Axiom nên sử dụng capability như một semantic abstraction:

```text
Capability<T>
```

Capability biểu diễn:

```text
identity
authority
scope
rights
lifetime
```

---

# 3. Capability ≠ Handle

```text
Handle
```

chỉ xác định resource.

```text
Capability
```

xác định **quyền thực hiện operation** trên resource.

Một process có thể biết:

```text
FileId
```

nhưng không có:

```text
WriteCapability<File>
```

---

# 4. Principle of Least Authority

API nên nhận capability tối thiểu.

Thay vì:

```text
save(data)
```

ngầm truy cập filesystem, API nên cần:

```text
save(file_write_capability, data)
```

hoặc capability được đóng trong resource type.

---

# 5. Ambient Authority

Axiom không nên có implicit global:

```text
current_user
current_filesystem
global_network
global_secret
```

nếu security-sensitive.

Dependency phải đi qua explicit capability/context.

---

# 6. Capability Transfer

Capability có thể được:

```text
move
split
restrict
delegate
revoke
```

theo contract.

---

# 7. Capability Restriction

Có capability:

```text
File<RW>
```

có thể tạo:

```text
File<R>
```

nhưng không ngược lại trong safe code.

---

# 8. Capability Delegation

Một service có thể cấp:

```text
ReadCapability<UserData>
```

cho service khác mà không cấp:

```text
WriteCapability<UserData>
```

---

# 9. Capability Lifetime

Capability không được sống lâu hơn resource mà nó cấp quyền.

Đây là extension trực tiếp của ownership/view model.

---

# 10. Revocation

Một capability có thể cần revoke.

Không nên dùng pointer invalidation.

Có thể dùng:

```text
Generation
Epoch
Lease
RevocationToken
```

tùy abstraction.

---

# 11. Memory Capability

Các abstraction đã có:

```text
view<T>
mut_view<T>
raw pointer
```

có thể được coi là memory capabilities.

Compiler đã kiểm tra:

```text
provenance
lifetime
bounds
access
```

394 thống nhất terminology này với security capability.

---

# 12. Security Boundary

Security boundary:

```text
Process
Thread
Task
Actor
Service
Node
Device
Sandbox
```

không giống nhau.

Mỗi boundary có security semantics riêng.

---

# 13. Trust Domain

Có thể biểu diễn:

```text
TrustDomain
```

ví dụ:

```text
Trusted
Untrusted
Foreign
Sandboxed
Kernel
Device
```

Nhưng đây là compiler/security metadata, không phải runtime object bắt buộc.

---

# 14. Unsafe Code

`unsafe` không đồng nghĩa:

```text
trusted
```

Nó chỉ có nghĩa:

> Programmer assumes responsibility for invariants compiler cannot prove automatically.

Security verification vẫn tiếp tục.

---

# 15. FFI Trust Boundary

Foreign function:

```text
extern fn foo(...)
```

là boundary.

Compiler phải biết:

```text
ownership
alias
thread safety
effects
security assumptions
```

nếu contract được khai báo.

---

# 16. Untrusted Input

Input từ:

```text
network
file
IPC
user
device
```

không được tự động coi là trusted typed value.

Ví dụ:

```text
bytes
 ↓ validation
UserId
```

khác:

```text
unsafe cast
```

---

# 17. Validated Types

Có thể dùng typestate:

```text
RawInput
Validated<T>
```

Compiler/generic system có thể đảm bảo validation đã xảy ra trước khi API nhạy cảm được gọi.

---

# 18. Parser Security

Protocol decoder phải phân biệt:

```text
Decode
Validate
Normalize
Authorize
```

Không được coi decode thành công là input hợp lệ về business semantics.

---

# 19. Canonicalization

Security-sensitive strings/data cần canonical representation.

Ví dụ:

```text
path
URL
Unicode text
identifiers
```

có thể có:

```text
raw
normalized
canonical
```

states.

---

# 20. Path Security

Filesystem path cần phân biệt:

```text
RawPath
NormalizedPath
SandboxedPath
```

để tránh security bugs ở abstraction layer.

---

# 21. Secret Data

Axiom nên có semantic marker:

```text
Secret<T>
```

không nhất thiết có runtime wrapper.

Compiler có thể biết secret data cần:

```text
no debug dump
no accidental logging
restricted serialization
controlled memory lifetime
```

---

# 22. Secret Memory

Compiler có thể hỗ trợ:

```text
@secret
```

hoặc equivalent attribute.

Có thể yêu cầu:

```text
no core dump
no swap
zeroize
no debug exposure
```

nhưng từng property phải explicit.

---

# 23. Zeroization

Secret:

```text
SecretKey
```

có thể yêu cầu:

```text
zeroize()
```

trước khi storage lifetime kết thúc.

Compiler phải tránh tối ưu hóa zeroization thành dead code khi security contract yêu cầu nó.

---

# 24. Constant-Time

Cryptographic code có thể cần:

```text
@constant_time
```

Compiler không được thực hiện transformation tạo timing-dependent branch/memory access trái với contract.

---

# 25. Constant-Time Scope

Không phải mọi crypto function đều có thể guarantee absolute constant time trên mọi CPU.

Contract nên phân biệt:

```text
SourceConstantTime
TargetConstantTime
HardwareAssisted
BestEffort
```

---

# 26. Timing Side Channel

Security analyzer có thể theo dõi:

```text
Secret
 ↓
branch
 ↓
observable timing
```

và cảnh báo/reject theo security profile.

---

# 27. Secret-Dependent Memory Access

Ví dụ:

```text
table[secret]
```

có thể tạo cache side channel.

Security analysis có thể đánh dấu:

```text
SecretDependentAddress
```

---

# 28. Cryptographic Primitive

Core không nên tích hợp toàn bộ crypto algorithm.

Standard/security library cung cấp:

```text
Hash
MAC
AEAD
Signature
KDF
KeyExchange
```

---

# 29. Hash

Generic contract:

```text
Hash<T>
```

với properties:

```text
deterministic
fixed_output
collision_resistance
```

tùy algorithm.

---

# 30. Cryptographic Hash ≠ General Hash

Không được dùng:

```text
HashMap hash
```

cho security semantics.

Hai trait nên tách.

---

# 31. MAC

```text
Mac<Key, Message>
```

phải giữ key ownership/secret semantics.

---

# 32. AEAD

Authenticated encryption:

```text
AEAD<Key>
```

semantic output:

```text
Ciphertext
AuthenticationTag
```

Associated Data phải được bảo toàn.

---

# 33. Nonce

Nonce reuse là security-critical.

API nên thiết kế để compiler/type system hạn chế misuse.

Ví dụ abstraction:

```text
NonceSequence
```

thay vì cho phép tùy ý dùng cùng nonce.

---

# 34. Randomness

394 dùng RNG từ 376.

Phân biệt:

```text
FastRng
DeterministicRng
SecureRng
```

Không được dùng RNG nhanh thay cho CSPRNG trong security API.

---

# 35. Key

Key nên có type riêng:

```text
Key<Aes256>
PrivateKey<Ed25519>
PublicKey<Ed25519>
```

không phải:

```text
Array<u8>
```

về mặt API semantics.

---

# 36. Key Type Safety

Không cho:

```text
PrivateKey<A>
```

truyền vào API cần:

```text
PublicKey<B>
```

nếu generic constraints không cho phép.

---

# 37. Key Lifetime

Key material phải tuân thủ ownership:

```text
create
use
zeroize
drop
```

không implicit copy nếu security contract cấm.

---

# 38. Key Export

Export private key nên là explicit operation:

```text
export_private_key()
```

không implicit serialization.

---

# 39. Key Storage

Có thể có:

```text
KeyStore
```

cho:

```text
memory
OS keychain
HSM
TPM
secure enclave
remote KMS
```

---

# 40. Hardware Security

Axiom không cần biết chi tiết TPM/TEE/HSM trong Core.

Chỉ cần abstraction:

```text
SecureKeyHandle
```

với explicit capability semantics.

---

# 41. Secure Enclave

Key có thể không bao giờ xuất hiện dưới dạng ordinary bytes.

Ví dụ:

```text
SecureKeyHandle
```

chỉ cho phép:

```text
sign()
decrypt()
derive()
```

---

# 42. Cryptographic Key vs Capability

Một key có thể là:

```text
cryptographic secret
```

Capability là:

```text
authority
```

Chúng liên quan nhưng không đồng nhất.

---

# 43. Authentication

Identity:

```text
Identity
Credential
Proof
Session
```

phải tách.

---

# 44. Authorization

Authorization có thể dựa trên:

```text
Role
Permission
Capability
Policy
Attribute
```

nhưng không hard-code một mô hình duy nhất.

---

# 45. Policy

Security policy nên có representation compile-time khi có thể.

Ví dụ:

```text
Policy<ReadUserData>
```

có thể được compiler specialize.

---

# 46. Policy Evaluation

Policy có thể là:

```text
static
dynamic
remote
```

Dynamic policy cần runtime evaluation.

---

# 47. Sandbox

Axiom có thể xây sandboxed execution:

```text
Sandbox
```

giới hạn:

```text
filesystem
network
process
device
memory
time
```

dựa trên capabilities.

---

# 48. Sandboxed Code

Code không có capability:

```text
NetworkCapability
```

không thể gọi network operation yêu cầu capability trong safe semantic model.

---

# 49. Comptime Security

Comptime đã có capability sandbox.

394 bổ sung security classification:

```text
Comptime
 ├── trusted
 └── restricted
```

Không cho comptime code tự ý đọc secrets/build environment nhạy cảm nếu capability không được cấp.

---

# 50. Build Security

Build system phải theo dõi:

```text
source
dependencies
tools
environment
generated files
```

để chống supply-chain attacks.

331 đã cung cấp hermetic build.

394 thêm security metadata.

---

# 51. Dependency Trust

Package có thể có:

```text
signature
publisher identity
version
hash
provenance
```

Không biến package registry thành trust root duy nhất.

---

# 52. Artifact Integrity

Executable:

```text
Axiom binary
```

có thể có:

```text
hash
signature
certificate
provenance
```

theo deployment policy.

---

# 53. Code Signing

Code signing là deployment layer.

Compiler có thể emit metadata:

```text
BuildIdentity
ArtifactHash
SourceRevision
CompilerVersion
Target
Features
```

---

# 54. Reproducible Build

Security system nên hỗ trợ:

```text
same source
+
same dependencies
+
same configuration
+
same toolchain
```

→ cùng artifact hoặc byte-for-byte reproducible artifact theo profile.

---

# 55. Supply Chain

Build graph có thể tạo:

```text
SBOM
Provenance
DependencyGraph
ArtifactManifest
```

mà không cần runtime overhead.

---

# 56. Memory Hardening

Compiler có thể hỗ trợ optional hardening:

```text
ASLR
DEP/NX
stack protection
CFI
shadow stack
control-flow protection
```

tùy target.

Không được giả định mọi CPU có cùng mechanism.

---

# 57. Control-Flow Integrity

Compiler có thể xây:

```text
CFI
```

từ:

```text
function type
call target set
indirect call analysis
```

và emit target-specific enforcement.

---

# 58. Indirect Call

Compiler có thể xác định:

```text
possible targets
```

nếu static.

Nếu dynamic:

```text
runtime check
```

có thể được thêm.

---

# 59. Memory Tagging

Nếu target hỗ trợ:

```text
MTE
CHERI-like capability
```

Axiom backend có thể tận dụng.

Không đưa hardware feature vào Core semantics.

---

# 60. Pointer Authentication

ARM PAC hoặc tương tự là backend security mechanism.

Source semantics vẫn:

```text
safe reference/capability
```

không phụ thuộc PAC.

---

# 61. CHERI-like Hardware

Nếu target có capability pointers:

```text
Axiom capability
```

có thể map xuống hardware capability.

Nếu target không có:

```text
software enforcement
```

hoặc compile-time proof.

---

# 62. FFI Security

Foreign pointer:

```text
*mut T
```

không tự trở thành safe capability.

Phải có explicit validation contract.

---

# 63. Unsafe Boundary

Một API:

```text
unsafe fn from_raw(...)
```

có thể establish:

```text
TrustedMemoryFact
```

nhưng security analyzer vẫn biết origin là unsafe.

---

# 64. Taint Tracking

Security analysis nên hỗ trợ:

```text
Tainted<T>
Trusted<T>
Sanitized<T>
```

như compiler metadata/analysis.

Không nhất thiết runtime wrapper.

---

# 65. Taint Sources

Ví dụ:

```text
network input
file input
environment
CLI
IPC
foreign API
```

có thể là taint source.

---

# 66. Taint Sinks

Ví dụ:

```text
SQL query
shell execution
HTML output
filesystem path
unsafe parser
cryptographic API
```

có thể yêu cầu sanitized input.

---

# 67. Taint Transform

Compiler/security analyzer theo dõi:

```text
RawInput
 ↓ sanitize
ValidatedInput
 ↓ normalize
CanonicalInput
```

---

# 68. Injection Security

Axiom không nên tạo “SQL type” Core.

Nhưng generic security metadata có thể hỗ trợ library analyzers:

```text
SqlQuery
ShellCommand
Html
Path
```

và compiler hiểu trust transitions.

---

# 69. Unicode Security

394 phải kết hợp text engine:

```text
normalization
confusable detection
canonicalization
```

khi security-sensitive identifiers được xử lý.

---

# 70. Serialization Security

391 codec phải có:

```text
max_size
max_depth
max_items
recursion_limit
```

để tránh malformed input gây tài nguyên vô hạn.

---

# 71. Resource Exhaustion

Security không chỉ là memory safety.

Phải xét:

```text
CPU
memory
file descriptors
threads
tasks
network connections
GPU memory
storage
```

---

# 72. Resource Budget

Sandbox có thể khai báo:

```text
Budget {
    max_memory
    max_tasks
    max_cpu
    max_io
    max_network
}
```

Runtime enforce khi dynamic.

---

# 73. Compiler-Provable Budget

Nếu compiler có thể chứng minh:

```text
allocation ≤ N
loop ≤ M
```

runtime check có thể được loại bỏ.

---

# 74. Denial of Service

Network server có thể áp dụng:

```text
rate_limit
connection_limit
message_limit
queue_limit
```

Đây là library/runtime policy.

---

# 75. Security Effects

Effect system mở rộng:

```text
SECRET_ACCESS
CREDENTIAL_ACCESS
TRUST_BOUNDARY
UNSAFE_MEMORY
FOREIGN_CALL
NETWORK_EXTERNAL
FILE_EXTERNAL
PROCESS_EXECUTION
DEVICE_ACCESS
```

Compiler có thể dùng để audit.

---

# 76. Security Labels

Compiler metadata có thể gắn:

```text
Public
Internal
Confidential
Secret
```

nhưng không nên hard-code một classification scheme.

Nó có thể là extensible metadata.

---

# 77. Information Flow

Security analyzer có thể kiểm tra:

```text
Secret
 ↓
PublicOutput
```

và reject nếu policy cấm.

---

# 78. Declassification

Nếu business logic cho phép:

```text
Secret
 ↓ authorized transformation
Public
```

phải có explicit declassification boundary.

---

# 79. Security Proof

Mỗi security-sensitive optimization có thể có:

```text
SecurityProof
```

ví dụ:

```text
ConstantTimeProof
SecretFlowProof
CapabilityProof
SandboxProof
TaintProof
IntegrityProof
```

---

# 80. Security + Optimization

Compiler **không được tối ưu chỉ dựa trên ordinary semantic equivalence** nếu security contract là observable.

Ví dụ:

```text
@constant_time
```

thì timing behavior trở thành một phần của contract.

---

# 81. Security + Parallelism

Secret computation có thể chạy parallel nếu:

```text
no secret-dependent leakage
```

và memory/race proofs vẫn hợp lệ.

---

# 82. Security + GPU

GPU kernel xử lý secret data cần contract:

```text
secret storage
execution isolation
side-channel policy
```

nếu application yêu cầu.

---

# 83. Security + Distributed

Remote service phải xác định:

```text
identity
authorization
encryption
integrity
capability delegation
```

trước khi compiler/runtime có thể coi boundary là trusted.

---

# 84. Security + Storage

Persistent secret data có thể yêu cầu:

```text
encrypted_at_rest
authenticated
zeroized_on_delete
restricted_mapping
```

tùy policy.

---

# 85. Secure Delete

Không nên giả định:

```text
delete(file)
```

đồng nghĩa bytes vật lý đã biến mất.

Nếu cần guarantee mạnh:

```text
SecureErase
```

phải là explicit storage contract.

---

# 86. Security + Debugger

Debugger không được mặc định expose:

```text
Secret<T>
```

nếu secret policy cấm.

Debug metadata có thể đánh dấu:

```text
redacted
opaque
no_dump
```

---

# 87. Security + Crash Dumps

Crash dump policy có thể loại:

```text
Secret
Credential
Key
```

khỏi dump.

---

# 88. Security + Logging

Compiler/tooling có thể cảnh báo:

```text
log(secret)
```

nếu type metadata cho biết đây là Secret.

---

# 89. Security + Serialization

`Secret<T>` không nên tự động implement generic serialization.

Export phải explicit.

---

# 90. CompilerDB

Bổ sung:

```text id="m9f5o6"
SecurityDB
SecurityPolicyDB
SecurityProfileDB
SecurityBoundaryDB
TrustDomainDB
TrustLevelDB

CapabilityDB
CapabilityTypeDB
CapabilityAuthorityDB
CapabilityScopeDB
CapabilityRightDB
CapabilityTransferDB
CapabilityRestrictionDB
CapabilityDelegationDB
CapabilityRevocationDB
CapabilityLeaseDB

SecurityIdentityDB
CredentialDB
AuthenticationDB
AuthorizationDB
PermissionDB
RoleDB
PolicyDB

SecretDB
SecretTypeDB
SecretFlowDB
SecretLifetimeDB
SecretStorageDB
SecretSerializationDB
SecretDebugDB
SecretDumpDB
ZeroizationDB

ConstantTimeDB
TimingAnalysisDB
SideChannelDB
SecretDependentBranchDB
SecretDependentMemoryDB
SecurityOptimizationDB

CryptoDB
CryptoAlgorithmDB
HashDB
MacDB
AeadDB
SignatureDB
KeyExchangeDB
KdfDB
NonceDB
KeyDB
KeyTypeDB
KeyStoreDB
SecureKeyHandleDB

SecureRandomDB
EntropyDB
CsprngDB

TaintDB
TaintSourceDB
TaintSinkDB
TaintTransformDB
SanitizationDB
CanonicalizationDB
ValidationDB

SandboxDB
SandboxPolicyDB
SandboxCapabilityDB
SandboxResourceDB
ResourceBudgetDB

InformationFlowDB
SecurityLabelDB
DeclassificationDB
InformationFlowProofDB

IntegrityDB
ArtifactIntegrityDB
CodeSigningDB
BuildProvenanceDB
SupplyChainDB
DependencyTrustDB

HardeningDB
StackProtectionDB
CfiDB
ShadowStackDB
AslrDB
NxDb
MemoryTaggingDB
PointerAuthenticationDB
HardwareCapabilityDB

SecurityAuditDB
SecurityDiagnosticDB
SecurityProofDB
SecurityVerificationDB
```

---

# 91. MIR

```text id="1uwl6x"
CAPABILITY_ACQUIRE
CAPABILITY_RESTRICT
CAPABILITY_DELEGATE
CAPABILITY_REVOKE
CAPABILITY_VALIDATE

TRUST_ENTER
TRUST_EXIT

SECURITY_CHECK
SECURITY_ASSERT

TAINT_SOURCE
TAINT_PROPAGATE
TAINT_SANITIZE
TAINT_SINK

SECRET_CREATE
SECRET_ACCESS
SECRET_ZEROIZE
SECRET_REDACT

SECURE_RANDOM
SECURE_KEY_CREATE
SECURE_KEY_USE
SECURE_KEY_EXPORT

CRYPTO_HASH
CRYPTO_MAC
CRYPTO_AEAD_ENCRYPT
CRYPTO_AEAD_DECRYPT
CRYPTO_SIGN
CRYPTO_VERIFY
CRYPTO_KDF
CRYPTO_KEY_EXCHANGE

CONSTANT_TIME_BEGIN
CONSTANT_TIME_END
SECRET_BRANCH_CHECK
SECRET_ADDRESS_CHECK

SANDBOX_ENTER
SANDBOX_EXIT
RESOURCE_BUDGET_CHECK

AUTHENTICATE
AUTHORIZE
DECLASSIFY

SECURE_ERASE

CFI_CHECK
STACK_PROTECT
CONTROL_FLOW_GUARD

SECURITY_FENCE
SECURITY_BARRIER
```

---

# 92. Proof System

```text id="g5ut66"
CapabilityProof
CapabilityAuthorityProof
CapabilityScopeProof
CapabilityTransferProof
CapabilityRevocationProof

TrustBoundaryProof
TrustDomainProof

InputValidationProof
CanonicalizationProof
TaintFlowProof
SanitizationProof

SecretFlowProof
SecretLifetimeProof
SecretStorageProof
SecretSerializationProof
SecretZeroizationProof
SecretDebugProof

ConstantTimeProof
TimingLeakProof
SecretBranchProof
SecretAddressProof

CryptographicTypeProof
KeyUsageProof
NonceUniquenessProof
CryptoParameterProof
CryptoIntegrityProof

AuthenticationProof
AuthorizationProof
IdentityProof

SandboxProof
ResourceBudgetProof

InformationFlowProof
DeclassificationProof

ArtifactIntegrityProof
CodeSigningProof
BuildProvenanceProof
DependencyTrustProof

HardeningProof
CfiProof
MemoryProtectionProof
HardwareCapabilityProof

SecurityOptimizationProof
SecurityVerificationProof
```

---

# 93. Invariants

### `ASEC-01`
Security-sensitive authority phải được biểu diễn bằng explicit capability hoặc equivalent contract.

### `ASEC-02`
Handle không mặc định mang authority.

### `ASEC-03`
Capability không được vượt lifetime của resource mà nó bảo vệ.

### `ASEC-04`
Capability restriction không được tạo thêm authority.

### `ASEC-05`
Capability delegation phải explicit.

### `ASEC-06`
Capability revocation phải có semantics xác định.

### `ASEC-07`
Unsafe code không tự động trở thành trusted code.

### `ASEC-08`
Foreign code là trust boundary nếu contract không chứng minh ngược lại.

### `ASEC-09`
Untrusted input không được tự động trở thành validated value.

### `ASEC-10`
Decode thành công không đồng nghĩa input đã được business validation.

### `ASEC-11`
Canonicalization phải xảy ra trước security-sensitive comparison khi policy yêu cầu.

### `ASEC-12`
Secret data không được implicit serialize/log/debug nếu policy cấm.

### `ASEC-13`
Secret zeroization không được bị optimizer loại bỏ khi security contract yêu cầu.

### `ASEC-14`
Constant-time contract phải được optimizer bảo toàn.

### `ASEC-15`
Secret-dependent branch/address access phải được security analyzer xử lý theo policy.

### `ASEC-16`
Cryptographic key types không được implicit interchangeable chỉ vì cùng representation.

### `ASEC-17`
Nonce uniqueness contract phải được bảo toàn.

### `ASEC-18`
CSPRNG không được thay thế bằng ordinary fast RNG khi security contract yêu cầu cryptographic randomness.

### `ASEC-19`
Authentication không đồng nghĩa authorization.

### `ASEC-20`
Authorization authority phải gắn với explicit identity/capability/policy.

### `ASEC-21`
Sandbox không được cấp authority ngoài capability set của nó.

### `ASEC-22`
Resource budget violation phải được xử lý theo declared policy.

### `ASEC-23`
Taint source không được tự động mất taint chỉ vì type conversion.

### `ASEC-24`
Sanitization phải là explicit transformation có contract.

### `ASEC-25`
Secret → Public flow phải được kiểm soát bởi information-flow policy.

### `ASEC-26`
Declassification phải là explicit security boundary.

### `ASEC-27`
Artifact integrity/provenance metadata phải được bảo toàn qua build/distribution pipeline khi policy yêu cầu.

### `ASEC-28`
Security hardening transformation không được phá vỡ ordinary language semantics.

### `ASEC-29`
Security-sensitive observable properties phải được xem là một phần semantic contract của optimizer.

### `ASEC-30`
Nếu chương trình không sử dụng security capability/crypto/sandbox subsystem, compiler không được kéo theo security runtime bắt buộc.

---

# 94. Điểm kiến trúc quan trọng của 394

Sau task này, Axiom có thể thống nhất một khái niệm rất mạnh:

```text
                 CAPABILITY
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
    Memory        Resource       Security
       │             │             │
    view<T>        File<T>       Secret<T>
    mut_view      Socket         Key<T>
    pointer       Device         Identity
```

Tức là **ownership/capability không chỉ giải quyết memory safety**.

Nó trở thành nền móng để xây:

```text
memory safety
resource safety
sandboxing
least authority
secure IPC
secure RPC
secret management
device access
distributed authorization
```

mà không cần đưa một “security runtime” khổng lồ vào mọi chương trình.

Và đây cũng rất phù hợp với triết lý Axiom:

> **Nếu compiler có thể chứng minh security property ở compile-time → không cần runtime check. Nếu không thể chứng minh → chỉ chèn đúng check cần thiết tại boundary.**