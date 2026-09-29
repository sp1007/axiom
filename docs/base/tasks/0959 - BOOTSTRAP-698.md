Tiếp tục chuỗi kiến trúc Axiom. Task kế tiếp là lớp thực thi **AXWELFARE**, tập trung vào phúc lợi xã hội, trợ cấp, lương hưu, quyền lợi và quản lý hồ sơ — tách rõ khỏi `AXLAW`, `AXFISCAL`, `AXFINANCE`, y tế và giáo dục.

:::writing{variant="document" id="58321" title="BOOTSTRAP-698 — Native AI Civilization-Scale Government Revenue Administration, Social Transfers, Welfare, Pensions, Public Benefits, Entitlements, Eligibility, Case Management & Social Protection Runtime 5.0"}

# BOOTSTRAP-698
# Native AI Civilization-Scale Government Revenue Administration, Social Transfers, Welfare, Pensions, Public Benefits, Entitlements, Eligibility, Case Management & Social Protection Runtime 5.0

**Namespace:** `AXWELFARE`  
**Status:** Architecture Specification  
**Version:** 5.0  
**Layer:** Government / Social Protection / Public Benefits  
**Axiom Platform:** Native AI Civilization-Scale Runtime

---

## 1. Mục tiêu

`AXWELFARE` là runtime native của Axiom cho việc thực thi quy mô lớn các hệ thống:

- an sinh xã hội;
- trợ cấp xã hội;
- chuyển giao tiền mặt;
- trợ cấp gia đình;
- trợ cấp trẻ em;
- trợ cấp người cao tuổi;
- trợ cấp người khuyết tật;
- trợ cấp thất nghiệp;
- trợ cấp nhà ở;
- trợ cấp năng lượng;
- hỗ trợ lương thực;
- hỗ trợ khẩn cấp;
- bảo hiểm xã hội;
- lương hưu;
- trợ cấp tử tuất;
- các chương trình phúc lợi công;
- quản lý quyền lợi công dân;
- quản lý hồ sơ và vụ việc;
- xác định điều kiện hưởng;
- tính toán mức hưởng;
- giải ngân;
- tái xác nhận;
- tạm đình chỉ;
- chấm dứt;
- kháng nghị;
- truy thu khoản chi sai;
- phát hiện bất thường;
- mô phỏng tác động chính sách.

Mục tiêu không phải biến `AXWELFARE` thành một hệ thống nghiệp vụ đóng.

Mục tiêu là tạo **primitive runtime + type system + rule engine + workflow engine + event model + audit model** đủ mạnh để xây dựng mọi hệ thống social-protection cấp quốc gia hoặc liên quốc gia.

---

# 2. Vị trí trong Axiom Civilization Stack

```text
                         AXGOV
                           │
                      Public Policy
                           │
                         AXLAW
                           │
              Legal Rights / Legal Authority
                           │
                       AXFISCAL
                           │
              Budget / Treasury / Funding
                           │
                       AXWELFARE
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    Eligibility        Entitlement        Case Management
        │                  │                  │
        ├──────────────┬───┴──────────────┐   │
        │              │                  │   │
     Benefits       Pension           Transfers │
        │              │                  │   │
        └──────────────┴──────────┬───────┘   │
                                  │           │
                           Payment Instruction
                                  │
                              AXBANKING
                                  │
                               Payment
                                  │
                              Citizen
```

Các hệ thống liên quan:

```text
AXLAW
  ↓
quyền pháp lý

AXFISCAL
  ↓
nguồn ngân sách / hạn mức tài khóa

AXWELFARE
  ↓
thực thi chương trình / xác định điều kiện / quản lý hồ sơ / quyền lợi

AXFINANCE
  ↓
sự thật kế toán và tài chính

AXBANKING
  ↓
hạ tầng thanh toán

AXPOPULATION
  ↓
danh tính dân cư / hộ gia đình / quan hệ nhân khẩu

AXLABOR
  ↓
việc làm / thu nhập lao động / thất nghiệp

AXHEALTH
  ↓
các dữ liệu y tế được pháp luật cho phép sử dụng

AXEDUCATION
  ↓
trạng thái học tập / giáo dục nếu chương trình cần

AXLAW
  ↓
quyền kháng nghị / nghĩa vụ / giới hạn pháp lý
```

---

# 3. Ranh giới kiến trúc

## 3.1. AXWELFARE không thay thế AXLAW

```text
AXLAW
    = quyền pháp lý

AXWELFARE
    = thực thi chương trình
```

Ví dụ:

```text
LegalEntitlement
```

được xác định theo luật.

`AXWELFARE` không tự tạo ra luật mới.

---

## 3.2. AXWELFARE không thay thế AXFISCAL

```text
AXFISCAL
    = ngân sách / treasury / fiscal authority

AXWELFARE
    = chương trình / eligibility / benefit execution
```

Do đó:

```text
BenefitEntitlement != BudgetAppropriation
```

Một cá nhân có thể có quyền lợi hợp pháp nhưng chương trình vẫn phải thực hiện kiểm soát nguồn tài chính theo quy định.

---

## 3.3. AXWELFARE không thay thế AXFINANCE

```text
AXWELFARE
    → phát sinh BenefitPayment

AXFINANCE
    → ghi nhận FinancialTransaction
```

---

# 4. Các phân biệt semantic bắt buộc

Axiom phải coi các cặp sau là những khái niệm khác nhau:

