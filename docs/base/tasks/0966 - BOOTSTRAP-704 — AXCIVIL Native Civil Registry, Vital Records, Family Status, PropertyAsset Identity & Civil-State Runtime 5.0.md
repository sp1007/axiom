# BOOTSTRAP-704 — AXCIVIL: Native Civil Registry, Vital Records, Family Status, Property/Asset Identity & Civil-State Runtime 5.0

**Namespace:** `AXCIVIL`  
**Phase:** Axiom Civilization Runtime / Civil-State Infrastructure  
**Status:** ARCHITECTURAL BASELINE — FROZEN TARGET  
**Depends on:** `AXIDENTITY`, `AXLAW`, `AXJUSTICE`, `AXCORRECTIONS`

---

## 704.0 — Mục tiêu

`AXCIVIL` là runtime native của Axiom dùng để quản lý **civil-state facts và civil registries** của một xã hội.

Nó cung cấp nền tảng cho:

```text
Birth
Death
Marriage
Divorce
Parentage
Guardianship
Adoption
Name Change
Civil Status
Residency
Household
Property Identity
Asset Registration
Certificates
Civil Documents
```

`AXCIVIL` không tự tạo ra luật.

Nó thực thi các quy tắc và authority được cung cấp bởi:

```text
AXLAW
```

và sử dụng identity infrastructure của:

```text
AXIDENTITY
```

---

# 704.1 — Core Principle

Nguyên tắc nền tảng:

> **Civil registry records facts and legally recognized states; it does not invent them.**

Do đó:

```text
AXLAW
   ↓
Civil Authority
   ↓
AXCIVIL
   ↓
Civil Record
```

Không:

```text
AXCIVIL
   ↓
invent legal status
   ↓
modify rights
```

nếu không có authority tương ứng.

---

# 704.2 — Civil-State Model

Civil state phải được biểu diễn dưới dạng các facts có provenance:

```axiom
civil_fact {
    fact_id
    subject
    type
    value
    jurisdiction
    authority
    effective_time
    recorded_time
    provenance
    status
}
```

Một fact không chỉ là:

```text
married = true
```

mà phải chứa:

```text
who
what
when
where
under which authority
from which source
```

---

# 704.3 — Fact vs Derived State

Phải phân biệt:

```text
registered_fact
derived_state
application_result
```

Ví dụ:

```text
birth_record
    ↓
age = derived_state
```

hoặc:

```text
marriage_record
+
divorce_record
    ↓
current_marital_status
```

Derived state có thể được tính lại từ authoritative facts.

---

# 704.4 — Vital Records

Core registry phải hỗ trợ:

```text
BIRTH
DEATH
MARRIAGE
DIVORCE
STILLBIRTH
ADOPTION
```

Các loại bổ sung phải được mở rộng bằng registry type system, không hard-code compiler.

---

# 704.5 — Birth Record

Canonical structure:

```axiom
birth_record {
    record_id
    child
    date_time
    place
    jurisdiction
    parentage
    registration_authority
    registration_time
    status
}
```

Phải hỗ trợ:

```text
single birth
multiple birth
delayed registration
amended registration
foreign birth registration
```

---

# 704.6 — Parentage

Parentage là relationship có provenance:

```axiom
parentage {
    child
    parent
    relationship_type
    authority
    effective_time
    evidence
    status
}
```

Không được suy ra parentage chỉ từ:

```text
co-residence
surname
genetic similarity
```

nếu pháp luật yêu cầu một thủ tục hoặc authority cụ thể.

---

# 704.7 — Parentage Types

Runtime phải hỗ trợ extensible relationship types:

```text
LEGAL_PARENT
BIOLOGICAL_PARENT
ADOPTIVE_PARENT
GUARDIAN
OTHER_LEGAL_RELATION
```

Các semantics khác nhau phải được giữ riêng.

---

# 704.8 — Death Record

```axiom
death_record {
    record_id
    subject
    date_time
    place
    jurisdiction
    registering_authority
    status
}
```

Death record phải có provenance rõ ràng.

Không cho phép application tùy tiện chuyển:

