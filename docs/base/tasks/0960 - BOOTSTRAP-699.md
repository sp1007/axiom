Tiếp tục với **BOOTSTRAP-699**, xây lớp tư pháp/adjudication native của Axiom và giữ ranh giới chặt giữa luật, xét xử, bằng chứng, phán quyết và thi hành.

:::writing{variant="document" id="74136" title="BOOTSTRAP-699 — Native AI Civilization-Scale Government Justice, Courts, Legal Proceedings, Case Law, Dispute Resolution, Administrative Adjudication & Judicial Workflow Runtime 5.0"}

# BOOTSTRAP-699
# Native AI Civilization-Scale Government Justice, Courts, Legal Proceedings, Case Law, Dispute Resolution, Administrative Adjudication & Judicial Workflow Runtime 5.0

**Namespace:** `AXJUSTICE`  
**Version:** 5.0  
**Layer:** Justice / Courts / Adjudication  
**Status:** Architecture Specification

---

# 1. Mục tiêu

`AXJUSTICE` là runtime native của Axiom cho:

- tòa án;
- cơ quan xét xử;
- tố tụng;
- vụ án;
- tranh chấp;
- yêu cầu pháp lý;
- nguyên đơn/bị đơn;
- công tố;
- luật sư;
- thẩm phán;
- hội đồng xét xử;
- bằng chứng;
- hồ sơ;
- phiên điều trần;
- phiên tòa;
- quyết định tố tụng;
- phán quyết;
- bản án;
- kháng cáo;
- tái thẩm;
- thi hành phán quyết;
- hòa giải;
- trọng tài;
- giải quyết tranh chấp hành chính;
- án lệ/case law;
- legal research;
- judicial workflow;
- judicial analytics;
- AI-assisted justice.

Mục tiêu là tạo một execution substrate có thể triển khai từ:

```text
small local court
```

đến:

```text
national judiciary
```

và:

```text
multi-jurisdiction legal systems
```

mà không biến `AXJUSTICE` thành một ứng dụng tòa án cụ thể.

---

# 2. Vị trí trong Axiom

```text
                    AXGOV
                      │
                 PUBLIC AUTHORITY
                      │
                    AXLAW
                      │
             LEGAL RULE / AUTHORITY
                      │
                  AXJUSTICE
                      │
       ┌──────────────┼───────────────┐
       │              │               │
     COURTS       PROCEEDINGS      DISPUTES
       │              │               │
     CASES         EVIDENCE        MEDIATION
       │              │               │
       └──────────────┼───────────────┘
                      │
                 JUDGMENT
                      │
                ENFORCEMENT
```

Các lớp liên quan:

```text
AXLAW
    legal rules / authority

AXJUSTICE
    adjudication / proceedings / judgments

AXPUBLIC
    public administration / contracts / assets

AXFINANCE
    financial truth

AXFISCAL
    public fiscal authority

AXBANKING
    payment / settlement

AXPOPULATION
    identity

AXSECURITY
    authorized security functions
```

---

# 3. Semantic Boundary

Các khái niệm sau **không được đồng nhất**:

```text
Law != Court

Court != Judge

Judge != JudicialPanel

Case != Claim

Claim != Allegation

Allegation != Evidence

Evidence != Fact

Fact != Finding

Finding != Judgment

Judgment != Enforcement

Order != Judgment

Judgment != Precedent

Precedent != Statute

LegalArgument != Evidence

Evidence != LegalArgument

Witness != Evidence

Testimony != Fact

Document != Authenticity

Authenticity != Truth

Charge != Conviction

Conviction != Sentence

Sentence != Enforcement

Appeal != Retrial

Appeal != AutomaticReversal

AdministrativeDecision != JudicialJudgment

Mediation != Adjudication

Settlement != Judgment

Arbitration != CourtJudgment

AIRecommendation != JudicialDecision

LegalResearch != JudicialDecision

LegalResearch != LegalAuthority

Prediction != Judgment

Simulation != Judgment
```

Đây là **semantic firewall** của `AXJUSTICE`.

---

# 4. Nguyên tắc tối cao

```text
AXLAW DEFINES LEGAL AUTHORITY

AXJUSTICE EXECUTES ADJUDICATION

COURT DECIDES ACCORDING TO AUTHORITY

EVIDENCE SUPPORTS FINDINGS

JUDGMENT RECORDS THE DECISION

ENFORCEMENT IMPLEMENTS VALID ORDERS

AI ASSISTS BUT DOES NOT SILENTLY BECOME JUDICIAL AUTHORITY
```

---

# 5. Court

```axiom
struct Court {
    id: CourtId
    jurisdiction: JurisdictionId
    level: CourtLevel
    authority: LegalAuthorityRef
    divisions: EntitySet<DivisionId>
    status: CourtStatus
}
```

---

# 6. Court Levels

```axiom
enum CourtLevel {
    LOCAL
    DISTRICT
    PROVINCIAL
    NATIONAL
    APPEAL
    SUPREME
    CONSTITUTIONAL
    SPECIALIZED
    ADMINISTRATIVE
    COMMERCIAL
    LABOR
    FAMILY
    JUVENILE
    TAX
    INTELLECTUAL_PROPERTY
    INTERNATIONAL
}
```

