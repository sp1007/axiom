Tiếp tục. Dưới đây là **BOOTSTRAP-701**, nối trực tiếp sau AXSAFETY-700 và giữ cùng nguyên tắc: đặc tả phải đủ cụ thể để agent/compiler team có thể triển khai, không chỉ là mô tả ý tưởng.

:::writing{variant="document" id="58321" title="BOOTSTRAP-701 — AXSECURITY: National Security, Strategic Security, Border, Immigration, Customs Security & Threat Intelligence Runtime 5.0"}
# BOOTSTRAP-701
## AXSECURITY
### Native AI Civilization-Scale Government National Security, Strategic Security, Border Management, Immigration, Customs Security, Critical Threat Intelligence & Secure State Coordination Runtime 5.0

**Status:** Architecture Specification  
**Layer:** Government / Security / Intelligence Runtime  
**Depends on:** Axiom Core, Semantic Core, Type & Trait Model, Memory Model, Concurrency Model, Compiler IR, AXLAW, AXGOV, AXPOPULATION, AXGEO, AXSAFETY, AXCRYPT/secure substrate  
**Primary namespace:** `AXSECURITY`  
**Runtime profile:** `government.security`  
**Primary design objective:** deterministic, auditable, privacy-aware, authority-bounded, AI-assisted national-security and border-security infrastructure without embedding policy decisions into the programming runtime.

---

# 1. Purpose

`AXSECURITY` defines the native Axiom runtime and domain model for:

- national-security coordination;
- strategic-security information management;
- threat intelligence;
- security assessments;
- border management;
- immigration management;
- visa and entry authorization;
- traveler processing;
- identity and credential verification;
- customs-security coordination;
- watchlist governance;
- security alerts;
- cross-agency intelligence exchange;
- security incidents;
- secure inter-agency coordination;
- intelligence provenance;
- evidence/record chain-of-custody;
- classified and compartmented information;
- security-clearance and access-control integration;
- cross-border information sharing;
- security analytics;
- AI-assisted intelligence analysis;
- security exercises and simulations.

The runtime is explicitly designed so that **information processing, risk analysis, intelligence assessment and government authority remain distinct concepts**.

---

# 2. Core Principle

AXSECURITY follows:

```text
COLLECT
→ NORMALIZE
→ VERIFY
→ CORRELATE
→ ASSESS
→ CLASSIFY
→ AUTHORIZE
→ DISSEMINATE
→ ACT
→ RECORD
→ REVIEW
→ RETAIN / DELETE
```

AI may assist:

```text
OBSERVE
→ EXTRACT
→ CORRELATE
→ DETECT
→ SUMMARIZE
→ TRANSLATE
→ ASSESS
→ RECOMMEND
→ SIMULATE
```

AI does not automatically become:

```text
LAW
AUTHORITY
JUDGMENT
CONVICTION
DETENTION ORDER
DEPORTATION ORDER
CITIZENSHIP DECISION
TRAVEL BAN
ENTRY DENIAL
SEARCH AUTHORIZATION
SEIZURE AUTHORIZATION
```

---

# 3. Architectural Position

AXSECURITY is not itself:

- a criminal court;
- a prosecutor;
- a police-force command system;
- a military weapons-control system;
- a political decision engine;
- a citizenship authority;
- a taxation system;
- a general customs-finance system.

It provides secure coordination and information infrastructure for authorized government systems.

---

# 4. System Boundary

```text
AXLAW
  ↓ legal authority
AXGOV
  ↓ governmental authority
AXPOPULATION
  ↓ person identity
AXGEO
  ↓ geographic truth
AXSECURITY
  ↓ security coordination
AXSAFETY
  ↓ emergency/resilience coordination
AXTRANSPORT
  ↓ movement infrastructure
AXCOMMERCE / AXTRADE
  ↓ commercial declarations
AXFISCAL
  ↓ fiscal consequences
AXJUSTICE
  ↓ judicial proceedings
AXHEALTH
  ↓ health-domain records where legally authorized
AXCRYPT
  ↓ cryptographic/security substrate
```

AXSECURITY must never silently duplicate authoritative records owned by these systems.

---

# 5. Semantic Firewall

The following distinctions are mandatory compiler/runtime concepts.

```text
Identity != Threat
Identity != Suspicion
Identity != Risk

Risk != Threat
RiskScore != ThreatConfirmation

Watchlist != Guilt
WatchlistMatch != Guilt
WatchlistMatch != Conviction

Alert != ThreatConfirmation
Warning != ThreatConfirmation

Intelligence != Evidence
IntelligenceLead != Evidence
IntelligenceAssessment != JudicialFinding

Source != Fact
SourceReliability != Truth

Confidence != Truth
Probability != Fact

Anomaly != Fraud
Anomaly != Crime

Suspicion != Guilt
Suspicion != Conviction

BorderScreening != CriminalInvestigation

BorderReferral != ViolationFinding

CustomsInspection != ViolationFinding
Inspection != Seizure
Seizure != Forfeiture

Visa != Citizenship
Visa != Residence
Residence != Citizenship

ImmigrationStatus != Citizenship

EntryAuthorization != Citizenship
EntryAuthorization != CriminalFinding

BiometricMatch != Criminality

TravelRestriction != CriminalConviction

SecurityRecommendation != GovernmentOrder

AIRecommendation != LegalDecision

Detention != Guilt

Denial != Conviction

IntelligenceSharing != AutomaticAuthoritySharing

SecurityClearance != GeneralLegalAuthority

Classification != Truth

Classification != Reliability

Simulation != RealIncident

ExerciseResult != RealThreat

Pattern != Intent
Correlation != Causation
Association != Guilt

EntityResolution != IdentityProof

CrossBorderMatch != IdentityConfirmation

Prediction != Observation
Forecast != Event
```

These distinctions must be represented in the type system where practical.

---

# 6. Security Domain Object Model

Core entities:

```text
Person
Organization
Credential
IdentityRecord
TravelDocument
Visa
ResidencePermit
CitizenshipRecord
EntryAuthorization
ExitRecord

BorderPoint
Checkpoint
Port
Airport
Seaport
BorderZone

Traveler
Journey
MovementRecord

Watchlist
WatchlistEntry
WatchlistMatch

Threat
ThreatIndicator
ThreatActor
ThreatAssessment
ThreatRelationship

IntelligenceSource
IntelligenceReport
IntelligenceLead
IntelligenceAssessment
IntelligenceProduct

Observation
Signal
Event
SecurityAlert
SecurityIncident

Case
Referral
Inspection
Examination
SeizureRecord

SecurityClearance
Compartment
AccessDecision
DisclosureAuthorization

EvidenceReference
ProvenanceRecord
ChainOfCustodyRecord

SecurityOrder
AuthorityReference
Delegation

CrossBorderRequest
InformationSharingAgreement

AuditRecord
RetentionPolicy
DeletionRecord

AIAnalysis
AIRecommendation
HumanDecision
DecisionRecord
```

---

# 7. Identity Model

Identity must be treated as a layered construct.

```text
IdentityClaim
IdentityEvidence
IdentityRecord
IdentityVerification
IdentityResolution
IdentityConfidence
```

Example:

```axiom
identity.verify(
    claim: person_claim,
    evidence: documents,
    policy: identity_policy
)
```

The result:

```text
IdentityVerificationResult
```

must not automatically produce:

```text
Threat
Crime
Suspicion
Guilt
```

---

# 8. Identity Confidence

Use explicit states:

```text
UNKNOWN
CLAIMED
PARTIALLY_VERIFIED
VERIFIED
STRONGLY_VERIFIED
CONFLICTED
REJECTED
EXPIRED
REVOKED
```

A confidence value must never be interpreted as legal certainty.

---

# 9. Credential Model

Credentials include:

```text
Passport
TravelDocument
Visa
ResidencePermit
BorderCredential
GovernmentCredential
ProfessionalCredential
SecurityCredential
DigitalCredential
```

Each credential has:

```text
issuer
subject
type
issued_at
expires_at
status
serial/reference
cryptographic_binding
revocation_state
provenance
```

---

# 10. Credential State Machine

```text
DRAFT
→ ISSUED
→ ACTIVE
→ SUSPENDED
→ REVOKED
→ EXPIRED
```

No transition may occur without an authorized actor or authorized automated policy.

---

# 11. Citizenship Boundary

Citizenship is authoritative in the population/citizenship domain.

AXSECURITY may consume:

```text
CitizenshipVerification
```

but must not infer citizenship from:

- nationality guess;
- language;
- name;
- ethnicity;
- location;
- biometric characteristics;
- travel history;
- watchlist status.

---

# 12. Immigration Status

Immigration status is modeled independently.

```text
NO_STATUS
VISITOR
TRANSIT
STUDENT
WORK
TEMPORARY_RESIDENT
PERMANENT_RESIDENT
ASYLUM_PROCESS
PROTECTED_STATUS
OTHER_AUTHORIZED_STATUS
EXPIRED
REVOKED
```

Actual legal statuses are jurisdiction-defined by AXLAW.

---

# 13. Visa

A visa is represented as:

```axiom
struct Visa {
    issuer
    subject
    visa_type
    valid_from
    valid_until
    entries
    conditions
    status
}
```

A visa does not automatically guarantee entry.

---

# 14. Entry Authorization

Entry processing produces an explicit decision object:

```text
EntryAuthorization
```

Possible states:

```text
PENDING
AUTHORIZED
AUTHORIZED_WITH_CONDITIONS
REFERRED
DENIED
CANCELLED
EXPIRED
```

Authorization must reference its legal basis.

---

# 15. Border Processing Pipeline

Canonical pipeline:

```text
ARRIVAL
→ DOCUMENT_CAPTURE
→ IDENTITY_VERIFICATION
→ CREDENTIAL_VALIDATION
→ IMMIGRATION_STATUS_CHECK
→ SECURITY_SCREENING
→ CUSTOMS_SECURITY_SCREENING
→ REFERRAL_IF_REQUIRED
→ AUTHORIZED_DECISION
→ ENTRY_RECORD
```

Each stage is independently auditable.

---

# 16. Primary vs Secondary Screening

Primary screening is a normal bounded verification process.

Secondary screening is an explicit referral state.

```axiom
screening.primary(traveler)

if result.requires_referral {
    screening.secondary(referral)
}
```

The system must not encode “secondary screening = guilt”.

---

# 17. Referral

A referral contains:

```text
referral_id
origin
reason_code
authority
scope
created_at
assigned_unit
status
review_deadline
```

Reason codes must be structured rather than arbitrary natural-language labels whenever possible.

---

# 18. Referral Lifecycle

```text
CREATED
→ ACCEPTED
→ IN_REVIEW
→ RESOLVED
→ CLOSED
```

Optional:

```text
ESCALATED
REASSIGNED
SUSPENDED
EXPIRED
```

---

# 19. Border Decision

A decision must contain:

```text
decision_id
subject
decision_type
legal_basis
authority
inputs
decision_time
decision_maker
conditions
expiry
appeal/review_reference
audit_reference
```

AI-generated content cannot populate `decision_maker` unless an actual authorized actor made the decision.

---

# 20. Border Movement Records

Movement events:

```text
ENTRY
EXIT
TRANSIT
TRANSFER
REFERRAL
CANCELLED_MOVEMENT
```

Each event requires:

```text
subject
location
time
source
confidence
provenance
```

---

# 21. Movement Truth

Movement data must distinguish:

```text
PLANNED_MOVEMENT
OBSERVED_MOVEMENT
RECORDED_MOVEMENT
AUTHORIZED_MOVEMENT
COMPLETED_MOVEMENT
```

Never collapse these into one boolean.

---

# 22. Watchlist Model

A watchlist is a governed collection of records requiring defined handling.

```axiom
watchlist {
    purpose
    authority
    jurisdiction
    entries
    inclusion_policy
    review_policy
    expiry_policy
}
```

Every entry must have:

```text
legal/policy basis
creator
created_at
review_at
status
scope
handling_instruction
source references
```

---

# 23. Watchlist Entry

An entry may refer to:

```text
Person
Organization
Vehicle
Vessel
Aircraft
Document
Account
Identifier
Object
```

A watchlist entry must not itself be represented as a criminal conviction.

---

# 24. Watchlist Lifecycle

```text
PROPOSED
→ REVIEWED
→ ACTIVE
→ SUSPENDED
→ EXPIRED
→ REMOVED
```

Emergency additions require explicit emergency authority and accelerated review.

---

# 25. Watchlist Matching

Matching produces:

```text
WatchlistMatch
```

not:

```text
ThreatConfirmation
```

Match output:

```text
candidate_entry
match_method
match_strength
supporting_attributes
conflicts
verification_required
```

---

# 26. False Match Handling

Every matching subsystem must support:

```text
FALSE_POSITIVE
CONFIRMED_MATCH
UNRESOLVED
INSUFFICIENT_DATA
IDENTITY_CONFLICT
```

A match must not be converted into an adverse decision without required verification.

---

# 27. Biometric Boundary

Biometric processing may provide:

```text
identity comparison
identity verification
duplicate detection
credential verification
```

It must not implicitly infer:

```text
criminality
intent
dangerousness
political belief
guilt
future behavior
```

---

# 28. Threat Model

A threat is an explicit security-domain object.

```axiom
struct Threat {
    id
    category
    description
    indicators
    affected_assets
    affected_regions
    confidence
    assessment
    provenance
    lifecycle
}
```

---

# 29. Threat Categories

Categories are extensible.

Examples:

```text
TERRORISM
ESPIONAGE
CYBER
SABOTAGE
ORGANIZED_CRIME
TRANSNATIONAL_CRIME
CRITICAL_INFRASTRUCTURE
PROLIFERATION
HOSTILE_INTERFERENCE
ILLICIT_TRAFFICKING
IDENTITY_FRAUD
SECURITY_BREACH
OTHER
```

These are categories, not conclusions about a person.

---

# 30. Threat Indicator

Indicators can include:

```text
identifier
artifact
technical signal
behavioral observation
transaction pattern
communication metadata
document anomaly
travel anomaly
infrastructure event
external intelligence
```

An indicator is evidence for analysis, not automatically proof of a threat.

---

# 31. Indicator Lifecycle

```text
OBSERVED
→ NORMALIZED
→ VALIDATED
→ CORRELATED
→ ASSESSED
→ EXPIRED
```

---

# 32. Intelligence Source

```axiom
struct IntelligenceSource {
    id
    source_type
    origin
    reliability
    access_constraints
    collection_period
    provenance
}
```

`reliability` describes the source, not the truth of every claim produced by the source.

---

# 33. Intelligence Report

```text
REPORT
├── claims
├── observations
├── sources
├── timestamps
├── confidence
├── provenance
├── classification
├── dissemination_policy
└── analyst_assessment
```

---

# 34. Intelligence Lifecycle

```text
COLLECTION
→ INGESTION
→ NORMALIZATION
→ VALIDATION
→ CORRELATION
→ ANALYSIS
→ ASSESSMENT
→ PRODUCTION
→ DISSEMINATION
→ REVIEW
→ RETENTION
→ DELETION
```

---

# 35. Intelligence Assessment

An assessment must explicitly distinguish:

```text
OBSERVED_FACT
SOURCE_CLAIM
ANALYST_INFERENCE
MODEL_INFERENCE
UNCERTAINTY
ALTERNATIVE_HYPOTHESIS
CONFIDENCE
```

This prevents AI-generated inference from silently becoming fact.

---

# 36. Structured Confidence

Use:

```axiom
assessment.confidence {
    value
    basis
    evidence_count
    contradictory_evidence
    source_quality
    model_uncertainty
}
```

A high confidence score is not equivalent to legal truth.

---

# 37. Alternative Hypotheses

Security assessments should support:

```text
primary_hypothesis
alternative_hypotheses[]
disconfirming_evidence[]
unknowns[]
```

This prevents the runtime from encoding a single interpretation as reality.

---

# 38. Intelligence Graph

AXSECURITY provides:

```text
Entity
Relationship
Observation
Claim
Indicator
Assessment
Source
Event
```

Graph edges are typed:

```text
OWNS
CONTROLS
ASSOCIATED_WITH
TRAVELED_WITH
COMMUNICATED_WITH
SHARES_IDENTIFIER
LOCATED_AT
REFERENCES
OBSERVED_AT
DERIVED_FROM
CONTRADICTS
SUPPORTS
```

Relationship existence must not imply criminality.

---

# 39. Provenance Graph

Every intelligence object may expose:

```text
source
→ observation
→ transformation
→ correlation
→ assessment
→ decision
```

Example:

```text
source:S1
  ↓
observation:O7
  ↓
normalized:N7
  ↓
correlation:C12
  ↓
assessment:A4
  ↓
human_decision:D9
```

---

# 40. Claim-Level Provenance

Claims must be independently traceable.

```axiom
claim.provenance()
```

returns:

```text
sources[]
transformations[]
analysts[]
models[]
timestamps[]
```

---

# 41. Classification

Security information may carry labels such as:

```text
PUBLIC
INTERNAL
RESTRICTED
CONFIDENTIAL
SECRET
TOP_SECRET
```

Actual labels are jurisdiction-defined.

Classification is metadata governing handling.

It does not indicate factual accuracy.

---

# 42. Compartments

Sensitive information can be compartmented:

```text
COMPARTMENT_A
COMPARTMENT_B
COMPARTMENT_C
```

Access requires:

```text
clearance
need_to_know
purpose
authority
context
```

---

# 43. Need-to-Know

Possessing clearance does not automatically grant access.

```axiom
access.evaluate(
    principal,
    resource,
    purpose,
    compartment
)
```

must evaluate:

```text
clearance
AND
need_to_know
AND
purpose
AND
policy
AND
authority
```

---

# 44. Access Decision

Possible states:

```text
ALLOW
ALLOW_REDACTED
DENY
ESCALATE
REQUIRES_AUTHORIZATION
```

Every decision is auditable.

---

# 45. Data Minimization

Each collection declaration should specify:

```text
purpose
required_fields
optional_fields
retention
legal_basis
authorized_consumers
```

Unnecessary fields should not be collected merely because they are technically available.

---

# 46. Purpose Limitation

A dataset collected for one purpose cannot automatically become authorized for every other purpose.

```axiom
purpose.check(
    dataset,
    requested_use
)
```

returns:

```text
ALLOWED
CONDITIONALLY_ALLOWED
PROHIBITED
REQUIRES_AUTHORIZATION
```

---

# 47. Retention

Every sensitive dataset requires a retention policy:

```text
retain_for
review_after
archive_after
delete_after
legal_hold
exception_authority
```

---

# 48. Deletion

Deletion must produce an auditable record:

```text
DeletionRecord {
    dataset
    subject/scope
    authority
    policy
    timestamp
    executor
}
```

---

# 49. Legal Hold

Legal hold suspends normal deletion where legally authorized.

```text
RETENTION_POLICY
        ↓
LEGAL_HOLD
        ↓
DELETE_SUSPENDED
```

The hold itself must expire or be explicitly reviewed.

---

# 50. Chain of Custody

Evidence-related references use:

```text
CustodyRecord
```

with:

```text
object
holder
transfer_time
transfer_reason
integrity_reference
authorization
location/context
```

