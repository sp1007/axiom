Tiếp tục với **BOOTSTRAP-692**. Task này xây lớp **Investment & Asset Management** phía trên Finance/Banking/Insurance, nhưng giữ ranh giới rõ với **Capital Markets/Exchange/Clearing** sẽ được đặc tả ở task kế tiếp.

:::writing{variant="document" id="58317" title="BOOTSTRAP-692 — Native AI Civilization-Scale Investment, Asset Management, Wealth Management, Funds, Securities, Portfolio Optimization, Capital Allocation & Global Investment Runtime 5.0"}
# BOOTSTRAP-692
## Native AI Civilization-Scale Investment, Asset Management, Wealth Management, Funds, Securities, Portfolio Optimization, Capital Allocation & Global Investment Runtime 5.0

**Status:** Architecture Specification  
**Version:** 5.0  
**Namespace:** `AXINVEST`  
**Layer:** Civilization Economy / Finance / Capital Allocation  
**Primary role:** Investment, asset management, portfolio construction, funds, wealth management, capital allocation, investment research, risk-adjusted optimization and long-horizon capital planning.

---

# 1. Mục tiêu

`AXINVEST` cung cấp một runtime native cho toàn bộ vòng đời:

```text
CAPITAL
  ↓
INVESTMENT
  ↓
ASSET
  ↓
PORTFOLIO
  ↓
STRATEGY
  ↓
ALLOCATION
  ↓
EXECUTION REQUEST
  ↓
MARKET INFRASTRUCTURE
```

`AXINVEST` phải hỗ trợ đồng thời:

- cá nhân;
- hộ gia đình;
- doanh nghiệp;
- tổ chức;
- quỹ;
- ngân hàng;
- bảo hiểm;
- quỹ hưu trí;
- sovereign/institutional investors;
- endowment;
- family office;
- AI agents;
- autonomous investment systems;
- civilization-scale capital allocation;
- simulation và digital twin.

Mục tiêu không phải tạo một ứng dụng đầu tư riêng lẻ mà là xây dựng **native investment substrate** cho Axiom.

---

# 2. Vị trí kiến trúc

```text
AXRESOURCE
AXAGRI
AXMANUFACTURING
AXCONSTRUCTION
AXHOUSING
AXTRANSPORT
AXCOMMERCE
AXLABOR
        │
        ▼
AXFINANCE
        │
        ├── AXBANKING
        ├── AXINSURANCE
        │
        ▼
AXINVEST
        │
        ▼
AXCAPITAL-MARKETS
        │
        ├── EXCHANGE
        ├── BROKER
        ├── ORDER BOOK
        ├── CLEARING
        └── SETTLEMENT
```

`AXINVEST` quyết định:

> **vốn nên được phân bổ vào đâu, theo chiến lược nào, với rủi ro nào và trong khoảng thời gian nào.**

`AXCAPITAL-MARKETS` quyết định:

> **giao dịch đó được đưa vào thị trường, khớp lệnh, bù trừ và thanh toán như thế nào.**

---

# 3. Nguyên tắc nền tảng

## 3.1 Investment ≠ Trading

```text
Investment
    = capital allocation decision

Trading
    = market execution activity
```

Một investment decision có thể tạo ra nhiều trading actions.

---

# 4. Investment ≠ Asset Ownership

Một hệ thống có thể:

```text
recommend(asset)
```

mà chưa:

```text
own(asset)
```

Ownership phải được xác nhận bởi authoritative financial/custody records.

---

# 5. Return ≠ Profit

```text
Return
    = performance measure

Profit
    = accounting/economic result
```

Không được tự động đồng nhất hai khái niệm.

---

# 6. Forecast ≠ Fact

Mọi output dự báo phải giữ provenance:

```text
Observed
Estimated
Forecast
Predicted
Scenario
Simulated
Stress
Optimized
```

Không được ghi đè:

```text
Observed
```

bằng:

```text
Predicted
```

---

# 7. Recommendation ≠ Decision

AI có thể tạo:

```text
InvestmentRecommendation
```

nhưng không mặc định có quyền:

```text
ExecuteInvestment
```

Execution phải yêu cầu capability tương ứng.

---

# 8. Optimization ≠ Truth

Một portfolio được tối ưu theo objective A không có nghĩa nó tối ưu theo mọi objective.

Ví dụ:

```text
maximize_return
```

khác:

```text
maximize_sharpe
```

khác:

```text
minimize_drawdown
```

khác:

```text
minimize_tail_risk
```

---

# 9. Risk ≠ Loss

```text
Risk
    = uncertainty about future outcomes

Loss
    = realized negative outcome
```

---

# 10. Market Value ≠ Fundamental Value

Runtime phải cho phép tồn tại đồng thời:

```text
MarketPrice
EstimatedFairValue
BookValue
LiquidationValue
ReplacementValue
IntrinsicValue
ScenarioValue
```

---

# 11. Core Entity Model

Các thực thể nền tảng:

```text
Investor
InvestorAccount
InvestmentMandate
InvestmentObjective
InvestmentConstraint

Asset
Security
Instrument
Position
Holding

Portfolio
PortfolioSleeve
PortfolioStrategy
PortfolioPolicy

Fund
FundShare
FundClass
FundNAV

AssetClass
Sector
Industry
Geography
Currency

Price
Valuation
Return
Benchmark

RiskModel
RiskMeasure
RiskFactor
Exposure

Allocation
TargetAllocation
ActualAllocation

OrderIntent
ExecutionInstruction
TradeReference

InvestmentDecision
InvestmentRecommendation

ResearchDocument
ResearchSignal
InvestmentThesis

Scenario
StressScenario
Simulation

PerformanceReport
AttributionReport

Fee
Expense
TaxReference

LiquidityProfile
CapitalCommitment
CashFlow

RebalancePlan
OptimizationProblem
OptimizationResult
```

---

# 12. Investor

```axiom
struct Investor {
    id: InvestorId
    kind: InvestorKind
    domicile: Jurisdiction
    base_currency: Currency
    objectives: InvestmentObjectiveSet
    constraints: InvestmentConstraintSet
}
```

`InvestorKind`:

```text
Individual
Household
Corporation
Institution
Fund
Pension
Insurance
Endowment
FamilyOffice
Sovereign
Trust
Foundation
AIManagedAccount
```

---

# 13. Investment Account

```axiom
struct InvestmentAccount {
    id: AccountId
    owner: InvestorRef
    custodian: CustodianRef?
    currency: Currency
    status: AccountStatus
}
```

Account ownership và custody phải được tách biệt.

---

# 14. Investment Mandate

Mandate mô tả phạm vi mà investment manager/agent được phép thực hiện.

```axiom
struct InvestmentMandate {
    id: MandateId
    investor: InvestorRef
    objectives: ObjectiveSet
    constraints: ConstraintSet
    permitted_assets: AssetClassSet
    max_risk: RiskLimit?
    liquidity_requirement: LiquidityRequirement?
    authority: InvestmentAuthority
}
```

---

# 15. Investment Objective

Các objective chuẩn:

```text
CapitalPreservation
IncomeGeneration
Growth
TotalReturn
Liquidity
InflationProtection
RetirementFunding
LiabilityMatching
StrategicReserve
Diversification
RiskReduction
MissionAligned
```

Một mandate có thể có nhiều objective.

---

# 16. Objective Function

Objective phải biểu diễn được bằng function:

```axiom
objective maximize_return
subject_to
    volatility <= 0.12
    drawdown <= 0.20
    equity_weight <= 0.70
```

---

# 17. Investment Constraint

Các constraint:

```text
MinWeight
MaxWeight
MinLiquidity
MaxLeverage
MaxDrawdown
MaxVolatility
MaxConcentration
MaxIssuerExposure
MaxSectorExposure
MaxCountryExposure
MaxCurrencyExposure
MaxDuration
MinQuality
AllowedAsset
ForbiddenAsset
TaxConstraint
ESGConstraint
MandateConstraint
RegulatoryConstraint
```

---

# 18. Asset

`Asset` là abstraction tổng quát.