```text
Person != Beneficiary

Person != Applicant

Applicant != Beneficiary

Household != Person

Need != Eligibility

Eligibility != Entitlement

Entitlement != Approval

Approval != Award

Award != PaymentInstruction

PaymentInstruction != Payment

Payment != Outcome

Program != Benefit

Benefit != BenefitAward

Case != Application

Application != Case

EligibilityAssessment != LegalDecision

LegalEntitlement != AdministrativeApproval

Income != AssessedIncome

AssessedIncome != DisposableIncome

Contribution != Benefit

ContributionRecord != PensionEntitlement

PensionEntitlement != PensionPayment

Payment != SuccessfulOutcome

Overpayment != Fraud

Anomaly != Fraud

RiskScore != FraudFinding

Investigation != Finding

Finding != LegalViolation

AIRecommendation != BenefitDecision

AIRecommendation != LegalDecision

Simulation != Policy

Simulation != Entitlement

Forecast != Actual

Household != Family

ProgramFunding != IndividualEntitlement

BudgetAvailability != Eligibility

EligibilityRule != PaymentRule

Suspension != Termination

Termination != Appeal

Appeal != AutomaticReversal

RecoveryClaim != FraudFinding
```

Đây là **semantic firewall** của `AXWELFARE`.

---

# 5. Mô hình lifecycle chuẩn

Lifecycle tổng quát:

```text
Person
   ↓
ProgramDiscovery
   ↓
Application
   ↓
IdentityVerification
   ↓
EvidenceCollection
   ↓
EligibilityAssessment
   ↓
EntitlementDetermination
   ↓
CaseReview
   ↓
Approval
   ↓
BenefitAward
   ↓
PaymentInstruction
   ↓
Payment
   ↓
Outcome
   ↓
Recertification
   ↓
Renewal / Adjustment / Suspension / Termination
```

Nhánh ngoại lệ:

```text
Application
   ↓
Denied
   ↓
Appeal
   ↓
Review
   ↓
Decision
```

và:

```text
Payment
   ↓
OverpaymentDetected
   ↓
RecoveryCase
   ↓
RecoveryPlan
   ↓
Recovered
```

---

# 6. Core Types

## 6.1. Person

```axiom
struct Person {
    id: PersonId
    identity: IdentityRef
}
```

`Person` không tự động đồng nghĩa với beneficiary.

---

## 6.2. Household

```axiom
struct Household {
    id: HouseholdId
    members: EntitySet<PersonId>
    composition: HouseholdComposition
}
```

Có thể tồn tại:

```text
Person → multiple household periods
```

vì cấu trúc hộ gia đình thay đổi theo thời gian.

---

# 7. Social Protection Program

```axiom
struct WelfareProgram {
    id: ProgramId
    name: Text
    category: ProgramCategory
    legal_basis: LegalReference
    funding_source: FundingSource
    eligibility_rule: RuleRef
    benefit_rule: RuleRef
    payment_rule: RuleRef
    lifecycle: ProgramLifecycle
}
```

`Program` là container nghiệp vụ.

Không phải bản thân quyền lợi.

---

# 8. Program Category

```axiom
enum ProgramCategory {
    SOCIAL_ASSISTANCE
    SOCIAL_INSURANCE
    PENSION
    UNEMPLOYMENT
    FAMILY
    CHILD
    DISABILITY
    ELDERLY
    HOUSING
    FOOD
    ENERGY
    HEALTH_SUPPORT
    EDUCATION_SUPPORT
    EMERGENCY
    SURVIVOR
    CONTRIBUTORY
    NON_CONTRIBUTORY
    UNIVERSAL
    MEANS_TESTED
    CATEGORICAL
    HYBRID
}
```

Một chương trình có thể có nhiều classification.

---

# 9. Application

```axiom
struct BenefitApplication {
    id: ApplicationId
    applicant: PersonId
    household: Option<HouseholdId>
    program: ProgramId
    submitted_at: Timestamp
    evidence: EvidenceSet
    status: ApplicationStatus
}
```

---

# 10. Evidence

```axiom
struct Evidence {
    id: EvidenceId
    type: EvidenceType
    source: EvidenceSource
    issued_at: Timestamp
    valid_from: Timestamp
    valid_until: Option<Timestamp>
    hash: Hash
    verification: VerificationStatus
}
```

Các nguồn có thể gồm:

```text
citizen-submitted
government-registry
employer
financial institution
authorized third-party
court
medical authority
education authority
```

Việc sử dụng dữ liệu phải chịu:

```text
purpose limitation
legal basis
access control
retention policy
audit
```

---

# 11. Eligibility

Eligibility là quá trình xác định một applicant có thỏa điều kiện của chương trình hay không.

```axiom
struct EligibilityAssessment {
    id: EligibilityAssessmentId
    application: ApplicationId
    rule_version: RuleVersion
    inputs: EligibilityInputSet
    result: EligibilityResult
    evaluated_at: Timestamp
}
```

---

# 12. Eligibility Result

```axiom
enum EligibilityResult {
    ELIGIBLE
    INELIGIBLE
    PARTIALLY_ELIGIBLE
    INDETERMINATE
    PENDING_EVIDENCE
    PENDING_REVIEW
}
```

`INDETERMINATE` phải là trạng thái hợp lệ.

Không được ép mọi dữ liệu chưa đủ thành `ELIGIBLE` hoặc `INELIGIBLE`.

---

# 13. Eligibility Rule Engine

Axiom cần native rule engine.

