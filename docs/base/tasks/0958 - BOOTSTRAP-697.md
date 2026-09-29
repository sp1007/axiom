Tiếp tục chuỗi kiến trúc. BOOTSTRAP-697 sẽ tách lớp **thực thi nguồn lực của chính phủ** khỏi `AXFISCAL`: mua sắm công, hợp đồng, tài sản công, DNNN và PPP, nhưng vẫn giữ liên kết chặt với ngân sách, pháp luật, kế toán và các domain vận hành.

:::writing{variant="document" id="74126" title="BOOTSTRAP-697 — Native AI Civilization-Scale Public Procurement, Government Contracting, Public Assets, State-Owned Enterprises, Public-Private Partnerships & Government Resource Allocation Runtime 5.0"}

# BOOTSTRAP-697
## Native AI Civilization-Scale Public Procurement, Government Contracting, Public Assets, State-Owned Enterprises, Public-Private Partnerships & Government Resource Allocation Runtime 5.0

**Axiom Architecture Series:** Civilization Runtime  
**Module:** `AXPUBLIC`  
**Status:** Architecture Specification v5.0  
**Task:** BOOTSTRAP-697  
**Primary Domain:** Public Procurement / Government Contracting / Public Assets / SOE / PPP / Public Resource Allocation

---

# 1. Mục tiêu

`AXPUBLIC` là runtime quản lý **việc chính phủ biến quyền hạn và ngân sách thành hàng hóa, dịch vụ, công trình, tài sản và năng lực cung ứng thực tế**.

Nếu:

```text
AXGOV    = Chính phủ có quyền làm gì?
AXLAW    = Pháp luật cho phép gì?
AXFISCAL = Chính phủ có nguồn lực tài chính nào?
```

thì:

```text
AXPUBLIC = Chính phủ sử dụng nguồn lực đó như thế nào?
```

Phạm vi:

```text
PUBLIC_PROCUREMENT
GOVERNMENT_CONTRACTING
TENDER
BIDDING
SUPPLIER
CONTRACT
PURCHASE_ORDER
DELIVERY_ACCEPTANCE
PUBLIC_PROJECT
PUBLIC_ASSET
ASSET_LIFECYCLE
STATE_OWNED_ENTERPRISE
PUBLIC_CORPORATION
PPP
CONCESSION
PUBLIC_SERVICE_CONTRACT
RESOURCE_ALLOCATION
CONTRACT_PERFORMANCE
PUBLIC_VALUE_ANALYSIS
PUBLIC_PROJECT_SIMULATION
```

---

# 2. Architectural Position

```text
                         AXLAW
                           │
                           ▼
                         AXGOV
                           │
                           ▼
                       AXFISCAL
                           │
                           ▼
                       AXPUBLIC
                     /     │      \
                    /      │       \
                   ▼       ▼        ▼
            PROCUREMENT CONTRACT  ASSETS
                   │       │        │
                   └───────┼────────┘
                           ▼
                    PUBLIC PROJECTS
                           │
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
       CONSTRUCTION    MANUFACTURING   SERVICES
             │             │              │
             └─────────────┼──────────────┘
                           ▼
                       AXFINANCE
```

PPP:

```text
AXGOV
  │
AXFISCAL
  │
AXPUBLIC
  │
PPP / CONCESSION
  │
PRIVATE OPERATOR
  │
REAL ECONOMY
```

---

# 3. Core Semantic Boundaries

Các distinction sau là bắt buộc.

```text
Budget != Procurement
Appropriation != Tender
Tender != Contract
Contract != PurchaseOrder
PurchaseOrder != Payment
Supplier != Contractor
Bid != Contract
BidPrice != FinalCost
Award != Delivery
Delivery != Acceptance
Acceptance != Payment
Project != Asset
Asset != Service
AssetOwnership != AssetOperation
PublicAsset != GovernmentCash
GovernmentContract != GovernmentAuthority
GovernmentSupplier != GovernmentEmployee
SOE != GovernmentAgency
SOE != GovernmentBudget
PPP != Privatization
PPP != Procurement
Concession != OwnershipTransfer
Forecast != ActualCost
RiskSignal != LegalViolation
BidAnomaly != FraudFinding
AIRecommendation != AwardDecision
Simulation != Contract
```

---

# 4. Responsibility Boundary

## 4.1 AXGOV

Quản lý:

```text
government authority
agency
institution
public mandate
administrative structure
```

## 4.2 AXLAW

Quản lý:

```text
legal authority
legal rules
rights
obligations
disputes
legal validity
```

## 4.3 AXFISCAL

Quản lý:

```text
budget
appropriation
public revenue
public expenditure
treasury
debt
fiscal authority
```

## 4.4 AXPUBLIC

Quản lý:

```text
procurement
contracting
supplier relationship
public asset
project execution
PPP
SOE relationship
resource allocation
```

## 4.5 AXFINANCE

Quản lý:

```text
accounting truth
financial statements
ledger
financial recognition
```

---

# 5. Public Procurement

Public procurement lifecycle:

```text
Need
 ↓
ProcurementPlan
 ↓
BudgetCheck
 ↓
Specification
 ↓
MarketResearch
 ↓
TenderPreparation
 ↓
Publication
 ↓
BidSubmission
 ↓
BidEvaluation
 ↓
Award
 ↓
Contract
 ↓
Delivery
 ↓
Acceptance
 ↓
Invoice
 ↓
Payment
 ↓
Closeout
 ↓
Audit
```

---

# 6. Procurement Need

```text
struct ProcurementNeed {
    id: ProcurementNeedId
    government: GovernmentId
    agency: GovernmentAgencyId
    category: ProcurementCategory
    description: String
    estimated_value: Money
    required_date: Option<Date>
    budget_ref: Option<AppropriationId>
    priority: ProcurementPriority
}
```

---

# 7. Procurement Plan

```text
struct ProcurementPlan {
    id: ProcurementPlanId
    government: GovernmentId
    fiscal_period: FiscalPeriod
    needs: []ProcurementNeed
    estimated_total: Money
    status: ProcurementPlanStatus
}
```

Plan không tạo quyền chi tiền.

```text
ProcurementPlan != Appropriation
```

---

# 8. Procurement Category

```text
enum ProcurementCategory {
    GOODS
    SERVICES
    WORKS
    CONSULTING
    SOFTWARE
    INFRASTRUCTURE
    EQUIPMENT
    MAINTENANCE
    RESEARCH
    PROFESSIONAL_SERVICE
    OTHER
}
```

---

# 9. Procurement Procedure

```text
enum ProcurementProcedure {
    OPEN_TENDER
    RESTRICTED_TENDER
    REQUEST_FOR_QUOTATION
    DIRECT_PURCHASE
    NEGOTIATED
    COMPETITIVE_DIALOGUE
    FRAMEWORK_AGREEMENT
    EMERGENCY_PROCUREMENT
    DESIGN_COMPETITION
    CONCESSION
    OTHER
}
```

Không hard-code một procedure là hợp pháp trong mọi jurisdiction.

---

# 10. Tender

```text
struct Tender {
    id: TenderId
    procurement_need: ProcurementNeedId
    procedure: ProcurementProcedure
    issuing_authority: AuthorityRef
    estimated_value: Money
    currency: CurrencyId
    submission_deadline: Timestamp
    evaluation_method: EvaluationMethod
    status: TenderStatus
}
```

---

# 11. Tender Lifecycle

```text
Draft
 ↓
Approved
 ↓
Published
 ↓
Open
 ↓
SubmissionClosed
 ↓
Evaluation
 ↓
AwardPending
 ↓
Awarded
 ↓
Contracted
```

Branches:

```text
Cancelled
Failed
ReTendered
Disputed
```

---

# 12. Tender Specification

```text
struct TenderSpecification {
    id: SpecificationId
    tender: TenderId
    requirements: []Requirement
    technical_criteria: []EvaluationCriterion
    commercial_criteria: []EvaluationCriterion
    compliance_requirements: []Requirement
}
```

