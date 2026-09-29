Tiếp tục với **BOOTSTRAP-675**. Đây là layer pháp luật và tư pháp cấp nền văn minh, nhưng phải giữ ranh giới rất rõ với `639 Policy/Authority`, `668 Federation Governance`, `603 Security`, và `665 Human Oversight`.

:::writing{variant="document" id="74136" title="BOOTSTRAP-675 — Native AI Civilization-Scale Law, Justice, Rights, Legal Knowledge, Courts, Regulation & Compliance Runtime 5.0"}

# BOOTSTRAP-675
## Native AI Civilization-Scale Law, Justice, Rights, Legal Knowledge, Courts, Regulation & Compliance Runtime 5.0

**Status:** ARCHITECTURE COMPLETE  
**Layer:** Civilization-Scale Legal & Justice Systems  
**Depends on:** BOOTSTRAP-603 → BOOTSTRAP-674  
**Target:** ≥ 5,000 automated tests, ≥ 400 architectural invariants  
**Execution modes:** local / server / distributed / GPU / edge / mobile / WASM / offline  
**Activation:** optional, capability-gated, jurisdiction-gated, authority-gated, privacy-gated, human-oversight-gated

---

# 1. Mục tiêu

BOOTSTRAP-675 cung cấp cho Axiom một **native computational substrate cho pháp luật, quyền, nghĩa vụ, quy định, hợp đồng pháp lý, tuân thủ, xét xử, bằng chứng, thủ tục, tranh chấp và hệ thống tư pháp**.

Nó cho phép xây dựng:

```text
Legal Information System
Legal Knowledge Graph
Contract Analysis System
Compliance Platform
Regulatory Engine
Court Case Management System
Evidence Management System
Legal Research Platform
Legal Document System
Dispute Resolution Platform
Arbitration Platform
Judicial Workflow Platform
Regulatory Reporting System
Rights/Obligations Engine
Legal Simulation
Justice System Simulation
```

nhưng **không biến Axiom thành một cơ quan nhà nước mặc định**.

---

# 2. Vị trí trong kiến trúc

```text
603  Capability / Security
        ↓
639  Policy / Authority
        ↓
640  Data Governance / Privacy
        ↓
645  Knowledge
        ↓
653  Causal / Probabilistic Reasoning
        ↓
663  Evaluation
        ↓
664  Safety
        ↓
665  Human Oversight
        ↓
667  Organizations / Institutions
        ↓
668  Federation / Inter-Organization Governance
        ↓
674  Health / Medicine
        ↓
675  Law / Justice / Rights / Compliance
```

---

# 3. Critical Separation

Đây là nguyên tắc quan trọng nhất của BOOTSTRAP-675.

| Layer | Trách nhiệm |
|---|---|
| 639 | policy, authority, permissions, governance rules |
| 665 | human approval/control |
| 667 | organizations/institutions |
| 668 | inter-organization governance, treaties, federation |
| 675 | legal semantics, rights, duties, cases, courts, evidence, compliance |
| 603 | security/capabilities |
| 640 | privacy/data governance |
| 645 | general knowledge |
| 653 | causal/probabilistic reasoning |
| 663 | evaluation |
| 664 | safety |

`675` có thể **mô hình hóa luật và áp dụng một bộ luật được khai báo**, nhưng không tự tạo ra quyền lực pháp lý.

---

# 4. Legal System Model

Core:

```text
LegalSystem
Jurisdiction
LegalDomain
LegalAuthority
LegalInstrument
LegalRule
LegalPrinciple
LegalNorm
LegalSource
LegalVersion
```

Một `LegalSystem` có thể đại diện cho:

```text
national
regional
local
organizational
contractual
institutional
international
federated
private arbitration
simulation
```

---

# 5. Jurisdiction

```text
Jurisdiction
JurisdictionId
JurisdictionBoundary
JurisdictionHierarchy
JurisdictionScope
JurisdictionRule
```

Jurisdiction có:

```text
territorial_scope
temporal_scope
subject_scope
personal_scope
matter_scope
authority_source
```

Invariant:

```text
Jurisdiction != automatic sovereignty
```

---

# 6. Legal Source

```text
Constitution
Statute
Law
Regulation
Directive
Decree
Order
JudicialDecision
AdministrativeDecision
Treaty
Convention
Contract
PolicyInstrument
CustomaryRule
InstitutionalRule
```

Mỗi source:

```text
source_id
issuer
jurisdiction
effective_from
effective_until
version
status
provenance
```

---

# 7. Legal Instrument Lifecycle

```text
DRAFT
→ PROPOSED
→ REVIEW
→ APPROVED
→ PUBLISHED
→ EFFECTIVE
→ AMENDED
→ SUSPENDED
→ REPEALED
→ ARCHIVED
```

Không được xóa lịch sử pháp lý.

---

# 8. Legal Rule

```text
LegalRule {
    condition
    subject
    action
    obligation
    prohibition
    permission
    exception
    consequence
    jurisdiction
    temporal_scope
    source
}
```

Các primitive:

```text
Duty
Right
Permission
Prohibition
Power
Immunity
Liability
Responsibility
Privilege
```

---

# 9. Deontic Model

Axiom cần mô hình hóa:

```text
OBLIGATED
PERMITTED
FORBIDDEN
AUTHORIZED
UNAUTHORIZED
OPTIONAL
CONDITIONALLY_ALLOWED
```

Ví dụ:

```text
if condition:
    action = PERMITTED
```

Không đồng nghĩa:

```text
PERMITTED → SHOULD
```

Legal permission không phải moral recommendation.

---

# 10. Rights Model

```text
Right
RightHolder
RightObject
RightScope
RightConstraint
RightException
RightEnforcement
RightRemedy
```

Rights có thể thuộc:

```text
person
organization
institution
community
state-like entity
contract party
AI/software entity
synthetic simulation entity
```

Nhưng:

```text
representation of a right
≠
automatic legal recognition
```

---

# 11. Duties

```text
Duty
DutyHolder
DutyBeneficiary
DutyCondition
DutyDeadline
DutyPerformance
DutyBreach
```

Lifecycle:

```text
CREATED
→ ACTIVE
→ PERFORMED
→ DISCHARGED
```

hoặc:

```text
ACTIVE
→ BREACHED
→ REMEDIED
→ RESOLVED
```

---

# 12. Liability

```text
Liability
LiabilityType
LiableParty
Trigger
Causation
Damage
Defense
Remedy
Allocation
```

Không được tự động coi:

```text
prediction of liability == legal liability
```

---

# 13. Legal Person / Entity

```text
LegalEntity
NaturalPerson
Organization
Corporation
Institution
PublicEntity
ContractEntity
TrustEntity
OtherEntity
```

Axiom phải phân biệt:

```text
Agent
Human
Organization
LegalEntity
SoftwareEntity
AIEntity
```

Không tự động:

```text
AI agent → legal person
```

Legal status phải đến từ authority.

---

# 14. Contract Model

```text
Contract
ContractParty
ContractTerm
ContractClause
Condition
Covenant
Representation
Warranty
Obligation
Right
Remedy
Breach
Termination
Amendment
```

Lifecycle:

```text
DRAFT
→ NEGOTIATION
→ OFFER
→ ACCEPTANCE
→ EXECUTED
→ ACTIVE
→ AMENDED
→ COMPLETED
```

---

# 15. Contract State

Một contract engine phải có:

```text
ContractState
ContractVersion
ContractEvent
ContractObligationState
ContractPerformance
ContractBreach
```

Mỗi version có content hash.

---

# 16. Contract Interpretation

```text
ContractInterpretation
ClauseInterpretation
Definition
Context
Precedent
ApplicableLaw
InterpretationResult
InterpretationConfidence
```

AI có thể đề xuất interpretation.

Nhưng:

```text
AI interpretation != authoritative judicial interpretation
```

---

# 17. Legal Knowledge Graph

BOOTSTRAP-675 sử dụng BOOTSTRAP-645:

```text
Person
Organization
Law
Case
Court
Judge
Contract
Right
Duty
Evidence
Decision
Jurisdiction
```

Relations:

```text
governs
creates_right
creates_duty
amends
repeals
depends_on
interprets
overrules
cites
applies_to
violates
remedies
```

---

# 18. Legal Precedent

```text
Precedent
CaseLaw
JudicialOpinion
Holding
Reasoning
Dicta
Citation
Overruling
Distinguishing
```

Phải phân biệt:

```text
binding_precedent
persuasive_precedent
historical_precedent
simulated_precedent
```

---

# 19. Court System

```text
Court
Tribunal
Chamber
CourtLevel
JudicialPanel
Judge
Magistrate
Clerk
CourtAdministrator
```

Court hierarchy:

```text
TrialCourt
→ AppellateCourt
→ SupremeCourt
```

Không được hard-code một cấu trúc duy nhất.

---

# 20. Court Case

```text
Case
CaseId
CaseType
CaseParty
Claim
Defense
Issue
QuestionOfLaw
QuestionOfFact
EvidenceSet
Hearing
Order
Judgment
Appeal
```

Case lifecycle:

```text
FILED
→ ACCEPTED
→ SERVICE
→ PLEADING
→ DISCOVERY
→ HEARING
→ DELIBERATION
→ DECISION
→ APPEAL
→ FINAL
→ ENFORCEMENT
→ CLOSED
```

---

# 21. Civil / Criminal / Administrative / Commercial

Các case type:

```text
CivilCase
CriminalCase
AdministrativeCase
CommercialCase
ConstitutionalCase
FamilyCase
LaborCase
TaxCase
IntellectualPropertyCase
InternationalCase
ArbitrationCase
```

Nhưng semantic model dùng chung.

---

# 22. Legal Claim

```text
Claim
Claimant
Respondent
CauseOfAction
ReliefRequested
LegalBasis
FactualBasis
```

Claim phải phân biệt:

```text
fact
assertion
allegation
proven_fact
legal_argument
legal_conclusion
```

---

# 23. Evidence Model

```text
Evidence
EvidenceItem
EvidenceSource
EvidenceCollection
EvidenceChain
EvidenceAuthenticity
EvidenceIntegrity
EvidenceAdmissibility
EvidenceWeight
```

Evidence types:

```text
Document
Testimony
PhysicalEvidence
DigitalEvidence
ExpertOpinion
ForensicEvidence
Image
Video
Audio
Log
Record
SensorData
```

---

# 24. Chain of Custody

```text
ChainOfCustody
CustodyEvent
Collector
Transfer
Storage
Access
Hash
Signature
Timestamp
```

Invariant:

```text
critical evidence history is append-only
```

---

# 25. Digital Evidence

Tích hợp:

```text
603 security
610 cryptography
628 distributed data
633 audit
```

Digital evidence có:

```text
content_hash
source
collection_method
timestamp
device
collector
chain_of_custody
integrity_status
```

