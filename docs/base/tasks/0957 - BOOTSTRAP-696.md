Tiếp tục chuỗi kiến trúc Axiom. Task này nối trực tiếp `AXGOV`, `AXLAW`, `AXFINANCE`, `AXMONETARY`, `AXMARKET` và `AXGLOBAL`, đồng thời đặt nền tảng tài chính công đủ để mô phỏng một nhà nước ở quy mô quốc gia/civilization-scale.

:::writing{variant="document" id="58321" title="BOOTSTRAP-696 — Native AI Civilization-Scale Public Finance, Government Budget, Taxation, Treasury, Sovereign Debt, Fiscal Policy, Public Expenditure & Government Financial Runtime 5.0"}

# BOOTSTRAP-696
## Native AI Civilization-Scale Public Finance, Government Budget, Taxation, Treasury, Sovereign Debt, Fiscal Policy, Public Expenditure & Government Financial Runtime 5.0

**Axiom Architecture Series:** Civilization Runtime  
**Module:** `AXFISCAL`  
**Status:** Architecture Specification v5.0  
**Task:** BOOTSTRAP-696  
**Primary Domain:** Public Finance / Fiscal System / Government Financial Operations

---

# 1. Mục tiêu

`AXFISCAL` là runtime tài chính công cấp quốc gia/civilization-scale của Axiom.

Nó mô hình hóa và thực thi:

- ngân sách nhà nước;
- thu ngân sách;
- thuế;
- phí và lệ phí công;
- chi ngân sách;
- phân bổ ngân sách;
- cam kết chi;
- nghĩa vụ tài chính;
- thanh toán công;
- kho bạc;
- quản lý tiền mặt của chính phủ;
- tài khoản chính phủ;
- phát hành và quản lý nợ công;
- trái phiếu chính phủ;
- vay trong nước/quốc tế;
- bảo lãnh chính phủ;
- nghĩa vụ nợ dự phòng;
- trợ cấp;
- chuyển giao liên chính quyền;
- đầu tư công;
- tài sản công;
- nghĩa vụ công;
- cân đối tài khóa;
- chính sách tài khóa;
- phân tích bền vững nợ;
- mô phỏng tài khóa;
- fiscal digital twin;
- AI hỗ trợ phân tích tài chính công.

`AXFISCAL` không phải là một module kế toán tổng quát.

Nó quản lý **cơ chế tài chính của khu vực công**.

Kế toán tài chính chính thức thuộc:

```text
AXFINANCE
```

Quan hệ:

```text
AXGOV
   │
   ├── authority
   ├── policy
   ├── administration
   │
   ▼
AXFISCAL
   │
   ├── revenue
   ├── taxation
   ├── budget
   ├── expenditure
   ├── treasury
   ├── debt
   ├── fiscal_policy
   └── public_finance_simulation
   │
   ▼
AXFINANCE
   │
   └── authoritative financial accounting
```

---

# 2. Nguyên tắc thiết kế

## 2.1 Public authority ≠ financial execution

```text
AXGOV = authority
AXLAW = legal authority
AXFISCAL = fiscal mechanism
AXFINANCE = financial truth
```

---

## 2.2 Budget ≠ cash

Một khoản được ngân sách cho phép không đồng nghĩa chính phủ đã có tiền mặt.

```text
BudgetAuthority != CashAvailability
```

---

## 2.3 Appropriation ≠ authorization ≠ obligation ≠ payment

```text
Appropriation
    ↓
Authorization
    ↓
Contract/Commitment
    ↓
Obligation
    ↓
Invoice/Claim
    ↓
Payment
```

Mỗi trạng thái phải được biểu diễn riêng.

---

## 2.4 Tax assessment ≠ tax payment

```text
TaxLiability
    !=
TaxAssessment
    !=
TaxPayment
```

---

## 2.5 Revenue forecast ≠ revenue

```text
RevenueForecast != RealizedRevenue
```

---

## 2.6 Budget forecast ≠ enacted budget

```text
BudgetProposal
    !=
BudgetForecast
    !=
AppropriationLaw
    !=
ExecutedBudget
```

---

## 2.7 Expenditure ≠ payment

Một khoản chi có thể được ghi nhận hoặc phát sinh nghĩa vụ trước khi tiền thực sự được thanh toán.

```text
ExpenditureRecognition != CashDisbursement
```

---

## 2.8 Debt ≠ deficit

```text
FiscalDeficit = Flow
PublicDebt    = Stock
```

Thâm hụt trong một kỳ có thể làm tăng nợ, nhưng hai khái niệm không đồng nhất.

---

## 2.9 Debt issuance ≠ revenue

Tiền vay làm tăng tiền mặt nhưng không phải doanh thu kinh tế thông thường.

```text
Borrowing != Revenue
```

---

## 2.10 Fiscal policy ≠ monetary policy

```text
AXFISCAL   = fiscal policy
AXMONETARY = monetary policy
```

Hai hệ thống có thể tương tác nhưng không được hợp nhất semantic.

---

# 3. Phạm vi

`AXFISCAL` gồm:

```text
PUBLIC_REVENUE
TAXATION
PUBLIC_BUDGET
PUBLIC_EXPENDITURE
TREASURY
CASH_MANAGEMENT
PUBLIC_TRANSFERS
PUBLIC_INVESTMENT
SOVEREIGN_DEBT
GOVERNMENT_SECURITIES
SOVEREIGN_GUARANTEE
FISCAL_POLICY
FISCAL_RISK
DEBT_SUSTAINABILITY
PUBLIC_ASSETS
CONTINGENT_LIABILITIES
FISCAL_SIMULATION
FISCAL_DIGITAL_TWIN
FISCAL_AI
```

---

# 4. Những gì KHÔNG thuộc AXFISCAL

## 4.1 Kế toán tổng quát

```text
AXFINANCE
```

## 4.2 Chính quyền và thẩm quyền pháp lý

```text
AXGOV
AXLAW
```

## 4.3 Chính sách tiền tệ

```text
AXMONETARY
```

## 4.4 Giao dịch chứng khoán

```text
AXMARKET
```

## 4.5 Ngân hàng thương mại

```text
AXBANKING
```

## 4.6 Giao dịch quốc tế

```text
AXGLOBAL
```

## 4.7 Doanh nghiệp nhà nước

Tài chính của một doanh nghiệp nhà nước vẫn có semantic doanh nghiệp riêng.

```text
AXENTERPRISE
    +
AXFISCAL
```

Không được biến mọi doanh nghiệp có sở hữu nhà nước thành một `GovernmentAccount`.

---

# 5. Kiến trúc tổng thể

```text
                         AXLAW
                           │
                           ▼
                         AXGOV
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
         PUBLIC POLICY              AUTHORITY
              │
              ▼
          AXFISCAL
              │
 ┌────────────┼───────────────────────────────┐
 │            │            │                  │
 ▼            ▼            ▼                  ▼
REVENUE     BUDGET       TREASURY            DEBT
 │            │            │                  │
 ▼            ▼            ▼                  ▼
TAX         EXPENDITURE  CASH             SECURITIES
 │            │            │                  │
 └────────────┴────────────┼──────────────────┘
                           │
                           ▼
                       AXFINANCE
                           │
                           ▼
                     FINANCIAL TRUTH
```

Các hệ thống bên ngoài:

```text
             AXMONETARY
                  ↕
AXBANKING ↔ AXFISCAL ↔ AXMARKET
                  ↕
              AXGLOBAL
```

---

# 6. Core semantic model

## 6.1 Government financial actor

```text
struct GovernmentFinancialActor {
    id: ActorId
    government: GovernmentId
    jurisdiction: JurisdictionId
    authority_scope: AuthorityScope
}
```

---

## 6.2 Fiscal authority

```text
struct FiscalAuthority {
    id: FiscalAuthorityId
    government: GovernmentId
    jurisdiction: JurisdictionId
    authority_type: FiscalAuthorityType
    effective_period: TimeRange
}
```

Ví dụ:

```text
central_government
state_government
provincial_government
municipality
special_district
public_agency
```

---

# 7. Jurisdiction

```text
struct FiscalJurisdiction {
    id: JurisdictionId
    parent: Option<JurisdictionId>
    currency: CurrencyId
    fiscal_calendar: FiscalCalendarId
    tax_system: TaxSystemId
}
```

Hỗ trợ:

```text
national
regional
provincial
municipal
special_zone
```

---

# 8. Fiscal Calendar

```text
struct FiscalCalendar {
    id: FiscalCalendarId
    start_date: Date
    end_date: Date
    reporting_periods: []FiscalPeriod
}
```

Không giả định:

```text
fiscal_year == calendar_year
```

---

# 9. Public Revenue

