# BOOTSTRAP-703 — AXCORRECTIONS: Native AI Civilization-Scale Corrections, Custodial Administration, Probation, Rehabilitation & Reentry Runtime 5.0

**Namespace:** `AXCORRECTIONS`  
**Phase:** Axiom Civilization Runtime / Justice Execution Layer  
**Status:** ARCHITECTURAL BASELINE — FROZEN TARGET  
**Depends on:** `BOOTSTRAP-702 / AXJUSTICE`

## 703.0 — Mục tiêu

`AXCORRECTIONS` là runtime native của Axiom chịu trách nhiệm quản lý **việc thi hành các quyết định tư pháp đã có hiệu lực**, bao gồm:

```text
Judgment
    ↓
Finality
    ↓
Sentence / Order
    ↓
Custody
    ↓
Correctional Administration
    ↓
Probation / Community Supervision
    ↓
Rehabilitation
    ↓
Reentry
    ↓
Post-Reentry Support
```

`AXCORRECTIONS` **không quyết định một người có phạm tội hay không**, không tạo judgment và không thay thế `AXJUSTICE`.

Nó nhận các quyết định đã có hiệu lực từ `AXJUSTICE` và cung cấp một runtime có khả năng:

- tạo execution plan;
- quản lý sentence;
- quản lý custody;
- quản lý detention/correctional placement;
- quản lý probation/community supervision;
- quản lý rehabilitation;
- quản lý education/training;
- quản lý treatment programs khi được pháp luật cho phép;
- quản lý reentry;
- quản lý compliance;
- quản lý violations;
- quản lý release;
- quản lý parole/probation interfaces;
- quản lý các thay đổi hợp pháp đối với execution state;
- duy trì audit trail hoàn chỉnh;
- bảo đảm mọi hành động đều có authorization và provenance;
- hỗ trợ quy mô từ một cá nhân đến hệ thống correctional cấp quốc gia.

---

# 703.1 — Core Principle

`AXCORRECTIONS` phải tuân thủ nguyên tắc:

> **The correctional runtime executes lawful decisions; it does not create justice decisions.**

Do đó:

```text
AXLAW
   ↓
AXJUSTICE
   ↓
Final Judgment / Order
   ↓
AXCORRECTIONS
```

Không được phép:

```text
AXCORRECTIONS
    ↓
infer guilt
    ↓
create conviction
    ↓
increase sentence
    ↓
create punishment
```

Runtime chỉ được thực hiện các quyền đã được cấp bởi legal/judicial authority.

---

# 703.2 — Separation of Concerns

Phải tách hoàn toàn:

```text
LegalRule
Case
Charge
Evidence
Finding
Judgment
Sentence
Custody
Supervision
Rehabilitation
Release
Reentry
```

Đặc biệt:

```text
Finding != Sentence
Sentence != Custody
Custody != Rehabilitation
Rehabilitation != Release
Release != Reentry
```

Không được sử dụng một object thay thế cho toàn bộ lifecycle.

---

# 703.3 — Correctional Subject Model

Core entity:

```axiom
correctional_subject
```

Một subject phải có:

```text
subject_id
legal_identity
jurisdiction
status
sentence_set
custody_state
supervision_state
program_state
release_state
reentry_state
```

Subject identity phải liên kết tới identity system nhưng không được đồng nhất với một physical location hoặc một custodial facility.

---

# 703.4 — Sentence Model

Sentence được biểu diễn độc lập:

```axiom
sentence {
    sentence_id
    authority
    jurisdiction
    source_judgment
    offense_reference
    start_condition
    duration
    concurrent_group
    consecutive_group
    credit_rules
    eligibility_rules
    modification_rules
    termination_condition
}
```

Phải hỗ trợ:

```text
single sentence
multiple sentences
concurrent sentences
consecutive sentences
suspended sentence
conditional sentence
time-credit
sentence modification
sentence termination
```

Không được phép dùng integer đơn giản làm đại diện cho toàn bộ sentence semantics.

---

# 703.5 — Sentence Execution Engine