---

# 26. Evidence Admissibility

```text
AdmissibilityRule
AdmissibilityDecision
ExclusionRule
AuthenticationRule
PrivilegeRule
RelevanceRule
```

Một AI model chỉ có thể:

```text
propose admissibility
```

trừ khi được cấp authority phù hợp.

---

# 27. Legal Fact

```text
Fact
AllegedFact
EstablishedFact
DisputedFact
UnknownFact
InferredFact
SimulatedFact
```

Critical invariant:

```text
inference != established fact
```

---

# 28. Burden of Proof

```text
BurdenOfProof
StandardOfProof
ProofThreshold
EvidenceThreshold
```

Các standard được cấu hình theo legal system:

```text
preponderance
clear_and_convincing
beyond_reasonable_doubt
custom
```

Không hard-code một standard cho mọi jurisdiction.

---

# 29. Legal Reasoning

```text
LegalReasoning
RuleApplication
FactMatching
PrecedentAnalysis
StatutoryInterpretation
ContractInterpretation
ConflictResolution
JurisdictionAnalysis
```

Pipeline:

```text
Facts
↓
Applicable Law
↓
Rule Selection
↓
Interpretation
↓
Evidence
↓
Arguments
↓
Analysis
↓
Decision
```

---

# 30. Rule Conflict

```text
RuleConflict
ConflictResolution
LexSpecialis
LexPosterior
LexSuperior
JurisdictionPriority
AuthorityPriority
TemporalPriority
```

Các nguyên tắc này phải là configurable rules.

Không được mặc định một hierarchy universal.

---

# 31. Legal Temporal Logic

Luật cần hỗ trợ:

```text
effective_from
effective_until
amended_at
repealed_at
transition_period
retroactivity
```

Ví dụ:

```text
law_v1 valid [2020, 2023)
law_v2 valid [2023, ∞)
```

Case năm 2022 phải evaluate theo temporal context phù hợp.

---

# 32. Regulatory System

```text
Regulator
Regulation
RegulatoryRequirement
License
Permit
Inspection
Report
ComplianceObligation
Violation
EnforcementAction
```

Lifecycle:

```text
REGISTER
→ LICENSE
→ OPERATE
→ MONITOR
→ INSPECT
→ COMPLY / VIOLATE
→ REMEDIATE
→ CLOSE
```

---

# 33. Compliance Engine

```text
ComplianceRule
ComplianceRequirement
ComplianceCheck
ComplianceResult
ComplianceEvidence
ComplianceReport
Violation
Remediation
```

Kết quả:

```text
COMPLIANT
NON_COMPLIANT
PARTIALLY_COMPLIANT
UNKNOWN
NOT_APPLICABLE
```

`UNKNOWN` không được biến thành `COMPLIANT`.

---

# 34. Regulatory Reporting

```text
RegulatoryReport
ReportingPeriod
RequiredField
EvidenceReference
Submission
SubmissionReceipt
Correction
```

Submission phải immutable sau khi accepted; correction tạo version mới.

---

# 35. License / Permit

```text
License
Permit
Credential
Qualification
Scope
Restriction
Expiration
Suspension
Revocation
Renewal
```

Không được nhầm:

```text
credential != legal authority
```

---

# 36. Inspection

```text
Inspection
Inspector
InspectionScope
InspectionFinding
InspectionEvidence
InspectionReport
CorrectiveAction
```

---

# 37. Enforcement

```text
EnforcementAction
Warning
Notice
Fine
Restriction
Suspension
Revocation
RemediationOrder
OtherAuthorizedAction
```

Action chỉ được thực thi nếu authority policy cho phép.

---

# 38. Dispute Resolution

```text
Dispute
DisputeParty
Negotiation
Mediation
Arbitration
Adjudication
Settlement
Appeal
```

Phân biệt:

```text
668 = federation/inter-organizational dispute infrastructure
675 = legal dispute semantics and judicial workflow
```

---

# 39. Mediation

```text
Mediator
MediationSession
Position
Interest
Proposal
SettlementDraft
SettlementAgreement
```

Mediation system không được tự động áp đặt settlement.

---

# 40. Arbitration

```text
Arbitration
Arbitrator
ArbitrationAgreement
Submission
Hearing
Award
Challenge
Enforcement
```

---

# 41. Judgment

```text
Judgment
Holding
Reasoning
Order
Remedy
Disposition
```

Lifecycle:

```text
DRAFT
→ DELIBERATION
→ ISSUED
→ PUBLISHED
→ APPEALED
→ FINAL
```

---

# 42. Remedies

```text
Remedy
Damages
Restitution
SpecificPerformance
Injunction
DeclaratoryRelief
CorrectiveAction
OtherRemedy
```

Không hard-code remedy semantics cho mọi jurisdiction.

---

# 43. Appeal

```text
Appeal
Appellant
Appellee
Ground
Record
ReviewScope
AppellateDecision
```

Review modes:

```text
de_novo
clear_error
abuse_of_discretion
question_of_law
custom
```

---

# 44. Rights Enforcement

```text
RightsClaim
RightsViolation
Remedy
ProtectiveOrder
Review
Appeal
```

Rights engine phải hỗ trợ:

```text
right exists
right applies
right conflict
right limitation
right exception
right remedy
```

nhưng không tự xác định một political/moral ideology.

---

# 45. Constitutional / Fundamental Rights Model

```text
Constitution
FundamentalRight
ConstitutionalProvision
ConstitutionalReview
ConstitutionalChallenge
```

