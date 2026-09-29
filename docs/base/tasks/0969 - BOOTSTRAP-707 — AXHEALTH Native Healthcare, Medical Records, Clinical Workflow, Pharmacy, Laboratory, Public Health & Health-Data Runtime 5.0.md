# BOOTSTRAP-707 — AXHEALTH: Native Healthcare, Medical Records, Clinical Workflow, Pharmacy, Laboratory, Public Health & Health-Data Runtime 5.0

**Namespace:** `AXHEALTH`  
**Phase:** Axiom Civilization Runtime / Healthcare Infrastructure  
**Status:** ARCHITECTURAL BASELINE — FROZEN TARGET  
**Depends on:** `AXLAW`, `AXIDENTITY`, `AXCIVIL`, `AXGOV`, `AXFINANCE`

---

# 707.0 — Mục tiêu

`AXHEALTH` là runtime native của Axiom cho **healthcare information, clinical state, medical records, care workflows, laboratory, pharmacy, appointments, procedures, insurance interfaces và public-health data**.

Mục tiêu không phải biến Axiom thành một hệ thống y tế cụ thể, mà cung cấp một semantic runtime đủ tổng quát để xây dựng:

```text
hospital systems
clinic systems
electronic health records
laboratory information systems
pharmacy systems
medical imaging systems
telemedicine
health insurance systems
emergency care systems
public-health systems
clinical research systems
```

Core principle:

> `AXHEALTH` quản lý dữ liệu và workflow y tế có provenance, authorization và temporal semantics; không tự biến dữ liệu thành chẩn đoán hay quyết định y khoa có thẩm quyền.

---

# 707.1 — Healthcare Domain Boundary

Các domain phải được phân biệt:

```text
Person
Patient
Provider
Organization
Encounter
Observation
Condition
Procedure
Medication
Prescription
Laboratory Result
Imaging Study
Care Plan
Allergy
Immunization
Consent
Referral
Claim
Coverage
```

Không dùng một generic `medical_record` object thay thế toàn bộ.

---

# 707.2 — Patient Identity

`AXIDENTITY` sở hữu identity.

`AXHEALTH` sở hữu:

```text
patient_record
patient_relationship
clinical_identity
healthcare_context
```

Một người có thể có:

```text
one identity
multiple patient records
multiple providers
multiple healthcare organizations
```

do jurisdiction/policy khác nhau.

---

# 707.3 — Patient Record

```axiom
patient_record {
    patient_id
    identity_reference
    identifiers
    status
    managing_organization
    created_at
}
```

Patient record không phải là identity database.

---

# 707.4 — Patient Identifier

Healthcare systems có thể có:

```text
national_health_id
hospital_id
clinic_id
insurance_id
laboratory_id
```

Các identifiers phải có:

```text
issuer
identifier
valid_from
valid_to
status
verification
```

---

# 707.5 — Provider

```axiom
provider {
    provider_id
    identity_reference
    provider_type
    licenses
    specialties
    organizations
    status
}
```

Provider có thể là:

```text
physician
nurse
pharmacist
laboratory_staff
technician
therapist
emergency_provider
other_authorized_role
```

---

# 707.6 — Provider Authorization

Provider capability phải được tách khỏi identity:

```text
identity
    ↓
credential
    ↓
license
    ↓
scope
    ↓
clinical capability
```

Không:

```text
logged_in_user == authorized_clinician
```

mặc định.

---

# 707.7 — Healthcare Organization

```axiom
healthcare_organization {
    organization_id
    type
    facilities
    departments
    licenses
    jurisdiction
    status
}
```

Có thể biểu diễn:

```text
hospital
clinic
laboratory
pharmacy
ambulance_service
research_center
public_health_agency
```

---

# 707.8 — Facility

```axiom
facility {
    facility_id
    organization
    type
    location
    capabilities
    status
}
```

Capabilities:

```text
emergency
surgery
laboratory
imaging
pharmacy
inpatient
outpatient
```

---

# 707.9 — Healthcare Encounter

Encounter là context cho clinical activity:

```axiom
encounter {
    encounter_id
    patient
    organization
    providers
    type
    start_time
    end_time
    status
}
```

---

# 707.10 — Encounter Types

```text
OUTPATIENT
INPATIENT
EMERGENCY
TELEHEALTH
HOME_CARE
LABORATORY
PHARMACY
PREVENTIVE
FOLLOW_UP
OTHER
```

Extensible.

---

# 707.11 — Encounter Lifecycle

```text
SCHEDULED
    ↓
ARRIVED
    ↓
IN_PROGRESS
    ↓
COMPLETED
```

Alternative:

```text
CANCELLED
NO_SHOW
TRANSFERRED
```

---

# 707.12 — Clinical Observation

Observation là dữ liệu được quan sát/đo/ghi nhận.

```axiom
observation {
    observation_id
    patient
    encounter
    type
    value
    unit
    reference_range
    observed_at
    recorded_at
    performer
    provenance
}
```

---

# 707.13 — Observation ≠ Diagnosis

Phải phân biệt:

```text
observation
    ≠
clinical interpretation
    ≠
diagnosis
```

Ví dụ một measurement không tự động trở thành medical diagnosis.

---

# 707.14 — Units

Health data cần native units:

```text
temperature
pressure
mass
volume
concentration
heart_rate
oxygen_saturation
dose
duration
```

Không dùng raw numeric values thiếu unit trong authoritative clinical data.

---

# 707.15 — Unit Safety

Compiler/runtime có thể reject:

```text
heart_rate + kilograms
```

và:

```text
temperature + pressure
```

tương tự dimensional analysis.

---

# 707.16 — Measurement Precision

Measurement phải giữ:

```text
value
unit
precision
method
device
timestamp
```

Không được tự động làm mất precision.

---

# 707.17 — Clinical Condition

```axiom
condition {
    condition_id
    patient
    encounter
    code
    description
    status
    onset
    resolution
    evidence
    author
}
```

Status:

```text
SUSPECTED
ACTIVE
RESOLVED
RECURRENT
HISTORICAL
```

---

# 707.18 — Diagnosis

Diagnosis phải reference:

```text
clinical_context
provider
evidence
classification_system
timestamp
```

Không cho AI-generated label trở thành authoritative diagnosis chỉ vì model tạo ra nó.

---

# 707.19 — Clinical Evidence

Evidence có thể gồm:

```text
observation
laboratory_result
imaging_result
procedure
patient_report
previous_record
external_record
```

Provenance bắt buộc.

---

# 707.20 — Procedure

```axiom
procedure {
    procedure_id
    patient
    encounter
    type
    performer
    indication
    start_time
    end_time
    outcome
    evidence
    status
}
```

---

# 707.21 — Procedure Lifecycle

```text
PLANNED
    ↓
AUTHORIZED
    ↓
SCHEDULED
    ↓
IN_PROGRESS
    ↓
COMPLETED
```

Failure:

```text
CANCELLED
ABORTED
DEFERRED
```

---

# 707.22 — Care Plan

```axiom
care_plan {
    plan_id
    patient
    author
    goals
    interventions
    schedule
    monitoring
    status
}
```

Care plan là structured clinical object, không phải một text blob.

---

# 707.23 — Care Plan State

```text
DRAFT
ACTIVE
SUSPENDED
COMPLETED
CANCELLED
```

---

# 707.24 — Referral

```axiom
referral {
    referral_id
    patient
    source_provider
    target_provider
    reason
    urgency
    destination
    status
}
```

---

# 707.25 — Referral Lifecycle

```text
CREATED
    ↓
SENT
    ↓
ACCEPTED
    ↓
SCHEDULED
    ↓
COMPLETED
```

Có thể:

```text
DECLINED
EXPIRED
CANCELLED
```

---

# 707.26 — Appointment

```axiom
appointment {
    appointment_id
    patient
    provider
    facility
    service
    start
    end
    status
}
```

Scheduling engine không được tự động ghi clinical result.

---

# 707.27 — Emergency Context

Emergency care phải hỗ trợ:

```text
emergency_case
triage
arrival
stabilization
transfer
disposition
```

Trong emergency context, policy có thể cho phép limited access khi consent chưa thể thu thập.

Mọi emergency override phải audit được.

---

# 707.28 — Consent

```axiom
consent {
    consent_id
    subject
    scope
    purpose
    recipient
    issued_at
    expires_at
    status
}
```

---

# 707.29 — Consent Scope

Consent có thể giới hạn theo:

```text
record_type
organization
provider
purpose
time
geography
research_use
data_category
```

---

# 707.30 — Consent Revocation

```text
ACTIVE
    ↓
REVOKED
```

Revocation không xóa lịch sử consent.

---

# 707.31 — Break-Glass Access

Healthcare emergency có thể hỗ trợ:

```axiom
break_glass_access {
    actor
    patient
    reason
    scope
    started_at
    expires_at
}
```

Break-glass phải:

```text
time-bounded
scope-bounded
audited
reviewable
```

---

# 707.32 — Medication

```axiom
medication {
    medication_id
    product
    active_ingredient
    strength
    form
    route
    manufacturer
    status
}
```

Medication identity không đồng nghĩa với prescription.

