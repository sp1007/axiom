# BOOTSTRAP-727 — AXSECURITY

**Namespace:** `AXSECURITY`  
**Phase:** Axiom Civilization Runtime / Native Security & Trust Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXIDENTITY`, `AXLAW`, `AXGOV`, `AXNETWORK`, `AXSTORAGE`, `AXCOMPUTE`, `AXASSET`

---

# 727.0 — Mục tiêu

`AXSECURITY` là security/trust substrate native của Axiom.

Mục tiêu là tạo một security model thống nhất cho toàn bộ Axiom:

```text
Application
     ↓
Capability / Policy
     ↓
AXSECURITY
     ├── Identity
     ├── Authentication
     ├── Authorization
     ├── Cryptography
     ├── Key Management
     ├── Secure Storage
     ├── Secrets
     ├── Attestation
     ├── Sandbox
     ├── Secure IPC
     ├── Audit Integrity
     └── Privacy
```

Nguyên tắc:

> Authentication xác định "ai", authorization xác định "được làm gì", capability xác định "được cấp quyền gì", policy xác định "trong điều kiện nào".

Không trộn các khái niệm này thành một API duy nhất.

---

# 727.1 — Security Boundary

`AXSECURITY` sở hữu:

```text
cryptographic primitives
keys
key lifecycle
certificates
signatures
hashes
encryption
authentication
authorization
capabilities
security policies
secure storage
secrets
attestation
sandbox
secure IPC
audit integrity
privacy primitives
security telemetry
security simulation
```

Không sở hữu:

```text
identity authority      → AXIDENTITY
legal authority         → AXLAW
government authority    → AXGOV
network transport       → AXNETWORK
physical assets         → AXASSET
money                   → AXFINANCE
```

---

# 727.2 — Security Principal

```axiom
security_principal {
    principal_id
    principal_type
    identity_reference
    attributes
}
```

Types:

```text
human
service
application
device
organization
system
anonymous
```

Principal không tự động có quyền.

---

# 727.3 — Security Context

```axiom
security_context {
    principal
    session
    capabilities
    policies
    environment
    authentication_state
}
```

Security context được truyền xuyên qua:

```text
process
thread/task
RPC
IPC
database session
filesystem operation
network operation
```

---

# 727.4 — Authentication

```axiom
authentication {
    principal
    method
    evidence
    timestamp
    assurance
}
```

Methods:

```text
password
passkey
certificate
hardware_token
biometric_reference
service_credential
federated_identity
device_attestation
```

Biometric data phải được xử lý theo privacy policy; `AXSECURITY` không biến biometric thành mặc định bắt buộc.

---

# 727.5 — Authentication Assurance

```text
assurance:
    LOW
    STANDARD
    HIGH
    HARDWARE_BACKED
```

Application có thể yêu cầu:

```axiom
require_assurance(HIGH)
```

---

# 727.6 — Authentication Session

```axiom
security_session {
    session_id
    principal
    authenticated_at
    expires_at
    assurance
    state
}
```

State:

```text
AUTHENTICATED
EXPIRED
REVOKED
LOCKED
TERMINATED
```

---

# 727.7 — Authorization

Authorization input:

```text
principal
resource
action
context
policy
```

Result:

```text
ALLOW
DENY
REQUIRE_STEP_UP
DEFER
```

Không được dùng:

```text
authenticated == true
```

làm equivalent của authorization.

---

# 727.8 — Resource

```axiom
security_resource {
    resource_id
    resource_type
    owner
    attributes
}
```

Ví dụ:

```text
database/table
file
device
network endpoint
government record
compute cluster
physical asset
service
API
```

---

# 727.9 — Action

```axiom
security_action {
    action_id
    name
    risk
}
```

Ví dụ:

```text
read
write
create
delete
execute
admin
export
share
grant
revoke
```

---

# 727.10 — Capability

Capability là một **unforgeable authority token/reference**.

```axiom
capability {
    capability_id
    principal
    resource
    actions
    constraints
    expiry
}
```

Ví dụ:

```text
capability:
    resource = database.users
    action   = read