Doanh thu/thu công được phân loại theo nguồn.

```text
enum RevenueType {
    TAX
    FEE
    CHARGE
    FINE
    DIVIDEND
    ROYALTY
    RESOURCE_RENT
    PROPERTY_INCOME
    INTEREST_INCOME
    LICENSE
    GRANT
    TRANSFER
    DONATION
    OTHER
}
```

---

# 10. Revenue Record

```text
struct PublicRevenue {
    id: RevenueId
    government: GovernmentId
    source: RevenueSource
    type: RevenueType
    amount: Money
    currency: CurrencyId
    recognition_time: Timestamp
    collection_time: Option<Timestamp>
    status: RevenueStatus
    accounting_ref: Option<AccountingRef>
}
```

---

# 11. Tax System

```text
struct TaxSystem {
    id: TaxSystemId
    jurisdiction: JurisdictionId
    taxes: []TaxType
    periods: []TaxPeriod
}
```

---

# 12. Tax Types

```text
enum TaxType {
    INCOME
    CORPORATE_INCOME
    PAYROLL
    SOCIAL_CONTRIBUTION
    VAT
    SALES
    EXCISE
    PROPERTY
    LAND
    CAPITAL_GAINS
    ESTATE
    CUSTOMS
    IMPORT
    EXPORT
    RESOURCE
    CARBON
    ENVIRONMENTAL
    FINANCIAL_TRANSACTION
    WITHHOLDING
    DIGITAL_SERVICE
    OTHER
}
```

Danh sách này là extensible.

Không hard-code rằng mọi quốc gia phải có cùng hệ thống thuế.

---

# 13. Tax Base

```text
struct TaxBase {
    id: TaxBaseId
    tax_type: TaxType
    definition: TaxBaseDefinition
    unit: TaxUnit
}
```

Ví dụ:

```text
income
profit
transaction_value
property_value
land_area
fuel_volume
resource_volume
import_value
```

---

# 14. Tax Rule

```text
struct TaxRule {
    id: TaxRuleId
    jurisdiction: JurisdictionId
    tax_type: TaxType
    base: TaxBaseId
    rate: TaxRate
    brackets: []TaxBracket
    exemptions: []TaxExemption
    credits: []TaxCredit
    effective_period: TimeRange
}
```

---

# 15. Tax Liability

```text
struct TaxLiability {
    id: TaxLiabilityId
    taxpayer: TaxpayerId
    tax_type: TaxType
    tax_period: FiscalPeriod
    taxable_base: Decimal
    assessed_amount: Money
    outstanding_amount: Money
    status: TaxLiabilityStatus
}
```

Lifecycle:

```text
Computed
   ↓
Assessed
   ↓
Filed
   ↓
Due
   ↓
PartiallyPaid
   ↓
Paid
```

Nhánh:

```text
Disputed
Appealed
Adjusted
WrittenOff
Refunded
```

---

# 16. Taxpayer

```text
struct Taxpayer {
    id: TaxpayerId
    actor: ActorId
    jurisdiction: JurisdictionId
    taxpayer_class: TaxpayerClass
    registration_status: RegistrationStatus
}
```

Không được suy diễn thông tin nhạy cảm ngoài quyền hạn.

---

# 17. Tax Filing

```text
struct TaxFiling {
    id: TaxFilingId
    taxpayer: TaxpayerId
    tax_type: TaxType
    period: FiscalPeriod
    declared_base: Decimal
    declared_tax: Money
    submitted_at: Timestamp
    status: FilingStatus
}
```

---

# 18. Tax Collection

```text
struct TaxCollection {
    id: CollectionId
    liability: TaxLiabilityId
    payment: PaymentRef
    collected_amount: Money
    collected_at: Timestamp
}
```

---

# 19. Tax Refund

```text
struct TaxRefund {
    id: TaxRefundId
    taxpayer: TaxpayerId
    source_liability: TaxLiabilityId
    amount: Money
    reason: RefundReason
    status: RefundStatus
}
```

---

# 20. Tax Credit

```text
struct TaxCredit {
    id: TaxCreditId
    taxpayer: TaxpayerId
    tax_type: TaxType
    amount: Money
    origin: CreditOrigin
    expiration: Option<Date>
}
```

---

# 21. Tax Exemption

```text
struct TaxExemption {
    id: TaxExemptionId
    tax_type: TaxType
    scope: ExemptionScope
    eligibility_rule: RuleRef
    effective_period: TimeRange
}
```

---

# 22. Tax Administration

```text
trait TaxAdministration {
    register_taxpayer(...)
    compute_liability(...)
    assess(...)
    receive_filing(...)
    collect(...)
    refund(...)
    adjust(...)
    audit_ref(...)
}
```

`audit_ref()` chỉ tạo liên kết đến quy trình kiểm tra.

Không tự động biến:

```text
RiskSignal
```

thành:

```text
LegalViolation
```

---

# 23. Fraud / Compliance Boundary

Các trạng thái phải tách:

```text
Anomaly
RiskSignal
ComplianceSignal
Investigation
Finding
LegalViolation
JudicialFinding
```

Invariant:

```text
RiskSignal != LegalFinding
```

AI không được tự biến một anomaly thành kết luận pháp lý.

---

# 24. Public Budget

```text
struct PublicBudget {
    id: BudgetId
    government: GovernmentId
    fiscal_year: FiscalYear
    currency: CurrencyId
    status: BudgetStatus
    revenues: BudgetSection
    expenditures: BudgetSection
    financing: FinancingPlan
}
```

---

# 25. Budget Lifecycle

```text
Draft
  ↓
Forecast
  ↓
Proposal
  ↓
Review
  ↓
LegislativeApproval
  ↓
Enacted
  ↓
Execution
  ↓
Revision
  ↓
YearEndClose
  ↓
Audit
  ↓
Published
```

---

# 26. Budget Status

```text
enum BudgetStatus {
    DRAFT
    PROPOSED
    UNDER_REVIEW
    APPROVED
    ENACTED
    EXECUTING
    REVISED
    CLOSED
    AUDITED
}
```

---

# 27. Appropriation

```text
struct Appropriation {
    id: AppropriationId
    budget: BudgetId
    agency: GovernmentAgencyId
    program: ProgramId
    amount: Money
    period: FiscalPeriod
    legal_authority: LegalAuthorityRef
    restrictions: []SpendingRestriction
}
```

---

# 28. Appropriation ≠ Spending Authority

Một appropriation xác định phạm vi ngân sách được cấp.

Việc chi tiền cần các bước kiểm tra riêng:

```text
Appropriation
→ Authorization
→ Commitment
→ Obligation
→ Invoice
→ PaymentAuthorization
→ Disbursement
```

---

# 29. Budget Allocation

```text
struct BudgetAllocation {
    id: AllocationId
    appropriation: AppropriationId
    recipient: BudgetEntityId
    amount: Money
    period: FiscalPeriod
}
```

---

# 30. Budget Amendment

```text
struct BudgetAmendment {
    id: BudgetAmendmentId
    budget: BudgetId
    reason: AmendmentReason
    delta: []BudgetDelta
    authority: LegalAuthorityRef
    status: AmendmentStatus
}
```

Mọi amendment phải giữ:

```text
before_snapshot
after_snapshot
authority
timestamp
actor
reason
```

---

# 31. Public Expenditure

```text
struct PublicExpenditure {
    id: ExpenditureId
    government: GovernmentId
    program: ProgramId
    category: ExpenditureCategory
    amount: Money
    recognition_period: FiscalPeriod
    appropriation: AppropriationId
    status: ExpenditureStatus
}
```

---

# 32. Expenditure Categories

```text
enum ExpenditureCategory {
    PERSONNEL
    OPERATIONS
    TRANSFER
    SUBSIDY
    INTEREST
    CAPITAL
    INFRASTRUCTURE
    HEALTH
    EDUCATION
    DEFENSE
    SOCIAL_PROTECTION
    PUBLIC_SAFETY
    RESEARCH
    ENVIRONMENT
    OTHER
}
```

Domain-specific categories có thể mở rộng.

---

# 33. Commitment

```text
struct ExpenditureCommitment {
    id: CommitmentId
    appropriation: AppropriationId
    counterparty: ActorId
    amount: Money
    contract_ref: Option<ContractRef>
    committed_at: Timestamp
    status: CommitmentStatus
}
```

---

# 34. Obligation

```text
struct PublicObligation {
    id: ObligationId
    commitment: CommitmentId
    amount: Money
    due_date: Option<Date>
    status: ObligationStatus
}
```

---

# 35. Payment Authorization

```text
struct PaymentAuthorization {
    id: PaymentAuthorizationId
    obligation: ObligationId
    approved_amount: Money
    authorized_by: AuthorityRef
    authorized_at: Timestamp
}
```