Execution engine phải tính:

```text
sentence start
sentence end
eligible credits
served time
remaining time
concurrent relationships
consecutive relationships
release eligibility
supervision period
```

Mọi calculation phải:

- deterministic;
- reproducible;
- versioned;
- jurisdiction-aware;
- auditable.

Cùng một input + cùng một legal/runtime version phải tạo cùng một execution result.

---

# 703.6 — Custody Model

Custody là state machine:

```text
NOT_IN_CUSTODY
    ↓
ORDERED_FOR_CUSTODY
    ↓
IN_CUSTODY
    ↓
TRANSFER_PENDING
    ↓
TRANSFERRED
    ↓
RELEASE_ELIGIBLE
    ↓
RELEASED
```

Có thể có các state chuyên biệt:

```text
PRETRIAL
SENTENCED
TEMPORARY_HOLD
MEDICAL_HOLD
TRANSFER
COMMUNITY_CUSTODY
```

Nhưng mọi state extension phải map về core custody semantics.

---

# 703.7 — Facility Model

Facility phải được biểu diễn như resource:

```axiom
facility {
    facility_id
    jurisdiction
    facility_type
    capacity
    security_class
    capabilities
    accessibility
    programs
    current_population
    status
}
```

Không được encode facility-specific logic vào compiler core.

---

# 703.8 — Placement Engine

Placement engine nhận:

```text
legal constraints
sentence constraints
custody requirements
facility capabilities
safety constraints
medical constraints
program requirements
jurisdiction constraints
```

và tạo:

```text
placement decision
```

Mọi placement decision phải:

```text
authorized
explainable
auditable
reversible when legally permitted
```

AI có thể hỗ trợ recommendation nhưng không được tự động biến recommendation thành binding placement decision.

---

# 703.9 — Transfer Engine

Transfer phải hỗ trợ:

```text
facility → facility
jurisdiction → jurisdiction
custody → community
temporary transfer
medical transfer
court transfer
```

Transfer record:

```text
origin
destination
authority
reason
authorization
time
custody state
chain-of-custody
transport record
```

---

# 703.10 — Custody Event Ledger

Mọi custody event phải append-only:

```text
ADMISSION
TRANSFER
PLACEMENT
RECLASSIFICATION
PROGRAM_ENTRY
PROGRAM_EXIT
DISCIPLINARY_EVENT
MEDICAL_EVENT_REFERENCE
RELEASE_ORDER
RELEASE
```

Không overwrite historical event.

Correction chỉ được thực hiện bằng:

```text
superseding_event
```

---

# 703.11 — Probation Runtime

Probation được model độc lập với custody.

```axiom
probation {
    probation_id
    subject
    authority
    start
    end
    conditions
    supervision_level
    reporting_requirements
    program_requirements
    violation_rules
    termination_rules
}
```

Phải hỗ trợ:

```text
reporting
appointments
conditions
compliance
violations
modification
termination
```

---

# 703.12 — Community Supervision

Community supervision phải có state:

```text
ACTIVE
COMPLIANT
NONCOMPLIANT
VIOLATION_REVIEW
MODIFIED
SUSPENDED
TERMINATED
```

Runtime không được tự kết luận rằng một violation đã xảy ra nếu jurisdiction yêu cầu human/legal determination.

---

# 703.13 — Violation Pipeline

Violation lifecycle:

```text
OBSERVATION
    ↓
REPORT
    ↓
REVIEW
    ↓
DETERMINATION
    ↓
AUTHORIZED_ACTION
```

Tách:

```text
event
allegation
finding
sanction
```

Không được collapse chúng thành một boolean:

```text
violated = true
```

---

# 703.14 — Rehabilitation Model

Rehabilitation phải được model như collection of programs:

```axiom
program {
    program_id
    type
    provider
    eligibility
    duration
    requirements
    completion_rules
    outcome_model
}
```

Program types có thể gồm:

```text
education
vocational_training
behavioral_program
substance_recovery_program
family_support
life_skills
employment_support
housing_support
```

Danh sách này không được hard-code vào language core.