```

---

# 727.11 — Capability Delegation

```axiom
delegate(
    capability,
    target,
    restrictions
)
```

Delegated capability không được mở rộng quyền vượt capability nguồn.

Ví dụ:

```text
Parent:
    read + write

Child:
    read
```

Child không thể tạo:

```text
write
admin
delete
```

từ capability đó.

---

# 727.12 — Capability Revocation

```axiom
revoke(capability)
```

Revocation phải có observable state:

```text
ACTIVE
REVOKED
EXPIRED
SUSPENDED
```

---

# 727.13 — Capability Attenuation

```axiom
attenuate(
    capability,
    reduced_actions,
    reduced_scope,
    expiry
)
```

Đây là primitive quan trọng để service có thể cấp quyền nhỏ hơn cho subsystem.

---

# 727.14 — Security Policy

```axiom
security_policy {
    policy_id
    subjects
    resources
    actions
    conditions
    effect
    priority
    version
}
```

Effect:

```text
allow
deny
require_authentication
require_step_up
audit
```

---

# 727.15 — Policy Evaluation

```text
Request
  ↓
Identity
  ↓
Authentication
  ↓
Capability
  ↓
Policy
  ↓
Context
  ↓
Decision
```

Policy engine phải deterministic trong cùng policy/version/context.

---

# 727.16 — Policy Version

```axiom
policy_version {
    policy_id
    version
    effective_at
    hash
}
```

Security decision có thể lưu:

```text
policy_id
policy_version
decision
```

để audit/replay.

---

# 727.17 — Deny by Default

Resource mới:

```text
no explicit authority
        ↓
DENY
```

Không được tự động inherit quyền chỉ vì resource cùng namespace.

---

# 727.18 — Explicit Grant

```axiom
grant(
    principal,
    resource,
    action
)
```

Grant phải tạo audit event.

---

# 727.19 — Separation of Duties

Có thể yêu cầu:

```axiom
policy {
    action: approve_payment
    requires:
        principal != creator
}
```

Một principal không nhất thiết được vừa:

```text
create
+
approve
```

trong các workflow yêu cầu maker-checker.

---

# 727.20 — Cryptographic Primitive Boundary

`AXSECURITY` cung cấp abstraction:

```text
hash
MAC
digital_signature
key_derivation
symmetric_encryption
asymmetric_encryption
randomness
key_exchange
```

Implementation phải dùng primitive cryptographic đã được platform/backend kiểm chứng thay vì tự viết thuật toán mới.

---

# 727.21 — Hash

```axiom
hash(
    algorithm,
    data
) -> digest
```

Digest:

```axiom
digest {
    algorithm
    bytes
}
```

Use cases:

```text
content addressing
integrity
deduplication
signing
password-derived verification
```

---

# 727.22 — Hash Agility

Hash algorithm phải là explicit metadata:

```text
algorithm
version
digest
```

Không hard-code một hash algorithm vào toàn bộ Axiom data model.

---

# 727.23 — HMAC / MAC

```axiom
mac(
    key,
    data
)

verify_mac(
    key,
    data,
    mac
)
```

Dùng để xác thực integrity/authenticity của data giữa các trusted parties.

---

# 727.24 — Digital Signature

```axiom
sign(
    private_key,
    data
)

verify(
    public_key,
    data,
    signature
)
```

Signature object:

```axiom
signature {
    algorithm
    key_reference
    data_hash
    signature_bytes
}
```

---

# 727.25 — Signed Object

```axiom
signed_object {
    payload
    signature
    signer
    signed_at
    schema_version
}
```

Có thể dùng cho:

```text
configuration
artifacts
certificates
database exports
software packages
policy documents
```

---

# 727.26 — Symmetric Encryption

```axiom
encrypt(
    key,
    plaintext,
    associated_data
)

