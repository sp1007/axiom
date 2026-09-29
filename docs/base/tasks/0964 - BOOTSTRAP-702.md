Tiếp tục chuỗi kiến trúc Axiom. Task kế tiếp là **BOOTSTRAP-702: AXJUSTICE**.

:::writing{variant="document" id="58321" title="BOOTSTRAP-702 — AXJUSTICE: Native AI Civilization-Scale Justice, Courts, Legal Proceedings & Judicial Administration Runtime 5.0"}
# BOOTSTRAP-702
## AXJUSTICE — Native AI Civilization-Scale Justice, Courts, Legal Proceedings & Judicial Administration Runtime 5.0

**Status:** Architecture Specification  
**Layer:** Government / Legal Infrastructure  
**Namespace:** `AXJUSTICE`  
**Depends on:** `AXCORE`, `AXLAW`, `AXDOC`, `AXPOPULATION`, `AXGEO`, `AXFISCAL`  
**Integrates with:** `AXSECURITY`, `AXSAFETY`, `AXRESOURCE`, future `AXCORRECTIONS`  
**Primary principle:** Justice records must represent what was alleged, what was submitted as evidence, what was established by an authorized decision-maker, what was ordered, and what became final as distinct machine-verifiable states.

---

# 1. Mục tiêu

`AXJUSTICE` là runtime native của Axiom dành cho:

- quản trị tòa án;
- quản lý vụ án;
- hồ sơ tố tụng;
- lịch xét xử;
- đương sự và đại diện pháp lý;
- đơn kiện, cáo buộc, phản tố, kháng nghị;
- chứng cứ;
- lời khai;
- phiên điều trần;
- xét xử;
- quyết định;
- bản án;
- lệnh của tòa;
- kháng cáo;
- xem xét lại;
- hòa giải/ADR;
- phí và nghĩa vụ tài chính liên quan;
- công khai và niêm phong hồ sơ;
- quản lý thời hạn tố tụng;
- quản trị thẩm phán, thư ký và cán bộ tòa;
- quản trị bồi thẩm đoàn nếu hệ thống pháp luật hỗ trợ;
- legal aid;
- liên thông với cơ quan công tố, điều tra, thi hành án và cơ sở giam giữ.

`AXJUSTICE` **không định nghĩa luật nội dung**.

Luật, thẩm quyền, điều kiện, quyền và nghĩa vụ phải đến từ `AXLAW` hoặc các module luật chuyên ngành.

---

# 2. Nguyên tắc nền tảng

```text
AXLAW       = nguồn của pháp luật và thẩm quyền
AXJUSTICE   = thực thi quy trình tư pháp
AXDOC       = nguồn của tài liệu và phiên bản tài liệu
AXPOPULATION = định danh chủ thể
AXGEO       = sự thật địa lý/phạm vi tài phán
```

`AXJUSTICE` không được biến thành một "AI judge".

Kiến trúc bắt buộc:

```text
LAW
  ↓
JURISDICTION
  ↓
PROCEDURE
  ↓
CLAIM / CHARGE
  ↓
EVIDENCE
  ↓
HEARING / TRIAL
  ↓
AUTHORIZED DECISION
  ↓
ORDER / JUDGMENT
  ↓
APPEAL / REVIEW
  ↓
FINALITY
  ↓
ENFORCEMENT INTERFACE
```

---

# 3. Semantic Firewall

Đây là phần bắt buộc của runtime.

Các khái niệm sau **không được đồng nhất**:

```text
Allegation       != Fact
Claim            != Finding
Charge           != Guilt
Accusation       != Conviction
Evidence         != Fact
Evidence         != Proof
Testimony        != Finding
Statement        != Admission
Suspicion        != Finding
Investigation    != Adjudication
Detention        != Conviction
Arrest           != Guilt
Warrant          != Conviction
Order            != Judgment
Judgment         != Finality
Appeal           != Reversal
Appeal           != Automatic Stay
Filing           != Service
Service          != NoticeRead
Notice           != Hearing
Hearing          != Trial
Recommendation   != JudicialDecision
AIAnalysis       != Finding
AIConfidence     != LegalCertainty
Document         != Authenticity
DocumentVersion  != DocumentTruth
DigitalSignature != SubstantiveTruth
CalendarEntry    != LegalDeadline
DeadlineEstimate != DeadlineDetermination
```

Đây là **semantic safety boundary cấp compiler/runtime**.

Không chỉ là quy ước tài liệu.

---

# 4. Jurisdiction

## 4.1 Native model

```axiom
struct Jurisdiction {
    id: JurisdictionId
    legal_system: LegalSystemId
    territory: GeoScope
    authority: AuthorityRef
    effective_from: Instant
    effective_until: Option<Instant>
}
```

Một vụ án phải có jurisdiction context.

```axiom
struct JurisdictionDecision {
    court: CourtId
    subject_matter: SubjectMatter
    territorial_basis: GeoScope
    temporal_basis: TimeRange
    authority_source: LawRef
    determined_by: DecisionRef
}
```

---

# 5. Court Model

```axiom
struct Court {
    id: CourtId
    jurisdiction: JurisdictionId
    level: CourtLevel
    name: String
    divisions: Vec<DivisionId>
    registry: RegistryId
    status: CourtStatus
}
```

Các cấp tòa là dữ liệu cấu hình.

Không hard-code:

```text
trial
appeal
supreme
constitutional
```

vì hệ thống pháp luật khác nhau.

---

# 6. Court Division

```axiom
struct CourtDivision {
    id: DivisionId
    court: CourtId
    jurisdiction_scope: JurisdictionScope
    subject_domains: Set<LegalDomain>
}
```

Ví dụ:

```text
Civil
Criminal
Family
Juvenile
Commercial
Administrative
Labor
Tax
Constitutional
Specialized
```

Không domain nào được mặc định tồn tại trong core.

---

# 7. Judicial Actor

