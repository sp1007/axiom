# BOOTSTRAP-728 — AXIDENTITY 2.0 / IDENTITY TRUST FABRIC

**Namespace:** `AXIDENTITY`  
**Phase:** Axiom Civilization Runtime / Identity & Trust Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXSECURITY`, `AXCIVIL`, `AXLAW`, `AXGOV`, `AXNETWORK`, `AXASSET`, `AXPROPERTY`

> Đây là **nâng cấp semantic của AXIDENTITY hiện hữu**, không tạo một identity system thứ hai. `AXIDENTITY` tiếp tục là nơi sở hữu identity facts và identity lifecycle; `AXSECURITY` sở hữu cryptographic trust, authentication primitives và authorization substrate.

---

# 728.0 — Mục tiêu

`AXIDENTITY 2.0` trở thành identity fabric dùng chung cho toàn bộ Axiom.

```text
                    AXIDENTITY
                         │
       ┌─────────────────┼──────────────────┐
       ↓                 ↓                  ↓
    Human             Organization       Device
       │                 │                  │
       └──────────────┬──┴──────────────────┘
                      ↓
                Identity Graph
                      ↓
              Claims / Credentials
                      ↓
                AXSECURITY
                      ↓
        Authentication / Authorization
```

Identity phải phân biệt rõ:

```text
identity
identifier
account
credential
authentication
authorization
role
attribute
claim
relationship
profile
legal status
device identity
service identity
```

---

# 728.1 — Identity Boundary

`AXIDENTITY` sở hữu:

```text
human identity
organization identity
device identity
service identity
identifiers
identity lifecycle
identity relationships
identity profiles
claims
credentials references
identity resolution
identity federation
identity mapping
identity recovery
identity revocation
identity events
identity graph
privacy-preserving identifiers
verifiable credentials
```

Không sở hữu:

```text
cryptographic primitive     → AXSECURITY
legal rule                  → AXLAW
civil registration fact     → AXCIVIL
government administration  → AXGOV
monetary account            → AXFINANCE
physical asset              → AXASSET
```

---

# 728.2 — Identity

```axiom
identity {
    identity_id
    identity_type
    lifecycle
    created_at
    updated_at
}
```

Types:

```text
HUMAN
ORGANIZATION
DEVICE
SERVICE
APPLICATION
AGENT
SYSTEM
GROUP
```

---

# 728.3 — Identity Is Not Account

```text
identity
    ≠
account
```

Một identity có thể có:

```text
0..N accounts
```

Ví dụ:

```text
Human Identity
 ├── government account
 ├── education account
 ├── banking account
 └── application account
```

Account là access representation.

Identity là entity/reference.

---

# 728.4 — Identifier

```axiom
identifier {
    identifier_id
    identity
    namespace
    value
    type
    status
}
```

Types:

```text
internal_id
public_id
government_id_reference
organization_id
device_id
service_id
email
phone_reference
username
URI
```

---

# 728.5 — Identifier Namespace

```axiom
identity_namespace {
    namespace_id
    name
    authority
    uniqueness_scope
}
```

Ví dụ:

```text
axiom://identity/...
government://...
organization://...
device://...
```

Identifier uniqueness phải có **scope rõ ràng**.

Không giả định mọi identifier đều globally unique.

---

# 728.6 — Identifier Lifecycle

```text
PROPOSED
ACTIVE
SUSPENDED
EXPIRED
REVOKED
RETIRED
```

Identifier bị retired không được tự động tái sử dụng nếu namespace policy cấm.

---

# 728.7 — Human Identity

```axiom
human_identity {
    identity
    civil_reference
    names
    birth_reference
    residency_references
    relationships
}
```

Thông tin pháp lý authoritative lấy từ `AXCIVIL`.

`AXIDENTITY` không tự tạo birth/death/marriage facts.

---

# 728.8 — Organization Identity

```axiom
organization_identity {
    identity
    legal_entity_reference
    names
    identifiers
    members
    roles
}
```

Legal existence thuộc domain pháp lý/civil tương ứng.

---

# 728.9 — Device Identity

```axiom
device_identity {
    identity
    hardware_reference
    manufacturer_reference
    model
    serial_reference
    attestation_reference
}
```

Device identity không đồng nghĩa:

```text
IP address
MAC address
hostname
```

---

# 728.10 — Service Identity

```axiom
service_identity {
    identity
    service_name
    publisher
    versions
    endpoints
}
```

Một service có thể thay đổi endpoint mà không thay đổi identity.

---

# 728.11 — Application Identity

```axiom
application_identity {
    identity
    package_id
    publisher
    artifact_reference
    version
}
```

Artifact integrity → `AXSECURITY`.

Identity → `AXIDENTITY`.

---

# 728.12 — Identity Lifecycle

```text
DISCOVERED
    ↓
