Tiếp tục với **BOOTSTRAP-695** — lớp tài khóa, ngân sách nhà nước, thuế, kho bạc và nợ công, tách rõ khỏi `AXMONETARY`, `AXFINANCE`, `AXGOV` và `AXLAW`.

:::writing{variant="document" id="74106" title="BOOTSTRAP-695 — Native AI Civilization-Scale Fiscal System, Government Budget, Taxation, Public Debt, Treasury, Government Spending, Transfers, Public Finance & Fiscal Policy Runtime 5.0"}

# BOOTSTRAP-695
## Native AI Civilization-Scale Fiscal System, Government Budget, Taxation, Public Debt, Treasury, Government Spending, Transfers, Public Finance & Fiscal Policy Runtime 5.0

**Status:** Architecture Specification  
**Version:** 5.0  
**Namespace:** `AXFISCAL`

---

# 1. Mục tiêu

`AXFISCAL` là runtime native của Axiom cho:

- government finance;
- public revenue;
- taxation;
- government budget;
- treasury;
- public expenditure;
- transfers;
- subsidies;
- grants;
- public procurement;
- public debt;
- sovereign borrowing;
- debt servicing;
- debt issuance;
- government cash management;
- fiscal rules;
- fiscal policy;
- intergovernmental transfers;
- public investment;
- fiscal forecasting;
- fiscal stress testing;
- debt sustainability analysis;
- public-finance simulation;
- AI-assisted fiscal analysis.

Mục tiêu là mô hình hóa được toàn bộ vòng đời:

```text
ECONOMIC ACTIVITY
       ↓
TAX / OTHER REVENUE
       ↓
GOVERNMENT REVENUE
       ↓
BUDGET
       ↓
APPROPRIATION
       ↓
PUBLIC SPENDING
       ↓
TRANSFERS / PROCUREMENT / INVESTMENT
       ↓
PUBLIC SERVICES / INFRASTRUCTURE
       ↓
ECONOMIC ACTIVITY
       ↓
TAX BASE
```

---

# 2. Boundary kiến trúc

Các distinction bắt buộc:

```text
Revenue ≠ Cash
TaxAssessment ≠ TaxPayment
TaxLiability ≠ TaxRevenue
Budget ≠ CashBalance
Appropriation ≠ Expenditure
Expenditure ≠ Payment
Payment ≠ PublicServiceOutcome
Debt ≠ Deficit
Deficit ≠ DebtIncrease
Debt ≠ FiscalRisk
Borrowing ≠ MoneyCreation
Treasury ≠ CentralBank
FiscalPolicy ≠ MonetaryPolicy
PublicAsset ≠ PublicCash
BudgetForecast ≠ BudgetFact
BudgetProposal ≠ BudgetAuthorization
Authorization ≠ Execution
Subsidy ≠ PublicProcurement
Transfer ≠ Purchase
GovernmentGuarantee ≠ GovernmentDebt
ContingentLiability ≠ DirectLiability
Simulation ≠ FiscalReality
AIRecommendation ≠ GovernmentDecision
```

---

# 3. Vị trí trong Axiom

```text
                         AXCIVILIZATION
                               │
                               ▼
                           AX671 ECONOMY
                               │
               ┌───────────────┼────────────────┐
               ▼               ▼                ▼
           AXMONETARY       AXFISCAL        AXFINANCE
               │               │                │
               │               ├── Tax          │
               │               ├── Budget       │
               │               ├── Treasury     │
               │               ├── Debt         │
               │               └── Spending     │
               │                                │
               └────────────┬───────────────────┘
                            ▼
                         AXGOV
                            │
                         AXLAW
```

---

# 4. Vai trò của AXFISCAL

```text
AXGOV
= Government authority / administration

AXLAW
= Legal authority / legal rules

AXFISCAL
= Public financial policy and execution

AXFINANCE
= Financial accounting truth

AXMONETARY
= Money / reserves / monetary policy

AXBANKING
= Commercial banking / credit

AXMARKET
= Market trading / clearing / settlement
```

---

# 5. Government fiscal system

```axiom
struct FiscalSystem {
    id: FiscalSystemId
    jurisdiction: JurisdictionRef
    fiscal_authority: EntityRef
    treasury: TreasuryRef
    tax_system: TaxSystemRef
    budget_framework: BudgetFrameworkRef
    debt_framework: DebtFrameworkRef
    fiscal_rules: FiscalRule[]
}
```

---

# 6. Fiscal authority

```axiom
struct FiscalAuthority {
    id: EntityId
    jurisdiction: JurisdictionRef
    authority_scope: FiscalAuthorityScope
}
```

Một jurisdiction có thể có:

```text
NationalGovernment
StateGovernment
ProvincialGovernment
Municipality
District
PublicAgency
SpecialFiscalEntity
```

---

# 7. Fiscal hierarchy

```text
Government
├── CentralGovernment
├── RegionalGovernment
├── LocalGovernment
├── PublicAgency
├── PublicFund
└── PublicEnterprise
```

---

# 8. Fiscal entity

```axiom
struct FiscalEntity {
    id: EntityId
    parent: EntityRef?
    entity_type: FiscalEntityType
    jurisdiction: JurisdictionRef
}
```

---

# 9. Fiscal year

```axiom
struct FiscalYear {
    id: FiscalYearId
    start: Date
    end: Date
}
```

Không giả định fiscal year = calendar year.

---

# 10. Fiscal period

```axiom
struct FiscalPeriod {
    fiscal_year: FiscalYearId
    start: Date
    end: Date
    period_type: FiscalPeriodType
}
```

---

# 11. Revenue

```axiom
struct Revenue {
    id: RevenueId
    source: RevenueSource
    amount: MonetaryAmount
    recognition_date: Date
    collection_status: CollectionStatus
}
```

---

# 12. Revenue sources

```text
Tax
SocialContribution
Fee
Fine
Dividend
PublicEnterpriseIncome
NaturalResourceRevenue
Grant
Donation
AssetSale
LicenseRevenue
InterestIncome
OtherRevenue
```

---

# 13. Tax

```axiom
struct Tax {
    id: TaxId
    jurisdiction: JurisdictionRef
    tax_type: TaxType
    taxpayer_scope: Scope
    tax_base: TaxBaseDefinition
    rate: TaxRate
}
```

---

# 14. Tax types

```text
IncomeTax
CorporateIncomeTax
ValueAddedTax
SalesTax
ExciseTax
PropertyTax
LandTax
CustomsDuty
PayrollTax
CapitalGainsTax
WithholdingTax
ResourceTax
EnvironmentalTax
TransactionTax
OtherTax
```

---

# 15. Tax ≠ universal property

Một tax definition phải có:

```text
jurisdiction
legal_basis
taxpayer
tax_base
rate
period
exemptions
deductions
credits
filing_rule
payment_rule
```

---

# 16. Tax base

```axiom
struct TaxBaseDefinition {
    source: DataSourceRef
    calculation: FormulaRef
    exclusions: Rule[]
    deductions: Rule[]
    exemptions: Rule[]
}
```

---

# 17. Tax rate

```axiom
struct TaxRate {
    rate_type: TaxRateType
    value: Decimal
    effective_from: Timestamp
    effective_to: Timestamp?
}
```

Types:

```text
Flat
Progressive
Regressive
Marginal
Average
SpecificAmount
AdValorem
Tiered
Custom
```

---

# 18. Tax bracket

```axiom
struct TaxBracket {
    lower_bound: MonetaryAmount
    upper_bound: MonetaryAmount?
    rate: Rate
}
```

---

# 19. Progressive tax schedule

```axiom
struct ProgressiveTaxSchedule {
    brackets: TaxBracket[]
}
```

Invariant:

```text
brackets must be ordered and non-overlapping
```

---

# 20. Taxpayer

```axiom
struct Taxpayer {
    id: TaxpayerId
    legal_entity: EntityRef
    jurisdiction: JurisdictionRef
    classifications: TaxClassification[]
}
```

---

# 21. Tax obligation

```axiom
struct TaxLiability {
    id: LiabilityId
    taxpayer: TaxpayerId
    tax_type: TaxType
    assessment_period: FiscalPeriod
    amount: MonetaryAmount
    due_date: Date
}
```

---

# 22. Tax lifecycle

```text
Potential
→ Registered
→ Assessed
→ Filed
→ Determined
→ Due
→ Paid
→ Reconciled
→ Closed
```

Branches:

```text
Disputed
Adjusted
Audited
Refunded
WrittenOff
Appealed
```

---

# 23. Tax assessment