```text
ACTIVE_PERSON
→ DEAD
```

mà không qua authorized transition.

---

# 704.9 — Identity State Boundary

`AXCIVIL` không sở hữu toàn bộ identity.

Boundary:

```text
AXIDENTITY
    ↓
Identity
    ↓
AXCIVIL
    ↓
Civil Status
```

Ví dụ:

```text
person_id
```

thuộc identity system.

Trong khi:

```text
birth_record
marriage_record
death_record
```

thuộc civil registry.

---

# 704.10 — Name Model

Tên phải được model như temporal records:

```axiom
name_record {
    subject
    name
    type
    valid_from
    valid_to
    authority
    status
}
```

Hỗ trợ:

```text
birth name
legal name
preferred name
former name
alias
```

Không được overwrite lịch sử tên.

---

# 704.11 — Name Change

Lifecycle:

```text
REQUESTED
    ↓
REVIEW
    ↓
AUTHORIZED
    ↓
REGISTERED
    ↓
EFFECTIVE
```

Nếu bị từ chối:

```text
REQUESTED
    ↓
DENIED
```

Không được tạo civil fact mới trước authorization.

---

# 704.12 — Marriage Model

Marriage phải là relationship entity:

```axiom
marriage {
    marriage_id
    parties
    jurisdiction
    ceremony_time
    registration_time
    authority
    status
}
```

Status:

```text
PROPOSED
REGISTERED
ACTIVE
TERMINATED
VOIDED
```

Các status phải có semantics pháp lý riêng.

---

# 704.13 — Marriage Invariants

Runtime phải ngăn các state transition không hợp lệ theo rule set hiện hành.

Ví dụ:

```text
cannot terminate non-existing marriage
cannot modify finalized registration without amendment
cannot create duplicate canonical registration
```

Các rule cụ thể thuộc jurisdiction layer.

---

# 704.14 — Divorce

Divorce không phải đơn giản:

```text
married = false
```

Mà là authoritative event:

```axiom
divorce_record {
    divorce_id
    marriage_id
    authority
    effective_time
    registration_time
    consequences
    status
}
```

---

# 704.15 — Civil Status

Current status phải là derived projection:

```text
civil_facts
    ↓
status engine
    ↓
current civil status
```

Ví dụ:

```text
SINGLE
MARRIED
DIVORCED
WIDOWED
```

Danh sách status không được hard-code thành một enum toàn cầu nếu jurisdiction có semantics khác.

---

# 704.16 — Adoption

Adoption phải được model như legal relationship transition:

```text
existing parentage state
        ↓
adoption authority
        ↓
new legal parentage state
```

Historical relationship không được xóa vật lý.

---

# 704.17 — Guardianship

```axiom
guardianship {
    guardian
    ward
    authority
    scope
    start
    end
    limitations
    status
}
```

Scope có thể giới hạn:

```text
education
medical
financial
legal
general
```

---

# 704.18 — Household

Household là derived/social structure, không mặc định đồng nghĩa với legal family.

```axiom
household {
    household_id
    members
    residence
    effective_period
    source
}
```

Không được suy ra:

```text
same household → parent
same household → spouse
```

---

# 704.19 — Residency

Residency phải là temporal relationship:

```axiom
residency {
    subject
    location
    type
    valid_from
    valid_to
    authority
}
```

Hỗ trợ:

```text
primary residence
temporary residence
registered residence
historical residence
```

---

# 704.20 — Address Model

Address phải là structured data:

```text
country
region
district
locality
street
building
unit
postal_code
```

Không phụ thuộc vào một quốc gia cụ thể.

---

# 704.21 — Property Registry

`AXCIVIL` phải cung cấp abstraction cho property identity:

```axiom
property {
    property_id
    property_type
    jurisdiction
    location
    identifiers
    status
}
```

Property không nhất thiết là real estate.

Có thể có:

```text
LAND
BUILDING
VEHICLE
VESSEL
AIRCRAFT
REGISTERED_ASSET
```

Các specialized registries có thể xây trên core.

---

