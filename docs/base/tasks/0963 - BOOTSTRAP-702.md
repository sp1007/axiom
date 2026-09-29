Tiếp tục với **BOOTSTRAP-702**. Task này nối trực tiếp AXSECURITY-701, tập trung vào **tư pháp, tòa án, tố tụng, hồ sơ vụ án và quản trị tư pháp**, đồng thời giữ ranh giới chặt giữa intelligence/security và judicial truth.

:::writing{variant="document" id="74126" title="BOOTSTRAP-702 — AXJUSTICE: Native AI Civilization-Scale Government Justice, Courts, Prosecutorial Case Management, Legal Proceedings & Judicial Administration Runtime 5.0"}
# BOOTSTRAP-702
## AXJUSTICE
### Native AI Civilization-Scale Government Justice, Courts, Prosecutorial Case Management, Legal Proceedings & Judicial Administration Runtime 5.0

**Status:** Architecture Specification  
**Layer:** Government / Justice / Judicial Runtime  
**Depends on:** Axiom Core, Semantic Core, Type & Trait Model, Memory Model, Concurrency Model, Compiler IR, AXLAW, AXGOV, AXSECURITY, AXPOPULATION, AXGEO, AXCRYPT  
**Primary namespace:** `AXJUSTICE`  
**Runtime profile:** `government.justice`

---

# 1. Purpose

`AXJUSTICE` defines the native Axiom infrastructure for:

- courts;
- judicial administration;
- legal proceedings;
- case management;
- prosecution case management;
- defense representation;
- judicial filings;
- hearings;
- orders;
- judgments;
- appeals;
- evidence references;
- exhibits;
- witnesses;
- parties;
- legal claims;
- legal issues;
- procedural deadlines;
- court scheduling;
- judicial assignment;
- legal aid;
- enforcement referrals;
- judicial statistics;
- court records;
- sealed records;
- public records;
- AI-assisted legal administration and analysis.

AXJUSTICE does **not** itself decide what the law should be.

AXLAW owns legal authority and legal rules.

AXJUSTICE executes and records judicial processes under those legal rules.

---

# 2. Fundamental Principle

AXJUSTICE separates:

```text
FACT
CLAIM
ALLEGATION
EVIDENCE
ARGUMENT
LEGAL ISSUE
PROCEDURAL EVENT
FINDING
ORDER
JUDGMENT
ENFORCEMENT
```

These must never collapse into a generic `CaseFact`.

---

# 3. Core Judicial Pipeline

```text
DISPUTE / ALLEGATION
        ↓
CASE INITIATION
        ↓
JURISDICTION
        ↓
PARTIES
        ↓
PLEADINGS / CLAIMS
        ↓
DISCOVERY / EVIDENCE
        ↓
HEARINGS
        ↓
LEGAL ARGUMENT
        ↓
FINDINGS
        ↓
JUDGMENT / ORDER
        ↓
APPEAL / REVIEW
        ↓
FINALITY
        ↓
ENFORCEMENT
        ↓
CLOSURE
        ↓
ARCHIVE
```

---

# 4. Semantic Firewall

Mandatory distinctions:

```text
Allegation != Fact
Claim != Finding
EvidenceReference != EvidenceTruth
Evidence != Fact
Testimony != EstablishedFact
Argument != Finding
LegalTheory != LegalRule
LegalAdvice != LegalDecision
Intelligence != Evidence
ThreatAssessment != JudicialFinding
SecurityReferral != Conviction
Investigation != Prosecution
Prosecution != Conviction
Charge != Guilt
Accusation != Guilt
Arrest != Guilt
Detention != Guilt
Indictment != Guilt
Verdict != Sentence
Judgment != Enforcement
Order != Judgment
Judgment != Finality
Appeal != Reversal
Appeal != NewJudgment
Settlement != Judgment
Mediation != Adjudication
EvidenceAdmissibility != EvidenceWeight
EvidenceWeight != Truth
AIRecommendation != JudicialDecision
AIProbability != LegalProof
LegalResearch != LegalAdvice
CourtSchedule != HearingOutcome
CaseStatus != LegalTruth
CaseClosure != Exoneration
Dismissal != FactualInnocence
Acquittal != UniversalFactualTruth
Conviction != Sentence
Sentence != Enforcement
```

---

# 5. AXJUSTICE Domain Objects

Core entities:

```text
Court
CourtDivision
Judge
Magistrate
Clerk
Prosecutor
DefenseCounsel
LegalRepresentative

Case
CaseParty
Claim
Defense
Charge
LegalIssue
Jurisdiction
Pleading
Motion
Application
Petition

Hearing
Proceeding
Transcript
Notice
Summons

Evidence
EvidenceReference
Exhibit
Witness
Testimony
ExpertReport
Document
DigitalArtifact

Order
Judgment
Verdict
Sentence
Settlement

Appeal
Review
Remand

EnforcementOrder
EnforcementAction

Deadline
Calendar
Assignment
Docket

LegalAidRequest
Fee
Cost

CourtRecord
SealedRecord
PublicRecord

AuditRecord
ProvenanceRecord
AuthorityReference
```

---

# 6. Court Model

```axiom
struct Court {
    id
    jurisdiction
    court_type
    divisions
    authority
    status
}
```

Court types are jurisdiction-defined.

Examples:

```text
TRIAL
APPEAL
SUPREME
CONSTITUTIONAL
SPECIALIZED
ADMINISTRATIVE
COMMERCIAL
FAMILY
JUVENILE
OTHER
```

---

# 7. Court Authority

A court's authority is represented explicitly:

```axiom
struct CourtAuthority {
    court
    jurisdiction
    subject_matter
    geographic_scope
    temporal_scope
    legal_basis
}
```

The runtime must never infer jurisdiction merely from database ownership.

---

# 8. Jurisdiction

Jurisdiction has independent dimensions:

```text
PERSONAL
SUBJECT_MATTER
TERRITORIAL
TEMPORAL
PROCEDURAL
```

Example:

```axiom
jurisdiction.evaluate(
    court,
    case,
    time
)
```

returns a typed result.

---

# 9. Jurisdiction Result

```text
CONFIRMED
PARTIAL
CONTESTED
ABSENT
REQUIRES_REVIEW
```

`CONTESTED` is not equivalent to `ABSENT`.

---

# 10. Judge

```axiom
struct Judge {
    id
    court
    authority
    appointment
    status
}
```

A judge identity is separate from the judge's individual decisions.

---

# 11. Judicial Assignment

Cases are assigned through explicit assignment records:

```axiom
struct JudicialAssignment {
    case_id
    judge_id
    assigning_authority
    assigned_at
    assignment_basis
    status
}
```

---

# 12. Assignment Conflict

The system supports:

```text
ASSIGNED
REASSIGNED
RECUSAL_REQUESTED
RECUSAL_GRANTED
RECUSAL_DENIED
VACATED
```

---

# 13. Recusal

A recusal is a procedural event.

It does not imply:

```text
GUILT
BIAS
MISCONDUCT
```

unless separately established.

---

# 14. Party

A party may be:

```text
PERSON
ORGANIZATION
GOVERNMENT
ESTATE
OTHER_LEGAL_ENTITY
```

---

# 15. Party Role

Roles are typed:

```text
PLAINTIFF
DEFENDANT
PETITIONER
RESPONDENT
CLAIMANT
APPELLANT
APPELLEE
PROSECUTION
ACCUSED
INTERVENOR
AMICUS
OTHER
```

---

# 16. Party Status

```text
ACTIVE
WITHDRAWN
DISMISSED
DECEASED
REPRESENTED
UNREPRESENTED
UNKNOWN
```

Status is procedural metadata, not factual judgment.

---

# 17. Legal Representation

```axiom
struct Representation {
    represented_party
    representative
    authority
    start
    end
    scope
}
```

---

# 18. Counsel

Counsel records:

```text
identity
license/reference
representation_scope
appointment
status
```

AXJUSTICE does not itself define professional licensing rules.

---

# 19. Legal Aid

```axiom
struct LegalAidRequest {
    applicant
    case
    requested_scope
    eligibility_basis
    status
}
```

Possible states:

```text
REQUESTED
UNDER_REVIEW
APPROVED
DENIED
WITHDRAWN
EXPIRED
```

---

# 20. Case

```axiom
struct Case {
    id
    court
    case_type
    jurisdiction
    parties
    claims
    charges
    status
    filing_time
    authority
}
```

---

# 21. Case Identity

`CaseId` must be globally unique within the federation.

It must not be interchangeable with:

```text
PersonId
ClaimId
JudgmentId
InvestigationId
```

---

# 22. Case Lifecycle

Canonical:

```text
INITIATED
→ FILED
→ ACCEPTED
→ ACTIVE
→ HEARING
→ DECIDED
→ REVIEW
→ FINAL
→ ENFORCEMENT
→ CLOSED
→ ARCHIVED
```

Jurisdictions may add states.

---

# 23. Case Closure

Closure means procedural completion.

It does not automatically mean:

```text
ACQUITTAL
EXONERATION
LIABILITY
NO_LIABILITY
```

The actual legal outcome remains separately typed.

---

# 24. Claim

```axiom
struct Claim {
    id
    case
    claimant
    respondent
    statement
    legal_basis
    requested_relief
    status
}
```

---

# 25. Claim Lifecycle

```text
PROPOSED
→ FILED
→ ANSWERED
→ CONTESTED
→ AMENDED
→ ADJUDICATED
→ WITHDRAWN
→ DISMISSED
```

---

# 26. Criminal Charge

A criminal charge is represented separately:

```axiom
struct Charge {
    id
    case
    accused
    offense_reference
    legal_basis
    filed_at
    status
}
```

A charge is not a conviction.

---

# 27. Charge Lifecycle

```text
PROPOSED
→ FILED
→ ACCEPTED
→ CONTESTED
→ AMENDED
→ DISMISSED
or
→ ADJUDICATED
```

---

# 28. Legal Issue

```axiom
struct LegalIssue {
    id
    case
    issue_type
    question
    governing_law
    status
}
```

Examples:

```text
JURISDICTION
ADMISSIBILITY
CONSTITUTIONALITY
INTERPRETATION
LIABILITY
DAMAGES
SENTENCING
PROCEDURE
```

---

# 29. Pleading

```text
COMPLAINT
ANSWER
PETITION
RESPONSE
MOTION
BRIEF
APPEAL
REPLY
OTHER
```

Every pleading contains:

```text
author
party
filing_time
version
claims
requests
attachments
signature
```

---

# 30. Filing

A filing creates an immutable event:

```axiom
court.file(document)
```

Corrections create a new version rather than silently rewriting the original.

---

# 31. Filing Versioning

```text
DRAFT
→ FILED
→ AMENDED
→ SUPERSEDED
```

Original versions remain auditable.

---

# 32. Filing Acceptance

A filing may be:

```text
RECEIVED
ACCEPTED
REJECTED
RETURNED_FOR_CORRECTION
```

Administrative rejection does not itself decide the legal merits.

---

# 33. Motion

```axiom
struct Motion {
    id
    case
    filer
    requested_action
    grounds
    attachments
    status
}
```

---

# 34. Motion Lifecycle

```text
FILED
→ SERVED
→ OPPOSED
→ HEARD
→ GRANTED
or
→ DENIED
or
→ PARTIALLY_GRANTED
```

---

# 35. Order

```axiom
struct CourtOrder {
    id
    court
    case
    issuer
    legal_basis
    directive
    effective_time
    expiry
    status
}
```

An order is an authoritative judicial action.

---

# 36. Order Lifecycle

```text
DRAFT
→ ISSUED
→ SERVED
→ EFFECTIVE
→ MODIFIED
→ VACATED
→ EXPIRED
```

---

# 37. Judgment

```axiom
struct Judgment {
    id
    case
    court
    findings
    legal_conclusions
    relief
    costs
    issued_at
    status
}
```

---

# 38. Judgment Status

```text
ISSUED
PENDING_REVIEW
FINAL
VACATED
REVERSED
REMANDED
MODIFIED
```

---

# 39. Finding of Fact

```axiom
struct FindingOfFact {
    issue
    finding
    supporting_evidence
    reasoning_reference
}
```

A finding must remain distinguishable from the underlying evidence.

---

# 40. Finding of Law

```axiom
struct FindingOfLaw {
    issue
    legal_rule
    interpretation
    application
}
```

---

# 41. Verdict

Criminal adjudication may produce:

```text
GUILTY
NOT_GUILTY
PARTIAL
MISTRIAL
OTHER_JURISDICTION_DEFINED_RESULT
```

Verdict is separate from sentence.

---

# 42. Sentence

```axiom
struct Sentence {
    case
    defendant
    legal_basis
    sentence_type
    duration
    conditions
    effective_time
}
```

Sentence types are jurisdiction-defined.

---

# 43. Settlement

```axiom
struct Settlement {
    parties
    terms
    approval
    effective_time
    status
}
```

Settlement is not equivalent to judicial factual findings unless explicitly incorporated into a judgment.

---

# 44. Mediation

Mediation is modeled independently:

```text
REQUESTED
→ ASSIGNED
→ SESSION
→ AGREEMENT
or
→ NO_AGREEMENT
```

A failed mediation does not establish liability.

---

# 45. Evidence Model

Evidence is layered:

```text
EvidenceItem
EvidenceReference
Exhibit
EvidenceSubmission
EvidenceAssessment
```

---

# 46. Evidence Item

```axiom
struct EvidenceItem {
    id
    type
    source
    collected_at
    provenance
    integrity
    custody
}
```

---

# 47. Evidence Types

```text
DOCUMENT
PHYSICAL_OBJECT
DIGITAL_ARTIFACT
PHOTOGRAPH
VIDEO
AUDIO
TESTIMONY_REFERENCE
EXPERT_REPORT
RECORD
OTHER
```

---

# 48. Evidence Submission

```axiom
struct EvidenceSubmission {
    evidence
    submitted_by
    case
    submission_time
    purpose
    status
}
```

---

# 49. Evidence Admissibility

Admissibility is a legal/procedural determination:

```text
ADMISSIBLE
INADMISSIBLE
CONDITIONALLY_ADMISSIBLE
PENDING
```

Admissibility is not equivalent to truth.

---

# 50. Evidence Weight

The court may record:

```text
EvidenceAssessment {
    relevance
    reliability
    weight
    limitations
}
```

These are separate attributes.

---

# 51. Chain of Custody

```axiom
struct JudicialCustody {
    evidence
    holder
    transferred_at
    reason
    authorization
    integrity_reference
}
```

---

# 52. Custody Event

```text
COLLECTED
→ STORED
→ TRANSFERRED
→ PRESENTED
→ RETURNED
→ SEALED
→ DISPOSED
```

Every transition is auditable.

---

# 53. Digital Evidence

Digital evidence contains:

```text
hash
format
source
acquisition_reference
timestamp
integrity
metadata
```

AXJUSTICE does not assume metadata is truthful merely because it exists.

---

# 54. Evidence Integrity

Possible states:

```text
VERIFIED
UNVERIFIED
CORRUPTED
CONFLICTED
UNKNOWN
```

---

# 55. Witness

```axiom
struct Witness {
    id
    case
    identity
    role
    status
}
```

Witness status is separate from testimony credibility.

---

# 56. Testimony

```axiom
struct Testimony {
    witness
    hearing
    statement
    timestamp
    transcript_reference
}
```

---

# 57. Testimony Assessment

A court may record:

```text
CONSISTENCY
CORROBORATION
CONFLICT
CREDIBILITY_ASSESSMENT
LIMITATIONS
```