Không giả định mọi quốc gia đều có cùng hierarchy.

Court topology phải configurable theo jurisdiction.

---

# 7. Jurisdiction

```axiom
struct Jurisdiction {
    id: JurisdictionId
    territory: TerritoryRef
    legal_system: LegalSystemRef
    effective_from: Timestamp
    effective_until: Option<Timestamp>
}
```

Jurisdiction có thể dựa trên:

```text
territory
subject matter
person
amount
legal relationship
administrative authority
appeal level
```

---

# 8. Judge

```axiom
struct Judge {
    id: JudgeId
    court: CourtId
    authority: JudicialAuthorityRef
    appointment: AppointmentRef
    status: JudgeStatus
}
```

Judge không tự động có quyền trên mọi case.

Authority phải được kiểm tra theo:

```text
jurisdiction
court
case type
assignment
recusal
conflict
```

---

# 9. Judicial Panel

```axiom
struct JudicialPanel {
    id: PanelId
    members: EntitySet<JudgeId>
    presiding_judge: Option<JudgeId>
    formation_rule: RuleRef
}
```

Hỗ trợ:

```text
single judge
panel
jury
mixed tribunal
special chamber
```

---

# 10. Case

```axiom
struct JusticeCase {
    id: CaseId
    court: CourtId
    type: CaseType
    jurisdiction: JurisdictionId
    parties: EntitySet<PartyId>
    claims: EntitySet<ClaimId>
    status: CaseStatus
    opened_at: Timestamp
}
```

Case là container tố tụng.

Không phải judgment.

---

# 11. Case Types

```axiom
enum CaseType {
    CIVIL
    CRIMINAL
    ADMINISTRATIVE
    COMMERCIAL
    LABOR
    FAMILY
    JUVENILE
    TAX
    CONSTITUTIONAL
    ELECTORAL
    INTELLECTUAL_PROPERTY
    INSOLVENCY
    ENVIRONMENTAL
    HUMAN_RIGHTS
    INTERNATIONAL
    ARBITRATION_REVIEW
    OTHER
}
```

---

# 12. Parties

```axiom
enum PartyRole {
    CLAIMANT
    PLAINTIFF
    DEFENDANT
    RESPONDENT
    PROSECUTOR
    ACCUSED
    VICTIM
    INTERVENOR
    PETITIONER
    APPELLANT
    APPELLEE
    GOVERNMENT
    THIRD_PARTY
}
```

Một entity có thể có nhiều role theo case nhưng role phải được ghi nhận theo procedural context.

---

# 13. Legal Representation

```axiom
struct LegalRepresentative {
    id: RepresentativeId
    represented_party: PartyId
    representative: PersonId
    authority: RepresentationAuthority
    valid_from: Timestamp
    valid_until: Option<Timestamp>
}
```

Authority phải được kiểm tra trước khi representative thực hiện hành động tố tụng.

---

# 14. Claim

```axiom
struct LegalClaim {
    id: ClaimId
    case: CaseId
    claimant: PartyId
    respondent: PartyId
    legal_basis: EntitySet<LegalReference>
    requested_relief: Relief
    status: ClaimStatus
}
```

---

# 15. Claim vs Allegation

```text
Claim
    = legal request/assertion before adjudication

Allegation
    = asserted factual proposition
```

Không được tự động coi allegation là fact.

---

# 16. Pleading

```axiom
struct Pleading {
    id: PleadingId
    case: CaseId
    author: PartyId
    type: PleadingType
    content: DocumentRef
    submitted_at: Timestamp
}
```

Các loại:

```text
complaint
answer
motion
petition
appeal
reply
rebuttal
submission
```

---

# 17. Evidence

```axiom
struct Evidence {
    id: EvidenceId
    case: CaseId
    type: EvidenceType
    source: EvidenceSource
    authenticity: AuthenticityStatus
    admissibility: AdmissibilityStatus
    provenance: ProvenanceRef
}
```

---

# 18. Evidence Types

```axiom
enum EvidenceType {
    DOCUMENT
    DIGITAL_RECORD
    PHYSICAL_OBJECT
    TESTIMONY
    EXPERT_REPORT
    AUDIO
    VIDEO
    IMAGE
    FORENSIC_RESULT
    FINANCIAL_RECORD
    GOVERNMENT_RECORD
    ELECTRONIC_COMMUNICATION
    OTHER
}
```

---

# 19. Evidence State Machine

```text
SUBMITTED
   ↓
IDENTIFIED
   ↓
AUTHENTICATED
   ↓
ADMISSIBILITY_REVIEW
   ↓
ADMITTED / EXCLUDED
   ↓
CONSIDERED
   ↓
FINDING_REFERENCE
```

Không được suy ra:

```text
ADMITTED == TRUE
```

từ:

```text
AUTHENTICATED == TRUE
```

---

# 20. Evidence Provenance

Mỗi evidence phải hỗ trợ:

```text
source
creator
creation_time
capture_method
custodian
transfer_chain
hash
signature
modification_history
```

Đối với digital evidence:

```axiom
struct DigitalEvidenceProvenance {
    content_hash: Hash
    acquisition_method: AcquisitionMethod
    acquired_at: Timestamp
    acquired_by: ActorRef
    chain_of_custody: EntitySet<CustodyEventId>
}
```

---

# 21. Chain of Custody

```axiom
struct CustodyEvent {
    evidence: EvidenceId
    from_actor: ActorRef
    to_actor: ActorRef
    timestamp: Timestamp
    action: CustodyAction
    signature: Signature
}
```

Không được sửa lịch sử custody.

---

# 22. Witness

```axiom
struct Witness {
    id: WitnessId
    case: CaseId
    party_relationship: Option<PartyId>
    identity: IdentityRef
}
```

Testimony phải là một evidence object riêng.

```text
Witness != Testimony
```

---

# 23. Expert

```axiom
struct Expert {
    id: ExpertId
    field: ExpertiseField
    qualifications: QualificationSet
}
```

Expert report:

```axiom
struct ExpertReport {
    id: ExpertReportId
    expert: ExpertId
    methodology: Methodology
    findings: FindingSet
    limitations: LimitationSet
}
```

---

# 24. Fact

Axiom phải phân biệt:

```text
asserted fact
established fact
disputed fact
undisputed fact
```

```axiom
enum FactStatus {
    ASSERTED
    DISPUTED
    UNDISPUTED
    ESTABLISHED
    UNESTABLISHED
    UNKNOWN
}
```

---

# 25. Finding

```axiom
struct JudicialFinding {
    id: FindingId
    case: CaseId
    proposition: LegalOrFactualProposition
    basis: EvidenceSet
    reasoning: ReasoningReference
    status: FindingStatus
}
```

Finding phải reference supporting evidence hoặc legal basis phù hợp.

---

# 26. Hearing

```axiom
struct Hearing {
    id: HearingId
    case: CaseId
    court: CourtId
    type: HearingType
    scheduled_at: Timestamp
    participants: EntitySet<ActorRef>
    status: HearingStatus
}
```

---

# 27. Hearing Types

```axiom
enum HearingType {
    PRETRIAL
    PROCEDURAL
    EVIDENTIARY
    MERITS
    SENTENCING
    APPEAL
    REVIEW
    MEDIATION
    ADMINISTRATIVE
    EMERGENCY
}
```

---

# 28. Judicial Workflow

```axiom
workflow JusticeProceeding {
    filing
    registration
    jurisdiction_check
    service
    response
    preliminary_review
    evidence
    hearing
    deliberation
    decision
    judgment
    appeal_window
    enforcement
    closure
}
```

Workflow phải hỗ trợ:

```text
parallel
serial
conditional
deadline
extension
recusal
transfer
remand
appeal
stay
```

---

# 29. Procedural Order

```axiom
struct ProceduralOrder {
    id: OrderId
    case: CaseId
    issued_by: JudicialAuthorityRef
    type: OrderType
    effective_from: Timestamp
    effective_until: Option<Timestamp>
    content: DocumentRef
}
```

Order không mặc định là final judgment.

---

# 30. Judgment

```axiom
struct Judgment {
    id: JudgmentId
    case: CaseId
    court: CourtId
    panel: PanelId
    findings: EntitySet<FindingId>
    legal_basis: EntitySet<LegalReference>
    disposition: Disposition
    issued_at: Timestamp
    status: JudgmentStatus
}
```

---

# 31. Judgment Status

```axiom
enum JudgmentStatus {
    DRAFT
    ISSUED
    APPEALABLE
    FINAL
    VACATED
    REVERSED
    REMANDED
    PARTIALLY_REVERSED
}
```

---

# 32. Judgment != Enforcement

Một judgment có thể:

```text
issued
```

nhưng chưa:

```text
enforced
```

Do đó:

```text
Judgment
    ↓
EnforcementOrder
    ↓
EnforcementAction
    ↓
Outcome
```

---

# 33. Enforcement

```axiom
struct EnforcementCase {
    id: EnforcementCaseId
    judgment: JudgmentId
    authority: EnforcementAuthorityRef
    obligations: EntitySet<ObligationId>
    status: EnforcementStatus
}
```

---

# 34. Enforcement Actions

```axiom
enum EnforcementAction {
    NOTICE
    PAYMENT_ORDER
    ASSET_TRANSFER
    PROPERTY_EXECUTION
    RESTITUTION
    COMPLIANCE_ORDER
    LICENSE_ACTION
    OTHER
}
```

Mỗi jurisdiction có thể giới hạn các action hợp lệ.

---

# 35. Criminal Justice

Criminal cases cần thêm:

```axiom
struct CriminalCharge {
    id: ChargeId
    case: CaseId
    accused: PartyId
    offense: LegalOffenseRef
    factual_basis: AllegationSet
}
```

Phải phân biệt:

```text
charge
indictment
conviction
sentence
```

---

# 36. Conviction

```axiom
struct Conviction {
    accused: PartyId
    offense: LegalOffenseRef
    judgment: JudgmentId
    status: ConvictionStatus
}
```

Không được coi charge là conviction.

---

# 37. Sentence

```axiom
struct Sentence {
    id: SentenceId
    conviction: ConvictionId
    type: SentenceType
    duration: Option<Duration>
    conditions: ConditionSet
}
```