decrypt(
    key,
    ciphertext,
    associated_data
)
```

Authenticated encryption phải là default cho dữ liệu cần cả confidentiality và integrity.

---

# 727.27 — Nonce

Encryption API phải quản lý nonce/IV semantics rõ ràng.

```axiom
ciphertext {
    algorithm
    nonce
    associated_data
    ciphertext
}
```

Không cho phép caller vô tình reuse nonce trong những chế độ yêu cầu uniqueness.

---

# 727.28 — Key Reference

Application không nhất thiết nhận raw key bytes.

```axiom
key_reference {
    key_id
    provider
    version
    usage
}
```

Ví dụ:

```text
encrypt
decrypt
sign
verify
derive
unwrap
```

---

# 727.29 — Key Object

```axiom
security_key {
    key_id
    type
    algorithm
    purpose
    version
    state
    hardware_backed
}
```

States:

```text
GENERATED
ACTIVE
SUSPENDED
EXPIRED
REVOKED
DESTROYED
```

---

# 727.30 — Key Generation

```axiom
generate_key()
generate_key_pair()
derive_key()
import_key()
wrap_key()
unwrap_key()
```

Randomness phải đến từ secure random source.

---

# 727.31 — Key Rotation

```axiom
rotate_key(key_id)
```

Rotation phải hỗ trợ:

```text
old version → verification/decryption
new version → signing/encryption
```

để tránh breaking toàn bộ dữ liệu ngay lập tức.

---

# 727.32 — Key Destruction

```axiom
destroy_key()
```

Sau destruction:

```text
key state = DESTROYED
```

Không được báo `success` nếu backend chỉ đánh dấu metadata mà key material vẫn còn accessible.

---

# 727.33 — Key Escrow

Nếu platform/domain yêu cầu recovery:

```axiom
key_escrow {
    policy
    custodians
    threshold
}
```

Threshold có thể biểu diễn:

```text
2-of-3
3-of-5
```

---

# 727.34 — Secure Randomness

```axiom
secure_random(bytes)
```

Phân biệt:

```text
secure_random()
pseudo_random()
simulation_random()
```

Simulation randomness không được sử dụng cho security secrets.

---

# 727.35 — Password Handling

AXSECURITY không lưu password plaintext.

```axiom
password_record {
    algorithm
    salt
    parameters
    verifier
}
```

Password verification phải sử dụng password-hardening primitive thích hợp và explicit parameters.

---

# 727.36 — Secret

```axiom
secret {
    secret_id
    type
    version
    expiry
    access_policy
}
```

Types:

```text
API_KEY
TOKEN
PASSWORD
PRIVATE_KEY
CREDENTIAL
RECOVERY_SECRET
```

---

# 727.37 — Secret Store

```axiom
secret_store {
    provider
    entries
    policy
}
```

Backend:

```text
OS secure storage
hardware security module
TPM-backed storage
secure enclave
encrypted local store
remote secret service
```

---

# 727.38 — Secret Exposure Boundary

Secret material phải có lifecycle:

```text
stored
loaded
used
expired
revoked
destroyed
```

Không tự động xuất secret vào:

```text
logs
telemetry
crash reports
traces
error messages
```

---

# 727.39 — Secure Memory

```axiom
secure_buffer {
    address
    size
    protection
}
```

Properties:

```text
non_swappable
zero_on_release
restricted_access
optional_locked_memory
```

Platform support có thể khác nhau và phải được expose rõ.

---

# 727.40 — Memory Zeroization

```axiom
secure_zero(buffer)
```

Compiler/runtime không được optimize away security-critical zeroization.

---

# 727.41 — Certificate

```axiom
certificate {
    subject
    issuer
    public_key
    validity
    extensions
    signature
}
```

Certificate validation:

```text
chain
validity
signature
policy
revocation
usage
```

---

# 727.42 — Trust Store

```axiom
trust_store {
    anchors
    policies
    version
}
```

Trust anchor phải explicit.

Không coi mọi certificate hợp lệ về syntax là trusted.

---

# 727.43 — Certificate Revocation

```axiom
revocation_status {
    valid
    revoked
    unknown
}
```

`UNKNOWN` không được tự động biến thành `VALID`.

---

# 727.44 — Trust Chain

```text
Root
 ↓