The runtime must not infer credibility from demographic attributes.

---

# 58. Expert

```axiom
struct Expert {
    identity
    expertise
    appointment
    report
}
```

Expert qualification is distinct from the truth of an expert opinion.

---

# 59. Expert Report

```text
method
assumptions
data
analysis
conclusion
limitations
```

must remain separate.

---

# 60. Court Hearing

```axiom
struct Hearing {
    id
    case
    court
    type
    scheduled_at
    location
    participants
    status
}
```

---

# 61. Hearing Types

Examples:

```text
PRETRIAL
MOTION
EVIDENTIARY
TRIAL
SENTENCING
APPEAL
STATUS
MEDIATION
OTHER
```

---

# 62. Hearing Lifecycle

```text
SCHEDULED
→ CONFIRMED
→ STARTED
→ SUSPENDED
→ RESUMED
→ COMPLETED
→ ADJOURNED
→ CANCELLED
```

---

# 63. Court Calendar

Calendar records:

```text
court
room
judge
case
hearing
start
end
availability
```

Scheduling does not determine case outcome.

---

# 64. Conflict Detection

Scheduler must detect:

```text
judge conflict
courtroom conflict
party conflict
counsel conflict
witness conflict
remote-system conflict
```

---

# 65. Deadline

```axiom
struct LegalDeadline {
    case
    event
    start
    due
    authority
    computation_rule
    status
}
```

---

# 66. Deadline States

```text
UPCOMING
DUE
OVERDUE
EXTENDED
SUSPENDED
SATISFIED
WAIVED
EXPIRED
```

---

# 67. Deadline Computation

Deadlines must use jurisdiction-specific rules.

```axiom
deadline.calculate(
    rule,
    event_time,
    calendar
)
```

The engine must preserve the exact rule version used.

---

# 68. Service

Court documents may require service:

```text
ISSUED
→ DELIVERED
→ ACKNOWLEDGED
```

or jurisdiction-specific alternatives.

---

# 69. Service Record

```axiom
struct ServiceRecord {
    document
    recipient
    method
    attempted_at
    delivered_at
    proof
}
```

---

# 70. Notice

Notice is distinct from service.

```text
Notice != Service
```

A notice may be informational while service has legal procedural consequences.

---

# 71. Transcript

```axiom
struct Transcript {
    hearing
    source
    version
    segments
    certification
}
```

---

# 72. Transcript Immutability

Certified transcripts cannot be silently edited.

Corrections create amendments.

---

# 73. Court Record

Court records have:

```text
PUBLIC
RESTRICTED
SEALED
CONFIDENTIAL
```

status.

---

# 74. Sealing

A sealed record requires:

```text
authority
legal_basis
scope
start
review
expiry
```

where applicable.

---

# 75. Unsealing

```axiom
record.unseal(
    authority,
    scope
)
```

must be audited.

---

# 76. Public Access

Public record APIs must filter according to:

```text
classification
sealing
privacy
legal restrictions
jurisdiction
```

---

# 77. Privacy

Court systems may contain highly sensitive personal information.

The runtime supports:

```text
redaction
pseudonymization
restricted views
sealed attachments
field-level access
```

---

# 78. Minor/Protected Person Data

Sensitive identity fields may be represented as:

```text
ProtectedIdentity
```

with stricter access policies.

---

# 79. Victim/Protected Witness

The data model supports protected identity:

```axiom
struct ProtectedParty {
    public_reference
    private_identity
    disclosure_policy
}
```

---

# 80. Prosecutorial Case Management

AXJUSTICE may provide prosecution workflow:

```text
referral
→ review
→ charging decision
→ filing
→ prosecution
→ adjudication
```

The prosecution decision remains an authorized legal action.

---

# 81. Investigation Boundary

Investigation systems may provide:

```text
InvestigationReference
```

to AXJUSTICE.

AXJUSTICE does not redefine investigative facts.

---

# 82. Security Intelligence Boundary

AXSECURITY intelligence may be attached as:

```text
IntelligenceReference
```

It does not automatically become evidence.

---

# 83. Evidence Conversion

Where legally permitted:

```text
intelligence
→ evidence acquisition
→ evidence item
```

must be an explicit transformation with provenance.

---

# 84. Prosecution Decision

Possible states:

```text
NO_ACTION
FURTHER_REVIEW
CHARGE
DIVERSION
SETTLEMENT
OTHER
```

No-action does not automatically establish innocence or factual falsity.

---

# 85. Defense

Defense submissions are first-class case objects:

```text
DefenseArgument
DefenseEvidence
DefenseMotion
DefenseWitness
DefenseExpert
```

---

# 86. Legal Argument

Arguments contain:

```text
claim
legal_basis
evidence_reference
reasoning
requested_result
```

Argument is not a court finding.

---

# 87. Legal Research

AI or human research can produce:

```text
LegalResearchResult {
    authorities
    citations
    propositions
    uncertainty
    jurisdiction
    effective_period
}
```

---

# 88. Legal Authority

Authorities include:

```text
CONSTITUTION
STATUTE
REGULATION
CASE_LAW
COURT_RULE
TREATY
ORDINANCE
OTHER
```

AXLAW remains authoritative for the legal corpus.

---

# 89. Legal Versioning

Every legal reference must support:

```text
law_id
version
effective_from
effective_until
jurisdiction
```

---

# 90. Historical Law

A case should be evaluated using the applicable legal state at the relevant time, subject to jurisdiction-specific rules.

The system must never silently substitute current law for historical law.

---

# 91. Legal Interpretation

AXJUSTICE can record:

```text
Interpretation
```

but the runtime must distinguish:

```text
existing_authority
```

from:

```text
proposed_interpretation
```

---

# 92. AI Legal Research

AI may assist with:

```text
case retrieval
citation extraction
precedent comparison
document summarization
timeline generation
issue spotting
contradiction detection
translation
draft organization
```

---

# 93. AI Judicial Boundary

AI must not silently create:

```text
Judgment
Verdict
Sentence
Binding Legal Finding
Final Order
```

---

# 94. Judicial AI Recommendation

AI may return:

```text
relevant_authorities
possible_issues
conflicting_authorities
missing_information
draft_options
procedural_deadlines
```

All are explicitly marked AI-generated.

---

# 95. AI Provenance

Every AI output:

```text
model_id
model_version
input_documents
retrieval_set
prompt/configuration
timestamp
confidence/limitations
```

---

# 96. Citation Verification

AI-generated legal citations should pass:

```text
citation.exists
citation.jurisdiction_matches
citation.time_valid
citation.text_matches
```

before being presented as verified.

---

# 97. Hallucination Firewall

An AI-generated legal authority that cannot be verified must be typed:

```text
UNVERIFIED_REFERENCE
```

not `LegalAuthority`.

---

# 98. Judicial Draft Assistance

The system may generate draft:

```text
order
judgment structure
hearing summary
case summary
```

but drafts are:

```text
DRAFT
```

until adopted by an authorized actor.

---

# 99. Human Adoption

```axiom
draft.adopt(
    judge,
    authority
)
```

creates an explicit judicial action.

---

# 100. Decision Provenance

Every final judgment records:

```text
court
judge
legal_basis
case
evidence_references
findings
legal_conclusions
procedural_history
decision_time
version
```

---

# 101. Decision Versioning

Judgments may be:

```text
DRAFT
SIGNED
ISSUED
CORRECTED
AMENDED
VACATED
REVERSED
REMANDED
FINAL
```

---

# 102. Clerical Correction

Clerical errors can use:

```text
CorrectionOrder
```

rather than rewriting the original judgment.

---

# 103. Appeal

```axiom
struct Appeal {
    id
    originating_case
    appellant
    grounds
    requested_relief
    status
}
```

---

# 104. Appeal Lifecycle

```text
FILED
→ ACCEPTED
→ RECORD_TRANSFERRED
→ BRIEFING
→ HEARING
→ DECIDED
→ FINAL
```

