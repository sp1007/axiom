Tiếp tục chuỗi Axiom với **BOOTSTRAP-672 — Civilization-Scale Law, Rights, Legal Identity, Contracts, Regulation, Courts, Adjudication & Justice Runtime 5.0**.

:::writing{variant="document" id="74163" title="BOOTSTRAP-672 — Native AI Civilization-Scale Law, Rights, Legal Identity, Contracts, Regulation, Courts, Adjudication, Dispute Resolution & Justice Runtime 5.0"}

# BOOTSTRAP-672
## Native AI Civilization-Scale Law, Rights, Legal Identity, Contracts, Regulation, Courts, Adjudication, Dispute Resolution & Justice Runtime 5.0

**Status:** ARCHITECTURE COMPLETE  
**Layer:** Civilization-Scale Legal & Institutional Rule Systems  
**Depends on:** BOOTSTRAP-603 … BOOTSTRAP-671  
**Primary dependencies:** 603, 610, 617, 627, 628, 633, 639, 640, 647, 663, 664, 665, 667, 668, 670, 671  
**Target:** ≥ 4,500 tests, ≥ 360 invariants  
**Execution classes:** deterministic, distributed, simulation, policy-controlled, human-review, offline  
**Capability model:** optional / capability-gated / authority-gated / privacy-gated / safety-gated / human-approval-gated.

---

# 1. Mission

BOOTSTRAP-672 defines Axiom's native computational substrate for formalized legal and institutional rule systems.

It provides executable representations for:

- legal identity;
- legal entities;
- rights;
- duties;
- permissions;
- obligations;
- claims;
- liabilities;
- legal relationships;
- contracts;
- statutes;
- regulations;
- rules;
- licenses;
- permits;
- compliance;
- violations;
- evidence;
- legal proceedings;
- courts;
- tribunals;
- adjudication;
- mediation;
- arbitration;
- appeals;
- remedies;
- judgments;
- enforcement;
- legal records;
- jurisdiction;
- conflict of laws;
- legal interoperability;
- institutional governance;
- regulatory execution;
- legal simulation.

The runtime is a **formal rule and adjudication substrate**.

It is not itself the source of political authority, sovereignty, moral truth, or human rights.

---

# 2. Architectural Position

```text
603 Capability / Security
627 Identity
640 Data Governance
665 Human Oversight
        ↓
667 Organizations / Institutions
668 Inter-Organization Governance
        ↓
672 Legal / Institutional Rule Systems
        ↓
671 Economic Contracts / Transactions
670 Human / Societal Systems
669 Physical / Infrastructure Systems
        ↓
663 Evaluation
664 Safety
```

672 intersects heavily with 639.

The separation is:

```text
639 = authority and policy decision boundary
672 = formal representation, interpretation, execution and adjudication
```

A policy authority can declare a rule.

672 can represent and execute that rule.

672 must not manufacture authority that was never granted.

---

# 3. Core Principle

A legal rule is represented as:

```text
Rule
+ Jurisdiction
+ EffectivePeriod
+ Scope
+ Preconditions
+ Obligations
+ Rights
+ Exceptions
+ Enforcement
```

Example:

```text
rule MinimumAgeForActivity {
    jurisdiction = J
    subject = Person
    condition = age >= 18
    effect = permitted
}
```

The rule is executable only inside its declared jurisdiction and validity period.

---

# 4. Critical Separation

The following concepts must never be conflated:

```text
legal_identity
human_identity
organizational_identity

right
permission
capability

legal_obligation
economic_obligation
technical_constraint

rule
policy
objective

violation
error
accident

evidence
belief
prediction

judgment
simulation_result
model_output

legal_person
human_person
AI_agent
software_component
```

---

# 5. Legal Identity

```text
LegalIdentity {
    id
    subject
    jurisdiction
    status
    effective_period
    credentials
}
```

Legal identity can refer to:

```text
HUMAN
ORGANIZATION
CORPORATION
ASSOCIATION
TRUST
PUBLIC_BODY
AI_SYSTEM
SOFTWARE_AGENT
ASSET
ESTATE
OTHER
```

The runtime does not infer legal personhood merely from an object existing.

---

# 6. Legal Person

```text
LegalPerson {
    id
    identity
    person_type
    rights
    duties
    representatives
}
```

`LegalPerson` is a jurisdiction-defined legal abstraction.

Axiom must not assume that:

```text
AI agent = legal person
```

or:

```text
organization = human
```

---

# 7. Human Legal Identity

Integration:

```text
670 Human Systems
627 Identity
617 Unicode / Language
640 Privacy
```

The legal identity layer may reference:

```text
PersonId
CredentialId
Residency
Nationality
LegalStatus
```

but sensitive personal attributes must remain access-controlled.

---

# 8. Rights

```text
Right {
    id
    holder
    object
    scope
    jurisdiction
    effective_period
    limitations
}
```

Possible computational categories:

```text
PROPERTY_RIGHT
CONTRACT_RIGHT
ACCESS_RIGHT
PARTICIPATION_RIGHT
PROCEDURAL_RIGHT
PRIVACY_RIGHT
DATA_RIGHT
LICENSE_RIGHT
USE_RIGHT
CLAIM_RIGHT
OTHER
```

The runtime does not define a universal normative list of human rights.

Rights are supplied by the applicable legal framework.

---

# 9. Duties

```text
Duty {
    holder
    action
    object
    conditions
    deadline
    jurisdiction
}
```

A duty may be:

```text
mandatory
conditional
time_limited
delegated
suspended
expired
```

---

# 10. Legal Permission

```text
Permission {
    subject
    action
    object
    scope
    conditions
}
```

Permission ≠ capability.

A subject may legally be permitted to perform an action but technically lack the capability to do so.

---

# 11. Technical Capability

603 controls technical capability.

Example:

```text
legal_permission = true
technical_capability = false
```

means:

> legally allowed, technically unavailable.

The inverse:

```text
legal_permission = false
technical_capability = true
```

must not imply legal authorization.

---

# 12. Legal Obligation

```text
LegalObligation {
    debtor
    creditor?
    action
    object
    condition
    deadline
    source_rule
}
```

Economic debt and legal obligation may overlap but are not identical.

---

# 13. Claim

```text
LegalClaim {
    claimant
    respondent
    legal_basis
    facts
    requested_remedy
    evidence
}
```

A claim is an assertion seeking legal recognition or remedy.

A claim is not automatically true.

---

# 14. Liability

```text
LegalLiability {
    subject
    basis
    conditions
    scope
    remedy
}
```

Possible bases:

```text
CONTRACT
TORT
STATUTE
REGULATION
PROPERTY
CORPORATE
ADMINISTRATIVE
CUSTOM
OTHER
```

---

# 15. Legal Relationship

```text
LegalRelationship {
    parties
    rights
    duties
    claims
    obligations
    source
    jurisdiction
}
```

Relationships may be:

```text
ownership
employment
agency
guardianship
contract
membership
licensing
delegation
custody
representation
```

---

# 16. Jurisdiction

```text
Jurisdiction {
    id
    authority
    territory?
    subjects
    domains
    effective_period
}
```

Jurisdiction is computational authority scope.

It does not automatically imply sovereignty.

---

# 17. Jurisdiction Boundary

```text
JurisdictionBoundary {
    source
    target
    subject_domain
    precedence_rule
    conflict_rule
}
```

This is required for multi-jurisdiction systems.

---

# 18. Conflict of Laws

```text
ConflictRule {
    jurisdictions
    priority
    subject_domain
    precedence
    exception
}
```

Possible mechanisms:

```text
LEX_SUPERIOR
LEX_SPECIALIS
LEX_POSTERIOR
CHOSEN_LAW
JURISDICTIONAL_PRIORITY
RECIPROCAL_RECOGNITION
CUSTOM
CUSTOM_RULE
```