---

# 51. Intelligence vs Evidence

AXSECURITY must preserve:

```text
INTELLIGENCE
```

and:

```text
EVIDENCE
```

as separate types.

An intelligence report may point toward evidence but does not automatically become evidence.

---

# 52. Security Incident

```axiom
struct SecurityIncident {
    id
    category
    detected_at
    affected_assets
    severity
    status
    commander
    actions
    outcome
}
```

---

# 53. Incident Lifecycle

```text
DETECTED
→ TRIAGED
→ CONFIRMED
→ CONTAINED
→ REMEDIATED
→ RECOVERED
→ CLOSED
→ REVIEWED
```

`DETECTED` does not mean `CONFIRMED`.

---

# 54. Security Alert

```text
SecurityAlert {
    severity
    scope
    indicators
    confidence
    expiration
    authority
}
```

Alerts must have explicit expiry.

---

# 55. Alert Expiration

No security alert should remain indefinitely active without review.

```text
ACTIVE
→ REVIEW_REQUIRED
→ RENEWED
or
→ EXPIRED
```

---

# 56. Critical Infrastructure Integration

AXSECURITY may consume AXSAFETY events:

```text
critical_infrastructure_threat
cyber_incident
physical_security_event
supply_chain_alert
facility_risk
```

AXSAFETY remains authoritative for disaster/emergency response.

---

# 57. Cybersecurity Boundary

AXSECURITY may coordinate:

```text
cyber threat intelligence
incident classification
cross-agency alerting
threat indicators
critical infrastructure coordination
```

Detailed endpoint security implementation belongs to dedicated cyber/security infrastructure.

---

# 58. Customs Security

AXSECURITY coordinates security aspects of:

```text
cargo screening
traveler/cargo risk referral
document anomaly detection
restricted-item alerts
security inspection
cross-border threat indicators
```

Financial customs/tax calculations remain external authorities.

---

# 59. Customs Declaration

A declaration is distinct from an inspection.

```text
Declaration
→ Validation
→ Risk Assessment
→ Inspection Referral
→ Inspection
→ Release / Hold / Further Process
```

---

# 60. Customs Security Risk

A customs risk score is:

```text
RiskAssessment
```

not:

```text
ViolationFinding
```

and not:

```text
CriminalFinding
```

---

# 61. Inspection

Inspection states:

```text
REQUESTED
AUTHORIZED
IN_PROGRESS
COMPLETED
CANCELLED
```

Results:

```text
NO_ISSUE_FOUND
IRREGULARITY_FOUND
REFERRAL
SEIZURE_REQUESTED
OTHER_AUTHORIZED_OUTCOME
```

---

# 62. Seizure Boundary

A seizure event must reference:

```text
authority
legal basis
object
scope
time
officer/system
chain of custody
review mechanism
```

Seizure does not imply forfeiture.

---

# 63. Cross-Border Data Exchange

Every cross-border exchange requires:

```text
requesting_authority
receiving_authority
legal_basis
agreement_reference
purpose
dataset_scope
retention
security_classification
audit_policy
```

---

# 64. Information-Sharing Agreement

```axiom
sharing.agreement {
    parties
    jurisdiction
    purpose
    allowed_data
    prohibited_data
    retention
    security_requirements
    onward_transfer_policy
    termination
}
```

---

# 65. Cross-Border Request

```text
CREATED
→ VALIDATED
→ AUTHORIZED
→ TRANSMITTED
→ RECEIVED
→ PROCESSED
→ RESPONSE
→ CLOSED
```

---

# 66. Cross-Border Data Minimization

Only the minimum authorized dataset should be exchanged.

The runtime should support field-level filtering:

```axiom
request.select(
    fields = [...]
)
```

---

# 67. Secure Government Messaging

AXSECURITY exposes abstract messaging:

```axiom
security.send(
    recipient,
    message,
    classification,
    authorization
)
```

Transport and cryptography are delegated to secure substrate implementations.

---

# 68. Cryptographic Boundary

AXSECURITY must not invent cryptographic primitives.

It consumes:

```text
sign
verify
encrypt
decrypt
hash
key_reference
credential_verify
signature_verify
```

from the cryptographic/security layer.

---

# 69. Key Management

AXSECURITY stores key references, not raw secrets wherever possible.

```text
KeyReference
KeyVersion
KeyPolicy
KeyStatus
```

---

# 70. Government Authority

Every security action that changes legal state must carry:

```text
authority
legal_basis
jurisdiction
scope
issuer
issued_at
expires_at
```

---

# 71. Delegation

Authority may be delegated:

```axiom
delegate(
    authority,
    principal,
    scope,
    start,
    expiry
)
```

Delegation cannot silently exceed the authority of the delegator.

---

# 72. Delegation Chain

```text
ROOT_AUTHORITY
→ DELEGATION_1
→ DELEGATION_2
→ ACTION
```

The runtime must be able to reconstruct the complete chain.

---

# 73. Emergency Authority

Emergency authority integrates with AXSAFETY.

Emergency privileges must have:

```text
trigger
authority
scope
start
expiry
review
audit
```

---

# 74. Break-Glass

Break-glass access is permitted only where policy allows it.

Required:

```text
reason
principal
resource
time
authority
automatic audit
post-event review
```

Break-glass must not erase normal access logs.

---

# 75. AI Security Analysis

AI services may provide:

```text
entity extraction
entity resolution assistance
document extraction
translation
summarization
correlation
anomaly detection
pattern discovery
risk estimation
timeline generation
hypothesis generation
scenario simulation
```

---

# 76. AI Output Classification

Every AI output is explicitly typed:

```text
AI_OBSERVATION
AI_EXTRACTION
AI_CORRELATION
AI_PREDICTION
AI_ASSESSMENT
AI_RECOMMENDATION
AI_SUMMARY
AI_TRANSLATION
```

---

# 77. AI Provenance

Every AI result includes:

```text
model_id
model_version
input_references
execution_time
configuration
confidence
limitations
human_review_state
```

---

# 78. AI Decision Boundary

AI cannot implicitly create:

```text
criminal conviction
immigration conviction
citizenship revocation
detention order
deportation order
travel ban
search warrant
seizure authorization
legal finding
```

unless a jurisdiction explicitly defines a lawful automated administrative decision and its governance permits it; even then, the decision must remain an explicit typed legal action rather than an AI inference.

---

# 79. Human Review

High-impact decisions should support:

```text
REVIEW_REQUIRED
REVIEWED
OVERRIDDEN
CONFIRMED
REJECTED
```

with reviewer identity and authority.

---

# 80. AI Explanation

AI-generated recommendations should expose:

```text
supporting_inputs
contradicting_inputs
uncertainty
model_version
reason_codes
alternative_explanations
```

The runtime must not require the model to reveal proprietary internal weights.

---

# 81. Model Versioning

AI security decisions must be reproducible against:

```text
model_id
model_version
prompt/configuration version
input snapshot
feature version
policy version
```

---

# 82. Model Drift

The system monitors:

```text
accuracy metrics
false-positive rate
false-negative rate
distribution drift
data-quality drift
calibration drift
```

Models may be suspended when governance thresholds are exceeded.

---

# 83. Sensitive Attribute Firewall

Security analytics must not silently derive adverse decisions from protected or sensitive attributes unless explicitly authorized by applicable law and policy.

The type system should support:

```text
SensitiveField
RestrictedField
PurposeRestrictedField
```

---

# 84. Privacy Firewall

Queries must specify:

```text
principal
purpose
jurisdiction
dataset
requested_fields
legal_basis
```

---

# 85. Query Authorization

```axiom
security.query(
    dataset,
    selector,
    purpose,
    authority
)
```

passes through:

```text
AUTHORIZATION
→ PURPOSE
→ CLASSIFICATION
→ MINIMIZATION
→ AUDIT
→ EXECUTION
```

---

# 86. Audit Model

Every security-sensitive operation produces:

```text
AuditEvent {
    actor
    action
    object
    purpose
    authority
    timestamp
    result
    source
}
```

---

# 87. Tamper Evidence

Audit records must support:

```text
hash chaining
signatures
immutable storage
external anchoring
verification
```

Implementation may vary.

---

# 88. Audit Query

Authorized investigators may query:

```axiom
audit.find(
    actor = ...,
    object = ...,
    period = ...,
    action = ...
)
```

---

# 89. Security Case

A case groups related information without declaring the underlying allegations true.

```text
Case
├── references
├── events
├── intelligence
├── decisions
├── referrals
├── evidence references
├── actors
└── audit
```

---

# 90. Case Lifecycle

```text
OPEN
→ ACTIVE
→ REVIEW
→ RESOLVED
→ CLOSED
→ ARCHIVED
```

---

# 91. Case Separation

A security case must distinguish:

```text
lead
claim
observation
finding
decision
evidence
```

These must never collapse into a generic `fact` field.

---

# 92. Security Finding

A finding is explicitly typed:

```text
OBSERVATION
POLICY_VIOLATION
SECURITY_FINDING
ADMINISTRATIVE_FINDING
JUDICIAL_FINDING_REFERENCE
```

Judicial findings remain owned by the judicial domain.

---

# 93. Adverse Action

Any adverse administrative action should reference:

```text
subject
authority
legal_basis
decision
evidence/inputs
review_right
effective_time
expiry
appeal_reference
```

---

# 94. Review and Appeal

The system must support:

```text
REQUEST_REVIEW
REVIEW_PENDING
UNDER_REVIEW
AFFIRMED
MODIFIED
REVERSED
```

---

# 95. Notification

Where legally required, affected persons or authorized representatives may receive:

```text
decision_notice
reason_code
effective_date
review_information
appeal_information
```