---

# 707.33 — Prescription

```axiom
prescription {
    prescription_id
    patient
    prescriber
    medication
    dose
    route
    frequency
    duration
    instructions
    status
}
```

---

# 707.34 — Prescription Lifecycle

```text
DRAFT
    ↓
AUTHORIZED
    ↓
ISSUED
    ↓
DISPENSED
```

Có thể:

```text
CANCELLED
EXPIRED
PARTIALLY_DISPENSED
```

---

# 707.35 — Medication Administration

Phải phân biệt:

```text
prescribed
dispensed
administered
```

Một prescription không chứng minh medication đã được administered.

---

# 707.36 — Allergy

```axiom
allergy {
    allergy_id
    patient
    substance
    reaction
    severity
    status
    source
}
```

Allergy phải có provenance.

---

# 707.37 — Allergy vs Intolerance

Runtime phải phân biệt semantic categories:

```text
allergy
intolerance
adverse_reaction
```

Không merge thành một boolean.

---

# 707.38 — Adverse Event

```axiom
adverse_event {
    event_id
    patient
    exposure
    event_type
    onset
    severity
    reporter
    evidence
    status
}
```

---

# 707.39 — Laboratory Order

```axiom
lab_order {
    order_id
    patient
    encounter
    requester
    tests
    priority
    status
}
```

---

# 707.40 — Laboratory Result

```axiom
lab_result {
    result_id
    order
    test
    value
    unit
    reference_range
    specimen
    performer
    observed_at
    verified_at
    status
}
```

---

# 707.41 — Lab Result Verification

Result lifecycle:

```text
PRELIMINARY
    ↓
VERIFIED
    ↓
FINAL
```

Corrections phải tạo amendment/version event.

---

# 707.42 — Specimen

```axiom
specimen {
    specimen_id
    patient
    type
    collection_time
    collector
    container
    status
}
```

Chain-of-custody phải được hỗ trợ khi cần.

---

# 707.43 — Specimen Chain

```text
COLLECTED
    ↓
LAB_RECEIVED
    ↓
PROCESSED
    ↓
ANALYZED
    ↓
STORED / DISPOSED
```

Mỗi transition có provenance.

---

# 707.44 — Medical Imaging

```axiom
imaging_study {
    study_id
    patient
    modality
    body_region
    acquisition_time
    facility
    series
    reports
}
```

---

# 707.45 — Imaging Report

Report:

```text
author
observations
impression
timestamp
status
```

Phải phân biệt raw imaging data với clinical interpretation.

---

# 707.46 — Medical Device

```axiom
medical_device {
    device_id
    manufacturer
    model
    serial
    calibration
    location
    status
}
```

---

# 707.47 — Device Data

Device-originated measurements phải lưu:

```text
device
firmware_version
measurement_method
timestamp
quality
provenance
```

Device output không mặc định là clinically verified fact.

---

# 707.48 — Device Connectivity

Adapter:

```text
AXHEALTH
    ↓
Device Interface
    ↓
External Device
```

External device protocol không được hard-code vào health semantic core.

---

# 707.49 — Health Data Provenance

Mọi authoritative health datum phải có:

```text
source
author
device
timestamp
method
organization
verification_status
```

tùy loại dữ liệu.

---

# 707.50 — Temporal Model

Healthcare records cần phân biệt:

```text
event_time
observation_time
recorded_time
verified_time
effective_time
```

Không dùng một `timestamp` cho mọi semantics.

---

# 707.51 — Historical Correction

Không:

```text
UPDATE diagnosis
```

theo nghĩa xóa lịch sử.

Thay vào đó:

```text
amendment
correction
superseding_record
```

Original record vẫn tồn tại.

---

# 707.52 — Clinical Record Version

```axiom
record_version {
    record_id
    version
    previous_version
    author
    created_at
    reason
    content_hash
}
```

---

# 707.53 — Clinical Document

Documents:

```text
clinical_note
discharge_summary
referral_letter
lab_report
imaging_report
prescription
care_plan
```

phải reference structured records.

---

# 707.54 — Structured + Narrative

AXHEALTH phải hỗ trợ đồng thời:

```text
structured data
+
clinical narrative
```

Narrative không được trở thành lý do để bỏ structured provenance.

---

# 707.55 — Clinical Note

```axiom
clinical_note {
    note_id
    patient
    encounter
    author
    sections
    created_at
    signed_at
    status
}
```

---

# 707.56 — Note Signing

Clinical note có thể:

```text
DRAFT
SIGNED
AMENDED
FINAL
```

Signed note không được silently modified.

---

# 707.57 — Health Record Access