Constitutional interpretation vẫn là jurisdiction-specific.

---

# 46. Privacy Law Boundary

675 có:

```text
LegalPrivacyRule
PrivacyRight
DataProtectionDuty
DisclosureAuthority
```

nhưng actual data access vẫn phải đi qua:

```text
640 Data Governance
603 Capability
```

---

# 47. Health Law Boundary

674 cung cấp:

```text
medical record
clinical event
consent
health state
```

675 cung cấp:

```text
medical legal authority
healthcare regulation
medical liability
legal consent semantics
```

Không trộn hai layer.

---

# 48. Financial Law Boundary

671:

```text
transaction
market
finance
payment
accounting
```

675:

```text
financial regulation
contract law
licensing
compliance
legal dispute
```

---

# 49. Employment Law Boundary

670:

```text
labor
workforce
employment
```

675:

```text
employment contract
labor regulation
workplace rights
dispute
compliance
```

---

# 50. Intellectual Property

```text
IntellectualProperty
Copyright
Patent
Trademark
TradeSecret
License
Assignment
Infringement
Ownership
PriorArt
```

Patent model:

```text
PatentApplication
Claim
PriorArt
Examination
Grant
Opposition
Invalidation
```

Copyright model:

```text
Work
Author
Rights
License
DerivativeWork
Infringement
```

---

# 51. Property Rights

```text
Property
RealProperty
PersonalProperty
DigitalProperty
Ownership
Possession
Custody
Transfer
Lien
Encumbrance
```

Phân biệt:

```text
ownership != possession != custody
```

---

# 52. Trust / Estate / Succession

```text
Trust
Trustee
Beneficiary
TrustAsset
Will
Estate
Inheritance
Succession
Executor
```

Jurisdiction-specific rules.

---

# 53. Family / Personal Status

```text
FamilyRelation
MarriageStatus
Parentage
Guardianship
Custody
Adoption
```

Đây là legal data model, không phải social-value engine.

---

# 54. Criminal Law Model

```text
Offense
Element
MensRea
ActusReus
Attempt
Participation
Defense
Victim
Prosecution
Sentence
```

Phải phân biệt:

```text
suspicion
investigation
charge
conviction
```

---

# 55. Criminal Procedure

```text
Investigation
SearchAuthorization
Arrest
Charge
Hearing
Trial
Verdict
Sentence
Appeal
```

Không được coi:

```text
prediction → guilt
```

---

# 56. Legal Investigation

```text
Investigation
Investigator
Lead
Evidence
Hypothesis
Interview
Search
ForensicAnalysis
InvestigationReport
```

Investigation model phải giữ:

```text
fact
hypothesis
uncertainty
evidence
```

riêng biệt.

---

# 57. Presumption Model

```text
Presumption
Rebuttal
CounterEvidence
PresumptionStatus
```

Một presumption có thể:

```text
active
rebutted
rebuttable
irrebuttable
jurisdiction_specific
```

---

# 58. Legal AI

```text
LegalModel
LegalSearchModel
CaseSimilarityModel
ContractModel
ComplianceModel
RiskModel
LegalReasoningModel
DocumentModel
EvidenceModel
```

Model metadata:

```text
model_version
training_source
jurisdiction_scope
temporal_scope
validation
limitations
confidence
```

---

# 59. Legal AI Safety

Không được mặc định:

```text
AI prediction = court decision
AI score = guilt
AI score = legal liability
AI similarity = precedent
AI summary = authoritative law
```

AI có thể:

```text
search
retrieve
summarize
compare
classify
extract
propose
simulate
```

nhưng authority phải được explicit.

---

# 60. Legal Research

```text
LegalSearch
LegalCorpus
CaseSearch
StatuteSearch
RegulationSearch
PrecedentSearch
CitationGraph
LegalTimeline
```

Search phải giữ:

```text
jurisdiction
effective_date
authority_level
version
status
```

---

# 61. Legal Document

```text
LegalDocument
Clause
Section
Article
Schedule
Appendix
Citation
Signature
Seal
Version
```

Hỗ trợ:

```text
diff
merge
redline
compare
validate
sign
archive
```

---

# 62. Digital Signature

Tích hợp BOOTSTRAP-610:

```text
LegalSignature
Signer
SignatureAlgorithm
Certificate
Timestamp
Verification
```

Signature verification không đồng nghĩa document validity về mặt pháp lý.

---

# 63. Legal Entity Identity

Tích hợp:

```text
627 Distributed Identity
```

Các object:

```text
LegalIdentity
LegalIdentifier
AuthorityCredential
Representation
PowerOfAttorney
Delegation
```

---

# 64. Power of Attorney

```text
PowerOfAttorney
Principal
Agent
AuthorityScope
EffectivePeriod
Restriction
Revocation
```

---

# 65. Representation

```text
Representative
RepresentedParty
RepresentationScope
Authority
Delegation
SubDelegation
```

Không được implicit grant quyền đại diện.

---

# 66. Legal Obligation Engine

```text
ObligationEngine
ObligationState
Deadline
Condition
Trigger
Fulfillment
Breach
Remedy
```

Có thể tự động:

```text
detect_due
detect_breach_candidate
generate_notice
```

nhưng enforcement cần authority.

---

# 67. Compliance Automation

Ví dụ:

```axiom
@compliance
rule report_due {
    when reporting_period.closed
    require regulatory_report.submitted
}
```

Result:

```text
ComplianceResult
```

không phải automatic punishment.

---