Specification phải versioned.

---

# 13. Requirement

```text
struct Requirement {
    id: RequirementId
    type: RequirementType
    description: String
    mandatory: Bool
    verification: VerificationMethod
}
```

Ví dụ:

```text
technical
financial
legal
security
quality
delivery
sustainability
experience
```

---

# 14. Supplier

```text
struct PublicSupplier {
    id: SupplierId
    actor: ActorId
    legal_entity: LegalEntityRef
    registration: SupplierRegistration
    classifications: []SupplierClassification
    status: SupplierStatus
}
```

Supplier không đồng nghĩa:

```text
ApprovedSupplier
```

---

# 15. Supplier Qualification

```text
struct SupplierQualification {
    supplier: SupplierId
    criteria: []QualificationResult
    evaluated_at: Timestamp
    valid_until: Option<Date>
}
```

Qualification phải có provenance.

---

# 16. Bid

```text
struct Bid {
    id: BidId
    tender: TenderId
    supplier: SupplierId
    submitted_at: Timestamp
    price: Money
    currency: CurrencyId
    technical_response: DocumentRef
    commercial_response: DocumentRef
    status: BidStatus
}
```

---

# 17. Bid State

```text
Submitted
 ↓
Validated
 ↓
Eligible
 ↓
Evaluated
 ↓
Ranked
 ↓
Selected
```

Nhánh:

```text
Rejected
Withdrawn
Disqualified
```

---

# 18. Bid Evaluation

```text
struct BidEvaluation {
    bid: BidId
    criteria: []CriterionScore
    evaluator: ActorId
    methodology: EvaluationMethod
    result: EvaluationResult
}
```

Không nên lưu chỉ:

```text
score = 87
```

mà phải lưu:

```text
criteria
weights
raw_values
normalization
method
evaluator
timestamp
```

---

# 19. Evaluation Method

```text
enum EvaluationMethod {
    LOWEST_PRICE
    BEST_VALUE
    QUALITY_COST
    TECHNICAL_QUALITY
    LIFECYCLE_COST
    CUSTOM_WEIGHTED
}
```

Evaluation method là metadata của tender, không phải universal rule.

---

# 20. Bid Anomaly

AI/statistical system có thể phát hiện:

```text
price_anomaly
timing_anomaly
duplicate_document
supplier_network_anomaly
collusion_signal
specification_anomaly
```

Nhưng:

```text
AnomalySignal != FraudFinding
```

---

# 21. Procurement Award

```text
struct ProcurementAward {
    id: AwardId
    tender: TenderId
    selected_bid: BidId
    authority: AuthorityRef
    awarded_amount: Money
    awarded_at: Timestamp
    status: AwardStatus
}
```

Award phải trace được về:

```text
Tender
Bid
Evaluation
Authority
```

---

# 22. Award ≠ Contract

Award tạo ra kết quả lựa chọn.

Contract tạo ra nghĩa vụ pháp lý/kinh tế.

```text
Award
  ↓
ContractNegotiation
  ↓
ContractExecution
```

---

# 23. Government Contract

```text
struct GovernmentContract {
    id: GovernmentContractId
    government: GovernmentId
    supplier: SupplierId
    procurement: ProcurementRef
    value: Money
    currency: CurrencyId
    start_date: Date
    end_date: Option<Date>
    payment_terms: PaymentTerms
    performance_terms: []PerformanceTerm
    status: ContractStatus
}
```

---

# 24. Contract Lifecycle

```text
Draft
 ↓
Negotiation
 ↓
Approved
 ↓
Signed
 ↓
Active
 ↓
Suspended
 ↓
Completed
```

Branches:

```text
Amended
Terminated
Cancelled
Disputed
Expired
```

---

# 25. Contract Amendment

```text
struct ContractAmendment {
    id: ContractAmendmentId
    contract: GovernmentContractId
    previous_version: ContractVersionId
    changes: []ContractChange
    authority: AuthorityRef
    effective_date: Date
}
```

Không overwrite contract history.

---

# 26. Purchase Order

```text
struct PublicPurchaseOrder {
    id: PurchaseOrderId
    contract: GovernmentContractId
    supplier: SupplierId
    items: []PurchaseOrderLine
    total: Money
    status: PurchaseOrderStatus
}
```

Quan hệ:

```text
Contract
    ↓
PurchaseOrder
    ↓
Delivery
```

---

# 27. Delivery

```text
struct PublicDelivery {
    id: DeliveryId
    purchase_order: PurchaseOrderId
    delivered_items: []DeliveredItem
    delivered_at: Timestamp
    status: DeliveryStatus
}
```

---

# 28. Acceptance

```text
struct DeliveryAcceptance {
    id: AcceptanceId
    delivery: DeliveryId
    accepted_by: AuthorityRef
    accepted_items: []AcceptedItem
    rejected_items: []RejectedItem
    accepted_at: Timestamp
}
```

Acceptance không tự động tạo payment.

---

# 29. Invoice

```text
struct PublicInvoice {
    id: PublicInvoiceId
    contract: GovernmentContractId
    supplier: SupplierId
    amount: Money
    invoice_date: Date
    status: InvoiceStatus
}
```

---

# 30. Payment Bridge

```text
AXPUBLIC
    ↓
validated invoice
    ↓
AXFISCAL
    ↓
payment authorization
    ↓
treasury
    ↓
AXBANKING
    ↓
settlement
    ↓
AXFINANCE
```

---

# 31. Procurement Financial Boundary

`AXPUBLIC` không tự ghi sổ cái tài chính.

Nó phát ra:

```text
Commitment
Obligation
Invoice
Acceptance
PaymentRequest
```

`AXFISCAL` quyết định fiscal authorization.

`AXFINANCE` ghi nhận accounting effect.

---

# 32. Public Project

```text
struct PublicProject {
    id: PublicProjectId
    government: GovernmentId
    program: ProgramId
    objective: String
    budget: Money
    schedule: ProjectSchedule
    funding: FinancingPlan
    status: ProjectStatus
}
```

---

# 33. Project Lifecycle

```text
Concept
 ↓
Feasibility
 ↓
Appraisal
 ↓
Approved
 ↓
Procurement
 ↓
Construction/Implementation
 ↓
Commissioning
 ↓
Operational
 ↓
Closed
```

---

# 34. Project Appraisal

```text
struct ProjectAppraisal {
    project: PublicProjectId
    capital_cost: Money
    operating_cost: Money
    expected_benefits: []BenefitEstimate
    risks: []ProjectRisk
    assumptions: []ModelAssumption
    methodology: ModelRef
}
```

---

# 35. Cost-Benefit Analysis

Hỗ trợ:

```text
NPV
IRR
economic_NPV
lifecycle_cost
benefit_cost_ratio
sensitivity_analysis
```

Nhưng:

```text
ModelResult != ProjectApproval
```

---

# 36. Lifecycle Cost

```text
LifecycleCost =
    Acquisition
  + Construction
  + Operation
  + Maintenance
  + Upgrade
  + Decommissioning
```

Không được đánh giá asset chỉ theo purchase price nếu policy yêu cầu lifecycle evaluation.

---

# 37. Public Asset

```text
struct PublicAsset {
    id: PublicAssetId
    owner: PublicOwnerRef
    asset_class: AssetClass
    acquisition: AssetAcquisition
    valuation: AssetValuation
    location: Option<LocationRef>
    lifecycle: AssetLifecycle
    operator: Option<ActorId>
    status: PublicAssetStatus
}
```

---

# 38. Asset Classes

```text
LAND
BUILDING
ROAD
BRIDGE
RAIL
PORT
AIRPORT
UTILITY
WATER_SYSTEM
ENERGY_INFRASTRUCTURE
PUBLIC_EQUIPMENT
VEHICLE
IT_SYSTEM
TELECOM
NATURAL_RESOURCE
FINANCIAL_ASSET
CULTURAL_ASSET
INTELLECTUAL_PROPERTY
OTHER
```