Intermediate
 ↓
Certificate
 ↓
Public Key
 ↓
Identity Mapping
```

Trust chain phải có verification result.

---

# 727.45 — Device Attestation

```axiom
attestation {
    device
    platform_state
    measurements
    evidence
    verifier
    timestamp
}
```

Có thể dùng để xác minh:

```text
trusted boot state
software measurement
hardware identity
execution environment
```

---

# 727.46 — Attestation Policy

```axiom
attestation_policy {
    required_measurements
    minimum_security_level
    expiry
}
```

Service có thể yêu cầu:

```axiom
require_attestation(policy)
```

---

# 727.47 — Secure Boot Integration

AXSECURITY có thể expose:

```axiom
secure_boot_state()
boot_measurements()
boot_chain()
```

Nhưng không giả định mọi platform đều hỗ trợ secure boot.

---

# 727.48 — Application Identity

Application binary có thể có:

```axiom
application_identity {
    application_id
    publisher
    version
    artifact_hash
    signature
}
```

---

# 727.49 — Artifact Verification

```axiom
verify_artifact(
    artifact,
    trust_policy
)
```

Result:

```text
VERIFIED
UNTRUSTED
INVALID_SIGNATURE
EXPIRED
REVOKED
UNKNOWN
```

---

# 727.50 — Package Trust

Package manager tương lai có thể dùng:

```text
artifact
 ↓
hash
 ↓
signature
 ↓
publisher identity
 ↓
trust policy
 ↓
installation
```

Không dựa chỉ vào filename hoặc URL.

---

# 727.51 — Sandbox

```axiom
security_sandbox {
    filesystem
    network
    process
    device
    memory
    compute
    time
}
```

---

# 727.52 — Sandbox Policy

Ví dụ:

```axiom
sandbox {
    filesystem:
        read "/data/models"
        deny "/system"

    network:
        allow "api.example"

    process:
        deny_spawn

    device:
        deny_camera
}
```

---

# 727.53 — Process Isolation

Sandbox có thể map xuống:

```text
process isolation
container
VM
OS sandbox
hardware isolation
Axiom runtime isolation
```

---

# 727.54 — Resource Limits

```axiom
security_limits {
    memory
    cpu
    disk
    network
    processes
    file_descriptors
    execution_time
}
```

---

# 727.55 — Secure IPC

```axiom
secure_channel {
    local_endpoint
    peer_identity
    authentication
    encryption
    authorization
}
```

IPC có thể dùng:

```text
shared memory
pipes
local sockets
message queues
RPC
```

---

# 727.56 — Shared Memory Security

Shared memory region phải có:

```axiom
shared_memory_capability {
    region
    permissions
    peers
    expiry
}
```

Không cho phép process khác tự ý map region.

---

# 727.57 — Network Security Integration

`AXNETWORK` gọi:

```text
AXSECURITY
   ↓
authentication
   ↓
TLS
   ↓
authorization
```

Ví dụ:

```axiom
secure_connect(
    endpoint,
    identity,
    trust_policy
)
```

---

# 727.58 — Database Security Integration

`AXDATABASE` dùng:

```text
principal
capability
policy
key reference
audit context
```

Không tự tạo một authorization system riêng.

---

# 727.59 — Storage Security Integration

`AXSTORAGE` có thể yêu cầu:

```axiom
storage.encrypt()
storage.key_reference()
storage.access_policy()
```

Database/file/object encryption dùng chung key-management substrate.

---

# 727.60 — Compute Security

`AXCOMPUTE` có thể yêu cầu:

```text
signed workload
trusted runtime
resource capability
device attestation
secure execution
```

AI workload không được bypass sandbox chỉ vì là AI workload.

---

# 727.61 — Security Audit

```axiom
security_audit_event {
    event_id
    timestamp
    principal
    action
    resource
    decision
    policy
    evidence
}
```

Events:

```text
AUTHENTICATION
AUTHORIZATION
CAPABILITY_GRANTED
CAPABILITY_REVOKED
KEY_CREATED
KEY_ROTATED
KEY_REVOKED
SECRET_ACCESSED
POLICY_CHANGED
CERTIFICATE_VALIDATED
ATTESTATION_VERIFIED
SANDBOX_VIOLATION
```

---

# 727.62 — Tamper-Evident Audit

Audit chain:

```text
Event 1
   ↓ hash