---

# 105. Appeal Outcomes

```text
AFFIRMED
REVERSED
VACATED
MODIFIED
REMANDED
DISMISSED
OTHER
```

---

# 106. Appeal != Automatic Reversal

Filing an appeal does not change the underlying judgment unless an explicit stay or other legal mechanism applies.

---

# 107. Stay

```axiom
struct StayOrder {
    target
    scope
    authority
    effective_time
    expiry
}
```

---

# 108. Remand

A remand creates a procedural relationship:

```text
Appeal
→ Remand
→ OriginalCourtAction
```

The system preserves both records.

---

# 109. Finality

Finality is explicit:

```text
NOT_FINAL
FINAL
PARTIALLY_FINAL
FINALITY_CONTESTED
```

---

# 110. Enforcement

Enforcement begins only from an enforceable authority.

```text
Judgment/Order
→ Enforceability
→ EnforcementReferral
→ EnforcementAction
```

---

# 111. Enforcement Boundary

AXJUSTICE records the judicial basis.

Dedicated enforcement agencies execute physical/administrative enforcement.

---

# 112. Enforcement Order

```axiom
struct EnforcementOrder {
    source_judgment
    authority
    scope
    effective_time
    expiry
}
```

---

# 113. Enforcement Status

```text
NOT_READY
READY
REFERRED
ACTIVE
SUSPENDED
COMPLETED
CANCELLED
```

---

# 114. Enforcement Outcome

Outcome is separate from judgment:

```text
Judgment != EnforcementOutcome
```

---

# 115. Settlement Enforcement

Approved settlements may create enforceable orders depending on jurisdiction.

The legal effect must be explicit.

---

# 116. Court Fees

Fees are separate from judicial merits.

```text
FilingFee
CourtCost
Waiver
Refund
Assessment
```

---

# 117. Fee Waiver

```axiom
struct FeeWaiver {
    applicant
    authority
    basis
    effective_time
}
```

---

# 118. Court Administration

Administrative objects:

```text
CourtStaff
Room
Equipment
Calendar
BudgetReference
DocumentService
Archive
Queue
```

Administrative state must remain separate from judicial findings.

---

# 119. Case Queue

Queue states:

```text
RECEIVED
TRIAGE
WAITING
ASSIGNED
ACTIVE
BLOCKED
COMPLETED
```

---

# 120. Queue Priority

Priority may be based on explicit rules.

It must not silently represent legal merit.

---

# 121. Judicial Workload

Metrics:

```text
pending_cases
average_processing_time
hearing_delay
backlog
case_age
```

Metrics are administrative analytics, not judicial-quality scores.

---

# 122. Judicial Independence Boundary

Administrative systems must not silently modify:

```text
judicial findings
judge decisions
case outcomes
legal reasoning
```

---

# 123. Assignment Transparency

Where permitted, assignment algorithms should preserve:

```text
assignment_rule
randomization_seed
eligibility_set
override_authority
```

---

# 124. Assignment Override

Manual override requires:

```text
authority
reason
timestamp
audit
```

---

# 125. Conflict of Interest

The system may record:

```text
ConflictDeclaration
RecusalRequest
RecusalDecision
```

but must not infer misconduct from a conflict declaration.

---

# 126. Court Security Boundary

AXSECURITY may provide:

```text
security alert
identity verification
facility threat
incident reference
```

AXJUSTICE retains procedural/legal authority.

---

# 127. Court Emergency

AXSAFETY may provide:

```text
building closure
disaster status
evacuation
service disruption
```

AXJUSTICE can reschedule proceedings according to authorized rules.

---

# 128. Remote Hearing

Remote proceedings support:

```text
participant authentication
session authorization
secure channel
recording/transcript
consent/policy
technical status
```

---

# 129. Remote Hearing Failure

States:

```text
CONNECTED
DEGRADED
DISCONNECTED
RECONNECTED
TERMINATED
```

The legal consequence must be governed by jurisdiction-specific procedure.

---

# 130. Recording

Recordings require:

```text
authority
purpose
retention
classification
integrity
```

---

# 131. Transcript Generation

AI transcription may produce:

```text
MachineTranscript
```

which remains distinct from:

```text
CertifiedTranscript
```

until authorized certification.

---

# 132. Audio/Video Evidence

Multimedia objects support:

```text
hash
source
timestamp
format
chain_of_custody
```

---

# 133. Document Redaction

Redaction preserves:

```text
original_hash
redaction_version
authority
reason
scope
```

---

# 134. Public Case API

Public API returns only records allowed by:

```text
public_access_policy
sealing
privacy
jurisdiction
```

---

# 135. Anonymous Publication

Sensitive persons may be represented as:

```text
PARTY_A
PARTY_B
MINOR_A
PROTECTED_WITNESS_1
```

where legally required.

---

# 136. Record Search

Court search supports:

```text
case_id
party
date
court
legal_reference
document_type
status
```

Sensitive fields require authorization.

---

# 137. Search Result Semantics

Search result ranking is not legal importance.

```text
SearchScore != JudicialImportance
```

---

# 138. Document Similarity

Similarity can assist retrieval but does not establish precedent.

```text
Similarity != BindingAuthority
```

---

# 139. Precedent Analysis

AI may group:

```text
similar cases
distinguishable cases
conflicting cases
overruled cases
```

The legal status must be verified against authoritative sources.

---

# 140. Case Citation

Each cited case requires:

```text
court
case_id
decision_date
jurisdiction
official_reference
status
```

---

# 141. Overruling

A precedent may be represented as:

```text
ACTIVE
LIMITED
OVERRULED
SUPERSEDED
UNCERTAIN
```

---

# 142. Legal Conflict

If two authorities conflict:

```text
LEGAL_CONFLICT
```

is represented explicitly.

The runtime does not invent a resolution.

---

# 143. Legal Hierarchy

Where AXLAW supplies a hierarchy:

```text
constitution
→ statute
→ regulation
→ binding precedent
→ persuasive authority
```

the hierarchy is jurisdiction-configurable.

---

# 144. Legal Rule Evaluation

```axiom
law.apply(
    rule,
    facts,
    jurisdiction,
    time
)
```

returns:

```text
Applicable
NotApplicable
Contested
InsufficientFacts
```

---

# 145. Facts Input

The legal engine must distinguish:

```text
ProposedFact
AdmittedFact
StipulatedFact
FoundFact
DisputedFact
UnknownFact
```

---

# 146. Stipulation

```axiom
struct Stipulation {
    parties
    facts
    scope
    court_acceptance
}
```

A stipulation is not necessarily a universal factual truth.

---

# 147. Admission

Admissions are case-scoped unless law says otherwise.

---

# 148. Burden of Proof

The model supports:

```text
burden_of_proof
standard_of_proof
burden_holder
```

Examples:

```text
PREPONDERANCE
CLEAR_AND_CONVINCING
BEYOND_REASONABLE_DOUBT
JURISDICTION_DEFINED
```

---

# 149. Standard of Proof

A probability emitted by an AI model is not automatically equivalent to a legal standard of proof.

---

# 150. Burden Shift

Burden changes must be explicit:

```axiom
burden.transfer(
    authority,
    rule,
    trigger
)
```

---

# 151. Presumption

```axiom
struct LegalPresumption {
    rule
    trigger
    rebuttable
    burden_effect
}
```

---

# 152. Presumption != Fact

A legal presumption must never be materialized as an observed fact.

---

# 153. Evidence Sufficiency

The runtime can calculate procedural completeness:

```text
sufficient_for_filing
sufficient_for_hearing
sufficient_for_submission
```

but should not automatically declare factual guilt.

---

# 154. Legal Reasoning Graph

Represent:

```text
Fact
→ Evidence
→ LegalIssue
→ Rule
→ Interpretation
→ Application
→ Conclusion
```

Every edge has provenance.

---