---

# 39. Asset Ownership

Phải phân biệt:

```text
LegalOwner
EconomicOwner
Custodian
Operator
Manager
Beneficiary
```

Ví dụ:

```text
Government owns road
Municipality operates road
Contractor maintains road
Public receives service
```

Không được gộp thành một actor.

---

# 40. Asset Lifecycle

```text
Planned
 ↓
Acquired
 ↓
Constructed
 ↓
Commissioned
 ↓
Operational
 ↓
Maintained
 ↓
Upgraded
 ↓
Retired
 ↓
Disposed
```

---

# 41. Asset Acquisition

```text
struct AssetAcquisition {
    method: AcquisitionMethod
    date: Date
    cost: Money
    procurement_ref: Option<ProcurementRef>
    contract_ref: Option<GovernmentContractId>
}
```

---

# 42. Asset Valuation

```text
struct AssetValuation {
    amount: Money
    valuation_date: Date
    methodology: ValuationMethod
    valuer: ActorId
}
```

Các methodology:

```text
COST
MARKET
INCOME
REPLACEMENT
SPECIALIZED
```

Valuation ≠ cash value.

---

# 43. Asset Maintenance

```text
struct AssetMaintenancePlan {
    asset: PublicAssetId
    maintenance_interval: Duration
    expected_cost: Money
    responsible_operator: ActorId
}
```

---

# 44. Asset Condition

```text
enum AssetCondition {
    NEW
    GOOD
    FAIR
    DEGRADED
    CRITICAL
    NON_OPERATIONAL
}
```

Condition phải dựa trên measurement/model.

Không được suy diễn từ giá trị tài sản.

---

# 45. Asset Utilization

```text
struct AssetUtilization {
    asset: PublicAssetId
    period: TimeRange
    utilization_rate: Decimal
    capacity: Quantity
    actual_usage: Quantity
}
```

---

# 46. Public Asset Registry

```text
struct PublicAssetRegistry {
    assets: []PublicAssetId
    ownership: []OwnershipRecord
    operators: []OperatorAssignment
    valuations: []AssetValuation
    maintenance: []AssetMaintenancePlan
}
```

---

# 47. Asset Disposal

```text
struct AssetDisposal {
    asset: PublicAssetId
    method: DisposalMethod
    authorization: AuthorityRef
    consideration: Option<Money>
    date: Date
}
```

Không được xóa asset khỏi historical registry.

---

# 48. Asset Disposal Methods

```text
SALE
TRANSFER
LEASE
DEMOLITION
RETIREMENT
DONATION
CONCESSION
OTHER
```

---

# 49. Public Land

Land có semantic riêng:

```text
struct PublicLandAsset {
    asset: PublicAssetId
    parcel: LandParcelRef
    zoning: Option<ZoningRef>
    rights: []LandRight
}
```

Phần legal land rights thuộc `AXLAW`; asset/resource representation thuộc `AXPUBLIC`.

---

# 50. Natural Resource Asset

```text
struct PublicNaturalResource {
    asset: PublicAssetId
    resource_type: ResourceType
    estimated_reserve: Quantity
    extraction_right: Option<RightRef>
}
```

Khai thác thực tế liên kết:

```text
AXRESOURCE
```

---

# 51. State-Owned Enterprise

```text
struct StateOwnedEnterprise {
    id: SOEId
    legal_entity: LegalEntityRef
    government_owner: GovernmentId
    ownership_share: Decimal
    governance_model: SOEGovernanceModel
    financial_profile: FinancialProfileRef
    status: SOEStatus
}
```

---

# 52. SOE ≠ Government Agency

```text
GovernmentAgency
    = public administrative authority

SOE
    = enterprise
```

SOE có:

```text
revenue
cost
assets
liabilities
employees
customers
contracts
financial statements
```

theo `AXFINANCE` và enterprise domains.

---

# 53. Government–SOE Relationship

Hỗ trợ:

```text
ownership
capital_injection
dividend
subsidy
guarantee
loan
public_service_obligation
procurement
regulatory_control
```

Không được coi tất cả là một loại transaction.

---

# 54. SOE Capital Injection

```text
struct SOECapitalInjection {
    government: GovernmentId
    soe: SOEId
    amount: Money
    instrument: CapitalInstrument
    authority: AuthorityRef
}
```

---

# 55. Government Dividend

```text
struct SOEDividend {
    soe: SOEId
    government: GovernmentId
    declared: Money
    paid: Money
    period: FiscalPeriod
}
```

Dividend có thể là public revenue nhưng không phải tax revenue.

---

# 56. Public Service Obligation

```text
struct PublicServiceObligation {
    id: PSOId
    government: GovernmentId
    provider: ActorId
    service: ServiceRef
    required_level: ServiceLevel
    compensation: Option<Money>
    period: TimeRange
}
```

---

# 57. Public Service Contract

```text
struct PublicServiceContract {
    id: PublicServiceContractId
    government: GovernmentId
    provider: ActorId
    service: ServiceRef
    term: TimeRange
    payment_model: PaymentModel
    performance_metrics: []ServiceMetric
}
```

---

# 58. PPP

PPP là một contractual/institutional structure dài hạn giữa khu vực công và tư.

```text
struct PublicPrivatePartnership {
    id: PPPId
    government: GovernmentId
    private_partner: ActorId
    project: PublicProjectId
    contract: GovernmentContractId
    financing: PPPFinancing
    risk_allocation: RiskAllocation
    concession: Option<ConcessionRef>
    term: TimeRange
    status: PPPStatus
}
```

---

# 59. PPP ≠ Privatization

```text
PPP
=
shared contractual responsibility

Privatization
=
ownership/control transfer model
```

Không được coi hai khái niệm là synonym.

---

# 60. PPP Lifecycle

```text
Concept
 ↓
ValueForMoneyAssessment
 ↓
Feasibility
 ↓
MarketSounding
 ↓
Tender
 ↓
Selection
 ↓
FinancialClose
 ↓
Construction
 ↓
Operation
 ↓
Monitoring
 ↓
Handover/Expiry
```

---

# 61. PPP Risk Allocation

```text
struct RiskAllocation {
    construction_risk: RiskHolder
    demand_risk: RiskHolder
    availability_risk: RiskHolder
    financing_risk: RiskHolder
    regulatory_risk: RiskHolder
    operational_risk: RiskHolder
    force_majeure_risk: RiskHolder
}
```

Risk assignment phải explicit.

---

# 62. PPP Revenue Models

```text
enum PPPPaymentModel {
    GOVERNMENT_PAYMENT
    USER_FEE
    AVAILABILITY_PAYMENT
    REVENUE_SHARE
    MIXED
}
```

---

# 63. PPP Contingent Liability

PPP có thể tạo:

```text
availability_payment
minimum_revenue_guarantee
termination_payment
debt_guarantee
exchange_rate_guarantee
```

Các nghĩa vụ này phải được đưa sang:

```text
AXFISCAL
```

dưới dạng:

```text
ContingentLiability
```

hoặc obligation khi trở thành hiện thực.

---

# 64. Concession

```text
struct Concession {
    id: ConcessionId
    grantor: GovernmentId
    operator: ActorId
    asset: PublicAssetId
    service: ServiceRef
    term: TimeRange
    rights: []ConcessionRight
    obligations: []ConcessionObligation
}
```

Concession không tự động chuyển quyền sở hữu.

---

# 65. Public Resource Allocation

```text
struct PublicResourceAllocation {
    id: AllocationId
    government: GovernmentId
    resource: PublicResourceRef
    recipient: ActorId
    quantity: Quantity
    purpose: AllocationPurpose
    authority: AuthorityRef
    period: TimeRange
}
```

Resources có thể là:

```text
money
land
infrastructure_capacity
spectrum
water_right
energy_capacity
public_service_capacity
data_access
```

---