Event 2
   ↓ hash
Event 3
   ↓ hash
...
```

Có thể định kỳ anchor chain bằng:

```text
signed checkpoint
external trusted store
hardware-backed key
```

---

# 727.63 — Audit Integrity

Audit record phải phân biệt:

```text
event recorded
event cryptographically protected
event externally anchored
```

Không tuyên bố tamper-proof nếu chỉ có local file.

---

# 727.64 — Privacy

Privacy primitives:

```text
data classification
purpose limitation
data minimization
retention
deletion
access logging
pseudonymization
tokenization
```

---

# 727.65 — Data Classification

```axiom
data_classification {
    PUBLIC
    INTERNAL
    CONFIDENTIAL
    RESTRICTED
    HIGHLY_RESTRICTED
}
```

Classification là policy metadata, không tự động thay thế legal classification.

---

# 727.66 — Purpose Binding

```axiom
data_access_policy {
    purpose
    allowed_actions
    expiry
}
```

Ví dụ:

```text
purpose = "billing"
```

không mặc nhiên cho phép:

```text
marketing
analytics
export
```

---

# 727.67 — Data Minimization

API có thể yêu cầu projection:

```axiom
read_user(
    fields = [id, name]
)
```

thay vì trả toàn bộ record.

---

# 727.68 — Pseudonymization

```axiom
pseudonymize(
    identity,
    domain
)
```

Pseudonym không phải anonymous identity.

---

# 727.69 — Tokenization

```axiom
tokenize(
    sensitive_value
)
```

Token phải có explicit vault/reference semantics.

---

# 727.70 — Security Event Correlation

Security engine có thể liên kết:

```text
authentication
 ↓
network connection
 ↓
database access
 ↓
file access
 ↓
configuration change
```

bằng:

```text
trace_id
session_id
principal_id
```

---

# 727.71 — Threat Detection

AI/rule engine có thể phát hiện:

```text
unusual login
credential misuse
unexpected network behavior
permission escalation attempt
abnormal data access
repeated authentication failures
```

Detection result:

```axiom
security_observation {
    observation
    confidence
    evidence
    model_version
}
```

---

# 727.72 — Detection ≠ Finding

```text
security_observation
        ≠
confirmed incident
```

Detection system không tự động biến một anomaly thành authoritative incident.

---

# 727.73 — Security Incident

```axiom
security_incident {
    incident_id
    observations
    severity
    state
    response
}
```

State:

```text
DETECTED
TRIAGED
CONTAINED
INVESTIGATING
RECOVERING
RESOLVED
CLOSED
```

---

# 727.74 — Security Response

```axiom
security_response {
    isolate
    revoke
    rotate_key
    terminate_session
    block_endpoint
    quarantine
    restore
}
```

Automated response phải nằm dưới explicit policy.

---

# 727.75 — Key Compromise

Khi key bị compromise:

```text
detect
 ↓
mark compromised
 ↓
revoke
 ↓
rotate
 ↓
reissue
 ↓