CREATED
    ↓
ACTIVE
    ↓
SUSPENDED
    ↓
REACTIVATED
    ↓
REVOKED
    ↓
RETIRED
```

Một số identity type có lifecycle riêng.

---

# 728.13 — Identity Merge

Hai identity có thể được đề xuất merge:

```axiom
merge_identity_candidate(a, b)
```

Nhưng merge authoritative phải explicit.

```text
candidate
    ≠
confirmed identity merge
```

---

# 728.14 — Identity Split

Nếu một identity bị phát hiện chứa nhiều entities:

```axiom
split_identity(
    source,
    targets
)
```

Phải preserve provenance.

---

# 728.15 — Identity Resolution

```axiom
resolve_identity(
    identifier
)
```

Result:

```text
RESOLVED
AMBIGUOUS
NOT_FOUND
REVOKED
UNKNOWN
```

Không được tự động chọn một identity khi resolution ambiguous.

---

# 728.16 — Identity Matching

Có thể sử dụng:

```text
exact match
deterministic match
probabilistic match
human-reviewed match
```

Probabilistic matching phải giữ:

```text
confidence
evidence
algorithm_version
```

---

# 728.17 — Identity Match ≠ Identity Fact

```text
match_score = 0.97
```

không có nghĩa:

```text
identity relationship = authoritative
```

Một identity resolution engine không được tự biến prediction thành fact.

---

# 728.18 — Identity Relationship

```axiom
identity_relationship {
    relationship_id
    source
    target
    relationship_type
    validity
    provenance
}
```

Types:

```text
parent
guardian
child
spouse
member
employee
employer
owner
operator
administrator
representative
delegate
service_owner
device_owner
```

Semantic authority thuộc domain tương ứng.

---

# 728.19 — Relationship Provenance

Mỗi relationship quan trọng có:

```text
source
authority
effective_time
recorded_time
evidence
```

---

# 728.20 — Relationship Lifecycle

```text
PROPOSED
ACTIVE
SUSPENDED
EXPIRED
REVOKED
```

Temporal relationship phải hỗ trợ historical queries.

---

# 728.21 — Identity Graph

```axiom
identity_graph {
    nodes
    relationships
    versions
}
```

Ví dụ:

```text
Human
 ├── member_of → Organization
 ├── owns → Device
 ├── operates → Service
 └── represents → Organization