# 155. Judgment Reasoning

A judgment may expose:

```text
facts_found
issues
rules
analysis
conclusions
orders
```

---

# 156. Reasoning Version

If judgment drafts are AI-assisted:

```text
draft_model
draft_version
source_documents
human_edits
adoption_authority
```

must be retained where policy permits.

---

# 157. AI Draft Integrity

AI-generated text must never be represented as judge-authored until explicitly adopted.

---

# 158. AI Role Separation

Supported roles:

```text
CLERICAL
RESEARCH
RETRIEVAL
SUMMARIZATION
TRANSCRIPTION
ANALYSIS
DRAFTING
```

All are distinct capabilities.

---

# 159. High-Risk AI Actions

Require explicit authorization:

```text
generate_judgment_draft
generate_sentence_draft
recommend_case_disposition
rank_legal_arguments
```

---

# 160. Forbidden Implicit Transformation

Never:

```text
AI_SCORE
→ GUILTY
```

or:

```text
AI_RANKING
→ JUDICIAL_OUTCOME
```

---

# 161. AI Bias Monitoring

Where AI is used in judicial administration, monitor:

```text
error_rate
citation_error
retrieval_quality
language_quality
distribution_shift
human_override_rate
```

These metrics describe system behavior and do not themselves establish legal bias.

---

# 162. Model Audit

Every deployed model must have:

```text
model_card
version
training_scope
known_limitations
evaluation_results
deployment_scope
```

---

# 163. Human Override

AI outputs support:

```text
ACCEPT
MODIFY
REJECT
REQUEST_MORE_INFORMATION
```

---

# 164. AI Audit

Every AI invocation records:

```text
actor
case
purpose
model
inputs
outputs
timestamp
```

subject to privacy/classification policies.

---

# 165. Court AI Sandbox

AI experimentation must use:

```text
AXJUSTICE.SIM
```

or isolated test environments.

Production case records must not be used by arbitrary development agents.

---

# 166. Agent Capability Model

```axiom
agent CourtAssistant {
    capabilities [
        ReadAuthorizedCase,
        SearchLegalCorpus,
        Summarize,
        DraftNonBindingDocument
    ]
}
```

No implicit judicial authority.

---

# 167. Case-Level Capability

Capabilities can be scoped to:

```text
case
document
party
jurisdiction
time
```

---

# 168. Sealed-Record Capability

Reading sealed records requires an explicit capability.

---

# 169. Cross-Case Access

Cross-case analysis requires separate authorization.

---

# 170. Bulk Case Analytics

Bulk access requires:

```text
purpose
authority
scope
privacy controls
audit
```

---

# 171. Anonymized Research Dataset

Court research can use:

```text
AnonymizedCase
```

with direct identifiers removed or transformed.

---

# 172. Statistical Privacy

Optional:

```text
aggregation
k-anonymity
differential_privacy
suppression
```

depending on jurisdiction and research requirements.

---

# 173. Court Statistics

Metrics:

```text
filings
dispositions
pending
case_duration
appeal_rate
hearing_delay
enforcement_status
```

These are descriptive statistics.

---

# 174. No Hidden Performance Ranking

The runtime must not convert raw court metrics into an implicit “best judge” or “worst judge” score without an explicitly governed administrative framework.

---

# 175. Judicial Work Queue

Tasks:

```text
review_filing
schedule_hearing
review_motion
prepare_notice
review_transcript
issue_order
```

Each task carries authority and deadline.

---

# 176. Task State

```text
QUEUED
ASSIGNED
IN_PROGRESS
BLOCKED
COMPLETED
CANCELLED
```

---

# 177. Workflow Engine

```axiom
workflow case_progress {
    filing
    jurisdiction_check
    service
    response
    hearing
    decision
    review
    closure
}
```

---

# 178. Workflow Guard

Each transition has:

```text
preconditions
authority
required_documents
deadline
audit_action
```

---

# 179. Invalid Transition

Example:

```text
CLOSED → HEARING
```

must fail unless an explicit reopening procedure exists.

---

# 180. Reopening

```axiom
case.reopen(
    authority,
    legal_basis
)
```

creates a new procedural event.

---

# 181. Case Consolidation

Cases may be consolidated:

```text
CaseA
+
CaseB
→
ConsolidatedCase
```

Original identities remain.

---

# 182. Case Severance

A consolidated case can be separated:

```text
ConsolidatedCase
→ CaseA
→ CaseB
```

with lineage.

---

# 183. Related Cases

Relationship types:

```text
RELATED
CONSOLIDATED
SEVERED_FROM
APPEAL_OF
REMAND_OF
ENFORCEMENT_OF
```

---

# 184. Criminal/Civil Separation

Criminal and civil proceedings are separate case types.

A relationship may exist without merging them.

---

# 185. Administrative Review

Administrative cases may reference:

```text
agency_decision
review_request
administrative_record
judicial_review
```

---

# 186. Constitutional Review

Constitutional issues are typed separately:

```text
constitutional_question
challenged_provision
constitutional_standard
decision
```

---

# 187. International Proceedings

Where applicable:

```text
treaty
international_court_reference
cross_border_service
foreign_judgment
recognition_request
```

---

# 188. Foreign Judgment

Foreign judgments require:

```text
origin_jurisdiction
authenticity
recognition_status
enforceability
```

They are not automatically domestic judgments.

---

# 189. Extradition Boundary

Extradition requests may be represented:

```text
ExtraditionRequest
```

with links to AXSECURITY and AXLAW.

AXJUSTICE handles judicial proceedings, not operational transport.

---

# 190. Mutual Legal Assistance

```text
MLARequest
```

contains:

```text
requesting_authority
requested_action
legal_basis
scope
status
```

---

# 191. International Evidence

Foreign evidence references preserve:

```text
origin
authority
translation
authentication
chain_of_custody
```

---

# 192. Enforcement Across Jurisdictions

Cross-jurisdiction enforcement requires:

```text
recognition
authority
jurisdiction
scope
```

---

# 193. Legal Document Signature

Court documents support:

```text
digital_signature
signer
certificate
timestamp
signature_status
```

---

# 194. Signature Verification

Possible states:

```text
VALID
INVALID
EXPIRED
REVOKED
UNKNOWN
```

---

# 195. Court Identity

Each court service has a cryptographic identity:

```text
CourtIdentity
```

---

# 196. Secure Filing

Electronic filing pipeline:

```text
CREATE
→ SIGN
→ TRANSMIT
→ VERIFY
→ ACCEPT
→ HASH
→ STORE
→ ACKNOWLEDGE
```

---

# 197. Filing Idempotency

Duplicate submission must not create duplicate cases unless explicitly requested.

---

# 198. Court Notification Bus

Topics:

```text
justice.case.*
justice.filing.*
justice.hearing.*
justice.motion.*
justice.order.*
justice.judgment.*
justice.appeal.*
justice.enforcement.*
justice.evidence.*
justice.audit.*
justice.ai.*
```

---

# 199. Event Structure

```axiom
event JusticeEvent<T> {
    id
    type
    case
    actor
    authority
    event_time
    payload
    provenance
    classification
}
```

---

# 200. Event Ordering

Judicial events require:

```text
event_id
case_sequence
causal_parent
event_time
processing_time
```

---

# 201. Immutable Procedural History

The case timeline is append-only.

Corrections use:

```text
CorrectionEvent
```

---

# 202. Procedural Timeline

Example:

```text
FILED
→ ACCEPTED
→ SERVED
→ RESPONSE
→ MOTION
→ HEARING
→ ORDER
→ JUDGMENT
→ APPEAL
```

---

# 203. Replay

```axiom
case.replay(
    case_id,
    version
)
```

must reconstruct the procedural state.

---

# 204. Historical State

Queries support:

```axiom
case.as_of(timestamp)
```

to reconstruct historical state.

---

# 205. Temporal Legal State

The runtime combines:

```text
case_event_time
+
law_version
+
procedural_rule_version
```

when evaluating historical workflows.

---

# 206. Deadline Recalculation

A change in law must not silently rewrite historical deadlines.

Recalculation requires explicit migration/legal rule.

---

# 207. Court Closure

Court closure may be triggered by:

```text
holiday
emergency
facility_failure
legal_order
administrative_action
```

Closures affect scheduling, not substantive case outcomes.

---

# 208. Emergency Continuity

During emergencies:

```text
REMOTE_HEARING
ELECTRONIC_FILING
EMERGENCY_DOCKET
DEADLINE_EXTENSION
```

may be activated by policy.

---

# 209. Emergency Judicial Authority

Emergency powers require:

```text
authority
scope
start
expiry
review
audit
```

---

# 210. Security Integration

AXSECURITY can provide:

```text
person verification
credential verification
facility security alert
threat reference
```

AXJUSTICE does not inherit security conclusions automatically.

---

# 211. Safety Integration

AXSAFETY can provide:

```text
building closure
disaster event
evacuation
transport disruption
```

---

# 212. Population Integration

AXPOPULATION provides authoritative identity references.

AXJUSTICE stores references rather than duplicating identity truth unnecessarily.

---

# 213. Legal Integration

AXLAW provides:

```text
statutes
regulations
legal rules
legal hierarchy
jurisdiction
procedural rules
```

---

# 214. Authority Integration

AXGOV provides:

```text
government authority
agency identity
office hierarchy
appointment references
```

---

# 215. Security Integration Rule

```text
AXSECURITY.IntelligenceReference
```

must remain:

```text
INTELLIGENCE_REFERENCE
```

until an authorized judicial process creates an appropriate evidence object.

---

# 216. Evidence Transformation

Transformation requires:

```text
source
authority
method
timestamp
result
custody
```

---

# 217. Legal Finding

A legal finding requires:

```text
court
judge/panel
case
issue
legal_basis
reasoning
decision
```

AI alone cannot produce a binding judicial finding.

---

# 218. Binding Decision

```text
BindingDecision
```

must have:

```text
authority
jurisdiction
effective_time
scope
status
```

---

# 219. Decision Scope

A decision may apply to:

```text
case
party
issue
class
jurisdiction
```

The scope must be explicit.

---

# 220. Precedent Scope

A precedent record contains:

```text
holding
facts
legal_issue
jurisdiction
court_level
status
```

---

# 221. Holding vs Dicta

Where the jurisdiction recognizes the distinction:

```text
Holding
Dicta
```

are separate types.

---

# 222. Legal Citation Graph

Graph nodes:

```text
Law
Case
Regulation
Order
Judgment
```

Edges:

```text
CITES
INTERPRETS
APPLIES
OVERRULES
DISTINGUISHES
AMENDS
SUPERSEDES
```

---

# 223. Citation Validation

The system verifies:

```text
authority exists
authority applies to jurisdiction
authority was valid at relevant time
citation target exists
```

---

# 224. Conflicting Authorities

The system reports:

```text
CONFLICTING_AUTHORITY
```

rather than silently selecting one.

---

# 225. Judicial Research Workspace

A research workspace can contain:

```text
Case
Authorities
Notes
AI Analysis
Drafts
Citations
Issues
```

Draft workspace is not authoritative court record until filed/adopted.

---

# 226. Notes

Notes are typed:

```text
PERSONAL_WORKING_NOTE
OFFICIAL_NOTE
COURT_RECORD_NOTE
```

Their legal status differs.

---

# 227. AI Working Notes

AI notes must be marked:

```text
AI_GENERATED
```

and must not silently enter the official record.

---

# 228. Document Comparison

System supports:

```text
redline
diff
semantic_diff
citation_diff
```

---

# 229. Version Comparison

Compare:

```text
pleading versions
judgment drafts
legal authorities
policy versions
```

---

# 230. Signature Freeze

Once a judgment is signed:

```text
editable = false
```

except through formal correction/amendment procedures.

---

# 231. Judicial Record Integrity

The system must preserve:

```text
who
what
when
authority
version
signature
```

for every authoritative mutation.

---

# 232. Backup

Court records support:

```text
encrypted backup
immutable backup
geographically redundant backup
offline recovery
```

---

# 233. Disaster Recovery

Recovery objectives:

```text
RPO
RTO
```

are explicitly configured by court.

---

# 234. Offline Court

Offline operation may support:

```text
document viewing
drafting
local filing queue
hearing notes
local signing
audit queue
```

---

# 235. Offline Restrictions

Offline mode must clearly identify:

```text
not_synced
not_current
pending_validation
```

---

# 236. Synchronization

```text
LOCAL_EVENTS
→ SIGNATURE_VERIFY
→ CONFLICT_CHECK
→ POLICY_CHECK
→ MERGE
→ ACKNOWLEDGE
```

---

# 237. Conflict Resolution

Conflicting authoritative judicial records require human/legal review.

No automatic overwrite.

---

# 238. Court Security

AXJUSTICE integrates with secure authentication:

```text
judge
clerk
counsel
party
witness
administrator
```

---

# 239. Role Separation

A clerk cannot automatically obtain judge capabilities.

A prosecutor cannot automatically obtain defense capabilities.

A system administrator cannot automatically obtain judicial authority.

---

# 240. Capability Separation

Example:

```text
ReadCase
FileDocument
ScheduleHearing
IssueNotice
IssueOrder
SignJudgment
ModifyPolicy
```

are distinct capabilities.

---

# 241. Four-Eyes

Sensitive administrative actions can require two authorized actors.

---

# 242. Break-Glass

Emergency administrative access:

```text
reason
authority
scope
time
audit
review
```

---

# 243. Secret Management

AXJUSTICE uses secure handles for:

```text
private keys
signing credentials
authentication secrets
encryption keys
```

---

# 244. Memory Model

No GC is required for hot-path court processing.

Resources should use deterministic ownership semantics.

---

# 245. Document Streaming

Large evidence/document objects use streaming APIs:

```axiom
stream<DocumentChunk>
```

to avoid loading entire files into memory.

---

# 246. Large Evidence

Large files support:

```text
chunk
hash
merkle_reference
stream
range_read
```

---

# 247. Parallel Processing

Independent tasks can run concurrently:

```text
document_ingestion
OCR
hashing
citation_extraction
classification
indexing
```

---

# 248. Transaction Boundary

For example:

```text
FILE_JUDGMENT
+
SIGN
+
AUDIT
+
PUBLISH
```

must be atomically represented from the perspective of authoritative state.

---

# 249. Event Sourcing Candidates

Suitable:

```text
case timeline
filings
orders
judgments
appeals
audit
assignments
```

---

# 250. Snapshotting

Large cases use:

```text
CaseSnapshot
+
EventTail
```

for fast loading.

---

# 251. Performance Targets

Reference targets:

```text
≥ 5M procedural events/sec per large cluster
≥ 100K concurrent active cases per regional deployment
≥ 1M document metadata operations/sec
≥ 100K citation queries/sec
```

Actual performance depends on deployment.

---

# 252. Latency Targets

Typical local operations:

```text
authorization lookup < 1 ms target
case-state lookup < 5 ms target
event append < 5 ms target
metadata query < 20 ms target
```

Large document/AI operations are excluded.

---

# 253. Storage

Recommended abstract storage capabilities:

```text
AppendLog
DocumentStore
TemporalStore
SearchIndex
GraphStore
ImmutableAuditStore
```

No specific vendor is required by the Axiom core.

---

# 254. Strong Types

Required identifiers:

```text
CourtId
JudgeId
CaseId
PartyId
ClaimId
ChargeId
IssueId
FilingId
MotionId
HearingId
EvidenceId
WitnessId
OrderId
JudgmentId
AppealId
SentenceId
EnforcementId
AuthorityId
LegalRuleId
```

---

# 255. Type Safety

