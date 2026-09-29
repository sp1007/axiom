Tiếp tục với **BOOTSTRAP-638 — Native Distributed Secrets, Key Rotation, Certificate Rotation, Identity Rotation, Trust Registry & Global Credential Lifecycle Runtime 5.0**.

:::writing{variant="document" id="74126" title="BOOTSTRAP-638 — Native Distributed Secrets, Key Rotation, Certificate Rotation, Identity Rotation, Trust Registry & Global Credential Lifecycle Runtime 5.0"}
# BOOTSTRAP-638
## Native Distributed Secrets, Key Rotation, Certificate Rotation, Identity Rotation, Trust Registry & Global Credential Lifecycle Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Trust & Credential Control Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-637  
**Primary dependencies:** 603, 610, 625, 628, 631, 633, 635, 636, 637

---

# 1. Mục tiêu

BOOTSTRAP-638 xây dựng lớp quản lý **credential lifecycle phân tán** của Axiom.

Nó quản lý vòng đời:

- secret;
- encryption key;
- signing key;
- certificate;
- certificate chain;
- service identity;
- workload identity;
- device identity;
- trust anchor;
- credential version;
- credential rotation;
- credential revocation;
- credential distribution;
- credential activation;
- credential retirement;
- credential recovery;
- trust registry.

Mục tiêu quan trọng:

> **Secret/key material không trở thành distributed configuration thông thường.**

637 quản lý:

```text
"ứng dụng nên làm gì?"
```

638 quản lý:

```text
"ứng dụng được phép chứng minh mình là ai bằng credential nào?"
```

---

# 2. Ranh giới với các hệ thống trước

| Hệ thống | Trách nhiệm |
|---|---|
| 603 | capability/security enforcement |
| 610 | cryptographic primitives, key providers, TLS |
| 627 | distributed identity/authentication/session |
| 637 | dynamic configuration/control |
| 638 | credential lifecycle/trust/rotation |
| 631 | service-to-service execution |
| 632 | edge authentication/TLS boundary |
| 635 | cluster control/leadership/fencing |
| 636 | deployment/release lifecycle |

638 **không thay thế 610**.

610 trả lời:

```text
How do we cryptographically operate on a key?
```

638 trả lời:

```text
Which key exists?
Which version is active?
Who owns it?
When should it rotate?
Where may it be used?
How is it distributed?
When is it retired?
```

---

# 3. Kiến trúc tổng thể

```text
                         ┌──────────────────────────┐
                         │      Axiom Application    │
                         └────────────┬─────────────┘
                                      │
                              Credential API
                                      │
              ┌───────────────────────▼──────────────────────┐
              │                  638 Runtime                  │
              ├──────────────────────────────────────────────┤
              │ Secret Lifecycle                              │
              │ Key Lifecycle                                 │
              │ Certificate Lifecycle                         │
              │ Identity Lifecycle                            │
              │ Trust Registry                                │
              │ Rotation Controller                           │
              │ Revocation Controller                         │
              │ Credential Distribution                       │
              ├──────────────────────────────────────────────┤
              │ Version / Lease / Epoch / Fencing             │
              └───────────────┬──────────────────────────────┘
                              │
        ┌─────────────┬───────┼────────┬─────────────┬─────────┐
        ▼             ▼       ▼        ▼             ▼         ▼
       603           610     627      628           635       637
    Security       Crypto   Identity  Storage      Control    Dynamic
```

---

# 4. Core principles

638 phải tuân thủ:

1. Secret material không phải config.
2. Private key không được xuất plaintext nếu provider không cho phép.
3. Key identity khác key material.
4. Credential version immutable.
5. Rotation tạo version mới.
6. Không overwrite credential đang active.
7. Revocation không xóa lịch sử.
8. Expiry phải deterministic.
9. Stale credential phải bị fencing khi policy yêu cầu.
10. Control plane không được yêu cầu private key phải rời hardware-backed provider nếu không cần.
11. Credential distribution phải least-privilege.
12. Credential scope phải explicit.
13. Credential usage phải audit được.
14. Rotation phải hỗ trợ overlap/grace period.
15. Certificate rotation phải hỗ trợ zero-downtime.
16. Trust anchor thay đổi phải có rollout strategy.
17. Emergency revocation phải nhanh hơn normal rotation.
18. Không có hidden backdoor.
19. Không có implicit credential sharing.
20. Không yêu cầu GC.

---

# 5. Credential model

Core object:

```text
Credential {
    credential_id
    credential_type
    owner
    scope
    version
    state
    provider
    created_at
    not_before
    expires_at
    policy
}
```

`Credential` là metadata handle.

Nó không đồng nghĩa với secret material.

---

# 6. Credential types

```text
Secret
SymmetricKey
SigningKey
EncryptionKey
KeyEncryptionKey
Certificate
CertificateChain
TrustAnchor
ServiceIdentity
WorkloadIdentity
DeviceIdentity
TokenSigningKey
SessionKey
AttestationCredential
```

---

# 7. Credential states

```text
Pending
Provisioning
Staged
Active
Grace
Expiring
Expired
Revoked
Suspended
Retired
Destroyed
Failed
```

Transitions phải được kiểm soát.

Ví dụ:

```text
Staged
   ↓
Active
   ↓
Grace
   ↓
Retired
   ↓
Destroyed
```

---

# 8. Credential identity

Mỗi credential có:

```text
CredentialId
CredentialGeneration
CredentialVersion
```

Ví dụ:

```text
credential = database-key
generation = 42
version = 3
```

Không dùng raw secret làm identity.

---

# 9. Secret

Secret được biểu diễn:

```text
SecretRef<T>
```

hoặc:

```text
SecretHandle<T>
```

Ứng dụng không nhận raw bytes nếu provider có khả năng giữ secret opaque.

---

# 10. Secret retrieval

API ưu tiên:

```text
secret.resolve()
```

trả opaque object.

Ví dụ:

```text
Secret<DatabasePassword>
```

Không khuyến khích:

```text
String password
```

---

# 11. Secret lifetime

Secret material có lifetime tối thiểu cần thiết.

Ví dụ:

```text
with_secret(secret) {
    connect()
}
```

Sau scope:

```text
material_release
```

Nếu platform/provider hỗ trợ zeroization thì thực hiện.

---

# 12. Zeroization

638 yêu cầu best-effort zeroization.

Nhưng specification phải ghi rõ:

> Zeroization của memory không được đảm bảo tuyệt đối trên mọi OS/hardware/compiler.

Provider phải khai báo:

```text
zeroization_guarantee
```

---

# 13. Hardware-backed keys

638 hỗ trợ provider:

```text
NativeProvider
PlatformProvider
HardwareProvider
TPMProvider
SecureEnclaveProvider
AndroidKeystoreProvider
HSMProvider
TestProvider
```

Private key có thể:

```text
non_exportable = true
```

---

# 14. Non-exportable key

Nếu:

```text
KeyPolicy.export = Deny
```

thì:

```text
export_private_key()
```

phải fail.

Nhưng:

```text
sign(data)
decrypt(data)
derive(...)
```

vẫn có thể hoạt động thông qua provider.

---

# 15. Key metadata

```text
KeyRecord {
    key_id
    version
    algorithm
    purpose
    provider
    export_policy
    owner
    scope
    created_at
    activation_time
    expiration_time
    state
}
```