Ví dụ:

```axiom
rule ChildBenefitEligibility {
    when
        child.age < 18
        && household.resident == true
        && household.income < threshold
    then
        eligible
}
```

Rule phải có version:

```text
Rule
RuleVersion
EffectiveFrom
EffectiveUntil
LegalBasis
```

Không được sửa ngầm rule đã dùng để tạo quyết định lịch sử.

---

# 14. Temporal Rule Model

Một rule:

```text
R1
effective 2026-01-01
```

sau đó:

```text
R2
effective 2027-01-01
```

Không được dùng `R2` để tái tạo một quyết định vốn được đánh giá bằng `R1`, trừ khi luật quy định hồi tố.

Do đó:

```axiom
EligibilityAssessment.rule_version
```

là immutable.

---

# 15. Means Testing

Axiom phải hỗ trợ nhiều mô hình:

```text
gross income
net income
household income
per-capita income
equivalized income
asset test
income + asset test
consumption proxy
categorical eligibility
```

Ví dụ:

```axiom
rule MeansTest {
    let adjusted_income =
        household.income / household.equivalence_scale

    return adjusted_income <= threshold
}
```

---

# 16. Categorical Eligibility

Một số chương trình không cần means test.

Ví dụ abstraction:

```axiom
rule ElderlyEligibility {
    when person.age >= retirement_age
    then eligible
}
```

Hoặc:

```axiom
rule DisabilityProgramEligibility {
    when disability_status == QUALIFIED
    then eligible
}
```

---

# 17. Entitlement

Eligibility không tự động đồng nghĩa entitlement.

```axiom
struct BenefitEntitlement {
    id: EntitlementId
    beneficiary: PersonId
    program: ProgramId
    legal_basis: LegalReference
    effective_from: Date
    effective_until: Option<Date>
    amount_rule: RuleRef
    status: EntitlementStatus
}
```

---

# 18. Entitlement Status

```axiom
enum EntitlementStatus {
    PROPOSED
    ACTIVE
    SUSPENDED
    EXPIRED
    TERMINATED
    APPEALED
    REVOKED
}
```

Mọi thay đổi phải tạo event.

---

# 19. Benefit Award

```axiom
struct BenefitAward {
    id: BenefitAwardId
    entitlement: EntitlementId
    amount: Money
    frequency: PaymentFrequency
    period: BenefitPeriod
    approved_by: AuthorityRef
}
```

---

# 20. Benefit Types

```axiom
enum BenefitType {
    CASH
    IN_KIND
    VOUCHER
    SERVICE
    TAX_CREDIT
    PREMIUM_SUBSIDY
    CONTRIBUTION_CREDIT
    HOUSING_SUPPORT
    FOOD_SUPPORT
    ENERGY_SUPPORT
    EMERGENCY_SUPPORT
}
```

---

# 21. Benefit Formula

Hệ thống phải hỗ trợ:

```text
fixed amount
percentage
tiered amount
income-tested amount
household-size based
age-based
contribution-based
indexed amount
hybrid formula
```

Ví dụ:

```axiom
rule BenefitAmount {
    base = 1000

    if household.members >= 4:
        base += 300

    if assessed_income < poverty_line:
        base += 500

    return base
}
```

Rule execution phải deterministic khi input và rule version giống nhau.

---

# 22. Indexation

Hỗ trợ:

```text
CPI index
wage index
fixed annual adjustment
statutory index
custom formula
```

Không được thay đổi lịch sử payment bằng cách thay đổi index hiện tại.

---

# 23. Case Management

```axiom
struct WelfareCase {
    id: CaseId
    subject: PersonId
    household: Option<HouseholdId>
    applications: EntitySet<ApplicationId>
    entitlements: EntitySet<EntitlementId>
    tasks: EntitySet<CaseTaskId>
    status: CaseStatus
    assigned_to: ActorRef
}
```

Case là container điều phối.

Không phải quyền lợi.

---

# 24. Case Status

```axiom
enum CaseStatus {
    OPEN
    REVIEW
    WAITING_EVIDENCE
    DECISION_PENDING
    ACTIVE
    SUSPENDED
    APPEALED
    CLOSED
}
```

---

# 25. Case Workflow

Native workflow:

```axiom
workflow WelfareApplication {
    submit
    verify_identity
    collect_evidence
    evaluate_eligibility
    determine_entitlement
    review
    approve
    award
    schedule_payment
    monitor
    recertify
    close
}
```

Workflow engine phải hỗ trợ:

```text
state
transition
guard
timeout
retry
compensation
human approval
parallel tasks
escalation
audit event
```

---

# 26. Human-in-the-loop

Các quyết định có tác động lớn phải có capability boundary:

```text
AI may recommend
AI may calculate
AI may detect anomalies
AI may summarize evidence
AI may simulate outcomes
```

nhưng:

```text
AI != legal authority
AI != final benefit authority
```

Các workflow nhạy cảm có thể yêu cầu:

```axiom
require_human_approval()
```

---

# 27. AI Decision Boundary

Cấm implicit automation đối với:

```text
final benefit denial
final entitlement termination
legal fraud finding
appeal rejection
asset seizure
recovery enforcement
```

nếu chương trình yêu cầu human/legal authority.

AI output phải mang provenance:

```axiom
struct AIRecommendation {
    model: ModelRef
    model_version: Version
    input_hash: Hash
    output: DecisionSuggestion
    confidence: Float
    generated_at: Timestamp
}
```