---

# 38. Civil Remedies

```axiom
enum ReliefType {
    DAMAGES
    RESTITUTION
    INJUNCTION
    DECLARATION
    SPECIFIC_PERFORMANCE
    PROPERTY_RETURN
    CONTRACT_REMEDY
    OTHER
}
```

---

# 39. Administrative Adjudication

`AXJUSTICE` phải hỗ trợ tranh chấp với cơ quan hành chính:

```text
GovernmentDecision
       ↓
AdministrativeChallenge
       ↓
Review
       ↓
AdministrativeJudgment
```

Phải phân biệt:

```text
administrative_action
administrative_review
judicial_review
```

---

# 40. Mediation

```axiom
struct MediationCase {
    id: MediationCaseId
    dispute: CaseId
    mediator: ActorRef
    participants: EntitySet<PartyId>
    status: MediationStatus
}
```

Mediation outcome:

```text
agreement
partial agreement
no agreement
```

Không tự động trở thành judgment.

---

# 41. Settlement

```axiom
struct Settlement {
    id: SettlementId
    case: CaseId
    parties: EntitySet<PartyId>
    terms: SettlementTerms
    approved_by: Option<JudicialAuthorityRef>
}
```

Nếu jurisdiction cho phép settlement trở thành enforceable order, runtime phải biểu diễn rõ transformation:

```text
Settlement
   ↓
Approval
   ↓
EnforceableOrder
```

---

# 42. Arbitration

```axiom
struct ArbitrationProceeding {
    id: ArbitrationId
    parties: EntitySet<PartyId>
    tribunal: ArbitrationTribunalRef
    claims: EntitySet<ClaimId>
    award: Option<ArbitrationAwardId>
}
```

Arbitration không mặc định là court proceeding.

---

# 43. Appeal

```axiom
struct Appeal {
    id: AppealId
    source_judgment: JudgmentId
    appellant: PartyId
    grounds: AppealGroundSet
    target_court: CourtId
    status: AppealStatus
}
```

Appeal phải reference judgment cụ thể.

---

# 44. Appeal Outcomes

```axiom
enum AppealOutcome {
    AFFIRMED
    REVERSED
    MODIFIED
    VACATED
    REMANDED
    DISMISSED
}
```

Đây là legal state, không chỉ text.

---

# 45. Case Law

Axiom phải hỗ trợ case law:

```axiom
struct Precedent {
    id: PrecedentId
    source_judgment: JudgmentId
    jurisdiction: JurisdictionId
    authority_level: PrecedentAuthority
    legal_propositions: PropositionSet
    status: PrecedentStatus
}
```

Không mọi judgment đều tự động là binding precedent.

---

# 46. Precedent Authority

```axiom
enum PrecedentAuthority {
    BINDING
    PERSUASIVE
    LIMITED
    NON_PRECEDENTIAL
}
```

Authority được xác định theo jurisdiction/legal system.

---

# 47. Legal Proposition

```axiom
struct LegalProposition {
    id: PropositionId
    text: LegalText
    legal_basis: EntitySet<LegalReference>
    source: LegalSourceRef
    scope: PropositionScope
}
```

AI legal research có thể index propositions nhưng không tự quyết định authority.

---

# 48. Legal Research Engine

Native services:

```text
find_statute()
find_precedent()
find_related_cases()
trace_proposition()
compare_judgments()
find_conflicting_authorities()
```

Kết quả:

```axiom
struct LegalResearchResult {
    sources: SourceSet
    propositions: PropositionSet
    jurisdiction: JurisdictionId
    temporal_scope: TimeRange
}
```

Không coi search result là legal decision.

---

# 49. AI Legal Research

AI có thể:

```text
summarize case
extract claims
extract evidence references
find related precedent
identify conflicting authorities
construct chronology
compare legal provisions
simulate arguments
```

AI không được tự động:

```text
issue judgment
alter case status
declare guilt
create legal authority
invalidate evidence
```

nếu không có explicit authorized workflow.

---

# 50. Judicial AI Provenance

```axiom
struct JudicialAIArtifact {
    model: ModelRef
    model_version: Version
    prompt_hash: Hash
    input_documents: EntitySet<DocumentId>
    output_hash: Hash
    generated_at: Timestamp
    human_reviewer: Option<ActorRef>
}
```

Nếu AI output materially ảnh hưởng đến workflow, artifact phải được audit.

---

# 51. AI Hallucination Firewall

AI-generated content phải phân biệt:

```text
VERIFIED_SOURCE
INFERRED
GENERATED
UNVERIFIED
```

Không cho generated proposition tự động trở thành:

```text
legal authority
fact
evidence
precedent
```

---

# 52. Judicial Decision Record

```axiom
struct JudicialDecisionRecord {
    id: DecisionId
    case: CaseId
    authority: JudicialAuthorityRef
    legal_basis: LegalReferenceSet
    factual_findings: FindingSet
    reasoning: ReasoningRecord
    disposition: Disposition
    provenance: DecisionProvenance
}
```

---

# 53. Decision Provenance

Phải lưu:

```text
judge/panel
jurisdiction
authority
applicable law versions
evidence set
findings
procedural history
AI assistance
draft versions
final signature
issuance timestamp
```