---

# 703.15 — Program Participation

Participation state:

```text
ELIGIBLE
ENROLLED
ACTIVE
PAUSED
COMPLETED
WITHDRAWN
INELIGIBLE
```

Program completion phải có:

```text
evidence
provider
timestamp
verification
authority
```

Không được coi prediction là completion evidence.

---

# 703.16 — AI Rehabilitation Support

AI có thể:

```text
recommend programs
identify unmet requirements
summarize progress
detect administrative inconsistencies
generate schedules
predict resource requirements
```

Nhưng:

```text
AI recommendation != legal decision
AI prediction != compliance finding
AI score != sentence modification
```

Các AI outputs phải được lưu riêng với authoritative records.

---

# 703.17 — Release Model

Release phải là explicit state transition:

```text
IN_CUSTODY
    ↓
RELEASE_AUTHORIZED
    ↓
RELEASE_PROCESSING
    ↓
RELEASED
```

Không được suy ra release chỉ từ:

```text
date >= expected_end_date
```

nếu legal rules yêu cầu additional authorization.

---

# 703.18 — Release Package

Release package có thể bao gồm:

```text
identity documents
legal documents
conditions
supervision information
housing information
employment/training information
healthcare continuity references
program references
contact information
```

Mọi component phải có provenance.

---

# 703.19 — Reentry Runtime

Reentry là một lifecycle chứ không phải một event.

```text
PRE_RELEASE
    ↓
RELEASE
    ↓
INITIAL_REENTRY
    ↓
STABILIZATION
    ↓
COMMUNITY_INTEGRATION
    ↓
SUPPORT_COMPLETE
```

Runtime phải hỗ trợ parallel plans:

```text
housing
employment
education
family
documents
transport
supervision
services
```

---

# 703.20 — Reentry Plan

```axiom
reentry_plan {
    subject
    release_date
    objectives
    obligations
    services
    milestones
    dependencies
    providers
    status
}
```

Plan phải có dependency graph.

Ví dụ:

```text
identity_document
      ↓
employment
      ↓
housing_stability
```

Runtime phải phát hiện dependency failure.

---

# 703.21 — Case Management

Correctional case manager phải có:

```text
case
tasks
milestones
appointments
documents
providers
events
alerts
```

Case management không được trở thành một hidden legal decision engine.

---

# 703.22 — Provider Model

Provider:

```axiom
provider {
    provider_id
    organization
    service_types
    jurisdiction
    authorization
    availability
}
```

Phải hỗ trợ nhiều provider cùng phục vụ một subject.

---

# 703.23 — Consent & Authorization

Sensitive information access phải yêu cầu:

```text
legal_authority
role
purpose
scope
time_window
```

Không được phép:

```text
role == administrator
    ⇒ access_everything
```

Access phải được kiểm soát theo capability.

---

# 703.24 — Privacy Boundary

Các domain phải được partition:

```text
LEGAL
CUSTODY
MEDICAL
EDUCATION
FAMILY
EMPLOYMENT
FINANCIAL
SUPERVISION
```

Một component không được tự động đọc toàn bộ subject record.

---

# 703.25 — Correctional Capability Model

Capability examples:

```text
custody.read
custody.assign
custody.transfer
sentence.read
sentence.execute
probation.manage
program.enroll
program.verify
release.prepare
release.execute
reentry.manage
case.manage
```

Capability phải có:

```text
issuer
subject
scope
expiration
revocation
audit_reference
```

---

# 703.26 — Administrative Separation

Hệ thống phải phân biệt:

```text
decision authority
execution authority
case management authority
service provider
auditor
observer
AI agent
```

Không một AI agent nào mặc định sở hữu toàn bộ capabilities.

---

# 703.27 — AI Agent Boundary

AI agent trong `AXCORRECTIONS` phải hoạt động theo:

```text
observe
→ reason
→ propose
→ request authorization
→ execute only authorized action
→ record provenance
```

Không:

```text
observe
→ reason
→ autonomously punish
```

---

# 703.28 — Human Override