```axiom
struct Asset {
    id: AssetId
    class: AssetClass
    currency: Currency
    jurisdiction: Jurisdiction?
}
```

---

# 19. Security

Security là financial instrument có thể được sở hữu/giao dịch theo market infrastructure.

Ví dụ:

```text
Equity
Bond
ETF
FundShare
REIT
MoneyMarketInstrument
DerivativeReference
StructuredProduct
```

---

# 20. Asset Class

Chuẩn hóa:

```text
Cash
FixedIncome
Equity
Commodity
RealEstate
Infrastructure
PrivateEquity
VentureCapital
PrivateCredit
PublicCredit
DigitalAsset
Fund
Derivative
Alternative
Collectible
Other
```

---

# 21. Asset Class ≠ Instrument

Ví dụ:

```text
AssetClass = Equity
Instrument = ACME.CommonShare
```

---

# 22. Position

```axiom
struct Position {
    account: AccountRef
    asset: AssetRef
    quantity: Decimal
    cost_basis: Money
    market_value: Money
    as_of: Timestamp
}
```

---

# 23. Holding

`Holding` biểu diễn quyền sở hữu/custody state.

```text
Position
    = portfolio representation

Holding
    = ownership/custody representation
```

---

# 24. Portfolio

```axiom
struct Portfolio {
    id: PortfolioId
    owner: InvestorRef
    mandate: MandateRef
    base_currency: Currency
    sleeves: PortfolioSleeveSet
}
```

---

# 25. Portfolio Sleeve

Cho phép chia portfolio thành:

```text
Core
Satellite
Income
Growth
Liquidity
Hedge
PrivateMarkets
RealAssets
StrategicReserve
```

---

# 26. Portfolio Strategy

Strategy định nghĩa logic allocation.

```axiom
strategy BalancedGrowth {
    target:
        Equity = 60%
        FixedIncome = 30%
        Cash = 10%

    rebalance:
        threshold = 5%
}
```

---

# 27. Strategic Asset Allocation

SAA là allocation dài hạn.

```text
StrategicTarget
    ↓
Portfolio
```

---

# 28. Tactical Asset Allocation

TAA cho phép deviation có kiểm soát:

```text
Strategic Equity = 60%

Tactical range:
    50% .. 70%
```

---

# 29. Dynamic Allocation

Cho phép target thay đổi theo state:

```axiom
if inflation > threshold {
    increase(real_assets)
}
```

Nhưng output vẫn là:

```text
AllocationRecommendation
```

cho tới khi execution authority được cấp.

---

# 30. Rebalancing

Rebalance engine:

```text
observe
→ calculate drift
→ evaluate constraints
→ generate plan
→ estimate costs
→ validate
→ produce execution instructions
```

---

# 31. Rebalance Trigger

```text
Calendar
Threshold
Risk
CashFlow
Tax
Liability
MarketEvent
MandateChange
Manual
AI
```

---

# 32. Rebalance Cost

Optimization phải tính:

```text
TradingCost
SpreadCost
MarketImpact
TaxCost
ExitCost
LiquidityCost
OperationalCost
```

---

# 33. Portfolio Optimization

Native optimization engine hỗ trợ:

```text
MeanVariance
BlackLitterman
RiskParity
MinimumVariance
MaximumDiversification
CVaR
RobustOptimization
GoalBasedOptimization
LiabilityDriven
FactorOptimization
ConstraintProgramming
MultiObjective
```

---

# 34. Optimization Problem

```axiom
optimize portfolio {
    maximize:
        expected_return

    minimize:
        volatility

    subject_to:
        equity <= 70%
        cash >= 5%
        issuer_exposure <= 10%
}
```

---

# 35. Multi-Objective Optimization

Cho phép:

```text
maximize(return)
minimize(risk)
minimize(cost)
maximize(liquidity)
```

với explicit weighting hoặc Pareto frontier.

Không được tự động chọn một điểm Pareto frontier nếu mandate chưa chỉ định policy.

---

# 36. Robust Optimization

Optimization phải hỗ trợ uncertainty:

```text
expected_return ∈ interval
volatility ∈ interval
correlation ∈ interval
```

---

# 37. Scenario Optimization

```axiom
optimize portfolio
under {
    baseline
    recession
    inflation
    deflation
    liquidity_crisis
}
```

---

# 38. Risk Model

Risk model gồm:

```text
MarketRisk
CreditRisk
LiquidityRisk
CurrencyRisk
InterestRateRisk
InflationRisk
ConcentrationRisk
CounterpartyRisk
OperationalRisk
ModelRisk
TailRisk
PoliticalRiskReference
ClimateRiskReference
```

Các risk factor phải có provenance.

---

# 39. Risk Exposure

```axiom
struct Exposure {
    portfolio: PortfolioRef
    factor: RiskFactorRef
    amount: Decimal
    unit: ExposureUnit
}
```

---

# 40. Concentration

Có thể tính theo:

```text
Issuer
Asset
Sector
Industry
Country
Currency
Counterparty
Maturity
LiquidityBucket
RiskFactor
```

---

# 41. Performance

Performance engine hỗ trợ:

```text
AbsoluteReturn
TimeWeightedReturn
MoneyWeightedReturn
InternalRateOfReturn
AnnualizedReturn
Volatility
Sharpe
Sortino
Calmar
MaximumDrawdown
TrackingError
InformationRatio
Beta
Alpha
```

Các metric chỉ là **measurement**, không phải universal evaluation.

---

# 42. Benchmark

```axiom
struct Benchmark {
    id: BenchmarkId
    methodology: BenchmarkMethodology
    constituents: BenchmarkConstituentSet
    currency: Currency
    rebalance_rule: RebalanceRule
}
```

---

# 43. Performance Attribution

Phân rã:

```text
AssetAllocation
SecuritySelection
Interaction
Currency
Factor
Sector
Country
Timing
Fees
Taxes
```

---

# 44. Fund

```axiom
struct Fund {
    id: FundId
    strategy: StrategyRef
    manager: ManagerRef
    base_currency: Currency
    nav_policy: NAVPolicy
    liquidity: FundLiquidity
}
```

---

# 45. Fund Share

```text
Fund
    ├── ShareClass A
    ├── ShareClass B
    └── Institutional
```

Mỗi share class có thể có:

```text
Fee
Currency
MinimumInvestment
DistributionPolicy
Eligibility
```

---

# 46. NAV

NAV engine:

```text
NAV
=
Assets
- Liabilities
----------------
UnitsOutstanding
```

NAV phải giữ valuation timestamp và valuation source.

---

# 47. NAV Lifecycle

```text
Estimated
→ Calculated
→ Validated
→ Published
→ Final
→ Restated?
```

Restatement phải giữ lịch sử.

---

# 48. Mutual Fund / ETF Boundary

`AXINVEST` quản lý:

```text
fund strategy
portfolio
NAV
shares
fees
investor allocation
```

Market trading của ETF/fund units thuộc market infrastructure.

---

# 49. Private Equity

Native support:

```text
Fund
Commitment
CapitalCall
Distribution
PortfolioCompany
InvestmentRound
Valuation
Exit
```

---

# 50. Venture Capital

```text
Deal
Pipeline
DueDiligence
InvestmentMemo
TermSheetRef
Commitment
Ownership
FollowOn
Exit
```

---

# 51. Private Credit

```text
Borrower
Loan
Commitment
Drawdown
Interest
Covenant
CollateralRef
DefaultEvent
Recovery
```

Loan accounting vẫn thuộc finance/banking boundary khi cần.

---

# 52. Real Assets

Hỗ trợ reference tới:

```text
RealEstate
Infrastructure
Agriculture
Energy
NaturalResource
```

Domain truth thuộc:

```text
AXHOUSING
AXCONSTRUCTION
AXAGRI
AXRESOURCE
```

---

# 53. Wealth Management

Wealth runtime quản lý:

```text
Client
Household
Goal
Account
Portfolio
TaxLot
EstateReference
LiquidityNeed
RiskProfile
InvestmentPlan
```

---

# 54. Goal-Based Investing