---

# 54. Digital Signature

Judgment phải hỗ trợ:

```axiom
sign(judgment, judicial_key)
```

Signature phải bind:

```text
judgment hash
issuer
authority
timestamp
certificate
```

Không sửa judgment sau signature.

---

# 55. Immutable Judicial Record

Sau khi issued:

```text
Judgment
```

không được overwrite.

Thay vào đó:

```text
Judgment
 ↓
Correction
Amendment
Appeal
Reversal
Vacatur
Remand
```

được tạo thành record mới.

---

# 56. Procedural Deadlines

Native temporal primitive:

```axiom
deadline(
    event = service_completed,
    duration = 30.days
)
```

Phải hỗ trợ:

```text
calendar days
business days
court holidays
jurisdiction-specific calendars
suspension
extension
tolling
```

---

# 57. Service of Process

```axiom
struct LegalService {
    id: ServiceId
    case: CaseId
    recipient: PartyId
    document: DocumentRef
    method: ServiceMethod
    served_at: Timestamp
    status: ServiceStatus
}
```

Service event có thể kích hoạt deadline.

---

# 58. Court Calendar

```axiom
struct CourtCalendar {
    jurisdiction: JurisdictionId
    holidays: DateSet
    working_days: CalendarRule
    emergency_days: DateSet
}
```

Deadline engine phải sử dụng calendar version phù hợp.

---

# 59. Conflict of Interest / Recusal

```axiom
struct Recusal {
    judge: JudgeId
    case: CaseId
    reason: RecusalReason
    status: RecusalStatus
}
```

Nếu judge bị recused:

```text
judge
```

không được tiếp tục thực hiện restricted action trên case.

---

# 60. Random / Rule-Based Assignment

Court assignment phải hỗ trợ:

```text
rotation
random assignment
weighted assignment
specialization
workload balancing
conflict exclusion
geographic rules
```

Assignment phải audit được.

---

# 61. Case Transfer

```axiom
struct CaseTransfer {
    case: CaseId
    from_court: CourtId
    to_court: CourtId
    authority: AuthorityRef
    reason: TransferReason
}
```

Transfer không xóa procedural history.

---

# 62. Case Consolidation

Nhiều case có thể được:

```text
consolidated
```

nhưng phải giữ:

```text
original_case_id
original_claims
original_parties
```

để audit.

---

# 63. Case Separation

Một case có thể split thành:

```text
Case A
Case B
```

nhưng genealogy phải được giữ:

```axiom
parent_case
child_cases
```

---

# 64. Legal Document Model

Native document metadata:

```text
document_id
case_id
author
created_at
file_hash
document_type
language
version
signature
confidentiality
retention
```

Content có thể được lưu external nhưng metadata phải native.

---

# 65. Multilingual Justice

Axiom core phải hỗ trợ:

```text
UTF-8
Unicode normalization
language metadata
translation provenance
original-language preservation
```

Không được overwrite original legal text bằng translation.

```text
Original
   +
Translation
   +
Translator
   +
Version
```

---

# 66. Confidentiality

Các classification:

```text
PUBLIC
RESTRICTED
CONFIDENTIAL
SEALED
HIGHLY_RESTRICTED
```

Access phải được field/document/case scoped.

---

# 67. Evidence Access

Không phải mọi party đều được đọc mọi evidence ở mọi thời điểm.

Native policy:

```axiom
can_access(
    actor,
    evidence,
    purpose,
    procedural_stage
)
```

---

# 68. Courtroom Event Stream

Các event:

```text
CaseFiled
CaseAccepted
JurisdictionDetermined
PartyServed
PleadingFiled
EvidenceSubmitted
EvidenceAdmitted
EvidenceExcluded
HearingScheduled
HearingStarted
HearingCompleted
MotionFiled
OrderIssued
JudgeRecused
CaseTransferred
JudgmentIssued
AppealFiled
JudgmentReversed
JudgmentFinal
EnforcementStarted
EnforcementCompleted
CaseClosed
```

Event immutable.

---

# 69. Event-Sourced Case History

Có thể reconstruct:

```text
case state at any historical time
```

bằng:

```text
event replay
```

Điều này cực kỳ quan trọng cho:

- appeal;
- judicial audit;
- legal research;
- procedural verification;
- historical reconstruction.

---

# 70. Four-Time Model

Justice event phải phân biệt:

```text
effective_at
decided_at
recorded_at
served_at
```

Ví dụ:

```text
Judgment decided:
2026-09-01

Recorded:
2026-09-02

Served:
2026-09-03

Effective:
2026-09-18
```

Không được đồng nhất các timestamp.

---

# 71. Enforcement Integration

```text
AXJUSTICE
    ↓
EnforceableOrder
    ↓
AXPUBLIC / AXFINANCE / AXBANKING / AXGOV
```

Ví dụ judgment yêu cầu payment:

```text
Judgment
 ↓
EnforcementOrder
 ↓
PaymentInstruction
 ↓
AXBANKING
```

Nhưng `AXJUSTICE` không giả lập settlement.

---

# 72. Property / Asset Enforcement

Nếu pháp luật cho phép:

```text
Judgment
 ↓
Enforcement
 ↓
AssetIdentification
 ↓
LegalRestriction
 ↓
Disposition
```

Asset state phải giao tiếp với:

```text
AXPUBLIC
AXFINANCE
AXCOMMERCE
```

thông qua typed interfaces.

---

# 73. Criminal Evidence Boundary

Criminal evidence có thể bao gồm:

```text
forensics
digital evidence
financial records
witness testimony
expert analysis
physical evidence
```

nhưng runtime không được tự động suy ra guilt từ risk score hoặc statistical correlation.

---

# 74. Standard of Proof

Không hard-code một standard duy nhất.

```axiom
enum ProofStandard {
    PREPONDERANCE
    CLEAR_AND_CONVINCING
    BEYOND_REASONABLE_DOUBT
    BALANCE_OF_PROBABILITIES
    STATUTORY_STANDARD
    CUSTOM
}
```

Case/jurisdiction xác định standard.

---

# 75. Burden of Proof

```axiom
struct BurdenOfProof {
    party: PartyId
    proposition: PropositionId
    standard: ProofStandard
}
```

Có thể thay đổi theo claim hoặc procedural stage.

---

# 76. Reasoning Graph

Judgment reasoning có thể được biểu diễn:

```text
LegalRule
   ↓
LegalInterpretation
   ↓
EstablishedFact
   ↓
RuleApplication
   ↓
Finding
   ↓
Disposition
```

Graph giúp:

- explainability;
- legal research;
- appeal;
- audit;
- AI assistance.

---

# 77. Judicial Knowledge Graph

Nodes:

```text
Statute
Regulation
Case
Judgment
Claim
Evidence
Finding
Proposition
Judge
Court
Jurisdiction
```

Edges:

```text
cites
interprets
distinguishes
overrules
supports
contradicts
applies
appeals
reverses
remands
```

---

# 78. Case-Law Versioning

Precedent graph phải hỗ trợ:

```text
new interpretation
distinguishing
overruling
limitation
jurisdiction change
statutory supersession
```

Không được xóa precedent cũ.

---

# 79. Search

Native indexes:

```text
case_id
party
judge
court
statute
legal_reference
claim
evidence
date
jurisdiction
proposition
citation
```

Hỗ trợ:

```text
exact search
full text
semantic search
graph traversal
temporal search
```

---

# 80. Semantic Search Boundary

Semantic similarity chỉ là:

```text
retrieval signal
```

không phải:

```text
legal authority ranking
```

Authority phải dựa trên metadata/legal rules.

---

# 81. Simulation

Có thể mô phỏng:

```text
appeal outcome scenarios
procedural workload
court capacity
case backlog
deadline changes
assignment strategies
legal rule changes
```

Nhưng:

```text
Simulation != Real Judgment
```

và:

```text
Simulation != Legal Outcome
```

---

# 82. Court Digital Twin

```text
Population
    ↓
Cases
    ↓
Courts
    ↓
Judges
    ↓
Hearings
    ↓
Workload
    ↓
Backlog
    ↓
Disposition
```

Cho phép mô phỏng:

```text
new court
new judge capacity
new procedure
new filing volume
new deadline
```

mà không tác động production.

---

# 83. Performance Targets

Mục tiêu architecture:

```text
≥ 5M lightweight procedural events/sec
per large partitioned deployment target
```

và:

```text
billions of historical procedural events
billions of documents/metadata records
billions of legal graph edges
millions of concurrent cases
```

Search và graph analytics phải scale độc lập với transactional workflow.

---

# 84. Memory Model

Không yêu cầu GC.

Hot path ưu tiên:

```text
arena
slab
pool
immutable snapshots
append-only event storage
packed IDs
columnar indexes
```

Large document content có thể nằm ngoài hot transactional memory.

---

# 85. Concurrency

Case state phải hỗ trợ optimistic concurrency:

```axiom
compare_version(case.version)
commit()
```

Nếu conflict:

```text
JUSTICE_CASE_VERSION_CONFLICT
```

Không silently overwrite.

---

# 86. Idempotency

Các hành động như:

```text
file_case
submit_evidence
serve_document
issue_order
schedule_hearing
file_appeal
start_enforcement
```

phải có idempotency semantics.

Retry không được tạo duplicate procedural action.

---

# 87. Runtime Profiles

```text
AXJUSTICE_NONE
AXJUSTICE_CORE
AXJUSTICE_CASE
AXJUSTICE_EVIDENCE
AXJUSTICE_COURT
AXJUSTICE_HEARING
AXJUSTICE_JUDGMENT
AXJUSTICE_APPEAL
AXJUSTICE_ENFORCEMENT
AXJUSTICE_MEDIATION
AXJUSTICE_ARBITRATION
AXJUSTICE_CASELAW
AXJUSTICE_RESEARCH
AXJUSTICE_AI
AXJUSTICE_ANALYTICS
AXJUSTICE_SIMULATION
AXJUSTICE_DIGITAL_TWIN
AXJUSTICE_DISTRIBUTED
AXJUSTICE_GPU
AXJUSTICE_WASM
AXJUSTICE_MOBILE
AXJUSTICE_REALTIME
AXJUSTICE_FULL
```

