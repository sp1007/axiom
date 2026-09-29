Tiếp tục chuỗi kiến trúc Axiom. Task kế tiếp là **BOOTSTRAP-667**, xây lớp tổ chức/thể chế bền vững phía trên cơ chế multi-agent của 666.

:::writing{variant="document" id="58317" title="AXIOM BOOTSTRAP-667 — Native AI Organization & Institutional Runtime 5.0"}

# BOOTSTRAP-667
## Native AI Organization & Institutional Runtime 5.0

**Tên đầy đủ:** Native AI Organization, Institution, Membership, Roles, Governance, Institutional Memory, Resource Allocation & Organizational Lifecycle Runtime

**Trạng thái:** SPECIFIED — COMPLETE

**Layer:** AI Organizational / Institutional Runtime

**Phụ thuộc chính:**

```text
603  Capability / Security Boundary
606  Resource Governance
608  Concurrency
620  Reactive State
623  Extension / Module Runtime
627  Distributed Identity
628  Distributed Data
629  Distributed Workflow
631  Distributed Service
633  Distributed Observability
637  Distributed Configuration / Policy
638  Distributed Secrets / Identity Rotation
639  Policy / Authority
643  AI Compute
644  AI Agent Runtime
647  AI Governance
650  AI Memory
651  AI Personalization
652  AI Planning
653  Probabilistic Reasoning
654  Symbolic Reasoning
655  World Model
657  Cognitive Executive
658  Social Intelligence
660  Self Model
661  Value / Goal / Motivation
663  Evaluation
664  Safety / Alignment
665  Human Oversight
666  Multi-Agent Society
```

**Mục tiêu kiểm thử:** ≥ 3,000 tests.

---

# 1. Mục đích

BOOTSTRAP-666 cung cấp khả năng để nhiều agent:

- phát hiện nhau;
- giao tiếp;
- chia sẻ nhiệm vụ;
- đấu thầu;
- thương lượng;
- ký contract;
- phối hợp;
- lập team;
- chia sẻ tri thức;
- hình thành collective;
- giải quyết nhiệm vụ chung.

Nhưng một **team** không đồng nghĩa với một **tổ chức**.

Một team có thể tồn tại vài phút.

Một tổ chức có thể tồn tại nhiều năm dù toàn bộ thành viên ban đầu đã biến mất.

667 bổ sung lớp persistent institution:

```text
Agent
   ↓
Team / Collective
   ↓
Organization
   ↓
Institution
   ↓
Federation
```

667 phải giải quyết:

```text
WHO BELONGS?
WHO HAS WHICH ROLE?
WHO MAY DECIDE?
WHO MAY SPEND?
WHO MAY DELEGATE?
WHAT RULES APPLY?
HOW ARE DECISIONS MADE?
HOW ARE LEADERS REPLACED?
HOW DOES MEMORY SURVIVE?
HOW DOES THE ORGANIZATION SURVIVE MEMBER FAILURE?
HOW CAN THE ORGANIZATION CHANGE?
HOW CAN IT SPLIT / MERGE / DISSOLVE?
```

---

# 2. Nguyên tắc kiến trúc

## 2.1 Organization không phải Agent

```text
Agent != Organization
```

Organization là một persistent computational entity.

Agent có thể:

```text
join organization
leave organization
represent organization
act for organization
hold organizational role
```

nhưng:

```text
Agent replacement
```

không được mặc định làm mất organization.

---

# 3. Organization không mặc định là legal person

Axiom không được tự động gán:

```text
legal personality
citizenship
human rights
corporate status
governmental authority
```

cho organization.

Đây là semantic layer bên ngoài runtime hoặc do policy/legal integration định nghĩa.

```text
Organization
    ≠
Legal Person
```

---

# 4. Organization Types

Runtime phải hỗ trợ:

```text
Organization
Institution
CompanyLikeOrganization
ResearchOrganization
ServiceOrganization
Community
ProjectOrganization
TaskForce
Department
Federation
Consortium
FoundationLikeOrganization
HumanAIOrganization
AgentOnlyOrganization
DistributedOrganization
TemporaryOrganization
PersistentInstitution
```

Không bắt buộc các loại trên là các native type riêng biệt.

Có thể biểu diễn bằng:

```text
OrganizationKind
```

---

# 5. Core Organizational Model

```text
Organization
 ├── Identity
 ├── Charter
 ├── Membership
 ├── Roles
 ├── Offices
 ├── Departments
 ├── Governance
 ├── Rules
 ├── Mandates
 ├── Budgets
 ├── Resources
 ├── InstitutionalMemory
 ├── Decisions
 ├── Contracts
 ├── Audits
 ├── Compliance
 ├── Succession
 ├── Continuity
 └── Lifecycle
```

---

# 6. Core Types

## 6.1 Identity

```text
OrganizationId
InstitutionId
OrganizationIdentity
InstitutionalIdentity
OrganizationVersion
OrganizationLineage
```

Identity phải tồn tại độc lập với member.

---

# 7. Membership

```text
Membership
Member
MembershipId
MembershipStatus
MembershipRole
MembershipPeriod
MembershipCondition
MembershipCredential
```

Lifecycle:

```text
INVITED
PENDING
ACTIVE
SUSPENDED
EXPIRED
TERMINATED
REVOKED
```

---

# 8. Member Types

Một organization có thể chứa:

```text
Human
Agent
Service
Device
SubOrganization
ExternalEntity
```

Ví dụ:

```text
organization "axiom-lab" {
    member human_user
    member agent_researcher
    member service_build
    member organization.security
}
```

---

# 9. Membership ≠ Capability

Một member có membership không đồng nghĩa với việc member có capability.

```text
Membership
    ↓
organizational relationship
```

trong khi:

```text
Capability
    ↓
what entity can technically do
```

Vì vậy:

```text
member.can("compile")
```

không được suy ra chỉ từ:

```text
member.belongs_to(org)
```

---

# 10. Membership ≠ Authority

Tương tự:

```text
Membership != Authority
```

Authority phải đến từ:

```text
Role
Mandate
Delegation
Policy
Office
Governance Decision
```

---

# 11. Role Model

```text
Role
RoleId
RoleDefinition
RoleBinding
RoleScope
RoleAuthority
RoleConstraint
RoleExpiration
```

Ví dụ:

```text
role Researcher
role Maintainer
role Treasurer
role SecurityOfficer
role Director
role Auditor
```

Role là organizational abstraction.

---

# 12. Role ≠ Capability

```text
Role != Capability
```

Ví dụ:

```text
role Treasurer
```

không tự tạo:

```text
Capability<TransferMoney>
```

Role chỉ có thể **authorize organizational actions** nếu policy cho phép và actor thực sự có capability tương ứng.

---

# 13. Office

Office biểu diễn một vị trí persistent trong organization:

```text
Office
OfficeId
OfficeHolder
OfficeTerm
OfficeAuthority
OfficeSuccession
```

Ví dụ:

```text
office Director
office ChiefEngineer
office SecurityOfficer
```

Khi agent rời organization:

```text
Office != destroyed
```

Office có thể được chuyển sang member khác.

---

# 14. Department

```text
Department
Division
Unit
Branch
WorkingGroup
```

Organization có thể có cây cấu trúc:

```text
Organization
 ├── Research
 │    ├── AI
 │    └── Compiler
 ├── Engineering
 ├── Security
 └── Operations
```

Sub-organization có identity riêng nhưng thuộc organization cha.

---

# 15. Committee / Board / Council

667 hỗ trợ các governance body:

```text
Committee
Board
Council
Panel
ReviewBoard
AuditCommittee
SecurityCouncil
```

Mỗi body có:

```text
members
roles
authority
scope
procedure
term
quorum
decision_rule
```

---

# 16. Charter

Charter là nền tảng constitution-level của organization.

```text
Charter
```

bao gồm:

```text
mission
scope
membership_policy
governance_model
authority_model
resource_model
amendment_rules
succession_rules
emergency_rules
dissolution_rules
```

---

# 17. Constitution

Một organization có thể có:

```text
Constitution
```

Constitution có precedence cao hơn ordinary organizational rules.

Ví dụ:

```text
constitution
    ↓
bylaws
    ↓
policies
    ↓
procedures
    ↓
task rules
```

Nhưng toàn bộ hierarchy vẫn thấp hơn các hard constraints của Axiom runtime.

---

# 18. Rule Hierarchy

Precedence:

```text
1. System safety/security constraints
2. Platform/runtime authority constraints
3. 639 policy constraints
4. 664 safety constraints
5. 665 human-oversight constraints
6. Organization constitution
7. Charter
8. Bylaws
9. Organizational policy
10. Role rules
11. Contract rules
12. Task rules
13. Local preferences
```

Không một organizational rule nào được nâng precedence lên trên runtime safety.

---

# 19. Rule Conflict

Nếu:

```text
rule_A
```

xung đột với:

```text
rule_B
```

runtime phải xác định:

```text
precedence
scope
authority
version
effective_time
```

Nếu không thể resolve:

```text
RULE_CONFLICT
```

Không được tự ý chọn rule thấp hơn.

---

# 20. Governance Model

667 không ép organization phải dùng một mô hình governance cụ thể.

Hỗ trợ:

```text
single_authority
hierarchical
committee
board
council
weighted_vote
one_member_one_vote
delegated_vote
consensus
quorum_vote
appointment
election
hybrid
algorithmic_governance
human_supervised
```

---

# 21. Governance Body

```text
GovernanceBody
GovernanceProcedure
DecisionRule
VotingRule
QuorumRule
EligibilityRule
AppealRule
```

---

# 22. Decision Lifecycle

Chu trình chuẩn:

```text
PROPOSE
    ↓
ELIGIBILITY_CHECK
    ↓
AGENDA
    ↓
REVIEW
    ↓
DELIBERATION
    ↓
VOTE / DECISION
    ↓
QUORUM_CHECK
    ↓
VALIDATION
    ↓
RESOLUTION
    ↓
PUBLICATION
    ↓
EXECUTION
    ↓
AUDIT
```

---

# 23. Proposal

```text
Proposal
ProposalId
Proposer
Scope
Evidence
ExpectedEffects
Risks
Cost
Dependencies
```

Proposal không phải decision.

```text
Proposal != Decision
```

---

# 24. Resolution

Resolution là kết quả governance đã được thông qua.

```text
Resolution
ResolutionId
Decision
Authority
EffectiveTime
Expiration
Scope
ExecutionPlan
```

---

# 25. Voting

```text
Vote
VoteChoice
VotingSession
VotingRule
Quorum
Threshold
Abstention
DelegatedVote
```

Choice:

```text
YES
NO
ABSTAIN
INVALID
```

Có thể mở rộng:

```text
RANKED
SCORE
APPROVAL
CONSENT
```

nhưng semantics phải được khai báo rõ.

---

# 26. Consensus

Consensus không đồng nghĩa với truth.

```text
Consensus != Truth
```

Consensus chỉ mô tả mức độ agreement theo một procedure.

---

# 27. Quorum

```text
QuorumRule
```

có thể dựa trên:

```text
member_count
eligible_member_count
weighted_vote
stake
role
committee_members
minimum_participation
```

Runtime phải lưu cách quorum được tính.

---

# 28. Appointment

```text
Appointment
AppointmentAuthority
AppointmentTerm
AppointmentCandidate
```

Lifecycle:

```text
NOMINATE
→ REVIEW
→ APPOINT
→ ACCEPT
→ ACTIVE
→ EXPIRE / REVOKE
```