---

# 28. Unified Social Registry

Axiom có thể hỗ trợ:

```axiom
SocialRegistry
```

nhưng registry không được trở thành một "database toàn quyền".

Mỗi field phải có:

```text
owner
source
legal_basis
purpose
classification
retention
access_policy
```

Ví dụ:

```text
income
    source = tax authority
    purpose = means_test
```

không mặc nhiên có nghĩa:

```text
income
    readable_by_every_government_service
```

---

# 29. Household Graph

Hỗ trợ graph:

```text
Person
 ├── Household
 ├── Spouse
 ├── Parent
 ├── Child
 ├── Guardian
 ├── Employer
 └── BenefitProgram
```

Nhưng relationship phải có temporal validity:

```axiom
Relation {
    from
    to
    type
    valid_from
    valid_until
}
```

---

# 30. Duplicate Prevention

Hệ thống phải hỗ trợ:

```text
identity resolution
duplicate detection
cross-program duplication
household overlap detection
payment duplication detection
```

Nhưng:

```text
duplicate_signal != fraud
```

Một cá nhân có nhiều hồ sơ có thể do:

```text
migration
name change
identity correction
administrative error
```

---

# 31. Benefit Coordination

Một beneficiary có thể đồng thời nhận:

```text
child benefit
housing support
energy support
pension
disability support
```

Do đó cần:

```axiom
BenefitCoordinationPolicy
```

để xác định:

```text
compatible
stackable
mutually exclusive
priority
offset
cap
interaction
```

---

# 32. Overpayment

```axiom
struct Overpayment {
    id: OverpaymentId
    beneficiary: PersonId
    benefit: BenefitAwardId
    amount: Money
    reason: OverpaymentReason
    detected_at: Timestamp
}
```

Không mặc định coi là gian lận.

---

# 33. Recovery

```axiom
struct RecoveryCase {
    id: RecoveryCaseId
    overpayment: OverpaymentId
    amount_due: Money
    recovery_plan: Option<RecoveryPlan>
    status: RecoveryStatus
}
```

Hỗ trợ:

```text
full repayment
installments
offset against future benefits
waiver
administrative adjustment
legal recovery
```

---

# 34. Appeals

```axiom
struct BenefitAppeal {
    id: AppealId
    case: CaseId
    challenged_decision: DecisionId
    grounds: AppealGrounds
    evidence: EvidenceSet
    status: AppealStatus
}
```

Lifecycle:

```text
Decision
 ↓
Appeal
 ↓
Review
 ↓
Decision
 ↓
Implementation
```

Appeal phải giữ nguyên historical decision.

Không rewrite history.

---

# 35. Pension Model

Lương hưu cần semantic riêng.

```axiom
struct PensionAccount {
    id: PensionAccountId
    beneficiary: PersonId
    contribution_record: ContributionRecordRef
    vesting: VestingState
    accrual: PensionAccrual
}
```

---

# 36. Contribution Record

```axiom
struct PensionContribution {
    period: ContributionPeriod
    contributor: EntityRef
    employee_amount: Money
    employer_amount: Money
    credited_amount: Money
}
```

---

# 37. Pension Entitlement

```axiom
struct PensionEntitlement {
    beneficiary: PersonId
    retirement_date: Date
    formula_version: RuleVersion
    monthly_amount: Money
    indexation: IndexationPolicy
}
```

Cần hỗ trợ:

```text
old-age pension
early retirement
deferred retirement
disability pension
survivor pension
dependent benefit
portable pension
partial pension
```

---

# 38. Pension Portability

Pension record có thể di chuyển giữa:

```text
employers
regions
administrative jurisdictions
funds
social insurance systems
```

Không được nhân đôi contribution.

Cần:

```text
transfer
merge
split
reconciliation
```

---

# 39. Survivor Benefits

Hỗ trợ:

```text
death event
eligible survivor
dependency test
survivor entitlement
benefit duration
termination
```

Mọi entitlement phải có legal basis và temporal validity.

---

# 40. Revenue Administration Boundary

`AXWELFARE` có thể tiêu thụ dữ liệu revenue/income để xác định benefit.

Nhưng:

```text
AXFISCAL = fiscal policy / public revenue authority

AXWELFARE = welfare-side execution
```

Ví dụ:

```text
AXFISCAL
    assesses public revenue

AXWELFARE
    consumes authorized income assessment
```

Không tạo duplicate tax engine trong `AXWELFARE`.

---

# 41. Payment Integration

Luồng:

```text
BenefitAward
    ↓
PaymentInstruction
    ↓
AXBANKING
    ↓
Payment
    ↓
Settlement
```

`AXWELFARE` không giả mạo payment success.

Payment state phải đến từ payment infrastructure hoặc trusted settlement event.

---

# 42. Payment State Machine

```text
CREATED
 ↓
AUTHORIZED
 ↓
SUBMITTED
 ↓
PROCESSING
 ↓
SETTLED
```

Các nhánh:

```text
REJECTED
FAILED
RETURNED
CANCELLED
REVERSED
```

---

# 43. Reconciliation

Phải có reconciliation:

```text
BenefitAward
        ↕
PaymentInstruction
        ↕
Payment
        ↕
Settlement
        ↕
AXFINANCE
```

Mọi mismatch tạo:

```axiom
ReconciliationException
```

không âm thầm sửa dữ liệu.

---

# 44. Program Funding