```axiom
struct TaxAssessment {
    taxpayer: TaxpayerId
    tax: TaxId
    tax_base: MonetaryAmount
    deductions: MonetaryAmount
    taxable_base: MonetaryAmount
    gross_tax: MonetaryAmount
    credits: MonetaryAmount
    final_liability: MonetaryAmount
    methodology: AssessmentMethod
}
```

---

# 24. Assessment ≠ payment

```text
TaxAssessment
      ≠
TaxPayment
```

Một assessment có thể tồn tại trước payment.

---

# 25. Tax payment

```axiom
struct TaxPayment {
    id: PaymentId
    taxpayer: TaxpayerId
    liability: LiabilityId
    amount: MonetaryAmount
    payment_date: Timestamp
    settlement_ref: SettlementRef
}
```

Settlement delegate:

```text
AXFINANCE
AXBANKING
AXMONETARY
```

---

# 26. Tax refund

```axiom
struct TaxRefund {
    liability: LiabilityId
    taxpayer: TaxpayerId
    amount: MonetaryAmount
    reason: RefundReason
}
```

---

# 27. Tax credit

```axiom
struct TaxCredit {
    taxpayer: TaxpayerId
    tax: TaxId
    amount: MonetaryAmount
    eligibility: Rule
    expiration: Date?
}
```

---

# 28. Tax exemption

```axiom
struct TaxExemption {
    tax: TaxId
    beneficiary_scope: Scope
    exemption_rule: Rule
    effective_period: TimeRange
}
```

---

# 29. Tax administration

```text
Registration
→ Filing
→ Assessment
→ Collection
→ Reconciliation
→ Audit
→ Dispute
→ Resolution
```

---

# 30. Tax audit

```axiom
struct TaxAudit {
    id: AuditId
    taxpayer: TaxpayerId
    scope: AuditScope
    evidence: EvidenceRef[]
    findings: AuditFinding[]
}
```

---

# 31. AI tax anomaly

AI may generate:

```text
TaxAnomalySignal
ComplianceRiskSignal
DataInconsistencySignal
```

But:

```text
TaxAnomalySignal ≠ TaxFraudFinding
```

---

# 32. Tax privacy

Tax data is highly restricted.

Capabilities:

```text
fiscal.tax.read
fiscal.tax.assess
fiscal.tax.file
fiscal.tax.collect
fiscal.tax.audit
fiscal.tax.refund
fiscal.tax.admin
```

---

# 33. Budget

```axiom
struct Budget {
    id: BudgetId
    fiscal_year: FiscalYearId
    authority: FiscalEntityId
    status: BudgetStatus
    revenue_plan: BudgetSection
    expenditure_plan: BudgetSection
    financing_plan: FinancingPlan
}
```

---

# 34. Budget lifecycle

```text
Draft
→ Proposed
→ Reviewed
→ Authorized
→ Published
→ Executing
→ Revised
→ Closed
```

Branches:

```text
Rejected
Amended
Suspended
```

---

# 35. Budget ≠ cash

```text
BudgetAuthorization
≠
TreasuryCash
```

Một chương trình có ngân sách nhưng chưa chắc đã có cash đã chi.

---

# 36. Appropriation

```axiom
struct Appropriation {
    id: AppropriationId
    budget: BudgetId
    program: ProgramId
    amount: MonetaryAmount
    fiscal_period: FiscalPeriod
    restrictions: SpendingRestriction[]
}
```

---

# 37. Appropriation lifecycle

```text
Proposed
→ Authorized
→ Allocated
→ Committed
→ Obligated
→ Spent
→ Closed
```

---

# 38. Budget allocation

```axiom
allocate_budget(
    appropriation,
    department,
    program,
    amount
)
```

Không được vượt appropriation nếu không có explicit amendment/authority.

---

# 39. Budget amendment

```axiom
struct BudgetAmendment {
    budget: BudgetId
    changes: BudgetChange[]
    authority: EntityRef
    effective_date: Date
}
```

---

# 40. Budget execution

```text
Appropriation
      ↓
Commitment
      ↓
Obligation
      ↓
Invoice/Claim
      ↓
Payment
      ↓
Accounting
```

---

# 41. Commitment

```axiom
struct BudgetCommitment {
    id: CommitmentId
    appropriation: AppropriationId
    beneficiary: EntityRef
    amount: MonetaryAmount
}
```

---

# 42. Obligation

```axiom
struct FiscalObligation {
    id: ObligationId
    commitment: CommitmentId
    amount: MonetaryAmount
    due_date: Date?
}
```

---

# 43. Expenditure

```axiom
struct GovernmentExpenditure {
    id: ExpenditureId
    program: ProgramId
    amount: MonetaryAmount
    category: ExpenditureCategory
    period: FiscalPeriod
}
```

---

# 44. Expenditure categories

```text
Personnel
Operations
Transfers
Subsidies
Procurement
Infrastructure
PublicInvestment
DebtService
Interest
SocialProtection
Health
Education
Defense
Other
```

---

# 45. Payment

```axiom
struct GovernmentPayment {
    expenditure: ExpenditureId
    beneficiary: EntityRef
    amount: MonetaryAmount
    settlement: SettlementRef
}
```

---

# 46. Spending ≠ payment

```text
Expenditure
≠
Payment
```

Recognition and cash settlement có thể khác thời điểm.

---

# 47. Treasury

```axiom
struct Treasury {
    id: TreasuryId
    authority: FiscalEntityId
    currency: CurrencyId
    cash_accounts: TreasuryAccount[]
    liquidity_policy: TreasuryLiquidityPolicy
}
```

---

# 48. Treasury account

```axiom
struct TreasuryAccount {
    id: AccountId
    institution: EntityRef
    currency: CurrencyId
    balance: MonetaryAmount
    account_type: TreasuryAccountType
}
```

---

# 49. Treasury account types

```text
CentralTreasuryAccount
AgencyAccount
TaxCollectionAccount
PaymentAccount
DebtServiceAccount
ForeignCurrencyAccount
EmergencyAccount
```

---

# 50. Treasury Single Account

Axiom hỗ trợ:

```text
TreasurySingleAccount
```

nhưng không ép mọi jurisdiction phải sử dụng mô hình này.

---

# 51. Cash management

```axiom
struct TreasuryCashForecast {
    horizon: Duration
    expected_inflows: CashFlow[]
    expected_outflows: CashFlow[]
    liquidity_gap: MonetaryAmount
}
```

---

# 52. Cash forecast

States:

```text
Observed
Estimated
Forecast
Stress
Scenario
```

---

# 53. Fiscal balance

Generic:

```text
FiscalBalance =
Revenue
-
Expenditure
```

Nhưng definition phải ghi rõ accounting basis.

---

# 54. Primary balance

```text
PrimaryBalance =
Revenue
-
PrimaryExpenditure
```

---

# 55. Overall balance

```text
OverallBalance =
Revenue
-
TotalExpenditure
```

---

# 56. Deficit

```text
Deficit =
max(0, -FiscalBalance)
```

---

# 57. Surplus

```text
Surplus =
max(0, FiscalBalance)
```

---

# 58. Deficit ≠ debt

```text
Deficit
=
period flow

Debt
=
stock
```

Đây là invariant quan trọng.

---

# 59. Public debt

```axiom
struct PublicDebt {
    id: DebtId
    issuer: FiscalEntityId
    currency: CurrencyId
    principal: MonetaryAmount
    instruments: DebtInstrument[]
    maturity_profile: MaturityProfile
}
```

---

# 60. Debt instrument

```text
TreasuryBill
GovernmentBond
GovernmentNote
Loan
ExternalLoan
IndexedBond
FloatingRateBond
ZeroCouponBond
GreenBond
SocialBond
SukukLikeInstrument
Other
```

---

# 61. Debt lifecycle

```text
Proposed
→ Authorized
→ Issued
→ Outstanding
→ Serviced
→ Refinanced
→ Matured
→ Redeemed
→ Closed
```

---

# 62. Debt issuance

```axiom
struct DebtIssuance {
    issuer: FiscalEntityId
    instrument: DebtInstrument
    face_value: MonetaryAmount
    issue_price: MonetaryAmount
    coupon: Rate?
    maturity: Date
}
```

---

# 63. Primary issuance

Execution:

```text
DebtAuthorization
→ Auction/Placement
→ AXMARKET
→ Clearing
→ Settlement
→ TreasuryReceipt
```

---

# 64. Debt service

```axiom
struct DebtService {
    debt: DebtId
    principal_payment: MonetaryAmount
    interest_payment: MonetaryAmount
    payment_date: Date
}
```

---

# 65. Interest expense

Interest expense must be separately observable from principal repayment.

---

# 66. Debt maturity

```text
MaturityDate
```

must be explicit.

---

# 67. Debt maturity ladder

```axiom
struct DebtMaturityProfile {
    periods: MaturityBucket[]
}
```