For example:

```text
CaseId != EvidenceId
JudgmentId != OrderId
AppealId != CaseId
PartyId != JudgeId
```

---

# 256. Core Enums

```axiom
enum CaseStatus {
    Initiated
    Filed
    Active
    Hearing
    Decided
    Review
    Final
    Enforcement
    Closed
    Archived
}
```

---

# 257. Procedural Event

```axiom
struct ProceduralEvent {
    id
    case
    type
    actor
    authority
    timestamp
    payload
    provenance
}
```

---

# 258. Audit Event

```axiom
struct JusticeAuditEvent {
    actor
    action
    object
    case
    authority
    purpose
    timestamp
    result
}
```

---

# 259. Query

```axiom
struct JusticeQuery<T> {
    principal
    purpose
    authority
    selector
    requested_fields
}
```

---

# 260. Command

```axiom
struct JusticeCommand<T> {
    issuer
    authority
    case
    payload
    effective_time
    expiry
    idempotency_key
}
```

---

# 261. AI Result

```axiom
struct JusticeAIResult<T> {
    value
    model_id
    model_version
    inputs
    citations
    uncertainty
    limitations
    generated_at
    review_state
}
```

---

# 262. Policy DSL

Example:

```axiom
justice_policy filing {
    require valid_signature
    require court.has_jurisdiction
    require required_fields
    create filing_record
    notify parties
}
```

---

# 263. Hearing Policy

```axiom
justice_policy hearing {
    require case.active
    require judge.assigned
    require required_notice
    require valid_schedule
}
```

---

# 264. Judgment Policy

```axiom
justice_policy judgment {
    require authorized_judge
    require case.ready_for_decision
    require required_findings
    require signature
    create immutable_judgment
}
```

---

# 265. Appeal Policy

```axiom
justice_policy appeal {
    require appealable_decision
    require within_deadline
    require authorized_filer
}
```

---

# 266. Enforcement Policy

```axiom
justice_policy enforcement {
    require enforceable_order
    require effective
    require no_active_stay
}
```

---

# 267. Access Policy

```axiom
access_policy sealed_case {
    allow if
        principal.has_capability(ReadSealedCase)
        and purpose.authorized
        and case.policy.permits
}
```

---

# 268. Public Access Policy

```axiom
access_policy public_case {
    allow fields [
        case_id,
        court,
        filing_date,
        public_status,
        public_orders
    ]

    deny protected_identity
}
```

---

# 269. Retention Policy

```axiom
retention_policy case_record {
    retain according_to jurisdiction.case_retention

    if legal_hold {
        suspend deletion
    }
}
```

---

# 270. Authority Policy

```axiom
authority_policy judge {
    allow issue.order
    allow issue.judgment
    allow conduct.hearing

    deny modify.law
    deny modify.population
}
```

---

# 271. Security Boundary

AXSECURITY may verify identity.

AXJUSTICE determines the legal significance of that identity within a proceeding.

---

# 272. No Automatic Criminalization

A security alert imported from AXSECURITY becomes:

```text
SecurityReference
```

not:

```text
Charge
```

without an explicit legal process.

---

# 273. No Automatic Guilt

The system must never transform:

```text
arrest
charge
watchlist match
risk score
intelligence report
```

into:

```text
conviction
```

without adjudication.

---

# 274. AI Guilt Firewall

Forbidden implicit flow:

```text
AI_SCORE → GUILTY
```

Required:

```text
AI_ANALYSIS
→ LEGAL_PROCESS
→ AUTHORIZED_ADJUDICATION
→ VERDICT
```

---

# 275. AI Sentencing Boundary

AI may assist with legal research or draft analysis where authorized.

The authoritative sentence must remain an explicit judicial decision.

---

# 276. Judicial Decision Boundary

The final legal decision object must identify:

```text
decision_maker
authority
legal_basis
case
findings
effective_time
```

---

# 277. Decision Publication

Publication state:

```text
PRIVATE
SEALED
RESTRICTED
PUBLIC
```

---

# 278. Notification

Parties may receive:

```text
filing_notice
hearing_notice
order_notice
judgment_notice
appeal_notice
```

---

# 279. Notification Delivery

Methods:

```text
PORTAL
EMAIL
SMS
PHYSICAL
AUTHORIZED_AGENT
OTHER
```

Actual delivery semantics are jurisdiction-specific.

---

# 280. Notification Proof

```axiom
struct NotificationProof {
    recipient
    method
    sent_at
    delivered_at
    acknowledged_at
}
```

---

# 281. Legal Deadline Trigger

A deadline may begin from:

```text
filing
service
receipt
judgment
order
statutory_event
```

The trigger type is explicit.

---

# 282. Calendar

Calendars support:

```text
court_holidays
jurisdiction_holidays
emergency_closures
working_days
```

---

# 283. Deadline Extension

```axiom
deadline.extend(
    authority,
    new_due_date,
    reason
)
```

creates an audit event.

---

# 284. Deadline Waiver

Waiver is distinct from extension.

```text
Waiver != Extension
```

---

# 285. Default

Failure to meet a deadline may produce:

```text
DEFAULT_STATUS
```

but its legal consequence is governed by applicable rules.

---

# 286. Procedural Sanction

Sanctions are explicit legal actions.

The runtime does not infer them merely from a missed deadline.

---

# 287. Court Fees and Enforcement

Financial consequences reference AXFISCAL where applicable.

AXJUSTICE owns the judicial basis.

---

# 288. Compensation

Judgment may contain:

```text
damages
costs
fees
restitution
```

Actual financial settlement may be executed by fiscal/enforcement systems.

---

# 289. Property Orders

Property-related orders contain:

```text
property_reference
authority
scope
conditions
```

---

# 290. Child/Family Cases

Sensitive family proceedings use stricter:

```text
privacy
identity
access
publication
```

policies.

---

# 291. Juvenile Proceedings

Juvenile case types are separate where required:

```text
JuvenileCase
```

with specialized privacy and procedure.

---

# 292. Mental/Medical Evidence Boundary

Medical or health records are treated as protected evidence references.

AXJUSTICE does not infer health conditions from unrelated data.

---

# 293. Expert Data

Expert evidence must preserve:

```text
source
method
qualifications
assumptions
limitations
```

---

# 294. Forensic Evidence

Forensic result:

```text
ForensicReport
```

is separate from:

```text
CourtFinding
```

---

# 295. Evidence Reliability

The system may record multiple assessments:

```text
technical_integrity
chain_integrity
source_reliability
procedural_admissibility
```

They are not interchangeable.

---

# 296. Contradictory Evidence

Cases may explicitly contain:

```text
supporting_evidence[]
contradicting_evidence[]
unresolved_evidence[]
```

---

# 297. Missing Evidence

Missing evidence is:

```text
EvidenceGap
```

not negative proof unless applicable law explicitly says so.

---

# 298. Evidence Destruction

If evidence is destroyed:

```text
DestructionRecord
```

must preserve:

```text
authority
reason
time
custodian
integrity/reference
```

---

# 299. Case Integrity

A case's procedural state must be reconstructable from:

```text
authoritative events
documents
orders
judgments
audit
```

---

# 300. Final Semantic Contract

AXJUSTICE is built on:

```text
CLAIMS ARE ASSERTIONS.
EVIDENCE IS A RECORDED INPUT.
FACT FINDINGS ARE JUDICIAL DETERMINATIONS.
LEGAL RULES COME FROM AUTHORITY.
ARGUMENTS ARE NOT FINDINGS.
INTELLIGENCE IS NOT AUTOMATICALLY EVIDENCE.
AI ASSISTS; IT DOES NOT BECOME THE COURT.
ORDERS ARE EXPLICIT AUTHORITY.
JUDGMENTS ARE EXPLICIT DECISIONS.
APPEALS ARE DISTINCT PROCEDURES.
ENFORCEMENT IS DISTINCT FROM ADJUDICATION.
AUDIT PRESERVES PROCEDURAL TRUTH.
```