---

# 29. Election

```text
Election
Candidate
Elector
Ballot
VotingPeriod
Result
AuditRecord
```

Election engine phải tách:

```text
eligibility
ballot
counting
verification
publication
appeal
```

---

# 30. Succession

Mọi office quan trọng nên có succession policy.

```text
SuccessionPlan
Successor
FallbackSuccessor
EmergencySuccessor
```

Ví dụ:

```text
Director
  → DeputyDirector
  → EmergencyCouncil
  → HumanOversight
```

---

# 31. Authority Delegation

667 sử dụng delegation của 666 nhưng mở rộng lên organization-level.

```text
AuthorityDelegation
```

phải có:

```text
grantor
grantee
authority
scope
constraints
start
expiration
revocation
```

Delegation không được vượt authority của grantor.

---

# 32. Authority Non-Amplification

Nếu:

```text
A has authority X
```

thì:

```text
A delegates X to B
```

không được tạo:

```text
B has X + Y
```

nếu A không có Y.

---

# 33. Budget

```text
Budget
BudgetPeriod
BudgetLine
BudgetLimit
BudgetAllocation
BudgetReservation
BudgetRelease
```

Ví dụ:

```text
budget Research {
    ai_compute = 1000
    storage = 500
    networking = 300
}
```

---

# 34. ResourcePool

```text
ResourcePool
ResourceType
ResourceQuota
AllocationPolicy
Reservation
Utilization
```

Resource có thể là:

```text
CPU
GPU
memory
storage
network
energy
money-like accounting units
compute credits
agent time
service capacity
```

---

# 35. Organizational Resource Boundary

667 không thay thế 606.

```text
606 = global/runtime resource governance
667 = organizational allocation
```

Organization chỉ phân phối resource mà nó thực sự được cấp.

---

# 36. Treasury

```text
Treasury
Account
Ledger
Transfer
Grant
Expense
Reservation
```

Mọi thay đổi tài chính/resource quan trọng phải có:

```text
authorization
trace
audit
```

---

# 37. Institutional Memory

Đây là một thành phần quan trọng của 667.

```text
InstitutionalMemory
```

không thuộc về một agent duy nhất.

Nó chứa:

```text
decisions
policies
precedents
records
contracts
organizational history
architectural decisions
incident records
audit records
succession records
```

---

# 38. Memory ≠ Hidden Reasoning

Institutional memory không được dùng để lưu hidden chain-of-thought.

Có thể lưu:

```text
decision summary
evidence
rationale summary
assumptions
alternatives considered
decision authority
```

nhưng không yêu cầu lưu private internal reasoning.

---

# 39. Record

```text
InstitutionalRecord
RecordId
Author
Authority
Timestamp
Version
Evidence
Provenance
Retention
Classification
```

---

# 40. Archive

```text
Archive
ArchivePolicy
RetentionPolicy
DeletionPolicy
LegalHold
```

Record không còn active vẫn phải có khả năng truy xuất nếu policy yêu cầu.

---

# 41. Institutional Precedent

Một decision có thể trở thành precedent:

```text
Precedent
```

nhưng:

```text
Precedent != BindingRule
```

trừ khi organizational governance explicitly quy định như vậy.

---

# 42. Organizational Knowledge

667 kết hợp:

```text
650 Memory
645 Knowledge Graph
654 Symbolic Reasoning
```

để tạo:

```text
InstitutionalKnowledge
```

Có provenance bắt buộc:

```text
source
authority
confidence
timestamp
version
verification
```

---

# 43. Audit

```text
Audit
AuditScope
Auditor
AuditFinding
AuditEvidence
AuditReport
```

Audit có thể kiểm tra:

```text
authority
resource usage
decision procedure
membership
security
policy compliance
safety
contract execution
succession
data handling
```

---

# 44. Compliance

```text
ComplianceState
ComplianceRule
ComplianceCheck
Violation
Remediation
```

Compliance phải phân biệt:

```text
PASS
FAIL
UNKNOWN
NOT_APPLICABLE
WAIVED
UNDER_REVIEW
```

---

# 45. Conflict of Interest

```text
ConflictOfInterest
Disclosure
Recusal
Review
```

Member có thể phải:

```text
declare conflict
recuse
appoint substitute
```

---

# 46. Recusal

Khi member bị conflict:

```text
eligible_to_vote = false
```

trong phạm vi decision tương ứng.

Recusal không nhất thiết đình chỉ membership.

---

# 47. Sanctions

Organization có thể:

```text
suspend membership
revoke role
remove office
restrict organizational access
quarantine organizational privileges
terminate membership
```

Nhưng không được vượt:

```text
603
639
664
665
```

---

# 48. Appeal

Mọi decision quan trọng có thể có:

```text
Appeal
AppealWindow
AppealAuthority
AppealEvidence
AppealDecision
```

Lifecycle:

```text
FILE
→ ELIGIBILITY
→ REVIEW
→ DECISION
→ FINALIZE
```

---

# 49. Reorganization

667 phải hỗ trợ:

```text
ReorganizationPlan
```

bao gồm:

```text
move department
rename role
merge units
split units
transfer assets
transfer contracts
transfer memory
transfer authority
```

---

# 50. Organization Merge

```text
OrganizationMerge
```

phải tạo lineage:

```text
OrgA
OrgB
   ↓
OrgC
```

Không được mất:

```text
identity history
records
contracts
assets
audit trail
membership history
```

---

# 51. Organization Split

```text
OrganizationSplit
```

có thể tạo:

```text
OrgA
 ↓
OrgB
OrgC
```

Phải xác định rõ:

```text
asset allocation
member allocation
contract ownership
memory partition
authority transfer
identity lineage
```

---

# 52. Dissolution

Organization lifecycle:

```text
ACTIVE
→ WINDING_DOWN
→ DISSOLVED
```