```axiom
goal retirement {
    target = 10_000_000
    horizon = 20y
    confidence_target = 0.85
}
```

Engine tính:

```text
required_contribution
required_return
probability_distribution
shortfall
scenario_range
```

---

# 55. Liability-Driven Investment

Cho phép portfolio tối ưu theo liability:

```text
Assets
vs
FutureLiabilities
```

Mục tiêu:

```text
funding_ratio
duration_matching
cashflow_matching
tail_protection
```

---

# 56. Pension

Native entities:

```text
PensionPlan
Participant
Contribution
Benefit
Liability
FundingRatio
GlidePath
```

---

# 57. Insurance Investment

`AXINSURANCE` có thể tạo investment mandate cho reserves/capital.

Ví dụ:

```text
InsuranceReserve
    ↓
InvestmentMandate
    ↓
AXINVEST
```

Nhưng insurance liability semantics vẫn thuộc `AXINSURANCE`.

---

# 58. Banking Investment

Bank treasury có thể dùng:

```text
LiquidityPortfolio
InvestmentPortfolio
HedgePortfolio
CapitalPortfolio
```

Banking regulatory state vẫn thuộc `AXBANKING`.

---

# 59. Capital Allocation

Enterprise allocation:

```text
BusinessUnit
Project
Plant
R&D
Acquisition
Infrastructure
WorkingCapital
```

Ví dụ:

```axiom
allocate capital {
    RnD = 20%
    expansion = 35%
    infrastructure = 25%
    reserve = 20%
}
```

---

# 60. Project Investment

Project phải có:

```text
InitialCapital
ExpectedCashFlow
Timeline
Risk
Scenario
NPV
IRR
Payback
Sensitivity
```

---

# 61. Capital Budgeting

```text
ProjectUniverse
    ↓
Forecast
    ↓
Constraints
    ↓
Optimization
    ↓
CapitalPlan
```

---

# 62. Investment Thesis

```axiom
struct InvestmentThesis {
    thesis: TextRef
    assumptions: AssumptionSet
    catalysts: CatalystSet
    risks: RiskSet
    invalidation_conditions: ConditionSet
    provenance: Provenance
}
```

AI-generated thesis phải được đánh dấu.

---

# 63. Research Signal

```text
ResearchSignal
    ├── Fundamental
    ├── Technical
    ├── Macro
    ├── AlternativeData
    ├── Sentiment
    └── Quantitative
```

Signal không phải trade instruction.

---

# 64. Research Pipeline

```text
Data
→ Normalize
→ Feature
→ Signal
→ Hypothesis
→ Backtest
→ Validation
→ ResearchResult
```

---

# 65. Alternative Data

Hỗ trợ:

```text
Satellite
Web
Transaction
SupplyChain
Weather
Mobility
Device
Sensor
Text
Audio
Image
```

Nhưng phải tuân thủ:

```text
AXPRIVACY
AXLAW
AXDATA_GOVERNANCE
```

---

# 66. Fundamental Analysis

Native primitive:

```text
Revenue
EBITDA
EBIT
CashFlow
Debt
Assets
Liabilities
Margin
Growth
ValuationMultiple
```

Nguồn dữ liệu phải được provenance.

---

# 67. Factor Model

Factor:

```text
Value
Growth
Quality
Momentum
Size
LowVolatility
Liquidity
Carry
Macro
Custom
```

Factor exposure không đồng nghĩa với causal explanation.

---

# 68. Portfolio Factor Decomposition

```text
Portfolio
    ↓
FactorExposure
    ↓
RiskContribution
    ↓
ScenarioImpact
```

---

# 69. Monte Carlo

Native simulation:

```axiom
simulate portfolio {
    paths = 100000
    horizon = 30y

    shocks:
        market
        inflation
        rates
        currency
}
```

---

# 70. Distribution Output

Không chỉ trả về một giá trị:

```text
P5
P10
P25
Median
P75
P90
P95
Mean
Variance
CVaR
```

---

# 71. Value at Risk

```text
VaR(confidence, horizon)
```

---

# 72. Expected Shortfall / CVaR

```text
CVaR(confidence, horizon)
```

phải giữ:

```text
confidence
horizon
model
dataset
timestamp
```

---

# 73. Stress Testing

Built-in scenario classes:

```text
MarketCrash
RateShock
InflationShock
Deflation
CurrencyShock
CreditCrisis
LiquidityFreeze
CommodityShock
SupplyShock
PandemicReference
ClimateScenario
GeopoliticalScenarioReference
```

Không được biến scenario thành assertion về tương lai.

---

# 74. Backtesting

Backtest phải chống look-ahead:

```text
DataTimestamp
DecisionTimestamp
ExecutionTimestamp
SettlementTimestamp
```

Engine phải reject dữ liệu không khả dụng tại decision time.

---

# 75. Backtest Bias Controls

Bắt buộc kiểm soát:

```text
LookAheadBias
SurvivorshipBias
SelectionBias
DataLeakage
Overfitting
TransactionCostOmission
CorporateActionError
TimezoneError
```

---

# 76. Walk-Forward Validation

```text
train
→ validate
→ roll
→ train
→ validate
```

---

# 77. Paper Portfolio

```text
SimulatedPortfolio
```

không được ghi nhận là:

```text
LivePortfolio
```

---

# 78. Digital Twin

Investment digital twin:

```text
ObservedState
EstimatedState
ForecastState
ScenarioState
```

Không được ghi đè live state.

---

# 79. AI Investment Agent

```axiom
agent PortfolioManager {
    can:
        read(portfolio)
        read(market_data)
        run(analysis)
        run(simulation)
        propose(rebalance)

    cannot:
        execute(trade)
}
```

Execution capability phải được cấp riêng.

---

# 80. AI Research Agent

Có thể:

```text
retrieve
analyze
compare
summarize
model
simulate
generate_thesis
```

Nhưng research agent không mặc định có quyền giao dịch.

---

# 81. AI Portfolio Manager

```text
Observe
→ Analyze
→ Generate Candidates
→ Optimize
→ Risk Check
→ Constraint Check
→ Explain
→ Request Approval
→ Execute
```

---

# 82. Human Approval

Policy:

```axiom
approval required when {
    transaction_value > limit
    or
    risk_change > threshold
}
```

---

# 83. Delegated Authority

```text
Owner
→ Delegate
→ Agent
→ Scope
→ Limit
→ Expiry
```

Delegation phải:

```text
time-bound
scope-bound
amount-bound
capability-bound
auditable
revocable
```

---

# 84. Investment Decision Record

Mỗi decision phải có:

```text
DecisionId
Actor
Authority
Timestamp
Inputs
DataVersions
ModelVersion
Objective
Constraints
Recommendation
Approval
ExecutionReference
Outcome
```

---

# 85. Explainability

Investment recommendation có thể yêu cầu:

```text
Why
Evidence
Assumptions
Sensitivity
Risk
AlternativeScenarios
ConstraintImpact
```

---

# 86. Model Provenance

Mọi model output phải lưu:

```text
ModelId
ModelVersion
TrainingDataset
FeatureSet
ParameterSet
ExecutionEnvironment
Timestamp
```

---

# 87. Data Provenance

Mỗi financial observation phải có:

```text
Source
ObservedAt
PublishedAt
EffectiveAt
Currency
Unit
TransformationChain
Confidence
```

---

# 88. Valuation

Valuation methods:

```text
MarketPrice
DCF
Comparable
NAV
ReplacementCost
Liquidation
YieldCurve
ModelBased
Oracle
Manual
```

---

# 89. Valuation Hierarchy

Không mặc định coi mọi valuation source ngang nhau.

```text
Source
→ Method
→ Timestamp
→ Confidence
→ OverridePolicy
```

---

# 90. Stale Price Detection

Runtime phải phát hiện:

```text
stale_price
missing_price
outlier_price
market_closed
suspended_asset
```

---

# 91. Currency

Portfolio có thể multi-currency.

Engine phải hỗ trợ:

```text
BaseCurrency
AssetCurrency
TransactionCurrency
ReportingCurrency
HedgeCurrency
```