Authorized human operators phải có khả năng:

```text
pause
override
correct
review
reassign
terminate
```

nhưng mọi override phải tạo immutable audit event.

---

# 703.29 — Emergency Operations

Emergency actions phải có:

```text
emergency_authority
reason
scope
operator
timestamp
actions
post_event_review
```

Emergency mode không được trở thành bypass vĩnh viễn của authorization model.

---

# 703.30 — Audit

Toàn bộ lifecycle phải replay được:

```text
Judgment
→ Sentence
→ Custody
→ Placement
→ Transfer
→ Program
→ Supervision
→ Release
→ Reentry
```

Auditor phải có thể trả lời:

```text
Who?
What?
When?
Under which authority?
Using which rule version?
Using which data?
With which AI assistance?
What changed?
Why was the action permitted?
```

---

# 703.31 — Immutable Event Architecture

Core architecture:

```text
Authoritative State
        ↑
   Event Stream
        ↑
Authorized Commands
        ↑
Capabilities
```

Không cho phép arbitrary database mutation bỏ qua command/event layer.

---

# 703.32 — Temporal Semantics

Mọi authoritative record phải có:

```text
effective_time
recorded_time
authority_time
```

Phải phân biệt:

```text
when something happened
```

với:

```text
when system recorded it
```

và:

```text
when legal authority became effective
```

---

# 703.33 — Rule Versioning

Correctional rules phải versioned:

```text
rule_id
jurisdiction
version
effective_from
effective_to
```

Historical execution phải replay được bằng đúng rule version đã áp dụng.

---

# 703.34 — Multi-Jurisdiction Runtime

Một deployment có thể quản lý:

```text
national
state/province
county
municipal
tribal
special jurisdiction
```

Mỗi jurisdiction có:

```text
legal rules
authority hierarchy
sentence rules
custody rules
release rules
supervision rules
```

Không hard-code một quốc gia vào runtime core.

---

# 703.35 — Interoperability

`AXCORRECTIONS` phải cung cấp native interfaces cho:

```text
AXJUSTICE
AXLAW
AXIDENTITY
AXHEALTH
AXEDUCATION
AXEMPLOYMENT
AXHOUSING
AXFINANCE
```

Interface phải typed và capability-controlled.

---

# 703.36 — External Agency Interface

External agencies không được truy cập trực tiếp internal state.

Thay vào đó:

```text
request
→ authorization
→ scoped projection
→ response
→ audit
```

---

# 703.37 — Data Projection

Một agency chỉ nhận projection cần thiết:

```text
SubjectProjection
SentenceProjection
SupervisionProjection
ProgramProjection
ReleaseProjection
```

Không expose internal database schema.

---

# 703.38 — Failure Model

Phải chịu được:

```text
network failure
database failure
service failure
duplicate command
out-of-order event
partial transaction
operator disconnect
AI service failure
```

Không được tạo double execution.

---

# 703.39 — Idempotency

Các command nguy hiểm phải idempotent:

```text
release
transfer
placement
enrollment
termination
```

Một command được gửi hai lần không được tạo hai hành động.

---

# 703.40 — Distributed Consistency

Authoritative transitions phải sử dụng:

```text
transaction id
command id
event id
causal sequence
```

Distributed replicas phải có thể xác định canonical ordering.

---

# 703.41 — Offline Operation

Facility/runtime node có thể mất kết nối nhưng vẫn phải:

```text
record authorized local events
```

Khi reconnect:

```text
local events
→ validation
→ causal reconciliation
→ authoritative commit
```

Không cho phép offline node tự tạo authority mới.

---

# 703.42 — Security

Mọi correctional system phải chống:

```text
unauthorized access
privilege escalation
record tampering
identity spoofing
command replay
audit deletion
AI prompt injection
malicious external integration
```

---

# 703.43 — AI Prompt-Injection Boundary

External text không được trực tiếp trở thành executable instruction.

Ví dụ:

```text
case_note
message
document
provider_text
```

phải được xem là:

```text
UNTRUSTED_DATA
```