Sensitive internal intelligence need not be exposed where lawfully restricted, but the system must distinguish restricted information from nonexistent information.

---

# 96. Geographic Model

Security geography uses AXGEO.

Objects include:

```text
Border
BorderSegment
BorderZone
Checkpoint
Port
Airport
Seaport
TransitZone
Jurisdiction
SecurityZone
```

---

# 97. Geographic Authority

A location may have:

```text
jurisdiction
authority
security_policy
entry_policy
exit_policy
emergency_policy
```

at a specific time.

---

# 98. Temporal Authority

Security policies are versioned by time:

```text
policy.valid_from
policy.valid_until
```

The runtime must evaluate policy against event time, not merely current time.

---

# 99. Event Time vs Processing Time

Every event may contain:

```text
event_time
ingestion_time
processing_time
```

They must remain distinct.

---

# 100. Distributed Event Bus

AXSECURITY topics:

```text
security.identity.*
security.credential.*
security.border.*
security.immigration.*
security.customs.*
security.watchlist.*
security.intelligence.*
security.threat.*
security.alert.*
security.incident.*
security.case.*
security.authority.*
security.access.*
security.audit.*
security.ai.*
security.sharing.*
```

---

# 101. Event Schema

```axiom
event SecurityEvent {
    id
    type
    subject
    source
    event_time
    ingestion_time
    jurisdiction
    classification
    authority
    payload
    provenance
}
```

---

# 102. Event Ordering

Distributed events use:

```text
event_id
source_sequence
logical_clock
causal_parent
partition
```

Ordering guarantees must be explicit.

---

# 103. Idempotency

All externally triggered security commands should support:

```text
idempotency_key
```

Repeated delivery must not create duplicate legal actions.

---

# 104. Exactly-Once Semantic Requirement

The runtime may use at-least-once transport internally.

The domain contract requires:

```text
exactly-once EFFECT
```

for operations such as:

```text
issue
revoke
authorize
deny
delegate
share
close
delete
```

through transactional/idempotent mechanisms.

---

# 105. Offline Border Operation

Border systems must support controlled offline mode.

Offline node stores:

```text
cached policy
authorized credentials
revocation snapshots
local events
pending decisions
audit chain
```

---

# 106. Offline Security Rules

Offline mode must have explicit limitations:

```text
OFFLINE_FULL
OFFLINE_LIMITED
OFFLINE_EMERGENCY
READ_ONLY
```

A node must not pretend it has current centralized information when disconnected.

---

# 107. Reconciliation

When connectivity returns:

```text
LOCAL_EVENT_LOG
→ SIGNATURE_VERIFY
→ CONFLICT_DETECTION
→ POLICY_RECHECK
→ MERGE
→ AUDIT
```

---

# 108. Conflict Resolution

Never silently overwrite conflicting security records.

Possible states:

```text
AUTO_RESOLVED
MANUAL_REVIEW
AUTHORITY_REVIEW
CONFLICT_PERSISTED
```

---

# 109. Revocation Propagation

Credential revocation events must support:

```text
priority
effective_time
distribution
acknowledgment
offline_sync
```

---

# 110. Security Notification

Notifications have:

```text
severity
audience
classification
delivery_policy
expiry
acknowledgment
```

---

# 111. Secure Federation

Multiple government agencies can operate separate security domains.

Federation requires:

```text
trust_relationship
schema_contract
identity_federation
policy_federation
audit_federation
data-sharing agreement
```

---

# 112. Agency Boundary

An agency owns its authoritative records.

AXSECURITY federation does not imply:

```text
shared database
shared authority
shared legal jurisdiction
```

---

# 113. Data Contract

Inter-agency APIs require explicit:

```text
schema_version
authority
purpose
classification
retention
consumer
provider
```

---

# 114. Schema Evolution

Security schemas use:

```text
major.minor.patch
```

Breaking changes require migration contracts.

---

# 115. Immutable Historical Records

Legal/security decisions cannot be silently edited.

Corrections use:

```text
CorrectionEvent
```

rather than destructive mutation.

---

# 116. Correction Model

```text
ORIGINAL_RECORD
→ CORRECTION
→ CURRENT_VIEW
```

The historical record remains reconstructable.

---

# 117. Data Integrity

Every authoritative object should support:

```text
version
revision
created_at
updated_at
provenance
integrity_reference
```

---

# 118. Deterministic Replay

Security event streams must be replayable:

```axiom
security.replay(
    event_range,
    policy_version,
    model_version
)
```

The system must distinguish:

```text
historical_result
```

from:

```text
recomputed_result
```

---

# 119. Policy Versioning

Every material decision records:

```text
policy_id
policy_version
effective_time
authority
```

---

# 120. Decision Reproduction

Given:

```text
input snapshot
policy version
model version
configuration
authority state
```

the runtime should reproduce the decision path as far as deterministic components permit.

---

# 121. Security Simulation

AXSECURITY provides a simulation namespace:

```text
AXSECURITY.SIM
```

Simulation objects are separate from production objects.

---

# 122. Simulation Firewall

Simulation cannot accidentally emit production commands.

```text
SIMULATION_EVENT != PRODUCTION_EVENT
```

A deliberate promotion step is required.

---

# 123. Security Exercises

Exercises can model:

```text
border disruption
credential compromise
cyber incident
critical infrastructure attack
mass identity mismatch
communication failure
cross-border information delay
large-scale traveler surge
```

Results become:

```text
ExerciseFinding
```

not real security incidents.

---

# 124. Threat Scenario

```axiom
scenario {
    assumptions
    actors
    assets
    dependencies
    events
    probabilities
    responses
    outcomes
}
```

---

# 125. Dependency Graph

AXSECURITY may represent:

```text
agency
system
facility
network
credential authority
border checkpoint
transport hub
critical infrastructure
```

with relationships:

```text
DEPENDS_ON
PROVIDES
AUTHORIZES
VERIFIES
CONNECTS
HOSTS
```

---

# 126. Cascading Risk

A dependency failure may produce:

```text
RiskPropagation
```

but not automatically:

```text
ThreatConfirmation
```

---

# 127. Security Resource Model

Resources include:

```text
personnel
inspection_capacity
communication_capacity
processing_capacity
identity_verification_capacity
transport_capacity
secure_storage
analysis_capacity
```

Resource state:

```text
AVAILABLE
ALLOCATED
DEPLOYED
BUSY
UNAVAILABLE
MAINTENANCE
```

---

# 128. Mission Boundary

AXSECURITY can create coordination missions:

```text
VERIFY
INSPECT
PROTECT
RESPOND
INVESTIGATE_REFERRAL
RESTORE_SERVICE
```

Operational tactical details remain outside the language specification.

---

# 129. Mission State

```text
PLANNED
AUTHORIZED
DISPATCHED
ACTIVE
SUSPENDED
COMPLETED
CANCELLED
```

---

# 130. Mission Outcome

A mission outcome is distinct from the original assessment.

```text
MissionAssessment
!=
MissionOutcome
```

---

# 131. Personnel Authority

Personnel are represented with:

```text
identity
role
agency
authority
clearance
jurisdiction
assignment
```

---

# 132. Role-Based Access

RBAC is supported:

```text
role → permission
```

---

# 133. Attribute-Based Access

ABAC adds:

```text
location
time
purpose
classification
case
jurisdiction
authority
```

---

# 134. Capability-Based Access

Axiom's capability system can represent:

```text
Capability<ReadIntelligence>
Capability<ModifyWatchlist>
Capability<IssueCredential>
Capability<AuthorizeEntry>
Capability<ShareClassifiedData>
```

Capabilities must be non-forgeable.

---

# 135. Capability Delegation

Capabilities may be delegated only where policy permits.

Delegated capabilities carry:

```text
scope
issuer
recipient
expiry
constraints
```

---

# 136. Security Token

```axiom
security_token {
    subject
    issuer
    scopes
    classification
    expiry
    audience
    nonce
}
```

---

# 137. Session Security

Sensitive sessions support:

```text
authentication
reauthentication
session_expiry
device_binding
step_up_authentication
```

---

# 138. Device Trust

Device state:

```text
UNKNOWN
REGISTERED
TRUSTED
RESTRICTED
COMPROMISED
REVOKED
```

A trusted device does not automatically grant data access.

---

# 139. Audit of Administrative Search

Searches involving sensitive datasets must log:

```text
who
what
why
when
authority
result_scope
```

---

# 140. Bulk Access

Bulk queries require additional authorization.

```text
normal_query
bulk_query
mass_export
```

are distinct capabilities.

---

# 141. Export Controls

Sensitive exports require:

```text
destination
classification
purpose
authority
expiry
watermark/reference
```

---

# 142. Data Redaction

The runtime supports:

```text
FIELD_REDACTION
RECORD_REDACTION
DOCUMENT_REDACTION
IDENTITY_PSEUDONYMIZATION
AGGREGATION
```

---

# 143. Pseudonymization

Analysts may operate on:

```text
SubjectToken
```

instead of direct identity when policy allows.

Re-identification requires a separate capability.

---

# 144. Re-identification

```axiom
identity.reveal(
    token,
    authority,
    purpose
)
```

must be audited.

---

# 145. Privacy-Preserving Analytics

Optional primitives:

```text
aggregation
differential_privacy
tokenization
secure_join
privacy_budget
```

These are analytical controls, not substitutes for legal authorization.

---

# 146. Secure Join

Cross-agency matching should support privacy-preserving joins where possible.

```text
AgencyA.identifier
↕
privacy_preserving_match
↕
AgencyB.identifier
```

The output may be:

```text
MATCH
NO_MATCH
REVIEW_REQUIRED
```

without automatically exposing unrelated data.