---

# 88. Capability Model

```text
justice.read_case
justice.create_case
justice.modify_case
justice.assign_case
justice.submit_evidence
justice.admit_evidence
justice.exclude_evidence
justice.schedule_hearing
justice.issue_order
justice.issue_judgment
justice.appeal
justice.enforce
justice.audit
justice.manage_precedent
justice.manage_rules
justice.run_simulation
justice.ai_assist
```

Đặc biệt:

```text
justice.issue_judgment
```

phải là capability riêng biệt.

---

# 89. Separation of Duties

Không mặc định cho một identity đồng thời:

```text
case_assignment
judicial_decision
enforcement
audit
```

Recusal/conflict policies phải được enforce bởi runtime.

---

# 90. Security Invariants

Tối thiểu:

1. Case phải thuộc một jurisdiction hợp lệ.
2. Judicial action phải có authority.
3. Judge phải có jurisdiction phù hợp.
4. Recused judge không được thực hiện restricted action.
5. Evidence provenance không được overwrite.
6. Admitted evidence không đồng nghĩa factual truth.
7. Allegation không đồng nghĩa established fact.
8. Charge không đồng nghĩa conviction.
9. Conviction không đồng nghĩa sentence.
10. Judgment không đồng nghĩa enforcement.
11. Appeal không xóa judgment gốc.
12. Reversal tạo legal state mới.
13. Historical judgment không bị overwrite.
14. AI recommendation không tự thành judgment.
15. Semantic search không tự tạo legal authority.
16. Generated AI text không tự thành evidence.
17. Legal research không tự thành judicial decision.
18. Simulation không thay đổi production case.
19. Enforcement phải reference enforceable authority.
20. Payment enforcement phải giao tiếp qua typed financial interface.
21. Case assignment phải audit được.
22. Procedural deadlines phải versioned.
23. Service event phải provenance.
24. Legal document hash phải bảo toàn integrity.
25. Digital signature phải bind document version.
26. Evidence chain-of-custody phải immutable.
27. Confidential evidence phải access-controlled.
28. Sealed record không được public qua normal search.
29. Appeal phải reference source judgment.
30. Remand phải reference appellate decision.
31. Precedent authority phải jurisdiction-aware.
32. Overruled precedent không bị xóa.
33. Legal source version phải immutable.
34. Decision reasoning phải traceable.
35. Human override phải audit.
36. Emergency authority phải có expiration.
37. Case merge phải giữ genealogy.
38. Case split phải giữ genealogy.
39. Transfer phải giữ procedural history.
40. Retry procedural action phải idempotent.
41. Concurrent modification phải detect.
42. Court calendar phải versioned.
43. Deadline calculation phải reproducible.
44. AI model version phải lưu khi materially used.
45. Sensitive data access phải audit.
46. Translation không được overwrite original.
47. Machine translation phải provenance.
48. External evidence phải source-authenticated.
49. Enforcement result không được giả mạo từ judgment state.
50. Judicial record phải có cryptographic integrity.

---

# 91. Testing

Target:

```text
≥ 20,000 automated tests
```

Bao gồm:

```text
case lifecycle
jurisdiction
assignment
recusal
evidence
chain of custody
hearing
deadline
judgment
appeal
precedent
enforcement
mediation
arbitration
privacy
security
concurrency
replay
AI boundary
simulation isolation
```

---

# 92. Property-Based Testing

Các property bắt buộc:

```text
Judgment cannot exist without Case.

Enforcement cannot exist without enforceable authority.

Appeal must reference Judgment.

Evidence custody cannot mutate history.

Retry(Filing) cannot create duplicate case.

Retry(Service) cannot create duplicate service event.

Replay(case_history) == historical_state.

Simulation(state) cannot mutate production_state.

AIRecommendation != Judgment.

Charge != Conviction.
```

---

# 93. Disaster Recovery

Phải bảo toàn:

```text
case history
evidence metadata
signatures
judgments
appeals
enforcement state
audit trail
precedent graph
```

Hỗ trợ:

```text
point-in-time recovery
cross-region replication
append-only backup
cryptographic verification
```

---

# 94. Offline Court Operations

Hỗ trợ:

```text
offline evidence capture
offline document signing
offline hearing metadata
deferred synchronization
conflict detection
```

Nhưng authoritative judgment issuance phải obey jurisdiction-specific trust rules.

---

# 95. WASM / Edge

Có thể compile:

```text
document verifier
signature verifier
deadline calculator
legal-rule evaluator
evidence hash verifier
```

xuống WASM/edge.

---

# 96. Native Justice DSL

Ví dụ:

```axiom
court CommercialCourt {

    jurisdiction = HanoiCommercial

    procedure CivilCommercial {

        filing
        service
        response
        evidence
        hearing
        judgment
        appeal
    }
}
```

Compiler hạ DSL xuống:

```text
types
rules
workflow
events
capabilities
schemas
indexes
```

Không tạo runtime riêng.

---

# 97. Procedural Rule DSL

```axiom
rule AppealDeadline {
    when judgment.is_appealable
    then
        deadline = service_date + 15.days
}
```

Rule phải có:

```text
legal_basis
version
effective_from
jurisdiction
```

---