---

# 16. Key purposes

Explicit:

```text
Sign
Verify
Encrypt
Decrypt
Wrap
Unwrap
Derive
Authenticate
TLS
TokenSigning
StorageEncryption
DataEncryption
```

Một key không tự động được dùng cho mục đích khác.

---

# 17. Algorithm policy

Mỗi key phải có:

```text
algorithm
parameters
security_policy
```

Ví dụ:

```text
Ed25519
ECDSA
RSA
AES-GCM
ChaCha20-Poly1305
```

Danh sách thực tế phụ thuộc 610/provider/platform.

---

# 18. Cryptographic agility

638 không hard-code một algorithm duy nhất.

Credential metadata chứa:

```text
algorithm_id
algorithm_version
parameters
```

Rotation có thể đổi algorithm:

```text
old = algorithm A
new = algorithm B
```

nếu policy cho phép.

---

# 19. Key versioning

Không:

```text
overwrite(key)
```

Mà:

```text
key v1
key v2
key v3
```

---

# 20. Active key

Một scope có thể khai báo:

```text
active_key_version
```

Ví dụ:

```text
database-encryption
    v7 = active
    v6 = grace
    v5 = retired
```

---

# 21. Rotation

Rotation:

```text
Prepare
Generate
Validate
Stage
Distribute
Activate
Overlap
Retire
Destroy
```

---

# 22. Rotation state machine

```text
Planned
↓
Preparing
↓
Generated
↓
Validated
↓
Staged
↓
Distributing
↓
Activated
↓
Grace
↓
Retiring
↓
Retired
↓
Destroyed
```

Failure:

```text
Failed
```

có thể retry tùy policy.

---

# 23. Rotation policy

```text
RotationPolicy {
    max_age
    max_uses
    max_exposure
    rotate_before_expiry
    grace_period
    distribution_timeout
    activation_strategy
    rollback_strategy
}
```

Không phải credential nào cũng rotate theo thời gian.

---

# 24. Event-triggered rotation

Có thể rotate khi:

```text
credential_compromise
provider_change
algorithm_deprecation
operator_request
deployment
identity_change
cluster_change
policy_change
```

---

# 25. Rotation jitter

Để tránh:

```text
100,000 services
→ rotate cùng lúc
```

638 hỗ trợ deterministic jitter:

```text
rotation_time =
scheduled_time + stable_jitter(credential_id)
```

Không dùng random runtime nếu cần reproducibility.

---

# 26. Rotation storm protection

Controller giới hạn:

```text
max_parallel_rotations
max_rotations_per_scope
max_provider_requests
```

Tích hợp 606.

---

# 27. Zero-downtime rotation

TLS/key rotation có thể dùng overlap:

```text
old credential = accepted
new credential = accepted
```

sau đó:

```text
old = retired
```

---

# 28. Dual-key period

Trong grace period:

```text
verify(old)
verify(new)
```

nhưng sign/encrypt mới ưu tiên:

```text
new
```

---

# 29. Encryption key rotation

Đối với data encryption:

```text
KEK rotation
```

không nhất thiết yêu cầu re-encrypt toàn bộ dữ liệu ngay lập tức.

Hỗ trợ envelope encryption:

```text
Data
 ↓
DEK
 ↓
KEK
```

Rotation KEK:

```text
re-wrap DEK
```

nếu provider hỗ trợ.

---

# 30. Lazy re-encryption

Có thể:

```text
old data
   ↓
read
   ↓
decrypt old DEK
   ↓
rewrite with new DEK
```

Nhưng đây là policy của storage layer, không tự động thực hiện bởi 638.

---

# 31. Certificate model

```text
CertificateRecord {
    certificate_id
    version
    subject
    issuer
    public_key
    serial
    not_before
    not_after
    chain
    usage
    state
}
```

---

# 32. Certificate issuance

Provider boundary:

```text
SelfSigned
InternalCA
ExternalCA
ACMEProvider
EnterpriseCA
TestCA
```

638 không bắt buộc một CA cụ thể.

---

# 33. Certificate request

```text
CertificateRequest {
    identity
    subject
    SANs
    key_algorithm
    usages
    validity
    issuer_policy
}
```

---

# 34. SAN

Certificate identity phải ưu tiên SAN.

Ví dụ:

```text
DNS:orders.internal
URI:spiffe://axiom/service/orders
```

nếu provider hỗ trợ.

---

# 35. Certificate rotation

Policy:

```text
renew_before = 30d
grace = 24h
```

Flow:

```text
new key
↓
new CSR
↓
certificate issuance
↓
validation
↓
distribution
↓
activation
↓
old certificate grace
↓
retirement
```

---

# 36. Certificate validation

Phải kiểm tra:

```text
signature
chain
hostname/SAN
validity
key usage
extended key usage
algorithm policy
trust anchor
revocation policy
```

610 là cryptographic validation provider.

---

# 37. Trust Registry

638 cung cấp:

```text
TrustRegistry
```

chứa metadata:

```text
TrustAnchor
CA
Publisher
IdentityIssuer
KeyIssuer
CertificateAuthority
```

---

# 38. TrustAnchor

```text
TrustAnchor {
    anchor_id
    public_key
    subject
    fingerprint
    issuer
    validity
    state
}
```

Private key không nằm trong trust registry.

---

# 39. Trust states

```text
Pending
Trusted
Deprecated
Blocked
Revoked
Retired
```

---

# 40. Trust-anchor rotation

Để tránh outage:

```text
old root trusted
new root trusted
```

sau đó rollout:

```text
new-issued certificates
```

sau khi toàn bộ consumers hiểu root mới:

```text
old root deprecated
```

---

# 41. Cross-signing

Provider có thể hỗ trợ:

```text
cross-signed certificates
```

nhưng không bắt buộc.

638 chỉ định nghĩa lifecycle semantics.

---

# 42. Trust bundle

Application nhận:

```text
TrustBundle {
    revision
    anchors
    intermediates
    policies
    expires_at
}
```

Bundle immutable.

---

# 43. Trust bundle activation

```text
validate
↓
stage
↓
verify chain
↓
activate
```

Nếu bundle invalid:

```text
active bundle unchanged
```

---

# 44. Identity model

638 hỗ trợ identity lifecycle:

```text
IdentityId
IdentityGeneration
IdentityVersion
IdentityType
IdentityScope
```

Types:

```text
Service
Workload
Device
Node
Application
Publisher
Tenant
```

---

# 45. Service identity

Ví dụ:

```text
spiffe://axiom/service/orders
```

hoặc provider-specific identity.

Identity không đồng nghĩa credential.

```text
Identity
   ├── certificate v1
   ├── certificate v2
   └── token key v7
```

---

# 46. Identity generation

Khi identity lifecycle thay đổi:

```text
generation++
```

Credential cũ có thể bị fencing.

Ví dụ:

```text
orders generation 8
```

credential của generation 7:

```text
reject
```

nếu policy yêu cầu.

---

# 47. Workload identity

Workload identity có thể bind:

```text
service
deployment
cluster
namespace
instance
```

Không bind vĩnh viễn vào process PID.

---

# 48. Deployment integration

636 có:

```text
release
revision
```

638 có thể cấp:

```text
credential generation
```

Deployment mới có thể yêu cầu:

```text
new identity generation
```

nhưng deployment không tự sở hữu credential authority.

---

# 49. Service discovery integration

631 endpoint metadata có thể tham chiếu:

```text
identity_id
certificate_profile
trust_domain
```

631 thực hiện routing.

638 cung cấp credential/trust lifecycle.

---

# 50. Gateway integration

632 sử dụng:

```text
certificate profile
trust bundle
TLS credential
client authentication policy
```

638 quản lý rotation.

---

# 51. mTLS

mTLS flow:

```text
638 identity
    ↓
certificate
    ↓
610 TLS
    ↓
632 / 631
```

638 không tự implement TLS handshake.

---

# 52. Token signing keys

Identity service có thể sử dụng:

```text
TokenSigningKey
```

Rotation:

```text
old signing key = verify
new signing key = sign + verify
```

Sau grace:

```text
old = revoke
```

---

# 53. JWKS-like publication

Provider có thể publish public verification keys:

```text
VerificationKeySet {
    revision
    keys
    expires_at
}
```

Private signing keys không publish.

---

# 54. Verification overlap

Trong rotation:

```text
sign(new)
verify(old,new)
```

Sau propagation:

```text
sign(new)
verify(new)
```

---

# 55. Credential leases

Temporary credential:

```text
CredentialLease {
    credential_id
    issued_at
    expires_at
    renewal
    scope
}
```

---

# 56. Lease renewal

Renewal phải kiểm tra:

```text
identity still valid
policy still valid
authority still valid
credential not revoked
```

---

# 57. Short-lived credentials

638 ưu tiên short-lived credential khi phù hợp:

```text
minutes
hours
days
```

thay vì credential vĩnh viễn.

Nhưng lifetime do policy quyết định.

---

# 58. Revocation

Revocation object:

```text
RevocationRecord {
    credential_id
    version
    reason
    issued_at
    effective_at
    issuer
}
```

Reasons:

```text
Compromised
Expired
Superseded
Unauthorized
IdentityRevoked
PolicyViolation
OperatorAction
ProviderFailure
```

---

# 59. Emergency revocation

Emergency revoke phải có fast path:

```text
revoke
↓
publish
↓
propagate
↓
enforce
```

không chờ normal rotation schedule.

---

# 60. Revocation semantics

Không phải mọi protocol đều hỗ trợ instantaneous revocation.

638 phải biểu diễn:

```text
revocation_propagation_bound
```

Ví dụ:

```text
expected < 60s
```

Không tuyên bố instant revocation nếu provider không thể đảm bảo.

---

# 61. CRL/OCSP boundary

Certificate provider có thể sử dụng:

```text
CRL
OCSP
OCSP stapling
provider-native revocation
```

638 chỉ chuẩn hóa policy/lifecycle.

---

# 62. Credential distribution

Distribution targets:

```text
Process
Service
Cluster
Node
Gateway
Device
Edge
HSM
```

---

# 63. Distribution modes

```text
Pull
Push
Hybrid
ProviderLocal
```

Ưu tiên:

```text
Pull + local cache
```

đối với scale lớn.

---

# 64. Push safety

Push không được gửi raw secret tới recipient không có capability.

Authorization được kiểm tra tại distribution boundary.

---

# 65. Credential projection

Consumer nhận:

```text
CredentialProjection
```

chỉ chứa phần cần thiết.

Ví dụ TLS server:

```text
certificate
private-key-handle
trust-bundle
```

Private key có thể vẫn nằm trong provider.

---

# 66. Provider-local private keys

Preferred architecture:

```text
638
 │
 └── metadata
       │
       └── 610 HardwareProvider
                │
                └── private key
```

thay vì:

```text
638
 └── plaintext private key database
```

---

# 67. Secret storage

Nếu secret cần persistent storage:

```text
encrypted envelope
```

với key từ 610.

Storage:

```text
611/612/628
```

---

# 68. Envelope encryption

```text
Secret
  ↓
DEK
  ↓
KEK
  ↓
Hardware/Platform root
```

637/638 metadata không chứa raw plaintext.

---

# 69. Backup

Backup có thể chứa:

```text
encrypted credential blob
metadata
revision
```

nhưng không được chứa plaintext secret nếu policy không cho phép.

---

# 70. Recovery

Recovery phải có:

```text
backup
key availability
trust verification
identity validation
```

Nếu root key mất:

```text
recovery may be impossible
```

Đây là trạng thái phải được explicit trong disaster-recovery design.

---

# 71. Credential escrow

Enterprise/provider có thể hỗ trợ escrow:

```text
EscrowPolicy
```

nhưng core không yêu cầu.

---

# 72. Multi-party recovery

Critical keys có thể yêu cầu:

```text
N-of-M authorization
```

đây là provider/policy boundary.

---

# 73. Credential policy

```text
CredentialPolicy {
    allowed_algorithms
    allowed_purposes
    export_policy
    max_lifetime
    rotation_policy
    revocation_policy
    distribution_scope
    audit_level
}
```

---

# 74. Scope

Credential scope:

```text
global
federation
cluster
region
service
workload
device
tenant
```

Scope narrowing được phép.

Scope widening không được tự động.

---

# 75. Capability integration

603 kiểm soát:

```text
credential.read
credential.issue
credential.rotate
credential.revoke
credential.export
trust.read
trust.modify
identity.read
identity.rotate
```

---

# 76. Export restrictions

Capability:

```text
credential.export
```

phải explicit.

Default:

```text
Deny
```

---

# 77. Identity delegation

Service có thể delegate limited identity capability:

```text
IdentityDelegation {
    issuer
    subject
    scope
    expiry
    generation
}
```

Không được delegate quyền rộng hơn issuer.

---

# 78. Delegation chain

Mỗi delegation có:

```text
parent
depth
scope
expiry
```

Maximum depth:

```text
max_delegation_depth
```

để tránh chain không giới hạn.

---

# 79. Federation trust

Federated cluster:

```text
Cluster A
   ↕
Trust relationship
   ↕
Cluster B
```

Trust relationship có:

```text
TrustId
Epoch
Scope
Expiry
Policy
```

---

# 80. Federation trust rotation

Trust anchor thay đổi:

```text
prepare
↓
establish new trust
↓
verify
↓
switch
↓
grace
↓
retire old
```

---

# 81. Split-brain protection

Credential issuance authority phải gắn với:

```text
control epoch
```

Old leader:

```text
epoch < current
```

không được issue credential.

---

# 82. Fencing token

Credential issuer có:

```text
IssuerEpoch
FencingToken
```

Provider từ chối stale issuer.

---

# 83. Issuance idempotency

Request:

```text
issue(request_id)
```

phải idempotent.

Nếu retry:

```text
same request_id
```

không tạo credential vô hạn.

---

# 84. Rotation idempotency

Rotation:

```text
rotation_id
```

đảm bảo retry không tạo nhiều active generations ngoài policy.

---

# 85. Credential activation transaction

Activation:

```text
prepare
validate
stage
activate
publish
```

Nếu activation thất bại:

```text
old active credential remains active
```

nếu policy cho phép.

---

# 86. Partial distribution

Nếu:

```text
10,000 instances
```

mà:

```text
9,800 updated
200 unavailable
```

638 biểu diễn:

```text
DistributionStatus {
    updated
    pending
    failed
    expired
}
```