Dissolution không được xóa lịch sử.

Persistent records chuyển sang:

```text
ARCHIVED
```

---

# 53. Continuity

Organization phải có:

```text
ContinuityPlan
```

để xử lý:

```text
agent failure
leader failure
service failure
storage failure
network partition
credential expiration
key rotation
mass member departure
```

---

# 54. Organizational Persistence

Điều kiện:

```text
all current agents die
```

không nhất thiết dẫn tới:

```text
organization.destroy()
```

Nếu persistent state vẫn tồn tại:

```text
organization remains recoverable
```

---

# 55. Emergency Governance

```text
EmergencyAuthority
```

cho phép organization phản ứng nhanh với incident.

Nhưng emergency authority bắt buộc:

```text
bounded
scoped
time-limited
auditable
reviewable
```

---

# 56. Emergency Expiration

Nếu:

```text
expires_at <= now
```

thì:

```text
EmergencyAuthority.active = false
```

Không có implicit renewal.

---

# 57. Emergency Non-Override

Emergency authority không được tự động bypass:

```text
603 security
639 policy
664 safety
665 human control
```

---

# 58. Organization ↔ Agent

667 và 666 phân chia:

```text
666:
    Agent ↔ Agent
    Agent ↔ Team
    Agent ↔ Collective

667:
    Agent ↔ Organization
    Organization ↔ Organization
    Organization ↔ Institution
```

---

# 59. Organization ↔ Contract

Contract có thể thuộc:

```text
agent
team
organization
institution
```

Nhưng organization-level contract phải có:

```text
authorized_signatory
organizational_scope
contract_authority
```

---

# 60. Organization ↔ Goal

Organizational goals sử dụng:

```text
661
```

Ví dụ:

```text
organization.goal("build_compiler")
```

không tự tạo capability.

Goal:

```text
WHAT
```

Capability:

```text
CAN
```

Authority:

```text
MAY
```

Safety:

```text
MUST_NOT
```

---

# 61. Core Semantic Separation

Axiom 667 bắt buộc giữ:

```text
Goal       != Capability
Capability != Authority
Authority  != Membership
Membership != Role
Role       != Office
Office     != Person
Trust      != Authority
Reputation != Capability
Consensus  != Truth
Decision   != Execution
Proposal   != Decision
Organization != Agent
```

---

# 62. Human-AI Organization

667 hỗ trợ:

```text
human + human
AI + AI
human + AI
human + AI + service + device
```

Không có loại nào được mặc định privileged chỉ vì identity category.

Quyền phải đến từ:

```text
policy
role
authority
membership
capability
oversight
```

---

# 63. Human Oversight

Các organization có critical operations phải tích hợp 665.

Ví dụ:

```text
@human_approval(required=true)
resolution approve_nuclear_system
```

Runtime:

```text
proposal
→ governance
→ human approval
→ execution
```

nếu policy yêu cầu.

---

# 64. Organization Creation

Creation có thể do:

```text
human
agent
existing organization
deployment system
```

nhưng creation authority phải được policy cho phép.

Agent không được:

```text
spawn organization
→ automatically acquire unlimited authority
```

---

# 65. Organization Creation Boundary

```text
CREATE_ORGANIZATION
```

không đồng nghĩa:

```text
CREATE_AUTHORITY
CREATE_CAPABILITY
CREATE_RESOURCE
CREATE_HUMAN_PERMISSION
```

---

# 66. Inter-Organization Relationship

667 hỗ trợ:

```text
Partnership
Federation
Consortium
ServiceAgreement
ResourceSharing
Memorandum
DelegatedAuthority
MutualDependency
```

Các interaction động vẫn sử dụng 666.

---

# 67. Federation

```text
Federation
FederationMember
FederationRule
FederationCouncil
FederationResolution
```

Organization vẫn giữ identity riêng.

```text
OrgA ∈ FederationX
```

không đồng nghĩa:

```text
OrgA == FederationX
```

---

# 68. Organizational Trust

667 có thể sử dụng:

```text
666 Trust / Reputation
```

để xây:

```text
InstitutionalTrust
InstitutionalReputation
```

Nhưng:

```text
trust != authority
```

---

# 69. Institutional Reputation

Reputation evidence có thể bao gồm:

```text
audit history
contract completion
incident history
policy compliance
resource reliability
decision consistency
service quality
```

Không được dùng reputation như một capability grant.

---

# 70. Organizational State Machine

```text
PROPOSED
   ↓
FORMING
   ↓
ACTIVE
   ↓
SUSPENDED
   ↓
REORGANIZING
   ↓
WINDING_DOWN
   ↓
DISSOLVED
```

Có thể quay lại:

```text
SUSPENDED → ACTIVE
REORGANIZING → ACTIVE
```

nếu policy cho phép.

---

# 71. Institutional Identity Persistence

Identity phải duy trì qua:

```text
member replacement
role replacement
department changes
software updates
organizational restructuring
```

---

# 72. Versioning

Các artifact governance đều versioned:

```text
CharterVersion
RuleVersion
RoleVersion
DecisionVersion
BudgetVersion
OrganizationVersion
```

Không được silently mutate historical state.

---

# 73. Effective Time

Governance artifact hỗ trợ:

```text
created_at
effective_at
expires_at
revoked_at
```

Do đó có thể query:

```text
what rules were active at T?
```

---

# 74. Temporal Governance

Decision engine phải hỗ trợ:

```text
current policy
future policy
historical policy
scheduled policy
expired policy
```

---

# 75. Organizational Event Log

Mọi thay đổi quan trọng tạo event:

```text
OrganizationCreated
MemberJoined
MemberLeft
RoleAssigned
RoleRevoked
OfficeFilled
CharterAmended
RuleChanged
ProposalCreated
DecisionMade
ResolutionPublished
BudgetAllocated
AuditCompleted
SuccessionActivated
OrganizationMerged
OrganizationSplit
OrganizationDissolved
```