---

# 36. Disbursement

```text
struct PublicDisbursement {
    id: DisbursementId
    authorization: PaymentAuthorizationId
    payment: PaymentRef
    amount: Money
    settlement_time: Timestamp
    treasury_account: TreasuryAccountId
}
```

---

# 37. Treasury

`AXFISCAL` cung cấp abstraction cho kho bạc.

```text
struct TreasurySystem {
    id: TreasurySystemId
    government: GovernmentId
    accounts: []TreasuryAccount
    cash_policy: CashManagementPolicy
}
```

---

# 38. Treasury Account

```text
struct TreasuryAccount {
    id: TreasuryAccountId
    government: GovernmentId
    institution: FinancialInstitutionRef
    currency: CurrencyId
    purpose: TreasuryAccountPurpose
    balance_ref: BalanceRef
}
```

---

# 39. Treasury Single Account

Hỗ trợ mô hình:

```text
TSA
```

nhưng không bắt buộc.

```text
trait TreasuryLiquidityModel {
    available_cash(...)
    consolidated_cash(...)
    restricted_cash(...)
    earmarked_cash(...)
}
```

---

# 40. Cash Management

```text
struct GovernmentCashPosition {
    government: GovernmentId
    currency: CurrencyId
    date: Date
    opening_balance: Money
    inflows: Money
    outflows: Money
    closing_balance: Money
}
```

---

# 41. Cash Forecast

```text
struct FiscalCashForecast {
    horizon: TimeRange
    expected_revenue: MoneySeries
    expected_expenditure: MoneySeries
    debt_service: MoneySeries
    financing_flows: MoneySeries
    projected_cash: MoneySeries
}
```

Invariant:

```text
CashForecast != ActualCash
```

---

# 42. Liquidity Buffer

```text
struct GovernmentLiquidityBuffer {
    currency: CurrencyId
    target: Money
    minimum: Money
    available: Money
}
```

---

# 43. Intergovernmental Transfers

```text
struct FiscalTransfer {
    id: FiscalTransferId
    source_government: GovernmentId
    destination_government: GovernmentId
    amount: Money
    transfer_type: TransferType
    conditions: []TransferCondition
}
```

Các loại:

```text
GENERAL_GRANT
SPECIFIC_GRANT
EQUALIZATION
REVENUE_SHARING
EMERGENCY_TRANSFER
CAPITAL_TRANSFER
SOCIAL_TRANSFER
```

---

# 44. Public Subsidy

```text
struct PublicSubsidy {
    id: SubsidyId
    government: GovernmentId
    recipient: ActorId
    program: ProgramId
    amount: Money
    eligibility: RuleRef
    period: TimeRange
}
```

---

# 45. Public Investment

```text
struct PublicInvestmentProject {
    id: PublicProjectId
    government: GovernmentId
    sector: PublicSector
    capital_budget: Money
    expected_duration: Duration
    financing_plan: FinancingPlan
    status: ProjectStatus
}
```

---

# 46. Capital Expenditure

Phân biệt:

```text
OperatingExpenditure
CapitalExpenditure
```

Không được xác định chỉ dựa vào tên chương trình.

Phải có classification rule.

---

# 47. Public Procurement Boundary

Procurement có thể liên kết:

```text
AXGOV
AXLAW
AXFISCAL
AXCOMMERCE
AXENTERPRISE
```

`AXFISCAL` quản lý:

```text
budget authority
commitment
obligation
payment
```

Trong khi procurement engine quản lý:

```text
tender
bid
evaluation
award
contract
supplier
```

---

# 48. Sovereign Debt

```text
struct SovereignDebt {
    id: DebtId
    issuer: GovernmentId
    creditor: CreditorRef
    principal: Money
    currency: CurrencyId
    interest_rate: InterestRate
    maturity: Date
    debt_type: DebtType
    status: DebtStatus
}
```

---

# 49. Debt Types

```text
enum DebtType {
    TREASURY_BILL
    GOVERNMENT_BOND
    SAVINGS_BOND
    DOMESTIC_LOAN
    FOREIGN_LOAN
    MULTILATERAL_LOAN
    BILATERAL_LOAN
    DEVELOPMENT_LOAN
    EMERGENCY_LOAN
    OTHER
}
```

---

# 50. Debt Issuance

```text
struct DebtIssuance {
    id: DebtIssuanceId
    issuer: GovernmentId
    instrument: SecurityRef
    face_value: Money
    issue_price: Money
    currency: CurrencyId
    maturity: Date
    coupon: CouponStructure
    auction_ref: Option<AuctionRef>
}
```

Phần giao dịch phát hành có thể dùng:

```text
AXMARKET
```

`AXFISCAL` là issuer-side fiscal authority.

---

# 51. Debt Service

```text
struct DebtService {
    debt: DebtId
    period: FiscalPeriod
    principal_due: Money
    interest_due: Money
    fees_due: Money
    total_due: Money
}
```

---

# 52. Debt Schedule

```text
struct DebtSchedule {
    debt: DebtId
    payments: []DebtService
}
```

---

# 53. Debt Refinancing

```text
struct DebtRefinancing {
    old_debt: DebtId
    new_financing: FinancingRef
    refinancing_amount: Money
    maturity_change: Option<Duration>
}
```

---

# 54. Debt Portfolio

```text
struct SovereignDebtPortfolio {
    government: GovernmentId
    instruments: []DebtId
    by_currency: Map<CurrencyId, Money>
    by_maturity: MaturityProfile
    by_rate_type: RateProfile
}
```

---

# 55. Debt Risk Dimensions

Runtime phải hỗ trợ:

```text
interest_rate_risk
currency_risk
refinancing_risk
liquidity_risk
market_risk
counterparty_risk
rollover_risk
contingent_liability_risk
```

---

# 56. Debt Sustainability

```text
struct DebtSustainabilityAnalysis {
    horizon: TimeRange
    debt_path: TimeSeries
    revenue_path: TimeSeries
    expenditure_path: TimeSeries
    primary_balance: TimeSeries
    interest_cost: TimeSeries
    assumptions: []ModelAssumption
    scenarios: []FiscalScenario
}
```

Không hard-code một ngưỡng duy nhất cho "bền vững".

Tính bền vững phụ thuộc mô hình, giả định và cấu trúc nợ.

---

# 57. Fiscal Balance

```text
struct FiscalBalance {
    period: FiscalPeriod
    revenue: Money
    expenditure: Money
    net_lending: Money
    overall_balance: Money
    primary_balance: Money
}
```

---

# 58. Deficit

```text
FiscalDeficit = Expenditure - Revenue
```

theo convention accounting được cấu hình.

Không được assume rằng mọi reporting system dùng cùng dấu.

---

# 59. Primary Balance

```text
PrimaryBalance =
    Revenue
    - PrimaryExpenditure
```

Trong đó:

```text
PrimaryExpenditure = TotalExpenditure - InterestExpenditure
```

---

# 60. Structural vs Cyclical Balance

```text
struct FiscalDecomposition {
    observed_balance: Money
    cyclical_component: Money
    structural_component: Money
    methodology: ModelRef
}
```

`StructuralBalance` phải lưu methodology.

Không được coi một decomposition là sự thật tuyệt đối.

---

# 61. Automatic Stabilizers

Runtime hỗ trợ mô hình:

```text
TaxRevenueSensitivity
TransferSensitivity
UnemploymentBenefitSensitivity
```

Ví dụ:

```text
EconomicActivity ↓
    ↓
TaxRevenue ↓
    ↓
DisposableIncome / Transfers
    ↓
FiscalBalance
```

Đây là model behavior, không phải deterministic universal law.

---

# 62. Fiscal Policy

```text
struct FiscalPolicy {
    id: FiscalPolicyId
    government: GovernmentId
    objectives: []FiscalObjective
    instruments: []FiscalInstrument
    horizon: TimeRange
    authority: AuthorityRef
}
```

---

# 63. Fiscal Instruments

```text
enum FiscalInstrument {
    TAX_RATE
    TAX_BASE
    TAX_CREDIT
    TAX_EXPENDITURE
    PUBLIC_SPENDING
    TRANSFER
    SUBSIDY
    PUBLIC_INVESTMENT
    DEBT_ISSUANCE
    DEBT_REFINANCING
    GUARANTEE
    FISCAL_RESERVE
}
```

---

# 64. Fiscal Scenario

```text
struct FiscalScenario {
    id: ScenarioId
    assumptions: []ModelAssumption
    tax_changes: []TaxPolicyChange
    spending_changes: []SpendingPolicyChange
    debt_changes: []DebtPolicyChange
    macro_inputs: MacroInputSet
}
```

---

# 65. Fiscal Multiplier