```

Graph là derived/queryable representation; authority vẫn nằm ở source domain.

---

# 728.22 — Identity Profile

```axiom
identity_profile {
    identity
    attributes
    preferences
    visibility
}
```

Profile không đồng nghĩa với legal record.

---

# 728.23 — Identity Attribute

```axiom
identity_attribute {
    name
    value
    source
    confidence
    valid_time
}
```

Attribute có thể là:

```text
language
timezone
contact preference
organization role
device capability
```

---

# 728.24 — Attribute Authority

Mỗi attribute phải biết:

```text
authoritative
verified
self_asserted
derived
inferred
```

---

# 728.25 — Identity Claim

```axiom
identity_claim {
    claim_id
    subject
    issuer
    claim_type
    value
    issued_at
    expires_at
    evidence
}
```

Ví dụ:

```text
"subject belongs to organization X"
```

---

# 728.26 — Claim Status

```text
VALID
EXPIRED
REVOKED
SUSPENDED
UNKNOWN
```

---

# 728.27 — Credential

```axiom
credential {
    credential_id
    subject
    issuer
    claims
    proof
    validity
}
```

Credential là evidence về claim, không phải identity itself.

---

# 728.28 — Verifiable Credential

```axiom
verifiable_credential {
    credential
    issuer_proof
    schema
    status_reference
}
```

Verification:

```axiom
verify_credential()
```

Result phải cho biết:

```text
cryptographically_valid
issuer_trusted
not_expired
not_revoked
schema_valid
```

---

# 728.29 — Credential Presentation

```axiom
credential_presentation {
    credentials
    requested_claims
    holder_proof
    purpose
}
```

Có thể chỉ reveal subset claims.

---

# 728.30 — Selective Disclosure

Ví dụ credential chứa:

```text
name
birth_date
nationality
address
```

Application chỉ cần:

```text
age_over_threshold
```

thì identity fabric có thể cung cấp minimal disclosure nếu credential/protocol hỗ trợ.

---

# 728.31 — Zero-Knowledge Capability

Architecture phải cho phép future cryptographic backend hỗ trợ:

```text
prove(attribute)
without
revealing(attribute)
```

Nhưng zero-knowledge primitive cụ thể thuộc `AXSECURITY`.

---

# 728.32 — Identity Federation

```axiom
identity_federation {
    local_namespace
    external_namespace
    trust_policy
    mapping
}
```

Có thể map:

```text
Axiom Identity
      ↕
External Identity Provider
```

---

# 728.33 — Federation Mapping

```axiom
identity_mapping {
    source_namespace
    source_identifier
    target_identity
    mapping_type
    confidence
    validity
}
```

---

# 728.34 — Federation Trust

External identity không tự động trở thành local authoritative identity.

Phải có:

```text
trust anchor
issuer
mapping policy
validation
```

---

# 728.35 — Authentication Reference

`AXIDENTITY` giữ authentication result reference:

```axiom
authentication_reference {
    session
    method
    assurance
    timestamp
}
```

Actual cryptographic verification:

→ `AXSECURITY`.

---

# 728.36 — Multi-Factor Identity

Identity session có thể yêu cầu:

```text
password
+
passkey
+
hardware factor
```

AXIDENTITY lưu assurance result.

AXSECURITY thực hiện factor verification.

---

# 728.37 — Identity Assurance

```text
IDENTITY_ASSURANCE:
    SELF_ASSERTED
    VERIFIED
    STRONGLY_VERIFIED
    HARDWARE_VERIFIED
```

Assurance không phải là "độ tốt" của identity; nó mô tả mức evidence verification.

---

# 728.38 — Delegated Identity

```axiom
identity_delegation {
    delegator
    delegate
    authority_scope
    starts_at
    expires_at
    revocation
}
```

Ví dụ:

```text
Organization
    ↓ delegate
Employee
    ↓
service operation
```

---

# 728.39 — Delegation ≠ Ownership

```text
delegate
    ≠
owner
```

Delegation không thay đổi ownership fact.

---

# 728.40 — Identity Impersonation Boundary

Có thể có:

```text
act_as
on_behalf_of
delegated_by
```

nhưng audit phải giữ cả:

```text
original principal
executing principal
delegation chain
```

---

# 728.41 — Service-to-Service Identity

```text
Service A
   ↓
authenticated channel
   ↓
Service B
```

B phải biết:

```text
caller = Service A
```

không chỉ:

```text
caller IP = 10.x.x.x
```

---

# 728.42 — Workload Identity

`AXCOMPUTE` workload có thể nhận:

```axiom
workload_identity {
    workload
    service_identity
    execution_environment
    expiry
}
```

Identity gắn với workload lifecycle.

---

# 728.43 — Device Enrollment

```axiom
enroll_device()
```

Flow:

```text
Device
 ↓