AI agent phải phân biệt:

```text
data
instruction
authority
command
```

---

# 703.44 — Explainability

AI-assisted action phải lưu:

```text
model
model_version
input references
retrieval references
output
confidence if applicable
policy/rule references
human reviewer
final action
```

Không cần lưu chain-of-thought nội bộ.

Phải lưu **decision provenance**, không phải hidden reasoning.

---

# 703.45 — Human Review Gates

Các action nhạy cảm phải có configurable review gate:

```text
placement
disciplinary action
release
supervision modification
program termination
high-impact classification
```

Runtime phải hỗ trợ:

```text
AUTO_ALLOWED
HUMAN_REVIEW_REQUIRED
MULTI_APPROVAL_REQUIRED
LEGAL_AUTHORITY_REQUIRED
```

---

# 703.46 — Risk Classification

Không được coi risk score là legal fact.

Model:

```text
RiskAssessment {
    source
    model
    version
    input_time
    result
    uncertainty
}
```

Risk assessment chỉ là derived information.

---

# 703.47 — No Hidden Punishment

Hệ thống không được biến:

```text
low score
AI recommendation
behavioral prediction
administrative flag
```

thành punishment nếu không có explicit legal authority.

---

# 703.48 — Accessibility

Correctional applications phải hỗ trợ:

```text
keyboard navigation
screen readers
large text
high contrast
multilingual UI
assistive technologies
```

Accessibility không được thay đổi semantic meaning của legal records.

---

# 703.49 — Localization

Text/resource phải tách khỏi executable logic:

```text
locale
jurisdiction
terminology
date format
calendar
number format
legal terminology
```

---

# 703.50 — Internationalization

Core phải UTF-8 native.

Identifier và legal document system phải hỗ trợ Unicode đầy đủ.

Không được giả định:

```text
ASCII-only names
Latin-only names
Western date formats
single-language legal systems
```

---

# 703.51 — Performance Architecture

Runtime phải hỗ trợ:

```text
millions of subjects
millions of events/day
large historical event stores
high-concurrency case management
```

Hot path phải tránh:

```text
global locks
unnecessary allocations
full-record scans
unbounded object graphs
```

---

# 703.52 — Storage Architecture

Recommended logical separation:

```text
authoritative event store
current-state index
projection store
document store
audit store
analytics store
AI artifact store
```

Analytics/AI store không được trở thành authoritative source.

---

# 703.53 — Query Model

Queries phải phân biệt:

```text
authoritative query
derived query
analytics query
AI query
```

Không được dùng approximate analytics làm authoritative legal state.

---

# 703.54 — Event Sourcing Boundary

Không bắt buộc toàn bộ application phải event-sourced.

Nhưng:

> **mọi legally significant state transition phải có immutable event provenance.**

Đây là architectural invariant.

---

# 703.55 — Document Integrity

Documents phải có:

```text
document_id
content_hash
issuer
created_at
effective_at
version
signature
authority
```

Document replacement phải tạo version mới.

---

# 703.56 — Digital Signature

Legal/administrative commands có thể yêu cầu:

```text
signature
certificate
issuer
timestamp
revocation status
```

Verification phải deterministic.

---

# 703.57 — Records Retention

Retention policy phải hỗ trợ:

```text
active
retained
archived
sealed
restricted
destroyed
```

Nhưng legal hold phải ngăn destruction.

---

# 703.58 — Legal Hold

```axiom
legal_hold {
    hold_id
    authority
    scope
    start
    release_condition
}
```

Khi active:

```text
destructive operation → denied
```

---

# 703.59 — Data Correction

Historical record không được sửa trực tiếp.

Sai record:

```text
original_event
    ↓
correction_event
    ↓
derived_state
```

Auditor phải thấy cả hai.

---

# 703.60 — Reconciliation

Runtime phải hỗ trợ reconciliation giữa:

```text
court record
correctional record
supervision record
facility record
provider record
```

Conflict phải trở thành explicit:

```text
CONFLICT_DETECTED
```

không âm thầm chọn một record.

---