# 66. Allocation ≠ Ownership

Ví dụ:

```text
Government allocates land use right
```

không nhất thiết:

```text
Government transfers land ownership
```

Legal semantics thuộc `AXLAW`.

---

# 67. Public Capacity

Có thể biểu diễn:

```text
struct PublicCapacity {
    id: CapacityId
    resource: PublicResourceRef
    total: Quantity
    reserved: Quantity
    allocated: Quantity
    available: Quantity
}
```

Invariant:

```text
reserved + allocated <= total
```

trừ capacity models có overbooking semantics explicit.

---

# 68. Public Infrastructure Capacity

Ví dụ:

```text
road_capacity
hospital_capacity
school_capacity
electricity_capacity
water_capacity
port_capacity
airport_capacity
```

Các domain vận hành thực tế thuộc module tương ứng.

`AXPUBLIC` chỉ giữ:

```text
ownership
allocation
contract
funding
governance
```

---

# 69. Public Procurement Marketplace

Có thể cung cấp:

```text
SupplierRegistry
TenderRegistry
ContractRegistry
AwardRegistry
PerformanceRegistry
```

Nhưng không phải marketplace thương mại tổng quát.

```text
AXPUBLIC != AXCOMMERCE
```

---

# 70. Supplier Performance

```text
struct SupplierPerformance {
    supplier: SupplierId
    contract: GovernmentContractId
    delivery_score: Option<Decimal>
    quality_score: Option<Decimal>
    schedule_performance: Option<Decimal>
    compliance_status: ComplianceStatus
    incidents: []ContractIncident
}
```

Scores phải có methodology.

Không được biến một score thành universal reputation về con người.

---

# 71. Contract Performance

```text
struct ContractPerformance {
    contract: GovernmentContractId
    milestones: []MilestoneResult
    deliverables: []DeliverableResult
    payments: []PaymentRef
    penalties: []PenaltyRef
    changes: []ContractChange
}
```

---

# 72. Milestone

```text
struct ContractMilestone {
    id: MilestoneId
    contract: GovernmentContractId
    due_date: Date
    deliverable: DeliverableRef
    payment_condition: Option<PaymentCondition>
}
```

---

# 73. Performance-Based Payment

```text
Payment
    ←
Milestone
    ←
Acceptance
    ←
Evidence
```

Payment không nên chỉ dựa trên:

```text
invoice.exists
```

nếu contract yêu cầu performance evidence.

---

# 74. Contract Penalty

```text
struct ContractPenalty {
    contract: GovernmentContractId
    trigger: ContractEvent
    amount: Money
    authority: AuthorityRef
    status: PenaltyStatus
}
```

Penalty determination phải tách khỏi AI anomaly detection.

---

# 75. Contract Dispute

```text
struct ContractDispute {
    id: DisputeId
    contract: GovernmentContractId
    parties: []ActorId
    issue: DisputeIssue
    amount: Option<Money>
    forum: DisputeForum
    status: DisputeStatus
}
```

Legal resolution thuộc:

```text
AXLAW
```

---

# 76. Procurement Integrity

Hệ thống phải hỗ trợ:

```text
conflict_of_interest
supplier_relationship
bid_collusion_signal
duplicate_bid
abnormal_pricing
specification_bias_signal
procurement_split_signal
unusual_amendment
```

Nhưng:

```text
Signal != Finding
```

---

# 77. Procurement Audit Graph

```text
Need
 ↓
Plan
 ↓
Budget
 ↓
Tender
 ↓
Bid
 ↓
Evaluation
 ↓
Award
 ↓
Contract
 ↓
Delivery
 ↓
Acceptance
 ↓
Invoice
 ↓
Payment
 ↓
Asset
```

Mỗi node phải trace được.

---

# 78. Provenance

Mỗi procurement decision phải giữ:

```text
source_documents
criteria
versions
evaluators
authority
timestamps
calculations
communications_ref
```

---

# 79. AI Procurement

AI có thể:

```text
market_research
cost_estimation
supplier_discovery
document_extraction
bid_comparison
anomaly_detection
schedule_prediction
cost_forecasting
contract_analysis
risk_analysis
```

Mặc định không được:

```text
award_contract
reject_supplier
disqualify_bid
change_tender
sign_contract
authorize_payment
```

---

# 80. AI Evaluation Boundary

AI có thể tạo:

```text
EvaluationRecommendation
```

nhưng final:

```text
AwardDecision
```

phải có authorized decision-maker hoặc authority policy.

---

# 81. AI Explainability

AI procurement output:

```text
recommendation
inputs
criteria
weights
model
model_version
confidence
uncertainty
excluded_data
limitations
```

---

# 82. AI Bias Monitoring

Hệ thống có thể kiểm tra:

```text
supplier concentration
geographic concentration
bid access patterns
qualification barrier patterns
evaluation sensitivity
```

nhưng không được suy diễn sensitive attributes trái phép.

---

# 83. Procurement Simulation

Có thể mô phỏng:

```text
supplier_exit
price_shock
delivery_delay
currency_shock
material_shortage
demand_change
contract_failure
```

Simulation không thay đổi tender thật.

---

# 84. Public Project Digital Twin

```text
struct PublicProjectTwin {
    project: PublicProjectId
    physical_state: ProjectPhysicalState
    financial_state: ProjectFinancialState
    contract_state: ProjectContractState
    schedule_state: ProjectScheduleState
    risk_state: ProjectRiskState
}
```

Các state có provenance riêng.

---

# 85. Project State

```text
Planned
Approved
Procurement
UnderConstruction
Delayed
Operational
Suspended
Cancelled
Completed
```

---

# 86. Project Risk

```text
struct ProjectRisk {
    id: ProjectRiskId
    project: PublicProjectId
    category: RiskCategory
    probability: Option<Decimal>
    impact: Option<Money>
    model: Option<ModelRef>
    owner: Option<ActorId>
}
```

---

# 87. Risk Categories

```text
COST
SCHEDULE
TECHNICAL
FINANCIAL
SUPPLY
LEGAL
REGULATORY
ENVIRONMENTAL
DEMAND
OPERATIONAL
SECURITY
FORCE_MAJEURE
```

---

# 88. Government Contract Graph

```text
Government
 ├── Agency
 │    └── ProcurementNeed
 │          └── Tender
 │               ├── Bid
 │               │    └── Supplier
 │               └── Award
 │                    └── Contract
 │                         ├── PO
 │                         ├── Delivery
 │                         ├── Acceptance
 │                         └── Invoice
 │                              └── Payment
 │
 └── PublicAsset
```

---

# 89. SOE Graph

```text
Government
   │
   ├── owns
   ▼
SOE
   ├── assets
   ├── liabilities
   ├── employees
   ├── customers
   └── contracts
```

Government interactions:

```text
ownership
capital
dividend
guarantee
subsidy
procurement
public_service_obligation
```

---

# 90. PPP Graph

```text
Government
    │
    ▼
PublicProject
    │
    ▼
PPP
 ┌──┴──────────────┐
 ▼                 ▼
Government      PrivatePartner
 │                 │
 ▼                 ▼
Funding          Financing
 │                 │
 └───────┬─────────┘
         ▼
      Project
         │
         ▼
      Asset/Service
```

---

# 91. Public Value Model

Có thể mô hình hóa:

```text
struct PublicValueAssessment {
    project: PublicProjectId
    fiscal_cost: Money
    economic_benefit: Option<Money>
    service_benefit: Option<Quantity>
    externalities: []Externality
    risk_adjustment: Option<ModelRef>
    methodology: ModelRef
}
```

Không ép mọi public value thành một monetary scalar.

---

# 92. Multi-Criteria Public Evaluation

Có thể đánh giá theo:

```text
cost
quality
time
resilience
service_capacity
lifecycle_cost
environment
accessibility
strategic_value
```

Kết quả là:

```text
EvaluationResult
```

không phải universal ranking của các chủ thể.

---