```axiom
struct JudicialOfficer {
    id: PersonId
    role: JudicialRole
    court: CourtId
    authority_scope: AuthorityScope
    appointment: AppointmentRef
    active_from: Instant
    active_until: Option<Instant>
}
```

Vai trò có thể gồm:

```text
Judge
ChiefJudge
Magistrate
Registrar
Clerk
CourtAdministrator
Bailiff
Mediator
JuryOfficer
```

---

# 8. Party Model

```axiom
struct Party {
    id: PartyId
    person: Option<PersonId>
    organization: Option<OrganizationId>
    legal_role: LegalRole
    representation: RepresentationRef
}
```

Một người có thể xuất hiện trong nhiều vụ án với vai trò khác nhau.

Không được suy luận:

```text
Party == GuiltyPerson
```

---

# 9. Legal Representation

```axiom
struct Representation {
    represented_party: PartyId
    representative: PersonId
    authority: RepresentationAuthority
    valid_from: Instant
    valid_until: Option<Instant>
}
```

Các trạng thái:

```text
PrivateCounsel
PublicDefender
LegalAid
SelfRepresented
Guardian
AuthorizedRepresentative
```

---

# 10. Conflict of Interest

```axiom
struct ConflictCheck {
    actor: PersonId
    case: CaseId
    conflicts: Vec<Conflict>
    result: ConflictResult
    reviewed_by: PersonId
}
```

Nếu xung đột yêu cầu recusal:

```text
ACTIVE
→ CONFLICT_DETECTED
→ RECUSAL_REQUESTED
→ RECUSAL_DECIDED
→ REASSIGNMENT
```

AI chỉ được phát hiện hoặc cảnh báo.

AI không tự quyết định recusal.

---

# 11. Case

```axiom
struct Case {
    id: CaseId
    jurisdiction: JurisdictionId
    court: CourtId
    division: DivisionId
    case_type: CaseType
    opened_at: Instant
    status: CaseStatus
    parties: Vec<PartyId>
    assigned_panel: PanelId
}
```

---

# 12. Case Lifecycle

Lifecycle chuẩn:

```text
INTAKE
  ↓
REGISTRATION
  ↓
JURISDICTION_CHECK
  ↓
SERVICE / NOTICE
  ↓
PLEADINGS
  ↓
DISCOVERY
  ↓
EVIDENCE
  ↓
HEARINGS
  ↓
TRIAL / ADJUDICATION
  ↓
DECISION
  ↓
JUDGMENT
  ↓
APPEAL / REVIEW
  ↓
FINALITY
  ↓
ENFORCEMENT
  ↓
CLOSURE
  ↓
RETENTION / ARCHIVE
```

Không phải mọi loại vụ án đều phải đi qua mọi state.

---

# 13. Filing

```axiom
struct Filing {
    id: FilingId
    case: CaseId
    filed_by: PartyId
    filing_type: FilingType
    submitted_at: Instant
    documents: Vec<DocumentRef>
    signature: Signature
    status: FilingStatus
}
```

Filing phải có:

```text
author
timestamp
case
document version
signature state
submission channel
validation result
```

---

# 14. Pleading

```axiom
struct Pleading {
    id: PleadingId
    case: CaseId
    party: PartyId
    claims: Vec<ClaimId>
    defenses: Vec<DefenseId>
    document: DocumentRef
}
```

---

# 15. Claim

```axiom
struct Claim {
    id: ClaimId
    asserted_by: PartyId
    against: PartyId
    legal_basis: Vec<LawRef>
    factual_assertions: Vec<FactualAssertionId>
    requested_relief: Vec<Relief>
    status: ClaimStatus
}
```

Một `Claim` không trở thành `Finding` chỉ vì được đưa vào hồ sơ.

---

# 16. Criminal Charge

```axiom
struct Charge {
    id: ChargeId
    case: CaseId
    defendant: PartyId
    offense: OffenseRef
    legal_basis: LawRef
    factual_allegations: Vec<FactualAssertionId>
    status: ChargeStatus
}
```

Các trạng thái độc lập:

```text
ALLEGED
FILED
ACCEPTED
AMENDED
DISMISSED
WITHDRAWN
ADJUDICATED
```

Không tồn tại implicit conversion:

```text
CHARGE → GUILTY
```

---

# 17. Evidence

```axiom
struct Evidence {
    id: EvidenceId
    case: CaseId
    evidence_type: EvidenceType
    source: EvidenceSource
    provenance: ProvenanceChain
    authenticity: AuthenticityState
    admissibility: AdmissibilityState
    status: EvidenceStatus
}
```

Evidence types:

```text
Document
Object
Image
Video
Audio
DigitalArtifact
PhysicalArtifact
Testimony
ExpertOpinion
Record
Metadata
ForensicResult
```

---

# 18. Evidence Provenance

```axiom
struct ProvenanceEvent {
    evidence: EvidenceId
    actor: ActorId
    action: ProvenanceAction
    timestamp: Instant
    location: Option<GeoPoint>
    previous_hash: Hash
    new_hash: Hash
}
```

Mục tiêu:

```text
WHO
WHAT
WHEN
WHERE
FROM_WHERE
TO_WHERE
WHICH_VERSION
```

Mọi thay đổi evidence phải tạo provenance event.

Không overwrite lịch sử.

---

# 19. Chain of Custody

```axiom
struct CustodyTransfer {
    evidence: EvidenceId
    from: CustodianId
    to: CustodianId
    transferred_at: Instant
    reason: String
    signature: Signature
}
```

Runtime phải phát hiện:

```text
missing transfer
duplicate custody
timestamp anomaly
hash mismatch
unauthorized custodian
```

AI có thể cảnh báo anomaly.

AI không tự tuyên bố evidence gian lận.

---

# 20. Evidence Admissibility

```axiom
enum AdmissibilityState {
    Unknown
    Pending
    Admitted
    Excluded
    Limited
    Withdrawn
}
```

`Admissibility` là trạng thái tố tụng.