Identity Creation
 ↓
Attestation
 ↓
Credential Provisioning
 ↓
Policy Assignment
 ↓
ACTIVE
```

---

# 728.44 — Device Revocation

```axiom
revoke_device()
```

Khi revoked:

```text
credentials
sessions
delegations
network access
```

có thể bị invalidated theo policy.

---

# 728.45 — Identity Recovery

```axiom
identity_recovery {
    identity
    evidence
    recovery_method
    approvals
    result
}
```

Recovery phải không làm mất historical identity provenance.

---

# 728.46 — Account Recovery

Account recovery khác identity recovery:

```text
account recovery
    → restore access

identity recovery
    → resolve identity ownership/control
```

---

# 728.47 — Identity Revocation

```axiom
revoke_identity(identity)
```

Nhưng revocation semantics phải xác định rõ:

```text
identity
credentials
sessions
delegations
claims
relationships
```

cái nào bị ảnh hưởng.

Không được tự động xóa lịch sử.

---

# 728.48 — Historical Identity

Identity records phải hỗ trợ:

```axiom
identity_at(timestamp)
```

để giữ:

```text
past names
past organization membership
past roles
past identifiers
```

khi policy/legal domain yêu cầu retention.

---

# 728.49 — Name Changes

Tên thay đổi không tạo identity mới theo mặc định.

```text
Identity A
 ├── Name v1
 └── Name v2
```

Name change authority đến từ `AXCIVIL` hoặc domain phù hợp.

---

# 728.50 — Pseudonymous Identity

```axiom
pseudonymous_identity {
    source_identity
    domain
    pseudonym
    scope
}
```

Pseudonym:

```text
domain-specific
non-global
revocable
```

---

# 728.51 — Pairwise Identifier

Hai service không nhất thiết nhìn thấy cùng identifier:

```text
User
 ├── Service A → ID-A
 ├── Service B → ID-B
 └── Service C → ID-C
```

Giúp giảm unnecessary cross-service correlation.

---

# 728.52 — Anonymous Session

Hệ thống có thể hỗ trợ:

```text
anonymous principal
```

nhưng anonymous không đồng nghĩa:

```text
untraceable
```

Audit/privacy policy quyết định metadata nào được giữ.

---

# 728.53 — Privacy-Preserving Identity

Identity API phải hỗ trợ:

```text
minimal disclosure
purpose-bound identifiers
selective disclosure
pseudonyms
pairwise identifiers
attribute proofs
```

---

# 728.54 — Identity Search

```axiom
search_identity(
    query,
    scope,
    purpose
)
```

Result:

```text
exact
candidate
ambiguous
not_found
```

Search result không mặc nhiên được coi là identity resolution.

---

# 728.55 — Identity Merge Approval

Các merge có ảnh hưởng lớn phải hỗ trợ:

```text
automatic
policy_approved
human_reviewed
multi_party_approved
```

---

# 728.56 — Identity Conflict

```axiom
identity_conflict {
    candidates
    evidence
    conflicting_attributes
    resolution_state
}
```

States:

```text
OPEN
UNDER_REVIEW
RESOLVED
REJECTED
```

---

# 728.57 — Identity Evidence

```axiom
identity_evidence {
    evidence_id
    type
    source
    collected_at
    integrity
    confidence
}
```

Evidence có thể là:

```text
signed document reference
credential
device attestation
verified registry reference
user assertion
organizational assertion
```

---

# 728.58 — Evidence ≠ Fact

```text
evidence
   ↓
verification
   ↓
claim
   ↓