Không giả vờ rollout hoàn tất.

---

# 87. Rotation gates

Rotation có thể yêu cầu:

```text
minimum_ready
maximum_failure
health_signal
```

633 cung cấp health.

---

# 88. Rotation rollout

Strategy:

```text
AllAtOnce
Rolling
Canary
Wave
RegionFirst
ClusterFirst
ProviderFirst
```

---

# 89. Canary credential rotation

Ví dụ:

```text
1 cluster
→ validate
→ 10%
→ 50%
→ 100%
```

---

# 90. Rollback credential

Credential rollback không phải luôn là:

```text
restore old key
```

Nếu key bị compromise:

```text
rollback forbidden
```

Policy phải quyết định.

---

# 91. Compromise state

Credential có:

```text
Compromised
```

Một credential compromised không được quay lại active.

---

# 92. Trust compromise

Nếu CA/root compromised:

```text
trust incident
```

có thể yêu cầu:

```text
new root
new intermediates
new leaf certificates
new identities
```

638 phải hỗ trợ orchestration hooks.

---

# 93. Certificate expiry prevention

Controller phải tính:

```text
renew_before
issuance_latency
distribution_latency
grace_period
```

để tránh rotation bắt đầu quá muộn.

---

# 94. Clock uncertainty

Expiry policy phải xét:

```text
clock_skew_budget
```

không dựa tuyệt đối vào local clock.

---

# 95. Monotonic scheduling

Control-plane ordering dựa trên:

```text
revision
epoch
sequence
```

Timestamp chỉ hỗ trợ scheduling.

---

# 96. Trust registry revisions

Trust bundle:

```text
revision 100
revision 101
revision 102
```

Consumer có thể yêu cầu:

```text
minimum_revision
```

---

# 97. Trust bundle caching

Local cache:

```text
active bundle
previous bundle
next bundle
```

giúp zero-downtime rotation.

---

# 98. Certificate chain caching

Cache:

```text
leaf
intermediate
root metadata
```

có TTL và revision.

---

# 99. Credential cache

Cache không được biến thành authority.

Nếu credential revoked:

```text
cache must honor revocation policy
```

---

# 100. Revocation propagation

Event:

```text
CredentialRevoked
```

được phát qua 634.

Consumer cập nhật cache.

---

# 101. Event payload

Không gửi:

```text
private_key
secret_plaintext
```

Event chỉ chứa:

```text
credential_id
version
state
reason
revision
```

---

# 102. Audit

638 phát audit:

```text
CredentialCreated
CredentialActivated
CredentialRotated
CredentialRevoked
CredentialExpired
CredentialDestroyed
CertificateIssued
CertificateRenewed
TrustAnchorAdded
TrustAnchorRevoked
IdentityCreated
IdentityRotated
IdentityRevoked
```

---

# 103. Audit integrity

Audit metadata có thể được hash-chain:

```text
event_n.hash
→ event_n+1.previous_hash
```

nếu provider yêu cầu tamper-evident audit.

---

# 104. Diagnostics

602/633 nhận:

```text
rotation_duration
rotation_failures
credential_age
credential_expiry_window
revocation_lag
trust_bundle_age
provider_latency
issuance_rate
distribution_lag
```

---

# 105. Security telemetry

Không log:

```text
secret bytes
private key bytes
seed
password
token plaintext
```

---

# 106. Resource governance

606 giới hạn:

```text
credential issuance rate
provider calls
rotation concurrency
watchers
cache size
distribution bandwidth
```

---

# 107. Provider throttling

Nếu CA/HSM rate-limit:

```text
provider throttling
```

638 phải:

```text
queue
backoff
jitter
prioritize expiry
```

---

# 108. Priority

Credential lifecycle priority:

```text
EmergencyRevocation
ExpiryPrevention
SecurityRotation
NormalRotation
BackgroundRefresh
Prefetch
```

---

# 109. Expiry emergency

Nếu certificate còn:

```text
5 minutes
```

controller phải ưu tiên hơn background rotation.

---

# 110. Thundering herd prevention

Credential refresh phải có:

```text
stable jitter
single-flight
local deduplication
provider rate limit
```

---

# 111. Single-flight

Nếu 100 local consumers yêu cầu cùng credential:

```text
100 requests
```

không nhất thiết thành:

```text
100 provider calls
```

Runtime có thể collapse thành:

```text
1 provider operation
100 consumers
```

---

# 112. Secret access telemetry

Có thể đếm:

```text
secret_access_total
```

nhưng không ghi secret.

---

# 113. Access anomaly hooks

638 có thể emit:

```text
unexpected_access_pattern
```

nhưng không tự suy đoán malicious intent.

Detection engine có thể nằm ngoài core.

---

# 114. Identity lifecycle

```text
Requested
↓
Provisioning
↓
Active
↓
Suspended
↓
Rotating
↓
Retired
↓
Revoked
```

---

# 115. Identity suspension

Suspension khác revocation.

```text
Suspended
```

có thể phục hồi.

```text
Revoked
```

không tự động phục hồi.

---

# 116. Device identity

Embedded/mobile/device có:

```text
DeviceIdentity
```

có thể bind:

```text
hardware attestation
device key
device certificate
```

---

# 117. Attestation

Provider boundary:

```text
TPM
Secure Enclave
Android hardware-backed keystore
platform attestation
```

638 lưu attestation metadata, không cần tự implement hardware protocol.

---

# 118. Attestation policy

Identity activation có thể yêu cầu:

```text
attestation_required = true
```

Provider phải xác minh.

---

# 119. Publisher identity

Package 625 có:

```text
PublisherId
PublisherKey
```

638 có thể quản lý publisher credential lifecycle.

---

# 120. Package trust integration

625 package verification:

```text
package signature
    ↓
638 trust registry
    ↓
610 cryptographic verification
```

---

# 121. Package key rotation

Publisher có thể publish:

```text
old signing key
new signing key
```

với overlap.

Consumers cần trust both trong transition.

---

# 122. Key compromise response

Nếu publisher key compromised:

```text
revoke old
publish new
block affected packages
```

625 thực thi package policy.

638 quản lý credential/trust lifecycle.

---

# 123. Trust domains

```text
TrustDomain {
    domain_id
    roots
    issuers
    policies
    revision
}
```

Ví dụ:

```text
prod.internal
edge.internal
development
```

---

# 124. Cross-domain trust

Explicit:

```text
TrustRelationship {
    source_domain
    target_domain
    allowed_identities
    allowed_purposes
    expiry
}
```

Không mặc định full trust.

---

# 125. Trust narrowing

A service có thể trust:

```text
domain A
```

nhưng chỉ cho:

```text
service.orders
```

không phải mọi identity của A.

---

# 126. Identity mapping

Cross-domain mapping:

```text
IdentityMapping {
    source_identity
    target_identity
    scope
    expiry
}
```

---

# 127. No implicit transitive trust

Nếu:

```text
A trusts B
B trusts C
```

thì không suy ra:

```text
A trusts C
```

---

# 128. Credential discovery

API:

```text
credentials.find(identity)
```

nhưng kết quả chỉ trả metadata/capability-safe references.

---

# 129. Credential binding

Application có thể bind:

```text
TlsIdentity
SigningIdentity
EncryptionIdentity
```

vào runtime object.