# 93. Resource Allocation Optimizer

```text
struct AllocationProblem {
    resources: []Resource
    demands: []Demand
    constraints: []Constraint
    objectives: []Objective
}
```

Solver có thể dùng:

```text
linear_programming
integer_programming
constraint_programming
network_flow
optimization
heuristics
simulation
```

---

# 94. Optimization Boundary

Optimizer trả:

```text
CandidateAllocation
```

Không tự động:

```text
ApprovedAllocation
```

Authority layer quyết định.

---

# 95. Fiscal Integration

```text
AXFISCAL
    │
    ├── appropriation
    ├── commitment
    ├── obligation
    └── payment
          ▲
          │
       AXPUBLIC
```

`AXPUBLIC` không được tự bypass appropriation.

---

# 96. Finance Integration

```text
AXPUBLIC
    ↓
economic event
    ↓
AXFISCAL
    ↓
fiscal event
    ↓
AXFINANCE
    ↓
ledger/accounting
```

---

# 97. Commerce Integration

Supplier discovery có thể dùng:

```text
AXCOMMERCE
```

nhưng public procurement vẫn có:

```text
special authority
special procedure
special audit
```

Không biến tender thành ordinary shopping cart.

---

# 98. Construction Integration

Public infrastructure:

```text
AXPUBLIC
   ↓
public project
   ↓
AXCONSTRUCTION
```

`AXCONSTRUCTION` quản lý:

```text
design
construction
materials
equipment
workers
site
schedule
```

`AXPUBLIC` quản lý:

```text
public ownership
procurement
contract
funding
acceptance
asset
```

---

# 99. Manufacturing Integration

Public equipment:

```text
AXPUBLIC
   ↓
procurement
   ↓
AXMANUFACTURING
```

---

# 100. Transport Integration

Public transport asset:

```text
AXPUBLIC
   ↓
ownership / contract
   ↓
AXTRANSPORT
```

---

# 101. Resource Integration

Public water/energy/resource:

```text
AXPUBLIC
   ↕
AXRESOURCE
```

`AXPUBLIC` quản lý public ownership/allocation.

`AXRESOURCE` quản lý physical resource dynamics.

---

# 102. Asset Accounting Boundary

```text
AXPUBLIC
    = asset lifecycle semantics

AXFINANCE
    = accounting valuation/recognition
```

Một asset acquisition có thể tạo:

```text
AXPUBLIC:
    AssetAcquired

AXFINANCE:
    asset_recognition
    cash/liability effect
```

---

# 103. Historical Immutability

Không được xóa:

```text
old tender
old bid
old award
old contract
old asset owner
old valuation
old PPP state
```

Correction bằng event/version mới.

---

# 104. Temporal Contract Query

Runtime phải hỗ trợ:

```text
contract_at(time)
asset_owner_at(time)
asset_operator_at(time)
tender_state_at(time)
budget_link_at(time)
ppp_state_at(time)
```

---

# 105. Versioned Procurement

Mọi tender/specification/contract phải có:

```text
version
effective_time
author
authority
change_reason
```

---

# 106. Contract Hashing

Hợp đồng điện tử có thể lưu:

```text
document_hash
canonical_representation_hash
signature_set
version_hash
```

để phát hiện thay đổi trái phép.

---

# 107. Digital Signature

```text
struct ContractSignature {
    signer: ActorId
    role: AuthorityRole
    signature: Signature
    timestamp: Timestamp
    document_hash: Hash
}
```

---

# 108. Contract Execution Security

Không cho phép:

```text
sign(contract_version_A)
execute(contract_version_B)
```

Nếu hash/version không khớp:

```text
ErrContractVersionMismatch
```

---

# 109. Payment Protection

Payment request phải trace:

```text
Contract
→ PurchaseOrder
→ Delivery
→ Acceptance
→ Invoice
→ Obligation
→ PaymentAuthorization
```

Thiếu node bắt buộc phải bị reject nếu contract/policy yêu cầu node đó.

---

# 110. Duplicate Payment Detection

System phải detect:

```text
same_invoice
same_contract
same_amount
same_supplier
same_reference
```

nhưng không chỉ dựa vào exact equality.

Hỗ trợ fuzzy duplicate detection.

---

# 111. Procurement Event Model

```text
struct ProcurementEvent {
    id: ProcurementEventId
    type: ProcurementEventType
    tender: Option<TenderId>
    contract: Option<GovernmentContractId>
    actor: ActorId
    authority: Option<AuthorityRef>
    timestamp: Timestamp
    payload: EventPayload
}
```

---

# 112. Event Types

```text
PROCUREMENT_CREATED
TENDER_PUBLISHED
BID_SUBMITTED
BID_WITHDRAWN
BID_EVALUATED
AWARD_ISSUED
CONTRACT_SIGNED
CONTRACT_AMENDED
PURCHASE_ORDER_CREATED
DELIVERY_RECEIVED
DELIVERY_ACCEPTED
INVOICE_RECEIVED
PERFORMANCE_RECORDED
CONTRACT_SUSPENDED
CONTRACT_TERMINATED

ASSET_ACQUIRED
ASSET_TRANSFERRED
ASSET_OPERATED
ASSET_MAINTAINED
ASSET_REVALUED
ASSET_RETIRED
ASSET_DISPOSED

PPP_CREATED
PPP_FINANCIAL_CLOSE
PPP_OPERATION_STARTED
PPP_TERMINATED

SOE_CAPITAL_INJECTED
SOE_DIVIDEND_DECLARED
SOE_GUARANTEE_ISSUED
```

---

# 113. Idempotency

Các operation:

```text
create_award
sign_contract
create_purchase_order
accept_delivery
submit_invoice
transfer_asset
execute_ppp_payment
```

phải hỗ trợ:

```text
IdempotencyKey
```

---

# 114. Distributed Consistency

Critical state:

```text
Tender
Contract
AssetOwnership
PaymentEligibility
```

phải có strong consistency hoặc equivalent serialized authority.

Analytics có thể eventual consistency.

---

# 115. Concurrency

Partitioning:

```text
government
procurement
tender
contract
asset
project
SOE
PPP
```

Một contract không được đồng thời có hai conflicting amendments được commit.

---

# 116. Transaction Model

Atomic operations:

```text
award_contract
accept_delivery
transfer_asset
activate_ppp
terminate_contract
```

phải đảm bảo:

```text
validate
authorize
commit
event
audit
```

---

# 117. Recovery

Recovery không xóa lịch sử.

Ví dụ:

```text
wrong_award
```

không:

```text
DELETE award
```

mà:

```text
AwardCorrection
AwardCancellation
```

theo legal/administrative rule.

---

# 118. Public Asset Recovery

Asset transfer recovery phải lưu:

```text
previous_owner
new_owner
authority
effective_time
reason
```

---

# 119. Public Transparency

Có thể publish:

```text
tender
award
contract
contract_value
supplier
project
asset
PPP
SOE ownership
```

theo transparency policy.

Không mặc định publish:

```text
protected personal data
security-sensitive information
confidential commercial information
```

---

# 120. Procurement Data Classification

```text
PUBLIC
PROCUREMENT_INTERNAL
CONFIDENTIAL
COMMERCIAL_CONFIDENTIAL
SECURITY_RESTRICTED
PERSONAL_DATA
```

Classification kết nối với:

```text
AXLAW
AX640 Data Governance
```

---

# 121. Security Capabilities

```text
public.read
public.analyze
public.simulate

procurement.read
procurement.create
procurement.publish
procurement.evaluate
procurement.award
procurement.admin

supplier.read
supplier.register
supplier.qualify

contract.read
contract.create
contract.amend
contract.sign
contract.terminate

project.read
project.create
project.manage

asset.read
asset.acquire
asset.transfer
asset.operate
asset.dispose
asset.admin

soe.read
soe.manage
soe.capital
soe.dividend
soe.guarantee

ppp.read
ppp.create
ppp.approve
ppp.manage

audit.read
admin
```