The central invariant is:

```text
ALLEGATION
≠
EVIDENCE
≠
FACT FINDING
≠
LEGAL CONCLUSION
≠
JUDGMENT
≠
ENFORCEMENT
```

---

# 301. Mandatory Invariants

Minimum:

```text
J001 CaseId != PersonId
J002 Claim != Finding
J003 Charge != Conviction
J004 Arrest != Guilt
J005 Detention != Guilt
J006 Prosecution != Conviction
J007 Intelligence != Evidence
J008 Evidence != Fact
J009 Testimony != EstablishedFact
J010 Argument != Finding
J011 LegalResearch != LegalDecision
J012 AIRecommendation != Judgment
J013 AIProbability != LegalProof
J014 SearchScore != LegalImportance
J015 Similarity != Precedent
J016 Filing != Acceptance
J017 Notice != Service
J018 Service != Decision
J019 Order != Judgment
J020 Judgment != Enforcement
J021 Appeal != Reversal
J022 Appeal != AutomaticStay
J023 Settlement != Judgment
J024 Mediation != Adjudication
J025 Admissibility != Truth
J026 EvidenceWeight != Truth
J027 CaseClosure != Exoneration
J028 Dismissal != UniversalInnocence
J029 Verdict != Sentence
J030 Sentence != Enforcement
J031 Finality is explicit
J032 Historical law is versioned
J033 Historical records are immutable
J034 Corrections preserve originals
J035 Sealed data requires capability
J036 Public access respects sealing
J037 AI output has provenance
J038 AI output has model version
J039 AI cannot invent judicial authority
J040 AI cannot silently issue judgment
J041 AI cannot silently issue sentence
J042 AI cannot silently issue conviction
J043 Judicial decision has identified authority
J044 Judicial decision has legal basis
J045 Judicial decision is auditable
J046 Deadline computation uses explicit rule
J047 Deadline extension is auditable
J048 Deadline waiver is distinct
J049 Appeal preserves originating case
J050 Remand preserves lineage
J051 Enforcement requires enforceable authority
J052 Stay affects enforcement explicitly
J053 Security referral != criminal finding
J054 Watchlist match != charge
J055 Risk score != guilt
J056 Evidence conversion has provenance
J057 Evidence custody is auditable
J058 Digital evidence integrity is explicit
J059 AI citation must be verifiable
J060 Unverified citation cannot become authoritative citation
J061 Court assignment is auditable
J062 Recusal is distinct from misconduct
J063 Judge capability != administrator capability
J064 Clerk capability != judge capability
J065 Prosecutor capability != defense capability
J066 Query != Command
J067 Simulation != Production
J068 Offline state != synchronized state
J069 Stale data is marked
J070 Conflicting records are not silently overwritten
J071 Legal authority is time-scoped
J072 Jurisdiction is explicit
J073 Case scope is explicit
J074 Judgment scope is explicit
J075 Enforcement scope is explicit
J076 Sensitive identity is protected
J077 Protected witness identity is scoped
J078 Public record != complete internal record
J079 Draft != authoritative document
J080 Signed judgment cannot be silently edited
```

---

# 302. Native Runtime Profiles

```text
AXJUSTICE_CORE
AXJUSTICE_COURT
AXJUSTICE_CASE
AXJUSTICE_EFILING
AXJUSTICE_RESEARCH
AXJUSTICE_AI
AXJUSTICE_ARCHIVE
AXJUSTICE_PUBLIC
AXJUSTICE_SIM
```

---

# 303. Implementation Order

```text
1. Strong judicial identifiers
2. Court and jurisdiction model
3. Case state machine
4. Party model
5. Filing system
6. Pleadings
7. Hearing/calendar
8. Deadline engine
9. Evidence/provenance
10. Chain of custody
11. Orders
12. Judgments
13. Appeals
14. Enforcement references
15. Court records
16. Access/classification
17. Audit
18. Legal authority integration
19. Security/intelligence boundary
20. AI research
21. AI drafting
22. Citation verification
23. Federation
24. Offline synchronization
25. Replay
26. Simulation
27. Static security analysis
28. Performance optimization
29. Conformance suite
30. Native deployment
```

---

# 304. Testing Requirements

Target:

```text
≥ 20,000 automated tests
```

including:

```text
unit
integration
property
fuzz
workflow
legal-state
authorization
privacy
audit
deadline
calendar
evidence
appeal
enforcement
AI provenance
citation verification
offline
replay
concurrency
disaster recovery
```

---

# 305. Formal Verification Targets

Formal verification should target:

```text
authority transitions
case-state transitions
judgment immutability
appeal lineage
evidence provenance
access control
classification flow
deadline correctness
enforcement preconditions
audit completeness
```

---

# 306. Acceptance Criteria

BOOTSTRAP-702 is complete when implementation demonstrates:

1. Native court model.
2. Explicit jurisdiction.
3. Typed parties.
4. Typed claims and charges.
5. Procedural case lifecycle.
6. Electronic filing.
7. Hearing/calendar engine.
8. Deadline engine.
9. Evidence/provenance model.
10. Chain-of-custody model.
11. Orders.
12. Judgments.
13. Verdicts.
14. Sentences.
15. Appeals.
16. Remands.
17. Finality.
18. Enforcement references.
19. Public/sealed records.
20. Legal authority versioning.
21. Historical-law support.
22. AI legal research.
23. AI citation verification.
24. AI draft separation.
25. Human adoption of AI drafts.
26. AXSECURITY integration boundary.
27. AXLAW integration.
28. AXSAFETY emergency integration.
29. Immutable procedural history.
30. Deterministic replay.
31. Offline operation.
32. Strong capability model.
33. Privacy controls.
34. Audit integrity.
35. ≥20,000 automated tests.
36. Native compilation for supported Axiom targets.
37. No mandatory GC in hot paths.
38. No mandatory third-party runtime dependency in the Axiom core.

---

# 307. Architecture Summary

```text
                         AXJUSTICE
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
        COURTS             CASES             EVIDENCE
          │                  │                  │
       Judges             Claims             Exhibits
       Hearings           Charges            Witnesses
       Orders             Motions            Experts
       Judgments          Appeals            Custody
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                      LEGAL AUTHORITY
                          AXLAW
                             │
                 ┌───────────┼───────────┐
                 │           │           │
             AXSECURITY   AXPOPULATION  AXGOV
                 │           │           │
              refs only    identity     authority
                             │
                        AUDIT / PROVENANCE
                             │
                       AXIOM NATIVE RUNTIME
```

---

# 308. Final Principle

```text
THE COURT RECORD MUST KNOW
WHAT WAS ALLEGED,
WHAT WAS SUBMITTED,
WHAT WAS VERIFIED,
WHAT WAS CONTESTED,
WHAT WAS FOUND,
WHAT LAW WAS APPLIED,
WHO DECIDED,
WHAT WAS ORDERED,
WHETHER IT BECAME FINAL,
AND HOW IT WAS ENFORCED.
```

And:

```text
AI MAY HELP FIND.
AI MAY HELP ORGANIZE.
AI MAY HELP ANALYZE.
AI MAY HELP DRAFT.

BUT:

AUTHORITY MUST BE EXPLICIT.
JUDGMENT MUST BE EXPLICIT.
LEGAL EFFECT MUST BE EXPLICIT.
PROCEDURAL HISTORY MUST BE IMMUTABLE.
```

# END OF BOOTSTRAP-702
:::

**BOOTSTRAP-702 hoàn tất.** Task kiến trúc kế tiếp trong chuỗi là:

**BOOTSTRAP-703 — AXEDUCATION: Native AI Civilization-Scale Government Education, Schools, Universities, Credentials, Learning Records, Research Administration & Lifelong Learning Runtime 5.0**

Namespace dự kiến: `AXEDUCATION`.