```text
struct FiscalMultiplierEstimate {
    instrument: FiscalInstrument
    estimate: Decimal
    confidence_interval: Option<Interval>
    methodology: ModelRef
    horizon: Duration
    assumptions: []ModelAssumption
}
```

Không được biến:

```text
fiscal_multiplier
```

thành một constant của Axiom.

---

# 66. Government Guarantee

```text
struct SovereignGuarantee {
    id: GuaranteeId
    guarantor: GovernmentId
    beneficiary: ActorId
    underlying_obligation: ObligationRef
    maximum_exposure: Money
    currency: CurrencyId
    expiration: Option<Date>
    status: GuaranteeStatus
}
```

---

# 67. Contingent Liability

```text
struct ContingentLiability {
    id: ContingentLiabilityId
    government: GovernmentId
    source: LiabilitySource
    maximum_exposure: Money
    expected_value: Option<Money>
    probability_model: Option<ModelRef>
    status: ContingentStatus
}
```

---

# 68. Public Asset

```text
struct PublicAsset {
    id: PublicAssetId
    owner: GovernmentId
    asset_type: PublicAssetType
    valuation: Option<Money>
    location: Option<LocationRef>
    status: AssetStatus
}
```

Hỗ trợ:

```text
land
building
infrastructure
financial_asset
natural_resource
strategic_asset
intellectual_property
other
```

---

# 69. Public Liability Registry

```text
struct PublicLiabilityRegistry {
    direct_liabilities: []LiabilityRef
    contingent_liabilities: []ContingentLiabilityId
    guarantees: []GuaranteeId
    pension_obligations: []ObligationRef
}
```

---

# 70. Sovereign Wealth Boundary

Quỹ tài sản quốc gia có thể được kết nối:

```text
AXFISCAL
     ↕
AXINVEST
```

Nhưng:

```text
GovernmentBudget != SovereignWealthFund
```

và:

```text
FiscalRevenue != InvestmentReturn
```

---

# 71. State-Owned Enterprise Boundary

```text
GovernmentOwnership
    !=
GovernmentBudget
```

Doanh nghiệp nhà nước có thể có:

```text
dividend_to_government
capital_injection
guarantee
subsidy
loan
```

nhưng bản thân doanh nghiệp vẫn có financial ledger riêng.

---

# 72. Fiscal–Monetary Interface

```text
AXFISCAL ↔ AXMONETARY
```

Các interface:

```text
GovernmentCashBalance
CentralBankAccount
GovernmentSecurities
LiquidityOperations
InterestRateEnvironment
FXReserveInteraction
EmergencyLiquidity
```

Không được merge:

```text
FiscalPolicy
MonetaryPolicy
```

---

# 73. Central Bank as Fiscal Agent

Hỗ trợ abstraction:

```text
trait FiscalAgent {
    hold_government_account(...)
    settle_government_payment(...)
    conduct_debt_auction(...)
    maintain_securities_registry(...)
}
```

Việc central bank thực hiện dịch vụ tài khóa không làm nó trở thành một bộ phận semantic của `AXFISCAL`.

---

# 74. Government Securities ↔ AXMARKET

```text
AXFISCAL
    │
    │ issuance authority
    ▼
GovernmentSecurity
    │
    ▼
AXMARKET
    │
    ├── auction
    ├── trading
    ├── clearing
    └── settlement
```

---

# 75. Cross-Border Sovereign Debt

```text
AXFISCAL
    ↕
AXGLOBAL
```

Hỗ trợ:

```text
foreign_currency_debt
external_bond
multilateral_loan
bilateral_loan
cross_border_interest_payment
FX_debt_exposure
external_refinancing
```

---

# 76. Currency Risk

```text
struct SovereignFXExposure {
    currency: CurrencyId
    principal: Money
    interest_exposure: Money
    maturity: Date
}
```

Có thể kết nối:

```text
AXMONETARY
AXMARKET
AXGLOBAL
```

---

# 77. Fiscal Accounting Boundary

Mọi sự kiện tài khóa quan trọng phải có:

```text
FiscalEvent
AccountingEffect
CashEffect
LegalEffect
```

nhưng bốn lớp không được gộp.

Ví dụ:

```text
DebtIssuance
```

có thể đồng thời tạo:

```text
FiscalEvent
CashInflow
LiabilityIncrease
SecurityCreation
```

---

# 78. Fiscal Event Model

```text
struct FiscalEvent {
    id: FiscalEventId
    type: FiscalEventType
    timestamp: Timestamp
    government: GovernmentId
    actor: ActorId
    amount: Option<Money>
    authority: Option<AuthorityRef>
    accounting_ref: Option<AccountingRef>
    correlation_id: CorrelationId
}
```

---

# 79. Event Types

```text
TAX_ASSESSED
TAX_COLLECTED
TAX_REFUNDED

BUDGET_ENACTED
BUDGET_AMENDED
APPROPRIATION_CREATED
APPROPRIATION_REDUCED

COMMITMENT_CREATED
OBLIGATION_CREATED
PAYMENT_AUTHORIZED
PAYMENT_EXECUTED

TRANSFER_CREATED
SUBSIDY_GRANTED

DEBT_ISSUED
DEBT_PURCHASED
DEBT_SERVICED
DEBT_REFINANCED
DEBT_RETIRED

GUARANTEE_ISSUED
GUARANTEE_CALLED

PUBLIC_ASSET_ACQUIRED
PUBLIC_ASSET_DISPOSED
```

---

# 80. Fiscal State Machine

Mọi authoritative state transition phải:

```text
validate
→ authorize
→ persist
→ emit_event
→ reconcile
```

Không cho phép:

```text
mutate_state()
```

bỏ qua authority hoặc audit.

---

# 81. Idempotency

Các thao tác tài chính phải hỗ trợ:

```text
IdempotencyKey
```

Ví dụ:

```text
execute_public_payment(idempotency_key)
```

Hai request giống nhau không được tạo hai lần thanh toán.

---

# 82. Exactly-Once Financial Effect

Trong distributed system:

```text
network_retry
!=
financial_retry
```

Runtime phải bảo đảm semantic:

```text
one logical payment
→ one financial effect
```

ngay cả khi transport retry.

---

# 83. Reconciliation

```text
FiscalRecord
    ↔
TreasuryRecord
    ↔
BankRecord
    ↔
AXFINANCE Ledger
```

Reconciliation engine:

```text
match
detect_difference
classify_difference
resolve
audit
```

---

# 84. Fiscal Data Lineage

Mọi chỉ tiêu public finance phải có provenance:

```text
Metric
 ├── source
 ├── period
 ├── jurisdiction
 ├── methodology
 ├── revision
 ├── transformation
 └── confidence
```

---

# 85. Forecast Revision

Không overwrite lịch sử forecast.

```text
Forecast v1
Forecast v2
Forecast v3
```

Mỗi version có:

```text
created_at
model
inputs
assumptions
result
```

---

# 86. Fiscal Digital Twin

```text
struct FiscalTwin {
    government: GovernmentId
    observed_state: FiscalState
    estimated_state: FiscalState
    forecast_state: FiscalState
    simulated_state: FiscalState
}
```

Bốn trạng thái phải độc lập.

```text
Observed != Estimated
Estimated != Forecast
Forecast != Simulated
```

---

# 87. Fiscal Simulation

Simulation engine hỗ trợ:

```text
tax_change
spending_change
interest_rate_change
growth_change
inflation_change
exchange_rate_change
commodity_price_change
unemployment_change
disaster
financial_crisis
debt_refinancing_shock
```

---

# 88. Scenario Graph

```text
FiscalScenario
    ├── assumptions
    ├── policy_inputs
    ├── macro_inputs
    ├── debt_inputs
    └── outcome_paths
```

Có thể chạy:

```text
baseline
upside
downside
stress
extreme_stress
custom
```

Tên scenario không phải đánh giá chính sách.

---

# 89. Fiscal Stress Testing

Stress test:

```text
RevenueShock
SpendingShock
InterestRateShock
FXShock
GrowthShock
DebtRolloverShock
GuaranteeCallShock
NaturalDisasterShock
CommodityShock
```

Kết quả:

```text
cash_shortfall
deficit_change
debt_path
interest_burden
refinancing_need
```

---

# 90. Fiscal AI

AI trong `AXFISCAL` hỗ trợ:

```text
forecasting
anomaly_detection
reconciliation
scenario_generation
debt_analysis
cash_forecasting
tax_gap_analysis
budget_analysis
spending_analysis
policy_simulation
explanation
document_analysis
```

---

# 91. AI Authority Boundary

Mặc định:

```text
AI
    observe
    analyze
    forecast
    simulate
    explain
    recommend
```

Không mặc định:

```text
AI
    enact_budget
    change_tax_law
    issue_debt
    execute_payment
    freeze_account
    assess_penalty
    seize_asset
    approve_expenditure
```

Các thao tác này yêu cầu capability + explicit authority.

---

# 92. AI Tax Analysis

AI có thể:

```text
detect_anomaly
estimate_tax_gap
identify_missing_data
forecast_collection
compare_scenarios
```

Không được:

```text
anomaly → guilt
```

---

# 93. AI Budget Analysis

AI có thể tạo:

```text
BudgetScenario
SpendingProjection
RevenueProjection
DebtProjection
SensitivityAnalysis
```

Nhưng:

```text
AIRecommendation != GovernmentDecision
```

---

# 94. Fiscal Optimization

Có thể tối ưu:

```text
cash_management
debt_maturity
refinancing
budget_allocation
project_portfolio
```

subject to:

```text
legal_constraints
budget_constraints
liquidity_constraints
risk_constraints
policy_constraints
```

Optimization result luôn là:

```text
CandidatePlan
```

không tự động là:

```text
ApprovedPlan
```

---

# 95. Public Budget Constraint

Runtime hỗ trợ:

```text
allocated <= appropriated
committed <= available_authorization
authorized_payment <= obligation
```

với các rule đặc biệt có thể được cấu hình theo jurisdiction.

---

# 96. Fiscal Invariants

`AXFISCAL` phải enforce tối thiểu các invariant sau.

### F-01

```text
BudgetAuthority != Cash
```

### F-02

```text
Appropriation != Payment
```

### F-03

```text
TaxAssessment != TaxPayment
```

### F-04

```text
RevenueForecast != Revenue
```

### F-05

```text
Deficit != Debt
```

### F-06

```text
Borrowing != Revenue
```

### F-07

```text
DebtStock != DebtFlow
```

### F-08

```text
Expenditure != Disbursement
```

### F-09

```text
Commitment <= AuthorizedBudget
```

trừ khi framework explicitly cho phép over-commitment như một trạng thái vi phạm.

### F-10

```text
Payment <= AuthorizedObligation
```

### F-11

```text
OneLogicalPayment == OneFinancialEffect
```

### F-12

```text
EveryBudgetChangeHasAuthority
```

### F-13

```text
EveryDebtIssuanceHasIssuerAuthority
```

### F-14

```text
EveryFiscalMutationIsAuditable
```

### F-15

```text
HistoricalFiscalRecordsAreImmutable
```

### F-16

```text
ForecastVersionsAreImmutable
```

### F-17

```text
AIRecommendation != FiscalAuthority
```

### F-18

```text
RiskSignal != LegalFinding
```

### F-19

```text
Simulation != ProductionState
```

### F-20

```text
ObservedState != SimulatedState
```

### F-21

```text
FiscalPolicy != MonetaryPolicy
```

### F-22

```text
GovernmentBudget != SovereignWealthFund
```

### F-23

```text
GovernmentOwnership != GovernmentBudget
```

### F-24

```text
GovernmentGuarantee != GovernmentDebt
```

cho tới khi guarantee được gọi và trở thành nghĩa vụ thực tế.

### F-25

```text
ContingentLiability != DirectLiability
```

### F-26

```text
DebtCurrencyExposureMustBeExplicit
```

### F-27

```text
DebtMaturityMustBeExplicit
```

### F-28

```text
InterestObligationMustBeTraceableToDebt
```

### F-29

```text
EveryTaxLiabilityHasTaxType
```

### F-30

```text
EveryTaxRuleHasEffectivePeriod
```

### F-31

```text
EveryBudgetExecutionEventHasFiscalPeriod
```

### F-32

```text
EveryTransferHasSourceAndDestination
```

### F-33

```text
EveryPublicPaymentHasTreasuryOrSettlementReference
```

### F-34

```text
EveryFiscalForecastHasAssumptions
```

### F-35

```text
EverySimulationHasScenarioIdentity
```

### F-36

```text
EveryPublicFinanceMetricHasProvenance
```

### F-37

```text
EveryRevisionPreservesPreviousVersion
```

### F-38

```text
NoCrossJurisdictionMutationWithoutAuthority
```

### F-39

```text
NoImplicitCurrencyConversion
```

### F-40

```text
NoImplicitLegalAuthority
```

### F-41

```text
NoImplicitAIExecutionAuthority
```

### F-42

```text
FiscalLedgerReferenceMustRemainReconciliable
```

---

# 97. Memory Architecture

Public finance có dữ liệu rất lớn nhưng transaction semantics phải deterministic.

Hot-path structures:

```text
struct FiscalHotState {
    balance
    authorization
    commitment
    obligation
    payment_state
}
```

Dữ liệu analytics:

```text
Columnar
SoA
Compressed
MemoryMapped
```

---

# 98. Không GC trong financial hot path

Các đường:

```text
tax_collection
budget_commitment
payment_authorization
payment_execution
debt_service
reconciliation
```

không được phụ thuộc vào tracing GC.

Sử dụng:

```text
arena
pool
slab
region
preallocated queues
```

khi phù hợp.

---

# 99. Concurrency

Fiscal runtime hỗ trợ partition theo:

```text
government
jurisdiction
currency
fiscal_period
account
taxpayer
```

Nhưng các aggregate tài chính có dependency phải serialize đúng semantic.

Ví dụ:

```text
TreasuryAccount
```

có thể yêu cầu ordered event stream.

---

# 100. Distributed Fiscal Runtime

Kiến trúc:

```text
Fiscal Coordinator
       │
 ┌─────┼─────────┐
 ▼     ▼         ▼
Revenue Budget  Treasury
 │       │         │
 ▼       ▼         ▼
Tax     Expenditure Cash
 │                 │
 └────────┬────────┘
          ▼
         Debt
```

Mọi node phải có:

```text
logical_clock
event_id
correlation_id
idempotency_key
```

---

# 101. Deterministic Replay

Một fiscal event log phải có thể replay:

```text
same input
+
same rule version
+
same authority state
=
same fiscal state
```

trừ các nguồn nondeterministic được đánh dấu rõ.

---

# 102. Security Capability Model

Capabilities:

```text
fiscal.read
fiscal.analyze
fiscal.forecast
fiscal.simulate

revenue.read
revenue.write

tax.read
tax.assess
tax.collect
tax.refund
tax.admin

budget.read
budget.propose
budget.allocate
budget.amend
budget.execute

expenditure.read
expenditure.commit
expenditure.authorize

treasury.read
treasury.transfer
treasury.admin

debt.read
debt.propose
debt.issue
debt.service
debt.refinance

guarantee.read
guarantee.issue

public_asset.read
public_asset.manage

fiscal_policy.read
fiscal_policy.simulate

audit.read
admin
```

---

# 103. Capability Separation

Ví dụ:

```text
tax.read
```

không bao gồm:

```text
tax.assess
```

và:

```text
tax.assess
```

không tự động bao gồm:

```text
tax.collect
```

Tương tự:

```text
debt.read
```

không bao gồm:

```text
debt.issue
```

---

# 104. AI Capability Profile

Mặc định:

```text
AXFISCAL_AI_DEFAULT {
    fiscal.read
    fiscal.analyze
    fiscal.forecast
    fiscal.simulate
    fiscal.explain
}
```

Không có:

```text
budget.amend
tax.assess
tax.collect
treasury.transfer
debt.issue
guarantee.issue
```

nếu không được cấp riêng.

---

# 105. Audit

Audit record:

```text
struct FiscalAuditRecord {
    event_id: FiscalEventId
    actor: ActorId
    authority: AuthorityRef
    capability: Capability
    timestamp: Timestamp
    before_hash: Hash
    after_hash: Hash
    reason: Option<String>
}
```

Audit log phải append-only.

---

# 106. Privacy

Tax data có thể chứa dữ liệu cá nhân và doanh nghiệp.

Do đó:

```text
tax.read
```

không mặc định đồng nghĩa:

```text
personal_data.read_all
```

Hỗ trợ:

```text
field-level access
row-level access
jurisdiction-level access
purpose limitation
data minimization
retention policy
redaction
pseudonymization
```

---

# 107. Fiscal Data Classification

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
SENSITIVE_FINANCIAL
TAX_SECRET
NATIONAL_SECURITY_RESTRICTED
```

Classification không tự quyết định legal status; nó liên kết với `AXLAW`.

---

# 108. API

```text
fiscal.budget.create()
fiscal.budget.approve()
fiscal.budget.amend()
fiscal.budget.allocate()

fiscal.tax.register()
fiscal.tax.assess()
fiscal.tax.collect()
fiscal.tax.refund()

fiscal.expenditure.commit()
fiscal.expenditure.authorize()
fiscal.expenditure.pay()