---

# 76. Institutional Trace

Trace phải kết nối:

```text
Proposal
→ Evidence
→ Review
→ Vote
→ Resolution
→ Authority
→ Execution
→ Outcome
→ Audit
```

---

# 77. Compiler Annotations

```text
@organization
@institution
@charter
@constitution
@bylaw
@membership
@member
@role
@office
@department
@division
@committee
@board
@council
@governance
@decision_rule
@quorum
@vote
@resolution
@appointment
@election
@succession
@mandate
@jurisdiction
@budget
@resource_pool
@allocation
@institutional_memory
@record
@archive
@audit
@compliance
@conflict_of_interest
@recusal
@appeal
@sanction
@reorganization
@merge
@split
@federation
@continuity
@emergency_authority
@emergency_succession
```

---

# 78. Metadata Artifacts

```text
.axorg
.axinstitution
.axcharter
.axconstitution
.axbylaw
.axmember
.axrole
.axoffice
.axdept
.axcommittee
.axboard
.axcouncil
.axgov
.axresolution
.axvote
.axelection
.axappointment
.axsuccession
.axmandate
.axjurisdiction
.axbudget
.axresourcepool
.axallocation
.axinstmemory
.axrecord
.axarchive
.axaudit
.axcompliance
.axappeal
.axsanction
.axreorg
.axfederation
.axcontinuity
.axemergencygov
```

---

# 79. IR Operations

Compiler/runtime IR phải hỗ trợ tối thiểu:

```text
OrganizationCreate
OrganizationRegister
OrganizationJoin
OrganizationLeave

MembershipGrant
MembershipSuspend
MembershipTerminate

RoleCreate
RoleAssign
RoleRevoke

OfficeCreate
OfficeAssign
OfficeVacate

DepartmentCreate
DepartmentMove
DepartmentMerge
DepartmentSplit

CommitteeCreate
BoardCreate
CouncilCreate
GovernanceBodyCreate

CharterCreate
CharterAmend

RuleCreate
RuleAmend
RuleEvaluate

ProposalCreate
AgendaAdd
ReviewRequest
Deliberate

VoteOpen
VoteCast
QuorumCheck

DecisionResolve
ResolutionAdopt
ResolutionPublish

DecisionAppeal

AppointmentCreate
AppointmentRevoke

ElectionCreate
ElectionRun
ElectionVerify

SuccessionCreate
SuccessionActivate

AuthorityDelegate
AuthorityRevoke

BudgetCreate
BudgetAllocate
BudgetReserve
BudgetRelease

ResourcePoolCreate
ResourceAllocate

InstitutionalRecordCreate
RecordArchive

AuditStart
AuditCheck
AuditComplete

ComplianceEvaluate

ConflictDeclare
Recuse

SanctionApply
SanctionRevoke

ReorganizationPlan
OrganizationMerge
OrganizationSplit
OrganizationDissolve

FederationJoin
FederationLeave

ContinuityCheck
ContinuityRecover

EmergencyAuthorityActivate
EmergencyAuthorityExpire

InstitutionalTrace
```

---

# 80. Runtime Profiles

```text
AXORG_NONE

AXORG_CORE
AXORG_IDENTITY
AXORG_MEMBERSHIP
AXORG_ROLE
AXORG_OFFICE
AXORG_DEPARTMENT

AXORG_COMMITTEE
AXORG_BOARD
AXORG_COUNCIL

AXORG_GOVERNANCE
AXORG_CHARTER
AXORG_RULES
AXORG_DECISION
AXORG_VOTING
AXORG_ELECTION
AXORG_APPOINTMENT
AXORG_SUCCESSION

AXORG_MANDATE
AXORG_JURISDICTION

AXORG_BUDGET
AXORG_RESOURCE

AXORG_MEMORY
AXORG_AUDIT
AXORG_COMPLIANCE

AXORG_APPEAL
AXORG_SANCTION

AXORG_REORG
AXORG_FEDERATION
AXORG_CONTINUITY
AXORG_EMERGENCY

AXORG_HUMAN_AI
AXORG_DISTRIBUTED
AXORG_REALTIME
AXORG_FULL
```

---

# 81. CLI

```text
axiom org list
axiom org inspect
axiom org create
axiom org status
axiom org join
axiom org leave

axiom org member list
axiom org member add
axiom org member suspend
axiom org member remove

axiom org role list
axiom org role assign
axiom org role revoke

axiom org office list
axiom org office assign
axiom org office vacate

axiom org department list
axiom org department create

axiom org committee list
axiom org committee create

axiom org charter inspect
axiom org charter amend

axiom org rule list
axiom org rule check
axiom org rule amend

axiom org decision propose
axiom org decision agenda
axiom org decision review
axiom org decision vote
axiom org decision status
axiom org decision publish
axiom org decision appeal

axiom org election create
axiom org election run
axiom org election status

axiom org appointment create
axiom org appointment revoke

axiom org succession inspect
axiom org succession activate

axiom org budget inspect
axiom org budget allocate
axiom org budget reserve
axiom org budget release

axiom org resource list
axiom org resource allocate

axiom org memory search
axiom org memory record
axiom org memory archive

axiom org audit start
axiom org audit status
axiom org audit report

axiom org compliance check

axiom org conflict declare
axiom org conflict recuse

axiom org appeal list
axiom org appeal review

axiom org reorg plan
axiom org reorg merge
axiom org reorg split
axiom org reorg dissolve

axiom org federation join
axiom org federation leave

axiom org continuity check
axiom org continuity recover

axiom org emergency activate
axiom org emergency review
axiom org emergency expire
```

---

# 82. Core Invariants

## Identity

**ORG-001**

Organization identity MUST be independent of member identity.