Không được suy ra từ:

```text
AIConfidence
SourceReliabilityScore
DocumentQuality
```

---

# 21. Witness

```axiom
struct Witness {
    id: WitnessId
    party_relation: WitnessRelation
    testimony_refs: Vec<TestimonyId>
    protection: WitnessProtection
}
```

---

# 22. Testimony

```axiom
struct Testimony {
    id: TestimonyId
    witness: WitnessId
    hearing: HearingId
    transcript: DocumentRef
    interpreter: Option<PersonId>
}
```

Transcript là bản ghi.

Transcript không tự động trở thành finding.

---

# 23. Expert

```axiom
struct ExpertOpinion {
    id: ExpertOpinionId
    expert: PersonId
    field: Expertise
    methodology: DocumentRef
    opinion_document: DocumentRef
    disclosures: Vec<Disclosure>
}
```

---

# 24. Hearing

```axiom
struct Hearing {
    id: HearingId
    case: CaseId
    hearing_type: HearingType
    scheduled_start: Instant
    scheduled_end: Instant
    participants: Vec<ParticipantId>
    location: HearingLocation
    status: HearingStatus
}
```

---

# 25. Hearing State Machine

```text
SCHEDULED
→ NOTICED
→ CONFIRMED
→ OPENED
→ IN_PROGRESS
→ ADJOURNED / COMPLETED
→ RECORDED
→ SEALED / PUBLISHED
```

---

# 26. Legal Notice

```axiom
struct LegalNotice {
    id: NoticeId
    recipient: PartyId
    case: CaseId
    legal_event: LegalEventRef
    delivery_method: DeliveryMethod
    sent_at: Instant
    served_at: Option<Instant>
    status: NoticeStatus
}
```

Phải phân biệt:

```text
NOTICE_CREATED
NOTICE_SENT
NOTICE_DELIVERED
NOTICE_SERVED
NOTICE_READ
NOTICE_ACKNOWLEDGED
```

---

# 27. Due Process State

```axiom
struct ProceduralRightState {
    party: PartyId
    case: CaseId
    right: ProceduralRight
    status: RightStatus
    evidence: Vec<DocumentRef>
}
```

Các quyền có thể cấu hình:

```text
RightToNotice
RightToBeHeard
RightToCounsel
RightToInterpreter
RightToPresentEvidence
RightToChallengeEvidence
RightToAppeal
```

Không hard-code nội dung pháp luật.

---

# 28. Legal Deadline Engine

Deadline là một subsystem riêng.

```axiom
struct LegalDeadline {
    id: DeadlineId
    case: CaseId
    source: LawRef
    trigger: LegalEventRef
    start: Instant
    duration: Duration
    calendar_rule: CalendarRule
    tolling_rules: Vec<TollingRule>
    extension_rules: Vec<ExtensionRule>
    due_at: Instant
}
```

Engine phải hỗ trợ:

```text
calendar days
business days
court days
holidays
weekends
time zones
midnight boundaries
tolling
suspension
extension
reopening
jurisdiction-specific calendars
```

Không được dùng timer đơn giản thay cho legal deadline.

---

# 29. Deadline Determinism

Cùng:

```text
LAW VERSION
CASE STATE
EVENT HISTORY
CALENDAR
TIMEZONE
```

phải tạo cùng:

```text
DEADLINE
```

Runtime phải hỗ trợ deterministic replay.

---

# 30. Court Calendar

```axiom
struct CourtCalendar {
    court: CourtId
    entries: Vec<CalendarEntry>
}
```

Calendar entry không phải legal deadline.

```text
CalendarEntry != LegalDeadline
```

---

# 31. Judicial Panel

```axiom
struct JudicialPanel {
    id: PanelId
    members: Vec<JudicialOfficer>
    presiding: JudicialOfficer
    authority_scope: AuthorityScope
}
```

Quyền quyết định được kiểm tra runtime.

---

# 32. Judicial Decision

```axiom
struct JudicialDecision {
    id: DecisionId
    case: CaseId
    decision_maker: PanelId
    legal_basis: Vec<LawRef>
    findings: Vec<FindingId>
    reasoning_document: DocumentRef
    disposition: Disposition
    signed_at: Instant
}
```

Decision phải có chữ ký hợp lệ.

---

# 33. Finding

```axiom
struct Finding {
    id: FindingId
    issue: IssueId
    factual_basis: Vec<EvidenceId>
    legal_basis: Vec<LawRef>
    determined_by: DecisionId
}
```

`Finding` chỉ được tạo bởi actor có thẩm quyền.

Không cho:

```text
AI → Finding
```

trực tiếp.

---

# 34. Issue

```axiom
struct LegalIssue {
    id: IssueId
    case: CaseId
    question: DocumentRef
    governing_law: Vec<LawRef>
    status: IssueStatus
}
```

---

# 35. Judgment

```axiom
struct Judgment {
    id: JudgmentId
    case: CaseId
    decision: DecisionId
    orders: Vec<OrderId>
    issued_at: Instant
    finality: FinalityState
}
```

---

# 36. Court Order

```axiom
struct CourtOrder {
    id: OrderId
    court: CourtId
    case: CaseId
    issuer: JudicialOfficer
    legal_basis: Vec<LawRef>
    directives: Vec<Directive>
    effective_from: Instant
    effective_until: Option<Instant>
    status: OrderStatus
}
```

---

# 37. Warrant Boundary

Warrant là một loại legal order.

```text
WARRANT != GUILT
```

`AXJUSTICE` quản lý:

```text
issuance
validity
scope
expiration
withdrawal
service
execution-status
```

Việc thực thi vật lý thuộc cơ quan có thẩm quyền.

Không để `AXJUSTICE` tự điều khiển lực lượng cưỡng chế.

---

# 38. Enforcement Boundary

Kiến trúc:

```text
AXJUSTICE
    ↓
FINAL / EXECUTABLE ORDER
    ↓
ENFORCEMENT INTERFACE
    ↓
AUTHORIZED ENFORCEMENT SYSTEM
```