fiscal.treasury.balance()
fiscal.treasury.forecast()

fiscal.debt.issue()
fiscal.debt.service()
fiscal.debt.refinance()

fiscal.guarantee.issue()

fiscal.simulation.run()
fiscal.forecast.run()
fiscal.reconcile()
```

---

# 109. Axiom DSL Example — Budget

```axiom
budget NationalBudget {
    government = Republic
    fiscal_year = 2030
    currency = VND

    revenue {
        tax = forecast(2_100_000_000_000_000)
        fees = forecast(120_000_000_000_000)
    }

    expenditure {
        education = 450_000_000_000_000
        healthcare = 380_000_000_000_000
        infrastructure = 600_000_000_000_000
    }
}
```

---

# 110. Tax Rule DSL

```axiom
tax CorporateIncome {
    jurisdiction = Republic
    base = taxable_profit

    brackets {
        0..1_000_000_000 => 0.10
        1_000_000_001..10_000_000_000 => 0.15
        above 10_000_000_000 => 0.20
    }
}
```

Compiler không giả định đây là luật thực tế của bất kỳ quốc gia nào.

---

# 111. Budget Execution DSL

```axiom
budget.commit {
    appropriation = Infrastructure.ProgramA
    amount = 50_000_000_000
    contract = Contract.42
}
```

Sau đó:

```axiom
budget.authorize_payment {
    obligation = Obligation.42
    amount = 20_000_000_000
}
```

và:

```axiom
treasury.pay {
    authorization = PaymentAuthorization.42
}
```

---

# 112. Debt DSL

```axiom
debt.issue {
    issuer = Republic
    instrument = TreasuryBond
    amount = 100_000_000_000_000
    currency = VND
    maturity = 2036-09-24
    coupon = 0.06
}
```

Execution trên thị trường:

```text
AXFISCAL
    →
AXMARKET
```

---

# 113. Fiscal Simulation DSL

```axiom
scenario TaxReform {
    tax_rate.corporate += 0.02
    public_investment += 100_000_000_000_000
    horizon = 10y
}

simulate TaxReform
    outputs {
        revenue
        deficit
        debt
        interest_burden
        growth
    }
}
```

Kết quả là simulation.

Không thay đổi production state.

---

# 114. Debt Sustainability DSL

```axiom
analyze debt_sustainability {
    horizon = 20y
    scenarios = [
        baseline,
        growth_down,
        rate_up,
        fx_shock,
        rollover_stress
    ]
}
```

---

# 115. AI Fiscal Analyst

```axiom
agent FiscalAnalyst {
    capabilities {
        fiscal.read
        fiscal.analyze
        fiscal.forecast
        fiscal.simulate
        fiscal.explain
    }

    deny {
        budget.amend
        tax.assess
        tax.collect
        treasury.transfer
        debt.issue
    }
}
```

---

# 116. AI Explainability

Một AI fiscal result phải có:

```text
result
assumptions
inputs
model
model_version
uncertainty
data_sources
scenario
timestamp
limitations
```

Không cho phép:

```text
"debt will be X"
```

nếu model chỉ cung cấp:

```text
forecast range
```

---

# 117. Fiscal Analytics

Built-in analytical dimensions:

```text
revenue/GDP
tax/GDP
expenditure/GDP
deficit/GDP
primary_balance/GDP
debt/GDP
interest/revenue
interest/expenditure
capital_expenditure/share
tax_compliance
tax_gap
cash_buffer
maturity_profile
FX_debt_share
```

Các ratio phải lưu:

```text
numerator
denominator
period
population
methodology
```

---

# 118. Fiscal Reporting

Hỗ trợ:

```text
monthly
quarterly
annual
multi-year
consolidated
agency
jurisdiction
program
function
economic_category
funding_source
currency
```

---

# 119. Consolidation

Khi tổng hợp nhiều cấp chính quyền:

```text
Central Government
      +
Regional Government
      +
Municipal Government
```

phải loại bỏ internal transfers theo consolidation rules.

Không được cộng đơn giản mọi transaction.

---

# 120. Double Counting Prevention

Ví dụ:

```text
Central → Province transfer
```

không được trở thành:

```text
national revenue
+
national expenditure
+
province revenue
```

mà phải có consolidation semantics.

---

# 121. Fiscal Data Cube

Native analytic representation:

```text
FiscalCube {
    period
    jurisdiction
    government
    program
    function
    economic_category
    revenue_type
    expenditure_type
    currency
    funding_source
}
```

Có thể chạy:

```text
aggregate
filter
group
pivot
window
drilldown
```

---

# 122. Performance

Mục tiêu:

```text
≥ 10M lightweight fiscal events/sec
```

trên hệ thống phân vùng phù hợp.

Analytics:

```text
billions of fiscal records
```

Simulation:

```text
millions of scenarios
```

có thể chạy song song.

---

# 123. GPU

GPU phù hợp cho:

```text
scenario simulation
Monte Carlo
debt optimization
portfolio analysis
tax anomaly detection
large-scale forecasting
graph analytics
```

Không bắt buộc GPU cho:

```text
single fiscal transaction
payment authorization
ledger reference
```

---

# 124. Zero-Copy

Dữ liệu:

```text
FiscalEvent
DebtSnapshot
BudgetSnapshot
FiscalCube
ScenarioState
```

nên hỗ trợ:

```text
memory mapping
zero-copy serialization
columnar buffers
shared memory
```

khi an toàn.

---

# 125. Runtime Profiles

```text
AXFISCAL_NONE
AXFISCAL_CORE

AXFISCAL_REVENUE
AXFISCAL_TAX
AXFISCAL_BUDGET
AXFISCAL_EXPENDITURE

AXFISCAL_TREASURY
AXFISCAL_CASH

AXFISCAL_TRANSFER
AXFISCAL_INVESTMENT

AXFISCAL_DEBT
AXFISCAL_SECURITIES
AXFISCAL_GUARANTEE

AXFISCAL_POLICY
AXFISCAL_RISK
AXFISCAL_ANALYTICS

AXFISCAL_FORECAST
AXFISCAL_SIMULATION
AXFISCAL_DIGITAL_TWIN

AXFISCAL_AI
AXFISCAL_DISTRIBUTED
AXFISCAL_GPU

AXFISCAL_WASM
AXFISCAL_MOBILE
AXFISCAL_REALTIME

AXFISCAL_FULL
```

---

# 126. Error Model

```text
BudgetError
TaxError
RevenueError
AppropriationError
CommitmentError
ObligationError
PaymentError
TreasuryError
DebtError
GuaranteeError
ReconciliationError
AuthorizationError
JurisdictionError
CurrencyError
ForecastError
SimulationError
AuditError
```

Ví dụ:

```text
ErrBudgetExceeded
ErrUnauthorizedFiscalAction
ErrDuplicatePayment
ErrInsufficientAppropriation
ErrInvalidTaxRule
ErrDebtLimitExceeded
ErrCurrencyMismatch
ErrStaleFiscalState
ErrReconciliationMismatch
ErrMissingAuthority
```

---

# 127. Recovery

Mọi financial mutation phải hỗ trợ:

```text
checkpoint
journal
replay
reconciliation
recovery
```

Không rollback bằng cách xóa lịch sử.

Thay vào đó:

```text
CorrectionEvent
```

được tạo.

---

# 128. Disaster Recovery

Mục tiêu:

```text
RPO ≈ 0
RTO configurable
```

đối với authoritative fiscal transaction log.

Backup phải giữ:

```text
budget versions
tax rules
debt states
treasury states
audit records
authority versions
model versions
```

---

# 129. Versioning

Các object quan trọng đều versioned:

```text
TaxRuleVersion
BudgetVersion
AppropriationVersion
DebtVersion
FiscalPolicyVersion
ForecastVersion
SimulationModelVersion
```

---

# 130. Legal Effective Time

Một rule có:

```text
effective_from
effective_to
```

và có thể khác:

```text
publication_time
approval_time
enforcement_time
```

Điều này đặc biệt quan trọng với tax rules.

---

# 131. Temporal Query

Runtime hỗ trợ:

```text
state_at(time)
rule_at(time)
budget_at(time)
debt_at(time)
tax_rule_at(time)
```

để tái hiện historical state.

---

# 132. Multi-Currency

Mọi monetary value phải chứa:

```text
amount
currency
```

Không cho phép:

```text
Money(100)
+
Money(200)
```

nếu currency không tương thích.

FX conversion phải explicit:

```text
convert(amount, rate, timestamp)
```

---

# 133. FX Source

Khi cần quy đổi:

```text
FXRateSource
```

phải lưu:

```text
provider
timestamp
rate
quote_currency
base_currency
method
```

---

# 134. Fiscal–Global Integration

```text
AXFISCAL
   ↕