authoritative identity state
```

Không bỏ qua verification layer.

---

# 728.59 — Organizational Membership

```axiom
membership {
    person
    organization
    role
    starts_at
    ends_at
    authority
}
```

Membership phải temporal.

---

# 728.60 — Role

```axiom
identity_role {
    role_id
    identity
    role_type
    scope
    validity
}
```

Role không tự động đồng nghĩa security capability.

Ví dụ:

```text
role = teacher
```

không tự động:

```text
database.admin
```

---

# 728.61 — Attribute-Based Identity

Policy có thể dùng:

```text
identity attributes
+
environment
+
resource
```

Ví dụ:

```text
organization == X
AND role == operator
AND device_assurance >= HIGH
```

→ `AXSECURITY` quyết định authorization.

---

# 728.62 — Identity Event

```axiom
identity_event {
    event_id
    identity
    type
    timestamp
    actor
    source
    previous_state
    new_state
}
```

Events:

```text
IDENTITY_CREATED
IDENTITY_UPDATED
IDENTIFIER_ADDED
IDENTIFIER_REVOKED
IDENTITY_SUSPENDED
IDENTITY_REACTIVATED
IDENTITY_REVOKED
IDENTITY_RETIRED

RELATIONSHIP_CREATED
RELATIONSHIP_UPDATED
RELATIONSHIP_REVOKED

CREDENTIAL_ISSUED
CREDENTIAL_REVOKED

DELEGATION_CREATED
DELEGATION_REVOKED

DEVICE_ENROLLED
DEVICE_REVOKED

IDENTITY_MERGE
IDENTITY_SPLIT
IDENTITY_RECOVERY
```

---

# 728.63 — Identity Event Sourcing

Identity lifecycle có thể được reconstruct:

```text
event 1
 ↓
event 2
 ↓
event 3
 ↓
snapshot
```

Nhưng:

```text
identity event sourcing
    ≠
AXDATABASE CDC
```

CDC vận chuyển database changes.

Identity events biểu diễn semantic identity changes.

---

# 728.64 — Identity Snapshot

```axiom
identity_snapshot {
    identity
    version
    state
    generated_at
}
```

Snapshot là projection có thể rebuild từ authoritative events khi architecture yêu cầu.

---

# 728.65 — Cross-Domain Identity Reference

Các domain chỉ nên giữ:

```axiom
identity_reference {
    identity_id
}
```

thay vì copy toàn bộ identity profile.

Ví dụ:

```text
AXEDUCATION
   ↓
student.identity_id

AXTRANSPORT
   ↓
driver.identity_id

AXFINANCE
   ↓
account_holder.identity_id
```

---

# 728.66 — Identity Reference Stability

Domain reference phải survive:

```text
name change
address change
profile update
credential rotation
```

---

# 728.67 — Identity Deletion

Không mặc định physical-delete identity.

Thay vào đó:

```text
ACTIVE
 ↓
RETIRED
```

Historical references vẫn có thể tồn tại theo retention policy.

---

# 728.68 — Privacy Deletion

Khi privacy policy yêu cầu xóa dữ liệu:

```text
identity
 ├── authoritative records
 ├── derived projections
 ├── credentials
 ├── indexes
 └── caches
```

phải xác định từng loại dữ liệu có được xóa, anonymize hoặc retain vì legal/operational requirement.

---

# 728.69 — Identity Cache

```axiom
identity_cache {
    identity
    version
    expiry
}
```

Cache không trở thành authority.

---

# 728.70 — Offline Identity

Edge device có thể cache:

```text
identity references
credentials
verification keys
policy snapshots
```

Nhưng offline verification phải expose:

```text
freshness
revocation freshness
trust state
```

---

# 728.71 — Offline Verification

Result:

```text
VERIFIED_CURRENT
VERIFIED_STALE
VERIFIED_OFFLINE
UNVERIFIED
REVOKED
UNKNOWN
```

`VERIFIED_OFFLINE` không được trình bày như equivalent với online-current verification nếu revocation state có thể thay đổi.

---

# 728.72 — Identity Synchronization

```text
Local Identity State
        ↓
Identity Events
        ↓
Network
        ↓