---

# 92. FX Exposure

Tách:

```text
EconomicExposure
AccountingExposure
TransactionExposure
```

---

# 93. Tax-Lot

```axiom
struct TaxLot {
    asset: AssetRef
    acquisition_date: Date
    quantity: Decimal
    cost_basis: Money
}
```

Tax rules không hard-code trong investment core.

---

# 94. Fee Model

```text
ManagementFee
PerformanceFee
TransactionFee
CustodyFee
PlatformFee
PerformanceCarry
SubscriptionFee
RedemptionFee
```

---

# 95. Fee Accrual

Fee phải có:

```text
basis
rate
period
accrual
settlement
```

---

# 96. Liquidity

Mỗi asset có:

```text
LiquidityClass
ExpectedExitTime
MarketDepth
Lockup
RedemptionTerms
SettlementCycle
```

---

# 97. Liquidity Buckets

```text
Immediate
Daily
Weekly
Monthly
Quarterly
Annual
Illiquid
Locked
```

---

# 98. Capital Commitment

Private-market investment:

```text
Committed
Called
Invested
Distributed
Uncalled
```

---

# 99. Cash Flow Engine

Hỗ trợ:

```text
Contribution
Distribution
Dividend
Interest
Coupon
CapitalCall
Redemption
Fee
Tax
```

---

# 100. Income

Income types:

```text
Dividend
Interest
Coupon
RentReference
RoyaltyReference
Distribution
Other
```

---

# 101. Corporate Actions Boundary

Investment layer consumes:

```text
Split
Dividend
Merger
SpinOff
Tender
Redemption
```

Market/custody system remains authoritative for execution.

---

# 102. Order Intent

`AXINVEST` creates:

```axiom
struct OrderIntent {
    portfolio: PortfolioRef
    asset: AssetRef
    side: BuySell
    quantity: Decimal
    limit: Price?
    rationale: DecisionRef
}
```

Đây chưa phải market order.

---

# 103. Execution Instruction Boundary

```text
OrderIntent
    ↓
ExecutionInstruction
    ↓
AXCAPITALMARKETS
```

---

# 104. Portfolio Constraint Engine

Mỗi proposed transaction phải kiểm tra:

```text
Mandate
Risk
Liquidity
Concentration
Leverage
Currency
Tax
Regulation
Operational
```

---

# 105. Pre-Trade Check

```axiom
check_trade(intent)
    -> PreTradeResult
```

Output:

```text
Approved
Rejected
NeedsApproval
NeedsReview
```

---

# 106. Post-Trade Check

Sau execution:

```text
Position
Risk
Exposure
Liquidity
Concentration
Performance
```

được recalculated.

---

# 107. Drift Engine

```axiom
drift(portfolio)
    -> AllocationDrift
```

---

# 108. Rebalance Planner

```axiom
plan_rebalance(
    portfolio,
    target,
    constraints
)
```

Output:

```text
RebalancePlan
```

---

# 109. Investment Policy Statement

```axiom
policy portfolio_policy {
    objective total_return

    risk:
        max_drawdown = 25%

    allocation:
        equity = 40..70%
        fixed_income = 20..50%
        cash = 5..20%

    liquidity:
        minimum = 10%
}
```

---

# 110. Policy Versioning

Mọi policy phải immutable theo version:

```text
Policy v1
Policy v2
Policy v3
```

Historical decisions phải tham chiếu policy version đã sử dụng.

---

# 111. Portfolio Versioning

Portfolio state phải hỗ trợ:

```text
snapshot
diff
restore
audit
```

---

# 112. Audit Trail

Mọi mutation quan trọng:

```text
who
what
when
why
under_which_authority
using_which_model
```

---

# 113. Security Capabilities

Core capabilities:

```text
investment.read
investment.write

portfolio.read
portfolio.write

position.read
position.write

mandate.read
mandate.write

strategy.read
strategy.write

allocation.read
allocation.write

rebalance.plan
rebalance.approve

order_intent.create
order_intent.approve

research.read
research.write

model.run
simulation.run

valuation.read
valuation.write

fund.read
fund.write

nav.calculate
nav.publish

wealth.read
wealth.write

capital_plan.read
capital_plan.write

investment.execute

investment.admin
```

---

# 114. Capability Separation

Đặc biệt:

```text
investment.analyze
≠
investment.recommend
≠
investment.approve
≠
investment.execute
```

---

# 115. Privacy

Dữ liệu wealth phải được phân loại:

```text
Public
Internal
Confidential
Restricted
HighlyRestricted
```

---

# 116. Wealth Privacy

Không cho phép agent suy luận hoặc xuất bản:

```text
net worth
holdings
income
portfolio
financial behavior
```

nếu không có authorization.

---

# 117. Multi-Tenant Isolation

Investment data phải partition theo:

```text
Tenant
Organization
Investor
Account
Portfolio
```

---

# 118. Regulatory Boundary

`AXINVEST` không hard-code một jurisdiction.

Thay vào đó:

```text
InvestmentRuleSet
RegulatoryProfile
JurisdictionPolicy
```

được inject từ governance/regulatory layer.

---

# 119. Compliance Engine

Pre-trade compliance có thể kiểm tra:

```text
PositionLimit
IssuerLimit
CountryLimit
AssetEligibility
Leverage
Liquidity
Concentration
Mandate
RestrictedList
```

---

# 120. Restricted Asset

```axiom
restriction asset X {
    reason = policy_reference
    scope = portfolio
    effective = time_range
}
```

---

# 121. Suitability / Appropriateness Boundary

Investment system có thể lưu:

```text
RiskProfile
InvestmentObjective
KnowledgeLevel
LiquidityNeed
```

nhưng legal suitability authority thuộc policy/regulatory layer.

---

# 122. Benchmark Governance

Benchmark methodology phải versioned:

```text
BenchmarkDefinition
BenchmarkVersion
ConstituentSnapshot
RebalanceHistory
```

---

# 123. Index Reference

Investment layer có thể consume:

```text
Index
IndexConstituent
IndexWeight
IndexEvent
```

Index calculation authority có thể thuộc market-data provider.

---

# 124. Market Data Boundary

`AXINVEST` không cần sở hữu exchange matching engine.

Nó consume:

```text
PriceFeed
OrderBookSnapshot
YieldCurve
FXRate
VolatilitySurface
ReferenceData
CorporateAction
```

từ market infrastructure.

---

# 125. Alternative Investment

Hỗ trợ abstraction:

```text
AlternativeAsset
AlternativeValuation
AlternativeLiquidity
AlternativeRisk
```

---

# 126. Collectibles / Non-Financial Assets

Có thể đầu tư vào:

```text
art
collectibles
land
resource
```

nhưng authoritative domain semantics vẫn thuộc:

```text
AXCULTURE
AXHOUSING
AXRESOURCE
```

---

# 127. Civilization Capital Allocation

Runtime phải cho phép mô phỏng:

```text
PlanetaryCapital
    ↓
Energy
Food
Housing
Transport
Manufacturing
Healthcare
Education
Science
Infrastructure
```

---

# 128. Civilization Investment Graph

```text
Capital
 ├── Production
 ├── Infrastructure
 ├── Research
 ├── HumanCapital
 ├── Energy
 ├── Food
 └── Reserves
```

---

# 129. Macro Allocation

Có thể mô hình hóa:

```text
Region
Country
Sector
Industry
AssetClass
```

và:

```text
capital_flow
```

---

# 130. Capital Flow

```axiom
struct CapitalFlow {
    source: CapitalNode
    destination: CapitalNode
    amount: Money
    purpose: CapitalPurpose
    timestamp: Timestamp
}
```

---

# 131. Investment Multiplier Simulation

Có thể mô phỏng:

```text
Investment
→ ProductionCapacity
→ Employment
→ Income
→ Consumption
→ Revenue
→ Reinvestment
```

Đây là simulation, không phải accounting fact.

---

# 132. AI Macro Investment Simulation

AI có thể tạo:

```text
Scenario
CapitalAllocation
ExpectedImpact
RiskDistribution
SecondOrderEffects
```