# 704.22 — Property vs Ownership

Phải tách:

```text
Property
Ownership
Possession
UseRight
Lien
Restriction
```

Không được:

```text
owner == possessor
```

mặc định.

---

# 704.23 — Ownership Model

```axiom
ownership {
    asset
    owner
    share
    authority
    valid_from
    valid_to
    status
}
```

Phải hỗ trợ:

```text
single owner
joint ownership
fractional ownership
corporate ownership
trust-like structures
```

theo jurisdiction rules.

---

# 704.24 — Asset Encumbrance

Asset có thể có:

```text
LIEN
MORTGAGE
LEASE
RESTRICTION
COURT_HOLD
TAX_HOLD
TRANSFER_BLOCK
```

Mỗi restriction phải có authority và lifecycle.

---

# 704.25 — Transfer Model

Asset transfer:

```text
PROPOSED
    ↓
AUTHORIZED
    ↓
EXECUTED
    ↓
REGISTERED
```

Registry phải phân biệt:

```text
contract
transaction
registration
ownership_effect
```

---

# 704.26 — Registration Principle

Một transaction và một registered state không nhất thiết là cùng một thứ.

```text
agreement
    ↓
transaction
    ↓
registration
    ↓
civil/property state
```

Điều này cho phép jurisdiction-specific registration semantics.

---

# 704.27 — Certificate Model

Certificates là signed projections của authoritative records:

```axiom
certificate {
    certificate_id
    subject
    record_reference
    issuer
    issued_at
    valid_until
    content_hash
    signature
}
```

Certificate không phải source of truth.

Source of truth là registry record.

---

# 704.28 — Digital Certificate

Certificate phải có:

```text
issuer
signature
algorithm
key_reference
issued_at
expiration
revocation
content_hash
```

Verification phải không phụ thuộc vào issuer UI.

---

# 704.29 — Amendment Model

Civil records có thể cần amendment.

Không được:

```text
UPDATE birth_record SET ...
```

theo nghĩa destructive mutation.

Phải:

```text
original_record
    ↓
amendment_request
    ↓
authorization
    ↓
amendment_event
    ↓
new_projection
```

---

# 704.30 — Correction vs Amendment

Phải phân biệt:

```text
CORRECTION
```

với:

```text
AMENDMENT
```

Correction sửa lỗi dữ liệu.

Amendment thay đổi legal/civil state theo authority.

---

# 704.31 — Historical Integrity

Registry phải cho phép:

```text
state_at(time)
```

Ví dụ:

```text
marital_status_at(t)
residency_at(t)
ownership_at(t)
guardianship_at(t)
```

Không chỉ:

```text
current_state
```

---

# 704.32 — Temporal Model

Mỗi civil fact có:

```text
effective_time
recorded_time
authority_time
```

Tương tự `AXCORRECTIONS`, phải phân biệt:

```text
when event occurred
when it became legally effective
when system recorded it
```

---

# 704.33 — Jurisdiction

Civil rules phải được scoped:

```axiom
jurisdiction {
    jurisdiction_id
    parent
    legal_system
    authority
    rule_version
}
```

Ví dụ:

```text
country
region
province
municipality
special jurisdiction
```

---

# 704.34 — Cross-Jurisdiction Registration

Phải hỗ trợ:

```text
foreign birth
foreign marriage
foreign divorce
foreign death
foreign property
```

Nhưng:

```text
foreign_record
```

không tự động trở thành:

```text
domestic_authoritative_record
```

Cần recognition/registration process.

---

# 704.35 — Recognition Model

```axiom
recognition {
    source_record
    target_jurisdiction
    authority
    effective_time
    scope
    status
}
```

---

# 704.36 — Duplicate Detection

Registry phải phát hiện khả năng duplicate:

```text
same identity
same event
same jurisdiction
same temporal window
```

Nhưng duplicate detection chỉ tạo:

```text
POTENTIAL_DUPLICATE
```

không tự động xóa record.

---

# 704.37 — Identity Resolution Boundary

Resolution engine có thể:

```text
match
probable_match
possible_match
no_match
```