```axiom
struct ProgramFunding {
    program: ProgramId
    fiscal_source: FundingSource
    allocation: Money
    fiscal_period: FiscalPeriod
}
```

Funding không quyết định eligibility.

```text
Funding != Eligibility
```

---

# 45. Intergovernmental Transfers

Hỗ trợ:

```text
national → regional
regional → local
government → agency
government → program
```

Các transfer có:

```text
allocation rule
period
conditions
reporting obligations
reconciliation
clawback
```

---

# 46. Policy Simulation

Axiom phải hỗ trợ mô phỏng:

```text
change eligibility threshold
change benefit amount
change indexation
change retirement age
change contribution rate
change household definition
```

Kết quả:

```axiom
PolicySimulationResult {
    beneficiary_count
    fiscal_cost
    distribution_effect
    coverage
    exclusion
    program_interaction
}
```

Simulation không thay đổi production state.

---

# 47. Digital Twin

Có thể tạo:

```text
Population Digital Twin
Welfare Program Digital Twin
Pension System Digital Twin
Household Distribution Model
```

để mô phỏng hàng triệu/hàng tỷ entity.

---

# 48. Privacy Architecture

Dữ liệu welfare thường có độ nhạy cao.

Mọi access phải chịu:

```text
identity
authentication
authorization
purpose
legal_basis
scope
field-level policy
audit
retention
```

Hỗ trợ:

```text
field-level encryption
tokenization
pseudonymization
selective disclosure
data minimization
privacy-preserving analytics
```

---

# 49. Capability Model

Ví dụ:

```text
welfare.read_case
welfare.modify_case
welfare.evaluate
welfare.approve
welfare.award
welfare.suspend
welfare.terminate
welfare.appeal
welfare.recover
welfare.audit
welfare.simulate
welfare.administer_rules
```

Tách biệt:

```text
evaluator
reviewer
approver
payment_authorizer
auditor
rule_admin
```

---

# 50. Separation of Duties

Không cho một identity mặc định đồng thời:

```text
create application
approve application
authorize payment
audit own decision
```

Runtime phải hỗ trợ policy:

```axiom
separation_of_duties(...)
```

---

# 51. Immutable Decision Provenance

Mỗi quyết định phải lưu:

```text
decision_id
subject
program
rule_version
legal_basis
input_snapshot_hash
evidence_hashes
actor
AI involvement
timestamp
decision
reason_code
```

Cho phép tái dựng:

```text
Why was this benefit awarded?
```

hoặc:

```text
Why was this application denied?
```

mà không cần phụ thuộc trạng thái database hiện tại.

---

# 52. Event Model

Các event cơ bản:

```text
ApplicationSubmitted
IdentityVerified
EvidenceAdded
EligibilityEvaluated
EntitlementCreated
EntitlementSuspended
EntitlementTerminated
BenefitAwarded
PaymentScheduled
PaymentSubmitted
PaymentSettled
PaymentFailed
RecertificationStarted
RecertificationCompleted
AppealFiled
AppealDecided
OverpaymentDetected
RecoveryStarted
RecoveryCompleted
ProgramRuleChanged
```

Event immutable.

---

# 53. Event Sourcing Compatibility

`AXWELFARE` phải hỗ trợ:

```text
event sourcing
snapshotting
materialized views
CQRS
append-only audit log
```

Nhưng không bắt buộc mọi ứng dụng phải dùng event sourcing.

---

# 54. Deterministic Replay

Cho cùng:

```text
input snapshot
rule version
program version
configuration
time context
```

engine phải có khả năng tái chạy:

```text
same input
→ same decision
```

trừ khi rule cố ý phụ thuộc external nondeterministic source.

---

# 55. Temporal Queries

Native syntax:

```axiom
case.entitlement.at("2026-01-01")
```

hoặc:

```axiom
income.during(period)
```

và:

```axiom
household.members.at(date)
```

Temporal semantics là primitive quan trọng của `AXWELFARE`.

---

# 56. Error Model

Các error code tối thiểu:

```text
WELFARE_INVALID_PROGRAM
WELFARE_INVALID_APPLICATION
WELFARE_IDENTITY_UNVERIFIED
WELFARE_EVIDENCE_MISSING
WELFARE_EVIDENCE_EXPIRED
WELFARE_ELIGIBILITY_INDETERMINATE
WELFARE_RULE_NOT_FOUND
WELFARE_RULE_VERSION_MISMATCH
WELFARE_ENTITLEMENT_INVALID
WELFARE_AWARD_INVALID
WELFARE_PAYMENT_INVALID
WELFARE_PAYMENT_DUPLICATE
WELFARE_PAYMENT_FAILED
WELFARE_RECONCILIATION_FAILED
WELFARE_OVERPAYMENT
WELFARE_RECOVERY_INVALID
WELFARE_APPEAL_INVALID
WELFARE_CASE_CONFLICT
WELFARE_PROGRAM_FUNDING_UNAVAILABLE
WELFARE_AUTHORITY_REQUIRED
WELFARE_SEPARATION_OF_DUTIES
WELFARE_PRIVACY_VIOLATION
WELFARE_ACCESS_DENIED
WELFARE_PROVENANCE_MISSING
WELFARE_VERSION_CONFLICT
WELFARE_TEMPORAL_CONFLICT
WELFARE_DUPLICATE_ENTITY
WELFARE_RULE_NONDETERMINISTIC
WELFARE_AI_RECOMMENDATION_ONLY
```

---

# 57. Memory Model