These are computational strategies, not universal legal truths.

---

# 19. Legal Source

```text
LegalSource {
    id
    issuer
    type
    version
    publication
    effective_period
    text_reference
}
```

Types:

```text
CONSTITUTION
STATUTE
REGULATION
ORDINANCE
COURT_DECISION
CONTRACT
TREATY
PROTOCOL
LICENSE
POLICY
CUSTOM
OTHER
```

---

# 20. Legal Rule

```text
LegalRule {
    id
    source
    jurisdiction
    subject
    predicates
    effects
    exceptions
    priority
}
```

Rule lifecycle:

```text
DRAFT
→ REVIEW
→ ADOPTED
→ PUBLISHED
→ EFFECTIVE
→ AMENDED
→ SUSPENDED
→ EXPIRED
→ REPEALED
→ ARCHIVED
```

---

# 21. Rule Versioning

Every executable legal rule requires:

```text
rule_id
version
source_version
effective_from
effective_until?
```

Historical decisions must retain the rule version used at adjudication time.

---

# 22. Retroactivity

Retroactive application must be explicit.

```text
RetroactivityPolicy {
    allowed
    scope
    effective_period
}
```

No rule is retroactive merely because a newer version exists.

---

# 23. Statute

```text
Statute {
    title
    jurisdiction
    provisions
    effective_date
    amendments
}
```

A statute can compile into a set of `LegalRule` objects.

---

# 24. Regulation

```text
Regulation {
    authority
    parent_law
    provisions
    applicability
}
```

The compiler should validate that the regulation's declared authority exists.

---

# 25. Delegated Authority

```text
DelegatedAuthority {
    delegator
    delegate
    powers
    limitations
    effective_period
    revocation
}
```

Delegation cannot exceed the authority of the delegator.

---

# 26. Authority Invariant

For an action:

```text
authorized(action)
```

must imply:

```text
authority_source.exists
authority_source.active
authority_scope.contains(action)
authority_subject.is_valid
```

An authority chain must be traceable.

---

# 27. Rights Hierarchy

Legal systems may define:

```text
RightPriority
RightConflict
RightLimitation
RightException
```

The runtime must not hard-code a universal hierarchy.

---

# 28. Rights Conflict

```text
RightsConflict {
    right_a
    right_b
    subject
    jurisdiction
    conflict_rule
    resolution
}
```

Resolution must reference an explicit legal rule or adjudicative decision.

---

# 29. Contract

671 already provides economic contracts.

672 adds legal semantics:

```text
LegalContract {
    parties
    offer
    acceptance
    consideration?
    obligations
    conditions
    representations
    warranties
    remedies
    governing_law
    jurisdiction
    signatures
    status
}
```

Thus:

```text
671 = economic execution
672 = legal meaning/enforceability
```

---

# 30. Contract Lifecycle

```text
DRAFT
→ OFFERED
→ ACCEPTED
→ EXECUTED
→ ACTIVE
→ AMENDED
→ SUSPENDED
→ BREACHED
→ CURED
→ TERMINATED
→ EXPIRED
```

---

# 31. Contract Formation

Possible events:

```text
Offer
CounterOffer
Acceptance
Rejection
Revocation
Expiration
Signature
Ratification
```

Formation rules are jurisdiction-specific.

---

# 32. Electronic Signature

```text
LegalSignature {
    signer
    credential
    timestamp
    signature
    verification
    legal_basis
}
```

Integration:

```text
610 Cryptography
627 Identity
603 Capability
```

---

# 33. Contract Amendment

An amendment must preserve:

```text
original_contract
amendment
effective_date
authorized_parties
changed_terms
```

No destructive replacement of historical contract state.

---

# 34. Contract Breach

```text
Breach {
    contract
    party
    obligation
    event
    timestamp
    severity
}
```

Potential remedies:

```text
CURE
DAMAGES
SPECIFIC_PERFORMANCE
TERMINATION
RESTITUTION
OTHER
```

The actual remedy is determined by applicable rules or adjudication.

---

# 35. License

```text
License {
    issuer
    holder
    subject
    permissions
    conditions
    jurisdiction
    effective_period
    revocation
}
```

Licenses may apply to:

```text
software
property
business activity
professional activity
resource usage
data
intellectual property
```

---

# 36. Permit

```text
Permit {
    authority
    holder
    activity
    location?
    conditions
    validity
}
```

Permit issuance is authority-gated.

---

# 37. Compliance

```text
ComplianceCheck {
    subject
    rule
    facts
    result
    evidence
    timestamp
}
```

Results:

```text
COMPLIANT
NON_COMPLIANT
UNKNOWN
NOT_APPLICABLE
PENDING
```

`UNKNOWN` must never silently become `COMPLIANT`.

---

# 38. Compliance Plan

```text
CompliancePlan {
    requirements
    controls
    evidence_sources
    schedule
    responsible_parties
}
```

---

# 39. Regulatory Obligation

```text
RegulatoryObligation {
    subject
    authority
    rule
    requirement
    deadline
    reporting
}
```

---

# 40. Legal Fact

```text
LegalFact {
    proposition
    source
    evidence
    timestamp
    confidence?
}
```

A legal fact can be:

```text
ASSERTED
ADMITTED
ESTABLISHED
DISPUTED
UNKNOWN
```

---

# 41. Evidence

```text
Evidence {
    id
    source
    content
    provenance
    collection_method
    timestamp
    integrity
    admissibility?
}
```

The runtime must separate:

```text
evidence_exists
evidence_is_authentic
evidence_is_admissible
evidence_proves_fact
```

---

# 42. Evidence Chain

```text
EvidenceProvenance {
    source
    collector
    timestamp
    transformation[]
    hash
    custody[]
}
```

Integration with 602 and 610.

---

# 43. Chain of Custody

```text
CustodyEvent {
    evidence
    holder
    transfer
    timestamp
    authorization
}
```

The chain must be append-only after finalization.

---

# 44. Legal Argument

```text
LegalArgument {
    premises
    evidence
    rules
    reasoning
    conclusion
}
```

Arguments are not automatically accepted.

---

# 45. Legal Interpretation

```text
Interpretation {
    rule
    method
    context
    source
    interpreter
    result
}
```

Possible methods:

```text
TEXTUAL
STRUCTURAL
PURPOSIVE
HISTORICAL
PRECEDENTIAL
CUSTOMARY
SYSTEMATIC
CUSTOM
```

The jurisdiction decides which interpretation methods are authoritative.

---

# 46. Precedent

```text
Precedent {
    decision
    authority_level
    binding_scope
    jurisdiction
    subject_domain
}
```

A precedent may be:

```text
BINDING
PERSUASIVE
NON_BINDING
```

---

# 47. Court

```text
Court {
    id
    jurisdiction
    subject_matter
    territorial_scope
    judges
    registry
    procedures
}
```

---

# 48. Tribunal

```text
Tribunal {
    id
    jurisdiction
    subject_domain
    members
    procedures
}
```

---

# 49. Court Hierarchy

```text
CourtSystem {
    courts
    levels
    appellate_relationships
    jurisdiction_rules
}
```

The hierarchy is jurisdiction-configurable.

---

# 50. Judge / Adjudicator

```text
Adjudicator {
    identity
    authority
    jurisdiction
    qualifications
    assignment
}
```

Axiom must not infer competence, impartiality or legitimacy from software representation.

---

# 51. Case

```text
LegalCase {
    id
    jurisdiction
    parties
    claims
    defenses
    evidence
    issues
    procedure
    status
}
```

---

# 52. Case Lifecycle