---

# 130. Automatic refresh

Bound credential có thể tự refresh:

```text
credential.bind()
```

nhưng refresh không được block hot path.

---

# 131. Refresh callback

```text
on_refresh(old, new)
```

callback phải chạy ngoài credential lock.

---

# 132. Atomic credential swap

Runtime:

```text
old credential
       │
       ▼
atomic swap
       │
       ▼
new credential
```

Existing operations có thể tiếp tục dùng old credential trong grace period.

---

# 133. TLS zero-downtime

TLS listener:

```text
certificate v1
certificate v2
```

có thể coexist.

New connections:

```text
v2
```

Existing connections:

```text
v1
```

cho đến khi policy cho phép close.

---

# 134. Connection drain

632/631 có thể drain:

```text
old identity connections
```

638 chỉ cung cấp lifecycle signal.

---

# 135. Key rotation for long-lived connections

Nếu protocol yêu cầu rekey:

```text
rekey signal
```

được phát.

Protocol layer quyết định thực thi.

---

# 136. Token rotation

Token credential có:

```text
issuer
audience
key_version
expiry
```

New tokens dùng key mới.

Old tokens được verify trong grace nếu policy cho phép.

---

# 137. Token revocation

Short-lived token ưu tiên expiry.

Nếu emergency:

```text
revocation source
```

được propagate.

---

# 138. Session integration

627 session runtime nhận:

```text
credential_generation
identity_generation
trust_revision
```

để phát hiện stale credentials.

---

# 139. Control-plane metadata

638 dùng 637 cho:

```text
rotation policy
expiry thresholds
rollout parameters
```

Nhưng:

```text
credential material != 637 config
```

---

# 140. Dynamic rotation policy

637 có thể chứa:

```text
tls.renew_before = 30d
```

638 thực thi.

Nếu 637 unavailable:

```text
static policy
```

được sử dụng.

---

# 141. Policy safety

Dynamic policy không được làm:

```text
max_lifetime = infinite
```

nếu 638 policy cấm.

Security upper bound nằm tại 638/603.

---

# 142. Security invariant

Dynamic config có thể:

```text
tighten
```

policy nhưng không được:

```text
weaken security beyond authority
```

---

# 143. Maximum-bound model

Ví dụ:

```text
637 requested TTL = 30 days
638 policy max TTL = 7 days
```

effective:

```text
7 days
```

---

# 144. Minimum-security model

Một config không thể:

```text
disable certificate validation
```

nếu 610/603 policy yêu cầu validation.

---

# 145. Credential generation metadata

Mọi credential event có:

```text
credential_id
version
generation
issuer_epoch
revision
```

---

# 146. Reconciliation

Controller loop:

```text
observe
↓
compare desired vs active
↓
validate
↓
prepare
↓
activate
↓
verify
```

---

# 147. Desired state

```text
CredentialDesiredState {
    identity
    credential_profile
    target
    version_policy
    rotation_policy
    trust_policy
}
```

---

# 148. Observed state

```text
CredentialObservedState {
    active_version
    provider_state
    distribution_state
    expiry
    revocation_state
}
```

---

# 149. Drift

States:

```text
Converged
Preparing
Rotating
PartiallyDistributed
Drifted
Expired
Revoked
Blocked
```

---

# 150. No infinite reconciliation

Controller phải detect:

```text
same failure
same revision
same target
```

và backoff.

---

# 151. Rotation history

History phải giữ:

```text
previous version
new version
reason
actor
provider
activation
distribution
retirement
```

---

# 152. Forensics

Security incident có thể truy vấn:

```text
which credential was active at time T?
```

Kết quả phải dựa trên:

```text
revision
generation
activation interval
```

---

# 153. Historical verification

API:

```text
credential.active_at(identity, timestamp)
```

trả credential metadata.

Không trả secret material nếu caller không có capability.

---

# 154. Reproducible security state

Crash dump/diagnostic snapshot nên ghi:

```text
identity_generation
credential_version
trust_revision
policy_revision
```

nhưng không ghi secret.

---

# 155. Compiler integration

Annotations:

```text
@credential
@secret
@key
@certificate
@identity
@trust
@rotate
@revocable
@non_exportable
@credential_scope
@credential_policy
@trust_domain
```

---

# 156. Example

```text
@identity("orders")
identity OrdersIdentity
```

Compiler sinh:

```text
IdentityRef<OrdersIdentity>
```

---

# 157. Key example

```text
@key(
    purpose = Sign,
    non_exportable = true
)
let signing_key: SigningKeyRef
```

---

# 158. Certificate example

```text
@certificate(
    identity = OrdersIdentity,
    rotate_before = 30d
)
let tls_certificate: CertificateRef
```

---

# 159. Secret example

```text
@secret("database/password")
let db_password: SecretRef<DatabasePassword>
```

---

# 160. Trust example

```text
@trust_domain("prod.internal")
let production_trust: TrustDomainRef
```

---

# 161. Generated metadata

Compiler sinh:

```text
.axcredential
.axidentity
.axtrust
.axrotation
.axcert
```

Metadata:

```text
type
purpose
scope
provider
algorithm
rotation policy
capabilities
expiry
```

Không chứa private key material.

---

# 162. CLI

```text
axiom credential list
axiom credential inspect
axiom credential rotate
axiom credential revoke
axiom credential history
axiom credential explain

axiom identity list
axiom identity inspect
axiom identity rotate
axiom identity revoke

axiom certificate list
axiom certificate renew
axiom certificate inspect

axiom trust list
axiom trust inspect
axiom trust rotate
axiom trust revoke

axiom key list
axiom key rotate
axiom key inspect
```

---

# 163. Dry run

```text
axiom credential rotate --plan
```

phải cho biết:

```text
targets
provider
new version
affected services
distribution waves
grace period
rollback constraints
health gates
```

---

# 164. Explain

```text
axiom credential explain orders-tls
```

Output:

```text
identity
active certificate
key provider
trust domain
rotation policy
expiry
distribution state
```

Không hiển thị private key.

---

# 165. Rotation simulator

Input:

```text
credential
targets
rotation policy
failure model
```

Output:

```text
activation waves
expected overlap
failure paths
rollback possibilities
```

---

# 166. Testing architecture

Required providers:

```text
FakeKeyProvider
FakeCertificateAuthority
FakeTrustProvider
FakeIdentityProvider
FakeClock
FakeDistributionProvider
FakeRevocationProvider
```

---

# 167. Deterministic test scenarios

Phải kiểm tra:

```text
expiry
rotation
revocation
leader failover
provider failure
partial rollout
network partition
stale issuer
certificate chain failure
trust-anchor replacement
```

---

# 168. Security fuzzing

Fuzz:

```text
certificate parser
trust bundle
credential metadata
policy
rotation plan
delegation chain
identity mapping
revocation record
```

---

# 169. Cryptographic testing

Known-answer tests thuộc 610.

638 test:

```text
correct provider selection
correct key purpose
correct lifecycle
correct rotation
correct revocation
```

---

# 170. Provider conformance

Provider phải pass:

```text
create
activate
sign
verify
rotate
revoke
destroy
```

tùy credential type.

---

# 171. Hardware provider conformance

Kiểm tra:

```text
non-exportability
provider failure
device loss
reconnect
key persistence
```

---