# 68. Legal Workflow Engine

```text
LegalWorkflow
Step
Transition
Condition
Deadline
Actor
Authority
Escalation
```

Có thể chạy:

```text
court workflow
contract workflow
regulatory workflow
compliance workflow
appeal workflow
```

---

# 69. Deadline Engine

Hỗ trợ:

```text
Calendar
BusinessDay
Holiday
FilingDeadline
AppealDeadline
ContractDeadline
RegulatoryDeadline
SuspensionPeriod
Extension
```

Calendar là jurisdiction-specific.

---

# 70. Legal Calculation

Axiom cần exact arithmetic cho:

```text
damages
interest
fines
contract quantities
tax-related legal calculations
deadlines
shares
percentages
```

Không dùng floating point khi legal exactness yêu cầu.

---

# 71. Legal Simulation

```text
LegalSimulation
CourtSimulation
RegulatorySimulation
ComplianceSimulation
ContractSimulation
PolicyScenario
JusticeSystemScenario
```

Có thể chạy:

```text
what_if
counterfactual
workflow
resource
case_load
compliance
```

Nhưng:

```text
simulation_result != legal ruling
```

---

# 72. Court Digital Twin

```text
CourtDigitalTwin
CaseFlowModel
JudgeCapacityModel
HearingCapacity
BacklogModel
AppealModel
```

Dùng BOOTSTRAP-648/655.

Không được coi simulation là authority.

---

# 73. Legal Analytics

Metrics:

```text
case_volume
case_duration
backlog
appeal_rate
compliance_rate
processing_time
resource_usage
```

Analytics không tự động đánh giá moral worth của participants.

---

# 74. Legal Statistics

```text
LegalStatistic
CaseStatistic
CrimeStatistic
ComplianceStatistic
CourtStatistic
RegulatoryStatistic
```

Mọi aggregate phải giữ:

```text
population
period
jurisdiction
method
uncertainty
```

---

# 75. Access Control

Critical legal resources:

```text
CaseFile
Evidence
SealedRecord
ProtectedRecord
LegalAdvice
CourtRecord
InvestigationRecord
JuvenileRecord
ConfidentialDocument
```

phải có policy-based access.

---

# 76. Sealing

```text
RecordSeal
SealScope
SealReason
SealAuthority
SealExpiration
Unseal
```

---

# 77. Legal Retention

```text
RetentionPolicy
RetentionPeriod
LegalHold
Archive
DestructionAuthorization
```

Legal hold phải ngăn deletion khi applicable.

---

# 78. Conflict of Interest

```text
ConflictOfInterest
Disclosure
Recusal
Waiver
Review
```

Có thể áp dụng cho:

```text
Judge
Arbitrator
Attorney
Expert
Regulator
Inspector
DecisionMaker
AISystem
```

---

# 79. AI Recusal

Một AI legal system có thể có:

```text
ModelConflict
TrainingConflict
DataConflict
InstitutionalConflict
```

Nếu policy yêu cầu:

```text
AI model → recused
```

---

# 80. Legal Ethics Boundary

675 có thể biểu diễn:

```text
EthicalRule
ProfessionalDuty
ConflictRule
DisclosureRule
```

nhưng không hard-code một universal moral philosophy.

---

# 81. Regulatory Policy Input

Policy layer `639` có thể cung cấp:

```text
PolicyInput
AuthorityScope
Threshold
Requirement
Exception
EnforcementPolicy
```

675 consume chúng để evaluate legal/compliance state.

---

# 82. Authority Boundary

Mọi legal action phải có:

```text
Authority
Scope
Issuer
Jurisdiction
EffectivePeriod
```

Không được:

```text
missing_authority → assume_authority
```

---

# 83. Multi-Jurisdiction

Hỗ trợ đồng thời:

```text
JurisdictionA
JurisdictionB
InternationalLaw
TreatyLaw
ContractLaw
OrganizationalRules
```

Có thể có conflict:

```text
JurisdictionConflict
ChoiceOfLaw
ForumSelection
Recognition
Enforcement
```

---

# 84. Cross-Border

```text
CrossBorderCase
ForeignJudgment
Recognition
Enforcement
TreatyBasis
MutualRecognition
ExtraditionModel
LegalAssistance
```

Actual authority phụ thuộc legal system configuration.

---

# 85. Treaty Boundary

Treaty semantics có thể tham chiếu:

```text
668 Federation/Treaty
```

675 xử lý:

```text
legal interpretation
legal obligations
enforcement
case application
```

---

# 86. Administrative Law

```text
AdministrativeAction
AdministrativeDecision
Agency
Regulation
Review
Appeal
JudicialReview
```

---

# 87. Regulatory Impact Analysis

```text
RegulationModel
ImpactModel
AffectedPopulation
CostModel
RiskModel
Scenario
Outcome
```

Có thể sử dụng:

```text
671 economy
670 society
669 infrastructure
648 simulation
652 optimization
653 causal reasoning
```

Nhưng output là analysis, không phải automatic policy choice.

---

# 88. Rights Conflict

```text
RightsConflict
RightA
RightB
Scope
Limitation
BalancingRule
Resolution
```

`BalancingRule` phải được jurisdiction/configuration cung cấp.

---

# 89. Legal Uncertainty

Legal engine phải biểu diễn:

```text
Certain
Likely
Uncertain
Contested
Unknown
Conflicting
PendingInterpretation
```

Không ép mọi legal query thành boolean.

---

# 90. Legal Argument Graph