```text
FILED
→ ACCEPTED
→ SERVED
→ RESPONSE
→ DISCOVERY
→ HEARING
→ DELIBERATION
→ DECISION
→ APPEAL
→ FINAL
→ ENFORCEMENT
→ CLOSED
```

Some procedures may omit stages.

---

# 53. Filing

```text
CaseFiling {
    filer
    case
    document
    timestamp
    signature
}
```

---

# 54. Service

```text
LegalService {
    recipient
    document
    method
    timestamp
    status
}
```

Service status:

```text
DELIVERED
ACKNOWLEDGED
REFUSED
FAILED
UNKNOWN
```

---

# 55. Discovery

```text
DiscoveryRequest {
    requesting_party
    responding_party
    scope
    deadline
    objection
}
```

Discovery rules are jurisdiction-specific.

---

# 56. Hearing

```text
Hearing {
    case
    participants
    date
    procedure
    evidence
    transcript
}
```

---

# 57. Judgment

```text
Judgment {
    case
    findings
    conclusions
    orders
    remedies
    authority
    effective_date
}
```

A judgment must retain its legal basis.

---

# 58. Decision vs Judgment

```text
Decision
Judgment
Order
Opinion
Finding
```

must be separate objects.

A procedural order does not necessarily resolve the merits.

---

# 59. Appeal

```text
Appeal {
    source_decision
    appellant
    grounds
    requested_relief
    reviewing_body
}
```

Possible outcomes:

```text
AFFIRM
REVERSE
REMAND
MODIFY
DISMISS
OTHER
```

These are procedural result types, not normative rankings.

---

# 60. Remand

```text
Remand {
    source_decision
    destination
    instructions
    scope
}
```

---

# 61. Alternative Dispute Resolution

Supported:

```text
Mediation
Arbitration
Negotiation
Conciliation
```

---

# 62. Mediation

```text
MediationCase {
    parties
    mediator
    issues
    proposals
    agreement?
}
```

A mediator does not automatically possess adjudicative authority.

---

# 63. Arbitration

```text
ArbitrationCase {
    parties
    arbitrator
    agreement
    issues
    evidence
    award
}
```

The legal effect of an award is jurisdiction-defined.

---

# 64. Arbitration Award

```text
ArbitrationAward {
    findings
    obligations
    remedies
    jurisdiction
    finality
}
```

---

# 65. Negotiated Settlement

```text
Settlement {
    parties
    claims
    obligations
    releases
    conditions
    signatures
}
```

Settlement is distinct from adjudication.

---

# 66. Enforcement

```text
EnforcementOrder {
    source
    target
    action
    authority
    deadline
    constraints
}
```

Enforcement requires explicit authority.

---

# 67. Enforcement Capability

The legal runtime must not directly acquire unrestricted system capabilities.

Instead:

```text
672 LegalOrder
    ↓
603 Capability Check
    ↓
Authorized Enforcement Adapter
    ↓
External Action
```

---

# 68. Administrative Enforcement

```text
AdministrativeAction {
    authority
    subject
    rule
    action
    review_right
}
```

---

# 69. Sanctions

The runtime may represent:

```text
Sanction
Penalty
Fine
Restriction
Suspension
Revocation
```

but cannot invent a sanction absent an applicable rule or authorized decision.

---

# 70. Criminal-Law Boundary

Where a jurisdiction models criminal law:

```text
Offense
Element
MensRea
Act
Defendant
Prosecution
Defense
Verdict
Sentence
```

may be represented.

The runtime must not infer guilt merely from anomaly, prediction, profiling or statistical correlation.

---

# 71. Presumption State

Legal systems may explicitly define:

```text
Presumed
NotPresumed
RebuttablePresumption
IrrebuttablePresumption
```

The compiler must not introduce a universal presumption rule.

---

# 72. Burden of Proof

```text
BurdenOfProof {
    party
    issue
    standard
}
```

Standards can be configured:

```text
CUSTOM
PREPONDERANCE
CLEAR_AND_CONVINCING
BEYOND_REASONABLE_DOUBT
OTHER
```

These are model values supplied by the jurisdiction.

---

# 73. Standard of Proof

```text
ProofStandard {
    threshold
    methodology
    jurisdiction
}
```

Numerical probability must not automatically be equated with a legal proof standard.

---

# 74. Evidence Evaluation

The system may compute:

```text
EvidenceWeight
Consistency
Corroboration
ReliabilityEstimate
```

but must distinguish these from legal admissibility and judicial findings.

---

# 75. AI Legal Analysis

AI may perform:

```text
search_rules()
retrieve_precedent()
summarize_case()
check_consistency()
find_missing_evidence()
simulate_arguments()
```

but AI analysis is not automatically a legal judgment.

---

# 76. AI Adjudication Boundary

An AI system may be designated as an adjudicator only if the applicable authority explicitly grants that role.

Even then:

```text
jurisdiction
procedure
appeal
audit
human oversight
```

must remain explicit where required.

---

# 77. Human Oversight

665 integrates:

```text
HumanReview
HumanApproval
Appeal
Override
Escalation
Recusal
```

The legal runtime must support mandatory human review.

---

# 78. Recusal

```text
Recusal {
    adjudicator
    case
    reason
    authority
}
```

The runtime must allow conflicts of interest to be declared.

---

# 79. Legal Conflict of Interest

```text
ConflictOfInterest {
    actor
    relationship
    case
    disclosure
    resolution
}
```

The system records conflicts; it does not independently determine personal motives.

---

# 80. Legal Deadlines

```text
LegalDeadline {
    start
    duration
    calendar
    extensions
    suspension_rules
}
```

Deadline calculation must be deterministic.

---

# 81. Limitation Period

```text
LimitationPeriod {
    offense_or_claim
    duration
    start_rule
    tolling_rules
}
```

---

# 82. Legal Time

Support:

```text
EffectiveDate
PublicationDate
FilingDate
HearingDate
DecisionDate
AppealDeadline
EnforcementDate
ExpiryDate
```

---

# 83. Legal Document

```text
LegalDocument {
    id
    type
    content
    language
    version
    signatures
    provenance
}
```

Integration with 617 for multilingual legal text.

---

# 84. Legal Language

The runtime should support:

- UTF-8;
- multilingual statutes;
- canonical language;
- translated versions;
- terminology dictionaries;
- legal definitions;
- cross-language citations.

Translations must preserve the distinction between:

```text
official_text
translation
machine_translation
interpretation
```

---

# 85. Legal Definition

```text
LegalDefinition {
    term
    meaning
    jurisdiction
    scope
    effective_period
}
```

Definitions may override ordinary-language meanings within a declared legal context.

---

# 86. Legal Ontology

```text
LegalOntology {
    concepts
    relations
    definitions
    jurisdiction
}
```

Integration with 645.

---

# 87. Legal Knowledge Graph

Nodes:

```text
Person
Organization
Right
Duty
Rule
Contract
Case
Court
Decision
Asset
Jurisdiction
```

Edges:

```text
OWNS
OWES
REPRESENTS
GOVERNS
LICENSES
CONTRACTS_WITH
CLAIMS
APPEALS
CITES
SUPERSEDES
```

---

# 88. Legal Record

```text
LegalRecord {
    subject
    event
    source
    authority
    timestamp
    version
}
```

Historical legal records must be immutable after finalization.

---

# 89. Legal Registry

```text
LegalRegistry {
    rules
    contracts
    licenses
    cases
    judgments
    entities
    authorities
}
```

---

# 90. Legal Entity Registry

```text
LegalEntityRegistry {
    entities
    statuses
    representatives
    jurisdiction
}
```

---

# 91. Corporate Legal Lifecycle

For jurisdictions that support organizational legal entities:

```text
FORMATION
→ REGISTRATION
→ ACTIVE
→ SUSPENDED
→ RESTRUCTURED
→ DISSOLVED
→ ARCHIVED
```

671 handles economic activity.

672 handles legal status.

667 handles organizational structure.

---

# 92. Property Rights

```text
PropertyRight {
    holder
    object
    scope
    jurisdiction
}
```

Property object may be:

```text
physical
digital
intellectual
financial
land
resource
custom
```

Physical resource state remains in 669.

---

# 93. Intellectual Property

Optional profiles:

```text
Copyright
Patent
Trademark
TradeSecret
License
```

The runtime models legal rules, not universal policy judgments about intellectual-property design.

---

# 94. Data Rights

Integration with 640.

```text
DataRight {
    subject
    data
    operation
    purpose
    scope
    expiration
}
```

Examples:

```text
ACCESS
CORRECT
DELETE
PROCESS
TRANSFER
RESTRICT
```

Availability depends on jurisdiction.

---

# 95. Privacy

672 can represent legal privacy obligations.

Actual technical enforcement uses:

```text
603
610
640
```

---

# 96. Legal Compliance With Economic Systems

671 may generate:

```text
Transaction
Payment
Invoice
Loan
Trade
```

672 can determine whether those events satisfy declared legal rules.

Example:

```text
671 transaction
        ↓
672 compliance check
        ↓
compliant / non-compliant / unknown
```

---

# 97. Labor Law Boundary

670 models:

```text
worker
skill
employment
labor capacity
```

671 models:

```text
wage
contract payment
labor-market transaction
```

672 can model:

```text
employment rights
contractual obligations
working-time rules
labor protections
dispute procedures
```

---

# 98. Environmental Law Boundary

669 models:

```text
emission
pollution
resource
environment
```

672 can represent:

```text
permit
limit
reporting obligation
environmental violation
remediation order
```

---

# 99. Regulatory Monitoring

```text
RegulatoryMonitor {
    rules
    observations
    checks
    alerts
}
```

An alert is not a legal finding.

---

# 100. Violation

```text
LegalViolation {
    rule
    subject
    event
    facts
    evidence
    status
}
```

Statuses:

```text
SUSPECTED
ALLEGED
UNDER_REVIEW
ESTABLISHED
DISMISSED
REVERSED
```

The runtime must not collapse `SUSPECTED` into `ESTABLISHED`.

---

# 101. Investigation

```text
Investigation {
    authority
    subject
    scope
    evidence
    status
}
```

Investigation capabilities require explicit authority.

---

# 102. Search / Inspection Order

```text
InspectionOrder {
    authority
    scope
    target
    duration
    limitations
}
```

Technical access is separately enforced by 603.

---

# 103. Seizure / Asset Freeze

Where authorized:

```text
AssetRestriction {
    asset
    authority
    scope
    duration
    review
}
```

672 records the legal restriction.

671/669 enforce the economic/physical consequences through authorized adapters.

---

# 104. Appeals and Review

Every adjudication framework should be able to declare:

```text
appeal_allowed
review_body
deadline
grounds
standard
effect
```

---

# 105. Finality

A legal decision may be:

```text
INTERLOCUTORY
APPEALABLE
FINAL
VOID
VACATED
REVERSED
```

Finality is jurisdiction-specific.

---

# 106. Enforcement Status

```text
PENDING
ACTIVE
PARTIALLY_EXECUTED
COMPLETED
SUSPENDED
VACATED
EXPIRED
```

---

# 107. Legal Settlement

A settlement can close disputes without establishing all disputed facts.

Therefore:

```text
settlement != adjudicated_truth
```

must be represented explicitly.

---

# 108. Alternative Legal Outcomes

A case can terminate as:

```text
JUDGMENT
SETTLEMENT
DISMISSAL
WITHDRAWAL
DEFAULT
MEDIATED_AGREEMENT
ARBITRATION_AWARD
OTHER
```

---

# 109. Legal Simulation

672 supports simulation of:

```text
rule_changes
contract_scenarios
regulatory_effects
court_procedure
jurisdiction_conflicts
compliance
institutional processes
```

Simulation results are not actual legal decisions.

---

# 110. Legal Digital Twin

A legal digital twin may combine:

```text
667 institutions
668 governance
671 economy
670 society
669 physical systems
672 legal rules
```

The result must distinguish:

```text
actual_legal_state
modeled_legal_state
simulated_legal_state
forecast_legal_state
```

---

# 111. Rule Engine

Core evaluator:

```text
LegalRuleEngine {
    facts
    rules
    jurisdiction
    time
    context
}
```

Output:

```text
RuleResult {
    applicable
    satisfied
    effects
    explanations
    provenance
}
```

---

# 112. Rule Evaluation

Rules should support:

```text
AND
OR
NOT
IF
THEN
UNLESS
EXCEPT
BEFORE
AFTER
DURING
UNTIL
```

---

# 113. Rule Priority

```text
RulePriority {
    source_priority
    jurisdiction_priority
    temporal_priority
    specificity
}
```

Priority must be explicit.

---

# 114. Rule Conflict

```text
RuleConflict {
    rule_a
    rule_b
    conflict_type
    resolution_method
}
```

Unresolved conflicts must produce:

```text
CONFLICT_UNRESOLVED
```

rather than silently choosing one.

---

# 115. Explainability

Every automated legal evaluation should be able to provide:

```text
applicable_rules
facts_used
exceptions
precedents
authority_chain
effective_dates
result
```

This is an explanation trace, not a claim that the reasoning is morally correct.

---

# 116. Deterministic Rule Evaluation

Given identical:

```text
rules
facts
jurisdiction
time
configuration
```

a deterministic rule engine must produce equivalent output.

---

# 117. Legal Event Sourcing

Events:

```text
RuleAdopted
RuleAmended
ContractSigned
LicenseIssued
CaseFiled
EvidenceSubmitted
HearingHeld
JudgmentIssued
AppealFiled
JudgmentReversed
EnforcementExecuted
```

can form an immutable legal event log.

---

# 118. Legal State Reconstruction

```text
LegalState = Replay(LegalEvents)
```

The runtime must support:

```text
snapshot
replay
restore
audit
diff
```

---

# 119. Legal Diff

```text
LegalDiff {
    added_rules
    removed_rules
    changed_rules
    changed_rights
    changed_obligations
    changed_jurisdiction
}
```

Useful for legislative/regulatory version comparison.

---

# 120. Rule Migration

When a law changes:

```text
RuleMigration {
    old_version
    new_version
    transition_rules
    grandfathering
    exceptions
}
```

---

# 121. Grandfathering

Some jurisdictions preserve existing rights/contracts.

Represent:

```text
GrandfatherRule {
    affected_subjects
    previous_rule
    continuation
    expiration
}
```

---

# 122. Emergency Legal Powers

```text
EmergencyAuthority {
    issuer
    scope
    powers
    start
    expiry
    review
}
```

Mandatory constraints:

```text
time_limited
scope_limited
auditable
reviewable
revocable
```

No emergency flag may automatically bypass:

```text
603 security
664 safety
665 human control
```

---

# 123. Constitutional / Higher-Order Rules

Some legal systems contain rules controlling how ordinary rules may be created.

Represent:

```text
MetaRule
ConstitutionalRule
AuthorityRule
AmendmentRule
```

672 may execute these formally but does not decide their legitimacy.

---

# 124. Legislative Process

Optional profile:

```text
Proposal
Review
Amendment
Vote
Adoption
Publication
EffectiveDate
```

This is a procedural model.

It does not grant legislative authority automatically.

---

# 125. Regulatory Process

```text
RegulationProposal
Consultation
Review
Adoption
Publication
Effective
Amendment
Repeal
```

---

# 126. Public Participation

Where supported:

```text
PublicComment
Petition
Consultation
Hearing
Submission
```

These are records/procedures, not automatic policy outcomes.

---

# 127. Legal Representation

```text
Representative {
    principal
    agent
    authority
    scope
    expiration
}
```

Representation must not exceed delegated authority.

---

# 128. Power of Attorney

```text
PowerOfAttorney {
    principal
    representative
    powers
    limitations
    effective_period
}
```

---

# 129. Guardianship / Fiduciary Role

Optional:

```text
Guardian
Trustee
Fiduciary
Executor
Administrator
```

All authority is scoped.

---

# 130. Estate

```text
Estate {
    assets
    liabilities
    beneficiaries
    administrator
}
```

Integration with 671 for economic assets.

---

# 131. Succession

```text
SuccessionRule
Beneficiary
InheritanceClaim
Transfer
```

Jurisdiction-specific.

---

# 132. Legal Asset State

A property may simultaneously have:

```text
physical_state
economic_state
legal_state
```

Example:

```text
physical owner = A
economic owner = B
legal restriction = C
custodian = D
```

This is valid when explicitly represented.

---

# 133. Legal Encumbrance

```text
Encumbrance {
    asset
    holder
    type
    priority
    conditions
}
```

Examples:

```text
LIEN
MORTGAGE
EASEMENT
PLEDGE
RESTRICTION
```

---

# 134. Legal Priority

Multiple claims on an asset require:

```text
ClaimPriority {
    claim
    rank
    basis
    jurisdiction
}
```

No implicit priority.

---

# 135. Insolvency Integration

671 supplies:

```text
debt
assets
liabilities
creditors
```

672 supplies:

```text
legal proceedings
priority
claims
court orders
restructuring
```

---

# 136. Bankruptcy Estate

```text
BankruptcyCase {
    debtor
    assets
    creditors
    claims
    priorities
    administrator
    plan
}
```

---

# 137. Regulatory Sandbox

672 supports controlled experimentation:

```text
LegalSandbox {
    jurisdiction
    rules
    exemptions
    duration
    participants
    reporting
}
```

Sandbox exemptions must be explicit and time-limited.

---

# 138. Legal Interoperability

Cross-jurisdiction systems may use:

```text
MutualRecognition
LegalBridge
CredentialRecognition
JudgmentRecognition
ContractRecognition
```

Integration with 668.

---

# 139. Treaty Boundary

Treaties and inter-organizational agreements are owned by 668.

672 interprets their legal effects when explicitly declared.

---

# 140. International Legal System

Optional:

```text
InternationalJurisdiction
Treaty
Convention
CrossBorderClaim
Recognition
Extradition
CrossBorderEnforcement
```

No universal international authority is assumed.

---

# 141. Legal Data Exchange

Canonical formats:

```text
.axlaw
.axrule
.axlegal
.axcontract
.axlicense
.axpermit
.axcase
.axjudgment
.axevidence
.axjurisdiction
.axcourt
.axregulation
.axcompliance
.axrights
```

All are versioned.

---

# 142. Annotations

```text
@legal
@jurisdiction
@legal_entity
@legal_identity
@right
@duty
@obligation
@claim
@liability
@rule
@statute
@regulation
@contract
@license
@permit
@compliance
@violation
@evidence
@case
@court
@tribunal
@judge
@decision
@judgment
@appeal
@mediation
@arbitration
@settlement
@enforcement
@precedent
@legal_document
@legal_definition
@legal_ontology
@legal_simulation
```

---

# 143. Compiler IR

Required IR operations:

```text
LegalIdentityCreate
LegalEntityCreate
LegalStatusSet

JurisdictionCreate
JurisdictionRuleDefine
JurisdictionBoundaryDefine

LegalSourceCreate
LegalRuleDefine
LegalRuleActivate
LegalRuleSuspend
LegalRuleAmend
LegalRuleRepeal

RightCreate
RightGrant
RightLimit
RightSuspend
RightRevoke

DutyCreate
ObligationCreate
ClaimCreate
LiabilityCreate

AuthorityCreate
AuthorityDelegate
AuthorityRevoke

ContractCreate
ContractOffer
ContractAccept
ContractSign
ContractAmend
ContractTerminate

LicenseCreate
LicenseRenew
LicenseSuspend
LicenseRevoke

PermitCreate
PermitRenew
PermitSuspend
PermitRevoke

ComplianceCheck
ViolationCreate
InvestigationCreate

EvidenceCreate
EvidenceTransfer
EvidenceVerify
EvidenceAdmit
EvidenceReject

CaseCreate
CaseFile
CaseServe
CaseRespond
DiscoveryRequest
HearingCreate
HearingClose

DecisionCreate
JudgmentCreate
OrderCreate

AppealCreate
AppealReview
RemandCreate

MediationCreate
ArbitrationCreate
SettlementCreate

EnforcementCreate
EnforcementExecute
EnforcementSuspend
EnforcementReverse

LegalSimulationCreate
LegalSimulationStep
LegalSimulationRun
LegalSimulationCheckpoint
LegalSimulationRestore

LegalAudit
LegalReconcile
LegalDiff
LegalStateSnapshot
LegalStateRestore
```

---

# 144. CLI

```text
axiom law list
axiom law inspect
axiom law compile
axiom law validate
axiom law diff

axiom jurisdiction list
axiom jurisdiction inspect
axiom jurisdiction rules

axiom legal-entity list
axiom legal-entity create
axiom legal-entity inspect
axiom legal-entity status

axiom rights list
axiom rights inspect
axiom rights grant
axiom rights revoke

axiom contract list
axiom contract create
axiom contract inspect
axiom contract sign
axiom contract amend
axiom contract terminate

axiom license list
axiom license create
axiom license suspend
axiom license revoke

axiom permit list
axiom permit create
axiom permit inspect

axiom compliance check
axiom compliance report

axiom case list
axiom case create
axiom case inspect
axiom case file
axiom case serve
axiom case evidence
axiom case hearing

axiom court list
axiom court inspect

axiom judgment list
axiom judgment inspect
axiom judgment issue

axiom appeal create
axiom appeal inspect

axiom mediation create
axiom arbitration create
axiom settlement create

axiom enforcement list
axiom enforcement inspect
axiom enforcement execute

axiom law simulation create
axiom law simulation run
axiom law simulation step
axiom law simulation checkpoint
axiom law simulation restore

axiom law audit
axiom law diff
axiom law reconcile
```

---

# 145. Example Axiom Syntax

```text
@jurisdiction
jurisdiction ExampleJurisdiction {
    name = "Example"
}
```

```text
@legal
rule PermitRequired {
    jurisdiction = ExampleJurisdiction

    when activity.type == "regulated"
    unless activity.permit.valid

    effect violation("permit_required")
}
```

---

# 146. Contract Example

```text
@contract
contract SupplyAgreement {
    party Buyer
    party Seller

    obligation Seller.deliver(
        Steel,
        100.tonne
    )

    obligation Buyer.pay(
        1500000.USD
    )

    governing_law = ExampleJurisdiction
}
```

---

# 147. Rights Example

```text
@right
right DataAccess {
    holder = Person
    object = PersonalData
    action = ACCESS
}
```

The actual existence and scope of the right depends on the applicable legal framework.

---

# 148. Compliance Example

```text
check compliance FactoryA {
    rule = EmissionLimit
    facts = [
        FactoryA.emission,
        FactoryA.permit
    ]
}
```

Possible result:

```text
COMPLIANT
NON_COMPLIANT
UNKNOWN
```

---

# 149. Case Example

```text
case ContractDispute {
    claimant = Buyer
    respondent = Seller

    claim {
        basis = SupplyAgreement
        allegation = non_delivery
    }
}
```

---