Remote Identity State
```

Conflict resolution:

```text
domain policy
authority
version
causal ordering
human review
```

---

# 728.73 — Causal Identity Updates

Events có thể chứa:

```axiom
causal_reference {
    parent_events
    source_version
}
```

để phát hiện concurrent updates.

---

# 728.74 — Identity Digital Twin

```axiom
identity_digital_twin {
    identities
    identifiers
    relationships
    credentials
    delegations
    policies
}
```

Dùng để mô phỏng:

```text
identity lifecycle
organization restructuring
credential rotation
delegation
revocation
federation
privacy exposure
```

---

# 728.75 — Identity Simulation

```axiom
simulate_identity()
```

Có thể hỏi:

```text
what identities are affected?
what credentials become invalid?
what delegations survive?
what services lose access?
```

Simulation không thay đổi production state.

---

# 728.76 — AI Identity Resolution

AI có thể:

```text
match candidates
detect duplicate identities
extract identity attributes
detect anomalous relationships
suggest merge
suggest profile normalization
```

AI output phải có:

```text
confidence
evidence
model_version
timestamp
```

---

# 728.77 — AI Identity Boundary

AI không được tự động:

```text
create authoritative identity
merge legal identities
revoke identity
grant legal status
change civil relationship
```

trừ khi một explicit authorized workflow đã định nghĩa operation đó.

---

# 728.78 — Identity Security Integration

```text
AXIDENTITY
    ↓
Identity / Claims / Relationships
    ↓
AXSECURITY
    ↓
Authentication / Cryptography / Authorization
```

Không duplicate key management trong AXIDENTITY.

---

# 728.79 — Identity + AXCIVIL

```text
AXCIVIL
    ↓ authoritative civil fact
AXIDENTITY
    ↓ identity representation/reference
AXSECURITY
    ↓ authentication/trust
```

Ví dụ:

```text
birth record
    ≠
login credential
    ≠
identity identifier
```

---

# 728.80 — Identity + AXGOV

Government service có thể:

```text
resolve identity
verify credential
check authority
```

Nhưng `AXGOV` sở hữu administrative workflow.

---

# 728.81 — Identity + AXFINANCE

Financial account:

```text
financial_account
    → identity_reference
```

Identity không sở hữu:

```text
balance
ledger
settlement
```

---

# 728.82 — Identity + AXPROPERTY

Property ownership:

```text
AXPROPERTY
    → ownership relation
```

AXIDENTITY chỉ cung cấp identity references.

Không để identity graph tự suy ra ownership legal fact.

---

# 728.83 — Identity + AXASSET

Asset custody:

```text
asset
 ↓
custodian identity reference
```

Asset lifecycle thuộc `AXASSET`.

---

# 728.84 — Identity + AXNETWORK

Network access:

```text
identity
 ↓
authentication
 ↓
capability
 ↓
network policy
```

IP address không thay thế identity.

---

# 728.85 — Identity + AXDATABASE

Database có thể lưu:

```axiom
owner: identity_reference
created_by: identity_reference
updated_by: identity_reference
```

Database không duplicate toàn bộ identity object.

---

# 728.86 — Native APIs

```axiom
create_identity()
get_identity()
update_identity()
retire_identity()

create_identifier()
resolve_identifier()
revoke_identifier()

search_identity()
match_identity()

create_relationship()
update_relationship()
revoke_relationship()

create_profile()
update_profile()

create_claim()
verify_claim()
revoke_claim()

issue_credential()
verify_credential()
present_credential()
revoke_credential()

create_delegation()
revoke_delegation()

enroll_device()
verify_device()
revoke_device()

create_service_identity()
create_application_identity()

authenticate_reference()

resolve_identity_conflict()
merge_identity()
split_identity()

recover_identity()
recover_account()

create_pseudonym()
create_pairwise_identifier()

sync_identity()
replay_identity()
snapshot_identity()

simulate_identity()
create_identity_digital_twin()

audit_identity_event()
```

---

# 728.87 — Canonical Identity Creation

```text
Identity Request
       ↓
Validate
       ↓
Resolve Namespace
       ↓
Generate Identity ID
       ↓
Create Initial State
       ↓
Attach Identifiers
       ↓
Record Provenance
       ↓
Identity Event
       ↓