**ORG-002**

Replacing all members MUST NOT automatically destroy persistent organizational identity.

**ORG-003**

Historical organization identifiers MUST remain resolvable according to retention policy.

**ORG-004**

Organization merge MUST preserve lineage.

**ORG-005**

Organization split MUST preserve lineage.

---

## Membership

**ORG-010**

Membership MUST explicitly identify the organization.

**ORG-011**

Membership MUST have lifecycle state.

**ORG-012**

Expired membership MUST NOT silently remain active.

**ORG-013**

Suspended membership MUST preserve historical membership evidence.

**ORG-014**

Membership MUST NOT automatically grant unrestricted authority.

---

## Roles

**ORG-020**

Role MUST be distinct from member identity.

**ORG-021**

Role MUST be distinct from capability.

**ORG-022**

Role authority MUST have scope.

**ORG-023**

Time-bounded roles MUST expire automatically.

**ORG-024**

Revoked roles MUST cease granting organizational authority.

---

## Offices

**ORG-030**

Office MUST be persistent independently from its holder.

**ORG-031**

Vacating an office MUST NOT delete the office definition.

**ORG-032**

Office succession MUST be explicitly defined or reportable as absent.

---

## Governance

**ORG-040**

Proposal MUST NOT equal decision.

**ORG-041**

Decision MUST record decision authority.

**ORG-042**

Vote MUST record voting rule.

**ORG-043**

Quorum MUST be evaluated using the declared quorum rule.

**ORG-044**

Decision procedure MUST be auditable.

**ORG-045**

Consensus MUST NOT be represented as truth.

---

## Rules

**ORG-050**

Rules MUST have explicit scope.

**ORG-051**

Rules MUST have version identity.

**ORG-052**

Higher-precedence constraints MUST override lower-precedence organizational rules.

**ORG-053**

An organization MUST NOT create a rule that bypasses system safety.

**ORG-054**

An organization MUST NOT create authority exceeding its own authority.

---

## Authority

**ORG-060**

Delegated authority MUST NOT exceed grantor authority.

**ORG-061**

Authority MUST be scope-bound.

**ORG-062**

Authority MUST be revocable unless explicitly immutable by higher-level policy.

**ORG-063**

Membership MUST NOT imply unrestricted authority.

**ORG-064**

Trust MUST NOT create authority.

**ORG-065**

Reputation MUST NOT create authority.

---

## Budget

**ORG-070**

Allocation MUST NOT exceed available organizational resource.

**ORG-071**

Reservation MUST reduce available allocatable capacity.

**ORG-072**

Released reservation MUST restore allocatable capacity according to accounting rules.

**ORG-073**

Budget changes MUST be auditable.

---

## Memory

**ORG-080**

Institutional records MUST preserve provenance.

**ORG-081**

Historical decisions MUST NOT be silently rewritten.

**ORG-082**

Institutional memory MUST support versioning.

**ORG-083**

Memory retention MUST obey organizational and higher-level policy.

**ORG-084**

Institutional memory MUST NOT require private chain-of-thought storage.

---

## Audit

**ORG-090**

Audit records MUST be tamper-evident under the configured trust model.

**ORG-091**

Compliance result MUST distinguish failure from unknown.

**ORG-092**

Audit authority MUST itself be scoped.

---

## Succession

**ORG-100**

Succession MUST preserve office identity.

**ORG-101**

Emergency succession MUST have explicit activation conditions.

**ORG-102**

Emergency authority MUST have expiration.

**ORG-103**

Expired emergency authority MUST NOT remain active implicitly.

---

## Reorganization

**ORG-110**

Merge MUST preserve source lineage.

**ORG-111**

Split MUST preserve source lineage.

**ORG-112**

Dissolution MUST NOT silently delete mandatory historical records.

---

## Safety

**ORG-120**

Organization rules MUST NOT override 664.

**ORG-121**

Organization governance MUST NOT override 665.

**ORG-122**

Organization authority MUST remain subordinate to 639.

**ORG-123**

Organization cannot manufacture capabilities prohibited by 603.

---

# 83. Organizational Decision Security

Mọi critical decision phải có:

```text
decision_id
organization_id
proposal_id
authority_source
participants
eligibility
procedure
evidence
result
effective_time
audit_reference
```

Không cho phép:

```text
anonymous critical resolution
```

trừ khi explicit privacy policy cho phép và vẫn phải giữ audit identity ở trust boundary thích hợp.

---

# 84. Organizational Memory Consistency

Institutional memory phải hỗ trợ:

```text
strong consistency
eventual consistency
append-only history
versioned state
conflict detection
merge
```

Tùy profile.

---

# 85. Distributed Organizations

Một organization có thể chạy trên:

```text
node A
node B
node C
```

với:

```text
distributed membership
distributed governance
distributed memory
distributed budget
distributed audit
```

Sử dụng 628/631/633 cho infrastructure.

---

# 86. Partition Handling

Network partition phải có policy rõ:

```text
block
continue locally
read-only
emergency mode
quorum-required
```

Không được tự động giả định rằng mọi partition đều an toàn để tiếp tục governance.

---

# 87. Governance Under Partition

Ví dụ:

```text
quorum = 7/10
available = 4
```

thì:

```text
quorum_not_reached
```

trừ khi constitution định nghĩa emergency procedure hợp lệ.

---

# 88. Institutional Fault Tolerance

Organization nên duy trì được:

```text
identity
memory
roles
contracts
assets
audit history
```

khi một số agent/service chết.

---

# 89. Institutional Self-Modification

Organization có thể sửa:

```text
rules
roles
departments
governance
```

nhưng modification phải đi qua governance procedure được khai báo.

Không được:

```text
agent modifies constitution
```

nếu agent không có authority tương ứng.

---

# 90. Constitutional Protection

Có thể đánh dấu:

```text
@immutable_until(...)
@constitutional
```

để yêu cầu threshold cao hơn cho amendment.

---

# 91. Amendment

```text
AmendmentProposal
```

phải chỉ rõ:

```text
old_version
new_version
changed_sections
reason_summary
effective_time
required_authority
```

---

# 92. Governance Determinism

Các decision procedure quan trọng phải có thể replay:

```text
inputs
participants
rules
votes
timestamps
result
```

để verifier tái tính toán kết quả.

---

# 93. No Hidden Governance

Critical organizational decisions không được dựa vào hidden state không thể audit.

Có thể dùng AI reasoning, nhưng final decision phải có:

```text
decision evidence
decision authority
decision procedure
decision result
```

---

# 94. AI Governance Integration

667 không thay thế 647.

```text
647:
    lifecycle/governance của AI model/agent

667:
    organization sử dụng những AI đó như thế nào
```

---

# 95. Agent Replacement

Nếu:

```text
Agent A = Director
```

và A bị mất:

```text
Office Director
```

vẫn tồn tại.

Runtime chạy:

```text
SuccessionPlan
```

để tìm successor.

---

# 96. Organizational Goal Failure

Nếu goal không thể đạt được:

```text
goal_failed
```

không có nghĩa organization phải bị destroy.

Có thể:

```text
replan
amend goal
change resources
replace agents
reorganize
suspend
dissolve
```

theo governance.

---

# 97. Institutional Risk

```text
OrganizationalRisk
RiskAssessment
RiskOwner
Mitigation
ResidualRisk
```

Risk không phải safety override.

---

# 98. Organizational Health

Có thể tính các metrics:

```text
member availability
authority coverage
succession coverage
budget health
resource utilization
policy compliance
audit backlog
incident rate
decision latency
memory integrity
service reliability
```

Đây là observability data, không phải automatic judgment.

---

# 99. Organizational Health ≠ Intelligence

Một organization có:

```text
high organizational health
```

không có nghĩa:

```text
high intelligence
```

Hai khái niệm phải tách biệt.

---

# 100. Institutional Reputation

Institutional reputation phải dựa trên evidence.

Không được:

```text
reputation = authority
```

hoặc:

```text
reputation = capability
```

---

# 101. Privacy

Organization có thể chứa sensitive records.

Runtime phải hỗ trợ:

```text
classification
access control
retention
redaction
audit
purpose limitation
```

theo 603/639.

---

# 102. Organizational Data Domains

Có thể khai báo:

```text
@data_domain public
@data_domain internal
@data_domain confidential
@data_domain restricted
```

Mỗi domain có access policy.

---

# 103. Organizational API

Conceptual API:

```text
org.create()
org.join()
org.leave()

org.members()
org.roles()
org.offices()

org.propose()
org.review()
org.vote()
org.resolve()

org.delegate()
org.revoke()

org.budget()
org.allocate()

org.memory.record()
org.memory.search()

org.audit()
org.compliance()

org.reorganize()
org.merge()
org.split()

org.succession()
org.continuity()

org.emergency()
```

---

# 104. Example

```text
@organization
organization AxiomResearch {

    charter {
        mission = "research programming systems"

        governance = council

        amendment {
            quorum = 0.75
            approval = 0.67
        }
    }

    role Researcher

    role Director {
        authority = [
            research,
            staffing
        ]
    }

    office Director {
        succession = DeputyDirector
    }

    department Compiler

    budget Research {
        compute = 100000
        storage = 10000
    }
}
```

---

# 105. Example Governance

```text
proposal compiler_v2 {
    proposer = role:Researcher

    evidence = [
        benchmark_v1,
        design_report
    ]

    requested_budget = 10000
}

decision compiler_v2 {
    quorum = 0.60
    approval = 0.67
}
```

---

# 106. Example Succession

```text
succession Director {

    primary = DeputyDirector

    fallback = ResearchCouncil

    emergency = HumanOversight

    expires = 30d
}
```

---

# 107. Example Institutional Memory

```text
institutional_record decision_2048 {

    type = decision

    source = resolution:compiler_v2

    evidence = [
        benchmark_v1,
        audit_882
    ]

    retention = permanent
}
```

---

# 108. Example Reorganization

```text
reorganization split_compiler {

    source = department:Engineering

    target = [
        Compiler,
        Runtime
    ]

    transfer {
        Compiler → team:CompilerTeam
        Runtime  → team:RuntimeTeam
    }
}
```

---

# 109. Integration Matrix

| Layer | Responsibility |
|---|---|
| 603 | capability/security |
| 606 | system resource governance |
| 627 | distributed identity |
| 639 | policy/authority |
| 643 | AI compute |
| 644 | individual agent |
| 647 | AI/model governance |
| 650 | AI memory |
| 661 | goals/values |
| 663 | evaluation |
| 664 | safety |
| 665 | human oversight |
| 666 | dynamic multi-agent coordination |
| **667** | **persistent organizations/institutions** |

---

# 110. 666 vs 667

## 666

```text
Agent A
   ↔
Agent B
```

Focus:

```text
coordination
delegation
negotiation
contracts
teams
collectives
trust
reputation
```

## 667

```text
Organization
 ├── members
 ├── roles
 ├── offices
 ├── departments
 ├── rules
 ├── governance
 ├── budget
 ├── memory
 └── lifecycle
```

Focus:

```text
persistence
institutional structure
governance
succession
continuity
```

---

# 111. Organization vs Federation

667 có federation primitives cơ bản.

Một lớp sau có thể mở rộng thành:

```text
civilization-scale federation
```

với:

```text
cross-organization governance
multi-institution coordination
large-scale resource allocation
civilization-scale knowledge
```

Không nên nhồi toàn bộ semantics đó vào organization core.

---

# 112. Performance Requirements