# 172. Device loss

Nếu HSM/TPM/Secure Enclave unavailable:

```text
ProviderUnavailable
```

Không tự export software key nếu policy cấm.

---

# 173. Failover provider

Policy có thể cho:

```text
HardwareProvider A
↓
HardwareProvider B
```

nhưng chỉ nếu trust policy cho phép.

---

# 174. Software fallback

Software fallback mặc định:

```text
Deny
```

cho key yêu cầu hardware backing.

---

# 175. Credential classification

```text
Public
Internal
Confidential
Secret
HighlySensitive
HardwareBound
```

Classification ảnh hưởng distribution policy.

---

# 176. Secret sharing

Secret chỉ có thể share qua:

```text
explicit capability
explicit scope
explicit recipient
```

Không implicit global visibility.

---

# 177. Tenant credentials

Tenant credential namespace:

```text
tenant/<tenant_id>/...
```

Tenant A không thể resolve Tenant B.

---

# 178. Service credentials

Service credential namespace:

```text
service/<service_id>/...
```

Instance-specific credential:

```text
service/<service_id>/<generation>/<instance>
```

---

# 179. Cluster credentials

Cluster credentials phải có:

```text
cluster_id
cluster_generation
```

Stale cluster generation bị fencing.

---

# 180. Edge credentials

Edge credentials:

```text
edge_group
device_id
delegation_epoch
expiry
```

---

# 181. Device credential revocation

Device lost:

```text
device generation revoked
```

Tất cả credential thuộc generation đó có thể bị invalidated theo policy.

---

# 182. Publisher revocation

Publisher credential revoked:

```text
new packages from publisher
```

có thể bị block bởi 625.

Existing installed packages cần policy riêng.

---

# 183. Trust registry query

```text
trust.resolve(identity)
trust.verify(identity, credential)
```

Verification có thể trả:

```text
Trusted
Untrusted
Expired
Revoked
Unknown
PolicyDenied
```

---

# 184. No binary trust shortcut

Không:

```text
if publisher == "trusted" then accept
```

Trust phải dựa trên:

```text
credential
chain
policy
scope
validity
revocation
```

---

# 185. Credential state consistency

Không được:

```text
metadata says Revoked
provider still treats Active
```

mà không phát hiện drift.

Controller phải reconcile.

---

# 186. Provider state verification

Sau activation:

```text
activate
↓
read-back verification
↓
confirm
```

Nếu provider không confirm:

```text
activation uncertain
```

không báo success giả.

---

# 187. Two-phase credential activation

Có thể dùng:

```text
Prepare
Commit
```

để tránh active credential chưa phân phối.

---

# 188. Distributed activation

Nếu cần multi-cluster:

```text
prepare all
↓
minimum readiness
↓
activate
↓
verify
```

Không giả định atomic commit across all clusters.

---

# 189. Failure semantics

Nếu 3/10 clusters fail:

```text
partial activation
```

must remain observable.

Higher-level deployment/DR system quyết định:

```text
pause
continue
rollback
```

---

# 190. Integration with 636

636 có thể orchestration:

```text
deploy
→ credential prepare
→ credential rotate
→ service rollout
→ certificate activation
→ traffic shift
```

638 không trở thành deployment engine.

---

# 191. Integration with 637

637:

```text
rotation_before
grace
max_age
```

638:

```text
actual credential lifecycle
```

---

# 192. Integration with 633

Health gates:

```text
credential errors
TLS failures
authentication failures
```

có thể trở thành signals.

---

# 193. Integration with 635

Leadership:

```text
issuer epoch
fencing
```

được lấy từ 635.

---

# 194. Integration with 628

Persistent metadata:

```text
credential revisions
rotation history
trust registry
```

có thể replicated qua 628.

Secret material vẫn phải được bảo vệ bởi 610/provider.

---

# 195. Integration with 634

Events:

```text
CredentialRotated
CertificateRenewed
IdentityRevoked
TrustChanged
```

được phát qua 634.

---

# 196. Integration with 603

603 enforcement:

```text
who may read?
who may rotate?
who may revoke?
who may export?
```

638 lifecycle:

```text
when?
which version?
which scope?
```

---

# 197. Integration with 610

610:

```text
generate
sign
verify
encrypt
decrypt
derive
```

638:

```text
lifecycle
policy
version
distribution
rotation
```

---

# 198. Disaster recovery

DR state:

```text
credential metadata
trust revisions
active generations
provider references
rotation state
```

không nhất thiết có raw private material.

---

# 199. DR promotion

Khi cluster mới promote:

```text
verify trust
verify issuer epoch
verify credential state
fence old issuer
resume rotation
```

---

# 200. Emergency recovery

Nếu control plane unavailable nhưng credential sắp expiry:

```text
provider-local renewal
```

có thể được phép nếu policy định trước.

---

# 201. Provider-local autonomy

Một HSM/CA có thể renew credential locally.

638 sau đó reconcile:

```text
observed credential
```

với desired state.

---

# 202. Credential reconciliation source of truth

Có thể cấu hình:

```text
ControlPlaneAuthoritative
ProviderAuthoritative
Hybrid
```

Nhưng phải explicit.

---

# 203. Hybrid mode

Ví dụ:

```text
CA = source of truth for certificate serial
638 = source of truth for desired lifecycle
```

---

# 204. Certificate renewal races

Nếu hai controllers cùng renew:

```text
request_id
identity_generation
certificate_version
```

giúp deduplicate.

---

# 205. Issuance quotas

Provider quota:

```text
certificates/hour
keys/hour
sign operations
```

được tích hợp 606.

---

# 206. Renewal prioritization

Priority:

```text
ExpiredRisk
SecurityIncident
NormalExpiry
PlannedRotation
Prefetch
```

---

# 207. Rotation observability

Dashboard/CLI phải có:

```text
active
expiring
expired
revoked
rotating
failed
distribution_lag
```

---

# 208. Credential inventory

Inventory query:

```text
credential.list(
    scope,
    type,
    state,
    owner
)
```

---

# 209. Expiry inventory

```text
credential.expiring(within=7d)
```

---

# 210. Compliance metadata

Credential có thể có:

```text
compliance_tags
retention_policy
owner
business_scope
```

nhưng core không tự tuyên bố compliance certification.

---

# 211. Retention

Credential history retention:

```text
audit_retention
credential_metadata_retention
revocation_retention
```

khác nhau.

---

# 212. Destruction

Destroy credential:

```text
retired
→ destruction scheduled
→ destroyed
```

Destruction event phải được audit.

---

# 213. Secure destruction

Hardware provider thực hiện secure deletion khi hỗ trợ.

Software deletion chỉ là best-effort.

Không tuyên bố impossible guarantee.

---

# 214. Historical metadata

Sau destruction vẫn giữ:

```text
credential_id
version
fingerprint
timestamps
state
reason
```

nếu retention policy yêu cầu.

---

# 215. Fingerprints

Public credential fingerprint:

```text
SHA-256
```

hoặc provider-approved equivalent.

Fingerprint dùng để identify.

Không dùng fingerprint như secret.

---

# 216. Stable references

Application nên reference:

```text
credential_id
```

thay vì:

```text
secret bytes
```

---

# 217. AI-readable metadata

`.axcredential` phải giải thích:

```text
owner
purpose
provider
scope
rotation
expiry
trust
dependencies
```

AI agent có thể trả lời:

```text
Which credential is expiring?
Why is this service failing TLS?
Which trust revision is active?
```

mà không cần xem private material.

---

# 218. Compiler diagnostics

Compiler cảnh báo:

```text
secret exported
non-exportable key requested for export
credential has no expiry
credential has no rotation policy
trust domain undefined
unsafe credential scope
```

tùy annotation/policy.

---

# 219. Static analysis

Có thể phát hiện:

```text
credential used outside declared purpose
identity scope mismatch
missing capability
missing trust dependency
expired static certificate
```

---

# 220. Build-time certificate checks

Compiler/package tool có thể kiểm tra:

```text
certificate format
key algorithm
SAN
expiry
chain metadata
```

nhưng runtime vẫn phải verify.

---

# 221. Binary embedding

Development build có thể embed:

```text
public trust anchor
development certificate
```

Không cho phép production embed secret plaintext nếu policy cấm.

---

# 222. Production policy

Production profile có thể enforce:

```text
no_embedded_private_key
hardware_backed_required
short_lived_credentials
mandatory_rotation
mandatory_audit
```

---

# 223. Development profile

Development có thể cho:

```text
TestProvider
self-signed certificate
ephemeral keys
local trust domain
```

nhưng phải explicit.

---

# 224. Test credentials

Test credential phải có marker:

```text
credential.environment = Test
```

Production runtime không accept test credentials nếu policy không cho phép.

---

# 225. Environment separation

Trust domains:

```text
development
staging
production
```

không được implicit trust lẫn nhau.

---

# 226. Cross-environment protection

Production credential không được phân phối vào development target trừ khi policy explicit.

---

# 227. Environment fingerprint

Credential policy có:

```text
environment_id
policy_fingerprint
```

---

# 228. Global registry

Trust registry có thể reference:

```text
credential
identity
certificate
key
trust domain
issuer
```

nhưng không chứa raw material.

---

# 229. Registry consistency

Registry revision:

```text
trust_revision
```

được ghi trong diagnostic context.

---

# 230. Global control interaction

637 có thể publish:

```text
certificate.renew_before
```

638 enforce:

```text
max_renewal_window
```

Security upper bound không thể bị dynamic config vượt qua.

---

# 231. Dynamic policy hierarchy

```text
603 hard security boundary
       ↓
638 credential policy
       ↓
637 operational tuning
       ↓
application request
```

Mỗi tầng chỉ có thể thu hẹp authority.

---

# 232. No privilege amplification

Nếu application có:

```text
credential.read(service.orders)
```

thì không thể sửa:

```text
credential.read(global)
```

bằng dynamic configuration.

---

# 233. Delegated credential

Short-lived delegated credential:

```text
DelegatedCredential {
    parent
    subject
    scope
    expiry
    purpose
}
```

---

# 234. Delegation validation

Phải kiểm tra:

```text
parent active
parent scope contains child scope
child expiry <= parent expiry
purpose allowed
issuer authorized
```

---

# 235. Delegation revocation

Parent revoked:

```text
child delegation
```

phải bị invalid theo policy.

---

# 236. Trust graph

638 có thể biểu diễn:

```text
TrustGraph {
    nodes
    edges
    epochs
    scopes
}
```

Không phải graph database bắt buộc.

---

# 237. Trust graph validation

Phát hiện:

```text
expired edge
revoked issuer
scope widening
invalid chain
cycle where prohibited
```

---

# 238. Trust cycle

Không mặc định coi:

```text
A trusts B
B trusts A
```

là lỗi.

Nhưng nếu policy yêu cầu acyclic trust delegation thì phải reject.

---

# 239. Certificate chain

Chain phải được validate:

```text
leaf
→ intermediate
→ root
```

theo 610/provider.

---

# 240. Trust bundle update

Bundle update có:

```text
old revision
new revision
added anchors
removed anchors
changed policy
```

---

# 241. Root removal safety

Không remove root nếu còn active certificates phụ thuộc nó trừ khi:

```text
explicit emergency override
```

hoặc provider chứng minh dependency đã migrated.

---

# 242. Staged trust removal

```text
new root
↓
new certs
↓
observe
↓
deprecate old root
↓
remove old root
```

---

# 243. Certificate renewal telemetry

633 nhận:

```text
certificate_days_to_expiry
renewal_success
renewal_failure
distribution_lag
tls_handshake_failure
```

---

# 244. Incident integration

Security incident có thể trigger:

```text
emergency_rotation
emergency_revocation
trust_anchor_replacement
```

638 cung cấp primitives; incident-response policy nằm ở higher layer.

---

# 245. No autonomous security decisions

638 không tự quyết định:

```text
"This service is malicious"
```

Nó chỉ thực hiện explicit policy/events.

---

# 246. Configuration of rotation

637:

```text
rotation.orders_tls.renew_before = 30d
```

638:

```text
enforce(renew_before <= security_max)
```

---

# 247. Safe configuration clamp

Nếu requested:

```text
renew_before = 1d
```

nhưng minimum:

```text
7d
```

effective:

```text
7d
```

nếu policy định nghĩa minimum.

---

# 248. Policy explainability

API:

```text
credential.explain_policy()
```

trả:

```text
requested
effective
constraint
source
revision
```

---

# 249. Security state snapshot

Axiom diagnostic snapshot có:

```text
identity_generation
credential_versions
trust_revision
issuer_epoch
policy_revision
```

không có secret.

---

# 250. Runtime invariant set

638 phải đảm bảo tối thiểu:

1. Raw secrets không xuất hiện trong ordinary metadata.
2. Private keys không export nếu policy cấm.
3. Key version immutable.
4. Credential revision immutable.
5. Rotation không overwrite active version.
6. Compromised credential không tự active lại.
7. Revoked credential không trở lại active.
8. Stale issuer bị fencing.
9. Identity generation monotonic.
10. Trust revision monotonic.
11. Credential purpose explicit.
12. Credential scope explicit.
13. Distribution authorization bắt buộc.
14. Security policy không thể bị 637 override.
15. Hardware-backed requirement không bị software fallback bypass.
16. Rotation retry idempotent.
17. Issuance retry idempotent.
18. Emergency revoke không chờ normal schedule.
19. Expiry risk được ưu tiên.
20. Zero-downtime rotation hỗ trợ overlap.
21. Existing sessions có grace semantics explicit.
22. Trust-anchor rotation hỗ trợ staged migration.
23. Old trust anchor chỉ remove khi policy cho phép.
24. Credential history không bị xóa bởi rollback.
25. Destruction không xóa audit metadata nếu retention yêu cầu.
26. Secret event payload không chứa secret.
27. Credential cache không tự tạo authority.
28. Control-plane outage không tự tạo new authority.
29. Provider failure không tự export prohibited key.
30. Offline credentials phải có expiry/delegation.
31. Edge issuer phải có fencing.
32. Cross-domain trust phải explicit.
33. Trust không transitive mặc định.
34. Tenant credentials không cross-read.
35. Credential generation gắn với identity generation khi policy yêu cầu.
36. Certificate validation không bị bỏ qua bởi lifecycle layer.
37. Algorithm policy phải được enforce.
38. Key purpose không tự mở rộng.
39. Distribution state phải observable.
40. Partial rollout không báo completed giả.
41. Rotation controller phải bounded.
42. Provider calls phải resource-governed.
43. Watchers phải bounded.
44. Credential lookup hot path không cần distributed RPC.
45. No mandatory GC.
46. No mandatory third-party credential runtime.
47. Provider abstraction phải stable.
48. Test provider không được mặc định production-trusted.
49. Emergency override phải audit.
50. Break-glass authority phải time-bounded.
51. Delegation không được widen scope.
52. Child credential expiry không vượt parent.
53. Parent revocation propagates theo policy.
54. Signed bundles chống replay.
55. Timestamp không phải sole ordering primitive.
56. Rotation schedule có jitter.
57. Large-scale rotation không tạo thundering herd.
58. Provider rate limits phải được tôn trọng.
59. Recovery phải verify trust.
60. Credential state phải reconcile với provider state.