# 98. Judicial AI DSL

```axiom
ai_assistant CaseResearch {

    can {
        summarize
        retrieve
        compare
        cite
        classify
    }

    cannot {
        issue_judgment
        modify_judgment
        declare_guilt
        alter_evidence
    }
}
```

Compiler phải biến `cannot` thành capability constraints thật, không phải comment.

---

# 99. Explainability

Một judgment record phải có thể tạo:

```text
Procedural history
Applicable law
Evidence considered
Findings
Reasoning references
Disposition
Appeal status
Enforcement status
```

AI explanation chỉ được xem là auxiliary representation; authoritative record vẫn là structured judicial record.

---

# 100. Final Semantic Contract

```text
AXLAW
    = legal authority

AXJUSTICE
    = adjudication and judicial execution

AXGOV
    = government authority

AXPUBLIC
    = public administration / public assets / procurement

AXFINANCE
    = financial truth

AXBANKING
    = payment infrastructure
```

Luồng chuẩn:

```text
LEGAL RULE
    ↓
CLAIM / CHARGE
    ↓
CASE
    ↓
PROCEEDING
    ↓
EVIDENCE
    ↓
FINDINGS
    ↓
JUDGMENT
    ↓
APPEAL
    ↓
FINALITY
    ↓
ENFORCEMENT
    ↓
OUTCOME
```

---

# 101. Civilization-Scale Justice Loop

```text
SOCIETY
   ↓
LEGAL RULES
   ↓
DISPUTES / OFFENSES / CLAIMS
   ↓
COURTS
   ↓
ADJUDICATION
   ↓
JUDGMENTS
   ↓
ENFORCEMENT
   ↓
LEGAL ORDER
   ↓
SOCIAL / ECONOMIC ACTIVITY
   ↓
NEW DISPUTES
```

`AXJUSTICE` cung cấp infrastructure cho loop này nhưng không tự định nghĩa chính sách pháp luật.

---

# 102. Acceptance Criteria

`BOOTSTRAP-699` hoàn thành khi:

- Có Court model.
- Có Jurisdiction model.
- Có Judge/Panel model.
- Có Case model.
- Có Party model.
- Có Claim model.
- Có Pleading model.
- Có Evidence model.
- Có provenance và chain-of-custody.
- Có Fact/Finding model.
- Có Hearing workflow.
- Có procedural order.
- Có Judgment model.
- Có appeal.
- Có enforcement.
- Có criminal charge/conviction/sentence separation.
- Có civil remedies.
- Có administrative adjudication.
- Có mediation.
- Có arbitration boundary.
- Có precedent/case-law model.
- Có legal research engine interface.
- Có AI-assistance boundary.
- Có temporal/deadline engine.
- Có recusal/conflict model.
- Có cryptographic integrity.
- Có immutable judicial history.
- Có deterministic replay.
- Có distributed execution.
- Có simulation/digital twin.
- Có privacy/security model.
- Có ≥50 security/semantic invariants.
- Có target ≥20,000 automated tests.
- Không yêu cầu GC trong hot path.
- Không phụ thuộc third-party runtime cho core semantics.

---

# 103. Architectural Conclusion

`AXJUSTICE` trở thành lớp:

```text
LEGAL AUTHORITY
       ↓
ADJUDICATION
       ↓
JUDICIAL DECISION
       ↓
ENFORCEMENT
```

trong Axiom.

Nguyên tắc cuối:

```text
LAW DEFINES AUTHORITY
COURTS APPLY AUTHORITY
EVIDENCE SUPPORTS FINDINGS
FINDINGS SUPPORT JUDGMENTS
JUDGMENTS CREATE LEGAL EFFECT
ENFORCEMENT IMPLEMENTS VALID EFFECT
AI ASSISTS THE PROCESS
AUDIT PRESERVES THE RECORD
```

**BOOTSTRAP-699 — COMPLETE.**

---

# 104. Next Architecture Task

**BOOTSTRAP-700 — Native AI Civilization-Scale Government Public Safety, Emergency Management, Disaster Response, Civil Protection, Critical Incident Command & Resilience Runtime 5.0**

**Namespace:** `AXSAFETY`

Trọng tâm:

```text
AXGOV
  ↓
AXLAW
  ↓
AXSAFETY
  ├── Emergency Management
  ├── Disaster Response
  ├── Civil Protection
  ├── Incident Command
  ├── Evacuation
  ├── Rescue Coordination
  ├── Emergency Logistics
  ├── Critical Infrastructure Resilience
  ├── Crisis Communications
  ├── Resource Mobilization
  └── Recovery
```

Các semantic firewall tiếp theo sẽ gồm:

```text
Emergency != Disaster

Incident != Crime

Risk != Event

Warning != Order

Evacuation Recommendation != Evacuation Order

Prediction != Incident

Alert != Confirmation

Resource Availability != Resource Deployment

Deployment != Arrival

Arrival != Mission Completion

Damage Estimate != Verified Damage

AI Recommendation != Emergency Command

Simulation != Real Incident
```

:::

**BOOTSTRAP-699 hoàn tất. Chuỗi kiến trúc chuyển thẳng sang BOOTSTRAP-700 — `AXSAFETY`.**