`AXWELFARE` không được yêu cầu GC.

Core runtime phải tương thích:

```text
arena allocation
region allocation
pool allocation
slab allocation
flat storage
immutable snapshots
copy-on-write
reference-counted external resources
```

Hot-path data nên ưu tiên:

```text
SoA
packed records
columnar storage
arena
contiguous arrays
```

để tối ưu batch processing.

---

# 58. Concurrency

Các workload chính:

```text
application ingestion
eligibility evaluation
payment generation
recertification
analytics
fraud/anomaly detection
pension calculation
policy simulation
```

phải partition theo:

```text
program
region
time period
beneficiary shard
case shard
```

Không dùng global lock cho toàn hệ thống.

---

# 59. Parallel Rule Evaluation

Ví dụ:

```axiom
parallel for application in applications {
    evaluate(application)
}
```

Compiler/runtime có thể biến thành:

```text
partition
→ worker pool
→ local evaluation
→ deterministic merge
```

---

# 60. GPU Acceleration

GPU có thể được sử dụng cho:

```text
large-scale eligibility simulation
population modeling
benefit distribution simulation
anomaly detection
policy optimization
pension projection
graph analytics
```

Không bắt buộc GPU cho transactional path.

---

# 61. Performance Targets

Kiến trúc mục tiêu:

```text
≥ 5M lightweight welfare events/sec
per large partitioned deployment target
```

và:

```text
billions of historical cases
billions of benefit events
billions of household/person relationships
millions of concurrent active cases
```

Rule evaluation phải hỗ trợ vectorization và batch execution.

---

# 62. Runtime Profiles

```text
AXWELFARE_NONE

AXWELFARE_CORE

AXWELFARE_BENEFITS

AXWELFARE_ELIGIBILITY

AXWELFARE_CASE

AXWELFARE_PENSION

AXWELFARE_SOCIAL_INSURANCE

AXWELFARE_PAYMENT

AXWELFARE_APPEAL

AXWELFARE_RECOVERY

AXWELFARE_ANALYTICS

AXWELFARE_AI

AXWELFARE_SIMULATION

AXWELFARE_DIGITAL_TWIN

AXWELFARE_DISTRIBUTED

AXWELFARE_GPU

AXWELFARE_WASM

AXWELFARE_MOBILE

AXWELFARE_REALTIME

AXWELFARE_FULL
```

Compiler chỉ link module được sử dụng.

---

# 63. Native DSL

Axiom nên cung cấp syntax chuyên dụng nhưng compile xuống core primitives.

Ví dụ:

```axiom
program ChildBenefit {

    eligibility {
        age(child) < 18
        resident(household)
    }

    benefit {
        base = 500
        per_child = 200
    }

    payment {
        frequency = MONTHLY
    }
}
```

DSL không được tạo thành runtime thứ hai.

Compiler hạ nó xuống:

```text
types
rules
functions
workflow
events
capabilities
```

---

# 64. AI-Friendly Representation

Mọi program/rule/decision cần machine-readable metadata:

```text
schema
semantic_type
legal_basis
rule_version
dependencies
inputs
outputs
side_effects
authority
privacy_class
audit_policy
```

AI agent có thể query:

```axiom
describe WelfareProgram
explain EligibilityRule
trace BenefitAward
simulate ProgramChange
```

nhưng quyền thực thi vẫn bị capability system kiểm soát.

---

# 65. AI Explainability

Một decision phải có thể tạo:

```text
input facts
→ rules evaluated
→ conditions matched
→ conditions failed
→ intermediate values
→ final result
```

Ví dụ:

```text
Income = 1200
Threshold = 1500
Age = 67
Residency = true

Rule R2026.3:
    income <= threshold       PASS
    age >= 65                 PASS
    residency                 PASS

Result:
    ELIGIBLE
```

---

# 66. Fraud Boundary

`AXWELFARE` có thể phát hiện:

```text
duplicate payment
identity collision
unusual payment pattern
impossible household transition
rapid account changes
repeated contradictory evidence
```

Nhưng:

```text
AnomalySignal != Fraud
```

Fraud finding phải đi qua quy trình điều tra phù hợp.

---

# 67. Risk Engine

```axiom
struct WelfareRiskSignal {
    subject: EntityRef
    score: Float
    features: FeatureSet
    model: ModelRef
    generated_at: Timestamp
}
```

Risk score không được tự động biến thành:

```text
denial
termination
fraud finding
```

---

# 68. Audit

Audit phải trả lời được:

```text
Who?
What?
When?
Under which rule?
Using which data?
Under which authority?
With which model?
What changed?
Why?
What payment followed?
```

---

# 69. Security Invariants

Ít nhất:

1. Không có benefit payment nếu không có valid award.
2. Không có award nếu không có valid entitlement.
3. Entitlement phải có legal basis.
4. Eligibility assessment phải có rule version.
5. Historical decisions không bị overwrite.
6. Payment không được đánh dấu settled bởi welfare engine nếu không có settlement evidence.
7. AI recommendation không tự động trở thành legal decision.
8. Anomaly không tự động trở thành fraud.
9. Appeal không xóa decision cũ.
10. Recovery không được thay đổi historical payment record.
11. Sensitive data phải có authorization.
12. Cross-program data sharing phải có policy.
13. Program rule version phải immutable sau khi được sử dụng.
14. Funding state không được sửa eligibility result.
15. Eligibility không được tự động suy ra entitlement nếu legal workflow yêu cầu approval.
16. Duplicate signal không được coi là fraud.
17. Case ownership phải audit được.
18. Payment instruction phải idempotent.
19. Recovery transaction phải idempotent.
20. Temporal records phải giữ validity interval.
21. Household relationships phải có effective period.
22. Pension contribution records không được duplicate.
23. Benefit calculation phải traceable.
24. Rule execution phải reproducible.
25. Program configuration phải versioned.
26. Privacy policy không được bypass bởi AI.
27. Auditor không được sửa decision history.
28. Rule administrator không mặc nhiên có payment authority.
29. Payment authority không mặc nhiên có rule-administration authority.
30. Production state không được thay đổi bởi simulation.
31. Simulation không được tạo real entitlement.
32. Forecast không được ghi thành actual.
33. Failed payment không được coi là successful benefit delivery.
34. Termination phải có reason code.
35. Suspension phải có effective period.
36. Appeal phải reference decision cụ thể.
37. Recovery phải reference overpayment cụ thể.
38. Overpayment phải có provenance.
39. Every externally sourced fact phải có source metadata.
40. Every material decision phải có provenance.
41. AI model version phải được lưu khi AI materially contributes.
42. Sensitive field access phải audit được.
43. Cross-jurisdiction transfer phải có authority.
44. Program identity phải globally unique trong namespace.
45. Event IDs phải idempotent.
46. Concurrent case mutations phải detect conflict.
47. Payment instructions không được duplicate khi retry.
48. Historical legal basis không được bị thay bằng current legal basis.
49. Human override phải được ghi nhận.
50. Emergency override phải audit và expire.

---

# 70. Testing Strategy

Target tối thiểu:

```text
≥ 20,000 automated tests
```

phân bổ:

```text
type tests
rule tests
temporal tests
workflow tests
payment tests
pension tests
appeal tests
privacy tests
security tests
concurrency tests
replay tests
property tests
fuzz tests
AI-boundary tests
simulation isolation tests
```

Đặc biệt phải có:

```text
same-input deterministic replay
```

và:

```text
historical-rule regression
```

---

# 71. Property-Based Tests

Ví dụ:

```text
Payment cannot exist without Award
```

```text
Award cannot exist without Entitlement
```

```text
Entitlement cannot exist without LegalBasis
```

```text
Retry(PaymentInstruction)
    == one effective payment instruction
```

```text
Replay(snapshot, rule_version)
    == original decision
```

---

# 72. Disaster Recovery

Phải hỗ trợ:

```text
event replication
snapshot
point-in-time recovery
cross-region replication
audit preservation
payment reconciliation
case recovery
```

Không được phục hồi database mà mất audit trail.

---

# 73. Offline / Low-Connectivity

Một số welfare systems cần hoạt động tại vùng mạng yếu.

Hỗ trợ:

```text
offline case capture
signed local records
deferred synchronization
conflict resolution
encrypted local storage
```

Không được cho offline client tự tạo authoritative payment settlement.

---

# 74. WASM / Mobile

Một phần rule engine có thể compile xuống:

```text
WASM
mobile
edge
desktop
```

Ví dụ:

```text
eligibility pre-check
document validation
benefit calculator
offline case intake
```

Nhưng authoritative state vẫn thuộc trusted government runtime.

---

# 75. Distributed Architecture

Partition key có thể là:

```text
program_id
jurisdiction_id
beneficiary_id
household_id
case_id
```

Event stream:

```text
application.events
eligibility.events
entitlement.events
payment.events
appeal.events
recovery.events
audit.events
```

---

# 76. Exactly-Once Semantic Layer

Transport không nhất thiết phải exactly-once.

Axiom phải cung cấp:

```text
idempotency key
deduplication
transaction identity
event identity
reconciliation
```

để đạt:

```text
exactly-once business effect
```

khi transport chỉ cung cấp at-least-once delivery.

---

# 77. Observability

Native metrics:

```text
applications/sec
eligibility/sec
benefit_awards/sec
payments/sec
appeals/sec
recovery/sec
rule_latency
case_age
processing_backlog
duplicate_rate
reconciliation_error
```

Distributed tracing phải giữ:

```text
application_id
case_id
entitlement_id
award_id
payment_id
decision_id
```

---

# 78. Compiler Integration

Compiler phải hiểu:

```text
@welfare_program
@eligibility_rule
@benefit_rule
@case_workflow
@payment_rule
@legal_basis
@privacy_class
@audit
@human_approval
```

Những annotation này không chỉ là comments.

Compiler có thể dùng chúng để:

```text
generate validation
generate audit metadata
generate schemas
generate capability checks
generate optimized rule code
generate event schemas
```

---

# 79. Zero-Cost Abstraction

Các abstraction nghiệp vụ phải compile xuống native representation.

Ví dụ:

```axiom
BenefitAmount
```

không bắt buộc tạo dynamic object.

Compiler có thể hạ thành:

```text
integer/fixed-point value
```

với metadata nằm ngoài hot path.

---

# 80. Monetary Arithmetic

Không dùng floating point cho tiền.

Native types:

```text
Money
Decimal
Rate
Percentage
BasisPoints
Currency
```

Ví dụ:

```axiom
money(1234, VND)
```

hoặc:

```axiom
Money<VND>
```

Phải có overflow checking.

---

# 81. Fixed-Point Arithmetic

Benefit formulas có thể dùng:

```text
i128
u128
decimal128
fixed-point
```

tùy target.