Projection
```

---

# 728.88 — Canonical Credential Flow

```text
Issuer
 ↓
Identity Resolution
 ↓
Claim Verification
 ↓
Credential Creation
 ↓
Cryptographic Proof
 ↓
Credential Registry/Status
 ↓
Holder
 ↓
Presentation
 ↓
Verifier
```

---

# 728.89 — Canonical Federated Login

```text
External Identity Provider
          ↓
Authentication
          ↓
Credential / Assertion
          ↓
AXSECURITY Verification
          ↓
AXIDENTITY Mapping
          ↓
Local Identity
          ↓
Local Security Context
```

---

# 728.90 — Canonical Delegation

```text
Principal A
 ↓
Delegation Policy
 ↓
Capability / Identity Authority
 ↓
Principal B
 ↓
Restricted Scope
 ↓
Expiry
 ↓
Audit
```

---

# 728.91 — Canonical Identity Recovery

```text
Recovery Request
 ↓
Identity Resolution
 ↓
Evidence Collection
 ↓
Evidence Verification
 ↓
Policy
 ↓
Approval
 ↓
Credential Reissue
 ↓
Old Credential Revocation
 ↓
Audit
```

---

# 728.92 — Formal Invariants

```text
ID-INV-01   Every identity has a stable identity ID.
ID-INV-02   Identity IDs are independent of mutable profile data.
ID-INV-03   Identifier uniqueness scope is explicit.
ID-INV-04   Identity and account are distinct concepts.
ID-INV-05   Identity and credential are distinct concepts.
ID-INV-06   Authentication does not imply identity ownership.
ID-INV-07   Authentication does not imply authorization.
ID-INV-08   Identity lifecycle state is explicit.
ID-INV-09   Identity history cannot be silently rewritten.
ID-INV-10   Retired identity references remain resolvable when policy requires.

ID-INV-11   Identity relationships have explicit type.
ID-INV-12   Relationships have explicit validity.
ID-INV-13   Relationship provenance is preserved.
ID-INV-14   Delegation does not imply ownership.
ID-INV-15   Delegation cannot silently expand authority.
ID-INV-16   Identity merge preserves provenance.
ID-INV-17   Identity split preserves provenance.
ID-INV-18   Ambiguous identity resolution cannot silently select a candidate.
ID-INV-19   Probabilistic matching is distinguishable from authoritative resolution.
ID-INV-20   AI identity matching cannot directly create authoritative identity state.

ID-INV-21   Claims identify their issuer.
ID-INV-22   Credentials identify their subject.
ID-INV-23   Credential validity is independently verifiable.
ID-INV-24   Revoked credentials cannot be reported as valid.
ID-INV-25   Expired credentials cannot be reported as current.
ID-INV-26   Federation mappings have explicit trust policy.
ID-INV-27   External identity is not automatically local authority.
ID-INV-28   Identity assurance is explicit.
ID-INV-29   Offline verification exposes freshness.
ID-INV-30   Cached identity state is not automatically authoritative.

ID-INV-31   Identity references do not require duplicating identity profiles.
ID-INV-32   Identity deletion semantics distinguish retirement, anonymization, and destruction.
ID-INV-33   Privacy-preserving identifiers are scope-bound.
ID-INV-34   Pairwise identifiers cannot silently become global identifiers.
ID-INV-35   Sensitive identity attributes require explicit access policy.
ID-INV-36   Identity audit records preserve actor and event provenance.
ID-INV-37   Identity simulation cannot mutate production state.
ID-INV-38   Identity replay cannot create production side effects.
ID-INV-39   Civil/legal facts cannot be inferred solely from identity graph structure.
ID-INV-40   Identity security operations delegate cryptographic authority to AXSECURITY.
```

---

# 728.93 — Performance Architecture

Identity resolution phải có fast path:

```text
identifier
    ↓
namespace lookup
    ↓
identity cache
    ↓
stable identity reference
```

không:

```text
identifier
 ↓
generic object graph
 ↓