Ví dụ:

```text
<1Y
1-3Y
3-5Y
5-10Y
>10Y
```

Buckets configurable.

---

# 68. Debt currency exposure

```axiom
struct DebtCurrencyExposure {
    currency: CurrencyId
    amount: MonetaryAmount
    share: Ratio
}
```

---

# 69. Debt risk

```text
InterestRateRisk
RefinancingRisk
CurrencyRisk
LiquidityRisk
MarketRisk
DefaultRisk
ContingentRisk
```

---

# 70. Debt sustainability

```axiom
struct DebtSustainabilityAnalysis {
    debt_path: VariablePath
    primary_balance_path: VariablePath
    interest_path: VariablePath
    growth_path: VariablePath
    assumptions: Assumption[]
    scenarios: ScenarioResult[]
}
```

---

# 71. Debt-to-GDP

```text
DebtToGDP =
PublicDebt / NominalGDP
```

GDP definition và debt perimeter phải explicit.

---

# 72. Interest-growth differential

```text
r - g
```

có thể là một input của debt-dynamics model, không phải universal deterministic rule.

---

# 73. Debt dynamics

Generic simulation:

```text
Debt[t+1]
=
Debt[t]
+
PrimaryDeficit[t]
+
Interest[t]
+
OtherAdjustments[t]
```

---

# 74. Stock-flow adjustment

```axiom
struct StockFlowAdjustment {
    debt: DebtId
    amount: MonetaryAmount
    cause: AdjustmentCause
}
```

Ví dụ:

```text
FXRevaluation
Privatization
BankRecapitalization
GuaranteeCall
AccountingAdjustment
Other
```

---

# 75. Contingent liability

```axiom
struct ContingentLiability {
    id: LiabilityId
    issuer: FiscalEntityId
    trigger: TriggerCondition
    maximum_exposure: MonetaryAmount?
    probability_model: ProbabilityModel?
}
```

---

# 76. Government guarantee

```axiom
struct GovernmentGuarantee {
    guarantor: FiscalEntityId
    beneficiary: EntityRef
    underlying_obligation: ObligationRef
    limit: MonetaryAmount
    maturity: Date
}
```

---

# 77. Guarantee ≠ debt

Guarantee trở thành direct fiscal liability chỉ khi applicable trigger xảy ra theo legal/accounting framework.

---

# 78. Public asset

```axiom
struct PublicAsset {
    id: AssetId
    owner: FiscalEntityId
    asset_type: PublicAssetType
    valuation: AssetValuation
}
```

Types:

```text
Cash
Land
Infrastructure
Buildings
Equity
NaturalResource
Receivable
FinancialAsset
Other
```

---

# 79. Public balance sheet

```axiom
struct PublicSectorBalanceSheet {
    assets: PublicAsset[]
    liabilities: PublicLiability[]
    net_position: MonetaryAmount
}
```

---

# 80. Fiscal net worth

```text
NetWorth =
PublicAssets
-
PublicLiabilities
```

Perimeter phải được khai báo.

---

# 81. Public investment

```axiom
struct PublicInvestment {
    project: ProjectId
    appropriation: AppropriationId
    capital_amount: MonetaryAmount
    expected_life: Duration
}
```

---

# 82. Infrastructure spending

Liên kết:

```text
AXFISCAL
   ↓
AXCONSTRUCTION
   ↓
InfrastructureProject
```

---

# 83. Public procurement

```axiom
struct PublicProcurement {
    id: ProcurementId
    authority: FiscalEntityId
    program: ProgramId
    tender: TenderRef
    contract: ContractRef?
    value: MonetaryAmount
}
```

---

# 84. Procurement lifecycle

```text
Planned
→ Tendered
→ Evaluated
→ Awarded
→ Contracted
→ Executing
→ Accepted
→ Paid
→ Closed
```

---

# 85. Procurement boundary

```text
AXFISCAL
= budget / authorization / payment

AXLAW
= procurement law

AXCOMMERCE
= supplier / product / market semantics

AXCONSTRUCTION
= construction execution

AXFINANCE
= accounting
```

---

# 86. Government contract

```axiom
struct GovernmentContract {
    id: ContractId
    authority: FiscalEntityId
    supplier: EntityRef
    value: MonetaryAmount
    duration: TimeRange
    obligations: ContractObligation[]
}
```

---

# 87. Public transfer

```axiom
struct PublicTransfer {
    payer: FiscalEntityId
    beneficiary: EntityRef
    amount: MonetaryAmount
    program: ProgramId
    eligibility: Rule
}
```

---

# 88. Transfer categories

```text
SocialTransfer
PensionTransfer
UnemploymentTransfer
FamilyTransfer
EducationTransfer
HealthTransfer
RegionalTransfer
EmergencyTransfer
BusinessSupport
Other
```

---

# 89. Subsidy

```axiom
struct Subsidy {
    authority: FiscalEntityId
    recipient_scope: Scope
    amount: MonetaryAmount
    program: ProgramId
    eligibility: Rule
    period: TimeRange
}
```

---

# 90. Subsidy ≠ procurement

```text
Subsidy
≠
GovernmentPurchase
```

---

# 91. Grant

```axiom
struct PublicGrant {
    grantor: FiscalEntityId
    grantee: EntityRef
    amount: MonetaryAmount
    purpose: GrantPurpose
    conditions: GrantCondition[]
}
```

---

# 92. Intergovernmental transfer

```axiom
struct IntergovernmentalTransfer {
    source: FiscalEntityId
    destination: FiscalEntityId
    amount: MonetaryAmount
    formula: AllocationFormula
}
```

---

# 93. Fiscal equalization

```axiom
struct FiscalEqualization {
    jurisdictions: JurisdictionRef[]
    formula: EqualizationFormula
    period: FiscalPeriod
}
```

---

# 94. Public-service spending

```text
GovernmentRevenue
        ↓
Budget
        ↓
Program
        ↓
Allocation
        ↓
Execution
        ↓
PublicService
```

---

# 95. Public-service outcome

```axiom
struct PublicServiceOutcome {
    program: ProgramId
    indicators: OutcomeIndicator[]
    observed_value: Decimal
    target_value: Decimal?
}
```

---

# 96. Spending ≠ outcome

```text
SpendingAmount ≠ ServiceQuality
```

Runtime phải giữ hai lớp riêng.

---

# 97. Fiscal performance

```axiom
struct FiscalPerformance {
    program: ProgramId
    inputs: Metric[]
    outputs: Metric[]
    outcomes: Metric[]
    cost: MonetaryAmount
}
```

---

# 98. Program evaluation

AI có thể phân tích:

```text
cost
coverage
output
outcome
uncertainty
counterfactual
```

nhưng không tự biến thành policy authority.

---

# 99. Fiscal rule

```axiom
struct FiscalRule {
    id: FiscalRuleId
    jurisdiction: JurisdictionRef
    variable: FiscalVariable
    threshold: Threshold
    adjustment_rule: AdjustmentRule
    escape_clause: EscapeClause?
}
```

---

# 100. Fiscal rule types

```text
DeficitRule
DebtRule
ExpenditureRule
RevenueRule
PrimaryBalanceRule
GoldenRule
CustomRule
```

---

# 101. Fiscal rule ≠ legal rule

Nếu fiscal rule có legal force, legal representation thuộc `AXLAW`.

---

# 102. Escape clause

```axiom
struct EscapeClause {
    trigger: TriggerCondition
    activation_authority: EntityRef
    duration: Duration
    reporting_requirement: Requirement[]
}
```

---

# 103. Fiscal policy

```axiom
struct FiscalPolicy {
    authority: FiscalEntityId
    revenue_policy: PolicySet
    expenditure_policy: PolicySet
    transfer_policy: PolicySet
    debt_policy: PolicySet
}
```

---

# 104. Fiscal policy instrument

```text
TaxRate
TaxBase
Transfer
Subsidy
GovernmentSpending
PublicInvestment
DebtIssuance
DebtRepayment
Guarantee
CashManagement
```

---

# 105. Fiscal policy decision

```axiom
struct FiscalPolicyDecision {
    id: DecisionId
    authority: FiscalEntityId
    measures: FiscalMeasure[]
    effective_period: TimeRange
    legal_basis: LegalReference?
}
```

---

# 106. Policy lifecycle

```text
Analysis
→ Proposal
→ Review
→ Authorization
→ Announcement
→ Implementation
→ Monitoring
→ Evaluation
```

---

# 107. Proposal ≠ authorization

```text
FiscalProposal ≠ FiscalAuthorization
```

---

# 108. AI fiscal analyst

AI có thể:

```text
forecast_revenue
forecast_expenditure
detect_budget_anomalies
simulate_tax_changes
simulate_spending_changes
stress_test_debt
analyze_cash_flow
analyze_program_outcomes
detect_procurement_anomalies
```

---

# 109. AI fiscal recommendation

```axiom
struct FiscalRecommendation {
    assumptions: Assumption[]
    options: FiscalOption[]
    projected_effects: Effect[]
    uncertainty: UncertaintyModel
}
```

Không được gán quyền quyết định.

---

# 110. AI authority boundary

Default:

```text
fiscal.data.read
fiscal.analysis.run
fiscal.simulation.run
fiscal.forecast.run
```

Không mặc định:

```text
fiscal.tax.change
fiscal.budget.authorize
fiscal.debt.issue
fiscal.payment.execute
fiscal.transfer.execute
```

---

# 111. Budget authority

Capabilities:

```text
fiscal.budget.read
fiscal.budget.propose
fiscal.budget.amend
fiscal.budget.authorize
fiscal.budget.execute
fiscal.budget.admin
```

---

# 112. Treasury authority

```text
fiscal.treasury.read
fiscal.treasury.transfer
fiscal.treasury.payment
fiscal.treasury.cash_manage
fiscal.treasury.admin
```

---

# 113. Tax authority

```text
fiscal.tax.read
fiscal.tax.assess
fiscal.tax.collect
fiscal.tax.audit
fiscal.tax.refund
fiscal.tax.admin
```

---

# 114. Debt authority

```text
fiscal.debt.read
fiscal.debt.propose
fiscal.debt.authorize
fiscal.debt.issue
fiscal.debt.service
fiscal.debt.refinance
```

---

# 115. Public procurement authority

```text
fiscal.procurement.read
fiscal.procurement.create
fiscal.procurement.evaluate
fiscal.procurement.award
fiscal.procurement.execute
```

---

# 116. Fiscal accounting boundary

`AXFISCAL` tạo public-finance events.

`AXFINANCE` là authoritative accounting layer.

```text
AXFISCAL
   ↓ financial event
AXFINANCE
   ↓
Ledger
```

---

# 117. Treasury-bank boundary

```text
Treasury
   ↔
CommercialBank
   ↔
CentralBank
```

Thông qua:

```text
AXBANKING
AXMONETARY
```

---

# 118. Treasury-central-bank interface

```axiom
struct TreasuryCentralBankInterface {
    government_account: AccountRef
    reserve_currency: CurrencyId
    settlement_endpoint: SettlementEndpoint
}
```

---

# 119. Government deposits

Government deposits phải được phân biệt:

```text
GovernmentDeposit
≠
CommercialBankCustomerDeposit
≠
CentralBankReserve
```

---

# 120. Fiscal-monetary interface

```text
AXFISCAL
      ↕
AXMONETARY
```

Objects:

```text
GovernmentDeposit
GovernmentDebt
CentralBankHolding
ReserveFlow
InterestPayment
LiquidityEffect
```

---

# 121. Monetary policy ≠ fiscal policy

Invariant:

```text
AXMONETARY
controls monetary-system semantics

AXFISCAL
controls public-finance semantics
```

---

# 122. Debt monetization

Nếu simulation cần:

```text
GovernmentDebt
→ CentralBankPurchase
→ ReserveChange
```

phải là explicit monetary-fiscal scenario.

Không implicit.

---

# 123. Fiscal multiplier

Runtime có thể model:

```axiom
struct FiscalMultiplierModel {
    spending_type: SpendingCategory
    horizon: Duration
    estimated_multiplier: Decimal
    uncertainty: Interval
}
```

Không hard-code một universal multiplier.

---

# 124. Tax elasticity

```axiom
struct TaxElasticity {
    tax: TaxId
    base: TaxBaseDefinition
    elasticity: Decimal
    estimation_period: TimeRange
}
```

---

# 125. Fiscal automatic stabilizer

```text
EconomicShock
      ↓
TaxBase
      ↓
TaxRevenue
      ↓
Transfers
      ↓
DisposableIncome
      ↓
Demand
```

---

# 126. Automatic stabilizer model

```axiom
struct AutomaticStabilizer {
    tax_rules: TaxRule[]
    transfer_rules: TransferRule[]
    activation_conditions: TriggerCondition[]
}
```

---

# 127. Fiscal shock

```text
TaxShock
SpendingShock
TransferShock
RevenueShock
DebtShock
InterestShock
FXShock
CommodityShock
NaturalDisasterShock
BankGuaranteeShock
```

---

# 128. Fiscal scenario

```axiom
struct FiscalScenario {
    baseline: ScenarioRef
    revenue_changes: FiscalShock[]
    spending_changes: FiscalShock[]
    debt_changes: FiscalShock[]
    macro_assumptions: Assumption[]
    horizon: Duration
}
```

---

# 129. Fiscal simulation

```axiom
fiscal.simulate {
    scenario: Baseline
    horizon: 30y

    outputs {
        revenue
        expenditure
        deficit
        debt
        debt_to_gdp
        interest_expense
        cash_balance
        public_net_worth
    }
}
```

---

# 130. Debt stress test

```axiom
fiscal.stress_debt {
    shocks {
        growth: -3%
        interest_rate: +300bp
        fx: -20%
        primary_balance: -2%GDP
    }

    horizon: 15y
}
```

---

# 131. Debt sustainability scenarios

```text
Baseline
Adverse
Severe
LiquidityStress
InterestShock
FXShock
GrowthShock
RevenueShock
GuaranteeCall
CombinedStress
```

---

# 132. Debt-service coverage

```axiom
struct DebtServiceCoverage {
    cash_revenue: MonetaryAmount
    debt_service: MonetaryAmount
    ratio: Decimal
}
```

---

# 133. Refinancing risk

```axiom
struct RefinancingRisk {
    maturity_amount: MonetaryAmount
    refinancing_window: Duration
    market_assumptions: Assumption[]
    stress_scenarios: ScenarioResult[]
}
```

---

# 134. Interest-rate risk

```axiom
struct FiscalInterestRisk {
    fixed_rate_share: Ratio
    floating_rate_share: Ratio
    average_maturity: Duration
    repricing_profile: Curve
}
```

---

# 135. FX debt risk

```axiom
struct FiscalFXRisk {
    currency_exposures: DebtCurrencyExposure[]
    stress_rates: FXShock[]
    projected_impact: MonetaryAmount
}
```

---

# 136. Sovereign liquidity

```axiom
struct SovereignLiquidity {
    cash: MonetaryAmount
    liquid_assets: MonetaryAmount
    near_term_obligations: MonetaryAmount
    liquidity_gap: MonetaryAmount
}
```

---

# 137. Sovereign solvency

Sovereign solvency model phải tách khỏi short-term liquidity.

```text
Liquidity ≠ Solvency
```

---

# 138. Public-private risk transfer

Public finance có thể interact với:

```text
AXINSURANCE
AXBANKING
AXMARKET
```

Ví dụ:

```text
GovernmentGuarantee
PublicInsurance
BankRecapitalization
DisasterInsurance
```

---

# 139. Government guarantee call

```text
Trigger
→ Claim
→ Verification
→ GovernmentObligation
→ BudgetRecognition
→ TreasuryPayment
```

---

# 140. Disaster fiscal response

```text
Disaster
→ EmergencyBudget
→ Procurement
→ Transfers
→ InfrastructureRepair
→ Debt/ReserveFinancing
→ Recovery
```

Liên kết:

```text
AXRESOURCE
AXCONSTRUCTION
AXINSURANCE
AXGOV
AXFISCAL
```

---

# 141. Natural-resource revenue

```axiom
struct ResourceRevenue {
    resource: ResourceRef
    quantity: Quantity
    price: MonetaryAmount
    royalty: MonetaryAmount
    tax: MonetaryAmount
}
```

---

# 142. Resource-fiscal link

```text
RESOURCE
   ↓
Production
   ↓
Revenue
   ↓
Royalty / Tax
   ↓
AXFISCAL
```

---

# 143. Sovereign wealth fund boundary

Nếu jurisdiction có sovereign wealth fund:

```text
AXFISCAL
   ↔
AXINVEST
```

`SovereignWealthFund` không đồng nhất với Treasury cash.

---

# 144. Sovereign wealth fund

```axiom
struct SovereignWealthFund {
    id: FundId
    owner: FiscalEntityId
    mandate: FundMandate
    assets: PortfolioRef
    liabilities: LiabilityRef[]
}
```

---

# 145. Public pension boundary

Public pension có thể interface:

```text
AXFISCAL
↔
AXLABOR
↔
AXINSURANCE
↔
AXINVEST
```

Nhưng pension fund accounting không tự động trở thành Treasury.