---

# 133. Feedback Loop

```text
CIVILIZATION
      ↓
ECONOMIC ACTIVITY
      ↓
CASH FLOW
      ↓
CAPITAL
      ↓
INVESTMENT
      ↓
PRODUCTION
      ↓
EMPLOYMENT
      ↓
CONSUMPTION
      ↓
CIVILIZATION
```

---

# 134. Insurance Feedback

```text
RISK
 ↓
INSURANCE
 ↓
CAPITAL
 ↓
INVESTMENT
 ↓
RESILIENCE
 ↓
RISK
```

---

# 135. Banking Feedback

```text
SAVINGS
 ↓
BANKING
 ↓
CREDIT
 ↓
INVESTMENT
 ↓
PRODUCTION
 ↓
INCOME
 ↓
SAVINGS
```

---

# 136. Investment Twin

`InvestmentTwin` phải chứa:

```text
LiveObservedState
EstimatedState
ForecastState
ScenarioState
PolicyState
```

---

# 137. Scenario Isolation

Simulation không được mutate live portfolio:

```text
simulate(portfolio)
```

phải tạo:

```text
SimulationPortfolio
```

---

# 138. Scenario Branching

```axiom
scenario recession from portfolio {
    market_return = -30%
    unemployment = +5%
}
```

---

# 139. Scenario Comparison

```text
Scenario A
Scenario B
Scenario C
```

có thể so sánh:

```text
return
risk
drawdown
liquidity
funding
capital
```

---

# 140. Decision Frontier

Runtime có thể tạo:

```text
risk-return frontier
liquidity-return frontier
cost-return frontier
```

nhưng không tự chọn phương án nếu mandate chưa xác định objective.

---

# 141. Optimization Explainability

`OptimizationResult` phải lưu:

```text
objective
constraints
feasible_region
binding_constraints
solver
solver_version
solution
alternative_solutions
```

---

# 142. Solver Boundary

Core runtime không phụ thuộc solver bên thứ ba.

Axiom có:

```text
OptimizationProvider
```

interface.

Có thể implement:

```text
NativeSolver
ExternalSolverAdapter
GPUOptimizer
DistributedOptimizer
```

---

# 143. Numerical Precision

Finance types:

```text
Money
Decimal
Rate
Ratio
Quantity
Price
Probability
Duration
```

Không dùng `f32` cho authoritative monetary arithmetic.

---

# 144. Deterministic Finance

Các operation quan trọng phải hỗ trợ deterministic mode:

```text
decimal arithmetic
fixed rounding
explicit currency
explicit timestamp
explicit valuation source
```

---

# 145. Rounding Policy

```axiom
rounding {
    mode = HalfEven
    scale = 2
}
```

Policy phải explicit.

---

# 146. Time

Investment engine phải phân biệt:

```text
TradeTime
MarketTime
ValuationTime
SettlementTime
AccountingTime
ReportingTime
```

---

# 147. Calendar

Hỗ trợ:

```text
MarketCalendar
SettlementCalendar
HolidayCalendar
BusinessDayRule
```

---

# 148. Event Model

Events:

```text
InvestmentCreated
MandateChanged
AllocationChanged
PositionChanged
ValuationUpdated
RiskUpdated
RebalanceProposed
RebalanceApproved
OrderIntentCreated
InvestmentDecisionRecorded
FundNAVPublished
CapitalCalled
DistributionMade
```

---

# 149. Event Sourcing Boundary

Có thể lưu event stream:

```text
PortfolioEventLog
```

để tái dựng portfolio state.

---

# 150. Query Model

Native queries:

```axiom
portfolio.positions()
portfolio.exposure()
portfolio.performance()
portfolio.risk()
portfolio.liquidity()
portfolio.attribution()
```

---

# 151. DSL

Ví dụ hoàn chỉnh:

```axiom
portfolio retirement {
    currency = USD

    objective {
        total_return
        preserve_liquidity = 12%
    }

    allocation {
        equity       = 45..65%
        fixed_income = 25..45%
        cash         = 5..20%
        real_assets  = 0..15%
    }

    risk {
        max_drawdown = 25%
        max_issuer = 5%
    }

    rebalance {
        threshold = 5%
    }
}
```

---

# 152. AI Strategy DSL

```axiom
strategy ai_growth {
    observe market
    observe macro
    observe portfolio

    analyze:
        valuation
        momentum
        risk
        liquidity

    propose allocation

    require approval
}
```

---

# 153. Autonomous Strategy

Autonomy levels:

```text
ObserveOnly
AnalyzeOnly
Recommend
Plan
ApproveBounded
ExecuteBounded
Autonomous
```

Mỗi level là capability riêng.

---

# 154. Kill Switch

Investment agent phải hỗ trợ:

```text
pause
revoke
freeze
disable
emergency_exit
```

`emergency_exit` vẫn phải tuân thủ authorization/policy.

---

# 155. Model Risk

Model phải có:

```text
ModelRiskClass
ValidationStatus
ApprovalStatus
Expiry
MonitoringPolicy
Fallback
```

---

# 156. Model Drift

Theo dõi:

```text
PredictionDrift
FeatureDrift
PerformanceDrift
RegimeShift
DataDrift
```

---

# 157. Strategy Lifecycle

```text
Draft
→ Backtested
→ Validated
→ Approved
→ Paper
→ Live
→ Suspended
→ Retired
```

---

# 158. Fund Lifecycle

```text
Proposed
→ Formed
→ Open
→ Operating
→ SoftClosed
→ Closed
→ Liquidating
→ Terminated
```

---

# 159. Portfolio Lifecycle

```text
Draft
→ Active
→ Restricted
→ Frozen
→ Closing
→ Closed
```

---

# 160. Position Lifecycle

```text
Proposed
→ Ordered
→ Executed
→ Settled
→ Held
→ Reduced
→ Closed
```

---

# 161. Investment Recommendation Lifecycle

```text
Generated
→ Validated
→ Reviewed
→ Approved
→ Executed
→ Evaluated
→ Archived
```

---

# 162. Error Model

Core errors:

```text
InvestmentError
InvalidMandate
ConstraintViolation
InsufficientLiquidity
UnauthorizedExecution
StaleValuation
MissingMarketData
InvalidPrice
InvalidCurrency
RiskLimitExceeded
ConcentrationLimitExceeded
ModelUnavailable
SimulationFailure
OptimizationInfeasible
PolicyConflict
DataProvenanceError
```

---

# 163. Optimization Infeasible

Không được tự động nới constraint.

Phải trả:

```text
Infeasible
```

kèm:

```text
conflicting_constraints
```

và optional relaxation analysis.

---

# 164. Constraint Relaxation

Có thể tính:

```text
minimum_relaxation_required
```

nhưng không tự động áp dụng.

---

# 165. Observability

Metrics:

```text
portfolio_count
position_count
valuation_latency
optimization_latency
risk_calculation_latency
simulation_throughput
decision_count
recommendation_count
approval_latency
execution_rejection_rate
model_drift
```

---

# 166. Tracing

Trace:

```text
InvestmentDecision
 → Data
 → Model
 → Optimization
 → Risk
 → Approval
 → OrderIntent
 → MarketExecution
```

---

# 167. Performance Architecture

Hot path:

```text
MarketData
→ PortfolioState
→ Risk
→ Constraint
→ Optimization
```

phải hỗ trợ:

```text
SIMD
parallel CPU
GPU
distributed execution
```

khi phù hợp.

---

# 168. Memory Model

Large portfolio matrices phải hỗ trợ:

```text
contiguous buffers
columnar layouts
memory mapping
zero-copy views
arena allocation
```

Không yêu cầu GC.

---

# 169. Numeric Kernel

Native kernels:

```text
vector
matrix
covariance
correlation
factor_exposure
optimization
MonteCarlo
quantile
convolution
```

---

# 170. GPU

Các workload phù hợp:

```text
Monte Carlo
matrix algebra
scenario simulation
large factor models
portfolio optimization
stress testing
```

---

# 171. Distributed Investment Compute