# 150. Legal Simulation Example

```text
simulation regulation_change {
    jurisdiction = ExampleJurisdiction

    scenario {
        replace EmissionLimitV1
        with EmissionLimitV2
    }

    run 10.years
}
```

The result is a scenario analysis, not an enacted law.

---

# 151. Rule Compilation

Legal source:

```text
human-readable legal document
```

can compile into:

```text
LegalSource
 ↓
LegalDefinition
 ↓
LegalRule
 ↓
RuleIR
 ↓
ExecutableRule
```

Ambiguous provisions must be marked unresolved rather than silently converted into arbitrary executable semantics.

---

# 152. Ambiguity

```text
LegalAmbiguity {
    provision
    interpretations[]
    unresolved
}
```

The compiler may report:

```text
AMBIGUOUS_RULE
MISSING_DEFINITION
CONFLICTING_RULE
MISSING_AUTHORITY
```

---

# 153. Human Legal Interpretation

Human interpretation may resolve ambiguity:

```text
InterpretationDecision {
    interpreter
    authority
    provision
    selected_interpretation
    reasoning
}
```

The system records the decision rather than pretending ambiguity never existed.

---

# 154. AI Legal Interpretation

AI may propose interpretations:

```text
AIInterpretationProposal
```

but proposed interpretation ≠ authoritative interpretation.

Authority must be explicitly supplied.

---

# 155. Legal Reasoning Trace

```text
LegalReasoningTrace {
    facts
    rules
    interpretations
    precedents
    exceptions
    authority
    conclusion
}
```

This is essential for auditability.

---

# 156. Legal Model Provenance

Every automated legal result retains:

```text
jurisdiction_version
rule_version
fact_version
evidence_version
interpretation_version
procedure_version
runtime_version
timestamp
```

---

# 157. Distributed Legal State

For distributed institutions:

```text
LegalEventLog
LegalSnapshot
LegalConsensus
LegalReplication
```

may be used.

But legal finality must be explicitly declared.

---

# 158. Strong Consistency

Operations requiring authoritative finality may use:

```text
STRONG_CONSISTENCY
```

Examples:

```text
final judgment
legal entity registration
license issuance
court order
final enforcement state
```

---

# 159. Eventual Consistency

Read-only replicated legal data may use:

```text
EVENTUAL_CONSISTENCY
```

but clients must be able to identify stale state.

---

# 160. Legal Conflict Resolution

Distributed legal systems require:

```text
authority
jurisdiction
version
precedence
consensus
```

A network partition must never cause two incompatible legal final states to be silently accepted as one.

---

# 161. Legal State Hash

```text
legal_state_hash
```

can verify identical state across nodes.

---

# 162. Legal Document Hash

```text
document_hash
```

ensures that the exact legal text used for execution can be identified.

---

# 163. Digital Signature

Legal artifacts may use:

```text
signature
certificate
timestamp
identity
authority
```

with cryptographic validation delegated to 610.

---

# 164. Access Control

Capabilities:

```text
law.read
law.publish
law.amend
case.read
case.file
evidence.submit
evidence.read
judgment.issue
appeal.file
enforcement.execute
license.issue
permit.issue
```

Each requires explicit authority.

---

# 165. Privacy

Legal records may contain:

- identity data;
- health data;
- financial data;
- family information;
- biometric data;
- evidence;
- confidential communications.

Default handling must therefore be restrictive.

---

# 166. Privacy-Preserving Court Records

Support:

```text
redaction
sealed_record
restricted_party
pseudonymization
access_log
disclosure_order
```

---

# 167. Evidence Privacy

Evidence access can be scoped by:

```text
case
party
role
authority
purpose
time
```

---

# 168. Legal Security

Integrations:

```text
603 capability security
610 cryptography
627 identity
633 audit/observability
640 privacy
```

---

# 169. Security Boundary

672 must never provide:

```text
unrestricted filesystem access
unrestricted credential access
unrestricted personal-data access
unrestricted enforcement capability
```

merely because a user has legal authority represented in a document.

Technical authorization remains separately enforced.

---

# 170. Enforcement Adapter

```text
LegalEnforcementAdapter {
    legal_order
    capability
    target_system
    execution
    result
}
```

Example:

```text
672 judgment
→ 603 capability
→ 671 asset restriction
```

---

# 171. Economic Enforcement

671 may execute:

```text
payment
asset transfer
account restriction
contract settlement
```

when legally authorized.

---

# 172. Physical Enforcement

669 may execute physical/infrastructure operations only through explicitly authorized interfaces.

672 does not directly control physical systems.

---

# 173. Organization Enforcement

667 handles organizational state.

672 provides legal orders affecting it.

---

# 174. Human Enforcement

A legal decision affecting a human must respect:

```text
665 human oversight
664 safety
603 capability
```

and applicable legal safeguards.

---

# 175. No Automatic Human Classification

672 must not create authoritative primitives such as:

```text
HumanWorth
CitizenValue
DeservingnessScore
CriminalProbabilityAsGuilt
PoliticalLoyaltyScore
```

A statistical prediction cannot itself establish legal status.

---

# 176. Presumption Against Automated Guilt

An anomaly detector can emit:

```text
RiskSignal
```

not:

```text
Guilty
```

A legal finding requires the applicable procedure and authority.

---

# 177. Legal AI Safety

AI systems working with legal data must expose:

```text
model_id
model_version
data_sources
confidence?
uncertainty?
retrieved_rules
human_review_status
```

---

# 178. High-Impact Legal Actions

Examples:

```text
license_revocation
asset_freeze
legal_status_change
enforcement
sanction
court_judgment
```

can be configured to require human approval.

---

# 179. Automated Legal Actions

Low-risk deterministic operations may be automated:

```text
deadline_calculation
document_validation
rule_lookup
registry_consistency_check
fee_calculation
contract_schema_validation
```

provided the authority framework permits it.

---

# 180. Legal Automation Levels

```text
LEVEL_0_INFORMATION
LEVEL_1_ASSISTANCE
LEVEL_2_RECOMMENDATION
LEVEL_3_AUTOMATED_PREPARATION
LEVEL_4_AUTOMATED_EXECUTION
LEVEL_5_AUTHORITY_BOUND_EXECUTION
```

Each application declares its permitted level.

---

# 181. Audit

Every authoritative action should record:

```text
actor
authority
rule
case
input
output
timestamp
approval
execution
```

---

# 182. Legal Audit Trail

Audit records must be:

```text
append_only
tamper_evident
timestamped
queryable
versioned
```

---

# 183. Legal Reconciliation

```text
LegalReconciliation {
    registry_state
    court_state
    contract_state
    enforcement_state
    discrepancies
}
```

---

# 184. Registry Consistency

Examples:

```text
registered_entity exists
active_license references valid entity
judgment references valid case
enforcement references valid judgment
appeal references valid decision
```

---

# 185. Orphan Prevention

The compiler/runtime should detect:

```text
orphan_license
orphan_judgment
orphan_enforcement
orphan_contract
orphan_authority
```

---

# 186. Legal State Machine Validation

A transition such as:

```text
FINAL_JUDGMENT → DRAFT
```

must be rejected unless an explicit legal procedure authorizes the transition.

---

# 187. Immutable Final Records

Final:

```text
judgment
court_order
settlement
legal_entity_registration
```

must not be destructively modified.

Corrections use:

```text
amendment
vacatur
reversal
supersession
correction_record
```

---

# 188. Legal Document Storage

Use 611/612/613 for:

```text
document storage
serialization
compression
archival
content addressing
```

672 owns legal semantics, not generic storage.

---

# 189. Search

Integration with 641:

```text
legal_search
precedent_search
statute_search
contract_search
case_search
```

---

# 190. Legal Analytics