Capability examples:

```text
health.patient.read
health.patient.write
health.clinical.record
health.prescription.issue
health.lab.verify
health.imaging.report
health.consent.manage
health.research.export
```

---

# 707.58 — Minimum Necessary Access

Default principle:

```text
need_to_know
+
purpose_bound
+
scope_bound
+
time_bound
```

Không cấp toàn bộ patient record chỉ vì actor có quyền truy cập một service.

---

# 707.59 — Data Segmentation

Các nhóm dữ liệu có thể có security levels:

```text
GENERAL_CLINICAL
SENSITIVE_CLINICAL
GENETIC
MENTAL_HEALTH
REPRODUCTIVE
SUBSTANCE_RELATED
RESEARCH
ADMINISTRATIVE
```

Việc phân loại và access rules phụ thuộc jurisdiction/policy.

---

# 707.60 — Research Data Boundary

Research dataset phải tách khỏi clinical source:

```text
Clinical Record
      ↓
Authorized Projection
      ↓
Research Dataset
```

Researcher không tự động có quyền sửa clinical state.

---

# 707.61 — De-identification

Hỗ trợ:

```text
de_identify()
pseudonymize()
aggregate()
redact()
```

Nhưng output phải được đánh dấu:

```text
DERIVED_DATASET
```

không phải canonical patient record.

---

# 707.62 — Public Health

Public-health subsystem:

```text
surveillance
outbreak_event
population_measure
vaccination_program
reportable_condition
health_statistics
```

---

# 707.63 — Population Health

```axiom
population_measure {
    population
    metric
    value
    period
    geography
    methodology
    provenance
}
```

Aggregate data không được tự động expose individual identities.

---

# 707.64 — Public Health Reporting

```axiom
public_health_report {
    report_id
    reporting_entity
    condition
    period
    jurisdiction
    data
    methodology
    status
}
```

---

# 707.65 — Vaccination

```axiom
immunization {
    immunization_id
    patient
    vaccine
    dose
    administration_date
    provider
    facility
    lot
    status
}
```

---

# 707.66 — Health Coverage

Insurance/coverage boundary:

```axiom
coverage {
    coverage_id
    beneficiary
    provider
    plan
    effective_from
    effective_to
    scope
    status
}
```

Coverage không phải financial ledger.

---

# 707.67 — Health Claim

```axiom
health_claim {
    claim_id
    provider
    patient
    coverage
    services
    amount
    status
}
```

Actual monetary state thuộc `AXFINANCE`.

---

# 707.68 — AXFINANCE Integration

```text
AXHEALTH
   ↓
service / claim / invoice
   ↓
AXFINANCE
   ↓
financial transaction
```

AXHEALTH không trở thành accounting ledger.

---

# 707.69 — AXGOV Integration

Government health programs:

```text
AXGOV
   ↓
program eligibility
   ↓
AXHEALTH
   ↓
care/service
   ↓
AXFINANCE
```

Administrative authority vẫn thuộc AXGOV/AXLAW.

---

# 707.70 — AXCIVIL Integration

Civil registry có thể cung cấp:

```text
identity
birth/death status
legal relationships
residency
```

AXHEALTH chỉ giữ references cần thiết.

---

# 707.71 — Death Boundary

Health system có thể record clinical death event, nhưng authoritative civil death registration thuộc `AXCIVIL` theo jurisdiction.

Flow:

```text
AXHEALTH
   ↓
clinical death record
   ↓
authorized notification
   ↓
AXCIVIL
   ↓
civil death registry
```

---

# 707.72 — Emergency Interoperability

Emergency services phải có interface:

```axiom
emergency_case {
    case_id
    patient
    incident
    priority
    location
    responders
    destination
    status
}
```

---

# 707.73 — Triage

Triage data phải phân biệt:

```text
observed condition
triage assessment
priority
clinical diagnosis
```

Không merge chúng.

---

# 707.74 — Ambulance Transfer

```text
DISPATCHED
    ↓
EN_ROUTE
    ↓
ON_SCENE
    ↓
TRANSPORTING
    ↓
ARRIVED
    ↓
TRANSFERRED
```

---

# 707.75 — Health Workflow Engine

Workflow primitives:

```text
task
approval
clinical_review
order
result
notification
escalation
timeout
handoff
```

Workflow engine không tự tạo medical truth.

---

# 707.76 — Clinical Task

```axiom
clinical_task {
    task_id
    patient
    encounter
    owner
    type
    priority
    due_at
    status
}
```

---

# 707.77 — Handoff

Healthcare handoff phải là explicit event:

```axiom
handoff {
    source
    destination
    patient
    context
    outstanding_tasks
    timestamp
    acknowledgement
}
```