Compiler tối ưu phép tính nếu scale cố định.

---

# 82. Program Versioning

```axiom
ProgramVersion {
    program
    version
    effective_from
    effective_until
}
```

Không được thay đổi semantics của version đã sử dụng.

---

# 83. Migration

Khi program thay đổi:

```text
Program V1
      ↓
Migration Plan
      ↓
Program V2
```

Migration phải có:

```text
compatibility
impact analysis
simulation
rollback strategy
audit
```

---

# 84. Backdated Changes

Backdated legal changes là một case đặc biệt.

Runtime phải phân biệt:

```text
effective_time
decision_time
record_time
payment_time
```

Đây là yêu cầu cực kỳ quan trọng.

---

# 85. Four-Time Model

Một event có thể có:

```text
effective_at
recorded_at
decided_at
settled_at
```

Ví dụ:

```text
Entitlement effective:
2026-01-01

Decision:
2026-02-15

Payment:
2026-02-20
```

Không được đồng nhất bốn thời điểm.

---

# 86. Final Semantic Contract

```text
AXLAW
    = legal authority

AXFISCAL
    = fiscal authority / budget / treasury

AXPOPULATION
    = identity / demographic authority

AXWELFARE
    = social protection execution

AXFINANCE
    = accounting / financial truth

AXBANKING
    = payment infrastructure
```

Và:

```text
LAW
 ↓
LEGAL ENTITLEMENT
 ↓
WELFARE PROGRAM
 ↓
APPLICATION
 ↓
ELIGIBILITY
 ↓
ENTITLEMENT
 ↓
APPROVAL
 ↓
AWARD
 ↓
PAYMENT INSTRUCTION
 ↓
PAYMENT
 ↓
OUTCOME
```

---

# 87. Civilization-Scale Social Protection Loop

```text
POPULATION
    ↓
SOCIOECONOMIC STATE
    ↓
ELIGIBILITY
    ↓
SOCIAL BENEFIT
    ↓
HOUSEHOLD INCOME
    ↓
CONSUMPTION / STABILITY
    ↓
LABOR PARTICIPATION
    ↓
TAX / CONTRIBUTION BASE
    ↓
PUBLIC REVENUE
    ↓
SOCIAL PROGRAM FUNDING
    ↓
SOCIAL BENEFIT
```

Đây là feedback loop mà `AXWELFARE` phải cho phép mô phỏng nhưng không tự ý điều khiển chính sách.

---

# 88. Acceptance Criteria

`BOOTSTRAP-698` được coi là hoàn thành khi:

- Có native model cho person/household/program/application/case.
- Có eligibility engine.
- Có versioned rules.
- Có entitlement model.
- Có benefit calculation.
- Có payment instruction.
- Có pension model.
- Có contribution records.
- Có appeal model.
- Có overpayment/recovery model.
- Có temporal semantics.
- Có provenance.
- Có privacy controls.
- Có separation of duties.
- Có AI decision boundary.
- Có anomaly/fraud boundary.
- Có policy simulation.
- Có digital twin compatibility.
- Có deterministic replay.
- Có distributed execution.
- Có GPU acceleration path.
- Có WASM/edge path.
- Có native monetary arithmetic.
- Có ≥50 semantic/security invariants.
- Có test architecture target ≥20,000 tests.
- Không yêu cầu GC trong hot path.
- Không phụ thuộc third-party runtime để thực thi core semantics.

---

# 89. Architectural Conclusion

`AXWELFARE` trở thành **social-protection execution substrate** của Axiom.

Nó không phải:

```text
tax engine
accounting engine
banking system
legal system
healthcare system
population registry
```

mà là lớp kết nối:

```text
LEGAL RIGHTS
      +
FISCAL FUNDING
      +
POPULATION DATA
      +
SOCIAL PROGRAM RULES
      ↓
AXWELFARE
      ↓
ENTITLEMENTS
      ↓
BENEFITS
      ↓
PAYMENTS
      ↓
SOCIAL OUTCOMES
```

Nguyên tắc tối cao:

```text
LAW DEFINES RIGHTS
FISCAL DEFINES FUNDING
WELFARE EXECUTES PROGRAMS
FINANCE RECORDS MONEY
BANKING MOVES MONEY
AUDIT PRESERVES TRUTH
AI ASSISTS, BUT DOES NOT SILENTLY BECOME AUTHORITY
```

**BOOTSTRAP-698 — COMPLETE.**

---

# 90. Next Architecture Task

**BOOTSTRAP-699 — Native AI Civilization-Scale Government Justice, Courts, Legal Proceedings, Case Law, Dispute Resolution, Administrative Adjudication & Judicial Workflow Runtime 5.0**

**Namespace:** `AXJUSTICE`

Trọng tâm tiếp theo:

```text
AXLAW
   ↓
AXJUSTICE
   ↓
Courts
Judges
Cases
Claims
Evidence
Proceedings
Hearings
Orders
Judgments
Appeals
Enforcement
Case Law
Administrative Adjudication
Dispute Resolution
```

với ranh giới đặc biệt:

```text
Law != Court
Claim != Evidence
Evidence != Finding
Finding != Judgment
Judgment != Enforcement
AIRecommendation != JudicialDecision
LegalResearch != LegalAdvice
Simulation != Judgment
```

:::

BOOTSTRAP-698 đã hoàn tất. Theo chuỗi tự động, task tiếp theo là **BOOTSTRAP-699 — AXJUSTICE**.