---

# 251. Acceptance Criteria

Implementation target: **≥350 acceptance criteria**.

Các nhóm bắt buộc:

### Credential
- creation;
- metadata;
- version;
- lifecycle;
- purpose;
- scope;
- expiry;
- destruction.

### Secret
- opaque references;
- access;
- zeroization;
- storage;
- backup;
- recovery.

### Key
- generation;
- algorithm policy;
- hardware backing;
- non-exportability;
- purpose;
- rotation;
- destruction.

### Certificate
- issuance;
- SAN;
- chain;
- renewal;
- overlap;
- revocation;
- zero-downtime rotation.

### Identity
- service identity;
- workload identity;
- device identity;
- generation;
- suspension;
- revocation;
- delegation.

### Trust
- trust domains;
- anchors;
- bundles;
- CA lifecycle;
- root rotation;
- cross-domain trust;
- trust revision.

### Rotation
- planned rotation;
- emergency rotation;
- canary;
- waves;
- partial failure;
- rollback;
- idempotency;
- fencing.

### Distribution
- pull;
- push;
- cache;
- authorization;
- partial distribution;
- reconnect;
- offline.

### Security
- capability;
- least privilege;
- tenant isolation;
- secret exclusion;
- audit;
- replay protection;
- break-glass.

### Federation
- global;
- regional;
- cluster;
- edge;
- delegated authority;
- issuer epochs;
- fencing.

### Reliability
- provider failure;
- HSM failure;
- CA failure;
- network partition;
- stale provider;
- control-plane failure;
- crash recovery.

### Integration
- 603;
- 610;
- 627;
- 628;
- 631;
- 632;
- 633;
- 634;
- 635;
- 636;
- 637.

### Tooling
- compiler annotations;
- metadata;
- CLI;
- dry-run;
- explain;
- simulator;
- inventory.

### Testing
- deterministic tests;
- fuzzing;
- property tests;
- security tests;
- provider conformance;
- fault injection;
- rotation stress;
- recovery tests.

---

# 252. Profiles

```text
AXCRED_NONE
AXCRED_LOCAL
AXCRED_SECRET
AXCRED_KEY
AXCRED_CERT
AXCRED_IDENTITY
AXCRED_TRUST
AXCRED_ROTATION
AXCRED_FEDERATION
AXCRED_EDGE
AXCRED_FULL
```

---

# 253. AXCRED_NONE

Không link credential lifecycle runtime.

---

# 254. AXCRED_LOCAL

Chỉ local/test credential provider.

---

# 255. AXCRED_SECRET

Secret lifecycle.

---

# 256. AXCRED_KEY

Key lifecycle.

---

# 257. AXCRED_CERT

Certificate issuance/renewal.

---

# 258. AXCRED_IDENTITY

Identity lifecycle.

---

# 259. AXCRED_TRUST

Trust registry.

---

# 260. AXCRED_ROTATION

Distributed rotation.

---

# 261. AXCRED_FEDERATION

Federated trust/credential lifecycle.

---

# 262. AXCRED_EDGE

Offline/edge delegated credential management.

---

# 263. AXCRED_FULL

Toàn bộ BOOTSTRAP-638.

---

# 264. Final architecture

```text
                         ┌─────────────────────────────┐
                         │       Axiom Application     │
                         └──────────────┬──────────────┘
                                        │
                                Credential API
                                        │
                 ┌──────────────────────▼─────────────────────┐
                 │                 638 Runtime                  │
                 ├──────────────────────────────────────────────┤
                 │ Secret Lifecycle                             │
                 │ Key Lifecycle                                │
                 │ Certificate Lifecycle                        │
                 │ Identity Lifecycle                           │
                 │ Trust Registry                               │
                 │ Rotation Controller                          │
                 │ Revocation Controller                        │
                 │ Credential Distribution                      │
                 ├──────────────────────────────────────────────┤
                 │ Version / Epoch / Lease / Fencing            │
                 └──────────────────────┬───────────────────────┘
                                        │
        ┌───────────────┬───────────────┼───────────────┬──────────────┐
        ▼               ▼               ▼               ▼              ▼
      603             610             627             628            635
   Security          Crypto         Identity         Storage        Control
        │               │               │               │              │
        └───────────────┴───────────────┴───────────────┴──────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
                  637                                     636
             Dynamic Control                         Deployment
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        ▼
                                631 / 632 / 633 / 634
```

---

# 265. Core design conclusion

BOOTSTRAP-638 tạo ra một nguyên tắc quan trọng cho toàn bộ Axiom distributed runtime:

```text
637 = dynamic behavior
638 = dynamic trust
603 = authority
610 = cryptography
627 = identity/authentication semantics
635 = control-plane authority
636 = deployment orchestration
```

Như vậy Axiom không biến secret, certificate, key và identity thành những biến configuration thông thường.

Luồng chuẩn:

```text
                 ┌──────────────┐
                 │    637       │
                 │ Runtime Ctrl  │
                 └──────┬───────┘
                        │ policy
                        ▼
                 ┌──────────────┐
                 │    638       │
                 │ Credential   │
                 │ Lifecycle    │
                 └──────┬───────┘
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
            610        603        627
          Crypto     Authority   Identity
             │
             ▼
       Hardware / OS / CA
             │
             ▼
       631 / 632 / Services
```

Điểm cốt lõi:

> **Credential rotation là một lifecycle operation, không phải một configuration update.**

---

# 266. Trạng thái

**BOOTSTRAP-638 = COMPLETE**

Đã xác định đầy đủ:

- distributed secret lifecycle;
- key lifecycle;
- hardware-backed keys;
- certificate issuance/renewal;
- certificate zero-downtime rotation;
- identity lifecycle;
- workload/device identity;
- trust registry;
- trust-domain model;
- trust-anchor rotation;
- credential versioning;
- credential leases;
- revocation;
- emergency revocation;
- delegation;
- fencing;
- issuer epochs;
- credential distribution;
- offline/edge credentials;
- federation;
- provider architecture;
- rotation orchestration;
- progressive credential rollout;
- disaster recovery;
- compiler integration;
- CLI;
- AI-readable metadata;
- security invariants;
- performance;
- resource governance;
- testing;
- ≥350 acceptance criteria target.

**Task tiếp theo: BOOTSTRAP-639 — Native Distributed Policy Decision, Policy Evaluation, Rule Engine, Admission Control, Governance, Compliance Guardrails & Declarative Authorization Runtime 5.0.**
:::