reflection
 ↓
full profile hydration
```

---

# 728.94 — Compile-Time Identity References

Domain schema có thể khai báo:

```axiom
owner: identity
created_by: identity
operator: identity
```

Compiler biết đây là typed identity reference.

Không cần runtime string lookup cho common path.

---

# 728.95 — Identity Graph Index

Index có thể tối ưu:

```text
identity → relationships
relationship type → identities
organization → members
device → owner
service → publisher
```

Graph projection có thể rebuild từ authoritative identity events.

---

# 728.96 — Security Fast Path

Common operation:

```text
identity_id
 ↓
cached assurance
 ↓
capability
 ↓
AXSECURITY policy
```

Không hydrate toàn bộ identity profile.

---

# 728.97 — Completion Criteria

`BOOTSTRAP-728` phải freeze:

1. Identity.
2. Identifier.
3. Namespace.
4. Human identity.
5. Organization identity.
6. Device identity.
7. Service identity.
8. Application identity.
9. Identity lifecycle.
10. Identity merge.
11. Identity split.
12. Identity resolution.
13. Identity matching.
14. Identity relationships.
15. Identity graph.
16. Identity profile.
17. Identity attributes.
18. Attribute authority.
19. Claims.
20. Credentials.
21. Verifiable credentials.
22. Credential presentation.
23. Selective disclosure.
24. Zero-knowledge extension point.
25. Federation.
26. Federation mapping.
27. Trust boundaries.
28. Authentication references.
29. Identity assurance.
30. Delegated identity.
31. Impersonation boundary.
32. Service identity.
33. Workload identity.
34. Device enrollment.
35. Device revocation.
36. Identity recovery.
37. Account recovery distinction.
38. Identity revocation.
39. Historical identity.
40. Name-change semantics.
41. Pseudonymous identity.
42. Pairwise identifiers.
43. Anonymous sessions.
44. Privacy-preserving identity.
45. Identity search.
46. Identity conflicts.
47. Evidence.
48. Evidence verification.
49. Organizational membership.
50. Roles.
51. Attribute-based identity.
52. Identity events.
53. Identity snapshots.
54. Cross-domain references.
55. Identity synchronization.
56. Offline verification.
57. Identity digital twin.
58. Identity simulation.
59. AI identity boundary.
60. AXSECURITY integration.
61. AXCIVIL integration.
62. AXGOV integration.
63. AXFINANCE integration.
64. AXPROPERTY integration.
65. AXASSET integration.
66. AXNETWORK integration.
67. AXDATABASE integration.
68. Native APIs.
69. Formal invariants.
70. Native performance architecture.

---

# 728.98 — Definition of Done

```text
BOOTSTRAP-728
STATUS: COMPLETE / FROZEN

AXIDENTITY 2.0
    ├── Human Identity
    ├── Organization Identity
    ├── Device Identity
    ├── Service Identity
    ├── Application Identity
    ├── Identifier Fabric
    ├── Identity Lifecycle
    ├── Identity Graph
    ├── Relationships
    ├── Claims
    ├── Verifiable Credentials
    ├── Federation
    ├── Delegation
    ├── Identity Resolution
    ├── Privacy-Preserving Identity
    ├── Device Enrollment
    ├── Identity Recovery
    ├── Identity Synchronization
    ├── Offline Verification
    ├── Identity Events
    ├── Identity Digital Twin
    ├── AI Identity Boundary
    └── AXSECURITY Integration
```

**BOOTSTRAP-728 / AXIDENTITY 2.0 — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-729 — AXAI

**Native AI & Machine Intelligence Runtime — tensors, models, datasets, inference, training, automatic differentiation, CPU/GPU/NPU execution, graph compilation, quantization, mixed precision, distributed training, checkpointing, embeddings, vector generation, multimodal data, model registry, model versioning, evaluation, reproducibility, AI agents, tool execution, model safety boundaries, provenance, AI-assisted programming, privacy-preserving inference, AI simulation & AI Runtime 5.0.**