revalidate dependent artifacts
```

Không chỉ đơn giản tạo key mới rồi bỏ key cũ.

---

# 727.76 — Recovery

Security recovery có thể cần:

```text
backup keys
identity recovery
credential recovery
device recovery
policy recovery
audit recovery
```

Recovery authority phải explicit.

---

# 727.77 — Multi-Party Authorization

```axiom
authorization_rule {
    required_approvals
    distinct_principals
}
```

Ví dụ:

```text
2 distinct authorized principals
```

cho operation nhạy cảm.

---

# 727.78 — Time-Bounded Authorization

```axiom
temporary_capability {
    capability
    starts_at
    expires_at
}
```

Hữu ích cho:

```text
maintenance
incident response
temporary administration
deployment
```

---

# 727.79 — Geographic/Network Conditions

Policy có thể tham chiếu context:

```text
network_zone
device
time
service
attestation
```

Không được tự động coi IP address là reliable geographic identity.

---

# 727.80 — Security Simulation

```axiom
security_simulation {
    identities
    capabilities
    policies
    resources
    attack_model
}
```

Có thể kiểm tra:

```text
can_access()
can_delegate()
can_escalate()
can_revoke()
policy_conflict()
```

---

# 727.81 — Policy Verification

Có thể kiểm tra static:

```axiom
verify_policy(policy)
```

Tìm:

```text
unreachable rule
conflicting rule
privilege escalation
unbounded delegation
missing deny
expired authority
```

---

# 727.82 — Security Digital Twin

```axiom
security_digital_twin {
    principals
    resources
    capabilities
    policies
    devices
    services
    network
}
```

Cho phép mô phỏng:

```text
access
delegation
revocation
compromise
rotation
incident response
```

---

# 727.83 — AI Security Assistant

AI có thể:

```text
explain policy
find suspicious patterns
suggest least-privilege changes
suggest key rotation
summarize audit events
simulate policy changes
```

AI không được:

```text
grant authority
disable controls
declare trust
override policy
```

trừ khi một automation policy rõ ràng đã trao quyền đó.

---

# 727.84 — Least Privilege

Mọi subsystem nên yêu cầu:

```text
minimum capability
minimum scope
minimum lifetime
minimum data
```

Ví dụ:

```text
database.read
```

thay vì:

```text
system.admin
```

---

# 727.85 — Security Context Propagation

Khi:

```text
A → RPC → B → Database
```

security context phải có thể truyền:

```text
principal
delegated authority
trace
purpose
authentication assurance
```

nhưng B không được tự động tin mọi metadata từ A.

---

# 727.86 — Confused Deputy Protection

Service B không được sử dụng authority của chính nó để thực hiện hành động thay A nếu policy yêu cầu authority của A.

```text
User A
  ↓
Service B
  ↓
Resource C
```

Phải xác định rõ:

```text
who requested
who executes
whose authority is used
```

---

# 727.87 — Secure Defaults

Default:

```text
deny
encrypted transport when available/required
authenticated identity
explicit authorization
bounded lifetime
audited privileged operations
minimal data exposure
```

---

# 727.88 — Native APIs

```axiom
authenticate()
logout()
create_session()
revoke_session()

authorize()
check_capability()
grant()
revoke()
delegate()
attenuate()

generate_key()
import_key()
export_public_key()
rotate_key()
revoke_key()
destroy_key()

hash()
mac()
sign()
verify()
encrypt()
decrypt()
derive_key()

secure_random()

create_secret()
read_secret()
rotate_secret()
revoke_secret()

create_trust_store()
validate_certificate()
validate_chain()

attest()
verify_attestation()

create_sandbox()
enter_sandbox()
exit_sandbox()

create_secure_channel()

classify_data()
create_access_policy()
pseudonymize()
tokenize()

audit_security_event()
verify_audit_chain()

detect_security_anomaly()
create_security_incident()

simulate_security()
verify_policy()
create_security_digital_twin()
```

---

# 727.89 — Canonical Authentication Flow

```text
Credential / Evidence
        ↓
Verification
        ↓
Principal Resolution
        ↓
Assurance Evaluation
        ↓
Session Creation
        ↓
Capability/Policy Evaluation
        ↓
Authorized Operation
```

---

# 727.90 — Canonical Authorization Flow

```text
Request
  ↓
Principal
  ↓
Authentication State
  ↓
Capability
  ↓
Resource
  ↓
Action
  ↓
Policy
  ↓
Context
  ↓
Decision
  ↓
Audit
```

---

# 727.91 — Canonical Key Rotation

```text
Current Key
    ↓
Generate New Key
    ↓
Activate New Version
    ↓
Dual Compatibility
    ↓
Re-encrypt / Re-sign
    ↓
Verify
    ↓
Revoke Old Key
    ↓