```text
Argument
Premise
CounterArgument
Evidence
Rule
Inference
Conclusion
Rebuttal
```

Graph:

```text
Evidence
   ↓
Premise
   ↓
Rule
   ↓
Inference
   ↓
Conclusion
```

---

# 91. Explainability

Legal AI output phải cho biết:

```text
applicable_rules
sources
precedents
evidence
assumptions
reasoning_steps
uncertainty
jurisdiction
effective_date
model_version
```

---

# 92. Citation Integrity

Mọi generated legal analysis có citation graph:

```text
Claim
→ Source
→ Version
→ EffectiveDate
→ Jurisdiction
```

Không cho phép citation tới version không còn hiệu lực mà không ghi historical context.

---

# 93. Legal Knowledge Versioning

```text
LegalCorpusVersion
StatuteVersion
CaseLawVersion
RegulationVersion
GuidelineVersion
```

Cache key phải bao gồm legal corpus version.

---

# 94. Reproducible Legal Analysis

Một legal analysis phải có thể replay:

```text
input facts
+
legal corpus version
+
jurisdiction
+
date
+
rules
+
model version
```

→

```text
same_analysis
```

trừ các component explicitly nondeterministic.

---

# 95. Immutable Case Record

Case history:

```text
CaseEventLog
```

Ví dụ:

```text
CaseFiled
PartyAdded
ClaimSubmitted
EvidenceAdded
HearingScheduled
HearingHeld
MotionFiled
MotionDecided
JudgmentIssued
AppealFiled
AppealDecided
CaseClosed
```

---

# 96. Legal Event Sourcing

Current case state:

```text
materialized_view(CaseEventLog)
```

Không sửa event lịch sử.

Correction:

```text
CorrectionEvent
```

---

# 97. Distributed Courts / Legal Systems

Hỗ trợ:

```text
centralized
federated
distributed
multi-court
cross-border
offline
```

Critical judicial records cần strong consistency.

Analytics có thể eventual consistency.

---

# 98. Offline Legal Operations

Có thể dùng:

```text
mobile court
field inspection
offline compliance
remote arbitration
disaster legal service
```

Sync:

```text
event replay
conflict detection
signature validation
authority validation
```

---

# 99. Security

Tích hợp:

```text
603
610
627
628
633
640
665
```

Không được để legal database bypass capability security.

---

# 100. Legal Model Registry

```text
LegalModelRegistry
RuleEngine
PrecedentModel
ComplianceModel
ContractModel
EvidenceModel
CaseSimilarityModel
LegalNLPModel
```

Lifecycle:

```text
DRAFT
→ VALIDATED
→ APPROVED
→ DEPLOYED
→ MONITORED
→ DEPRECATED
→ RETIRED
```

---

# 101. Model Governance

Mỗi legal AI model cần:

```text
jurisdiction_scope
legal_corpus_version
training_data_provenance
validation
limitations
known_failure_modes
drift_status
human_oversight_policy
```

---

# 102. AI Legal Assistant Boundary

AI assistant được phép:

```text
search law
find precedent
summarize documents
extract clauses
compare contracts
identify possible conflicts
generate draft
calculate deadlines
run simulations
```

Không được tự động:

```text
issue judgment
declare guilt
grant legal authority
revoke rights
execute coercive enforcement
```

nếu không có explicit authority.

---

# 103. Human-in-the-Loop

High-impact legal actions:

```text
judgment
criminal conviction
rights restriction
license revocation
coercive enforcement
custody decision
major regulatory action
```

phải hỗ trợ:

```text
review
approval
override
appeal
audit
```

theo jurisdiction/policy.

---

# 104. Legal Data Provenance

Mọi legal object có:

```text
source
issuer
jurisdiction
effective_date
version
retrieval_time
integrity_hash
```

---

# 105. Legal Document Integrity

Canonical representation:

```text
normalized_document
content_hash
signature
timestamp
version
```

Cho phép xác định:

```text
same document
modified document
superseded document
invalid signature
```

---

# 106. Contract Execution

Contract engine có thể tự động hóa:

```text
deadline reminder
condition check
payment trigger
delivery verification
document generation
compliance check
```

Nhưng irreversible external actions phải qua capability/authority boundary.

---

# 107. Smart Contract Boundary

Axiom có thể hỗ trợ:

```text
ContractCode
ContractState
ContractEvent
ContractCondition
```

nhưng:

```text
code execution != legal validity
```

Legal contract và executable contract là hai layer có thể liên kết nhưng không đồng nhất.

---

# 108. Compliance + Runtime

Ví dụ:

```axiom
@compliance
rule encrypted_storage_required {
    require storage.encryption == true
}
```

Runtime có thể:

```text
evaluate
→ report
→ alert
```

Enforcement chỉ khi authority cho phép.

---

# 109. Legal Test Categories

Mục tiêu ≥ 5,000 tests:

```text
Legal core                    500
Jurisdiction                  300
Rules                         450
Rights/duties                 350
Contracts                     400
Courts/cases                  550
Evidence                      450
Precedent                     300
Regulation/compliance         450
Dispute resolution            300
Criminal procedure            300
Civil/commercial               250
IP/property                    250
Legal AI                       400
Privacy/security               300
Distributed/offline            250
Simulation                     250
Compiler/IR                    350
```

Integration tests phải đưa tổng lên ≥ 5,000.

---

# 110. Core Invariants

## L01 — Jurisdiction

Mọi legal rule phải có jurisdiction hoặc explicit global scope.

## L02 — Temporal Validity