Không:

```text
AI
 ↓
AUTONOMOUS ENFORCEMENT
```

---

# 39. Appeal

```axiom
struct Appeal {
    id: AppealId
    source_case: CaseId
    appellant: PartyId
    grounds: Vec<AppealGround>
    filed_at: Instant
    status: AppealStatus
}
```

Các trạng thái:

```text
FILED
ACCEPTED
REJECTED
PENDING
HEARD
DECIDED
WITHDRAWN
FINAL
```

---

# 40. Review

Appeal và review là các process khác nhau.

```text
Appeal != Review
```

Một jurisdiction có thể có:

```text
appeal
reconsideration
revision
cassation
constitutional_review
administrative_review
```

Tất cả phải configurable.

---

# 41. Finality

```axiom
struct FinalityState {
    status: FinalityStatus
    effective_at: Instant
    source: LegalBasis
}
```

Không suy luận:

```text
JUDGMENT_ISSUED → FINAL
```

Finality phải được xác định theo luật và trạng thái tố tụng.

---

# 42. Stay

```axiom
struct Stay {
    order: OrderId
    scope: StayScope
    starts: Instant
    ends: Option<Instant>
}
```

Appeal không mặc định đồng nghĩa với stay.

---

# 43. ADR / Mediation

ADR là subsystem riêng:

```axiom
struct ADRProceeding {
    id: ADRId
    case: CaseId
    type: ADRType
    mediator: PersonId
    participants: Vec<PartyId>
    status: ADRStatus
}
```

ADR không được tự động biến thành judgment.

---

# 44. Jury

Jurisdiction hỗ trợ jury có thể bật module:

```axiom
struct JuryPanel {
    id: JuryId
    case: CaseId
    members: Vec<JuryMemberId>
    status: JuryStatus
}
```

Thông tin nhạy cảm phải được bảo vệ bằng access policy.

---

# 45. Sealed Records

```axiom
struct RecordVisibility {
    record: RecordId
    classification: VisibilityClass
    authority: AuthorityRef
    effective_from: Instant
    effective_until: Option<Instant>
}
```

Ví dụ:

```text
PUBLIC
RESTRICTED
SEALED
CONFIDENTIAL
PRIVILEGED
JUDICIAL_ONLY
```

---

# 46. Redaction

Redaction không được phá hủy bản gốc.

```text
ORIGINAL
    ↓
REDACTION_SPEC
    ↓
PUBLIC_VIEW
```

Bản gốc vẫn được quản lý theo retention/security policy.

---

# 47. Legal Privilege

Privilege phải là metadata pháp lý:

```axiom
struct PrivilegeClaim {
    record: RecordId
    asserted_by: PartyId
    privilege_type: PrivilegeType
    status: PrivilegeStatus
    authority: DecisionRef
}
```

AI không tự xác nhận privilege cuối cùng.

---

# 48. AI Subsystem

AI được phép:

```text
document classification
OCR
transcription
translation
legal retrieval
citation linking
timeline extraction
entity extraction
duplicate detection
deadline calculation assistance
case summarization
evidence indexing
contradiction detection
missing-document detection
anomaly detection
procedural checklist
search
simulation
```

AI không được tự động:

```text
determine guilt
determine innocence
determine liability
issue judgment
issue warrant
set sentence
deny bail
detain person
dismiss case
accept/reject evidence
make final finding
decide appeal
change finality
alter court record
```

---

# 49. AI Provenance

Mọi output AI phải lưu:

```axiom
struct AIJudicialArtifact {
    id: AIArtifactId
    model: ModelId
    model_version: String
    prompt_hash: Hash
    input_refs: Vec<RecordRef>
    output: DocumentRef
    generated_at: Instant
    human_review: ReviewState
}
```

Bắt buộc:

```text
AI output != authoritative court record
```

cho tới khi actor có thẩm quyền xác nhận theo procedure.

---

# 50. Source Traceability

Một AI summary phải truy ngược được:

```text
SUMMARY
 ↓
SOURCE DOCUMENTS
 ↓
DOCUMENT VERSIONS
 ↓
EVIDENCE / FILINGS
 ↓
EVENT HISTORY
```

Không chấp nhận summary không có provenance.

---

# 51. Human Authorization Gate

Các action nhạy cảm:

```text
ISSUE_ORDER
ISSUE_JUDGMENT
DETERMINE_FINDING
CHANGE_FINALITY
SEAL_RECORD
UNSEAL_RECORD
ISSUE_WARRANT
MODIFY_CASE_STATUS
DISMISS_CASE
ENTER_CONVICTION
IMPOSE_RELIEF
```

phải yêu cầu:

```text
AUTHORIZED_ACTOR
+
VALID_AUTHORITY
+
VALID_SIGNATURE
+
PROCEDURAL_STATE
```

---

# 52. Immutable Court Record

Court record phải có append-only event history.

```axiom
struct CourtEvent {
    id: EventId
    case: CaseId
    type: CourtEventType
    actor: ActorId
    timestamp: Instant
    payload_hash: Hash
    previous_hash: Hash
    signature: Signature
}
```

Không sửa event cũ.

Nếu correction:

```text
OLD_EVENT
    +
CORRECTION_EVENT
```

---

# 53. Case Event Stream

Topic chuẩn:

```text
justice.case.created
justice.filing.submitted
justice.notice.created
justice.notice.served
justice.hearing.scheduled
justice.hearing.opened
justice.evidence.submitted
justice.evidence.admitted
justice.evidence.excluded
justice.decision.signed
justice.order.issued
justice.judgment.issued
justice.appeal.filed
justice.review.opened
justice.finality.changed
justice.case.closed
```

---

# 54. Distributed Consistency

Một case có logical owner:

```text
CasePartition
```

Các state transition quan trọng phải serialized theo:

```text
case_id + sequence
```

Cho phép parallel:

```text
document indexing
AI retrieval
OCR
search indexing
analytics
notifications
```

Không parallel destructive mutation trên cùng authoritative state.

---

# 55. Offline Court Operation

Court registry có thể mất kết nối.

Runtime hỗ trợ:

```text
local append-only journal
signed offline events
monotonic sequence
reconciliation
conflict detection
duplicate suppression
later replication
```

Không cho offline actor tạo authority vượt delegation.

---

# 56. Delegated Authority

```axiom
struct JudicialDelegation {
    issuer: JudicialOfficer
    delegate: PersonId
    authority: AuthorityScope
    starts: Instant
    expires: Instant
    constraints: Vec<Constraint>
}
```

Runtime kiểm tra:

```text
scope
time
jurisdiction
case
action
```

---

# 57. Break-Glass

Trường hợp khẩn cấp:

```axiom
struct JusticeBreakGlass {
    actor: ActorId
    reason: String
    scope: AuthorityScope
    expires: Instant
    justification: DocumentRef
}
```

Break-glass:

- không xóa access control;
- không biến thành permanent privilege;
- luôn tạo audit event;
- phải có expiry.

---

# 58. Access Control

Mô hình:

```text
RBAC
+
ABAC
+
CASE_SCOPE
+
LEGAL_PRIVILEGE
+
RECORD_CLASSIFICATION
```

Ví dụ:

```text
judge(case=A)
```

không mặc định có quyền:

```text
judge(case=B)
```

---

# 59. Data Isolation

Tenant/domain isolation:

```text
Jurisdiction
Court
Division
Case
Record
```

Một query không được vượt scope nếu capability không cho phép.

---

# 60. Privacy

PII được quản lý qua `AXPOPULATION`.

`AXJUSTICE` chỉ giữ:

```text
PersonRef
OrganizationRef
```

khi full identity không cần thiết.

---

# 61. Search Index

Search phải phân biệt:

```text
authoritative record
derived index
AI-generated index
public index
sealed index
```

Index hỏng không được làm thay đổi authoritative record.

---

# 62. Legal Knowledge Graph

```axiom
LegalGraph {
    Party
    Case
    Claim
    Charge
    Issue
    Evidence
    Law
    Finding
    Decision
    Order
    Judgment
    Appeal
}
```

Quan hệ:

```text
CASE --has_party--> PARTY
CASE --contains--> CLAIM
CLAIM --based_on--> LAW
CLAIM --supported_by--> EVIDENCE
CASE --raises--> ISSUE
DECISION --contains--> FINDING
FINDING --supported_by--> EVIDENCE
JUDGMENT --contains--> ORDER
APPEAL --reviews--> JUDGMENT
```

---

# 63. Legal Truth Layers

Axiom phải biểu diễn tối thiểu 5 tầng:

```text
ASSERTED
SUPPORTED
ADMITTED
FOUND
FINAL
```

Ví dụ:

```text
Party asserts X
    ≠
Evidence supports X
    ≠
Court admits evidence about X
    ≠
Court finds X
    ≠
Finding becomes final
```

Đây là một trong những invariant quan trọng nhất của `AXJUSTICE`.

---

# 64. Record Truth vs World Truth

Một judgment ghi:

```text
COURT_FOUND(X)
```

không có nghĩa runtime được phép biến thành:

```text
WORLD_FACT(X)
```

Runtime phải giữ provenance:

```text
ASSERTED_BY
FOUND_BY
LEGAL_EFFECT
EFFECTIVE_FROM
FINALITY
```

---

# 65. Correction Model

Sai sót hành chính:

```text
CorrectionRequest
→ Review
→ AuthorizedCorrection
→ CorrectionEvent
```

Không sửa trực tiếp immutable record.

---

# 66. Retention

```axiom
struct RetentionPolicy {
    record_class: RecordClass
    retain_for: Duration
    legal_basis: LawRef
    archive_mode: ArchiveMode
    destruction_rules: Vec<Rule>
}
```

Không xóa record chỉ vì:

```text
database_cleanup
storage_pressure
AI_optimization
```

---

# 67. Archive

Archive phải giữ:

```text
schema version
law version
document version
signature
event chain
metadata
hash
retention authority
```

Để có thể replay trạng thái lịch sử.

---

# 68. Temporal Legal State

Mỗi record quan trọng có:

```text
valid_time
transaction_time
```

Ví dụ:

```text
LAW VERSION A
valid: Jan-Jun

LAW VERSION B
valid: Jul-Dec
```

Case phát sinh trong A không được truy vấn như thể B luôn tồn tại.

---

# 69. Versioned Law Binding

Mọi quyết định phải tham chiếu:

```axiom
LawRef {
    law_id
    version
    effective_range
}
```

Không chỉ lưu:

```text
"Article 123"
```

mà phải biết chính xác phiên bản luật.

---

# 70. Multi-Jurisdiction

Core không hard-code một quốc gia.

```text
Country
State
Province
Municipality
Federal
Tribal
SpecialJurisdiction
International
```

là configuration/domain.

---

# 71. Language & Translation

Court record hỗ trợ:

```text
original_language
official_translation
interpreter
translation_version
translation_authority
```

Bản dịch không được overwrite bản gốc.

---

# 72. Time & Location

Tất cả timestamp authoritative dùng:

```text
Instant
```

UI có thể hiển thị:

```text
local date/time
court timezone
user timezone
```

Không lưu legal event chỉ bằng local wall-clock.

---

# 73. Notification Engine

Notification có:

```text
created
sent
delivered
served
acknowledged
expired
failed
```

Mỗi state độc lập.

---

# 74. Payment/Fee Boundary

`AXJUSTICE` có thể phát sinh:

```text
court_fee
filing_fee
fine_reference
bond_reference
cost_order
```

Nhưng accounting thuộc:

```text
AXFISCAL
```

Không duplicate financial ledger.

---

# 75. External Agency Boundary

Các hệ thống:

```text
Police
Prosecution
Defense
Corrections
Probation
Immigration
ChildProtection
TaxAuthority
```

không được truy cập trực tiếp toàn bộ case database.

Dùng capability-scoped interfaces.

---

# 76. API

Ví dụ:

```axiom
justice.case.create(...)
justice.case.get(...)
justice.case.assign(...)
justice.filing.submit(...)
justice.notice.issue(...)
justice.hearing.schedule(...)
justice.evidence.register(...)
justice.evidence.transfer(...)
justice.decision.prepare(...)
justice.decision.sign(...)
justice.order.issue(...)
justice.judgment.enter(...)
justice.appeal.file(...)
justice.finality.evaluate(...)
justice.record.seal(...)
justice.record.unseal(...)
```

`prepare` và `sign` phải là hai operation khác nhau.

---

# 77. Query Model

CQRS:

```text
COMMAND
    ↓
AUTHORITATIVE EVENT LOG
    ↓
PROJECTION
    ↓
QUERY
```

Không cho UI query trực tiếp authoritative mutation store để tự suy luận trạng thái.

---

# 78. Transaction Boundary

Một judicial mutation quan trọng phải atomic:

```text
VALIDATE_AUTHORITY
VALIDATE_PROCEDURE
VALIDATE_SIGNATURE
APPEND_EVENT
UPDATE_STATE
EMIT_EVENT
```

Nếu một bước thất bại:

```text
NO_PARTIAL_AUTHORITY_CHANGE
```

---

# 79. Idempotency

Mọi external command có:

```axiom
CommandId
```

Retry cùng command không tạo duplicate:

```text
ORDER
JUDGMENT
FILING
NOTICE
APPEAL
PAYMENT_REFERENCE
```

---

# 80. Security

Bắt buộc:

```text
encryption at rest
encryption in transit
signed events
key rotation
capability security
least privilege
tamper evidence
audit logging
secure deletion policy
```

---

# 81. AI Safety Invariants

### AJ-AI-001
AI không được tạo authoritative finding.

### AJ-AI-002
AI không được tự ký judicial decision.

### AJ-AI-003
AI không được thay đổi finality.

### AJ-AI-004
AI không được xóa court record.

### AJ-AI-005
AI output phải truy nguyên được nguồn.

### AJ-AI-006
AI confidence không được ánh xạ trực tiếp thành legal certainty.

### AJ-AI-007
AI recommendation phải phân biệt với judicial order.

### AJ-AI-008
AI summary không được thay thế original record.

### AJ-AI-009
AI translation không được overwrite original language.

### AJ-AI-010
Model version phải được ghi nhận.

---

# 82. Core Judicial Invariants

### AJ-001
Case phải thuộc jurisdiction hợp lệ.

### AJ-002
Authority phải phù hợp jurisdiction.

### AJ-003
Không actor nào được thực hiện action ngoài authority scope.

### AJ-004
Filing phải có case hoặc quy trình intake hợp lệ.

### AJ-005
Không evidence event được sửa destructive.

### AJ-006
Chain of custody phải giữ được lịch sử.

### AJ-007
Finding phải tham chiếu decision hợp lệ.

### AJ-008
Decision phải có authorized decision-maker.

### AJ-009
Judgment phải tham chiếu decision.

### AJ-010
Order phải có issuer hợp lệ.

### AJ-011
Appeal phải tham chiếu proceeding hợp lệ.

### AJ-012
Finality không được suy ra đơn giản từ judgment issuance.

### AJ-013
Notice phải phân biệt sent/served/read.

### AJ-014
Legal deadline phải có legal basis.

### AJ-015
Deadline calculation phải deterministic.

### AJ-016
Law reference phải versioned.

### AJ-017
Court record phải append-only.

### AJ-018
Correction phải tạo event mới.

### AJ-019
Sealed record không xuất hiện trong public projection.

### AJ-020
Redaction không phá bản gốc.

### AJ-021
Privilege phải có legal status riêng.

### AJ-022
Case assignment phải audit được.

### AJ-023
Recusal phải tạo audit trail.

### AJ-024
Delegation phải có expiry.

### AJ-025
Break-glass phải có reason.

### AJ-026
Break-glass phải có expiry.

### AJ-027
Offline event phải có signature.

### AJ-028
Offline sequence conflict phải detectable.

### AJ-029
Duplicate command phải idempotent.

### AJ-030
Unauthorized mutation phải bị reject.

### AJ-031
Document version không được bị overwrite.

### AJ-032
Evidence authenticity không đồng nghĩa admissibility.

### AJ-033
Admissibility không đồng nghĩa truth.

### AJ-034
Claim không đồng nghĩa finding.

### AJ-035
Charge không đồng nghĩa guilt.

### AJ-036
Detention không đồng nghĩa conviction.

### AJ-037
Warrant không đồng nghĩa conviction.

### AJ-038
Appeal không đồng nghĩa reversal.

### AJ-039
Appeal không tự động đồng nghĩa stay.

### AJ-040
Judgment không tự động đồng nghĩa finality.

### AJ-041
AI recommendation không đồng nghĩa decision.

### AJ-042
AI confidence không đồng nghĩa certainty.

### AJ-043
Calendar entry không đồng nghĩa legal deadline.

### AJ-044
Transcript không đồng nghĩa finding.

### AJ-045
Expert opinion không đồng nghĩa court finding.

### AJ-046
Public projection không được làm lộ sealed data.

### AJ-047
Cross-case access phải có capability.

### AJ-048
Cross-jurisdiction query phải được authorize.

### AJ-049
Historical state phải replay được.

### AJ-050
Law-version binding phải deterministic.

### AJ-051
Court record phải có tamper evidence.

### AJ-052
Authoritative event sequence phải monotonic.

### AJ-053
Invalid signature không được tạo authority.

### AJ-054
Expired authority không được thực hiện command.

### AJ-055
Expired order không được tự động coi là active.

### AJ-056
Withdrawn order không được xuất hiện như active order.