Destroy When Safe
```

---

# 727.92 — Canonical Secure RPC

```text
Client
 ↓
Identity
 ↓
Authentication
 ↓
TLS / Secure Channel
 ↓
RPC Schema Validation
 ↓
Authorization
 ↓
Server Execution
 ↓
Audit
 ↓
Response
```

---

# 727.93 — Canonical Security Incident

```text
Observation
 ↓
Correlation
 ↓
Detection
 ↓
Incident Creation
 ↓
Policy Evaluation
 ↓
Containment
 ↓
Investigation
 ↓
Recovery
 ↓
Key / Credential Rotation
 ↓
Verification
 ↓
Closure
```

---

# 727.94 — Formal Invariants

```text
SEC-INV-01   Authentication never implies authorization.
SEC-INV-02   Every privileged operation has an authorization decision.
SEC-INV-03   Capabilities cannot be expanded through delegation.
SEC-INV-04   Revoked capabilities cannot authorize new operations.
SEC-INV-05   Expired capabilities cannot authorize new operations.
SEC-INV-06   Security policies are versioned.
SEC-INV-07   Security decisions identify policy version.
SEC-INV-08   Deny is the default for unspecified privileged access.
SEC-INV-09   Principal identity cannot be inferred solely from network address.
SEC-INV-10   Service identity and human identity remain distinct.

SEC-INV-11   Cryptographic keys have explicit lifecycle state.
SEC-INV-12   Destroyed keys cannot be reported as active.
SEC-INV-13   Cryptographic algorithm metadata is explicit.
SEC-INV-14   Secure randomness is distinct from simulation randomness.
SEC-INV-15   Encryption authentication failures cannot produce valid plaintext.
SEC-INV-16   Nonce/IV requirements are enforced by the crypto API.
SEC-INV-17   Private key material cannot be exposed through public-key APIs.
SEC-INV-18   Secret material is excluded from normal telemetry.
SEC-INV-19   Key rotation preserves declared compatibility.
SEC-INV-20   Compromised keys can be revoked independently of identity.

SEC-INV-21   Certificate trust requires an explicit trust anchor/policy.
SEC-INV-22   Unknown certificate revocation state is not equivalent to valid.
SEC-INV-23   Attestation evidence identifies verifier and time.
SEC-INV-24   Sandbox policy is explicit.
SEC-INV-25   Sandbox escape is a security failure, not normal application behavior.
SEC-INV-26   Secure IPC identifies peer authority.
SEC-INV-27   Shared-memory authority is explicit.
SEC-INV-28   Security context cannot silently gain privileges across RPC.
SEC-INV-29   Confused-deputy execution is detectable/preventable by policy.
SEC-INV-30   Privileged operations are auditable when policy requires.

SEC-INV-31   Audit records preserve event ordering.
SEC-INV-32   Tamper-evident state identifies its integrity mechanism.
SEC-INV-33   Privacy classification does not automatically grant access.
SEC-INV-34   Purpose-bound access cannot silently become unrestricted access.
SEC-INV-35   Data minimization may not be bypassed by generic serialization.
SEC-INV-36   Security observations are not automatically authoritative incidents.
SEC-INV-37   AI security recommendations cannot silently change authority.
SEC-INV-38   AI cannot bypass authentication or authorization.
SEC-INV-39   Security simulation cannot mutate production security state.
SEC-INV-40   Security replay cannot create production side effects.
```

---

# 727.95 — Performance Architecture

Security không được đồng nghĩa với:

```text
generic object
+
reflection
+
runtime policy interpretation
+
multiple copies
```

Hot path:

```text
Request
 ↓
cached principal
 ↓
capability check
 ↓
compiled policy
 ↓
native operation
```

---

# 727.96 — Compile-Time Security

Axiom compiler có thể kiểm tra trước:

```text
capability requirements
resource types
RPC permissions
sandbox declarations
secret usage
data classification
```

Ví dụ:

```axiom
requires network.connect
requires database.read
```

Compiler/runtime có thể phát hiện thiếu capability trước execution.

---

# 727.97 — Policy Compilation

```text
Policy Source
     ↓