---

# 707.78 — Clinical Escalation

```text
NORMAL
    ↓
ATTENTION_REQUIRED
    ↓
ESCALATED
    ↓
URGENT_REVIEW
```

Escalation engine không tự quyết định diagnosis.

---

# 707.79 — AI Clinical Assistance

AI có thể hỗ trợ:

```text
medical document summarization
record search
coding assistance
clinical decision support
image pre-analysis
lab anomaly detection
drug interaction screening
workflow routing
speech transcription
translation
```

Nhưng AI output phải có:

```text
model
version
timestamp
input provenance
confidence
review state
```

---

# 707.80 — AI ≠ Clinical Authority

Invariant:

```text
AI recommendation
    !=
clinical order
```

và:

```text
AI classification
    !=
confirmed diagnosis
```

AI phải hoạt động dưới explicit capability.

---

# 707.81 — Human Review

AI-assisted clinical action có thể yêu cầu:

```text
AI_GENERATED
    ↓
CLINICIAN_REVIEW
    ↓
ACCEPTED / MODIFIED / REJECTED
```

Review event phải được giữ lại.

---

# 707.82 — AI Safety Boundary

AI không được tự động:

```text
prescribe medication
change authoritative diagnosis
delete medical record
override allergy
authorize invasive procedure
```

trừ khi một explicit, policy-governed automated workflow cho phép hành động đó; ngay cả khi đó provenance và authorization phải tồn tại.

---

# 707.83 — Model Versioning

Clinical AI output phải reference:

```text
model_id
model_version
prompt_or_policy_version
input_snapshot
output
reviewer
```

để reproducibility.

---

# 707.84 — Medical Device AI

Device AI result phải phân biệt:

```text
raw_signal
algorithm_output
clinician_interpretation
final_record
```

Không flatten thành một value.

---

# 707.85 — Clinical Decision Support

Decision-support result:

```axiom
clinical_recommendation {
    recommendation_id
    patient
    context
    evidence
    model
    recommendation
    confidence
    generated_at
    review_status
}
```

---

# 707.86 — Evidence Trace

Mỗi AI recommendation phải có thể truy ngược:

```text
recommendation
    ↓
evidence
    ↓
source records
    ↓
source timestamps
```

---

# 707.87 — Security

Healthcare runtime phải bảo vệ:

```text
patient identity
clinical records
genetic data
medications
lab data
imaging
insurance information
research data
```

Security primitives:

```text
encryption
access control
audit
tokenization
data segmentation
key rotation
secure deletion
```

---

# 707.88 — Key Management

Cryptographic keys phải được quản lý ngoài business objects:

```text
key_id
purpose
owner
algorithm
created_at
rotation_policy
status
```

Không hard-code keys trong AXHEALTH applications.

---

# 707.89 — Immutable Clinical Audit

Events:

```text
PATIENT_CREATED
RECORD_ACCESSED
RECORD_MODIFIED
CONSENT_GRANTED
CONSENT_REVOKED
BREAK_GLASS_USED
ORDER_CREATED
RESULT_VERIFIED
PRESCRIPTION_ISSUED
MEDICATION_DISPENSED
PROCEDURE_COMPLETED
RECORD_AMENDED
```

phải audit được.

---

# 707.90 — Access Audit

Audit phải trả lời:

```text
Who accessed?
Which patient?
Which records?
Why?
Under which capability?
When?
Was consent present?
Was break-glass used?
What was changed?
```

---

# 707.91 — Offline Healthcare

Offline operation có thể hỗ trợ:

```text
ambulance
remote clinic
field medicine
disaster response
```

Nhưng offline node không được tự tạo unrestricted authority.

---

# 707.92 — Offline Command

Offline commands phải có:

```text
issuer
capability
scope
expiry
sequence
signature
```

và sync sau đó.

---

# 707.93 — Conflict Resolution

Clinical conflicts không được silently merge.

Ví dụ:

```text
record A
record B
```

phải tạo:

```text
CONFLICT
```

và cần resolution policy.

---

# 707.94 — Distributed Healthcare

Hệ thống phải hỗ trợ:

```text
hospital node
regional node
national node
mobile node
laboratory node
pharmacy node
```

với scoped synchronization.

---

# 707.95 — Interoperability

Core phải có adapter architecture cho:

```text
HL7-like systems
FHIR-like systems
DICOM-like imaging systems
laboratory protocols
pharmacy systems
insurance systems
public-health systems
```

Các external standards không được trở thành dependency bắt buộc của Axiom core.

---

# 707.96 — Canonical Data Model

External records:

```text
External Format
      ↓
Adapter
      ↓
AXHEALTH Canonical Model
      ↓
Validation
      ↓
Authoritative / Imported State
```

---

# 707.97 — External Data Trust

Imported medical data phải mang:

```text
source
source_system
import_time
original_identifier
verification_status
trust_level
```

Không mặc định coi external data là verified.

---

# 707.98 — Duplicate Detection

Duplicate detection có thể dùng:

```text
identity matching
record similarity
clinical identifiers
temporal consistency
```

Nhưng:

```text
POTENTIAL_DUPLICATE
```

không được biến thành automatic deletion.

---

# 707.99 — Data Quality

Health records phải hỗ trợ:

```text
missing
unknown
not_applicable
not_measured
invalid
estimated
verified
```

Không ép mọi field thành `null` hoặc `0`.

---

# 707.100 — Clinical State

Patient state phải là projection:

```text
event history
     ↓
clinical state
```

Không phải một mutable giant object.

---

# 707.101 — Event Sourcing Boundary

Không bắt buộc toàn bộ AXHEALTH phải event-sourced internally, nhưng mọi **authoritative clinical transition** phải có immutable event/provenance đủ để reconstruct state.

---

# 707.102 — Temporal Queries

API:

```axiom
patient_state_at(patient, timestamp)
condition_history(patient)
medication_history(patient)
encounter_history(patient)
lab_history(patient)
consent_history(patient)
```

---

# 707.103 — Replay

```axiom
replay_patient(patient, timestamp)
replay_encounter(encounter, timestamp)
replay_record(record, version)
```

Kết quả phải deterministic.

---

# 707.104 — Simulation

```axiom
simulate_care_plan()
simulate_workflow()
simulate_resource_allocation()
simulate_claim()
```

Simulation không thay đổi clinical state.

---

# 707.105 — Resource Management

Healthcare resource:

```text
bed
operating_room
ambulance
medical_device
staff
laboratory_capacity
pharmacy_inventory
```

phải được quản lý như resource state riêng.

---

# 707.106 — Bed Management

```axiom
bed {
    bed_id
    facility
    ward
    type
    status
    patient
}
```

Status:

```text
AVAILABLE
RESERVED
OCCUPIED
CLEANING
MAINTENANCE
BLOCKED
```

---

# 707.107 — Pharmacy Inventory

```axiom
inventory_item {
    medication
    batch
    quantity
    expiry
    location
    status
}
```

Inventory state không thay thế prescription state.

---

# 707.108 — Batch / Lot

```axiom
medication_batch {
    batch_id
    product
    manufacturer
    lot
    manufacture_date
    expiry_date
    quantity
}
```

Recall phải có traceability.

---

# 707.109 — Medication Recall

```text
IDENTIFIED
    ↓
FLAGGED
    ↓
QUARANTINED
    ↓
REMOVED
    ↓
RESOLVED
```

---

# 707.110 — Resource Allocation

Resource allocation phải có:

```text
resource
request
priority
authority
time
reservation
status
```

Priority policy phải explicit.

---

# 707.111 — Clinical Capacity

System có thể calculate:

```text
bed_capacity
staff_capacity
lab_capacity
appointment_capacity
```

Đây là derived analytics, không tự động thay đổi clinical truth.

---

# 707.112 — Health Analytics

Analytics categories:

```text
operational
clinical
population
financial
quality
research
```

Mỗi output phải mang provenance và aggregation scope.

---

# 707.113 — Quality Metrics

Quality metrics phải phân biệt:

```text
raw event
calculated metric
benchmark
interpretation
```

Không biến benchmark thành clinical fact.

---

# 707.114 — Public Health Privacy

Population analytics phải hỗ trợ:

```text
aggregation
minimum_cell_size
suppression
pseudonymization
geographic generalization
```

theo policy.

---

# 707.115 — Consent for Research

Research access phải reference:

```text
consent
legal_basis
protocol
data_scope
expiry
review
```

---

# 707.116 — Clinical Trial

```axiom
clinical_trial {
    trial_id
    sponsor
    protocol
    sites
    participants
    interventions
    outcomes
    status
}
```

---

# 707.117 — Trial Participant

Participant record phải tách khỏi general clinical record nhưng có controlled linkage.

```text
clinical_identity
      ↕
trial_participant
```

---

# 707.118 — Research Integrity

Trial data phải có:

```text
protocol_version
data_source
collection_time
collector
amendment_history
```

---

# 707.119 — Healthcare Financial Boundary

AXHEALTH tạo:

```text
service
claim
coverage event
billing reference
```

AXFINANCE tạo:

```text
invoice
receivable
payment
settlement
ledger entry
```

---

# 707.120 — Canonical Architecture

```text
                         AXIDENTITY
                              │
                              ▼
                        ┌────────────┐
                        │ AXHEALTH   │
                        └─────┬──────┘
                              │
       ┌──────────────┬───────┼────────┬───────────────┐
       ▼              ▼       ▼        ▼               ▼
   Clinical        Pharmacy   Lab    Imaging        Emergency
       │              │       │        │               │
       └──────────────┴───────┼────────┴───────────────┘
                              ▼
                       Health Workflow
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
             AXGOV        AXFINANCE      Research
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                     Public Health / External
```

---

# 707.121 — Native API

```axiom
create_patient()
link_patient_identity()

register_provider()
register_organization()
create_facility()

create_encounter()
schedule_appointment()
create_referral()
create_care_plan()

record_observation()
record_condition()
record_procedure()

create_lab_order()
record_lab_result()
verify_lab_result()

create_imaging_study()
record_imaging_report()

create_prescription()
authorize_prescription()
dispense_medication()
record_administration()

record_allergy()
record_adverse_event()

grant_consent()
revoke_consent()
request_break_glass()

create_health_claim()

record_immunization()
create_public_health_report()

create_research_protocol()
create_trial_participant()

replay_patient()
replay_encounter()
simulate_care_plan()
```

---

# 707.122 — Compiler Integration

Axiom compiler nên hỗ trợ semantic checking cho:

```text
unit
measurement
duration
dose
rate
percentage
health identifier
clinical capability
```

Ví dụ:

```axiom
heart_rate: bpm
temperature: celsius
dose: mg
```

Compiler có thể phát hiện dimensional mismatch trước runtime.

---

# 707.123 — Effect System

Clinical operations phải khai báo effects:

```text
read_patient
write_patient
issue_prescription
verify_lab
access_sensitive_record
break_glass
research_export
```

Ví dụ:

```axiom
fn issue_prescription(...)
    effects [health.prescription.issue]
```

---

# 707.124 — Capability Model

Capability phải có:

```text
subject
resource
action
scope
purpose
expiry
authority
```

Ví dụ:

```text
provider
→ prescription.issue
→ patient X
→ encounter Y
→ valid until T
```

---

# 707.125 — Formal Invariants

```text
HLT-INV-01  AXHEALTH does not own identity truth.
HLT-INV-02  Clinical records have provenance.
HLT-INV-03  Observation is distinct from diagnosis.
HLT-INV-04  Prescription is distinct from administration.
HLT-INV-05  Lab result is distinct from clinical interpretation.
HLT-INV-06  Historical clinical records are immutable.
HLT-INV-07  Corrections use explicit amendments.
HLT-INV-08  AI output is not automatically clinical authority.
HLT-INV-09  AI recommendation is distinguishable from clinician decision.
HLT-INV-10  Sensitive health data requires scoped authorization.
HLT-INV-11  Break-glass access is time-bounded and audited.
HLT-INV-12  Consent history is immutable.
HLT-INV-13  Research access cannot mutate clinical records.
HLT-INV-14  Imported external records retain source provenance.
HLT-INV-15  Duplicate detection cannot silently delete records.
HLT-INV-16  Clinical units are explicit.
HLT-INV-17  Measurements retain precision and unit semantics.
HLT-INV-18  Emergency overrides are auditable.
HLT-INV-19  Health financial state belongs to AXFINANCE.
HLT-INV-20  Civil death state belongs to AXCIVIL.
HLT-INV-21  Public-health aggregates do not expose individual identity by default.
HLT-INV-22  Historical patient state is replayable.
HLT-INV-23  Simulation cannot mutate authoritative health state.
HLT-INV-24  Offline nodes cannot create unrestricted healthcare authority.
HLT-INV-25  Clinical state remains valid if AI services fail.
```

---

# 707.126 — End-to-End Clinical Flow

```text
Patient
   ↓
AXIDENTITY
   ↓
Patient Record
   ↓
Encounter
   ↓
Observation
   ↓
Clinical Assessment
   ↓
Order
   ├── Laboratory
   ├── Imaging
   └── Procedure
   ↓
Result
   ↓
Clinical Review
   ↓
Care Plan
   ↓
Prescription / Procedure
   ↓
Follow-up
   ↓
Outcome
```

---

# 707.127 — End-to-End Emergency Flow

```text
Emergency Event
      ↓
Dispatch
      ↓
Triage
      ↓
Emergency Encounter
      ↓
Assessment
      ↓
Intervention
      ↓
Transfer
      ↓
Receiving Facility
      ↓
Handoff
      ↓
Continued Care
```