### AJ-057
Closed case không được mutation tùy tiện.

### AJ-058
Reopened case phải có legal basis.

### AJ-059
Record destruction phải tuân retention policy.

### AJ-060
AI indexing không được thay đổi authoritative semantics.

---

# 83. Performance Model

Mục tiêu:

```text
≥ 5M lightweight case/workflow events/sec
per large partitioned deployment
```

với:

```text
billions of records
millions of concurrent cases
```

Các operation hot-path:

```text
event append
case state transition
deadline lookup
authorization check
document reference
query projection
```

phải tránh:

```text
GC pauses
global locks
large object graphs
unbounded recursion
implicit allocations
```

---

# 84. Memory Model

`AXJUSTICE` không được yêu cầu GC.

Các object lớn:

```text
documents
transcripts
evidence blobs
media
AI artifacts
```

nằm ngoài hot state bằng:

```text
BlobRef
DocumentRef
ContentAddress
```

Case state chỉ giữ metadata và references.

---

# 85. Concurrency

Case mutation:

```text
single logical sequencer
```

Các read/index task:

```text
parallel
```

Ví dụ:

```text
Case 100 → shard A
Case 101 → shard B
Case 102 → shard C
```

Các case độc lập có thể xử lý song song.

---

# 86. Deterministic Replay

Cho:

```text
case_id
event_sequence
law_versions
calendar_versions
```

runtime phải tái tạo được:

```text
case state
```

tại bất kỳ historical point hợp lệ nào.

---

# 87. Audit

Audit record phải chứa:

```text
WHO
WHAT
WHEN
AUTHORITY
CASE
OBJECT
BEFORE
AFTER
SOURCE
SIGNATURE
```

AI-generated action cũng phải audit.

---

# 88. Testing

Compiler/runtime phải có tối thiểu:

```text
20,000 automated tests
```

phân bổ:

```text
unit
property
state-machine
fuzz
security
authorization
temporal
distributed
offline
replay
AI provenance
document integrity
cross-jurisdiction
```

---

# 89. Property Testing

Ví dụ property:

```text
replay(events) == live_state
```

và:

```text
apply(command twice)
==
apply(command once)
```

đối với command idempotent.

---

# 90. Fuzzing

Fuzz:

```text
case transitions
deadline rules
calendar rules
signatures
event ordering
duplicate commands
offline reconciliation
document versions
redaction
access control
```

---

# 91. Failure Injection

Phải test:

```text
network loss
clock skew
database crash
node crash
duplicate event
missing event
corrupted document
expired authority
revoked key
partial replication
concurrent filing
concurrent order
```

---

# 92. Observability

Native telemetry:

```axiom
justice.metrics(...)
justice.trace_case(...)
justice.audit(...)
justice.replay(...)
justice.deadline_explain(...)
```

`deadline_explain` phải trả:

```text
trigger
law
version
calendar
tolling
extensions
calculated result
```

để cán bộ có thể kiểm tra.

---

# 93. Explainability

Không dùng "AI explanation" thay cho legal reasoning.

System explanation phải trả:

```text
Which rule?
Which version?
Which event?
Which authority?
Which calculation?
Which document?
```

---

# 94. Compiler Integration

Compiler phải nhận biết semantic types:

```text
CaseId
PartyId
EvidenceId
DecisionId
JudgmentId
OrderId
LawRef
Deadline
Authority
```

Không cho implicit conversion:

```text
CaseId → PersonId
EvidenceId → FindingId
ClaimId → JudgmentId
```

---

# 95. Capability Types

Ví dụ:

```axiom
capability CaseRead
capability CaseWrite
capability EvidenceRead
capability EvidenceWrite
capability JudicialDecision
capability IssueOrder
capability SealRecord
capability AppealAdmin
```

Capability phải được type-check tại compile/runtime boundary.

---

# 96. DSL

Có thể cung cấp:

```axiom
case CriminalCase {
    jurisdiction = AXLAW.jurisdiction(...)
    parties(...)
    deadlines(...)
    evidence(...)
    hearings(...)
    decisions(...)
}
```

Nhưng DSL chỉ là syntax layer.

Semantic engine vẫn dùng core structures.

---

# 97. Court Workflow DSL

Ví dụ:

```axiom
workflow CivilCase {
    intake
    jurisdiction_check
    service
    pleadings
    evidence
    hearing
    decision
    judgment
    appeal?
    finality
    closure
}
```

Jurisdiction có thể override workflow.

---

# 98. No Hidden Legal Semantics

Compiler không được tự hiểu:

```text
criminal = guilty
appeal = stay
judgment = final
charge = conviction
```

Mọi semantic transition phải explicit.

---

# 99. Interoperability

API phải hỗ trợ:

```text
JSON
CBOR
MessagePack
binary Axiom ABI
signed event stream
document references
```

Nhưng authoritative internal representation dùng native Axiom types.

---

# 100. External Document Integrity

Document được tham chiếu bằng:

```text
DocumentId
Version
ContentHash
```

Không tin filename.

Ví dụ:

```text
complaint.pdf
```

không phải identity.

Identity:

```text
doc://case/123/version/7/hash/...
```

---

# 101. Security Classification

Mỗi record có thể có:

```text
classification
compartment
case_scope
party_scope
authority_scope
```

Access decision phải được đánh giá trước khi trả data.

---

# 102. Public Portal

Public-facing system chỉ đọc:

```text
public projection
```

Không query authoritative private database trực tiếp.

Có thể công khai:

```text
case number
hearing date
public orders
public judgments
public docket
```

theo policy của jurisdiction.

---

# 103. Legal AI Search

AI search phải trả:

```text
answer
+
source refs
+
document versions
+
law versions
+
confidence metadata
```

Không trả bare assertion.

---

# 104. Semantic Query

Ví dụ:

```axiom
find cases
where
    jurisdiction == J
    and status == Active
    and deadline.before(now + 7d)
```

Compiler đảm bảo:

```text
deadline
```

là legal deadline, không phải calendar date.

---

# 105. Case Timeline

Timeline phải phân biệt:

```text
ASSERTION
FILING
SERVICE
EVIDENCE
HEARING
DECISION
ORDER
APPEAL
FINALITY
```

Không tạo timeline bằng cách trộn mọi timestamp.

---

# 106. Data Quality

Các anomaly:

```text
missing party
missing authority
missing signature
invalid law version
orphan evidence
orphan order
expired authority
impossible timeline
duplicate case number
broken provenance
```

được đưa vào:

```text
DataQualityFinding
```

Không tự sửa.

---

# 107. Governance Boundary

`AXJUSTICE` không quyết định:

```text
what law should be
what punishment should exist
what rights should exist
what jurisdiction should legislate
```

Những vấn đề đó thuộc legal/government policy layer.

`AXJUSTICE` chỉ thực thi mô hình pháp lý đã được cấu hình và có thẩm quyền.

---

# 108. Reference Architecture

```text
                 ┌──────────────┐
                 │    AXLAW     │
                 └──────┬───────┘
                        │
                        ▼
┌──────────┐     ┌──────────────┐     ┌─────────────┐
│ AXPOPULATION │──►│  AXJUSTICE   │◄──│    AXDOC    │
└──────────┘     │              │     └─────────────┘
                 │ CASE ENGINE  │
                 │ EVIDENCE     │
                 │ PROCEDURE    │
                 │ COURT        │
                 │ DECISION     │
                 │ APPEAL       │
                 │ FINALITY     │
                 └──────┬───────┘
                        │
            ┌───────────┼────────────┐
            ▼           ▼            ▼
       AXFISCAL    AXSECURITY   AXCORRECTIONS
```

---

# 109. Canonical Lifecycle

```text
PERSON / ORGANIZATION
        ↓
PARTY
        ↓
CASE
        ↓
CLAIM / CHARGE
        ↓
PROCEDURAL NOTICE
        ↓
PLEADING
        ↓
EVIDENCE
        ↓
HEARING
        ↓
AUTHORIZED FINDING
        ↓
DECISION
        ↓
ORDER / JUDGMENT
        ↓
APPEAL / REVIEW
        ↓
FINALITY
        ↓
ENFORCEMENT INTERFACE
        ↓
CLOSURE
        ↓
ARCHIVE
```

---

# 110. Final AXJUSTICE Principle

```text
LAW DEFINES AUTHORITY.

COURTS APPLY PROCEDURE.

PARTIES ASSERT CLAIMS.

EVIDENCE RECORDS MATERIAL.

AUTHORIZED ACTORS MAKE DECISIONS.

ORDERS DEFINE LEGAL EFFECT.

APPEALS PROVIDE REVIEW.

FINALITY DEFINES LEGAL STATE.

AI ASSISTS, BUT DOES NOT BECOME THE JUDICIARY.

EVERY AUTHORITATIVE CHANGE IS SIGNED,
VERSIONED, AUDITED AND REPLAYABLE.
```

---

# 111. Acceptance Criteria

`BOOTSTRAP-702` chỉ được xem là hoàn thành khi:

1. Case lifecycle có state machine rõ ràng.
2. Jurisdiction được versioned.
3. Claim/Charge/Finding/Judgment được tách biệt.
4. Evidence provenance hoạt động.
5. Chain of custody bất biến.
6. Legal deadline deterministic.
7. Court record append-only.
8. Judicial authority được capability-check.
9. Decision và signature tách biệt.
10. Judgment và finality tách biệt.
11. Appeal/review độc lập.
12. Sealed/public projection tách biệt.
13. AI provenance đầy đủ.
14. AI không có đường trực tiếp tới authoritative judicial decision.
15. Offline operation có signed journal.
16. Distributed replay deterministic.
17. Historical legal state replay được.
18. Retention/archival có legal basis.
19. ≥60 semantic/security invariants được test.
20. ≥20,000 automated tests đạt.
21. Cross-jurisdiction configuration không yêu cầu sửa compiler core.
22. Không có GC bắt buộc trong hot path.
23. Không có hidden implicit legal semantic.
24. Tất cả authoritative mutations đều audit được.

---

# 112. Compiler-Level Rule

Một trong những yêu cầu quan trọng nhất của `AXJUSTICE` là:

```text
AXIOM MUST MAKE ILLEGAL STATE TRANSITIONS HARD
TO EXPRESS, NOT MERELY DOCUMENT THEM.
```

Ví dụ:

```axiom
let charge: Charge = ...
let guilt: Finding = charge       // COMPILE ERROR
```

và:

```axiom
let judgment: Judgment = decision // COMPILE ERROR
```

nếu thiếu bước authorized judgment creation.

Tương tự:

```axiom
ai_result.finality = Final
```

phải là compile-time/type-system violation.

Mục tiêu là chuyển phần lớn safety semantics từ:

```text
documentation
```

sang:

```text
type system
+
capability system
+
state machine
+
runtime validation
```

---

# 113. Completion

`BOOTSTRAP-702 / AXJUSTICE` hoàn thành architectural baseline.

Task kế tiếp trong chuỗi:

**BOOTSTRAP-703 — AXCORRECTIONS: Native AI Civilization-Scale Corrections, Custodial Administration, Probation, Rehabilitation & Reentry Runtime 5.0**

Namespace:

```text
AXCORRECTIONS
```

Mục tiêu tiếp theo là thiết kế lớp sau **Judgment/Finality → Custody → Sentence/Order Execution → Probation → Rehabilitation → Reentry**, đồng thời giữ firewall rất rõ giữa **judicial decision**, **correctional administration**, **custody status**, **risk assessment**, **rehabilitation services** và **AI recommendation**.
:::

Đã hoàn tất `BOOTSTRAP-702`; theo chuỗi tự động, bước kế tiếp là **AXCORRECTIONS / BOOTSTRAP-703**.