Không được tự động merge identities khi confidence không đạt policy threshold.

---

# 704.38 — Civil Event Ledger

Mọi legally significant civil transition phải có immutable event:

```text
BIRTH_REGISTERED
DEATH_REGISTERED
MARRIAGE_REGISTERED
DIVORCE_REGISTERED
PARENTAGE_ESTABLISHED
PARENTAGE_CHANGED
ADOPTION_REGISTERED
GUARDIANSHIP_CREATED
NAME_CHANGED
RESIDENCY_REGISTERED
PROPERTY_REGISTERED
OWNERSHIP_TRANSFERRED
```

---

# 704.39 — Event Provenance

Mỗi event:

```axiom
civil_event {
    event_id
    event_type
    subject
    authority
    issuer
    source
    effective_time
    recorded_time
    payload_hash
    previous_event
}
```

---

# 704.40 — No Silent Mutation

Invariant:

```text
No authoritative civil state may change without an auditable event.
```

---

# 704.41 — Access Control

Capabilities:

```text
civil.read
civil.register
civil.amend
civil.certify
civil.verify
civil.recognize
civil.revoke
civil.audit
```

Phải có scope:

```text
jurisdiction
record_type
subject
time
purpose
```

---

# 704.42 — Least Privilege

Không được:

```text
civil_admin → everything
```

mà:

```text
birth_officer
marriage_officer
property_officer
certificate_officer
auditor
```

có capabilities khác nhau.

---

# 704.43 — Privacy

Civil registry có thể chứa dữ liệu cực kỳ nhạy cảm.

Partition:

```text
identity
vital_records
family
residency
property
financial_reference
restricted_records
```

Một consumer chỉ nhận projection cần thiết.

---

# 704.44 — Restricted Records

Một record có thể:

```text
PUBLIC
LIMITED
CONFIDENTIAL
RESTRICTED
SEALED
```

Classification không thay đổi source record.

---

# 704.45 — Data Minimization

API phải ưu tiên:

```text
purpose-specific projection
```

thay vì:

```text
return entire person record
```

Ví dụ:

```text
verify_birth()
```

có thể trả:

```text
valid = true
```

thay vì toàn bộ birth record.

---

# 704.46 — Verification API

Core verification APIs:

```axiom
verify_identity()
verify_birth()
verify_death()
verify_marriage()
verify_divorce()
verify_parentage()
verify_guardianship()
verify_residency()
verify_property()
verify_certificate()
```

Kết quả phải có provenance.

---

# 704.47 — Proof Model

Verification result:

```axiom
verification_result {
    claim
    status
    source
    authority
    verified_at
    rule_version
}
```

Status:

```text
VERIFIED
NOT_VERIFIED
UNKNOWN
REVOKED
CONFLICT
```

Không dùng:

```text
false
```

cho mọi trường hợp không xác minh được.

---

# 704.48 — Conflict Resolution

Nếu có:

```text
Record A
Record B
```

mâu thuẫn, system tạo:

```text
CIVIL_RECORD_CONFLICT
```

và giữ cả provenance.

Không silently overwrite.

---

# 704.49 — Legal Hold

Civil record có thể bị:

```text
LEGAL_HOLD
```

Khi active:

```text
destructive_operation → denied
```

---

# 704.50 — Retention

Retention policy phải hỗ trợ:

```text
ACTIVE
ARCHIVED
RESTRICTED
SEALED
RETAINED_INDEFINITELY
```

Các record có giá trị lịch sử/legal phải giữ immutable history.

---

# 704.51 — Deletion Boundary

Không cho phép delete authoritative civil history chỉ vì application request.

Nếu luật cho phép destruction:

```text
destruction_authority
+
retention_check
+
legal_hold_check
+
audit_event
```

bắt buộc.

---

# 704.52 — Document Storage

Civil documents có thể nằm ở document store riêng.

Registry chỉ giữ:

```text
document_id
hash
type
issuer
relationship
```

Không nhúng binary lớn vào authoritative civil event.

---

# 704.53 — Digital Signatures

Authority-issued records có thể sử dụng:

```text
digital signature
certificate chain
timestamp
revocation
```

Signature verification phải độc lập với UI/application.

---

# 704.54 — Offline Registry Node

Local registry node có thể hoạt động offline với:

```text
pre-authorized operations
```

Nhưng không được tạo authority mới.

Khi reconnect:

```text
local event
→ validation
→ causal ordering
→ central registration
```

---

# 704.55 — Distributed Consistency

Mỗi event phải có:

```text
event_id
command_id
transaction_id
causal_parent
authority
```

Canonical state phải deterministic.

---

# 704.56 — Idempotency

Các command:

```text
register_birth
register_marriage
register_death
register_divorce
register_property
transfer_property
issue_certificate
```

phải idempotent theo command ID.

---

# 704.57 — Replay

Required API:

```axiom
civil.replay(subject, timestamp)
civil.replay(property, timestamp)
civil.replay(record, timestamp)
```

Kết quả phải tái tạo được historical state.

---

# 704.58 — Simulation

Phải hỗ trợ:

```axiom
simulate_marriage()
simulate_divorce()
simulate_property_transfer()
simulate_guardianship()
simulate_registration()
```

Simulation không mutate registry.

---

# 704.59 — AI Assistance

AI có thể:

```text
document classification
OCR
translation
duplicate detection
record linkage
anomaly detection
workflow routing
form completion
```

Nhưng:

```text
AI suggestion != civil fact
AI match != identity merge
AI extraction != authoritative registration
```

---

# 704.60 — AI Provenance

AI-generated extraction phải lưu:

```text
model
version
input_document
output
confidence
timestamp
human_verification
```

Nếu chưa được verify:

```text
status = UNVERIFIED
```

---

# 704.61 — Human Verification

Các high-impact changes có thể yêu cầu:

```text
SINGLE_REVIEW
DUAL_REVIEW
AUTHORIZED_OFFICER
LEGAL_AUTHORITY
```

Policy thuộc jurisdiction.

---

# 704.62 — AI Prompt Injection

Civil documents phải được coi là:

```text
UNTRUSTED_DATA
```

Một document có nội dung:

```text
"ignore system rules"
```

không được biến thành executable instruction.

AI layer phải tách:

```text
document content
system instruction
authority
command
```

---

# 704.63 — Security Invariants

```text
No capability → no registry mutation.

No authority → no legally significant registration.

No provenance → no authoritative fact.

Revoked authority → no new action.

Expired authorization → denial.

Historical events → immutable.

AI output → non-authoritative until verified.
```

---

# 704.64 — Property Registry Security

Ownership changes phải đặc biệt bảo vệ:

```text
create_transfer
authorize_transfer
register_transfer
revoke_transfer
```

Mỗi transition phải có explicit authority.

---

# 704.65 — Asset Identity

Asset ID phải stable:

```text
asset_id
```

không thay đổi chỉ vì:

```text
owner changes
location changes
name changes
status changes
```

---

# 704.66 — Asset Lifecycle

```text
UNREGISTERED
    ↓
REGISTERED
    ↓
ACTIVE
    ↓
RESTRICTED
    ↓
TRANSFER_PENDING
    ↓
TRANSFERRED
    ↓
RETIRED
```

Jurisdiction có thể mở rộng state machine.

---

# 704.67 — Ownership History

Không được:

```text
owner = Bob
```

ghi đè Alice.

Phải:

```text
Alice ownership
      ↓
transfer event
      ↓
Bob ownership
```

Historical ownership phải replayable.

---

# 704.68 — Civil Graph

Civil relationships nên được biểu diễn thành graph:

```text
Person
 ├── parent_of
 ├── child_of
 ├── spouse_of
 ├── guardian_of
 ├── resident_at
 └── owns
       ↓
      Asset
```

Nhưng mỗi edge phải là authoritative/derived rõ ràng.

---

# 704.69 — Graph Integrity

Không được cho phép:

```text
arbitrary graph mutation
```

Relationship creation phải đi qua domain command.

---

# 704.70 — Query Graph