Cluster execution:

```text
ScenarioPartition
AssetPartition
PortfolioPartition
TimePartition
```

---

# 172. Deterministic Distributed Simulation

Distributed simulation phải hỗ trợ:

```text
seed
partition
ordering
aggregation
```

để reproducibility.

---

# 173. Cache

Cache levels:

```text
MarketDataCache
ValuationCache
RiskCache
FeatureCache
ModelCache
OptimizationCache
SimulationCache
```

Cache key phải bao gồm version/provenance.

---

# 174. Incremental Computation

Nếu chỉ thay đổi:

```text
one_position
```

không được bắt buộc recompute toàn bộ portfolio nếu dependency graph cho phép incremental update.

---

# 175. Dependency Graph

```text
Position
 ↓
Exposure
 ↓
Risk
 ↓
Allocation
 ↓
Portfolio
 ↓
Performance
```

Compiler/runtime có thể build dependency graph.

---

# 176. Compile-Time Investment Graph

Investment DSL có thể compile thành:

```text
InvestmentIR
```

---

# 177. Investment IR

Các node:

```text
ASSET
POSITION
PORTFOLIO
OBJECTIVE
CONSTRAINT
RISK_FACTOR
VALUATION
FORECAST
SCENARIO
OPTIMIZATION
DECISION
ORDER_INTENT
```

---

# 178. IR Example

```text
PORTFOLIO P
  OBJECTIVE TOTAL_RETURN
  CONSTRAINT EQUITY <= 70
  EXPOSURE FACTOR_VALUE
  OPTIMIZE
  RISK_CHECK
  EMIT ORDER_INTENT
```

---

# 179. Static Validation

Compiler có thể phát hiện:

```text
missing_currency
invalid_asset_class
conflicting_constraints
undefined_benchmark
unauthorized_capability
invalid_risk_measure
```

trước runtime.

---

# 180. AI-Readable Artifacts

Compiler artifact phải chứa:

```text
PortfolioSchema
MandateSchema
StrategySchema
RiskSchema
ConstraintSchema
DecisionGraph
ProvenanceGraph
```

---

# 181. Investment Metadata

Annotations:

```axiom
@risk_factor("equity_beta")
@valuation("market")
@liquidity("daily")
@authority("portfolio_manager")
@requires("investment.execute")
```

---

# 182. Static Authority Analysis

Compiler phải kiểm tra:

```text
recommend()
```

không tự động được coi là:

```text
execute()
```

---

# 183. Simulation Isolation

Compiler phải phân biệt:

```text
live
paper
simulation
backtest
stress
```

và reject accidental cross-write.

---

# 184. Serialization

Native formats:

```text
AXINVEST-BIN
AXPORT
AXFUND
AXSTRATEGY
AXSCENARIO
AXDECISION
```

---

# 185. Version Compatibility

Artifacts phải chứa:

```text
schema_version
compiler_version
model_version
policy_version
```

---

# 186. WASM

WASM profile hỗ trợ:

```text
portfolio analytics
financial calculators
simulation subset
visualization backend
```

---

# 187. Mobile

Mobile profile ưu tiên:

```text
portfolio
wealth
risk
analytics
approval
```

Không mặc định chạy full distributed simulation.

---

# 188. Embedded

Embedded profile có thể hỗ trợ:

```text
portfolio controller
treasury device
energy investment controller
```

với memory footprint nhỏ.

---

# 189. Server

Server profile hỗ trợ:

```text
multi-tenant
distributed
GPU
AI
large portfolio
simulation
```

---

# 190. Native Profiles

```text
AXINVEST_NONE
AXINVEST_CORE
AXINVEST_PORTFOLIO
AXINVEST_RISK
AXINVEST_OPT
AXINVEST_FUND
AXINVEST_WEALTH
AXINVEST_PRIVATE
AXINVEST_RESEARCH
AXINVEST_SIMULATION
AXINVEST_AI
AXINVEST_GPU
AXINVEST_DISTRIBUTED
AXINVEST_MOBILE
AXINVEST_WASM
AXINVEST_FULL
```

---

# 191. Dependency Rule

`AXINVEST_CORE` không được phụ thuộc:

```text
GUI
AI
GPU
Network
Database
```

---

# 192. Database Independence

Investment runtime phải hoạt động với:

```text
in-memory
file
embedded storage
distributed storage
external database adapter
```

---

# 193. External Provider Boundary

Các provider:

```text
MarketDataProvider
CustodyProvider
ExecutionProvider
ValuationProvider
TaxProvider
RegulatoryProvider
OptimizationProvider
AIModelProvider
```

---

# 194. No Mandatory Third-Party Runtime

Native Axiom implementation phải có fallback provider cho core.

---

# 195. Test Architecture

Tối thiểu:

**≥ 17.000 automated tests**

và:

**≥ 1.400 architecture invariants**

---

# 196. Test Categories

```text
Unit
Integration
Numerical
Determinism
PropertyBased
Fuzz
Backtest
Simulation
Security
Authorization
Privacy
Performance
Concurrency
Distributed
GPU
WASM
Mobile
Recovery
Audit
AI
```

---

# 197. Numerical Tests

Kiểm tra:

```text
rounding
overflow
underflow
precision
currency conversion
return calculation
NAV
risk metrics
optimization
Monte Carlo
```

---

# 198. Financial Invariants

### INV-01

```text
PortfolioValue
=
Σ PositionValue
+
Cash
```

trong cùng valuation context.

### INV-02

```text
NAV
=
Assets - Liabilities
```

theo fund accounting context.

### INV-03

Recommendation không tự động tạo execution.

### INV-04

Simulation không mutate live portfolio.

### INV-05

Forecast không được ghi thành observed fact.

### INV-06

Không được execute nếu capability không tồn tại.

### INV-07

Backtest không được sử dụng dữ liệu tương lai.

### INV-08

Historical decision phải giữ model/policy/data version.

### INV-09

Optimization không được tự động relax constraints.

### INV-10

Currency phải explicit trong monetary calculation.

---

# 199. AI Safety Invariants

```text
AI cannot self-grant investment.execute
AI cannot modify its own authority
AI cannot erase decision history
AI cannot rewrite provenance
AI cannot convert simulation into live state
AI cannot silently change mandate
AI cannot silently relax constraints
```

---

# 200. Capital Allocation Invariants

```text
AllocatedCapital <= AvailableCapital
CommittedCapital >= CalledCapital
CalledCapital >= InvestedCapital
```

theo lifecycle semantics tương ứng.

---

# 201. Liquidity Invariants

Nếu mandate yêu cầu:

```text
minimum_liquidity = X
```

mọi approved allocation phải satisfy constraint tại execution check.

---

# 202. Concentration Invariants

Issuer/sector/country limits không được vượt nếu policy đang active.

---

# 203. Audit Invariants

Mọi privileged mutation phải có:

```text
Actor
Authority
Timestamp
Reason
```

---

# 204. Reproducibility

Cùng:

```text
dataset
model
parameters
seed
policy
code version
```

phải cho phép tái tạo kết quả trong deterministic mode.

---

# 205. Failure Recovery

Nếu optimizer crash:

```text
PortfolioState
```

không được mutate một phần.

Optimization transaction phải atomic:

```text
prepare
→ validate
→ commit
```

---

# 206. Crash Safety

Decision record phải được durable trước khi execution instruction được phát ra nếu policy yêu cầu.

---

# 207. Security Threats

Phải chống:

```text
UnauthorizedTrading
PrivilegeEscalation
PortfolioTampering
ModelTampering
DataPoisoning
SignalInjection
PromptInjection
MarketDataSpoofing
ReplayAttack
DecisionForgery
AuditDeletion
TenantEscape
```

---

# 208. AI Prompt Injection

Research documents có thể chứa nội dung độc hại.

AI investment agent phải coi external research là:

```text
untrusted data
```

không phải authority.

---

# 209. Market Data Poisoning

Không được để một nguồn dữ liệu duy nhất tự động trở thành authoritative nếu policy yêu cầu multi-source validation.

---

# 210. Model Governance