# 703.61 — State Machine Verification

Các transition phải được kiểm tra bằng formal invariants:

```text
cannot release twice
cannot transfer released subject
cannot execute expired sentence
cannot modify finalized judgment
cannot create unauthorized custody
cannot execute revoked capability
```

---

# 703.62 — Security Invariants

Ví dụ:

```text
No capability → no action

No authority → no legally significant transition

No provenance → no authoritative state

Revoked capability → immediate denial

Expired authorization → denial
```

---

# 703.63 — Deterministic Replay

System phải có:

```text
replay(subject_id, timestamp)
```

cho phép tái tạo authoritative state tại một thời điểm lịch sử.

Output phải phụ thuộc vào:

```text
events
rule versions
configuration versions
authorization state
```

---

# 703.64 — Simulation Mode

Phải có simulation:

```text
simulate(sentence)
simulate(custody)
simulate(release)
simulate(reentry)
```

Simulation không được mutate authoritative state.

---

# 703.65 — What-if Planning

Case manager có thể:

```text
simulate program plan
simulate release plan
simulate resource allocation
simulate supervision schedule
```

nhưng output phải được đánh dấu:

```text
SIMULATION
```

và không được trở thành legal fact.

---

# 703.66 — Resource Optimization Boundary

AI/system optimization có thể tối ưu:

```text
facility capacity
staff scheduling
program capacity
transport
appointments
```

nhưng không được tối ưu theo mục tiêu làm thay đổi legal rights hoặc sentence.

---

# 703.67 — Metrics

Operational metrics:

```text
population
capacity
program utilization
case backlog
release preparation status
reentry completion
service availability
```

Không được coi operational metric là judgment về một cá nhân.

---

# 703.68 — Privacy-Preserving Analytics

Analytics phải hỗ trợ:

```text
aggregation
pseudonymization
access-controlled cohorts
minimum necessary data
```

Không được expose individual-level data nếu không có authorization.

---

# 703.69 — Testing

Phải có test suites:

```text
sentence tests
custody tests
transfer tests
release tests
probation tests
program tests
reentry tests
authorization tests
audit tests
replay tests
failure tests
security tests
AI-boundary tests
```

---

# 703.70 — Property Tests

Các invariant phải được property-tested:

```text
double release impossible
unauthorized transition impossible
historical event immutable
replay deterministic
command idempotent
revoked capability denied
simulation does not mutate state
```

---

# 703.71 — End-to-End Test

Canonical test:

```text
Judgment
→ Sentence
→ Custody
→ Placement
→ Program
→ Supervision
→ Release
→ Reentry
→ Completion
```

Toàn bộ lifecycle phải replay được từ event ledger.

---

# 703.72 — Crash Recovery

Nếu process crash giữa:

```text
command
→ authorization
→ event
→ projection
```

system phải recover mà không:

```text
duplicate action
lost legal event
corrupt state
```

---

# 703.73 — Transaction Boundary

Legally significant operation phải có atomicity:

```text
authorization
+
command acceptance
+
authoritative event
```

Projection có thể eventually consistent nhưng authoritative event không được mất.

---

# 703.74 — Observability

Metrics:

```text
command latency
event latency
projection lag
authorization failures
reconciliation conflicts
AI recommendation volume
human review latency
```

Tracing phải liên kết:

```text
request
→ command
→ authorization
→ event
→ projection
```

---

# 703.75 — Operational Alerts

Alerts có thể bao gồm:

```text
release deadline approaching
missing release requirement
expired authorization
unresolved violation review
facility capacity threshold
program unavailable
reentry dependency blocked
record reconciliation conflict
```

Alert không tự tạo legal action.

---

# 703.76 — Inter-Axiom Contract

Các boundary:

```text
AXJUSTICE → AXCORRECTIONS
AXCORRECTIONS → AXHEALTH
AXCORRECTIONS → AXEDUCATION
AXCORRECTIONS → AXEMPLOYMENT
AXCORRECTIONS → AXHOUSING
```

phải sử dụng stable typed contracts.

---

# 703.77 — Contract Versioning