Có thể hỗ trợ:

```axiom
related(subject)
parents(subject)
children(subject)
guardians(subject)
spouses(subject)
household(subject)
properties(subject)
ownership_history(asset)
```

Queries phải obey privacy scope.

---

# 704.71 — Eventual Consistency

Derived graph projections có thể eventually consistent.

Authoritative registry event thì không.

```text
event
  ↓
authoritative
  ↓
projection
```

---

# 704.72 — Cross-Axiom Interfaces

`AXCIVIL` phải cung cấp typed contracts cho:

```text
AXIDENTITY
AXLAW
AXJUSTICE
AXCORRECTIONS
AXHEALTH
AXEDUCATION
AXFINANCE
AXHOUSING
```

---

# 704.73 — AXIDENTITY Boundary

```text
AXIDENTITY
    owns:
        person identity
        credentials
        authentication

AXCIVIL
    owns:
        civil facts
        civil relationships
        registrations
```

Không duplicate canonical identity databases.

---

# 704.74 — AXJUSTICE Boundary

Court order:

```text
AXJUSTICE
    ↓
civil execution request
    ↓
AXCIVIL
```

`AXCIVIL` không sửa court judgment.

---

# 704.75 — AXCORRECTIONS Boundary

Correctional release có thể tạo civil events liên quan đến:

```text
status
residency
documentation
```

nhưng phải qua appropriate authority.

---

# 704.76 — Native Axiom API

Core API:

```axiom
register_birth()
register_death()
register_marriage()
register_divorce()
establish_parentage()
register_adoption()
create_guardianship()
change_name()
register_residency()
register_property()
transfer_property()
register_ownership()
issue_certificate()
verify_record()
recognize_foreign_record()
amend_record()
replay_state()
simulate_transition()
```

---

# 704.77 — Effect System

Các operations phải khai báo effects:

```text
read
write
register
certify
verify
recognize
transfer
amend
audit
external_io
ai_inference
```

Ví dụ:

```axiom
fn register_birth(...)
    effects [register, write, audit]
```

---

# 704.78 — No Ambient Civil Authority

Một module không được tự động có:

```text
registry.write
certificate.issue
ownership.transfer
identity.merge
```

Capabilities phải explicit.

---

# 704.79 — Agent Sandbox

AI civil agents:

```text
document_agent
registry_agent
verification_agent
translation_agent
audit_agent
property_agent
```

phải có:

```text
data_scope
capability_scope
jurisdiction_scope
time_scope
effect_budget
```

---

# 704.80 — Failure Model

Phải xử lý:

```text
duplicate command
network loss
database failure
partial commit
clock skew
conflicting records
invalid signature
revoked authority
AI failure
```

Không được tạo silent corruption.

---

# 704.81 — Clock Semantics

Legal timestamps phải sử dụng:

```text
trusted time source
```

và phân biệt:

```text
event time
record time
effective time
```

Clock skew không được tự động làm thay đổi legal state.

---

# 704.82 — Observability

Metrics:

```text
registration_latency
verification_latency
conflict_count
amendment_count
certificate_verification_rate
duplicate_detection_rate
projection_lag
authorization_failures
```

Không expose private data trong telemetry mặc định.

---

# 704.83 — Audit Query

Auditor phải có thể trả lời:

```text
Who registered this fact?
When?
Under which authority?
Which source document?
Which rule version?
Which amendment changed it?
Who certified it?
Was AI involved?
Who verified the AI output?
```

---

# 704.84 — Formal Invariants