---

# 707.128 — End-to-End Medication Flow

```text
Clinical Assessment
      ↓
Prescription
      ↓
Authorization
      ↓
Pharmacy
      ↓
Dispensing
      ↓
Administration
      ↓
Outcome / Adverse Event
```

Mỗi state phải độc lập và traceable.

---

# 707.129 — End-to-End Laboratory Flow

```text
Order
  ↓
Specimen Collection
  ↓
Transport
  ↓
Laboratory Receipt
  ↓
Processing
  ↓
Analysis
  ↓
Verification
  ↓
Final Result
  ↓
Clinical Interpretation
```

---

# 707.130 — End-to-End Public Health Flow

```text
Clinical / Laboratory Events
          ↓
Authorized Reporting
          ↓
Public Health System
          ↓
Aggregation
          ↓
Population Metric
          ↓
Surveillance
          ↓
Authorized Response Workflow
```

---

# 707.131 — End-to-End AI Flow

```text
Clinical Data
      ↓
Scoped Data Projection
      ↓
AI Model
      ↓
AI Output
      ↓
Confidence + Provenance
      ↓
Human / Authorized Review
      ↓
Clinical Action
      ↓
Authoritative Record
```

AI không được bypass review/authorization boundary.

---

# 707.132 — Test Matrix

Phải có:

```text
identity_tests
patient_tests
provider_tests
encounter_tests
observation_tests
condition_tests
procedure_tests
care_plan_tests
consent_tests
break_glass_tests
medication_tests
prescription_tests
allergy_tests
laboratory_tests
imaging_tests
device_tests
emergency_tests
public_health_tests
research_tests
insurance_tests
security_tests
privacy_tests
audit_tests
replay_tests
offline_tests
AI_boundary_tests
interoperability_tests
```

---

# 707.133 — Property Tests

Các property bắt buộc:

```text
replay(patient_history) == current_patient_state

revoked_consent
    cannot grant new authorized access

duplicate_import
    does not silently create duplicate patient

duplicate_command
    does not duplicate clinical effect

AI_output
    cannot become authoritative without required authorization

simulation
    does not mutate clinical state

amendment
    preserves original record

break_glass
    always produces audit event

external_record
    retains source provenance

unit_mismatch
    cannot silently execute
```

---

# 707.134 — Completion Criteria

`BOOTSTRAP-707` chỉ hoàn thành khi:

1. Patient model frozen.
2. Provider model frozen.
3. Organization/facility model frozen.
4. Encounter model frozen.
5. Observation model frozen.
6. Clinical condition model frozen.
7. Procedure model frozen.
8. Care-plan model frozen.
9. Consent model frozen.
10. Break-glass model frozen.
11. Medication model frozen.
12. Prescription lifecycle frozen.
13. Laboratory model frozen.
14. Imaging model frozen.
15. Device model frozen.
16. Emergency model frozen.
17. Public-health model frozen.
18. Research model frozen.
19. Insurance/claim boundary frozen.
20. AXFINANCE boundary frozen.
21. AI clinical boundary frozen.
22. Privacy/security model frozen.
23. Provenance model frozen.
24. Temporal model frozen.
25. Clinical amendment model frozen.
26. Distributed/offline model frozen.
27. Interoperability boundary frozen.
28. Native healthcare APIs frozen.
29. Compiler semantic-health integration frozen.
30. Formal invariants and test matrix frozen.

---

# 707.135 — Definition of Done

```text
BOOTSTRAP-707
STATUS: COMPLETE / FROZEN

AXHEALTH 5.0
    ├── Patient
    ├── Provider
    ├── Organization
    ├── Facility
    ├── Encounter
    ├── Observation
    ├── Condition
    ├── Procedure
    ├── Care Plan
    ├── Consent
    ├── Emergency
    ├── Medication
    ├── Prescription
    ├── Allergy
    ├── Laboratory
    ├── Imaging
    ├── Medical Devices
    ├── Public Health
    ├── Research
    ├── Insurance / Claims Boundary
    ├── Clinical Workflow
    ├── Provenance
    ├── Privacy
    ├── Security
    ├── Audit
    ├── Offline / Distributed Healthcare
    ├── Native Unit Safety
    ├── AI Clinical Assistance Boundary
    ├── Replay
    └── Simulation
```

**BOOTSTRAP-707 / AXHEALTH hoàn thành architectural baseline.**

### Task kế tiếp

**BOOTSTRAP-708 — AXEDUCATION: Native Education, Student Records, Curriculum, Assessment, Credential, Learning Workflow & Knowledge-State Runtime 5.0**