---

# 146. Fiscal transparency

Mọi public-finance object quan trọng phải có:

```text
source
legal_basis
period
authority
status
revision
provenance
```

---

# 147. Budget transparency

Budget publication có:

```text
appropriation
execution
revision
commitment
obligation
payment
```

theo available disclosure framework.

---

# 148. Fiscal data vintage

```axiom
struct FiscalDataVintage {
    observation_period: FiscalPeriod
    publication_time: Timestamp
    revision: u32
    source: DataSourceRef
}
```

---

# 149. Fiscal forecast

```axiom
struct FiscalForecast {
    horizon: Duration
    revenue_path: VariablePath
    expenditure_path: VariablePath
    debt_path: VariablePath
    assumptions: Assumption[]
    vintage: FiscalDataVintage
}
```

---

# 150. Forecast ≠ budget

```text
FiscalForecast
≠
AuthorizedBudget
```

---

# 151. Fiscal digital twin

```axiom
struct FiscalTwin {
    observed: FiscalState
    estimated: FiscalState
    forecast: FiscalState
    scenario: FiscalState
}
```

---

# 152. Digital-twin invariant

```text
Observed
≠
Estimated
≠
Forecast
≠
Scenario
```

---

# 153. Public-finance graph

```text
Taxpayer
   ↓
Tax
   ↓
Revenue
   ↓
Treasury
   ↓
Budget
   ↓
Appropriation
   ↓
Program
   ↓
Expenditure
   ↓
Payment
   ↓
Public Service
```

---

# 154. Debt graph

```text
FiscalDeficit
      ↓
FinancingNeed
      ↓
DebtIssuance
      ↓
AXMARKET
      ↓
Settlement
      ↓
TreasuryCash
      ↓
GovernmentSpending
```

---

# 155. Debt-refinancing loop

```text
MaturingDebt
      ↓
RefinancingNeed
      ↓
NewIssuance
      ↓
MarketDemand
      ↓
Yield
      ↓
InterestCost
      ↓
FutureBudget
```

---

# 156. Fiscal-monetary loop

```text
FISCAL POLICY
      ↓
Government Spending / Taxes
      ↓
Aggregate Demand
      ↓
Prices / Output
      ↓
MONETARY POLICY
      ↓
Rates / Liquidity
      ↓
Credit
      ↓
Investment
      ↓
Output / Income
      ↓
TAX BASE
      ↓
FISCAL SYSTEM
```

---

# 157. Public-finance civilization loop

```text
ECONOMY
   ↓
INCOME / PROFITS / TRANSACTIONS
   ↓
TAX BASE
   ↓
PUBLIC REVENUE
   ↓
BUDGET
   ↓
PUBLIC INVESTMENT / SERVICES / TRANSFERS
   ↓
INFRASTRUCTURE / HUMAN CAPITAL / DEMAND
   ↓
ECONOMY
```

---

# 158. Fiscal AI simulation

AI có thể chạy:

```text
TaxReformScenario
SpendingScenario
DebtScenario
InfrastructureScenario
TransferScenario
RecessionScenario
DisasterScenario
CommodityScenario
InterestShockScenario
FXShockScenario
```

---

# 159. AI model outputs

Output phải chứa:

```text
projection
uncertainty
assumptions
sensitivity
data_vintage
model_version
scenario_id
```

---

# 160. Fiscal model registry

```axiom
struct FiscalModel {
    id: ModelId
    version: Version
    variables: Variable[]
    equations: Equation[]
    assumptions: Assumption[]
    validity_period: TimeRange?
}
```

---

# 161. Model governance

```text
Draft
→ Validated
→ Approved
→ Published
→ Active
→ Deprecated
```

---

# 162. Model comparison

```axiom
fiscal.compare_models(
    model_a,
    model_b,
    scenario
)
```

---

# 163. Model risk

```text
SpecificationRisk
ParameterRisk
DataRisk
StructuralRisk
ScenarioRisk
ImplementationRisk
```

---

# 164. Fiscal anomaly detection

Có thể phát hiện:

```text
budget_spike
payment_duplicate
procurement_outlier
revenue_gap
debt_rollover_anomaly
cash_flow_anomaly
tax_data_inconsistency
```

Nhưng:

```text
Anomaly ≠ Fraud
```

---

# 165. Procurement anomaly

AI output:

```axiom
struct ProcurementAnomalySignal {
    procurement: ProcurementId
    indicators: Signal[]
    confidence: Probability
    provenance: Provenance
}
```

Không tự kết luận wrongdoing.

---

# 166. Tax anomaly

```axiom
struct TaxAnomalySignal {
    taxpayer: TaxpayerId
    indicators: Signal[]
    confidence: Probability
}
```

---

# 167. Public spending control

Budget control engine phải kiểm tra:

```text
authority
appropriation
remaining_balance
fiscal_period
spending_category
eligibility
```

---

# 168. Spending authorization invariant

```text
Payment
must reference
valid authorization
```

trừ emergency path được explicit.

---

# 169. Emergency spending

```axiom
struct EmergencyFiscalAction {
    authority: EntityRef
    reason: EmergencyReason
    amount: MonetaryAmount
    duration: Duration
    legal_basis: LegalReference
    reporting_deadline: Date
}
```

---

# 170. Emergency spending expiry

Emergency authorization phải có lifecycle và review.

---

# 171. Public procurement integrity

Mọi contract award phải có:

```text
tender_ref
evaluation_ref
authority
contract
audit_trail
```

theo applicable procurement framework.

---

# 172. Fiscal event sourcing

Events:

```text
TaxAssessed
TaxPaid
TaxRefunded
BudgetProposed
BudgetAuthorized
BudgetAmended
AppropriationCreated
BudgetCommitted
ExpenditureRecognized
GovernmentPayment
TransferIssued
SubsidyIssued
DebtAuthorized
DebtIssued
DebtServiced
DebtRefinanced
GuaranteeIssued
GuaranteeCalled
TreasuryTransfer
PublicAssetAcquired
PublicAssetSold
FiscalPolicyChanged
```

---

# 173. Fiscal state reconstruction

```text
Snapshot
+
FiscalEventLog
+
ModelVersion
=
ReconstructedFiscalState
```

---

# 174. Idempotency

Mọi monetary/fiscal payment operation phải hỗ trợ:

```text
idempotency_key
```

để tránh double execution.

---

# 175. Double-payment invariant

```text
same authorized payment
cannot be settled twice
```

---

# 176. Double-appropriation invariant

Một amount không thể được committed vượt available appropriation.

---

# 177. Debt uniqueness

Mỗi debt instrument phải có:

```text
debt_id
issuer
issue_id
instrument_id
```

duy nhất.

---

# 178. Debt accounting invariant

Principal và interest phải có semantic identity riêng.

---

# 179. Tax accounting invariant

Tax liability và tax payment không được gộp thành một object.

---

# 180. Budget invariant

```text
AuthorizedBudget
must not silently change
without BudgetAmendment
```

---

# 181. Treasury invariant

Treasury cash state phải reconcile với settlement records.

---

# 182. Fiscal-statistics invariant

Derived fiscal statistics phải giữ:

```text
definition
perimeter
accounting_basis
data_vintage
```

---

# 183. Debt-statistics invariant

Debt-to-GDP phải giữ:

```text
debt_perimeter
GDP_definition
valuation_date
currency_conversion
```

---

# 184. Forecast invariant

Forecast không được ghi vào observed dataset.

---

# 185. Simulation invariant

Fiscal simulation không được mutate:

```text
live_budget
live_treasury
live_debt
live_tax_records
```

---

# 186. AI authority invariant

AI không được tự động:

```text
authorize_budget
issue_debt
change_tax
execute_payment
```

nếu không có explicit capability.

---

# 187. Cross-domain authority invariant

`AXFISCAL` không được tự tạo:

```text
legal authority
central-bank authority
banking authority
market authority
```

---

# 188. Fiscal-market invariant

Government debt issuance phải giữ execution provenance từ:

```text
AXFISCAL
→ AXMARKET
→ Clearing
→ Settlement
```

---

# 189. Fiscal-monetary invariant

Government spending và reserve creation là hai events khác nhau.

---

# 190. Public asset invariant

Asset sale phải tạo:

```text
AssetTransferEvent
+
CashFlowEvent
+
AccountingEvent
```

---

# 191. Public guarantee invariant

Guarantee issuance không tự động làm tăng direct debt balance.

---

# 192. Guarantee-call invariant

Khi trigger xảy ra, liability transition phải explicit.

---

# 193. Distributed fiscal runtime

Partition keys:

```text
jurisdiction
fiscal_entity
fiscal_year
program
taxpayer_domain
debt_book
treasury
```