Rule phải được evaluate theo effective period.

## L03 — Authority

Legal action phải có authority phù hợp.

## L04 — Provenance

Legal source phải có provenance.

## L05 — Version

Legal source phải versioned.

## L06 — Case Immutability

Case history không được silently mutate.

## L07 — Evidence Integrity

Critical evidence phải giữ chain of custody.

## L08 — Fact Separation

Allegation không phải established fact.

## L09 — AI Separation

AI output không tự động là legal decision.

## L10 — Simulation Separation

Simulation không phải real legal ruling.

## L11 — Contract Versioning

Contract amendment không được overwrite lịch sử.

## L12 — Compliance Unknown

Unknown không được coi là compliant.

## L13 — Rights

Rights representation không tự động tạo legal recognition.

## L14 — Entity

AI/software entity không tự động có legal personhood.

## L15 — Appeal

Appeal phải giữ immutable lower-level decision.

## L16 — Evidence

Evidence source và evidence interpretation phải riêng.

## L17 — Citation

Legal citation phải trỏ tới source/version hợp lệ.

## L18 — Privacy

Protected legal records phải chịu access control.

## L19 — Human Control

High-impact legal action phải tuân thủ oversight policy.

## L20 — Authority Non-Escalation

Một legal capability không được tự nâng scope authority.

---

# 111. Property Testing

Bắt buộc property tests cho:

```text
jurisdiction resolution
rule temporal validity
rule conflict
rights/duties consistency
contract lifecycle
contract amendment
case replay
evidence chain
chain-of-custody
precedent graph
appeal preservation
compliance evaluation
license lifecycle
regulatory reporting
legal hold
privacy enforcement
authority scope
legal AI reproducibility
simulation isolation
multi-jurisdiction conflicts
offline synchronization
```

---

# 112. Formal Safety Properties

Implementation compliant phải đảm bảo:

```text
∀ rule:
    jurisdiction is defined

∀ legal_action:
    authority.scope covers action

∀ evidence:
    provenance != null

∀ case:
    historical_events immutable

∀ legal_ai_output:
    model_version != null

∀ compliance_result:
    unknown != compliant

∀ simulation:
    real_legal_state unchanged

∀ rights_change:
    authority == valid

∀ judgment:
    source_case != null

∀ legal_document:
    version != null
```

---

# 113. Compiler IR

Các operation chính:

```text
LegalSystemCreate

JurisdictionCreate
JurisdictionRuleCreate

LegalSourceCreate
LegalSourceVersion
LegalSourcePublish
LegalSourceAmend
LegalSourceRepeal

LegalRuleCreate
LegalRuleEvaluate
LegalRuleConflictResolve

RightCreate
RightAssign
RightLimit
RightEnforce

DutyCreate
DutyFulfill
DutyBreach
DutyRemedy

LegalEntityCreate
LegalIdentityLink

ContractCreate
ContractAmend
ContractExecute
ContractTerminate
ContractObligationEvaluate
ContractBreach

CaseCreate
CaseFile
PartyAdd
ClaimAdd
DefenseAdd

EvidenceCreate
EvidenceCollect
EvidenceTransfer
EvidenceVerify
EvidenceAdmit
EvidenceExclude

HearingSchedule
HearingOpen
HearingClose

MotionCreate
MotionDecide

JudgmentDraft
JudgmentIssue
JudgmentPublish

AppealCreate
AppealReview
AppealDecide

MediationCreate
MediationSession
SettlementCreate

ArbitrationCreate
ArbitrationHearing
ArbitrationAward

RegulationCreate
RegulationPublish
ComplianceRuleCreate
ComplianceEvaluate
ComplianceReport
ViolationCreate
RemediationCreate

LicenseCreate
LicenseRenew
LicenseSuspend
LicenseRevoke

InspectionCreate
InspectionPerform
InspectionReport

LegalModelRegister
LegalModelValidate
LegalModelDeploy
LegalModelMonitor

LegalSimulationCreate
LegalSimulationStep
LegalSimulationRun
LegalSimulationBranch
LegalSimulationCheckpoint
LegalSimulationRestore

LegalAudit
LegalProvenanceAudit
LegalPrivacyAudit
```

---

# 114. CLI

```text
axiom legal list
axiom legal inspect
axiom legal status

axiom jurisdiction list
axiom jurisdiction inspect

axiom law search
axiom law inspect
axiom law version
axiom law timeline

axiom rule list
axiom rule evaluate
axiom rule explain

axiom rights list
axiom rights inspect
axiom rights enforce

axiom duty list
axiom duty inspect
axiom duty status

axiom contract create
axiom contract inspect
axiom contract diff
axiom contract validate
axiom contract amend
axiom contract execute

axiom case list
axiom case create
axiom case inspect
axiom case history
axiom case file

axiom evidence list
axiom evidence inspect
axiom evidence verify
axiom evidence chain

axiom court list
axiom court case
axiom court hearing
axiom court judgment

axiom appeal create
axiom appeal inspect
axiom appeal decide

axiom mediation create
axiom mediation session
axiom mediation settlement

axiom arbitration create
axiom arbitration hearing
axiom arbitration award

axiom regulation list
axiom regulation inspect

axiom compliance check
axiom compliance report
axiom compliance violations

axiom license list
axiom license inspect
axiom license renew
axiom license suspend
axiom license revoke

axiom inspection create
axiom inspection run
axiom inspection report

axiom legal-ai models
axiom legal-ai evaluate
axiom legal-ai audit

axiom legal simulation create
axiom legal simulation run
axiom legal simulation checkpoint
axiom legal simulation restore

axiom legal audit
axiom legal provenance
axiom legal privacy
```