---

# 122. AI Default Profile

```text
AXPUBLIC_AI_DEFAULT {
    public.read
    public.analyze
    public.simulate
    procurement.read
    supplier.read
    contract.read
    project.read
    asset.read
}
```

Không có implicit:

```text
procurement.award
contract.sign
asset.transfer
ppp.approve
soe.capital
soe.guarantee
```

---

# 123. Separation of Duties

Có thể cấu hình:

```text
ProcurementOfficer
Evaluator
Approver
ContractOfficer
ProjectManager
AssetManager
TreasuryOfficer
Auditor
LegalOfficer
AIAnalyst
```

Ví dụ:

```text
Evaluator != FinalAwardApprover
```

nếu policy yêu cầu.

---

# 124. Dual Control

Các hành động high-impact:

```text
large_contract
asset_transfer
SOE_capital_injection
government_guarantee
PPP_financial_close
```

có thể yêu cầu:

```text
two_person_rule
multi_signature
```

---

# 125. Procurement DSL

```axiom
procurement HospitalEquipment {
    government = Republic.HealthAgency
    category = GOODS
    estimated_value = 50_000_000_000 VND

    procedure = OPEN_TENDER

    requirements {
        quality >= certified
        warranty >= 5y
        delivery <= 180d
    }

    evaluation = BEST_VALUE
}
```

---

# 126. Contract DSL

```axiom
contract HospitalEquipmentContract {
    supplier = Supplier.Acme
    value = 48_000_000_000 VND

    milestones {
        delivery = 0.70
        acceptance = 0.20
        warranty_completion = 0.10
    }
}
```

---

# 127. Public Asset DSL

```axiom
asset NationalHospital {
    class = BUILDING
    owner = Republic
    operator = HealthAgency

    lifecycle {
        acquisition = 2030
        expected_life = 50y
    }
}
```

---

# 128. PPP DSL

```axiom
ppp MetroLine01 {
    government = City
    private_partner = MetroOperator

    payment_model = AVAILABILITY_PAYMENT

    term = 30y

    risk {
        construction = private
        demand = shared
        regulatory = government
    }
}
```

---

# 129. SOE DSL

```axiom
soe NationalEnergy {
    owner = Republic
    ownership = 72%

    public_service {
        electricity_access
        emergency_supply
    }
}
```

---

# 130. Resource Allocation DSL

```axiom
allocate PublicLandParcel42 {
    recipient = InfrastructureProject01
    purpose = PUBLIC_TRANSPORT
    period = 2030..2060
}
```

Allocation không tự tạo legal title nếu thiếu authority.

---

# 131. Public Project Simulation

```axiom
simulate MetroExpansion {
    construction_cost += 15%
    completion_delay += 18m
    demand -= 10%

    outputs {
        fiscal_cost
        project_delay
        service_capacity
        contingent_liability
    }
}
```

---

# 132. AI Procurement Analyst

```axiom
agent ProcurementAnalyst {
    capabilities {
        procurement.read
        supplier.read
        contract.read
        public.analyze
        public.simulate
    }

    outputs {
        cost_anomaly
        schedule_risk
        supplier_concentration
        contract_risk
    }

    deny {
        procurement.award
        contract.sign
        asset.transfer
    }
}
```

---

# 133. Public Resource Optimization

Solver có thể tối ưu:

```text
procurement_cost
delivery_time
lifecycle_cost
capacity
risk
supplier_diversity
resilience
```

subject to:

```text
budget
law
procurement_rules
capacity
schedule
security
```

---

# 134. Supplier Network Graph

```text
Supplier
 ├── ownership
 ├── subsidiaries
 ├── contracts
 ├── bids
 ├── subcontractors
 ├── deliveries
 └── performance
```

Có thể dùng để phân tích:

```text
concentration
dependency
supply risk
single-source risk
```

Không tự suy diễn wrongdoing.

---

# 135. Government Contract Graph

```text
Government
   │
   ├── Agency
   │
   ├── Tender
   │      └── Bids
   │
   ├── Contract
   │      ├── Supplier
   │      ├── PO
   │      ├── Delivery
   │      └── Payment
   │
   └── Asset
          └── Operator
```

---

# 136. Public Asset Graph

```text
Asset
 ├── owner
 ├── custodian
 ├── operator
 ├── project
 ├── acquisition
 ├── maintenance
 ├── valuation
 ├── financing
 └── disposal
```

---

# 137. Public Finance Trace

Một public asset phải trace được:

```text
Asset
 ↓
Project
 ↓
Contract
 ↓
Procurement
 ↓
Appropriation
 ↓
Budget
 ↓
FiscalYear
```

và:

```text
Asset
 ↓
AccountingRecord
 ↓
AXFINANCE
```

---

# 138. SOE Financial Trace

```text
Government
 ↓
SOE ownership
 ↓
Capital injection
 ↓
SOE financial statements
 ↓
Dividend
 ↓
Government revenue
```

Không được tự động net tất cả thành một transaction.

---

# 139. PPP Fiscal Trace

```text
PPP
 ↓
Contract
 ↓
Risk allocation
 ↓
Government commitment
 ↓
Contingent liability
 ↓
Actual payment
 ↓
AXFISCAL
 ↓
AXFINANCE
```

---

# 140. Public Procurement Invariants

### P-01

```text
Tender != Contract
```

### P-02

```text
Bid != Award
```

### P-03

```text
Award != Contract
```

### P-04

```text
Contract != Payment
```

### P-05

```text
Delivery != Acceptance
```

### P-06

```text
Acceptance != Payment
```

### P-07

```text
ProcurementPlan != Appropriation
```

### P-08

```text
Supplier != Employee
```

### P-09

```text
SOE != GovernmentAgency
```

### P-10

```text
SOE != GovernmentBudget
```

### P-11

```text
PPP != Privatization
```

### P-12

```text
Concession != OwnershipTransfer
```

### P-13

```text
Asset != Cash
```

### P-14

```text
AssetOwner != AssetOperator
```

### P-15

```text
BidPrice != FinalCost
```

### P-16

```text
ForecastCost != ActualCost
```

### P-17

```text
RiskSignal != LegalFinding
```

### P-18

```text
BidAnomaly != FraudFinding
```

### P-19

```text
AIRecommendation != AwardDecision
```

### P-20

```text
AIRecommendation != ContractSignature
```

### P-21

```text
Simulation != LiveContract
```

### P-22

```text
Simulation != LiveAsset
```

### P-23

```text
EveryAwardHasTender
```

### P-24

```text
EveryAwardHasEvaluation
```

### P-25

```text
EveryContractHasAuthority
```

### P-26

```text
EveryContractVersionHasHash
```

### P-27

```text
EveryContractAmendmentPreservesHistory
```

### P-28

```text
EveryAssetTransferHasAuthority
```

### P-29

```text
EveryPublicPaymentHasFiscalReference
```

### P-30

```text
EveryProcurementMutationIsAuditable
```

### P-31

```text
EveryAssetMutationIsAuditable
```

### P-32

```text
EveryPPPHasExplicitRiskAllocation
```

### P-33

```text
EveryPPPHasDefinedTerm
```

### P-34

```text
EverySOECapitalInjectionHasAuthority
```

### P-35

```text
EveryGovernmentGuaranteeHasExplicitExposure
```

### P-36

```text
EveryPublicProjectHasFundingReference
```

### P-37

```text
EveryBidHasTenderReference
```

### P-38

```text
EverySupplierHasLegalIdentityReference
```

### P-39

```text
EveryAssetHasOwner
```

### P-40

```text
EveryOperationalAssetHasLifecycleState
```

### P-41

```text
NoCrossJurisdictionProcurementWithoutAuthority
```

### P-42

```text
NoImplicitCurrencyConversion
```

### P-43

```text
NoImplicitContractExecutionAuthority
```

### P-44

```text
NoImplicitAssetTransferAuthority
```

### P-45