AXGLOBAL
```

Các flow:

```text
foreign debt issuance
external loan
foreign interest payment
aid
international transfer
customs revenue
export/import tax
FX debt exposure
```

---

# 135. Fiscal–Banking Integration

```text
AXFISCAL
   ↕
AXBANKING
```

Hỗ trợ:

```text
government account
commercial bank collection
tax payment
government payment
bank financing
government deposits
```

---

# 136. Fiscal–Market Integration

```text
AXFISCAL
   ↕
AXMARKET
```

Hỗ trợ:

```text
bond issuance
auction
secondary trading
repo
yield curve
market valuation
settlement
```

---

# 137. Fiscal–Finance Integration

```text
AXFISCAL
   ↕
AXFINANCE
```

`AXFISCAL` tạo:

```text
fiscal events
```

`AXFINANCE` tạo:

```text
authoritative financial records
```

Reconciliation bắt buộc.

---

# 138. Government Financial Graph

```text
Government
 ├── Revenue
 ├── Taxpayer
 ├── Budget
 ├── Agency
 ├── Program
 ├── Expenditure
 ├── Treasury
 ├── Debt
 ├── Guarantee
 ├── PublicAsset
 └── Transfer
```

Graph edges:

```text
funds
owes
collects
allocates
commits
pays
borrows
guarantees
transfers
owns
```

---

# 139. Fiscal Contagion Model

Mô phỏng:

```text
Revenue Shock
    ↓
Budget Deficit
    ↓
Borrowing
    ↓
Debt
    ↓
Interest Cost
    ↓
Future Budget
```

và:

```text
Interest Rate Shock
    ↓
Debt Service
    ↓
Fiscal Balance
    ↓
Borrowing Requirement
```

---

# 140. Civilization Fiscal Loop

```text
ECONOMIC ACTIVITY
        ↓
TAX / PUBLIC REVENUE
        ↓
PUBLIC BUDGET
        ↓
PUBLIC EXPENDITURE
        ↓
INFRASTRUCTURE / SERVICES
        ↓
PRODUCTIVITY / WELFARE / ECONOMIC ACTIVITY
```

Debt loop:

```text
FISCAL DEFICIT
      ↓
BORROWING
      ↓
SOVEREIGN DEBT
      ↓
INTEREST / DEBT SERVICE
      ↓
FUTURE BUDGET
      ↓
FISCAL POLICY
```

---

# 141. Public Finance Knowledge Graph

Các entity phải liên kết:

```text
Taxpayer
TaxRule
TaxLiability
Revenue
Budget
Appropriation
Program
Commitment
Obligation
Payment
TreasuryAccount
Debt
Bond
Guarantee
PublicAsset
FiscalPolicy
Scenario
Forecast
```

Graph traversal phải trả được:

```text
Where did this public payment originate?
Which appropriation funded it?
Which budget authorized it?
Which legal authority enabled it?
Which treasury account settled it?
Which accounting record represents it?
```

---

# 142. End-to-End Example

```text
Government enacts budget
        ↓
Appropriation
        ↓
Agency allocation
        ↓
Procurement contract
        ↓
Commitment
        ↓
Obligation
        ↓
Payment authorization
        ↓
Treasury payment
        ↓
Bank settlement
        ↓
AXFINANCE accounting
        ↓
Audit trail
```

Tax side:

```text
Economic activity
        ↓
Taxable event
        ↓
Tax computation
        ↓
Assessment
        ↓
Filing
        ↓
Liability
        ↓
Collection
        ↓
Treasury
        ↓
AXFINANCE
```

Debt side:

```text
Budget deficit
      ↓
Financing requirement
      ↓
Debt issuance decision
      ↓
Government security
      ↓
AXMARKET
      ↓
Auction / execution
      ↓
Settlement
      ↓
Treasury
      ↓
Debt liability
      ↓
AXFINANCE
```

---

# 143. Test Architecture

`AXFISCAL` phải có test suites:

```text
tax/
budget/
appropriation/
expenditure/
treasury/
cash/
transfer/
investment/
debt/
guarantee/
asset/
forecast/
simulation/
reconciliation/
security/
audit/
distributed/
recovery/
performance/
```

---

# 144. Property-Based Testing

Ví dụ:

```text
payment <= obligation
```

phải được test trên hàng triệu input combinations.

Debt:

```text
outstanding_principal >= 0
```

trừ các instrument có short/negative semantic được explicit model hóa.

Currency:

```text
currency_conversion_is_explicit
```

Idempotency:

```text
retry(payment) == one_effect
```

---

# 145. Deterministic Test

Cùng:

```text
tax_rule_version
taxpayer_state
tax_period
inputs
```

phải tạo:

```text
same_tax_assessment
```

---

# 146. Security Tests

Phải test:

```text
unauthorized_budget_change
unauthorized_tax_assessment
unauthorized_payment
unauthorized_debt_issue
cross_jurisdiction_access
privilege_escalation
audit_tampering
replay_attack
duplicate_payment
```

---

# 147. Simulation Tests

Kiểm tra:

```text
simulation_does_not_modify_live_state
```

và:

```text
simulation_reproducibility
```

---

# 148. Target Test Scale

Mục tiêu ban đầu:

```text
≥ 20,000 automated tests
≥ 2,000 architecture invariants
≥ 1,000 property-based tests
≥ 500 distributed consistency tests
≥ 500 recovery tests
≥ 500 security tests
```

Các con số này là engineering targets, không phải yêu cầu runtime tối thiểu.

---

# 149. Observability

Metrics:

```text
tax_assessment_rate
tax_collection_rate
budget_execution_rate
appropriation_utilization
commitment_rate
obligation_rate
payment_latency
treasury_balance
cash_buffer
debt_service
debt_maturity
refinancing_need
forecast_error
reconciliation_error
```

---

# 150. Trace

Một payment trace:

```text
Budget
 → Appropriation
 → Commitment
 → Obligation
 → Authorization
 → Treasury
 → Bank
 → Settlement
 → Accounting
```

phải trace được end-to-end.

---

# 151. Fiscal Control Plane

```text
FiscalControlPlane
 ├── policy registry
 ├── tax rule registry
 ├── budget registry
 ├── authority registry
 ├── debt registry
 ├── treasury registry
 ├── model registry
 └── audit registry
```

---

# 152. Fiscal Data Plane

```text
FiscalDataPlane
 ├── transactions
 ├── balances
 ├── obligations
 ├── payments
 ├── debt schedules
 └── event streams
```

Tách:

```text
control plane
```

khỏi:

```text
data plane
```

để tăng khả năng bảo mật và vận hành.

---

# 153. Governance Boundary

`AXFISCAL` không tự quyết định:

```text
what government should tax
what government should spend
which policy is morally preferable
which citizen deserves funding
```

Nó cung cấp:

```text
mechanisms
models
constraints
calculations
execution primitives
auditability
simulation
```

Quyết định chính sách thuộc authority layer.

---

# 154. Human Oversight

Các thao tác có tác động lớn phải hỗ trợ:

```text
review
approval
dual_control
multi_signature
separation_of_duties
```

Ví dụ:

```text
large_payment
debt_issuance
budget_amendment
tax_rule_change
guarantee_issue
```

---

# 155. Separation of Duties

Có thể cấu hình:

```text
PolicyMaker
Approver
TreasuryOfficer
Accountant
Auditor
TaxOfficer
DebtManager
SystemOperator
AIAnalyst
```

Một role không mặc định có toàn quyền.

---

# 156. Multi-Signature Fiscal Action

```text
struct FiscalApproval {
    action: FiscalActionId
    required_signatures: UInt32
    signatures: []Signature
}
```

Action chỉ executable khi:

```text
signatures >= required_signatures
```

---

# 157. Public Transparency Interface

Có thể publish:

```text
budget
execution
revenue
expenditure
debt
fiscal_reports
```

theo public-data policy.

Nhưng public transparency không có nghĩa expose:

```text
private taxpayer information
```

---

# 158. Open Fiscal Data

Export:

```text
CSV
JSON
Parquet
Arrow
Axiom Binary
```

và metadata:

```text
schema_version
source
period
revision
methodology
```

---

# 159. Native Serialization

```text
FiscalEvent → AXBIN
BudgetSnapshot → AXBIN
DebtSnapshot → AXBIN
FiscalCube → Arrow-compatible representation
```

Không bắt buộc JSON trong hot path.

---

# 160. Compiler Integration

Compiler có thể optimize fiscal DSL:

```text
static budget constraints
constant tax rules
currency compatibility
capability checks
schema validation
```

Ví dụ:

```text
treasury.pay(...)
```

có thể compile-time reject nếu capability không tồn tại trong agent profile.

---

# 161. Static Safety

Axiom compiler nên phát hiện:

```text
missing_currency
missing_authority
missing_fiscal_period
missing_budget
missing_appropriation
missing_idempotency
unauthorized_capability
```

trước runtime khi có thể.

---

# 162. Compile-Time Fiscal Type System

Có thể phân biệt:

```text
type BudgetMoney
type TreasuryMoney
type DebtPrincipal
type TaxLiabilityAmount
type AppropriationAmount
type PaymentAmount
```

Không nhất thiết tất cả đều là primitive `Money`.

Điều này giảm lỗi semantic.

---

# 163. Example

Không cho phép:

```axiom
let x: Revenue = debt_issued
```

nếu semantic type không tương thích.

Tương tự:

```axiom
let x: AppropriationAmount = TreasuryBalance
```

phải explicit conversion.

---

# 164. Fiscal Capability Type

Authority có thể trở thành type-level capability:

```axiom
fn execute_payment(
    auth: TreasuryPaymentAuthority,
    payment: PaymentAuthorization
)
```

Không có authority:

```text
compile/runtime rejection
```

---

# 165. Formal Model

Một government fiscal state:

```text
F_t =
{
    revenue_t,
    budget_t,
    expenditure_t,
    cash_t,
    debt_t,
    guarantees_t,
    assets_t
}
```

Transition:

```text
F_(t+1) = Transition(F_t, Event_t, Rules_t, Authority_t)
```

---

# 166. State Transition Correctness

Mỗi transition phải satisfy:

```text
Preconditions
→ Authorization
→ State Transition
→ Accounting Link
→ Event Emission
→ Postconditions
```

---

# 167. Fiscal Model vs Accounting Model

```text
AXFISCAL:
    "what fiscal event occurred?"