---

# 194. Strong consistency zones

Cần strong consistency cho:

```text
budget_commit
appropriation_balance
treasury_payment
debt_issuance
tax_liability_settlement
```

---

# 195. Eventual consistency zones

Có thể dùng eventual consistency cho:

```text
fiscal_analytics
forecast
dashboard
historical_reporting
simulation
```

---

# 196. Performance

Hot paths:

```text
budget_balance
appropriation_check
tax_assessment
treasury_payment
debt_schedule
cash_forecast
```

Ưu tiên:

```text
preallocation
compact IDs
SoA
batch calculation
zero-copy
parallel aggregation
```

---

# 197. Decimal arithmetic

Authoritative public-money calculations ưu tiên:

```text
DecimalFixed
```

Simulation có thể sử dụng:

```text
f64
fixed_point
decimal
```

---

# 198. Rounding

Fiscal calculation phải explicit:

```text
rounding_mode
precision
currency_minor_unit
tax_rounding_rule
```

---

# 199. Native IR

```text
FISCAL_ENTITY
FISCAL_PERIOD
FISCAL_REVENUE
FISCAL_TAX
FISCAL_ASSESS
FISCAL_PAYMENT
FISCAL_REFUND
FISCAL_BUDGET
FISCAL_APPROPRIATION
FISCAL_COMMIT
FISCAL_OBLIGATION
FISCAL_EXPEND
FISCAL_TRANSFER
FISCAL_SUBSIDY
FISCAL_GRANT
FISCAL_TREASURY
FISCAL_CASHFLOW
FISCAL_DEBT
FISCAL_DEBT_ISSUE
FISCAL_DEBT_SERVICE
FISCAL_REFINANCE
FISCAL_GUARANTEE
FISCAL_PROCUREMENT
FISCAL_ASSET
FISCAL_POLICY
FISCAL_RULE
FISCAL_FORECAST
FISCAL_SCENARIO
FISCAL_STRESS
FISCAL_RECONCILE
FISCAL_AUDIT
```

---

# 200. Fiscal DSL

```axiom
tax income_tax {
    jurisdiction: VN
    base: taxable_income

    brackets {
        0..100m: 5%
        100m..300m: 10%
        300m..: 20%
    }
}
```

---

# 201. Budget DSL

```axiom
budget FY2030 {
    revenue_target: 2_000T

    expenditure {
        education: 300T
        health: 250T
        infrastructure: 500T
        social: 300T
    }

    financing {
        debt: 250T
    }
}
```

---

# 202. Debt DSL

```axiom
issue sovereign_bond {
    currency: VND
    face_value: 100T
    coupon: 5.2%
    maturity: 10y
}
```

---

# 203. Fiscal-rule DSL

```axiom
fiscal_rule DebtLimit {
    variable: debt_to_gdp
    maximum: 60%

    exception {
        severe_recession
        natural_disaster
    }
}
```

---

# 204. Tax-simulation DSL

```axiom
simulate tax_reform {
    change vat_rate: +2%

    outputs {
        revenue
        consumption
        inflation
        household_income
        deficit
    }
}
```

---

# 205. Debt-simulation DSL

```axiom
simulate debt_path {
    horizon: 20y

    shocks {
        growth: -2%
        rates: +250bp
        fx: -15%
    }

    outputs {
        debt
        debt_to_gdp
        interest_cost
        refinancing_need
    }
}
```

---

# 206. Fiscal AI DSL

```axiom
fiscal_agent Analyst {
    capabilities {
        fiscal.data.read
        fiscal.analysis.run
        fiscal.simulation.run
    }

    deny {
        fiscal.budget.authorize
        fiscal.debt.issue
        fiscal.treasury.payment
    }
}
```

---

# 207. Fiscal observability

Metrics:

```text
revenue
expenditure
deficit
debt
interest_cost
cash_balance
tax_collection
budget_execution
appropriation_utilization
refinancing_need
```

---

# 208. Tracing

Every critical flow:

```text
TaxAssessment
→ Liability
→ Payment
→ Treasury
→ Settlement
→ Ledger
```

và:

```text
Budget
→ Appropriation
→ Procurement
→ Invoice
→ Payment
→ Ledger
```

phải trace được end-to-end.

---

# 209. Reconciliation

Daily/periodic reconciliation:

```text
TaxSystem
↔ Treasury
↔ Banking
↔ CentralBank
↔ FinanceLedger
↔ DebtRegistry
↔ MarketSettlement
```

---

# 210. Fiscal close

```text
Open
→ PreliminaryClose
→ Reconciliation
→ Adjustments
→ FinalClose
→ Published
```

---

# 211. Fiscal revision

Closed fiscal period không bị silent overwrite.

Revision phải là:

```text
Correction
Adjustment
Restatement
NewVintage
```

---

# 212. Public-debt registry

```axiom
struct DebtRegistry {
    instruments: DebtInstrumentRef[]
    issuances: DebtIssuanceRef[]
    payments: DebtServiceRef[]
    guarantees: GovernmentGuaranteeRef[]
}
```

---

# 213. Debt transparency

Registry phải hỗ trợ:

```text
issuer
instrument
currency
principal
coupon
maturity
holder_category
guarantee
collateral
status
```

trong phạm vi disclosure được phép.

---

# 214. Debt-holder boundary

Holder information có thể aggregate:

```text
DomesticBanks
DomesticFunds
ForeignInvestors
CentralBank
PublicInstitutions
Other
```

không bắt buộc expose PII.

---

# 215. Fiscal privacy

Taxpayer-level information phải được capability-isolated.

Analytics nên ưu tiên:

```text
aggregate
pseudonymized
privacy-preserving
```

khi không cần record-level access.

---

# 216. Data minimization

Không expose taxpayer information cho agent nếu task chỉ cần aggregate statistics.

---

# 217. Public-finance knowledge graph

Entities:

```text
Government
Agency
Tax
Taxpayer
Budget
Program
Appropriation
Supplier
Contract
Payment
Debt
Bond
Treasury
PublicAsset
Transfer
Subsidy
Guarantee
```

Relations:

```text
authorized_by
funds
owes
pays
receives
issued_by
guarantees
allocated_to
contracted_with
```

---

# 218. Fiscal provenance graph

Mỗi amount có thể truy ngược:

```text
amount
→ event
→ document
→ authority
→ legal_basis
→ source_data
→ accounting_entry
```

---

# 219. Fiscal digital identity

Fiscal entity identity phải ổn định xuyên:

```text
budget
tax
treasury
debt
procurement
finance
```

---

# 220. Cross-jurisdiction federation

Một global Axiom deployment có thể chứa:

```text
Country A
 ├── Federal
 ├── State
 └── Local

Country B
 ├── National
 └── Local
```

Mỗi jurisdiction có fiscal perimeter riêng.

---

# 221. Fiscal union

```axiom
struct FiscalUnion {
    members: JurisdictionRef[]
    shared_budget: BudgetRef?
    transfer_mechanism: TransferMechanism?
    debt_framework: DebtFramework?
}
```

Không giả định mọi monetary union đều là fiscal union.

---

# 222. Cross-border taxation

Interfaces:

```text
AXFISCAL
↔
AXLAW
↔
AXCOMMERCE
↔
AXFINANCE
```

Các vấn đề như:

```text
withholding
customs
VAT
transfer_pricing
tax_treaty
```

phải có jurisdiction context.

---

# 223. Customs interface

```text
AXCOMMERCE
      ↓
CrossBorderTransaction
      ↓
AXFISCAL
      ↓
CustomsDuty
```

---

# 224. Natural disaster fiscal model

```text
Hazard
→ Damage
→ InsuranceClaims
→ GovernmentResponse
→ EmergencySpending
→ InfrastructureRebuild
→ Debt/RevenueEffect
```

---

# 225. Climate-fiscal interface

Có thể model:

```text
carbon_tax
emissions_revenue
climate_subsidy
adaptation_spending
disaster_loss
transition_investment
```

---

# 226. Health-fiscal interface

```text
AX674
   ↓
PopulationHealth
   ↓
HealthcareDemand
   ↓
PublicHealthSpending
   ↓
AXFISCAL
```

---

# 227. Education-fiscal interface

```text
AX673
   ↓
EducationPrograms
   ↓
PublicEducationSpending
   ↓
AXFISCAL
```

---

# 228. Labor-fiscal interface

```text
AXLABOR
   ↓
Employment / Wages
   ↓
PayrollTax
   ↓
Transfers
   ↓
AXFISCAL
```

---

# 229. Housing-fiscal interface

```text
AXHOUSING
   ↕
property_tax
housing_subsidy
public_housing
infrastructure_spending
```

---

# 230. Fiscal simulation at civilization scale