Contract:

```text
namespace
version
schema
capabilities
compatibility
```

Không được silently break historical records.

---

# 703.78 — Migration

Schema migration phải:

```text
versioned
reversible where possible
audited
deterministic
tested
```

Không được rewrite historical events để phù hợp schema mới.

---

# 703.79 — Governance Boundary

`AXCORRECTIONS` phải cho phép jurisdiction định nghĩa:

```text
authorized actors
legal rules
review requirements
retention
release procedures
supervision procedures
```

nhưng core runtime vẫn bảo đảm:

```text
authorization
provenance
auditability
immutability
determinism
```

---

# 703.80 — AI Civilization-Scale Constraint

Axiom có thể triển khai AI agents ở quy mô lớn:

```text
case agents
facility agents
reentry agents
resource agents
audit agents
translation agents
document agents
```

Nhưng agent architecture phải tuân thủ:

```text
bounded authority
least privilege
explicit capability
immutable provenance
human/legal authority boundaries
```

Không có khái niệm:

```text
super-agent with unrestricted correctional authority
```

---

# 703.81 — Core Runtime API

Logical API tối thiểu:

```text
create_sentence()
execute_sentence()
get_custody_state()
place_subject()
transfer_subject()
create_supervision()
record_compliance()
record_violation()
enroll_program()
complete_program()
prepare_release()
authorize_release()
execute_release()
create_reentry_plan()
update_reentry_plan()
reconcile_record()
replay_state()
simulate_execution()
```

---

# 703.82 — Native Axiom Representation

Không thiết kế `AXCORRECTIONS` như một external application framework.

Nó phải là native Axiom domain runtime:

```text
types
traits
capabilities
effects
events
queries
state machines
contracts
```

và có thể được compiler tối ưu trực tiếp.

---

# 703.83 — Effect System

Các operation phải khai báo effects:

```text
read
write
authorize
execute
transfer
release
audit
external_io
ai_inference
```

Ví dụ:

```axiom
fn execute_release(...) 
    effects [authorize, write, audit]
```

Compiler/runtime có thể kiểm tra capability/effect boundary.

---

# 703.84 — Capability + Effect Enforcement

Một operation chỉ được execute nếu:

```text
required_effect
+
required_capability
+
valid_authority
```

đều thỏa mãn.

Đây là compiler/runtime security boundary.

---

# 703.85 — No Ambient Authority

Code không được tự động có:

```text
database access
filesystem access
network access
identity access
legal authority
custody authority
```

Mọi authority phải explicit.

---

# 703.86 — Agent Sandboxing

AI agents phải chạy trong sandbox:

```text
agent
  ├── capabilities
  ├── effect budget
  ├── data scope
  ├── jurisdiction scope
  └── time scope
```

Agent không thể tự mở rộng scope.

---

# 703.87 — Audit of AI

Mọi AI-assisted operation phải lưu:

```text
agent_id
model_id
model_version
capability_context
input_reference
output_reference
human_review
final_command
```

---

# 703.88 — AI Failure Safety

Nếu AI service:

```text
fails
times out
hallucinates
returns invalid schema
loses context
```

thì:

```text
authoritative state remains unchanged
```

AI failure không được làm mất legal state.

---

# 703.89 — Deterministic Administrative Core

AI có thể nằm trên administrative core:

```text
             AI
              ↓
       recommendation
              ↓
     authorization layer
              ↓
       command engine
              ↓
     authoritative events
```

Không:

```text
AI → direct database mutation
```

---

# 703.90 — Completion Criteria

`BOOTSTRAP-703` chỉ được coi là complete khi:

1. Sentence execution model frozen.
2. Custody state machine frozen.
3. Placement/transfer semantics frozen.
4. Probation model frozen.
5. Rehabilitation/program model frozen.
6. Release model frozen.
7. Reentry model frozen.
8. Capability model frozen.
9. AI authority boundary frozen.
10. Immutable event model frozen.
11. Temporal semantics frozen.
12. Replay semantics frozen.
13. Multi-jurisdiction model frozen.
14. Privacy boundaries frozen.
15. Failure/recovery model frozen.
16. Security invariants frozen.
17. Simulation semantics frozen.
18. Native Axiom API contract frozen.
19. End-to-end lifecycle test defined.
20. No authoritative legal decision can be generated by `AXCORRECTIONS` itself.