---

# 147. Entity Resolution

Entity resolution combines:

```text
identity attributes
documents
authorized identifiers
biometric verification where lawful
source provenance
conflicts
```

Output:

```text
ResolvedEntity
```

with confidence and unresolved conflicts.

---

# 148. Entity Resolution Firewall

Similarity must not be interpreted as identity proof.

```text
similarity != identity
```

---

# 149. Document Intelligence

AI may extract:

```text
names
dates
identifiers
document types
fields
anomalies
translations
```

Every extracted value has provenance.

---

# 150. Translation

Security translation must preserve:

```text
source text
translated text
language
model
confidence
human review
```

Machine translation is never silently substituted for the original source.

---

# 151. Human Review of Critical Translation

For legally significant material:

```text
MACHINE_TRANSLATION
→ HUMAN_REVIEW
→ CERTIFIED_TRANSLATION
```

where required by policy.

---

# 152. Threat Intelligence Product

An intelligence product may contain:

```text
executive_summary
observations
assessment
confidence
alternative_hypotheses
indicators
affected_entities
recommended_actions
classification
distribution
```

---

# 153. Recommendation Model

Recommendations are typed:

```text
MONITOR
VERIFY
REVIEW
PROTECT
INVESTIGATE
ESCALATE
SHARE
WAIT_FOR_MORE_INFORMATION
```

They are not commands.

---

# 154. Human Command

A command requires:

```text
authorized_principal
authority
legal_basis
scope
target
time
command
```

---

# 155. AI-to-Command Firewall

The following path is forbidden:

```text
AI_OUTPUT
→ AUTOMATIC_COMMAND
```

Required:

```text
AI_OUTPUT
→ AUTHORIZED_POLICY / HUMAN_AUTHORITY
→ COMMAND
```

except for narrowly defined pre-authorized deterministic automation that has already been explicitly encoded as policy.

---

# 156. Pre-Authorized Automation

Examples of permitted deterministic automation:

```text
credential expiration notification
routine certificate revocation propagation
policy-defined session timeout
known-format data synchronization
audit generation
```

Such automation must be explicitly declared.

---

# 157. Autonomous Security Limits

No unrestricted autonomous agent may:

```text
invent authority
expand jurisdiction
modify law
modify watchlist policy
create legal findings
issue unrestricted detention orders
revoke citizenship
create criminal convictions
```

---

# 158. Security Agent

An AI agent is represented as:

```axiom
agent SecurityAnalyst {
    capabilities
    tools
    data_scope
    authority_scope
    model
    audit_policy
}
```

---

# 159. Agent Sandbox

Agents execute in:

```text
READ_ONLY
ANALYSIS
SIMULATION
RECOMMENDATION
CONTROLLED_ACTION
```

profiles.

`CONTROLLED_ACTION` requires explicit capability grants.

---

# 160. Agent Memory

Agent memory is classified:

```text
EPHEMERAL
CASE_SCOPED
ORGANIZATIONAL
LONG_TERM
```

Retention must be policy controlled.

---

# 161. Agent Provenance

Every agent action records:

```text
agent_id
model_id
tool
input_reference
output_reference
timestamp
authority
```

---

# 162. Threat Correlation Engine

Core pipeline:

```text
INGEST
→ NORMALIZE
→ DEDUPLICATE
→ RESOLVE_ENTITIES
→ CORRELATE
→ SCORE
→ ASSESS
→ HUMAN_REVIEW
```

---

# 163. Correlation Rule

A correlation rule must declare:

```text
inputs
conditions
time_window
relationship
output
confidence_method
```

---

# 164. Rule Example

```axiom
rule possible_document_anomaly {
    when
        document.expired
        and credential.presented
        and credential.date_conflict
    then
        create ReferralCandidate
}
```

This does not create:

```text
CrimeFinding
```

---

# 165. Risk Engine

Risk models may produce:

```text
RiskScore
RiskBand
RiskFactors
Uncertainty
```

Risk scores must include model/policy version.

---

# 166. Risk Explainability

```axiom
risk.explain()
```

returns:

```text
factors
weights_or_contributions
uncertainty
missing_data
model_version
```

where technically available.

---

# 167. Risk Calibration

Models should expose:

```text
calibration_version
training_period
validation_period
population_scope
known_limitations
```

---

# 168. Population Shift

If model deployment population differs materially from validation population, the system should emit:

```text
MODEL_SCOPE_WARNING
```

---

# 169. Fairness Monitoring

Where legally applicable, monitor relevant performance disparities.

Metrics remain diagnostic rather than automatically proving discrimination.

---

# 170. Security Metrics

System metrics:

```text
verification_latency
false_match_rate
false_referral_rate
review_time
incident_detection_latency
data_quality
audit_completeness
policy_compliance
model_calibration
availability
```

---

# 171. No Outcome Optimization Without Governance

The runtime must not optimize a sensitive security system solely for:

```text
maximum denials
maximum arrests
maximum referrals
maximum watchlist matches
maximum surveillance
```

Operational objectives must be explicit, authorized and reviewable.

---

# 172. Security Data Quality

Each dataset exposes:

```text
completeness
freshness
consistency
provenance_coverage
duplicate_rate
conflict_rate
```

---

# 173. Stale Data

Objects may be marked:

```text
CURRENT
AGING
STALE
EXPIRED
UNKNOWN
```

Stale information should not silently receive the same treatment as current information.

---

# 174. Contradiction Engine

If sources conflict:

```text
CONFLICT_DETECTED
```

is produced.

The runtime must not arbitrarily choose one source unless a declared precedence policy exists.

---

# 175. Source Precedence

Precedence is policy-defined:

```axiom
precedence {
    authoritative_registry > external_claim
}
```

But precedence must not eliminate provenance.

---

# 176. Data Lineage

Every transformed record supports:

```text
origin
transform
consumer
```

lineage.

---

# 177. Compliance Engine

Security systems can declare compliance rules:

```text
retention
classification
access
purpose
sharing
notification
review
```

---

# 178. Policy DSL

Example:

```axiom
security_policy border_entry {
    require identity.verified
    require credential.valid
    require authorization.valid

    if security.referral_required {
        route secondary_screening
    }

    record entry_event
}
```

---

# 179. Access Policy DSL

```axiom
access_policy classified_intelligence {
    allow if
        principal.clearance >= resource.classification
        and principal.need_to_know
        and purpose.authorized
}
```

---

# 180. Sharing Policy DSL

```axiom
sharing_policy partner_exchange {
    allow fields [
        subject_token,
        threat_indicator,
        timestamp
    ]

    require agreement("AG-2026-17")
    require classification <= RESTRICTED
}
```

---

# 181. Watchlist Policy DSL

```axiom
watchlist_policy {
    require legal_basis
    require review_date
    require source_provenance

    deny insertion if identity.unresolved
}
```

---

# 182. Retention DSL

```axiom
retention_policy traveler_records {
    retain 365d
    review 300d

    if legal_hold {
        suspend deletion
    }
}
```

---

# 183. Authority DSL

```axiom
authority border_officer {
    allow credential.verify
    allow traveler.screen

    deny watchlist.modify
    deny citizenship.modify
}
```

---

# 184. Security Capability Types

Native capability types:

```text
ReadIdentity
VerifyIdentity
ReadCredential
VerifyCredential
ScreenTraveler
CreateReferral
ReadThreat
CreateAssessment
ModifyWatchlist
IssueCredential
RevokeCredential
AuthorizeEntry
ShareInformation
ReadClassified
ModifyPolicy
ExecuteBreakGlass
```

Sensitive capabilities require explicit authority.

---

# 185. Type-Level Security

Axiom compiler should support:

```text
@classification(...)
@purpose(...)
@requires_capability(...)
@retention(...)
@jurisdiction(...)
```

metadata.

---

# 186. Example

```axiom
@classification(SECRET)
@requires_capability(ReadClassified)
@purpose("national_security")

fn read_intelligence(id: IntelligenceId) -> IntelligenceReport
```

Compiler/runtime metadata can enforce these constraints.

---

# 187. Compile-Time Security Checks

Compiler should detect:

```text
classification downgrade
capability omission
illegal authority flow
cross-domain type confusion
unsafe secret exposure
unauthorized field access
invalid policy reference
```

---

# 188. Classification Flow

Data may flow:

```text
LOW → HIGH
```

with appropriate handling.

A flow:

```text
HIGH → LOW
```

requires explicit declassification policy.

---

# 189. Declassification

```axiom
declassify(
    object,
    authority,
    target_classification,
    reason
)
```

must be auditable.

---

# 190. Secret Handling

Secrets should use dedicated secure memory primitives where supported.

```text
SecureBuffer
SecureHandle
KeyReference
```

Secrets must not be casually copied.

---

# 191. Memory Safety

AXSECURITY should avoid GC-dependent hot paths.

Sensitive objects should use deterministic ownership/resource semantics defined by the Axiom memory model.

---

# 192. Zeroization

Sensitive memory supports:

```axiom
secure_zero(buffer)
```

where required.

Compiler must prevent unsafe optimization from removing mandated zeroization.

---

# 193. Concurrency

Security workloads are naturally partitionable by:

```text
jurisdiction
border_point
agency
case
subject
event_partition
```

---

# 194. Actor Model

High-volume ingestion may use lightweight actors:

```text
BorderNode
WatchlistShard
ThreatShard
CaseShard
AuditShard
```

---

# 195. Lock-Free Hot Path

Read-heavy operations should prefer:

```text
immutable snapshots
copy-on-write metadata
RCU-like read paths
partition-local state
append-only logs
```

where appropriate.

---

# 196. Transaction Model

Authoritative mutations require transactions.

Example:

```text
REVOKE_CREDENTIAL
+
PUBLISH_REVOCATION
+
AUDIT_EVENT
```

must form a consistent transaction boundary.

---

# 197. Event Sourcing

Suitable domains:

```text
watchlists
credentials
authority
cases
security incidents
audit
sharing agreements
```

may use event sourcing.

---

# 198. Snapshotting

Large state stores use:

```text
snapshot
+
event tail
```

for fast recovery.

---

# 199. Disaster Recovery

Security runtime must support:

```text
HOT
WARM
COLD
OFFLINE
```

recovery profiles.

---

# 200. Multi-Region Deployment

Deployments can use:

```text
primary
secondary
regional
border-edge
offline-edge
```

with explicit consistency policies.

---

# 201. Consistency

Security records classify consistency as:

```text
STRONG
CAUSAL
EVENTUAL
LOCAL
```

The API must expose the guarantee.

---

# 202. No Hidden Stale Reads

If a query reads a stale replica, the response includes:

```text
data_version
as_of
staleness
```

where applicable.

---

# 203. Availability vs Authority

Availability must never silently imply authority.

A node can remain operational while lacking authority to perform certain actions.

---

# 204. Border Edge Runtime

A lightweight runtime profile:

```text
AXSECURITY_EDGE
```

supports:

```text
credential verification
local policy evaluation
offline cache
local event logging
secure synchronization
```

---

# 205. Central Intelligence Runtime

```text
AXSECURITY_CORE
```

supports:

```text
large-scale graph
AI analysis
cross-agency correlation
historical analytics
policy management
federation
```

---

# 206. Analytics Runtime

```text
AXSECURITY_ANALYTICS
```

supports:

```text
batch
stream
graph
ML
simulation
```

without acquiring authority to modify legal records by default.

---

# 207. Read-Only Intelligence Environment

Analysts can receive:

```text
READ_ONLY
```

views that cannot mutate source systems.

---

# 208. Separation of Duties

Critical operations can require multiple principals:

```text
PROPOSE
→ REVIEW
→ AUTHORIZE
→ EXECUTE
```

---

# 209. Four-Eyes Rule

Policies may require:

```text
2 independent approvals
```

for especially sensitive operations.

---

# 210. Dual Control

Certain operations support:

```text
operator_A
+
operator_B
```

before activation.

---

# 211. Emergency Override

Emergency override bypasses normal timing constraints only where legally authorized.

It never bypasses:

```text
audit
authority
scope
expiry
```

unless emergency law explicitly specifies otherwise.

---

# 212. Time-Bounded Privilege

Every elevated privilege should have:

```text
start
expiry
renewal
revocation
```

---

# 213. Automatic Expiry

Expired authority must become unusable automatically.

---

# 214. Security Clock

Critical security events use trusted time references.

Time uncertainty must be represented.

---

# 215. Clock Conflict

If timestamps conflict:

```text
TIME_CONFLICT
```

is recorded rather than silently corrected.

---

# 216. International Time

All canonical records use UTC internally.

Jurisdictional views may display local time.

---

# 217. Language

All textual fields use UTF-8.

Multilingual support:

```text
language
script
transliteration
translation
original_text
```

must remain distinct.

---

# 218. Name Matching

Name matching must support:

```text
Unicode normalization
diacritics
transliteration
alternate scripts
ordering differences
aliases
```

but similarity does not establish identity.

---

# 219. Alias

Aliases are explicit:

```text
Alias {
    value
    source
    validity
    confidence
}
```

---

# 220. Unknown Identity

The system must support:

```text
UNKNOWN_PERSON
UNKNOWN_ORGANIZATION
UNKNOWN_DOCUMENT
```

rather than forcing a guessed identity.

---

# 221. Entity Merge

Entity merges require:

```text
merge_reason
authority
source_entities
result_entity
review
audit
```

---

# 222. Entity Split

False merges must be reversible:

```text
split_reason
affected_records
authority
audit
```

---

# 223. Security Search

Search supports:

```text
exact
fuzzy
phonetic
semantic
graph
temporal
geospatial
```

Each result identifies the matching method.

---

# 224. Search Confidence

Search ranking is not evidence strength.

```text
search_score != truth_score
```

---

# 225. Graph Query

```axiom
security.graph.find(
    subject,
    relation,
    depth,
    period
)
```

must enforce access controls before traversal.

---

# 226. Query Budget

Large graph queries may require:

```text
query_budget
time_limit
node_limit
edge_limit
```

to prevent denial-of-service.

---

# 227. Security Observability

Metrics:

```text
authentication_failures
authorization_denials
watchlist_match_rate
false_match_rate
audit_gap_rate
data_staleness
replication_lag
policy_errors
model_errors
```

---

# 228. Health State

Runtime health:

```text
HEALTHY
DEGRADED
PARTIAL
OFFLINE
RECOVERING
COMPROMISED
```

---

# 229. Compromise Mode

If the system is suspected compromised:

```text
ISOLATE
→ PRESERVE_AUDIT
→ ROTATE_CREDENTIALS
→ LIMIT_ACTIONS
→ RECOVER
→ REVIEW
```

---

# 230. Evidence Preservation

Incident response must preserve:

```text
logs
audit records
system snapshots
configuration versions
model versions
policy versions
```

without silently altering originals.

---

# 231. Security Incident Correlation

Security incidents may correlate with AXSAFETY incidents.

Example:

```text
cyber incident
→ infrastructure outage
→ emergency declaration
```

The domains remain separate but interoperable.

---

# 232. Safety-Security Boundary

```text
SecurityThreat
```

may become:

```text
SafetyHazard
```

only through an explicit domain transformation.

---

# 233. Security-to-Safety Event

```axiom
security.publish_safety_signal(
    threat,
    affected_area,
    confidence
)
```

must preserve uncertainty.

---

# 234. Safety-to-Security Event

AXSAFETY may publish:

```text
infrastructure disruption
mass evacuation
critical facility failure
```

AXSECURITY may correlate these with security intelligence.

---

# 235. Government Coordination Dashboard

The runtime data model supports views:

```text
NationalSecurityOverview
BorderOperations
ThreatLandscape
WatchlistStatus
ImmigrationOperations
CustomsSecurity
IncidentOverview
IntelligenceProduction
CrossAgencySharing
AuditOverview
```

Views are read models, not authoritative records.

---

# 236. Command Dashboard Boundary

A dashboard action must invoke an explicit command API.

UI clicks cannot directly mutate authoritative state without authorization.

---

# 237. API Categories

```text
Identity API
Credential API
Border API
Immigration API
Watchlist API
Threat API
Intelligence API
Incident API
Case API
Authority API
Sharing API
Audit API
AI API
Simulation API
```

---

# 238. Native API Contract

Each API method declares:

```text
input
output
capabilities
classification
purpose
authority
transactionality
idempotency
audit behavior
```

---

# 239. Example API

```axiom
@requires_capability(ScreenTraveler)
@audit
fn screen(
    traveler: TravelerId
) -> ScreeningResult
```

---

# 240. Command vs Query

AXSECURITY follows:

```text
QUERY != COMMAND
```

Queries do not mutate authoritative state.

Commands explicitly declare mutations.

---

# 241. Error Model

Security APIs use typed errors:

```text
Unauthorized
Forbidden
ExpiredAuthority
InvalidCredential
IdentityConflict
WatchlistConflict
ClassificationViolation
PurposeViolation
PolicyViolation
StaleData
OfflineRestriction
AuthorityExpired
AuditFailure
IntegrityFailure
```

---

# 242. Fail Closed

Security-sensitive authorization checks should fail closed.

---

# 243. Availability Exception

Availability exceptions must be explicit:

```text
OFFLINE_POLICY
EMERGENCY_POLICY
DEGRADED_POLICY
```

Never implicit.

---

# 244. Audit Failure

If mandatory audit cannot be recorded, high-risk operations should fail unless an explicit emergency policy defines a controlled fallback.

---

# 245. Data Corruption

Corrupted authoritative records must transition to:

```text
INTEGRITY_ERROR
```

rather than silently being repaired.

---

# 246. Repair

Repair produces:

```text
RepairRecord
```

containing:

```text
original
diagnosis
repair_method
authority
operator
time
verification
```

---

# 247. Performance Targets

Reference deployment targets:

```text
≥ 10M lightweight security events/sec
≥ 1M credential verification ops/sec
≥ 100K concurrent border sessions per large regional cluster
sub-millisecond local authorization-cache lookup target
linear partition scaling
```

Actual performance is hardware/deployment dependent.

---

# 248. Memory Targets

Hot-path processing should avoid:

```text
GC pauses
large temporary allocations
global locks
unbounded queues
```

---

# 249. Storage Targets

Storage supports:

```text
append-only event log
columnar analytics
graph index
key-value state
immutable audit store
object/document store
```

without requiring a third-party runtime dependency in the Axiom language core.

---

# 250. Compilation

AXSECURITY code compiles to native Axiom targets:

```text
Windows EXE/DLL
Linux ELF/SO
macOS Mach-O
iOS
Android
WASM
```

subject to platform capabilities.

---

# 251. Runtime Profiles

```text
AXSECURITY_CORE
AXSECURITY_EDGE
AXSECURITY_ANALYTICS
AXSECURITY_GATEWAY
AXSECURITY_AUDIT
AXSECURITY_SIM
```

---

# 252. Minimal Runtime

The edge runtime should be capable of running without:

```text
GC
large VM
heavy scripting engine
mandatory cloud dependency
```

---

# 253. Deterministic Build

Security binaries support:

```text
reproducible build
content hash
dependency manifest
compiler version
schema version
policy bundle version
```

---

# 254. Supply Chain Integrity

Artifacts support:

```text
signed build
SBOM
dependency hash
compiler provenance
source revision
```

---

# 255. Secure Update

Updates:

```text
SIGNED
VERIFIED
STAGED
TESTED
DEPLOYED
ROLLBACK_CAPABLE
```

---

# 256. Policy Update

Policy updates must be separately versioned from binaries.

```text
binary_version
policy_version
model_version
schema_version
```

are independent.

---

# 257. Model Update

AI model updates require:

```text
validation
approval
versioning
rollback
audit
```

---

# 258. Rollback

The system must support rollback of:

```text
binary
policy
model
schema
configuration
```

without deleting historical audit records.

---

# 259. Testing Strategy

AXSECURITY requires:

```text
unit tests
property tests
fuzz tests
policy tests
authorization tests
concurrency tests
replay tests
disaster tests
offline tests
model validation
integration tests
cross-domain tests
```

---

# 260. Security Invariants

At minimum, the implementation must enforce:

```text
I001 Identity != Threat
I002 Watchlist != Guilt
I003 RiskScore != Guilt
I004 Alert != Confirmation
I005 Intelligence != Evidence
I006 Assessment != JudicialFinding
I007 Source != Fact
I008 Confidence != Truth
I009 Anomaly != Crime
I010 Suspicion != Guilt
I011 Visa != Citizenship
I012 Residence != Citizenship
I013 EntryAuthorization != Citizenship
I014 BiometricMatch != Criminality
I015 Screening != Investigation
I016 Inspection != Seizure
I017 Seizure != Forfeiture
I018 Denial != Conviction
I019 Detention != Guilt
I020 AIRecommendation != LegalDecision
I021 Simulation != Production
I022 Forecast != Observation
I023 Prediction != Event
I024 SearchScore != TruthScore
I025 Similarity != Identity
I026 Clearance != NeedToKnow
I027 Classification != Truth
I028 Classification != Reliability
I029 Authority != Identity
I030 Delegation <= DelegatorAuthority
I031 ExpiredAuthority cannot mutate
I032 Audit cannot be silently deleted
I033 HistoricalDecision cannot be silently mutated
I034 Correction preserves history
I035 HighClassification cannot flow downward implicitly
I036 SensitiveQuery requires purpose
I037 SensitiveQuery requires authority
I038 BulkExport requires explicit capability
I039 Reidentification requires explicit capability
I040 CrossBorderSharing requires legal basis
I041 CrossBorderSharing requires agreement where applicable
I042 AI output carries provenance
I043 AI output carries model version
I044 AI cannot invent authority
I045 AI cannot modify law
I046 Offline node cannot claim online freshness
I047 Stale data carries staleness
I048 Conflict cannot be silently resolved
I049 Credential revocation is auditable
I050 Watchlist modification is auditable
I051 Security command is explicitly typed
I052 Query != Command
I053 Simulation cannot emit production command
I054 Emergency privilege has scope
I055 Emergency privilege has expiry
I056 Break-glass is audited
I057 Legal hold blocks normal deletion
I058 Deletion produces audit record
I059 Entity merge is auditable
I060 Entity split is auditable
I061 Authority is time-bounded where applicable
I062 Classification downgrade requires authorization
I063 Secure audit failure blocks high-risk operations unless explicit emergency policy
I064 Model version is reproducible
I065 Policy version is reproducible
I066 Decision inputs are traceable
I067 Alternative hypotheses remain distinguishable from facts
I068 Correlation != Causation
I069 Association != Guilt
I070 Recommendation != Command
```

---

# 261. Native Type Requirements

Core native types:

```text
PersonId
OrganizationId
CredentialId
VisaId
TravelDocumentId
BorderPointId
JourneyId
WatchlistId
WatchlistEntryId
ThreatId
IndicatorId
AssessmentId
IntelligenceId
IncidentId
CaseId
ReferralId
AuthorityId
PolicyId
AgreementId
AuditId
Classification
Confidence
RiskScore
Timestamp
Jurisdiction
Capability
```

---

# 262. Strong Identifier Types

Identifiers must not be interchangeable.

For example:

```text
PersonId != CredentialId
ThreatId != CaseId
WatchlistEntryId != PersonId
AuthorityId != PolicyId
```

This prevents major classes of domain bugs.

---

# 263. Units and Time

All time types are strongly typed.

```text
Timestamp
Duration
ValidityPeriod
ReviewPeriod
RetentionPeriod
```

---

# 264. Classification Type

```axiom
enum Classification {
    Public
    Internal
    Restricted
    Confidential
    Secret
    TopSecret
}
```

Jurisdiction extensions are permitted.

---

# 265. Confidence Type

Confidence is not a generic float.

```axiom
struct Confidence {
    value
    method
    calibration
    basis
}
```

---

# 266. Risk Type

```axiom
struct RiskScore {
    value
    model
    version
    scope
    uncertainty
}
```

---

# 267. Authority Type

```axiom
struct Authority {
    issuer
    jurisdiction
    scope
    legal_basis
    valid_from
    valid_until
}
```

---

# 268. Policy Type

```axiom
struct SecurityPolicy {
    id
    version
    jurisdiction
    effective_from
    effective_until
    rules
    authority
}
```

---

# 269. Provenance Type

```axiom
struct Provenance {
    source
    observed_at
    ingested_at
    transformed_by
    parent
}
```

---

# 270. AI Result Type

```axiom
struct AIResult<T> {
    value
    model
    model_version
    confidence
    inputs
    provenance
    limitations
    review_state
}
```

---

# 271. Security Event Type

```axiom
struct SecurityEvent<T> {
    id
    type
    payload: T
    source
    subject
    jurisdiction
    event_time
    classification
    authority
    provenance
}
```

---

# 272. Command Type

```axiom
struct SecurityCommand<T> {
    id
    command_type
    payload: T
    issuer
    authority
    scope
    issued_at
    expires_at
    idempotency_key
}
```

---

# 273. Decision Type

```axiom
struct SecurityDecision<T> {
    id
    subject
    decision
    authority
    legal_basis
    inputs
    policy_version
    decision_time
    reviewer
    review_state
}
```

---

# 274. Query Type

```axiom
struct SecurityQuery<T> {
    principal
    purpose
    authority
    selector
    requested_fields
}
```

---

# 275. Secure Storage

Native storage abstractions:

```text
AppendLog
ImmutableStore
SecureKV
TemporalStore
GraphStore
DocumentStore
AuditStore
```

---

# 276. No Mandatory Database Dependency

AXSECURITY APIs target abstract storage traits.

The Axiom compiler/runtime does not require a specific third-party database.

---

# 277. Persistence Trait

```axiom
trait SecureStore<T> {
    fn read(...)
    fn append(...)
    fn version(...)
    fn snapshot(...)
    fn verify(...)
}
```

---

# 278. Audit Trait

```axiom
trait AuditSink {
    fn record(event: AuditEvent)
    fn verify(range)
}
```

---

# 279. Authority Trait

```axiom
trait AuthorityProvider {
    fn evaluate(action, principal, context)
}
```

---

# 280. Policy Trait

```axiom
trait PolicyEngine {
    fn evaluate(policy, context)
}
```

---

# 281. Intelligence Trait

```axiom
trait IntelligenceAnalyzer {
    fn analyze(input) -> IntelligenceAssessment
}
```

---

# 282. AI Trait

```axiom
trait SecurityAI {
    fn analyze(input) -> AIResult
    fn recommend(input) -> AIResult
}
```

---

# 283. Human Review Trait

```axiom
trait HumanReview {
    fn review(case, recommendation) -> ReviewDecision
}
```

---

# 284. Border Adapter

```axiom
trait BorderAdapter {
    fn arrival()
    fn verify_document()
    fn screen()
    fn refer()
    fn record_entry()
    fn record_exit()
}
```

---

# 285. Credential Adapter

```axiom
trait CredentialAuthority {
    fn verify()
    fn issue()
    fn revoke()
    fn status()
}
```

---

# 286. Federation Adapter

```axiom
trait SecurityFederation {
    fn request()
    fn respond()
    fn verify_partner()
    fn audit_exchange()
}
```

---

# 287. Event Adapter

```axiom
trait SecurityEventSource {
    fn subscribe(topic)
    fn ingest(event)
}
```

---

# 288. Compiler Metadata

The compiler should preserve:

```text
@security_domain
@classification
@purpose
@requires_capability
@authority
@retention
@jurisdiction
@audit
@ai_generated
@provenance
```

in machine-readable metadata.

---

# 289. AI-Readable Artifacts

Compiled security schemas should emit:

```text
AXMETA
```

containing:

```text
types
fields
relationships
authority requirements
classification
capabilities
policies
events
commands
queries
provenance
```

This supports AI-assisted maintenance and analysis.

---

# 290. Static Security Analyzer

Compiler tooling:

```text
axiom security check
```

detects:

```text
unauthorized flow
classification violation
missing audit
missing authority
unbounded retention
unsafe AI action
implicit legal decision
```

---

# 291. Security Linter

Example:

```text
AXS001 Missing authority
AXS002 Missing audit
AXS003 Classification downgrade
AXS004 AI-to-command flow
AXS005 Unbounded retention
AXS006 Missing provenance
AXS007 Weak identifier typing
AXS008 Unreviewed adverse decision
AXS009 Cross-border sharing without agreement
AXS010 Sensitive query without purpose
```

---

# 292. Formal Verification Targets

Formal methods should target:

```text
authority boundaries
classification flow
capability safety
audit completeness
state transitions
idempotency
retention rules
policy consistency
```

---

# 293. Property Testing

Properties include:

```text
expired authority never authorizes
unauthorized actor never accesses
classification never silently downgrades
duplicate command never duplicates effect
correction never destroys history
watchlist match never becomes guilt automatically
AI recommendation never becomes command automatically
```

---

# 294. Fuzz Testing

Fuzz:

```text
credential formats
identity names
Unicode
timestamps
event ordering
policy expressions
classification labels
federation messages
AI metadata
```

---

# 295. Concurrency Testing

Test:

```text
simultaneous revocation
simultaneous authorization
watchlist updates
offline reconciliation
duplicate events
conflicting decisions
authority expiration during transaction
```

---

# 296. Failure Injection

Simulate:

```text
database loss
network partition
clock drift
duplicate message
corrupted event
stale cache
revoked key
compromised node
model unavailable
policy unavailable
audit unavailable
```

---

# 297. Security Test Target

Minimum target:

```text
≥ 20,000 automated tests
```

across:

```text
unit
integration
policy
security
performance
fuzz
property
replay
federation
offline
AI governance
```

---

# 298. Conformance Suite

Every AXSECURITY implementation must pass:

```text
AXSECURITY-CONFORMANCE-v1
```

before production certification.

---

# 299. Deterministic Test Replay

Each test may capture:

```text
input
policy
model
authority
event stream
expected state
expected audit
```

---

# 300. Reference End-to-End Flow

Canonical border flow:

```text
TRAVELER
    ↓
ARRIVAL
    ↓
DOCUMENT
    ↓
IDENTITY VERIFICATION
    ↓
CREDENTIAL VALIDATION
    ↓
IMMIGRATION STATUS
    ↓
SECURITY SCREENING
    ↓
WATCHLIST CHECK
    ↓
CUSTOMS SECURITY
    ↓
NORMAL ENTRY
      OR
REFERRAL
    ↓
AUTHORIZED REVIEW
    ↓
DECISION
    ↓
ENTRY / EXIT RECORD
    ↓
AUDIT
```

---

# 301. Intelligence End-to-End Flow

```text
SOURCE
→ COLLECTION
→ OBSERVATION
→ NORMALIZATION
→ ENTITY RESOLUTION
→ CORRELATION
→ INDICATOR
→ ASSESSMENT
→ ALTERNATIVE HYPOTHESES
→ AI ANALYSIS
→ HUMAN REVIEW
→ INTELLIGENCE PRODUCT
→ AUTHORIZED DISSEMINATION
→ AUDIT
```

---

# 302. Security Incident Flow

```text
SIGNAL
→ ALERT
→ TRIAGE
→ INCIDENT
→ ASSESSMENT
→ AUTHORITY
→ RESPONSE
→ CONTAINMENT
→ RECOVERY
→ REVIEW
→ LESSONS
```

---

# 303. Cross-Agency Flow

```text
REQUEST
→ AUTHORITY CHECK
→ PURPOSE CHECK
→ CLASSIFICATION CHECK
→ DATA MINIMIZATION
→ TRANSMISSION
→ RECEIPT
→ PROCESSING
→ RESPONSE
→ AUDIT
```

---

# 304. AI-Assisted Flow

```text
RAW DATA
→ AI EXTRACTION
→ PROVENANCE
→ CORRELATION
→ AI ASSESSMENT
→ UNCERTAINTY
→ HUMAN REVIEW
→ AUTHORIZED DECISION
→ AUDIT
```

---

# 305. Security Truth Hierarchy

AXSECURITY recognizes:

```text
OBSERVATION
    <
VERIFIED RECORD
    <
AUTHORIZED DECISION
    <
JUDICIAL FINDING
```

but these are not interchangeable.

An observation cannot automatically become a judicial finding.

---

# 306. Security State Hierarchy

The system distinguishes:

```text
SIGNAL
→ INDICATOR
→ ALERT
→ ASSESSMENT
→ THREAT
→ INCIDENT
→ AUTHORIZED ACTION
→ OUTCOME
```

Every transition requires explicit semantics.

---

# 307. Core Design Rule

The system must never answer:

> "Is this person dangerous?"

as a single untyped boolean.

It should expose:

```text
identity status
known observations
authorized watchlist state
risk assessments
threat assessments
confidence
uncertainty
source provenance
legal findings
authorized decisions
```

as separate objects.

---

# 308. Governance Rule

Security infrastructure must optimize for:

```text
TRUTHFULNESS
TRACEABILITY
AUTHORITY
MINIMIZATION
REVIEWABILITY
AVAILABILITY
SECURITY
ACCOUNTABILITY
```

rather than simply maximizing automated action.

---

# 309. Architectural Summary

AXSECURITY is therefore:

```text
                 ┌───────────────────────┐
                 │       AXSECURITY      │
                 └───────────┬───────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
     BORDER              INTELLIGENCE         SECURITY
        │                    │                 INCIDENTS
        │                    │                    │
  Immigration          Threat Graph          Alerts
  Credentials          Assessments            Cases
  Entry/Exit            AI Analysis            Response
  Customs               Sharing                Recovery
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                     AUTHORITY / POLICY
                             │
                      AUDIT / PROVENANCE
                             │
                    AXIOM NATIVE RUNTIME
```

---

# 310. Final Semantic Contract

AXSECURITY's fundamental semantic contract is:

```text
IDENTITY ESTABLISHES WHO
CREDENTIALS ESTABLISH AUTHORIZATION CLAIMS
OBSERVATIONS RECORD WHAT WAS OBSERVED
INTELLIGENCE CONNECTS INFORMATION
ASSESSMENTS EXPRESS INTERPRETATION
THREATS REPRESENT SECURITY CONCERNS
WATCHLISTS DEFINE GOVERNED HANDLING
RISK MODELS ESTIMATE RISK
AUTHORITIES DEFINE LEGAL POWER
POLICIES DEFINE PERMITTED BEHAVIOR
AI ASSISTS ANALYSIS
HUMANS/AUTHORIZED SYSTEMS EXERCISE AUTHORITY
AUDIT PRESERVES ACCOUNTABILITY
PROVENANCE PRESERVES ORIGIN
LAW DEFINES LEGAL EFFECT
```

The critical invariant is:

```text
INFORMATION ≠ INTERPRETATION ≠ AUTHORITY ≠ LEGAL TRUTH
```

---

# 311. Acceptance Criteria

BOOTSTRAP-701 is complete when the Axiom implementation can demonstrate:

1. Typed identity/credential/immigration/border models.
2. Typed watchlists and match states.
3. Intelligence provenance.
4. Threat and risk separation.
5. Classification and compartment enforcement.
6. Purpose limitation.
7. Retention and legal hold.
8. Cross-border sharing governance.
9. Border screening workflows.
10. Customs-security workflows.
11. Authority and delegation.
12. Break-glass audit.
13. AI provenance.
14. AI-to-command firewall.
15. Human review workflows.
16. Offline border operation.
17. Deterministic reconciliation.
18. Event replay.
19. Immutable audit history.
20. Strong identifier types.
21. Policy DSL.
22. Security capability model.
23. Federation contracts.
24. Secure storage traits.
25. Threat graph.
26. Entity resolution.
27. Privacy-preserving query mechanisms.
28. Model/version reproducibility.
29. Security static analysis.
30. ≥20,000 automated tests.
31. Native compilation on Axiom target platforms.
32. No mandatory GC in hot paths.
33. No mandatory third-party runtime dependency for Axiom core.
34. Explicit separation from AXLAW/AXJUSTICE/AXSAFETY/AXFISCAL.
35. Deterministic production/simulation separation.

---

# 312. Implementation Order

The compiler/runtime implementation should proceed:

```text
1. Strong security identifiers
2. Classification types
3. Capability types
4. Authority model
5. Audit primitives
6. Provenance
7. Policy engine
8. Credential model
9. Identity verification
10. Border state machine
11. Immigration state machine
12. Watchlist engine
13. Threat model
14. Intelligence graph
15. Case model
16. Cross-agency federation
17. Offline event log
18. Reconciliation
19. AI provenance
20. AI recommendation boundary
21. Retention engine
22. Privacy engine
23. Security DSL
24. Static analyzer
25. Simulation
26. Performance optimization
27. Conformance suite
28. Native deployment
```

---

# 313. Final Architecture Principle

```text
SECURITY SYSTEMS MUST KNOW THE DIFFERENCE BETWEEN
WHAT WAS OBSERVED,
WHAT WAS CLAIMED,
WHAT WAS INFERRED,
WHAT WAS ASSESSED,
WHAT WAS AUTHORIZED,
AND WHAT IS LEGALLY TRUE.
```

And therefore:

```text
IDENTITY IS NOT THREAT.
WATCHLIST IS NOT GUILT.
RISK IS NOT CRIME.
INTELLIGENCE IS NOT EVIDENCE.
AI IS NOT AUTHORITY.
ALERT IS NOT CONFIRMATION.
SCREENING IS NOT INVESTIGATION.
IMMIGRATION STATUS IS NOT CITIZENSHIP.
INSPECTION IS NOT SEIZURE.
SEIZURE IS NOT FORFEITURE.
RECOMMENDATION IS NOT COMMAND.
CLASSIFICATION IS NOT TRUTH.
CONFIDENCE IS NOT CERTAINTY.
```

This semantic separation is a first-class architectural property of Axiom, not merely documentation.

# END OF BOOTSTRAP-701
:::

**BOOTSTRAP-701 hoàn tất.** Theo chuỗi kiến trúc, task kế tiếp là:

**BOOTSTRAP-702 — AXJUSTICE: Native AI Civilization-Scale Government Justice, Courts, Prosecutorial Case Management, Legal Proceedings & Judicial Administration Runtime 5.0**

Tôi sẽ tiếp tục từ đó ở lượt kế tiếp, không cần hỏi lại.