```text
CIV-INV-01  Civil facts require provenance.
CIV-INV-02  Authoritative history is immutable.
CIV-INV-03  Civil state is replayable.
CIV-INV-04  Derived state is distinguishable from authoritative fact.
CIV-INV-05  Identity and civil status are separate domains.
CIV-INV-06  Legal relationship changes require authority.
CIV-INV-07  AI output is non-authoritative until verified.
CIV-INV-08  Foreign records require recognition where applicable.
CIV-INV-09  Property ownership history cannot be silently overwritten.
CIV-INV-10  Certificate is a signed projection, not source of truth.
CIV-INV-11  Registry mutation requires capability.
CIV-INV-12  Revoked capability cannot authorize new mutations.
CIV-INV-13  Simulation cannot mutate authoritative state.
CIV-INV-14  Conflicting records remain explicitly identifiable.
CIV-INV-15  Historical state is deterministically reproducible.
CIV-INV-16  Privacy scope is enforced at API boundary.
CIV-INV-17  External systems receive scoped projections.
CIV-INV-18  Offline nodes cannot create new authority.
CIV-INV-19  AI failure cannot corrupt authoritative state.
CIV-INV-20  Destructive deletion cannot bypass retention/legal-hold rules.
```

---

# 704.85 — Canonical Architecture

```text
                         ┌──────────────────┐
                         │      AXLAW       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Civil Authority│
                         └────────┬─────────┘
                                  │
                                  ▼
                  ┌────────────────────────────┐
                  │          AXCIVIL           │
                  │                            │
                  │ Vital Records              │
                  │ Family Relationships       │
                  │ Residency                  │
                  │ Civil Status                │
                  │ Property Registry           │
                  │ Ownership                   │
                  │ Certificates                │
                  │ Recognition                 │
                  └──────────────┬─────────────┘
                                 │
                       ┌─────────┴─────────┐
                       ▼                   ▼
                ┌──────────────┐    ┌──────────────┐
                │ AI Services  │    │ Human Review │
                │ Assist only  │    │ Authority    │
                └──────┬───────┘    └──────┬───────┘
                       │                   │
                       └─────────┬─────────┘
                                 ▼
                       ┌──────────────────┐
                       │ Capability +     │
                       │ Effect Engine    │
                       └────────┬─────────┘
                                ▼
                       ┌──────────────────┐
                       │ Command Engine   │
                       └────────┬─────────┘
                                ▼
                       ┌──────────────────┐
                       │ Immutable Civil │
                       │ Event Ledger     │
                       └────────┬─────────┘
                                ▼
                       ┌──────────────────┐
                       │ State Projections│
                       └──────────────────┘
```

---

# 704.86 — Completion Criteria

`BOOTSTRAP-704` chỉ hoàn thành khi:

1. Vital-record model frozen.
2. Birth/death model frozen.
3. Marriage/divorce model frozen.
4. Parentage/adoption model frozen.
5. Guardianship model frozen.
6. Name-change model frozen.
7. Residency model frozen.
8. Household model frozen.
9. Property registry model frozen.
10. Ownership model frozen.
11. Asset-transfer model frozen.
12. Certificate model frozen.
13. Recognition model frozen.
14. Amendment model frozen.
15. Temporal semantics frozen.
16. Event ledger frozen.
17. Privacy boundary frozen.
18. Capability model frozen.
19. AI authority boundary frozen.
20. Replay and simulation semantics frozen.
21. Multi-jurisdiction model frozen.
22. Native Axiom API frozen.
23. Security invariants frozen.
24. End-to-end civil lifecycle test defined.

---

# 704.87 — Definition of Done

```text
BOOTSTRAP-704
STATUS: COMPLETE / FROZEN

AXCIVIL 5.0
    ├── Vital Records
    ├── Birth / Death
    ├── Marriage / Divorce
    ├── Parentage / Adoption
    ├── Guardianship
    ├── Name Management
    ├── Residency
    ├── Household
    ├── Property Registry
    ├── Ownership
    ├── Asset Transfer
    ├── Certificates
    ├── Foreign Recognition
    ├── Amendment
    ├── Temporal History
    ├── Immutable Events
    ├── Privacy
    ├── Capability Security
    ├── AI Assistance Boundary
    ├── Deterministic Replay
    ├── Simulation
    └── Native Axiom Integration
```

**BOOTSTRAP-704 / AXCIVIL hoàn thành architectural baseline.**

### Task kế tiếp

**BOOTSTRAP-705 — AXGOV: Native Government Administration, Public-Service Delivery, Agency Workflow, Intergovernmental Coordination & Administrative-State Runtime 5.0**