Model lifecycle:

```text
Created
→ Tested
→ Validated
→ Approved
→ Deployed
→ Monitored
→ Suspended
→ Retired
```

---

# 211. Strategy Governance

Strategy lifecycle tương tự model:

```text
Research
→ Backtest
→ Validation
→ Approval
→ Paper
→ Production
```

---

# 212. Shadow Mode

Strategy mới có thể chạy:

```text
shadow
```

mà không tạo live order intent.

---

# 213. Canary Strategy

Có thể giới hạn:

```text
capital
portfolio
region
asset
```

trong rollout.

---

# 214. Kill Criteria

Strategy có thể bị suspend khi:

```text
risk_limit_breach
model_drift
data_integrity_failure
unexpected_behavior
authority_revoked
```

---

# 215. Investment Monitoring

Dashboard native API:

```text
portfolio value
allocation
risk
drawdown
liquidity
performance
exposure
strategy state
model state
```

---

# 216. Alert Engine

```text
risk_alert
liquidity_alert
concentration_alert
drawdown_alert
model_alert
data_alert
authority_alert
```

---

# 217. Reporting

Native reports:

```text
PortfolioReport
PerformanceReport
RiskReport
AttributionReport
LiquidityReport
ExposureReport
FundReport
InvestorReport
CapitalPlan
ScenarioReport
```

---

# 218. Reporting Reproducibility

Report phải tham chiếu:

```text
as_of
valuation_set
data_version
policy_version
model_version
```

---

# 219. Global Investment Network

Civilization-scale graph:

```text
Investor
  ↓
Fund
  ↓
Portfolio
  ↓
Asset
  ↓
Company
  ↓
Production
  ↓
Economy
```

---

# 220. Ownership Graph

Hỗ trợ:

```text
Investor
→ Fund
→ Holding
→ Company
→ Subsidiary
→ Asset
```

nhưng legal ownership authority có thể nằm ở `AXLAW/AXFINANCE/custody`.

---

# 221. Capital Network

Graph edges:

```text
owns
invests
lends
funds
insures
guarantees
hedges
allocates
```

---

# 222. Systemic Risk Interface

`AXINVEST` cung cấp:

```text
PortfolioExposure
CapitalFlow
Concentration
CrossOwnership
LiquidityDependency
CounterpartyDependency
```

cho civilization/economic simulation.

---

# 223. Cross-Domain Risk

Có thể liên kết:

```text
Climate
Energy
Food
Housing
Transport
Labor
Healthcare
Manufacturing
Finance
Insurance
```

để mô phỏng systemic risk.

---

# 224. Investment → Real Economy

Một investment allocation có thể reference:

```text
Factory
HousingProject
EnergyPlant
Farm
InfrastructureProject
ResearchProgram
```

nhưng không trực tiếp sở hữu operational semantics của các domain đó.

---

# 225. Capital Efficiency

Analytics:

```text
ROIC
ROE
CapitalTurnover
AssetTurnover
EconomicProfit
CapitalIntensity
```

---

# 226. Enterprise Capital Allocation

```axiom
capital_plan enterprise {
    maximize economic_value

    projects:
        factory_A
        solar_B
        research_C

    constraints:
        capital <= 1B
        liquidity >= 200M
}
```

---

# 227. Portfolio + Project Integration

Một portfolio có thể chứa:

```text
public securities
private investments
projects
real assets
cash
```

nhưng mỗi domain giữ semantics riêng.

---

# 228. Wealth Aggregation

Household wealth có thể aggregate:

```text
cash
securities
retirement
real_estate_ref
private_assets
liabilities_ref
```

---

# 229. Net Worth Boundary

`AXINVEST` có thể consume:

```text
AssetValuation
LiabilityReference
```

nhưng canonical balance sheet thuộc finance/accounting layer.

---

# 230. Family Office

Support:

```text
Household
MultipleAccounts
MultipleJurisdictions
MultipleCurrencies
TaxLots
PrivateAssets
TrustReferences
Goals
```

---

# 231. Multi-Generational Planning

Có thể mô phỏng:

```text
generation
wealth_transfer
investment
liability
education
retirement
```

Legal estate transfer vẫn thuộc legal layer.

---

# 232. Investment Knowledge Graph

Nodes:

```text
Company
Asset
Sector
Factor
MacroEvent
Research
Analyst
Model
Strategy
Portfolio
```

Edges:

```text
exposes
depends_on
correlates
owns
competes
supplies
invests
references
```

---

# 233. Semantic Search

Native queries:

```text
find assets exposed to energy shortage
find portfolios with high FX exposure
find investments affected by housing slowdown
```

---

# 234. Causal Boundary

Correlation không được tự động ghi thành causal relation.

Causal claims phải có:

```text
CausalEvidence
```

hoặc explicit model.

---

# 235. Uncertainty

Mọi forecast quan trọng phải có:

```text
estimate
confidence
interval
scenario
model
```

nếu available.

---

# 236. Probability Calibration

AI probability output có thể được monitor:

```text
Calibration
BrierScore
LogLoss
Reliability
```

---

# 237. Strategy Evaluation

Không dùng một metric duy nhất.

Có thể báo cáo:

```text
return
risk
drawdown
liquidity
turnover
cost
stability
capacity
```

---

# 238. Capacity

Strategy capacity là estimate về mức vốn có thể triển khai trước khi market impact/cost thay đổi đáng kể.

Không đồng nhất:

```text
Capacity ≠ GuaranteedReturn
```

---

# 239. Crowding

Có thể monitor:

```text
crowded_factor
crowded_trade
common_exposure
```

---

# 240. Systemic Investment Simulation

Simulation có thể mô hình hóa:

```text
many investors
many funds
many assets
capital flows
feedback
liquidity
risk propagation
```

---

# 241. Agent Investment Economy

AI agents có thể đại diện:

```text
RetailInvestor
FundManager
Pension
BankTreasury
InsuranceInvestor
SovereignFund
Corporation
```

nhưng mỗi agent phải có explicit mandate.

---

# 242. Agent Interaction

```text
observe
forecast
allocate
request_execution
receive_result
update_belief
```

---

# 243. Multi-Agent Market Boundary

Actual matching/auction/order-book logic thuộc:

```text
BOOTSTRAP-693
```

---

# 244. Global Capital Simulation

```axiom
simulate civilization {
    investors = 1_000_000
    funds = 50_000
    companies = 1_000_000

    horizon = 30y

    shocks:
        energy
        food
        housing
        rates
        climate
}
```

---

# 245. Civilization-Level Outputs

```text
capital_allocation
investment_flow
sector_funding
infrastructure_funding
systemic_risk
liquidity
wealth_distribution_reference
```

---

# 246. Distribution Boundary

Wealth distribution analytics có thể được consume từ `AX670`, nhưng `AXINVEST` không tự suy luận sensitive personal attributes.

---

# 247. Ethical / Policy Constraints

Investment strategy có thể encode explicit policy:

```text
restricted_assets
sustainability_policy
mission_policy
organization_policy
```

Runtime chỉ enforce policy đã được cung cấp.

---

# 248. No Hidden Objective

AI investment system không được có objective ẩn ngoài:

```text
DeclaredObjective
DeclaredConstraints
DeclaredAuthority
```

---

# 249. Objective Audit

Mỗi optimization phải có machine-readable:

```text
objective_graph
constraint_graph
authority_graph
```

---

# 250. Final Architecture Contract

`AXINVEST` trở thành lớp native:

```text
                AXINVEST
                    │
       ┌────────────┼────────────┐
       │            │            │
   PORTFOLIO      FUNDS       WEALTH
       │            │            │
       ├────────────┼────────────┤
       │            │            │
      RISK       RESEARCH     CAPITAL
       │            │            │
       └────── OPTIMIZATION ─────┘
                    │
              DECISION ENGINE
                    │
             ORDER INTENT
                    │
                    ▼
          AXCAPITAL-MARKETS
```

---

# 251. Core Separation