Parse
     ↓
Type Check
     ↓
Conflict Analysis
     ↓
Optimization
     ↓
Compiled Policy
```

Runtime không cần evaluate toàn bộ policy tree cho mỗi operation nếu policy có thể specialize.

---

# 727.98 — Hardware Acceleration

AXSECURITY có thể tận dụng:

```text
AES acceleration
SHA acceleration
hardware RNG
TPM
Secure Enclave
HSM
CPU isolation
memory encryption
```

Nhưng API phải expose capability:

```axiom
security_capabilities()
```

để application biết mức bảo đảm thực tế.

---

# 727.99 — Platform Portability

Backend:

```text
Windows
Linux
macOS
iOS
Android
WASM
embedded
```

có thể khác nhau.

Axiom security contract phải phân biệt:

```text
REQUIRED
OPTIONAL
UNAVAILABLE
```

thay vì giả vờ mọi platform đều có hardware security.

---

# 727.100 — Completion Criteria

`BOOTSTRAP-727` phải freeze:

1. Security principal.
2. Security context.
3. Authentication.
4. Authentication assurance.
5. Session.
6. Authorization.
7. Resource.
8. Action.
9. Capability.
10. Delegation.
11. Revocation.
12. Attenuation.
13. Policy.
14. Policy version.
15. Cryptographic abstraction.
16. Hash.
17. MAC.
18. Digital signature.
19. Authenticated encryption.
20. Secure randomness.
21. Key management.
22. Key rotation.
23. Key destruction.
24. Secret management.
25. Secure memory.
26. Certificate.
27. Trust store.
28. Certificate revocation.
29. Attestation.
30. Secure boot integration.
31. Artifact verification.
32. Package trust.
33. Sandbox.
34. Resource limits.
35. Secure IPC.
36. Network security integration.
37. Database security integration.
38. Storage security integration.
39. Compute security integration.
40. Audit.
41. Tamper-evident audit.
42. Privacy.
43. Data classification.
44. Purpose binding.
45. Pseudonymization.
46. Tokenization.
47. Threat detection.
48. Security incidents.
49. Automated response.
50. Recovery.
51. Multi-party authorization.
52. Temporary authorization.
53. Policy verification.
54. Security simulation.
55. Security digital twin.
56. AI security boundary.
57. Least privilege.
58. Context propagation.
59. Confused-deputy protection.
60. Secure defaults.
61. Native APIs.
62. Compile-time security.
63. Hardware security integration.
64. Cross-platform security backend.
65. Formal invariants.
66. Native performance architecture.

---

# 727.101 — Definition of Done

```text
BOOTSTRAP-727
STATUS: COMPLETE / FROZEN

AXSECURITY 5.0
    ├── Identity & Authentication
    ├── Authorization
    ├── Capability Security
    ├── Policy Engine
    ├── Cryptography
    ├── Key Management
    ├── Secret Management
    ├── Secure Memory
    ├── Certificates
    ├── Trust Chains
    ├── Attestation
    ├── Sandbox
    ├── Secure IPC
    ├── Network Security
    ├── Database Security
    ├── Storage Security
    ├── Compute Security
    ├── Privacy
    ├── Audit Integrity
    ├── Threat Detection
    ├── Incident Response
    ├── Security Simulation
    ├── Security Digital Twin
    ├── AI Security Boundary
    ├── Compile-Time Security
    └── Hardware Security
```

**BOOTSTRAP-727 / AXSECURITY — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-728 — AXIDENTITY 2.0 / IDENTITY TRUST FABRIC

**Native Identity & Trust Fabric — human/service/device identities, identifiers, credentials, profiles, organizations, relationships, authentication federation, identity lifecycle, claims, roles, attributes, delegated identity, identity graph, identity resolution, privacy-preserving identifiers, verifiable credentials, organizational identity, device identity, service identity, cross-domain identity mapping, identity recovery, revocation, identity events, distributed identity synchronization, identity simulation & Identity Fabric 5.0.**