AXFINANCE:
    "what is the authoritative financial accounting consequence?"
```

Đây là boundary bắt buộc.

---

# 168. Final Module Contract

```text
AXGOV
=
PUBLIC AUTHORITY / ADMINISTRATION

AXLAW
=
LEGAL AUTHORITY

AXFISCAL
=
PUBLIC REVENUE
+
TAXATION
+
BUDGET
+
PUBLIC EXPENDITURE
+
TREASURY
+
SOVEREIGN DEBT
+
FISCAL POLICY
+
PUBLIC FINANCE SIMULATION

AXFINANCE
=
ACCOUNTING / FINANCIAL TRUTH

AXMONETARY
=
MONEY / CENTRAL BANK / MONETARY POLICY

AXBANKING
=
BANKING / CREDIT / BANK ACCOUNTS

AXMARKET
=
MARKET EXECUTION / TRADING / CLEARING / SETTLEMENT

AXGLOBAL
=
CROSS-BORDER ECONOMIC FLOWS
```

---

# 169. Civilization Financial Stack

```text
                    AXGOV
                      │
                      ▼
                  AXFISCAL
                 /    │    \
                /     │     \
               ▼      ▼      ▼
        AXMONETARY AXBANKING AXMARKET
               \      │      /
                \     │     /
                 ▼    ▼    ▼
                   AXFINANCE
                       │
                       ▼
                   AXGLOBAL
```

---

# 170. Civilization-Scale Economic Loop

```text
HOUSEHOLDS
    ↓
LABOR / PRODUCTION
    ↓
INCOME
    ↓
CONSUMPTION / INVESTMENT
    ↓
ECONOMIC ACTIVITY
    ↓
TAX REVENUE
    ↓
PUBLIC BUDGET
    ↓
PUBLIC EXPENDITURE
    ↓
INFRASTRUCTURE / EDUCATION / HEALTH / SERVICES
    ↓
PRODUCTIVITY / HUMAN CAPITAL
    ↓
ECONOMIC ACTIVITY
```

Financial loop:

```text
FISCAL DEFICIT
    ↓
GOVERNMENT BORROWING
    ↓
SOVEREIGN DEBT
    ↓
DEBT SERVICE
    ↓
FUTURE FISCAL CAPACITY
```

Monetary interaction:

```text
FISCAL POLICY
      ↕
MONEY / CREDIT CONDITIONS
      ↕
MONETARY POLICY
      ↕
ECONOMIC ACTIVITY
```

---

# 171. Integration Contract With Previous Modules

```text
AX671
  ↓
economic activity
  ↓
AX686
  ↓
commerce
  ↓
AX688
  ↓
labor/income
  ↓
AXFISCAL
  ↓
tax/revenue
  ↓
public budget
  ↓
AX683 / AX681 / AX674 / AX673 / AX682
  ↓
public infrastructure/services
  ↓
AX671
```

Financial integration:

```text
AXFISCAL
   ↕
AXFINANCE
   ↕
AXBANKING
   ↕
AXMONETARY
   ↕
AXMARKET
   ↕
AXGLOBAL
```

---

# 172. Acceptance Criteria

BOOTSTRAP-696 được xem là hoàn thành khi:

1. Có semantic model hoàn chỉnh cho public finance.
2. Tax lifecycle được định nghĩa.
3. Revenue lifecycle được định nghĩa.
4. Budget lifecycle được định nghĩa.
5. Appropriation được tách khỏi payment.
6. Commitment/obligation/payment được tách.
7. Treasury model được định nghĩa.
8. Cash management được định nghĩa.
9. Intergovernmental transfer được định nghĩa.
10. Public expenditure được định nghĩa.
11. Public investment được định nghĩa.
12. Sovereign debt được định nghĩa.
13. Debt service/refinancing được định nghĩa.
14. Government securities integration với `AXMARKET`.
15. Fiscal accounting integration với `AXFINANCE`.
16. Monetary integration với `AXMONETARY`.
17. Banking integration với `AXBANKING`.
18. Cross-border integration với `AXGLOBAL`.
19. Guarantee và contingent liability được mô hình hóa.
20. Public asset registry được mô hình hóa.
21. Fiscal forecast được version hóa.
22. Fiscal simulation được tách khỏi live state.
23. Fiscal digital twin được định nghĩa.
24. AI authority boundary được định nghĩa.
25. Capability/security model được định nghĩa.
26. Audit trail được định nghĩa.
27. Reconciliation được định nghĩa.
28. Distributed/idempotent execution được định nghĩa.
29. Deterministic replay được định nghĩa.
30. Multi-currency được hỗ trợ.
31. Historical/temporal queries được hỗ trợ.
32. Fiscal data lineage được hỗ trợ.
33. Static semantic checks được xác định.
34. Runtime profiles được xác định.
35. Error/recovery model được xác định.
36. Performance architecture được xác định.
37. GPU acceleration boundary được xác định.
38. ≥40 architectural invariants được xác định.
39. ≥20,000 automated-test target được xác định.
40. End-to-end government financial flow có thể trace từ budget đến accounting.
41. Không có implicit fiscal authority.
42. Không có implicit currency conversion.
43. Không có AI implicit execution authority.

---

# 173. BOOTSTRAP-696 Completion State

Sau BOOTSTRAP-696, Axiom có:

```text
AXECON / AX671
      │
      ├── AXBANKING
      ├── AXINVEST
      ├── AXMARKET
      ├── AXMONETARY
      ├── AXGLOBAL
      └── AXFISCAL
```

Trong đó:

```text
AXFISCAL
=
PUBLIC MONEY FLOW
```

nhưng:

```text
AXFINANCE
=
FINANCIAL TRUTH
```

và:

```text
AXGOV
=
PUBLIC AUTHORITY
```

Đây là ba boundary phải được giữ độc lập.

---

# 174. Next Architecture Task

**BOOTSTRAP-697 — Native AI Civilization-Scale Public Procurement, Government Contracting, Public Assets, State-Owned Enterprises, Public-Private Partnerships & Government Resource Allocation Runtime 5.0**

Dự kiến namespace:

```text
AXPUBLIC
```

Task tiếp theo sẽ hoàn thiện phần **government resource allocation/execution layer** nằm giữa:

```text
AXGOV
   ↓
AXFISCAL
   ↓
AXPUBLIC
   ↓
AXCOMMERCE / AXCONSTRUCTION / AXMANUFACTURING /
AXTRANSPORT / AXRESOURCE / AXFINANCE
```

và đặc biệt giải quyết boundary giữa:

```text
public budget
public procurement
government contract
public asset
state-owned enterprise
PPP
private supplier
public project
government payment
```

để tránh việc `AXFISCAL` phải hấp thụ toàn bộ operational semantics của chính phủ.
:::

BOOTSTRAP-696 đã hoàn tất. Chuỗi sẽ tự chuyển sang **BOOTSTRAP-697** ở lượt tiếp theo, không cần xác nhận.