```text
NoAIImplicitAwardAuthority
```

### P-46

```text
NoAIImplicitContractSignatureAuthority
```

### P-47

```text
NoHistoricalProcurementDeletion
```

### P-48

```text
NoHistoricalAssetOwnershipDeletion
```

### P-49

```text
ContractExecutionVersionMustMatch
```

### P-50

```text
PaymentTraceMustReachContractOrAuthorizedProgram
```

---

# 141. Procurement Performance

Metrics:

```text
procurement_cycle_time
competition_rate
bid_count
award_value
cost_variance
schedule_variance
contract_change_rate
supplier_concentration
delivery_success_rate
acceptance_failure_rate
payment_cycle_time
lifecycle_cost
```

Không một metric đơn lẻ đại diện cho toàn bộ procurement quality.

---

# 142. Project Performance

```text
budget_variance
schedule_variance
scope_change
capacity_delivered
operating_cost
maintenance_cost
service_availability
risk_realization
```

---

# 143. Asset Performance

```text
availability
utilization
condition
maintenance_cost
lifecycle_cost
service_output
downtime
remaining_life
```

---

# 144. PPP Performance

```text
service_availability
government_payment
user_revenue
demand
construction_progress
operating_cost
risk_realization
contract_compliance
```

---

# 145. SOE Performance

`AXPUBLIC` có thể lưu:

```text
ownership
public_service_metrics
government_support
dividend
guarantees
```

Nhưng financial performance chi tiết vẫn thuộc enterprise/finance layers.

---

# 146. Observability

Metrics:

```text
tender_open_count
bid_submission_rate
evaluation_latency
award_latency
contract_activation_latency
delivery_delay
acceptance_failure
contract_amendment_rate
asset_transfer_rate
project_cost_variance
PPP_contingent_exposure
SOE_public_support
```

---

# 147. Distributed Architecture

```text
Public Control Plane
       │
 ┌─────┼───────────────┐
 ▼     ▼               ▼
Procurement Contract  Asset
 ▼       ▼               ▼
Tender  Performance    Registry
 │       │               │
 └───────┼───────────────┘
         ▼
    Public Project
```

Control plane quản lý:

```text
rules
authority
schemas
workflow
policy
```

Data plane quản lý:

```text
tenders
bids
contracts
assets
events
```

---

# 148. Event Sourcing

Authoritative event streams:

```text
TenderEvents
ContractEvents
AssetEvents
ProjectEvents
PPPEvents
SOEEvents
```

Snapshot:

```text
TenderSnapshot
ContractSnapshot
AssetSnapshot
ProjectSnapshot
```

Replay phải deterministic.

---

# 149. Memory Model

Hot-path:

```text
TenderState
ContractState
AssetState
PaymentEligibilityState
```

sử dụng:

```text
struct
SoA
arena
pool
preallocation
intrusive queues
```

Không yêu cầu GC.

---

# 150. GPU

GPU phù hợp:

```text
supplier_graph_analysis
procurement_anomaly_detection
cost_forecasting
project_simulation
PPP_scenario_analysis
asset_portfolio_optimization
```

Không cần GPU cho:

```text
contract_signature_validation
single_award_commit
single_asset_transfer
```

---

# 151. Runtime Profiles

```text
AXPUBLIC_NONE
AXPUBLIC_CORE

AXPUBLIC_PROCUREMENT
AXPUBLIC_TENDER
AXPUBLIC_SUPPLIER
AXPUBLIC_CONTRACT
AXPUBLIC_PROJECT

AXPUBLIC_ASSET
AXPUBLIC_LAND
AXPUBLIC_INFRASTRUCTURE

AXPUBLIC_SOE
AXPUBLIC_PPP
AXPUBLIC_CONCESSION

AXPUBLIC_RESOURCE
AXPUBLIC_ANALYTICS
AXPUBLIC_AUDIT

AXPUBLIC_AI
AXPUBLIC_SIMULATION
AXPUBLIC_DIGITAL_TWIN

AXPUBLIC_DISTRIBUTED
AXPUBLIC_GPU
AXPUBLIC_WASM
AXPUBLIC_MOBILE
AXPUBLIC_REALTIME

AXPUBLIC_FULL
```

---

# 152. Error Model

```text
ProcurementError
TenderError
BidError
EvaluationError
AwardError
ContractError
DeliveryError
AcceptanceError
ProjectError
AssetError
SOEError
PPPError
ConcessionError
AllocationError
AuthorityError
SecurityError
VersionMismatchError
DuplicateOperationError
ReconciliationError
SimulationError
```

Các lỗi quan trọng:

```text
ErrNoBudgetReference
ErrNoProcurementAuthority
ErrTenderClosed
ErrInvalidBid
ErrAwardMissingEvaluation
ErrContractVersionMismatch
ErrAssetOwnershipConflict
ErrUnauthorizedTransfer
ErrDuplicateContract
ErrDuplicatePaymentReference
ErrPPPExposureExceeded
ErrMissingRiskAllocation
```

---

# 153. Recovery

Mọi correction dùng event mới:

```text
ContractCorrection
AwardCorrection
AssetCorrection
SupplierCorrection
ProjectCorrection
```

Không mutate lịch sử đã commit.

---

# 154. Test Architecture

Test suites:

```text
procurement/
tender/
bid/
evaluation/
award/
contract/
delivery/
acceptance/
project/
asset/
soe/
ppp/
concession/
allocation/
security/
audit/
distributed/
recovery/
simulation/
performance/
```

---

# 155. Property Tests

Ví dụ:

```text
EveryAwardHasTender
```

```text
EveryContractHasAwardOrExplicitAuthority
```

```text
AssetOwnershipTransitionIsContinuous
```

```text
ContractVersionHashIsStable
```

```text
DuplicateAwardCannotCommit
```

```text
SimulationCannotMutateProduction
```

```text
UnauthorizedAssetTransferFails
```

---

# 156. Security Tests

Phải test:

```text
unauthorized_award
unauthorized_contract_sign
unauthorized_asset_transfer
unauthorized_SOE_capital
unauthorized_PPP_approval
supplier_data_leak
bid_confidentiality_breach
contract_tampering
signature_replay
privilege_escalation
```

---

# 157. Privacy Tests

Đặc biệt:

```text
bid_confidentiality
supplier_personal_data
beneficial_owner_access
contractor_employee_data
```

Phải kiểm tra:

```text
purpose limitation
least privilege
field-level access
redaction
auditability
```

---

# 158. Deterministic Replay

Cùng:

```text
tender
bids
evaluation_rules
authority
versions
```

phải cho cùng:

```text
evaluation result
```

nếu methodology deterministic.

---

# 159. Performance Target

Mục tiêu:

```text
≥ 5M lightweight procurement/contract events/sec
```

trên hệ thống partitioned phù hợp.

Asset registry:

```text
≥ billions of asset records
```

Supplier/contract graph:

```text
≥ billions of edges
```

Simulation:

```text
massively parallel
```

---

# 160. Acceptance Criteria

BOOTSTRAP-697 hoàn thành khi:

1. Procurement lifecycle đầy đủ.
2. Tender lifecycle đầy đủ.
3. Bid model đầy đủ.
4. Evaluation methodology versioned.
5. Award authority được kiểm soát.
6. Contract lifecycle được định nghĩa.
7. Contract versioning được định nghĩa.
8. Purchase order được tách khỏi contract.
9. Delivery được tách khỏi acceptance.
10. Acceptance được tách khỏi payment.
11. Public project lifecycle được định nghĩa.
12. Project appraisal được định nghĩa.
13. Public asset registry được định nghĩa.
14. Asset ownership/operator/custodian được tách.
15. Asset lifecycle được định nghĩa.
16. Asset disposal được audit.
17. SOE model được định nghĩa.
18. Government–SOE relationship được định nghĩa.
19. Public service obligation được định nghĩa.
20. PPP model được định nghĩa.
21. PPP risk allocation được định nghĩa.
22. PPP contingent liabilities được nối với `AXFISCAL`.
23. Concession được định nghĩa.
24. Public resource allocation được định nghĩa.
25. Procurement–fiscal boundary được xác định.
26. Procurement–finance boundary được xác định.
27. Procurement–law boundary được xác định.
28. Procurement–commerce boundary được xác định.
29. Construction/manufacturing/transport/resource integration được xác định.
30. AI procurement boundary được xác định.
31. Simulation/digital twin được xác định.
32. Audit/provenance được xác định.
33. Distributed consistency được xác định.
34. Idempotency được xác định.
35. Recovery được xác định.
36. Security capability model được xác định.
37. Privacy model được xác định.
38. Runtime profiles được xác định.
39. ≥50 architecture invariants được xác định.
40. ≥20,000 automated tests target được xác định.
41. End-to-end procurement trace được xác định.
42. End-to-end asset trace được xác định.
43. End-to-end PPP fiscal trace được xác định.
44. SOE financial boundary được xác định.
45. Không có implicit AI award authority.
46. Không có implicit asset-transfer authority.
47. Không có implicit contract-signing authority.
48. Không có historical deletion.

---

# 161. Final Semantic Contract

```text
AXGOV
=
PUBLIC AUTHORITY
+
PUBLIC ADMINISTRATION

AXLAW
=
LEGAL AUTHORITY
+
LEGAL VALIDITY

AXFISCAL
=
PUBLIC REVENUE
+
BUDGET
+
TREASURY
+
PUBLIC EXPENDITURE
+
SOVEREIGN DEBT
+
FISCAL POLICY

AXPUBLIC
=
PROCUREMENT
+
GOVERNMENT CONTRACTING
+
PUBLIC PROJECTS
+
PUBLIC ASSETS
+
SOE RELATIONSHIPS
+
PPP
+
PUBLIC RESOURCE ALLOCATION

AXFINANCE
=
ACCOUNTING
+
FINANCIAL TRUTH

AXCOMMERCE
=
GENERAL COMMERCIAL TRANSACTIONS

AXCONSTRUCTION
=
PHYSICAL CONSTRUCTION EXECUTION

AXMANUFACTURING
=
INDUSTRIAL PRODUCTION

AXTRANSPORT
=
PHYSICAL MOVEMENT

AXRESOURCE
=
PHYSICAL RESOURCE SYSTEMS
```

---

# 162. Complete Government Resource Flow

```text
PUBLIC AUTHORITY
       │
       ▼
PUBLIC POLICY
       │
       ▼
BUDGET / APPROPRIATION
       │
       ▼
PUBLIC NEED
       │
       ▼
PROCUREMENT
       │
       ▼
TENDER
       │
       ▼
BID
       │
       ▼
EVALUATION
       │
       ▼
AWARD
       │
       ▼
CONTRACT
       │
       ▼
DELIVERY
       │
       ▼
ACCEPTANCE
       │
       ▼
PAYMENT
       │
       ▼
PUBLIC ASSET / PUBLIC SERVICE
       │
       ▼
PUBLIC OUTCOME
```

---

# 163. Public Capital Loop

```text
PUBLIC REVENUE
      ↓
PUBLIC BUDGET
      ↓
PUBLIC INVESTMENT
      ↓
INFRASTRUCTURE
      ↓
SERVICE CAPACITY
      ↓
ECONOMIC / SOCIAL OUTPUT
      ↓
TAX BASE
      ↓
PUBLIC REVENUE
```

---

# 164. Government Enterprise Loop

```text
PUBLIC OWNERSHIP
      ↓
SOE
      ↓
PRODUCTION / SERVICES
      ↓
REVENUE
      ↓
PROFIT / CASH FLOW
      ↓
DIVIDEND
      ↓
PUBLIC REVENUE
```

hoặc:

```text
PUBLIC POLICY
      ↓
PUBLIC SERVICE OBLIGATION
      ↓
SOE COST
      ↓
GOVERNMENT COMPENSATION
      ↓
PUBLIC BUDGET
```

Hai flow phải được phân biệt.

---

# 165. PPP Loop

```text
PUBLIC NEED
      ↓
PUBLIC PROJECT
      ↓
PPP
      ↓
PRIVATE FINANCING
      ↓
CONSTRUCTION
      ↓
OPERATION
      ↓
PUBLIC SERVICE
      ↓
GOVERNMENT PAYMENT / USER REVENUE
      ↓
PRIVATE RETURN
```

và:

```text
PPP
 ↓
CONTINGENT LIABILITY
 ↓
FISCAL RISK
 ↓
AXFISCAL
```

---

# 166. Civilization-Scale Government Resource Graph

```text
                         GOVERNMENT
                             │
          ┌──────────────────┼───────────────────┐
          │                  │                   │
          ▼                  ▼                   ▼
       REVENUE             BUDGET              DEBT
          │                  │                   │
          │                  ▼                   │
          │             PROCUREMENT             │
          │                  │                   │
          │                  ▼                   │
          │              CONTRACTS              │
          │                  │                   │
          │          ┌───────┼────────┐          │
          │          ▼       ▼        ▼          │
          │        GOODS   SERVICES  WORKS        │
          │          │       │        │          │
          │          └───────┼────────┘          │
          │                  ▼                   │
          │             PUBLIC ASSETS            │
          │                  │                   │
          │                  ▼                   │
          │             PUBLIC SERVICES          │
          │                  │                   │
          └──────────────────┴───────────────────┘
                             │
                             ▼
                     CIVILIZATION OUTPUT
```

---

# 167. BOOTSTRAP-697 Completion

Sau task này, chuỗi government-finance đã có ba lớp rõ ràng:

```text
AXGOV
   │
   │ authority
   ▼
AXFISCAL
   │
   │ money / budget
   ▼
AXPUBLIC
   │
   │ procurement / contract / asset / project
   ▼
REAL ECONOMY
```

với financial truth:

```text
             AXFINANCE
             ▲       ▲
             │       │
         AXFISCAL   AXPUBLIC
```

và legal authority:

```text
             AXLAW
               │
        ┌──────┴──────┐
        ▼             ▼
     AXGOV         AXFISCAL
                      │
                      ▼
                   AXPUBLIC
```

Boundary này ngăn `AXFISCAL` trở thành một "god module" chứa toàn bộ hoạt động của chính phủ.

---

# 168. Next Architecture Task

**BOOTSTRAP-698 — Native AI Civilization-Scale Government Revenue Administration, Social Transfers, Welfare, Pensions, Public Benefits, Entitlements, Eligibility, Case Management & Social Protection Runtime 5.0**

Namespace dự kiến:

```text
AXWELFARE
```

Mục tiêu của task kế tiếp là xây lớp **public benefit / social protection execution**:

```text
AXGOV
   ↓
AXLAW
   ↓
AXFISCAL
   ↓
AXWELFARE
   ├── benefits
   ├── pensions
   ├── social transfers
   ├── eligibility
   ├── entitlements
   ├── welfare programs
   ├── case management
   └── public assistance
```

đồng thời giữ ranh giới với:

```text
AX674       = healthcare
AX673       = education
AX688       = labor
AX670       = population
AXFINANCE   = accounting
AXFISCAL    = budget/treasury
AXLAW       = legal entitlement
```

Task này sẽ đặc biệt xử lý vấn đề quan trọng:

```text
Eligibility ≠ Entitlement
Entitlement ≠ Approval
Approval ≠ Payment
Payment ≠ Outcome
Need ≠ Eligibility
RiskScore ≠ FraudFinding
AIRecommendation ≠ BenefitDecision
```

và thiết kế một social-protection runtime có thể chạy từ **một chương trình trợ cấp đơn lẻ đến hệ thống an sinh của toàn bộ quốc gia**.
:::

BOOTSTRAP-697 hoàn tất. Chuỗi kiến trúc tiếp theo là **BOOTSTRAP-698**.