---

# 115. Compiler Annotations

```text
@legal
@law
@jurisdiction
@legal_rule
@legal_source
@statute
@regulation
@right
@duty
@permission
@prohibition
@liability
@legal_entity
@contract
@contract_party
@contract_clause
@case
@claim
@defense
@evidence
@chain_of_custody
@court
@judge
@hearing
@judgment
@appeal
@precedent
@mediation
@arbitration
@dispute
@compliance
@regulation
@license
@permit
@inspection
@enforcement
@intellectual_property
@copyright
@patent
@trademark
@property
@criminal
@civil
@administrative
@legal_ai
@legal_reasoning
@legal_simulation
@legal_model
@legal_forecast
```

---

# 116. File Extensions

```text
.axlegal
.axlaw
.axjurisdiction
.axrule
.axrights
.axduty
.axcontract
.axcase
.axevidence
.axcourt
.axjudgment
.axappeal
.axprecedent
.axmediation
.axarbitration
.axregulation
.axcompliance
.axlicense
.axpermit
.axinspection
.axproperty
.axip
.axlegalmodel
.axlegalsim
.axlegalforecast
```

---

# 117. Capability Profiles

```text
AXLEGAL_NONE

AXLEGAL_CORE
AXLEGAL_JURISDICTION
AXLEGAL_RULES
AXLEGAL_RIGHTS
AXLEGAL_DUTIES
AXLEGAL_LIABILITY

AXLEGAL_CONTRACT
AXLEGAL_CASE
AXLEGAL_EVIDENCE
AXLEGAL_COURT
AXLEGAL_JUDGMENT
AXLEGAL_APPEAL
AXLEGAL_PRECEDENT

AXLEGAL_MEDIATION
AXLEGAL_ARBITRATION
AXLEGAL_DISPUTE

AXLEGAL_REGULATION
AXLEGAL_COMPLIANCE
AXLEGAL_LICENSE
AXLEGAL_INSPECTION
AXLEGAL_ENFORCEMENT

AXLEGAL_CRIMINAL
AXLEGAL_CIVIL
AXLEGAL_ADMINISTRATIVE
AXLEGAL_COMMERCIAL

AXLEGAL_PROPERTY
AXLEGAL_IP
AXLEGAL_CONSTITUTIONAL

AXLEGAL_LEGAL_AI
AXLEGAL_LEGAL_KNOWLEDGE
AXLEGAL_LEGAL_SIMULATION

AXLEGAL_PRIVACY
AXLEGAL_DISTRIBUTED
AXLEGAL_GPU
AXLEGAL_WASM
AXLEGAL_MOBILE
AXLEGAL_GLOBAL
AXLEGAL_FULL
```

---

# 118. Runtime Cost

Nếu application không sử dụng legal features:

```text
legal runtime = 0
legal database = 0
legal ontology = 0
legal model = 0
```

Compiler chỉ đưa vào binary những thành phần thực sự được tham chiếu.

---

# 119. Integration Matrix

```text
603 → capability/security
610 → cryptographic signatures
627 → legal identity
628 → distributed records
633 → audit
639 → authority/policy
640 → privacy
645 → legal knowledge graph
648 → legal simulation
653 → legal uncertainty/causal reasoning
663 → model evaluation
664 → safety
665 → human oversight
667 → organizations/institutions
668 → treaties/federation
669 → infrastructure
670 → human systems
671 → economic/legal-financial interface
672 → legal research methodology
673 → legal education/training
674 → health-law interface
675 → legal/justice substrate
```

---

# 120. Hard Boundary

BOOTSTRAP-675 **không được** tự trở thành:

```text
government
court
police
legislature
regulator
judge
prosecutor
legal authority
```

Nó chỉ cung cấp computational primitives để xây các hệ thống đó khi một application có authority tương ứng.

---

# 121. Final Contract

BOOTSTRAP-675 cung cấp native substrate cho:

- legal knowledge;
- jurisdictions;
- laws;
- rules;
- rights;
- duties;
- contracts;
- legal entities;
- liability;
- courts;
- cases;
- evidence;
- precedent;
- judgments;
- appeals;
- mediation;
- arbitration;
- regulation;
- compliance;
- licensing;
- inspection;
- enforcement;
- intellectual property;
- property;
- civil/criminal/administrative workflows;
- legal AI;
- legal simulation;
- reproducible legal reasoning.

Nhưng:

```text
Legal model ≠ legal authority
AI analysis ≠ judicial decision
Prediction ≠ guilt
Similarity ≠ precedent
Allegation ≠ fact
Simulation ≠ ruling
Contract code ≠ legal validity
Credential ≠ legal authority
Permission ≠ obligation
Compliance prediction ≠ enforcement
```

Và:

```text
No hidden authority escalation.
No silent legal-record mutation.
No fabricated legal source.
No fabricated precedent.
No automatic conviction.
No automatic rights removal.
No automatic coercive enforcement.
No automatic legal personhood for AI.
No bypass of jurisdiction.
No bypass of human oversight.
```

**BOOTSTRAP-675 = ARCHITECTURE COMPLETE.**

:::

Task kế tiếp trong chuỗi là **BOOTSTRAP-676 — Native AI Civilization-Scale Government, Civic Administration, Public Services, Democratic/Civic Processes & Public Administration Runtime 5.0**.