642 can compute:

```text
case statistics
rule usage
processing time
compliance rates
appeal rates
```

These analytics must not automatically become legal conclusions.

---

# 191. Legal Forecasting

A model may forecast:

```text
case_duration
regulatory_load
compliance_probability
```

Forecasts remain predictions.

---

# 192. Legal Causal Analysis

653 may evaluate:

```text
effect_of_rule_change
effect_of_procedure_change
```

The causal model and assumptions must be retained.

---

# 193. Legal Optimization

652 may optimize:

```text
court scheduling
resource allocation
case routing
administrative workload
```

The objective must be explicit.

The optimizer cannot redefine rights or legal standards.

---

# 194. Legal Simulation

648 supplies generic simulation infrastructure.

672 supplies:

```text
legal rules
procedure
jurisdiction
rights
obligations
cases
decisions
```

---

# 195. Scenario Comparison

The runtime may compare:

```text
RuleSet A
RuleSet B
RuleSet C
```

using explicit metrics.

It must not automatically label one legally or morally superior.

---

# 196. Legal Model Profiles

```text
AXLAW_NONE

AXLAW_CORE
AXLAW_IDENTITY
AXLAW_RIGHTS
AXLAW_DUTIES
AXLAW_AUTHORITY

AXLAW_RULES
AXLAW_STATUTES
AXLAW_REGULATIONS
AXLAW_CONTRACTS

AXLAW_LICENSE
AXLAW_PERMIT
AXLAW_COMPLIANCE

AXLAW_EVIDENCE
AXLAW_CASE
AXLAW_COURT
AXLAW_TRIBUNAL
AXLAW_ADJUDICATION

AXLAW_APPEAL
AXLAW_MEDIATION
AXLAW_ARBITRATION
AXLAW_SETTLEMENT
AXLAW_ENFORCEMENT

AXLAW_PROPERTY
AXLAW_CORPORATE
AXLAW_LABOR
AXLAW_ENVIRONMENT
AXLAW_DATA
AXLAW_INTELLECTUAL_PROPERTY

AXLAW_DISTRIBUTED
AXLAW_CROSS_JURISDICTION
AXLAW_INTERNATIONAL

AXLAW_SIMULATION
AXLAW_AI
AXLAW_AUDIT

AXLAW_WASM
AXLAW_MOBILE
AXLAW_EDGE

AXLAW_FULL
```

Unused profiles must have zero runtime cost.

---

# 197. Compiler Optimization

Legal rule execution should support:

- constant propagation;
- predicate simplification;
- rule indexing;
- jurisdiction indexing;
- temporal indexing;
- fact caching;
- immutable rule tables;
- incremental evaluation;
- memoization;
- parallel independent rule evaluation.

---

# 198. Rule Index

Efficient lookup indexes:

```text
subject
jurisdiction
date
domain
rule_type
source
```

---

# 199. Incremental Legal Evaluation

If one fact changes:

```text
FactChanged
```

the engine should reevaluate only dependent rules where possible.

---

# 200. Deterministic Legal Execution

Identical:

```text
facts
rules
jurisdiction
time
configuration
```

must yield equivalent deterministic results.

---

# 201. Legal Computation Numeric Model

Support:

```text
integer
decimal
date
duration
percentage
quantity
currency
probability
interval
```

Probability must not be silently converted to legal proof.

---

# 202. Temporal Logic

Rules can use:

```text
before
after
during
until
within
for
since
```

Example:

```text
if filing_date within 30.days of decision
```

---

# 203. Legal Interval

```text
LegalInterval {
    start
    end
    inclusivity
}
```

---

# 204. Rule Dependency Graph

```text
RuleDependencyGraph {
    rules
    dependencies
}
```

Cycles should be detected.

---

# 205. Recursive Rules

Recursive legal rules are permitted only when:

```text
termination
resource_bound
cycle_detection
```

are defined.

---

# 206. Rule Engine Resource Limits

Untrusted rule sets must have:

```text
max_rules
max_depth
max_iterations
max_memory
max_runtime
```

Integration with 606.

---

# 207. Legal DSL

Axiom may expose a concise legal DSL:

```text
law Example {
    jurisdiction J

    rule Permit {
        when activity.type == Controlled
        requires activity.permit.valid
    }
}
```

The DSL compiles to the same core Legal IR.

---

# 208. Contract DSL

```text
contract Agreement {
    party A
    party B

    obligation A.pay(100.USD)
    obligation B.deliver(Item)

    condition delivery <= 30.days
}
```

---

# 209. Court Procedure DSL

```text
procedure CivilCase {
    file
    serve
    response
    hearing
    decision
    appeal
}
```

The procedure is declarative and jurisdiction-specific.

---

# 210. Legal Package

A legal package may contain:

```text
rules
definitions
jurisdictions
procedures
forms
contracts
schemas
tests
precedents
```

---

# 211. Legal Package Verification

Before activation:

```text
authority_check
reference_check
version_check
conflict_check
temporal_check
schema_check
test_suite
```

must pass according to the declared activation policy.

---

# 212. Formal Verification

Rules may optionally be verified using:

```text
SAT
SMT
constraint_solver
theorem_prover
model_checker
```

Integration with 654.

---

# 213. Legal Safety Properties

Examples:

```text
no_authority_escalation
no_rule_without_source
no_enforcement_without_order
no_finality_without_procedure
no_hidden_retroactivity
no_unauthorized_disclosure
no_duplicate_final_judgment
```

---

# 214. Legal Model Checking

The system can verify properties such as:

```text
Every enforcement action references a valid authority.
Every judgment references a valid case.
Every active rule has an effective period.
Every legal entity has a jurisdiction.
```

---

# 215. Formal Rights Verification

Where rights are formally represented:

```text
rights_non_conflict
authority_scope
temporal_validity
exception_consistency
```

can be mechanically checked.

---

# 216. Legal Testing

Target:

**≥ 4,500 tests**

Categories:

```text
identity
rights
duties
authority
jurisdiction
rules
statutes
regulations
contracts
licenses
permits
compliance
evidence
cases
courts
adjudication
appeals
mediation
arbitration
settlement
enforcement
privacy
security
distributed consistency
simulation
formal verification
AI integration
performance
WASM
ABI
```

---

# 217. Property-Based Tests

Required properties:

```text
authority_non_escalation
rule_temporal_consistency
contract_state_consistency
judgment_reference_integrity
appeal_reference_integrity
enforcement_reference_integrity
evidence_chain_integrity
immutable_final_records
jurisdiction_scope
rights_scope
delegation_scope
```

---

# 218. Fuzz Testing

Fuzz:

```text
legal rules
contracts
case filings
evidence graphs
jurisdiction conflicts
temporal rules
appeal chains
authority chains
distributed events
```

---

# 219. Failure Injection

Test:

```text
duplicate judgment
missing authority
expired license
stale rule
network partition
conflicting rule versions
corrupted evidence
duplicate filing
clock skew
partial enforcement
revoked authority
```

---

# 220. Recovery

Support:

```text
snapshot
restore
replay
audit
reconciliation
```

---

# 221. Performance Targets

Benchmark:

```text
rule evaluation/sec
fact insertion/sec
case query latency
registry lookup latency
contract validation
compliance evaluation
legal graph traversal
simulation speed
document verification
distributed synchronization
```

---

# 222. Memory Efficiency

Use:

- immutable rule tables;
- compact IDs;
- interned legal terms;
- structural sharing;
- arena allocation;
- compressed evidence indexes;
- copy-on-write snapshots.

---

# 223. Distributed Legal Runtime

Supported topologies:

```text
CENTRALIZED
FEDERATED
DISTRIBUTED
HIERARCHICAL
MESH
HYBRID
```

No mandatory central server.