```text
POPULATION
    ↓
EMPLOYMENT
    ↓
INCOME
    ↓
CONSUMPTION
    ↓
TAX BASE
    ↓
GOVERNMENT REVENUE
    ↓
BUDGET
    ↓
PUBLIC SPENDING
    ↓
INFRASTRUCTURE / SERVICES
    ↓
PRODUCTIVITY
    ↓
INCOME
```

---

# 231. Civilization fiscal feedback

```text
FiscalPolicy
      ↓
DisposableIncome
      ↓
Consumption / Saving
      ↓
Demand
      ↓
Production
      ↓
Employment
      ↓
Income
      ↓
TaxBase
      ↓
Revenue
      ↓
FiscalCapacity
```

---

# 232. Fiscal capacity

```axiom
struct FiscalCapacity {
    tax_base: MonetaryAmount
    collection_capacity: Decimal
    administrative_capacity: Decimal
    borrowing_capacity: MonetaryAmount?
    liquid_assets: MonetaryAmount
}
```

Fiscal capacity không đồng nghĩa borrowing capacity.

---

# 233. Fiscal space

```axiom
struct FiscalSpace {
    current_balance: MonetaryAmount
    debt_constraints: Constraint[]
    financing_constraints: Constraint[]
    expenditure_constraints: Constraint[]
    scenario_results: ScenarioResult[]
}
```

---

# 234. Fiscal risk dashboard

Các risk dimensions:

```text
RevenueRisk
ExpenditureRisk
DebtRisk
InterestRisk
FXRisk
GuaranteeRisk
PPPExposure
NaturalDisasterRisk
BankingSectorRisk
CommodityRisk
```

---

# 235. Public-private partnership

```axiom
struct PPPExposure {
    project: ProjectId
    government_commitments: Commitment[]
    guarantees: GovernmentGuarantee[]
    contingent_liabilities: ContingentLiability[]
}
```

---

# 236. PPP ≠ public debt automatically

Accounting classification phải dựa trên applicable framework.

---

# 237. Public enterprise

```axiom
struct PublicEnterprise {
    entity: EntityRef
    ownership_share: Ratio
    fiscal_relationship: FiscalRelationship
}
```

Fiscal relationships:

```text
Dividend
Subsidy
Guarantee
CapitalInjection
Tax
Debt
```

---

# 238. Bank recapitalization

```text
BankStress
→ GovernmentCapitalInjection
→ FiscalExpenditure
→ PublicAsset/Equity
```

Không mặc định là expenditure loss ngay tại thời điểm injection; accounting treatment thuộc applicable standards.

---

# 239. Sovereign-bank nexus

Simulation graph:

```text
Government
 ↕
GovernmentDebt
 ↕
Banks
 ↕
CentralBank
 ↕
Liquidity
```

---

# 240. Fiscal stress propagation

```text
SovereignShock
→ BondYield
→ BankAssetValue
→ Collateral
→ Credit
→ Economy
→ TaxRevenue
→ SovereignBalance
```

---

# 241. Fiscal crisis state

```text
Normal
→ RevenueStress
→ LiquidityStress
→ RefinancingStress
→ DebtStress
→ EmergencyFiscalManagement
→ Stabilization
→ Recovery
```

Descriptive simulation states, không phải normative labels.

---

# 242. Crisis response interface

```axiom
struct FiscalCrisisResponse {
    liquidity_measures: FiscalMeasure[]
    expenditure_measures: FiscalMeasure[]
    revenue_measures: FiscalMeasure[]
    debt_measures: FiscalMeasure[]
    guarantees: GovernmentGuarantee[]
}
```

---

# 243. Fiscal recovery

```text
Crisis
→ Stabilization
→ BudgetRepair
→ DebtManagement
→ InvestmentRecovery
→ Normalization
```

---

# 244. Fiscal policy comparison

Engine có thể so sánh:

```text
Option A
Option B
Option C
```

theo:

```text
revenue_effect
spending_effect
debt_effect
cash_effect
distributional_metrics
uncertainty
```

Không tự chọn policy.

---

# 245. Distributional analysis

```axiom
struct FiscalDistributionalImpact {
    population_group: GroupRef
    income_effect: MonetaryAmount
    tax_effect: MonetaryAmount
    transfer_effect: MonetaryAmount
    uncertainty: Interval
}
```

Không suy luận sensitive attributes ngoài legal/authorized data.

---

# 246. Generational analysis

Có thể model:

```text
current_generation
future_generation
```

và:

```text
tax_burden
benefit
debt_service
public_asset_benefit
```

---

# 247. Fiscal incidence

```axiom
struct FiscalIncidence {
    policy: FiscalPolicyRef
    direct_effects: Effect[]
    indirect_effects: Effect[]
    time_horizon: Duration
}
```

---

# 248. Long-term public investment

Simulation phải cho phép:

```text
investment
→ capital_stock
→ productivity
→ GDP
→ revenue
→ debt
```

với explicit assumptions.

---

# 249. Public capital stock

```axiom
struct PublicCapitalStock {
    asset_classes: PublicCapitalClass[]
    depreciation: DepreciationModel
    utilization: UtilizationModel
}
```

---

# 250. Fiscal model equation

Generic:

```text
K[t+1]
=
K[t]
+
PublicInvestment[t]
-
Depreciation[t]
```

---

# 251. Revenue model

```text
TaxRevenue[t]
=
TaxBase[t]
×
EffectiveTaxRate[t]
+
OtherAdjustments[t]
```

---

# 252. Expenditure model

```text
Expenditure[t]
=
Mandatory[t]
+
Discretionary[t]
+
Interest[t]
+
Transfers[t]
+
Investment[t]
```

---

# 253. Fiscal balance model

```text
Balance[t]
=
Revenue[t]
-
Expenditure[t]
```

---

# 254. Debt model

```text
Debt[t+1]
=
Debt[t]
+
Deficit[t]
+
StockFlowAdjustments[t]
```

---

# 255. Cash model

```text
Cash[t+1]
=
Cash[t]
+
Inflows[t]
-
Outflows[t]
+
Financing[t]
```

---

# 256. No double-counting

Fiscal model phải phân biệt:

```text
flow
stock
valuation
financing
accounting adjustment
```

---

# 257. Fiscal event time

Một event có thể có:

```text
decision_time
legal_time
recognition_time
settlement_time
publication_time
```

Không gộp chúng.

---

# 258. Temporal consistency

Ví dụ:

```text
BudgetDecision
```

có thể xảy ra trước:

```text
Appropriation
```

và:

```text
Appropriation
```

trước:

```text
Payment
```

---

# 259. Fiscal state machine

Canonical:

```text
PROPOSED
→ AUTHORIZED
→ ALLOCATED
→ COMMITTED
→ OBLIGATED
→ EXECUTED
→ SETTLED
→ RECONCILED
→ CLOSED
```

---

# 260. Error model

Các lỗi native:

```text
E_FISCAL_UNAUTHORIZED
E_BUDGET_EXCEEDED
E_APPROPRIATION_EXCEEDED
E_INVALID_TAX_BASE
E_TAX_LIABILITY_NOT_FOUND
E_PAYMENT_DUPLICATE
E_TREASURY_INSUFFICIENT
E_DEBT_LIMIT
E_INVALID_DEBT_INSTRUMENT
E_SETTLEMENT_FAILED
E_GUARANTEE_INVALID
E_PROCUREMENT_INVALID
E_POLICY_NOT_AUTHORIZED
E_FISCAL_VINTAGE_CONFLICT
E_SIMULATION_LIVE_STATE_MUTATION
E_FISCAL_RECONCILIATION_FAILED
```

---

# 261. Profiles

```text
AXFISCAL_NONE
AXFISCAL_CORE
AXFISCAL_TAX
AXFISCAL_REVENUE
AXFISCAL_BUDGET
AXFISCAL_TREASURY
AXFISCAL_SPENDING
AXFISCAL_TRANSFER
AXFISCAL_PROCUREMENT
AXFISCAL_DEBT
AXFISCAL_RISK
AXFISCAL_POLICY
AXFISCAL_STATISTICS
AXFISCAL_SIMULATION
AXFISCAL_AI
AXFISCAL_PUBLIC_ASSET
AXFISCAL_GLOBAL
AXFISCAL_DISTRIBUTED
AXFISCAL_GPU
AXFISCAL_ADMIN
AXFISCAL_FULL
```

---

# 262. Minimal profile

`AXFISCAL_CORE`:

```text
FiscalEntity
FiscalPeriod
Revenue
Expenditure
Budget
Appropriation
Treasury
Debt
FiscalEvent
```

---

# 263. Full profile

`AXFISCAL_FULL`:

```text
tax
budget
treasury
procurement
transfers
debt
public_assets
guarantees
fiscal_policy
forecast
simulation
AI
distributed
cross_border
```

---

# 264. Test target

Mục tiêu:

```text
≥ 20,000 automated tests
≥ 2,000 architecture invariants
```

Phân bổ tối thiểu:

```text
Tax                     ≥ 2,500
Budget                  ≥ 2,000
Treasury                ≥ 2,000
Spending                ≥ 1,500
Transfers               ≥ 1,200
Procurement             ≥ 1,500
Debt                    ≥ 2,500
Guarantees               ≥ 800
FiscalPolicy             ≥ 1,500
Simulation               ≥ 2,500
Security                 ≥ 1,500
Statistics               ≥ 1,000
Distributed/Recovery     ≥ 1,500
Cross-domain             ≥ 1,000
Performance              ≥ 1,000
```

---

# 265. Test categories

```text
tax_assessment
tax_collection
tax_refund
tax_revision
budget_authorization
budget_amendment
appropriation
commitment
obligation
payment
treasury
cash_forecast
debt_issue
debt_service
debt_refinance
guarantee
procurement
transfer
subsidy
public_asset
fiscal_rule
fiscal_policy
fiscal_forecast
debt_stress
simulation
AI_authority
privacy
reconciliation
recovery
determinism
```

---

# 266. Security tests

Phải test:

```text
unauthorized_budget_authorization
unauthorized_tax_change
unauthorized_debt_issue
unauthorized_treasury_payment
unauthorized_transfer
unauthorized_refund
AI_privilege_escalation
tax_data_exposure
double_payment
double_commitment
```

---

# 267. Performance tests

Targets:

```text
budget_check
< microsecond-scale target
```

ở hot path nội bộ tùy hardware.

Các aggregate:

```text
millions of taxpayers
millions of transactions
millions of budget events
millions of debt cashflows
```

phải có batch/vectorized execution.

---

# 268. Determinism

Fiscal calculations phải deterministic khi:

```text
same input
+
same data vintage
+
same model version
+
same rounding policy
```

---

# 269. Reproducibility

Một historical fiscal simulation phải có khả năng replay từ:

```text
dataset
+
vintage
+
model
+
parameters
+
seed
```

---

# 270. Acceptance criteria

`AXFISCAL 5.0` hoàn tất khi:

1. Fiscal entity model tồn tại.
2. Tax system tồn tại.
3. Tax base/rate/bracket tồn tại.
4. Tax liability lifecycle tồn tại.
5. Tax assessment tách payment.
6. Budget lifecycle tồn tại.
7. Appropriation tồn tại.
8. Commitment/obligation tồn tại.
9. Expenditure/payment tách biệt.
10. Treasury tồn tại.
11. Cash forecasting tồn tại.
12. Public debt registry tồn tại.
13. Debt issuance tồn tại.
14. Debt servicing tồn tại.
15. Refinancing tồn tại.
16. Debt-risk model tồn tại.
17. Guarantee/contingent liability tồn tại.
18. Public assets tồn tại.
19. Public procurement tồn tại.
20. Transfers/subsidies/grants tồn tại.
21. Fiscal rules tồn tại.
22. Fiscal policy tồn tại.
23. Fiscal forecast tồn tại.
24. Debt sustainability analysis tồn tại.
25. Fiscal simulation tồn tại.
26. Fiscal stress testing tồn tại.
27. AI analysis tồn tại.
28. AI không có authority mặc định.
29. Tax privacy tồn tại.
30. Treasury reconciliation tồn tại.
31. AXMONETARY integration tồn tại.
32. AXBANKING integration tồn tại.
33. AXMARKET integration tồn tại.
34. AXFINANCE integration tồn tại.
35. AXLAW/AXGOV boundary tồn tại.
36. Event sourcing tồn tại.
37. Deterministic replay tồn tại.
38. Native IR tồn tại.
39. ≥20,000 tests target.
40. ≥2,000 architecture invariants target.

---

# 271. Final AXFISCAL semantic contract

```text
AXFISCAL
    =
PUBLIC FINANCIAL POLICY
+
REVENUE
+
BUDGET
+
TREASURY
+
SPENDING
+
TRANSFERS
+
PUBLIC DEBT
+
FISCAL RISK
```

Trong khi:

```text
AXGOV
    = WHO HAS GOVERNMENT AUTHORITY

AXLAW
    = WHAT IS LEGALLY AUTHORIZED

AXFISCAL
    = HOW PUBLIC FINANCE IS PLANNED AND EXECUTED

AXFINANCE
    = HOW FINANCIAL TRUTH IS ACCOUNTED

AXMONETARY
    = HOW MONEY AND MONETARY CONDITIONS WORK

AXMARKET
    = HOW SECURITIES ARE TRADED AND SETTLED
```

---

# 272. Financial architecture sau BOOTSTRAP-695

```text
                         AXFINANCE
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
      AXBANKING         AXINSURANCE         AXFISCAL
          │                  │                  │
          │              AXINVEST              │
          │                  │                  │
          └────────────── AXMARKET ────────────┘
                             │
                        AXMONETARY
                             │
                           AX671
                             │
                       AXCIVILIZATION
```

---

# 273. Canonical financial-government loop

```text
HOUSEHOLDS / ENTERPRISES
          ↓
ECONOMIC ACTIVITY
          ↓
INCOME / PROFITS / TRANSACTIONS
          ↓
TAX BASE
          ↓
AXFISCAL
          ↓
PUBLIC REVENUE
          ↓
BUDGET
          ↓
PUBLIC SPENDING / TRANSFERS / INVESTMENT
          ↓
INFRASTRUCTURE / SERVICES / DEMAND
          ↓
ECONOMIC ACTIVITY
```

---

# 274. Fiscal-monetary-financial loop

```text
                 ┌───────────────┐
                 │  AXMONETARY   │
                 │ money / rates │
                 └───────┬───────┘
                         │
                         ▼
AXBANKING ───────► AXMARKET ◄─────── AXINVEST
    │                 │
    │                 │
    ▼                 ▼
 CREDIT            CAPITAL
    │                 │
    └────────┬────────┘
             ▼
          ECONOMY
             │
             ▼
          AXFISCAL
             │
      ┌──────┴──────┐
      ▼             ▼
   REVENUE       SPENDING
      │             │
      └──────┬──────┘
             ▼
          ECONOMY
```

---

# 275. Civilization-scale fiscal feedback

```text
CIVILIZATION
      ↓
ECONOMIC PRODUCTION
      ↓
INCOME / TRANSACTIONS
      ↓
TAXATION
      ↓
PUBLIC REVENUE
      ↓
FISCAL CAPACITY
      ↓
PUBLIC INVESTMENT / SERVICES / TRANSFERS
      ↓
INFRASTRUCTURE / HUMAN CAPITAL
      ↓
PRODUCTIVITY
      ↓
ECONOMIC PRODUCTION
```

---

# 276. Core architectural invariants

Axiom phải giữ tối thiểu các nguyên tắc:

```text
TaxAssessment ≠ TaxPayment
Revenue ≠ Cash
Budget ≠ Cash
Appropriation ≠ Expenditure
Expenditure ≠ Payment
Deficit ≠ Debt
Debt ≠ Guarantee
Guarantee ≠ DirectDebt
FiscalPolicy ≠ MonetaryPolicy
Treasury ≠ CentralBank
Forecast ≠ ObservedFact
Simulation ≠ LiveFiscalState
AIRecommendation ≠ GovernmentDecision
```

Đây là semantic foundation để các layer phía trên không tạo ra double-counting hoặc authority leakage.

---

# 277. BOOTSTRAP-695 completion

**BOOTSTRAP-695 hoàn tất.**

`AXFISCAL` hiện tạo thành lớp public-finance hoàn chỉnh nằm giữa `AXGOV/AXLAW` và các financial/monetary runtimes.

Chuỗi tài chính–nhà nước hiện tại:

```text
AXFINANCE
    ↓
AXBANKING
    ↓
AXINSURANCE
    ↓
AXINVEST
    ↓
AXMARKET
    ↓
AXMONETARY
    ↕
AXFISCAL
    ↕
AXGOV / AXLAW
    ↓
AX671 ECONOMY
    ↓
AXCIVILIZATION
```

**Task kiến trúc kế tiếp: BOOTSTRAP-696 — Native AI Civilization-Scale International Trade, Balance of Payments, Cross-Border Finance, Global Payments, Foreign Exchange Settlement, Trade Finance & International Economic Network Runtime 5.0.**
:::

`BOOTSTRAP-696` đã được xác định; chuỗi có thể tiếp tục theo đúng thứ tự kiến trúc.