---

# 703.91 — Canonical Architecture

```text
                    ┌─────────────────────┐
                    │      AXLAW          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    AXJUSTICE        │
                    │ Judgment / Finality │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   AXCORRECTIONS     │
                    │                     │
                    │ Sentence            │
                    │ Custody             │
                    │ Placement           │
                    │ Transfer            │
                    │ Probation           │
                    │ Programs            │
                    │ Release             │
                    │ Reentry             │
                    └──────┬──────┬───────┘
                           │      │
             ┌─────────────┘      └─────────────┐
             ▼                                  ▼
      ┌──────────────┐                   ┌──────────────┐
      │ Human/Legal  │                   │ AI Agents    │
      │ Authority    │                   │ Recommend    │
      └──────┬───────┘                   └──────┬───────┘
             │                                  │
             └──────────────┬───────────────────┘
                            ▼
                  ┌────────────────────┐
                  │ Capability + Effect│
                  │ Authorization      │
                  └─────────┬──────────┘
                            ▼
                  ┌────────────────────┐
                  │ Command Engine     │
                  └─────────┬──────────┘
                            ▼
                  ┌────────────────────┐
                  │ Immutable Event    │
                  │ Ledger             │
                  └─────────┬──────────┘
                            ▼
                  ┌────────────────────┐
                  │ State / Projection │
                  └────────────────────┘
```

---

# 703.92 — Architectural Invariants

Các invariant sau được **FROZEN**:

```text
AXC-INV-01  Judgment authority belongs to AXJUSTICE.
AXC-INV-02  AXCORRECTIONS executes; it does not adjudicate.
AXC-INV-03  Legally significant transitions require explicit authority.
AXC-INV-04  Historical events are immutable.
AXC-INV-05  Correction is represented by superseding events.
AXC-INV-06  AI recommendation is not legal authority.
AXC-INV-07  Risk assessment is not legal fact.
AXC-INV-08  No ambient correctional authority exists.
AXC-INV-09  Every authoritative action has provenance.
AXC-INV-10  Every sensitive action is capability-controlled.
AXC-INV-11  Revoked capability cannot authorize new actions.
AXC-INV-12  Replay of authoritative history is deterministic.
AXC-INV-13  Simulation cannot mutate authoritative state.
AXC-INV-14  AI failure cannot corrupt authoritative state.
AXC-INV-15  Historical legal state remains reproducible.
AXC-INV-16  Jurisdiction-specific rules are versioned.
AXC-INV-17  Analytics cannot become authoritative legal state.
AXC-INV-18  External agencies receive scoped projections.
AXC-INV-19  Offline operation cannot create new authority.
AXC-INV-20  No correctional AI agent has unrestricted authority.
```

---

## BOOTSTRAP-703 — Definition of Done

```text
BOOTSTRAP-703
STATUS: COMPLETE / FROZEN

AXCORRECTIONS 5.0
    ├── Sentence Execution
    ├── Custody
    ├── Placement
    ├── Transfer
    ├── Probation
    ├── Rehabilitation
    ├── Program Management
    ├── Release
    ├── Reentry
    ├── Case Management
    ├── Capability Security
    ├── AI Agent Boundary
    ├── Immutable Audit
    ├── Temporal Semantics
    ├── Multi-Jurisdiction
    ├── Deterministic Replay
    ├── Simulation
    ├── Privacy
    ├── Failure Recovery
    └── Native Axiom Integration
```

**BOOTSTRAP-703 / AXCORRECTIONS hoàn thành architectural baseline.**

### Task kế tiếp

**BOOTSTRAP-704 — AXCIVIL: Native Civil Registry, Vital Records, Family Status, Property/Asset Identity & Civil-State Runtime 5.0**