---

# 224. WASM

Safe WASM profile supports:

```text
rule evaluation
contract validation
compliance simulation
legal document validation
legal model simulation
```

Actual court/enforcement actions remain capability-gated.

---

# 225. Mobile / Edge

Support:

```text
offline legal registry
cached rules
local validation
signed updates
incremental synchronization
```

---

# 226. Offline Rule Validation

A device may validate a previously synchronized rule set without network access.

It must report:

```text
rule_version
last_sync
staleness
signature_status
```

---

# 227. Stale Legal State

If a rule set is outdated:

```text
STALE
```

must be explicit.

The runtime must not claim current legal validity without current state.

---

# 228. AI Agent Integration

AI agents can:

```text
search_law()
analyze_contract()
retrieve_precedent()
prepare_case()
simulate_rule()
check_compliance()
draft_document()
```

They cannot silently:

```text
issue_judgment
grant_right
revoke_license
execute_enforcement
```

without corresponding authority.

---

# 229. AI Agent Legal Identity

An AI agent can possess:

```text
AgentIdentity
Credential
DelegatedAuthority
Role
```

but legal personhood remains jurisdiction-defined.

---

# 230. Delegated AI Authority

```text
AIAuthority {
    agent
    principal
    powers
    limitations
    expiry
    approval_policy
}
```

Delegation is bounded by the principal's authority.

---

# 231. AI Audit

Every authoritative AI action records:

```text
agent_id
model_id
authority_id
rule_versions
facts
action
approval
result
```

---

# 232. AI Uncertainty

If an AI legal analysis is uncertain:

```text
UNCERTAIN
```

must remain a first-class result.

The system must not convert uncertainty into legal certainty.

---

# 233. Human Review Queue

```text
LegalReviewQueue {
    case
    issue
    reason
    urgency
    evidence
    deadline
}
```

---

# 234. Escalation

```text
Escalation {
    source
    destination
    reason
    deadline
}
```

---

# 235. Legal Notification

```text
LegalNotification {
    recipient
    document
    deadline
    delivery
    acknowledgement
}
```

---

# 236. Accessibility

Legal systems should integrate with 618/619 for:

```text
accessible documents
screen readers
language support
IME
visual accessibility
```

---

# 237. Internationalization

Legal text supports:

```text
locale
language
legal_locale
jurisdiction_language
translation
```

The authoritative language must be explicitly identified.

---

# 238. Legal Translation

```text
LegalTranslation {
    source
    target
    translator
    method
    certification
}
```

Machine translation must not automatically become authoritative legal text.

---

# 239. Legal Terminology

```text
LegalTerm {
    canonical
    synonyms
    jurisdiction
    definition
}
```

---

# 240. Final Responsibility Map

```text
603  Capability / Security
610  Cryptography
617  Language / Unicode
627  Identity
628  Distributed Data
633  Observability / Audit
639  Policy / Authority
640  Privacy / Data Governance
641  Search
642  Analytics
645  Knowledge Graph
648  Generic Simulation
652  Optimization
653  Causal / Probabilistic Reasoning
654  Symbolic Reasoning
655  World Model
663  Evaluation
664  Safety
665  Human Oversight

667  Organization / Institution
668  Federation / Inter-Organization Governance
669  Physical / Resource / Infrastructure
670  Human / Social / Population
671  Economic / Market / Finance
672  Legal / Rights / Rules / Adjudication / Enforcement
```

---

# 241. Boundary Matrix

| Domain | Owner |
|---|---|
| Technical capability | 603 |
| Identity | 627 |
| Policy authority | 639 |
| Privacy | 640 |
| Organization | 667 |
| Federation | 668 |
| Physical resources | 669 |
| Human/social systems | 670 |
| Economic activity | 671 |
| Legal rules | 672 |
| Optimization | 652 |
| Causal analysis | 653 |
| Formal logic | 654 |
| Evaluation | 663 |
| Safety | 664 |
| Human control | 665 |

---

# 242. Non-Goals

672 does not define:

```text
a universal moral system
a universal constitution
a universal justice philosophy
a universal political system
a universal rights hierarchy
a universal punishment model
AI legal personhood
human economic worth
automatic political legitimacy
```

These remain external, jurisdictional, philosophical or governance-level concerns.

---

# 243. Final Contract

BOOTSTRAP-672 provides a native computational substrate for:

```text
legal identity
rights
duties
obligations
claims
liabilities
jurisdiction
laws
rules
regulations
contracts
licenses
permits
compliance
evidence
cases
courts
tribunals
adjudication
appeals
mediation
arbitration
settlement
judgments
enforcement
legal simulation
```

It guarantees:

```text
authority traceability
rule versioning
jurisdiction scoping
temporal validity
evidence provenance
procedural state
auditability
distributed consistency
privacy boundaries
human oversight hooks
AI authority boundaries
```

It must never silently:

```text
invent legal authority
invent rights
invent obligations
declare guilt from prediction
convert AI output into authoritative judgment
execute enforcement without authority
change final legal records destructively
hide rule conflicts
hide uncertainty
treat simulation as reality
treat technical capability as legal permission
treat legal permission as technical capability
```

---

# 244. Completion Criteria

```text
[✓] legal identity model
[✓] legal entity model
[✓] rights
[✓] duties
[✓] obligations
[✓] claims
[✓] liabilities
[✓] jurisdiction
[✓] authority
[✓] statutes
[✓] regulations
[✓] legal rules
[✓] rule versioning
[✓] contracts
[✓] licenses
[✓] permits
[✓] compliance
[✓] violations
[✓] evidence
[✓] chain of custody
[✓] cases
[✓] courts
[✓] tribunals
[✓] adjudication
[✓] judgments
[✓] appeals
[✓] mediation
[✓] arbitration
[✓] settlements
[✓] enforcement
[✓] property
[✓] corporate/legal entities
[✓] labor-law boundary
[✓] environmental-law boundary
[✓] data/privacy-law boundary
[✓] cross-jurisdiction operation
[✓] legal simulation
[✓] AI legal boundary
[✓] human oversight
[✓] compiler IR
[✓] CLI
[✓] profiles
[✓] distributed semantics
[✓] formal verification hooks
[✓] security/privacy architecture
[✓] testing architecture
[✓] performance architecture
[✓] responsibility boundaries
```

**BOOTSTRAP-672 — ARCHITECTURE COMPLETE.**

---

# 245. Next Architecture Frontier

Sau 672, Axiom hiện đã có một chuỗi civilization-scale substrate rất rộng:

```text
668  Federation / Inter-Organization
669  Physical / Infrastructure / Ecological Systems
670  Human / Social / Population Systems
671  Economy / Markets / Finance
672  Law / Rights / Legal Systems
```

Một lớp còn thiếu ở quy mô civilization là **public administration / government operations / civic services / taxation administration / elections and democratic procedures / public records / policy execution**.

Do đó task tiếp theo là:

**BOOTSTRAP-673 — Native AI Civilization-Scale Public Administration, Government Operations, Civic Services, Public Records, Tax Administration, Elections, Democratic Procedures & Policy Execution Runtime 5.0**

Lớp 673 sẽ phải giữ ranh giới rất rõ:

```text
639 = authority / policy
668 = federation governance
672 = law / legal validity / adjudication
673 = administrative execution / public services / civic procedures
671 = economic transactions / taxation flows
670 = population / human systems
665 = human oversight
```

Đặc biệt, **election/democratic procedures sẽ được thiết kế như cơ chế thủ tục và kiểm chứng**, không hard-code một hệ tư tưởng hay mô hình chính trị duy nhất.
:::

**BOOTSTRAP-672 đã hoàn tất.** Chuỗi tự động chuyển sang **BOOTSTRAP-673**.