```text
AXFINANCE
    = financial truth/accounting primitives

AXBANKING
    = banking/credit/deposit/payment systems

AXINSURANCE
    = risk transfer/insurance

AXINVEST
    = capital allocation/investment management

AXCAPITAL-MARKETS
    = market execution infrastructure
```

---

# 252. Required Native APIs

Tối thiểu:

```text
create_investor()
create_account()
create_mandate()

create_portfolio()
add_position()
remove_position()

calculate_value()
calculate_return()
calculate_risk()
calculate_exposure()

optimize()
simulate()
stress_test()
backtest()

plan_rebalance()
check_constraints()

create_investment_decision()
create_recommendation()
create_order_intent()

calculate_nav()
calculate_attribution()

create_fund()
create_strategy()

run_capital_plan()
run_wealth_plan()

audit_decision()
```

---

# 253. Native Query Examples

```axiom
portfolio P {
    value()
    risk()
    exposure()
    liquidity()
    performance()
}
```

```axiom
risk portfolio P {
    var(95%, 1d)
    cvar(95%, 1d)
    max_drawdown()
}
```

```axiom
optimize P {
    objective maximize(total_return)
    constraint volatility <= 12%
    constraint equity <= 70%
}
```

---

# 254. Native AI Example

```axiom
agent InvestorAI {
    authority = recommendation

    observe portfolio
    observe market

    analyze risk
    analyze valuation

    propose allocation

    require approval
}
```

---

# 255. Native Autonomous Example

```axiom
agent TreasuryAI {
    authority {
        execute
        max_notional = 10M
        asset_classes = [Cash, FixedIncome]
    }

    policy treasury_policy

    enforce all_constraints

    audit every_decision
}
```

---

# 256. Compiler Guarantees

Axiom compiler phải có khả năng xác minh tĩnh:

```text
authority mismatch
invalid asset reference
invalid currency
missing objective
constraint contradiction
simulation/live contamination
unauthorized execution
```

---

# 257. Runtime Guarantees

Runtime phải đảm bảo:

```text
atomic portfolio mutation
deterministic accounting primitives
immutable audit history
capability enforcement
versioned policy
versioned model
provenance preservation
simulation isolation
```

---

# 258. Performance Targets

Target:

```text
portfolio valuation:
    O(n)

risk incremental update:
    O(changed_dependencies)

constraint checking:
    O(k)

large matrix operations:
    SIMD/GPU capable

Monte Carlo:
    massively parallel

optimization:
    pluggable solver architecture
```

---

# 259. Memory Targets

Không bắt buộc garbage collection.

Ưu tiên:

```text
arena
region
owned buffers
contiguous arrays
views
immutable snapshots
copy-on-write khi cần
```

---

# 260. Concurrency

Portfolio calculations có thể parallel:

```text
positions
risk factors
scenarios
assets
portfolios
```

nhưng commit state phải có transactional boundary.

---

# 261. Deterministic Commit

```text
parallel calculate
→ deterministic reduce
→ validate
→ atomic commit
```

---

# 262. Distributed Commit

Distributed portfolio updates phải sử dụng explicit consistency policy:

```text
strong
snapshot
eventual
```

Không được mặc định coi eventual state là authoritative financial state.

---

# 263. Observed / Estimated / Predicted / Simulated

Đây là invariant xuyên suốt:

```text
OBSERVED
   ≠
ESTIMATED
   ≠
PREDICTED
   ≠
SIMULATED
```

---

# 264. Recommendation / Approval / Execution

Invariant:

```text
RECOMMENDATION
      ≠
APPROVAL
      ≠
EXECUTION
```

---

# 265. Final Domain Boundary

`AXINVEST` chịu trách nhiệm:

```text
who invests
what they invest in
why they invest
how much they allocate
what constraints apply
what risks exist
how portfolio is optimized
how performance is measured
how capital is simulated
```

Không chịu trách nhiệm trực tiếp:

```text
exchange matching
broker execution
clearing
settlement
custody authority
legal ownership adjudication
```

---

# 266. Architecture Invariant Set

Các invariant quan trọng nhất:

```text
INV-001 Investment ≠ Trading
INV-002 Asset ≠ Security
INV-003 Position ≠ Ownership Record
INV-004 Return ≠ Profit
INV-005 Risk ≠ Loss
INV-006 Forecast ≠ Fact
INV-007 Recommendation ≠ Decision
INV-008 Decision ≠ Execution
INV-009 Simulation ≠ Live State
INV-010 Capacity ≠ Guaranteed Performance
INV-011 Optimization ≠ Truth
INV-012 Model Output ≠ Authority
INV-013 AI Authority Cannot Self-Escalate
INV-014 Constraint Relaxation Requires Explicit Policy
INV-015 Historical Decision Is Immutable
INV-016 Provenance Is Preserved
INV-017 Backtest Cannot See Future Data
INV-018 Monetary Arithmetic Is Explicitly Typed
INV-019 Currency Is Never Implicit
INV-020 Live Portfolio Mutation Is Atomic
INV-021 Unauthorized Agent Cannot Execute
INV-022 Fund NAV Is Versioned
INV-023 Strategy Is Versioned
INV-024 Policy Is Versioned
INV-025 Model Is Versioned
INV-026 Simulation Cannot Write Live State
INV-027 Portfolio State Can Be Reconstructed
INV-028 Risk Calculation Is Reproducible
INV-029 AI Research Is Untrusted Input
INV-030 External Market Data Does Not Automatically Become Truth
```

---

# 267. Completion Criteria

BOOTSTRAP-692 chỉ được xem là hoàn thành khi:

```text
[✓] Investor model
[✓] Account model
[✓] Mandate
[✓] Objective
[✓] Constraint
[✓] Asset model
[✓] Security model
[✓] Position
[✓] Portfolio
[✓] Strategy
[✓] SAA/TAA
[✓] Rebalancing
[✓] Risk
[✓] Performance
[✓] Benchmark
[✓] Fund
[✓] NAV
[✓] Private markets
[✓] Wealth management
[✓] Capital budgeting
[✓] Research
[✓] Factor model
[✓] Optimization
[✓] Monte Carlo
[✓] Backtesting
[✓] Stress testing
[✓] AI investment agent
[✓] Authority
[✓] Provenance
[✓] Privacy
[✓] Security
[✓] Simulation
[✓] Digital twin
[✓] Civilization-scale capital allocation
[✓] Native DSL
[✓] Investment IR
[✓] Compiler validation
[✓] CPU/GPU
[✓] Distributed
[✓] WASM
[✓] Mobile
[✓] Test architecture
```

---

# 268. Architecture Result

Sau BOOTSTRAP-692, Axiom có một lớp vốn hoàn chỉnh:

```text
PRODUCTION
     ↓
CASH FLOW
     ↓
FINANCE
     ↓
BANKING
     ↓
INSURANCE
     ↓
CAPITAL
     ↓
INVESTMENT
     ↓
PORTFOLIO
     ↓
ALLOCATION
     ↓
ORDER INTENT
```

Lớp tiếp theo phải xây dựng **hạ tầng thị trường** nhận `OrderIntent` và biến nó thành giao dịch có khả năng khớp, bù trừ và thanh toán.

---

# 269. Next Architecture Task

**BOOTSTRAP-693**

## Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Order Books, Market Data, Clearing, Settlement, Custody & Global Financial Market Infrastructure Runtime 5.0

Chuỗi tiếp theo:

```text
AXFINANCE
    ↓
AXBANKING
    ↓
AXINSURANCE
    ↓
AXINVEST
    ↓
AXCAPITAL-MARKETS
    ↓
EXCHANGE
    ↓
BROKER
    ↓
ORDER BOOK
    ↓
MATCHING
    ↓
CLEARING
    ↓
SETTLEMENT
    ↓
CUSTODY
    ↓
GLOBAL CAPITAL MARKET
```

Đây sẽ là lớp nối trực tiếp **quyết định phân bổ vốn của BOOTSTRAP-692** với **hạ tầng giao dịch tài chính thực tế**.
:::

**Task kế tiếp đã được xác định là BOOTSTRAP-693; chuỗi có thể tiếp tục tự động từ lớp Capital Markets.**