667 không được biến organization thành heavyweight runtime object cho mọi chương trình Axiom.

Core implementation phải:

```text
zero-cost when unused
lazy initialization
event-driven
incremental persistence
compact identifiers
immutable/versioned records where useful
lock-free/read-optimized structures where appropriate
```

---

# 113. Compile-Time Elimination

Nếu application không sử dụng:

```text
organization
governance
institutional memory
```

compiler phải loại bỏ toàn bộ unused organizational runtime.

```text
AXORG_NONE
```

phải gần như zero-cost.

---

# 114. Persistence Strategy

Không bắt buộc organization state nằm trong một database cụ thể.

Backend boundary:

```text
InstitutionStore
GovernanceStore
MembershipStore
MemoryStore
AuditStore
BudgetStore
```

có thể map tới:

```text
memory
local storage
embedded storage
distributed storage
remote service
```

---

# 115. Event Sourcing Compatibility

667 phải hỗ trợ event-sourced organizations.

```text
event log
+
snapshot
=
organization state
```

Điều này đặc biệt hữu ích cho:

```text
audit
replay
recovery
historical queries
```

---

# 116. Snapshot

Organization snapshot phải có:

```text
organization_version
membership_version
governance_version
budget_version
memory_version
```

để phát hiện mismatch.

---

# 117. Recovery

Recovery:

```text
load_snapshot
→ verify_integrity
→ replay_events
→ validate_rules
→ validate_authority
→ validate_resources
→ restore_active_state
```

---

# 118. Security Boundary

Không cho phép client trực tiếp mutate:

```text
organization.authority
organization.identity
organization.audit
```

Các mutation phải đi qua validated operation.

---

# 119. Capability Checks

Critical organization operations:

```text
create
amend
delegate
allocate
vote
appoint
sanction
dissolve
```

phải trải qua:

```text
capability check
+
authority check
+
policy check
+
safety check
```

khi profile yêu cầu.

---

# 120. Final Contract

BOOTSTRAP-667 thiết lập:

```text
Agent
   ↓
can cooperate through 666
   ↓
can belong to Organization
   ↓
Organization has persistent identity
   ↓
Organization has members
   ↓
members have roles/offices
   ↓
organization has rules
   ↓
rules define governance
   ↓
governance produces decisions
   ↓
decisions can allocate authority/resources
   ↓
institutional memory preserves history
   ↓
succession preserves continuity
   ↓
reorganization evolves structure
```

Nhưng:

```text
603 grants capability
639 defines authority/policy
661 defines objectives
664 enforces safety
665 preserves human control
666 coordinates agents
667 structures persistent organizations
647 governs AI/model/agent lifecycle
```

**Không một organization nào có thể tự tạo capability, tự nâng authority, tự vô hiệu hóa safety, tự loại bỏ human oversight, hoặc biến consensus thành truth.**

---

# 121. Acceptance Criteria

BOOTSTRAP-667 được xem là hoàn thành khi compiler/runtime test suite chứng minh tối thiểu:

```text
Organization identity                 PASS
Persistent membership                 PASS
Role lifecycle                        PASS
Office lifecycle                      PASS
Department hierarchy                  PASS
Committee/Board/Council               PASS
Charter                               PASS
Constitution                          PASS
Rule precedence                       PASS
Proposal                              PASS
Review                                PASS
Voting                                PASS
Quorum                                PASS
Resolution                            PASS
Appointment                           PASS
Election                              PASS
Succession                            PASS
Delegation                            PASS
Budget                                PASS
Resource allocation                   PASS
Institutional memory                  PASS
Records                               PASS
Archive                               PASS
Audit                                 PASS
Compliance                            PASS
Conflict of interest                  PASS
Recusal                               PASS
Appeal                                PASS
Sanction                              PASS
Reorganization                       PASS
Merge                                 PASS
Split                                 PASS
Dissolution                           PASS
Federation                            PASS
Continuity                            PASS
Emergency authority                  PASS
Human-AI organization                PASS
Distributed organization             PASS
Crash recovery                        PASS
Event replay                          PASS
Policy integration                    PASS
Safety integration                    PASS
Human oversight integration          PASS
```

**Target: ≥ 3,000 automated tests.**

---

# 122. Completion Status

```text
BOOTSTRAP-667
Native AI Organization / Institution Runtime
STATUS = COMPLETE
```

Axiom hiện đã có chuỗi:

```text
644  Agent Runtime
645  Knowledge
646  Evaluation
647  AI Governance
648  Simulation
649  Multimodal
650  Memory
651  Personalization
652  Planning
653  Causal/Probabilistic
654  Symbolic
655  World Model
656  Embodied
657  Cognitive Executive
658  Social Intelligence
659  Emotion
660  Self Model
661  Value / Motivation
663  Evaluation / Assurance
664  Safety
665  Human Oversight
666  Multi-Agent Society
667  Organization / Institution
```

**Kiến trúc đã chuyển từ “nhiều agent phối hợp” sang “các tổ chức có thể tồn tại, ghi nhớ, quản trị, phân bổ nguồn lực và tự tổ chức theo luật”.**

---

# 123. Next Architecture Boundary

Lớp tiếp theo không nên chỉ là “thêm nhiều organization”.

Sau 667, abstraction tự nhiên là **civilization-scale / inter-organizational systems**:

```text
Agent
  ↓
Team
  ↓
Organization
  ↓
Institution
  ↓
Federation
  ↓
Civilization-scale Network
```

Do đó task kế tiếp:

**BOOTSTRAP-668 — Native AI Civilization / Federation Runtime: Inter-Organizational Networks, Federations, Alliances, Cross-Institution Governance, Shared Infrastructure, Common Protocols, Civilization-Scale Resource Coordination & Collective Memory 5.0**

:::

**Task kế tiếp đã được xác định: BOOTSTRAP-668.**