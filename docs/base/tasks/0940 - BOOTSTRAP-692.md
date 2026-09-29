Tiếp tục chuỗi kiến trúc Axiom với **BOOTSTRAP-692 — Investment & Global Capital Allocation Runtime 5.0**. Đây là lớp nối `AXFINANCE + AXINSURANCE + AXCOMMERCE + AXLABOR + AXCIVILIZATION` vào hệ thống đầu tư, thị trường vốn, quỹ và phân bổ vốn quy mô lớn.

:::writing{variant="document" id="58321" title="BOOTSTRAP-692 — Native AI Civilization-Scale Investment, Asset Management, Wealth Management, Funds, Securities, Portfolio Optimization, Capital Allocation & Global Investment Runtime 5.0"}
# BOOTSTRAP-692
## Native AI Civilization-Scale Investment, Asset Management, Wealth Management, Funds, Securities, Portfolio Optimization, Capital Allocation & Global Investment Runtime 5.0

**Status:** Architecture Specification  
**Version:** 5.0  
**Namespace:** `AXINVEST`  
**Layer:** Civilization Financial Intelligence / Capital Allocation  
**Primary role:** native investment, securities, portfolio, fund, asset-management, wealth-management and capital-allocation runtime.

---

# 1. Mục tiêu

`AXINVEST` cung cấp một runtime thống nhất cho:

- tài sản đầu tư;
- chứng khoán;
- cổ phiếu;
- trái phiếu;
- quỹ;
- ETF;
- private equity;
- venture capital;
- real estate investment;
- commodity exposure;
- digital assets;
- portfolio;
- asset allocation;
- wealth management;
- institutional investment;
- fund management;
- trading boundary;
- capital allocation;
- investment research;
- risk-adjusted optimization;
- scenario analysis;
- financial simulation;
- AI investment agents;
- civilization-scale capital-flow simulation.

Mục tiêu không phải xây một "ứng dụng chứng khoán", mà xây **native financial computation substrate** để các ứng dụng đầu tư, quỹ, ngân hàng, doanh nghiệp, chính phủ, AI agent và simulation engine cùng sử dụng một mô hình dữ liệu và execution model thống nhất.

---

# 2. Nguyên tắc kiến trúc

`AXINVEST` phải:

1. native;
2. deterministic ở những nơi yêu cầu;
3. high-performance;
4. vectorizable;
5. GPU-capable;
6. distributed-capable;
7. AI-native;
8. simulation-native;
9. audit-friendly;
10. provenance-aware;
11. capability-secured;
12. không biến prediction thành fact;
13. không biến recommendation thành execution;
14. không biến simulation thành live financial state.

---

# 3. Architectural Position

```text
AXCIVILIZATION
      │
      ├── AXGOV
      ├── AXLAW
      ├── AXECON
      ├── AXFINANCE
      ├── AXBANKING
      ├── AXINSURANCE
      │
      └── AXINVEST
             │
             ├── Securities
             ├── Markets
             ├── Funds
             ├── Portfolios
             ├── Wealth
             ├── Capital Allocation
             ├── Investment Research
             ├── Risk
             ├── Optimization
             ├── Simulation
             └── Investment AI
```

---

# 4. Fundamental Distinctions

Các distinction này là invariant của kiến trúc:

```text
Asset ≠ Security

Security ≠ Position

Position ≠ Portfolio

Portfolio ≠ Account

Price ≠ Value

MarketPrice ≠ FairValue

Return ≠ Profit

Profit ≠ CashFlow

Yield ≠ TotalReturn

Risk ≠ Loss

RiskEstimate ≠ ActualLoss

Forecast ≠ Fact

Prediction ≠ Decision

Recommendation ≠ Order

Order ≠ Execution

Execution ≠ Settlement

Settlement ≠ OwnershipRecord

Fund ≠ Portfolio

NAV ≠ MarketPrice

Capital ≠ Cash

Liquidity ≠ Solvency

Allocation ≠ Transfer

Simulation ≠ LiveState

Scenario ≠ Forecast

ModelOutput ≠ FinancialFact

AIRecommendation ≠ AuthorizedAction

OptimizationResult ≠ GuaranteedOutcome
```

---

# 5. Core Namespace

```axiom
namespace AXINVEST
```

Các module chính:

```text
AXINVEST.CORE
AXINVEST.ASSET
AXINVEST.SECURITY
AXINVEST.MARKET
AXINVEST.ORDER
AXINVEST.TRADE
AXINVEST.SETTLEMENT
AXINVEST.PORTFOLIO
AXINVEST.FUND
AXINVEST.ASSET_MANAGEMENT
AXINVEST.WEALTH
AXINVEST.ALLOCATION
AXINVEST.RISK
AXINVEST.VALUATION
AXINVEST.RESEARCH
AXINVEST.OPTIMIZATION
AXINVEST.SIMULATION
AXINVEST.AI
AXINVEST.GOVERNANCE
AXINVEST.PROVENANCE
AXINVEST.SECURITY
```

---

# 6. Core Entity Model

Các primitive entities:

```text
Investor
InvestorGroup
InvestmentAccount
CustodyAccount
Asset
Security
Instrument
Issuer
Market
Venue
Portfolio
Position
Holding
Fund
FundShare
Order
Execution
Trade
Settlement
CashBalance
Valuation
Price
Yield
Return
RiskMeasure
Scenario
Forecast
Allocation
Mandate
Strategy
Benchmark
Model
InvestmentRecommendation
```

---

# 7. Investor

```axiom
struct Investor {
    id: InvestorId
    entity: EntityRef
    jurisdiction: Jurisdiction
    profile: InvestorProfile
    risk_profile: RiskProfile
    objectives: InvestmentObjectives
}
```

Không được suy luận các thuộc tính nhạy cảm ngoài phạm vi được cấp quyền.

---

# 8. Investment Account

```axiom
struct InvestmentAccount {
    id: AccountId
    owner: EntityRef
    currency: Currency
    custody: CustodyRef
    portfolio: PortfolioRef
    status: AccountStatus
}
```

Account không đồng nghĩa với portfolio.

Một account có thể:

```text
1 portfolio
N portfolios
sub-portfolios
mandated sleeves
```

tùy cấu hình.

---

# 9. Asset

```axiom
struct Asset {
    id: AssetId
    class: AssetClass
    issuer: optional<IssuerRef>
    denomination: Currency
    jurisdiction: Jurisdiction
}
```

Asset class:

```text
Equity
Debt
Fund
Derivative
Commodity
Currency
RealEstate
Infrastructure
PrivateCompany
DigitalAsset
Cash
Collectible
Other
```

---

# 10. Security

```axiom
struct Security {
    id: SecurityId
    issuer: IssuerRef
    instrument: InstrumentType
    currency: Currency
    issue_date: DateTime
    maturity: optional<DateTime>
    identifiers: SecurityIdentifiers
}
```

Security có thể đại diện cho:

```text
share
bond
note
fund_unit
ETF_unit
certificate
preferred_share
convertible
structured_product
```

---

# 11. Issuer

```axiom
struct Issuer {
    id: IssuerId
    legal_entity: EntityRef
    jurisdiction: Jurisdiction
    sector: Sector
}
```

Issuer metadata không được coi là financial forecast.

---

# 12. Market

```axiom
struct Market {
    id: MarketId
    name: String
    currency: Currency
    timezone: TimeZone
    venue_type: VenueType
}
```

Venue:

```text
Exchange
OTC
Auction
Dealer
PrivateMarket
FundPlatform
InternalVenue
SimulationVenue
```

---

# 13. Price Model

Price phải phân biệt:

```text
ObservedPrice
IndicativePrice
BidPrice
AskPrice
LastPrice
ReferencePrice
SettlementPrice
ModelPrice
FairValue
EstimatedValue
```

Không được implicit cast:

```text
ModelPrice -> ObservedPrice
EstimatedValue -> MarketPrice
```

---

# 14. Portfolio

```axiom
struct Portfolio {
    id: PortfolioId
    owner: EntityRef
    base_currency: Currency
    positions: PositionSet
    mandate: MandateRef
    benchmark: optional<BenchmarkRef>
}
```

Portfolio là logical collection.

Nó không tự động là custody account.

---

# 15. Position

```axiom
struct Position {
    security: SecurityRef
    quantity: Decimal
    average_cost: Money
    market_value: Money
    unrealized_pnl: Money
    realized_pnl: Money
}
```

---

# 16. Lot Accounting

Hệ thống phải hỗ trợ:

```text
Lot
TaxLot
AcquisitionLot
DisposalLot
CostBasis
HoldingPeriod
```

Ví dụ:

```axiom
lot = position.lot("AAPL", acquisition_date)
```

Không được mất lot provenance khi aggregate.

---

# 17. Cash

Cash là position đặc biệt:

```text
CashPosition
CashBalance
AccruedCash
RestrictedCash
MarginCash
CollateralCash
```

Không đồng nhất:

```text
Cash ≠ Liquidity
```

---

# 18. Portfolio State

Portfolio state phải có:

```text
positions
cash
exposure
market_value
cost_basis
PnL
income
fees
taxes
leverage
liquidity
risk
constraints
```

---

# 19. Portfolio Valuation

Runtime hỗ trợ:

```axiom
portfolio.value(at: timestamp)
portfolio.value(currency: USD)
portfolio.pnl(period)
portfolio.return(period)
portfolio.exposure()
```

Valuation phải mang provenance:

```text
source
timestamp
price_type
currency
FX_source
model
confidence
```

---

# 20. Return Model

Hỗ trợ:

```text
AbsoluteReturn
SimpleReturn
LogReturn
TimeWeightedReturn
MoneyWeightedReturn
IRR
XIRR
AnnualizedReturn
RollingReturn
```

Không cho phép nhầm lẫn giữa return methodology.

---

# 21. PnL

```text
RealizedPnL
UnrealizedPnL
GrossPnL
NetPnL
TradingPnL
IncomePnL
FXPnL
FeePnL
TaxPnL
```

---

# 22. Income

```text
Dividend
Coupon
Interest
Distribution
RentalIncome
Royalty
OtherIncome
```

Income không tự động là realized profit.

---

# 23. Benchmark

```axiom
struct Benchmark {
    id: BenchmarkId
    methodology: BenchmarkMethodology
    constituents: BenchmarkConstituents
    rebalance: RebalanceRule
}
```

Benchmark phải có methodology version.

---

# 24. Investment Strategy

```axiom
struct Strategy {
    id: StrategyId
    objective: StrategyObjective
    universe: InvestmentUniverse
    constraints: ConstraintSet
    rebalance_rule: RebalanceRule
}
```

---

# 25. Mandate

Mandate xác định:

```text
allowed assets
forbidden assets
risk limits
concentration limits
liquidity limits
currency limits
leverage limits
ESG/custom constraints nếu được cấu hình
execution authority
approval requirements
```

Mandate là constraint, không phải prediction.

---

# 26. Security Master

`AXINVEST.SECURITY` phải duy trì canonical instrument metadata:

```text
ISIN
CUSIP
SEDOL
ticker
exchange_symbol
issuer
currency
country
sector
asset_class
maturity
coupon
share_class
fund_class
```

External identifiers là aliases.

`SecurityId` là canonical internal identifier.

---

# 27. Corporate Actions

Hỗ trợ:

```text
Dividend
Split
ReverseSplit
RightsIssue
BonusIssue
Merger
Acquisition
SpinOff
TenderOffer
Conversion
Redemption
Delisting
SymbolChange
```

Corporate action phải có:

```text
announcement
effective_date
record_date
payment_date
terms
source
```

---

# 28. Corporate Action Processing

Pipeline:

```text
Detected
Validated
Announced
Eligible
Applied
Reconciled
Closed
```

---

# 29. Order

```axiom
struct Order {
    id: OrderId
    account: AccountRef
    security: SecurityRef
    side: Side
    quantity: Decimal
    order_type: OrderType
    limit_price: optional<Price>
    time_in_force: TimeInForce
}
```

Order không phải execution.

---

# 30. Order Types

```text
Market
Limit
Stop
StopLimit
Auction
TWAP
VWAP
Iceberg
Pegged
Conditional
Algorithmic
```

Advanced order types nằm ngoài core nếu venue không hỗ trợ.

---

# 31. Order Lifecycle

```text
Draft
Submitted
Validated
Accepted
Routed
PartiallyFilled
Filled
Cancelled
Rejected
Expired
```

---

# 32. Execution

```axiom
struct Execution {
    id: ExecutionId
    order: OrderRef
    quantity: Decimal
    price: Price
    timestamp: DateTime
    venue: VenueRef
    fees: Money
}
```

Một order có thể có nhiều execution.

---

# 33. Trade

Trade là aggregate economic event:

```text
buyer
seller
security
quantity
price
venue
trade_time
settlement_terms
```

---

# 34. Settlement

Settlement phải tách khỏi execution:

```text
TradeExecuted
SettlementPending
CashLegPending
AssetLegPending
Settled
Failed
Reconciled
```

---

# 35. Custody Boundary

Custody có thể thuộc:

```text
Broker
Bank
Custodian
FundAdministrator
InternalCustody
ExternalCustody
```

`AXINVEST` giữ economic position.

Custodian giữ authoritative custody record khi được cấu hình.

---

# 36. Fund

```axiom
struct Fund {
    id: FundId
    manager: EntityRef
    strategy: StrategyRef
    base_currency: Currency
    valuation_rule: ValuationRule
    share_classes: ShareClassSet
}
```

---

# 37. Fund Types

```text
MutualFund
ETF
IndexFund
MoneyMarketFund
HedgeFund
PrivateEquityFund
VentureCapitalFund
RealEstateFund
InfrastructureFund
PensionFund
SovereignFund
FamilyOfficeFund
ClosedEndFund
```

---

# 38. Fund NAV

NAV:

```text
NAV = (Assets - Liabilities) / OutstandingShares
```

Runtime phải lưu:

```text
gross_assets
liabilities
net_assets
shares
NAV
NAV_timestamp
valuation_method
```

NAV không mặc định bằng market price.

---

# 39. Fund Share

```axiom
struct FundShare {
    fund: FundRef
    class: ShareClass
    units: Decimal
    nav: Money
}
```

---

# 40. Subscription / Redemption

Fund lifecycle:

```text
OrderSubmitted
Accepted
CutoffValidated
Priced
Allocated
Settled
```

Redemption có thể có:

```text
lockup
notice_period
gate
fee
liquidity_limit
```

---

# 41. Asset Management

Asset manager entities:

```text
AssetManager
PortfolioManager
InvestmentCommittee
ResearchTeam
RiskTeam
Trader
Operations
FundAdministrator
Custodian
```

Role không tự động cấp financial authority.

---

# 42. Wealth Management

Wealth layer hỗ trợ:

```text
ClientProfile
Household
Goal
Account
Portfolio
RiskProfile
InvestmentPlan
TaxConstraint
LiquidityNeed
AllocationPlan
```

---

# 43. Household

```axiom
struct Household {
    id: HouseholdId
    members: EntitySet
    accounts: AccountSet
    goals: GoalSet
    consolidated_view: ConsolidatedPortfolio
}
```

Consolidation không làm mất account-level provenance.

---

# 44. Investment Goal

```text
Retirement
Education
HomePurchase
LiquidityReserve
CapitalPreservation
Income
Growth
Legacy
Other
```

Goal là objective, không phải guaranteed outcome.

---

# 45. Risk Profile

Risk profile có thể chứa:

```text
risk_capacity
risk_tolerance
liquidity_need
time_horizon
constraints
```

Không được tự động biến behavioral inference thành authoritative investor profile.

---

# 46. Investment Universe

```axiom
struct InvestmentUniverse {
    securities: SecuritySet
    filters: FilterSet
    eligibility_rules: RuleSet
}
```

---

# 47. Exposure

Hỗ trợ exposure theo:

```text
security
issuer
sector
country
currency
asset_class
factor
duration
maturity
commodity
geography
theme
```

---

# 48. Gross / Net Exposure

Portfolio phải hỗ trợ:

```text
GrossExposure
NetExposure
LongExposure
ShortExposure
DerivativeExposure
LookThroughExposure
```

---

# 49. Look-Through

Fund có thể được phân rã:

```text
Portfolio
  └── Fund
       └── Holdings
```

Look-through phải lưu:

```text
source
timestamp
depth
confidence
method
```

---

# 50. Concentration

Các metrics:

```text
TopNExposure
IssuerConcentration
SectorConcentration
CountryConcentration
CurrencyConcentration
LiquidityConcentration
MaturityConcentration
```

---

# 51. Risk Model

Risk engine hỗ trợ:

```text
Volatility
Variance
Covariance
Correlation
Beta
TrackingError
Drawdown
VaR
CVaR
ExpectedShortfall
StressLoss
LiquidityRisk
ConcentrationRisk
CreditRisk
MarketRisk
CurrencyRisk
InterestRateRisk
```

---

# 52. Risk Factor

Factor:

```text
Market
Size
Value
Momentum
Quality
Volatility
Rates
Credit
Inflation
FX
Commodity
Liquidity
Custom
```

Factor model version phải được lưu.

---

# 53. Covariance Engine

Hỗ trợ:

```text
HistoricalCovariance
EWMA
FactorCovariance
Shrinkage
RobustCovariance
ScenarioCovariance
```

Các model không được trộn mà không ghi model identity.

---

# 54. VaR

Hỗ trợ:

```text
HistoricalVaR
ParametricVaR
MonteCarloVaR
```

Mọi VaR result phải ghi:

```text
confidence
horizon
method
dataset
model_version
timestamp
```

---

# 55. Expected Shortfall

```axiom
portfolio.expected_shortfall(
    confidence: 0.975,
    horizon: 10d
)
```

Kết quả là estimate, không phải future fact.

---

# 56. Stress Testing

Stress scenario:

```text
rate_shock
equity_crash
FX_shock
commodity_shock
credit_spread_shock
liquidity_shock
combined_macro_shock
custom_scenario
```

---

# 57. Scenario

```axiom
struct Scenario {
    id: ScenarioId
    assumptions: AssumptionSet
    shocks: ShockSet
    probability: optional<Probability>
}
```

Probability optional vì scenario không nhất thiết là forecast.

---

# 58. Forecast

Forecast phải phân biệt:

```text
PointForecast
IntervalForecast
DistributionForecast
ConditionalForecast
```

Kèm:

```text
horizon
model
training_window
confidence
timestamp
```

---

# 59. Valuation

Valuation methods:

```text
Market
DCF
Comparable
NAV
YieldBased
ReplacementCost
OptionModel
Fundamental
BookValue
Appraisal
Custom
```

---

# 60. Fair Value

```axiom
struct FairValue {
    security: SecurityRef
    value: Money
    method: ValuationMethod
    assumptions: AssumptionSet
    confidence: optional<ConfidenceInterval>
}
```

Fair value không phải market price.

---

# 61. DCF Engine

Native DCF hỗ trợ:

```text
revenue
margin
capex
working_capital
tax
terminal_value
discount_rate
scenario
```

Không hard-code business assumptions vào core runtime.

---

# 62. Fixed Income

Bond model hỗ trợ:

```text
coupon
yield
duration
modified_duration
convexity
maturity
credit_spread
cashflow_schedule
```

---

# 63. Interest Rate Risk

Metrics:

```text
DV01
PV01
duration
convexity
key_rate_duration
```

---

# 64. Credit

Credit analytics:

```text
default_probability
loss_given_default
exposure_at_default
expected_loss
credit_spread
rating_reference
```

Rating là external observation/reference, không phải runtime truth.

---

# 65. Derivatives Boundary

Hỗ trợ semantic model:

```text
Option
Future
Forward
Swap
Warrant
Convertible
StructuredProduct
```

Pricing engines:

```text
BlackScholes
Binomial
MonteCarlo
FiniteDifference
Custom
```

---

# 66. Derivative Exposure

Runtime phải hỗ trợ:

```text
Delta
Gamma
Theta
Vega
Rho
Greeks
ScenarioSensitivity
```

---

# 67. Alternative Investments

Hỗ trợ:

```text
PrivateEquity
VentureCapital
PrivateDebt
RealEstate
Infrastructure
Commodity
Collectibles
PrivateCompany
```

Các tài sản illiquid phải có liquidity metadata.

---

# 68. Private Equity

Fund model:

```text
Commitment
CalledCapital
UncalledCapital
Investment
Distribution
NAV
Exit
IRR
MOIC
TVPI
DPI
RVPI
```

---

# 69. Venture Capital

Hỗ trợ:

```text
Round
Valuation
Dilution
CapTable
Ownership
PreferredShares
OptionPool
ExitScenario
```

Cap table có thể liên kết với `AXCOMMERCE`/`AXLAW` nhưng financial ownership model nằm tại `AXINVEST`.

---

# 70. Real Estate Investment

Liên kết:

```text
AXHOUSING
AXCONSTRUCTION
AXRESOURCE
AXCOMMERCE
```

Investment runtime quản lý:

```text
property_asset
rent
occupancy
cap_rate
NOI
mortgage_ref
valuation
cashflow
```

Không trở thành authoritative property registry.

---

# 71. Commodity

Commodity exposure:

```text
Physical
Futures
ETF
Forward
Synthetic
```

Physical asset semantics thuộc domain resource/agriculture/manufacturing khi cần.

---

# 72. Digital Asset Boundary

Hỗ trợ generic:

```text
DigitalAsset
Token
CustodyReference
ExchangeReference
OnChainPosition
```

Blockchain infrastructure thuộc lớp transport/storage/distributed systems.

---

# 73. Portfolio Allocation

Allocation vector:

```axiom
allocation[
    Equity = 0.60,
    FixedIncome = 0.25,
    Cash = 0.10,
    Alternatives = 0.05
]
```

Tổng allocation phải tuân thủ normalization policy.

---

# 74. Strategic Asset Allocation

```text
StrategicAllocation
TacticalAllocation
DynamicAllocation
LiabilityDrivenAllocation
GoalBasedAllocation
```

---

# 75. Rebalancing

Triggers:

```text
Calendar
Threshold
Drift
Risk
Liquidity
Tax
CorporateAction
MandateChange
```

Rebalancing tạo **proposed actions**, không tự động execute nếu thiếu authority.

---

# 76. Optimization

Core optimization problem:

```text
maximize objective
subject to constraints
```

Objective có thể là:

```text
ExpectedReturn
RiskAdjustedReturn
TrackingError
Utility
Income
Liquidity
CapitalPreservation
GoalAchievement
```

---

# 77. Optimization Constraints

```text
weight >= 0
weight <= max_weight
sum(weight) = 1
sector <= limit
issuer <= limit
turnover <= limit
liquidity >= minimum
leverage <= maximum
```

---

# 78. Mean-Variance

Native solver:

```axiom
portfolio.optimize.mean_variance(...)
```

---

# 79. Risk Parity

```axiom
portfolio.optimize.risk_parity(...)
```

---

# 80. Black-Litterman Boundary

Có thể cung cấp:

```text
Prior
Views
Confidence
Posterior
```

Nhưng views phải được lưu provenance.

---

# 81. Goal-Based Optimization

Objective:

```text
maximize probability of meeting goals
```

Runtime phải trả về:

```text
scenario_distribution
goal_probability_estimate
shortfall_distribution
```

Không được mô tả probability estimate như guarantee.

---

# 82. Multi-Period Optimization

Hỗ trợ:

```text
dynamic_programming
stochastic_control
scenario_tree
model_predictive_allocation
```

---

# 83. Capital Allocation

Capital allocation engine phân bổ giữa:

```text
BusinessUnits
Projects
Funds
Securities
Infrastructure
R&D
Inventory
RealEstate
Loans
Reserves
```

Liên kết với:

```text
AXFINANCE
AXBANKING
AXINSURANCE
AXMANUFACTURING
AXCOMMERCE
AXSCIENCE
AXCIVILIZATION
```

---

# 84. Enterprise Capital Allocation

```text
Cash
Debt
Equity
Capex
R&D
Acquisition
Buyback
Dividend
WorkingCapital
Reserves
```

---

# 85. Project Investment

Investment project:

```axiom
struct InvestmentProject {
    id: ProjectId
    capital_required: Money
    cashflows: CashFlowSchedule
    risks: RiskSet
    scenarios: ScenarioSet
}
```

Metrics:

```text
NPV
IRR
Payback
ProfitabilityIndex
RiskAdjustedNPV
```

---

# 86. Capital Budgeting

Pipeline:

```text
Proposal
DueDiligence
Modeling
RiskReview
Approval
Allocation
Execution
Monitoring
Exit
```

---

# 87. Investment Research

Research entities:

```text
ResearchReport
ResearchNote
FinancialModel
Thesis
Catalyst
Risk
Assumption
Evidence
Source
```

---

# 88. Research Provenance

Mọi model output phải truy được:

```text
input_dataset
source
timestamp
model
version
assumptions
analyst/agent
```

---

# 89. Investment Thesis

```axiom
struct Thesis {
    claim: Statement
    evidence: EvidenceSet
    assumptions: AssumptionSet
    risks: RiskSet
    invalidation_conditions: ConditionSet
}
```

Thesis không phải fact.

---

# 90. Evidence

Evidence types:

```text
MarketData
FinancialStatement
RegulatoryFiling
CompanyDisclosure
Research
AlternativeData
DerivedMetric
ModelOutput
HumanObservation
```

---

# 91. Financial Data

Native structured datasets:

```text
PriceSeries
FundamentalSeries
FinancialStatement
CashFlowStatement
BalanceSheet
IncomeStatement
EconomicSeries
AlternativeData
```

---

# 92. Time Series

Time series phải hỗ trợ:

```text
timestamp
timezone
frequency
calendar
adjustment
revision
source
quality
```

---

# 93. Revised Data

Economic/financial datasets có thể bị revision.

Runtime phải hỗ trợ:

```text
Vintage
Revision
AsOf
EffectiveAt
ObservedAt
```

Để backtest không vô tình dùng future-revised data.

---

# 94. Backtesting

Backtest engine:

```text
Dataset
Universe
Strategy
ExecutionModel
Costs
Slippage
Constraints
Period
Benchmark
```

Output:

```text
return
drawdown
turnover
risk
fees
taxes
exposure
```

---

# 95. Backtest Invariant

Không được sử dụng dữ liệu chưa tồn tại tại thời điểm simulation:

```text
future_information == forbidden
```

---

# 96. Transaction Cost Model

Hỗ trợ:

```text
commission
spread
slippage
market_impact
tax
exchange_fee
financing_cost
borrow_cost
```

---

# 97. Market Impact

Model:

```text
Linear
SquareRoot
OrderBook
Empirical
Custom
```

Kết quả là estimate.

---

# 98. Liquidity

Metrics:

```text
ADV
bid_ask_spread
depth
turnover
days_to_liquidate
liquidity_score
```

---

# 99. Liquidity Simulation

Portfolio liquidation simulation phải tính:

```text
position_size
market_depth
impact
time
fees
constraints
```

---

# 100. Asset Management Workflow

```text
Universe
→ Research
→ Thesis
→ Risk Analysis
→ Optimization
→ Proposed Allocation
→ Compliance Check
→ Approval
→ Order Generation
→ Execution
→ Settlement
→ Reconciliation
→ Performance
→ Risk Monitoring
```

---

# 101. Investment Recommendation

```axiom
struct InvestmentRecommendation {
    subject: SecurityRef
    thesis: ThesisRef
    rationale: EvidenceSet
    expected_metrics: MetricSet
    risks: RiskSet
    horizon: Duration
    confidence: optional<Confidence>
}
```

Recommendation không có execution authority.

---

# 102. AI Investment Agent

```axiom
agent InvestmentAnalyst {
    tools:
        market.read
        fundamentals.read
        portfolio.read
        research.read
        risk.compute
        simulation.run

    cannot:
        trade.execute
        cash.transfer
        custody.modify
}
```

---

# 103. AI Portfolio Manager

Agent có thể:

```text
analyze
simulate
optimize
propose
monitor
explain
```

Execution cần capability riêng:

```text
invest.order.create
invest.order.approve
invest.order.execute
```

---

# 104. Human Approval Boundary

Các action có financial consequence lớn có thể yêu cầu:

```text
human approval
multi-party approval
policy approval
limit approval
```

---

# 105. AI Guardrail

Không cho phép agent:

```text
bypass mandate
bypass risk limit
bypass approval
alter audit history
forge market data
convert forecast to fact
```

---

# 106. Portfolio AI

AI services:

```text
PortfolioAnalysis
RiskExplanation
AllocationProposal
RebalanceProposal
TaxAwareAllocation
LiquidityPlanning
ScenarioAnalysis
ResearchAssistant
AnomalyDetection
PerformanceAttribution
```

---

# 107. Performance Attribution

Hỗ trợ:

```text
AssetAllocationEffect
SecuritySelectionEffect
InteractionEffect
CurrencyEffect
SectorEffect
FactorEffect
Fees
```

---

# 108. Risk Attribution

```text
MarketRisk
FactorRisk
SectorRisk
IssuerRisk
CurrencyRisk
LiquidityRisk
DurationRisk
CreditRisk
```

---

# 109. Factor Attribution

```axiom
portfolio.factor_exposure()
portfolio.factor_contribution()
```

---

# 110. Tax-Aware Investment

Runtime chỉ cung cấp computational primitives:

```text
tax_lot
gain
loss
holding_period
realization
tax_estimate
```

Actual legal/tax authority thuộc:

```text
AXLAW
AXGOV
AXFINANCE
```

---

# 111. Portfolio Accounting Boundary

Investment runtime ghi:

```text
economic_position
valuation
performance
investment_events
```

General ledger authoritative state thuộc `AXFINANCE`.

---

# 112. Banking Boundary

`AXBANKING` quản lý:

```text
cash account
payment account
credit
deposit
loan
bank settlement
```

`AXINVEST` quản lý:

```text
investment position
portfolio
securities
investment orders
investment performance
```

---

# 113. Insurance Boundary

`AXINSURANCE` cung cấp:

```text
risk transfer
insurance liabilities
reserves
claims
```

`AXINVEST` cung cấp:

```text
investment of insurance assets
ALM allocation
portfolio risk
```

---

# 114. Pension Investment

Hỗ trợ:

```text
PensionFund
LiabilitySchedule
AssetPortfolio
FundingRatio
LiabilityDrivenInvestment
```

---

# 115. Asset-Liability Management

ALM model:

```text
Assets
Liabilities
Cashflows
Duration
Liquidity
Scenarios
FundingRatio
```

---

# 116. Sovereign Investment

Hỗ trợ generic:

```text
SovereignFund
ReservePortfolio
PublicInvestmentPortfolio
InfrastructureAllocation
StrategicReserve
```

Không trao cho runtime quyền lực chính sách ngoài capability được cấp.

---

# 117. Civilization Capital Flow

Simulation có thể mô hình hóa:

```text
Households
→ Banks
→ Funds
→ Companies
→ Projects
→ Production
→ Profits
→ Households
```

và:

```text
Insurance
→ Investment
→ Capital
→ Infrastructure
→ EconomicOutput
→ Risk
```

---

# 118. Global Capital Network

Graph:

```text
Investor
   ↓
Fund
   ↓
Security
   ↓
Issuer
   ↓
Project
   ↓
Production
```

Edges có:

```text
ownership
exposure
cashflow
control
risk
dependency
```

---

# 119. Systemic Risk

Simulation metrics:

```text
concentration
contagion
network_exposure
liquidity_shock
default_cascade
funding_stress
cross_asset_correlation
```

---

# 120. Contagion Simulation

Không được coi simulation result là prediction.

```axiom
scenario.simulate()
```

trả:

```text
ScenarioResult
```

không trả:

```text
FutureFact
```

---

# 121. Monte Carlo

Native engine:

```text
MonteCarloEngine
RandomProcess
Distribution
PathGenerator
ScenarioSampler
```

Hỗ trợ:

```text
CPU
SIMD
GPU
Distributed
```

---

# 122. Randomness

Phân biệt:

```text
TrueRandom
PseudoRandom
DeterministicRandom
CryptographicRandom
SimulationRandom
```

Backtesting phải có deterministic seed.

---

# 123. Distributed Simulation

Simulation có thể partition theo:

```text
scenario
portfolio
time
asset
agent
geography
```

---

# 124. GPU Execution

Các workloads GPU-native:

```text
MonteCarlo
MatrixOperations
Covariance
Optimization
ScenarioEvaluation
RiskCalculation
LargePortfolioValuation
```

---

# 125. Vectorized Portfolio Engine

Portfolio computations phải hỗ trợ:

```text
SIMD
SoA
batch valuation
batch risk
batch scenario
```

AoS chỉ sử dụng khi phù hợp.

---

# 126. Memory Model

Investment data phải ưu tiên:

```text
contiguous arrays
columnar layouts
arena allocation
immutable snapshots
copy-on-write
memory mapping
```

Không yêu cầu GC.

---

# 127. Snapshot

Portfolio snapshot:

```text
SnapshotId
Timestamp
Positions
Cash
Prices
FX
Risk
Valuation
ModelVersions
```

Snapshot phải immutable.

---

# 128. Event Sourcing Boundary

Investment event:

```text
OrderCreated
ExecutionReceived
TradeBooked
SettlementCompleted
DividendReceived
CorporateActionApplied
PositionAdjusted
ValuationUpdated
```

Event history không bị sửa trực tiếp.

Correction là event mới.

---

# 129. Reconciliation

Hỗ trợ reconciliation giữa:

```text
InternalPosition
BrokerPosition
CustodianPosition
FundAdministratorPosition
BankCash
MarketData
```

---

# 130. Reconciliation States

```text
Matched
Pending
Mismatch
Investigating
Resolved
```

---

# 131. Data Quality

Mỗi market datum có:

```text
source
timestamp
quality
confidence
revision
latency
adjustment
```

---

# 132. Market Data Feed

Provider boundary:

```text
MarketDataProvider
ReferenceDataProvider
FundamentalDataProvider
AlternativeDataProvider
```

Provider không thuộc core runtime.

---

# 133. Market Data Cache

Cache hỗ trợ:

```text
latest
historical
intraday
tick
snapshot
```

Content-addressing có thể được dùng cho immutable historical datasets.

---

# 134. Compliance Boundary

Investment compliance có thể kiểm tra:

```text
mandate
position_limit
issuer_limit
sector_limit
country_limit
leverage
liquidity
restricted_list
```

Compliance result:

```text
Pass
Fail
Warning
RequiresApproval
Unknown
```

`Unknown` không được tự động coi là Pass.

---

# 135. Restricted List

```axiom
RestrictedSecuritySet
RestrictedIssuerSet
RestrictedSectorSet
```

Nguồn và effective time phải được ghi.

---

# 136. Investment Policy

Policy engine:

```text
if exposure.issuer > 0.10:
    violation("issuer_limit")
```

Policy là declarative.

---

# 137. Capability Model

Core capabilities:

```text
invest.read
invest.write

security.read
security.write

market.read

portfolio.read
portfolio.write

position.read
position.write

order.create
order.approve
order.cancel

execution.read

trade.book

settlement.read
settlement.write

fund.read
fund.write

allocation.propose
allocation.approve
allocation.execute

risk.compute
valuation.compute
simulation.run

research.read
research.write

ai.analyze
ai.recommend
ai.execute

admin
```

---

# 138. Least Privilege

Agent nghiên cứu:

```text
market.read
research.read
risk.compute
```

không có:

```text
order.execute
cash.transfer
```

---

# 139. Audit

Audit record:

```text
actor
agent
capability
input
action
decision
output
timestamp
model_version
policy_version
approval
```

---

# 140. Provenance

Mọi financial derived result phải có:

```text
source lineage
calculation graph
model version
input snapshot
```

---

# 141. Calculation Graph

Ví dụ:

```text
Price
 ├── PositionValue
 │      └── PortfolioValue
 │             └── Return
 │                    └── RiskAdjustedReturn
```

Graph có thể được lưu dưới dạng native IR.

---

# 142. Financial IR

Đề xuất:

```text
FIN-IR
```

Nodes:

```text
ASSET
PRICE
POSITION
CASHFLOW
RISK
MODEL
SCENARIO
OPTIMIZATION
ALLOCATION
ORDER
EXECUTION
SETTLEMENT
```

---

# 143. FIN-IR Example

```text
%price = market_price %security @ %time

%position_value =
    multiply %price, %quantity

%portfolio_value =
    reduce_add %position_value

%risk =
    compute_var %portfolio_value,
                confidence=0.975,
                horizon=10d
```

---

# 144. Optimization IR

```text
%allocation =
    optimize
        objective=min_risk
        constraints=%constraints
        universe=%universe
        covariance=%cov
```

---

# 145. Compile-Time Optimization

Compiler có thể specialize:

```text
portfolio size
asset type
currency
risk model
frequency
GPU availability
```

---

# 146. Numerical Precision

Financial calculations phải hỗ trợ:

```text
i32/i64
u32/u64
f32
f64
Decimal
FixedPoint
Rational
```

Money mặc định không dùng binary floating point cho authoritative settlement values.

---

# 147. Decimal

```axiom
Money<USD>
Decimal<18,8>
Fixed<scale=8>
```

Phép toán tiền tệ phải xác định rounding mode.

---

# 148. Rounding

```text
RoundHalfEven
RoundHalfUp
RoundDown
RoundUp
Truncate
```

Rounding policy là explicit.

---

# 149. Currency

```text
Currency
FXRate
FXPair
FXForward
CurrencyExposure
```

FX conversion phải ghi:

```text
rate
source
timestamp
```

---

# 150. Multi-Currency Portfolio

Portfolio có:

```text
base_currency
local_currency
reporting_currency
```

FX PnL phải được tách riêng.

---

# 151. Performance Attribution Across Currency

```text
LocalReturn
FXReturn
CombinedReturn
```

Không cộng nhầm local return với FX return.

---

# 152. Fees

```text
ManagementFee
PerformanceFee
TransactionFee
CustodyFee
PlatformFee
BorrowFee
FinancingCost
```

---

# 153. Fund Fee Model

Hỗ trợ:

```text
ManagementFee
PerformanceFee
HighWaterMark
HurdleRate
Clawback
Carry
```

---

# 154. Liquidity Management

Portfolio có:

```text
available_cash
expected_inflows
expected_outflows
liquidity_buffer
```

---

# 155. Cashflow Forecast

```text
DividendForecast
CouponForecast
RedemptionForecast
CapitalCallForecast
DistributionForecast
ExpenseForecast
```

Forecast không phải realized cashflow.

---

# 156. Private Fund Capital Calls

```text
Commitment
CapitalCall
PaidCapital
UnfundedCommitment
Distribution
```

---

# 157. Portfolio Constraints

Constraint engine phải hỗ trợ:

```text
hard constraints
soft constraints
penalty constraints
conditional constraints
time-varying constraints
```

---

# 158. Optimization Objective

Objective function có thể được biểu diễn bằng Axiom:

```axiom
objective {
    maximize expected_return
    minimize risk
    penalty turnover * 0.01
}
```

---

# 159. Multi-Objective Optimization

Hỗ trợ:

```text
ParetoFront
WeightedObjective
LexicographicObjective
ConstraintPriority
```

---

# 160. Explainable Optimization

Result phải trả:

```text
why_selected
binding_constraints
marginal_contribution
sensitivity
alternative_solutions
```

---

# 161. Sensitivity

```text
dReturn/dRate
dValue/dFX
dRisk/dWeight
dNPV/dAssumption
```

---

# 162. Robust Optimization

Hỗ trợ uncertainty sets:

```text
parameter_uncertainty
covariance_uncertainty
return_uncertainty
liquidity_uncertainty
```

---

# 163. Stress Allocation

Portfolio phải có khả năng:

```text
stress()
stress_under(scenario)
compare(base, stressed)
```

---

# 164. Digital Twin

`InvestmentTwin` mô phỏng:

```text
portfolio
fund
market
capital network
institution
```

Twin states:

```text
Observed
Estimated
Predicted
Simulated
```

---

# 165. Civilization Investment Twin

Có thể mô phỏng:

```text
Households
Banks
Funds
Insurers
Corporations
Governments
Infrastructure
Markets
```

---

# 166. Capital Flow Graph

```text
Household Savings
      ↓
Bank / Fund
      ↓
Capital Market
      ↓
Enterprise
      ↓
Investment
      ↓
Production
      ↓
Income
      ↓
Household
```

---

# 167. Investment Shock

Simulation events:

```text
RateShock
LiquidityShock
DefaultShock
CommodityShock
EquityShock
FXShock
PolicyShock
SupplyShock
DemandShock
ClimateShock
InfrastructureShock
```

---

# 168. Systemic Feedback

Runtime có thể mô hình hóa:

```text
Risk
→ Selling
→ LiquidityDecline
→ PriceDecline
→ CollateralDecline
→ FundingStress
→ Selling
```

Đây là simulation graph, không phải assertion rằng chuỗi này sẽ xảy ra trong thực tế.

---

# 169. AI Research Pipeline

```text
Collect
→ Normalize
→ Validate
→ Retrieve
→ Analyze
→ Hypothesize
→ Model
→ Simulate
→ Compare
→ Explain
```

---

# 170. AI Evidence Graph

```text
Claim
 ├── Evidence
 ├── Assumption
 ├── Model
 ├── CounterEvidence
 └── Uncertainty
```

---

# 171. Contradiction Detection

AI có thể phát hiện:

```text
data contradiction
model contradiction
thesis contradiction
time-series inconsistency
accounting inconsistency
```

Không tự động quyết định source nào đúng.

---

# 172. Research Agent Memory

Investment agent memory phân biệt:

```text
Observation
Fact
Hypothesis
Thesis
Prediction
Decision
Outcome
```

---

# 173. Prediction Registry

Mỗi prediction:

```text
prediction_id
created_at
horizon
target
model
confidence
assumptions
outcome
```

Cho phép đánh giá calibration theo thời gian.

---

# 174. Model Registry

```text
InvestmentModel
RiskModel
PricingModel
ForecastModel
OptimizationModel
ExecutionModel
```

Lifecycle:

```text
Draft
Validated
Approved
Production
Deprecated
Retired
```

---

# 175. Model Governance

Model phải lưu:

```text
version
training_data
validation_data
metrics
owner
approval
limitations
known_failures
```

---

# 176. AI Model Drift

Monitor:

```text
data_drift
concept_drift
prediction_drift
calibration_drift
performance_drift
```

---

# 177. Simulation Registry

```text
Simulation
Scenario
Dataset
Seed
Model
Configuration
Result
```

Simulation result phải reproducible nếu deterministic seed được dùng.

---

# 178. Reproducibility

```axiom
simulation.reproduce(
    seed,
    dataset_version,
    model_version,
    config_hash
)
```

---

# 179. Security

Sensitive financial data phải hỗ trợ:

```text
encryption
capability isolation
tenant isolation
audit
data minimization
secure deletion
key rotation
```

Crypto primitives sử dụng `AXCRYPTO`.

---

# 180. Privacy

Không được mặc định expose:

```text
individual wealth
portfolio
trades
income
assets
investment behavior
```

---

# 181. Multi-Tenant Isolation

Tenant boundary:

```text
tenant
institution
account
portfolio
```

Cross-tenant aggregation chỉ khi capability cho phép.

---

# 182. Data Classification

```text
Public
Internal
Confidential
Restricted
HighlyRestricted
```

---

# 183. Access Control

Access có thể giới hạn theo:

```text
tenant
entity
account
portfolio
asset
market
operation
time
geography
```

---

# 184. Failure Model

Investment operations có các failure:

```text
InvalidSecurity
StalePrice
MissingMarketData
SettlementFailure
LimitViolation
InsufficientLiquidity
InsufficientCash
UnauthorizedAction
ModelUnavailable
OptimizationFailure
NumericalInstability
DataMismatch
```

---

# 185. Numerical Safety

Runtime phải phát hiện:

```text
NaN
Infinity
overflow
underflow
ill-conditioned matrix
non-positive covariance
non-convergent solver
```

---

# 186. Solver Failure

Không được trả một solution sai dưới dạng successful optimization.

Trạng thái:

```text
Optimal
Feasible
Infeasible
Unbounded
Approximate
Timeout
NumericalFailure
```

---

# 187. Market Closure

Market state:

```text
Open
Closed
PreOpen
Auction
Halted
Suspended
Unknown
```

---

# 188. Trading Calendar

Calendar phải hỗ trợ:

```text
holidays
half_days
timezone
market_sessions
auction_sessions
special_closures
```

---

# 189. Time Semantics

Financial timestamp phải phân biệt:

```text
ObservedAt
EffectiveAt
PublishedAt
TradeAt
SettlementAt
AsOf
```

---

# 190. Event Ordering

Events không được giả định global ordering nếu distributed.

Dùng:

```text
event_id
sequence
logical_clock
source_timestamp
ingestion_timestamp
```

---

# 191. Distributed Architecture

```text
Market Data Nodes
       ↓
Security Master
       ↓
Portfolio Engine
       ↓
Risk Cluster
       ↓
Optimization Cluster
       ↓
Execution Boundary
       ↓
Settlement
```

---

# 192. Distributed Consistency

Các dữ liệu cần strong consistency:

```text
order state
execution state
settlement state
cash authorization
position mutation
```

Các dữ liệu có thể eventual:

```text
analytics
research index
derived metrics
non-authoritative dashboards
```

---

# 193. Cache

Cacheable:

```text
market data
security metadata
factor matrices
valuation results
risk calculations
research embeddings
```

Không cache immutable-looking state mà không có version key.

---

# 194. Content Addressing

Dataset:

```text
dataset_hash
model_hash
scenario_hash
result_hash
```

Cho reproducibility.

---

# 195. Native API

```axiom
invest.security(id)
invest.market(id)
invest.portfolio(id)
invest.position(id)
invest.fund(id)

invest.price(...)
invest.value(...)
invest.risk(...)
invest.optimize(...)
invest.simulate(...)
invest.rebalance(...)
```

---

# 196. DSL

Ví dụ:

```axiom
portfolio Growth {
    base USD

    target {
        equity 0.70
        bonds 0.20
        cash 0.10
    }

    limit issuer <= 0.08
    limit sector <= 0.25
    limit leverage <= 1.0
}
```

---

# 197. Research DSL

```axiom
thesis CompanyA {
    claim revenue_growth > 0.10

    evidence revenue_history
    evidence industry_growth

    risk margin_compression
    risk valuation_multiple

    invalidate if revenue_growth < 0.02
}
```

---

# 198. Risk DSL

```axiom
risk Portfolio {
    var 99% horizon 10d
    stress rate +200bp
    stress equity -30%
    stress fx -15%
}
```

---

# 199. Allocation DSL

```axiom
allocation {
    maximize risk_adjusted_return

    constraint equity <= 0.70
    constraint issuer <= 0.05
    constraint liquidity >= 0.15
}
```

---

# 200. Simulation DSL

```axiom
simulate CapitalSystem {
    agents households
    agents banks
    agents funds
    agents firms

    shock rates +200bp
    horizon 10y
}
```

---

# 201. CLI

```text
axiom invest security
axiom invest market
axiom invest portfolio
axiom invest position
axiom invest risk
axiom invest optimize
axiom invest simulate
axiom invest backtest
axiom invest reconcile
axiom invest audit
```

---

# 202. Serialization

Investment schemas phải hỗ trợ:

```text
binary
JSON
CSV
Arrow-like columnar
Parquet-like analytical storage
```

Native binary là canonical runtime format.

---

# 203. Persistent Storage

Các aggregate lớn:

```text
PriceSeries
PositionHistory
TradeHistory
PortfolioSnapshots
RiskHistory
ScenarioResults
```

phải hỗ trợ memory mapping và columnar storage.

---

# 204. Compression

Historical market data nên hỗ trợ:

```text
delta encoding
dictionary encoding
column compression
time-series compression
```

---

# 205. GPU API Boundary

```axiom
risk.compute gpu
optimization.solve gpu
monte_carlo.run gpu
```

Compiler chọn CPU/GPU backend tùy target.

---

# 206. WASM

WASM profile hỗ trợ:

```text
portfolio analytics
financial calculators
research dashboards
simulation subset
```

Không expose privileged trading capabilities mặc định.

---

# 207. Mobile

Mobile profile ưu tiên:

```text
read-only portfolio
analytics
charts
alerts
research
```

Trading capability phải explicit.

---

# 208. Embedded

Có thể compile subset:

```text
AXINVEST_MIN
AXINVEST_PORTFOLIO
AXINVEST_RISK
AXINVEST_ANALYTICS
```

---

# 209. Native Profiles

```text
AXINVEST_NONE
AXINVEST_CORE
AXINVEST_ASSET
AXINVEST_MARKET
AXINVEST_PORTFOLIO
AXINVEST_FUND
AXINVEST_WEALTH
AXINVEST_RISK
AXINVEST_VALUATION
AXINVEST_RESEARCH
AXINVEST_OPTIMIZATION
AXINVEST_SIMULATION
AXINVEST_AI
AXINVEST_DISTRIBUTED
AXINVEST_GPU
AXINVEST_WASM
AXINVEST_MOBILE
AXINVEST_REALTIME
AXINVEST_GLOBAL
AXINVEST_FULL
```

---

# 210. Dependency Graph

```text
AXINVEST.CORE
 ├── AXASSET
 ├── AXSECURITY
 ├── AXMARKET
 ├── AXPORTFOLIO
 ├── AXFUND
 ├── AXRISK
 ├── AXVALUATION
 ├── AXOPT
 ├── AXSIM
 └── AXAI
```

Không module nào được circular dependency với compiler core.

---

# 211. External Boundary

External integrations:

```text
Broker
Exchange
Custodian
FundAdministrator
MarketDataProvider
ResearchProvider
Bank
TaxProvider
Regulator
```

đều thông qua provider interfaces.

---

# 212. No Vendor Lock-In

Core không được phụ thuộc vào:

```text
broker SDK
exchange SDK
database vendor
cloud vendor
GPU vendor
market-data vendor
```

Provider adapters nằm ngoài core.

---

# 213. Backtest Correctness

Automated tests phải kiểm tra:

```text
no lookahead bias
no survivorship bias where dataset supports it
correct corporate actions
correct transaction costs
correct timestamp ordering
correct cash accounting
correct position accounting
```

---

# 214. Accounting Invariants

Phải kiểm tra:

```text
position_quantity >= valid_domain_minimum
portfolio_value ≈ sum(position_values) + cash
NAV consistency
cash conservation
trade conservation
settlement conservation
```

Sai số numerical phải theo tolerance policy.

---

# 215. Conservation

Không được tạo tiền/tài sản từ hư không trong authoritative simulation.

Mọi creation/destruction phải có event semantics rõ ràng:

```text
issuance
redemption
corporate_action
profit
loss
fee
tax
transfer
```

---

# 216. Ownership

Investment system phải phân biệt:

```text
economic_owner
legal_owner
custodian
beneficial_owner
manager
advisor
```

---

# 217. Control vs Ownership

Một investor có thể có:

```text
economic exposure
```

mà không có:

```text
control
```

Runtime không suy luận control chỉ từ position size nếu legal rules yêu cầu dữ liệu khác.

---

# 218. Investment Network Graph

Nodes:

```text
Investor
Fund
Issuer
Security
Bank
Insurer
Project
Government
```

Edges:

```text
owns
invests
borrows
lends
insures
guarantees
exposes
controls
```

---

# 219. Systemic Portfolio Analytics

Có thể tính:

```text
common_exposure
common_factor
network_centrality
concentration
cross-holding
fund_overlap
```

---

# 220. Fund Overlap

```axiom
fund.overlap(other)
```

trả:

```text
shared_security
shared_issuer
shared_sector
shared_factor
```

---

# 221. AI Portfolio Monitoring

AI có thể phát hiện:

```text
unexpected exposure
drift
risk spike
data anomaly
corporate action anomaly
liquidity deterioration
model drift
```

Không được tự động gọi anomaly là fraud.

---

# 222. Fraud Boundary

`FraudSignal` chỉ là signal.

Actual fraud determination thuộc:

```text
AXLAW
AXGOV
authorized compliance workflow
```

---

# 223. Investment Governance

Governance entities:

```text
InvestmentPolicy
Mandate
Committee
Approval
Exception
Breach
Remediation
```

---

# 224. Breach Workflow

```text
Detected
→ Validated
→ Notified
→ Reviewed
→ Approved/Rejected
→ Remediated
→ Closed
```

---

# 225. Exception

Exception phải có:

```text
reason
authority
scope
expiration
approval
audit
```

Không có permanent implicit exception.

---

# 226. Monitoring

Metrics:

```text
AUM
NAV
return
drawdown
volatility
VaR
ES
turnover
fees
cash
liquidity
tracking_error
active_share
exposure
```

---

# 227. AUM

Assets under management phải ghi:

```text
valuation_time
valuation_method
included_accounts
currency
```

AUM không phải net worth của organization.

---

# 228. Dashboard Data

Dashboard values là derived views.

Không được trở thành authoritative financial ledger.

---

# 229. Observability

Tracing:

```text
market_ingestion
valuation
risk
optimization
order
execution
settlement
simulation
AI_reasoning
```

---

# 230. Performance Targets

Mục tiêu architecture:

```text
millions of positions
billions of historical observations
large scenario batches
SIMD valuation
GPU Monte Carlo
distributed optimization
```

Benchmark phải phụ thuộc workload profile.

---

# 231. Latency Classes

```text
REALTIME
INTERACTIVE
BATCH
ANALYTICAL
SIMULATION
OFFLINE
```

---

# 232. Realtime

Realtime workloads:

```text
price update
position update
risk update
limit monitoring
market event
```

---

# 233. Batch

Batch workloads:

```text
NAV
end-of-day valuation
performance
reconciliation
risk reports
```

---

# 234. Analytical

Analytical workloads:

```text
factor analysis
portfolio attribution
historical research
cross-sectional analysis
```

---

# 235. Simulation

Simulation workloads có thể chạy hàng triệu scenarios.

Không được block realtime execution engine.

---

# 236. Deterministic Mode

Dùng cho:

```text
regression tests
accounting
backtest
audit
reconciliation
reproducible simulation
```

---

# 237. Fast Mode

Có thể cho phép:

```text
approximate numerical kernels
GPU nondeterminism
parallel reductions
```

nhưng phải explicit.

---

# 238. Exact Mode

Dùng:

```text
Decimal
FixedPoint
Rational
deterministic rounding
```

cho financial authority-sensitive calculations.

---

# 239. Numerical Policy

```axiom
numeric_policy authoritative {
    money = decimal
    rounding = half_even
    deterministic = true
}
```

---

# 240. API Safety

API phải tránh:

```text
execute()
```

là operation duy nhất.

Tách:

```text
propose()
approve()
execute()
settle()
reconcile()
```

---

# 241. Two-Phase Financial Action

```text
Proposal
→ Authorization
→ Execution
```

---

# 242. Multi-Signature Approval

Institutional actions có thể yêu cầu:

```text
2-of-3
3-of-5
role_based
committee_based
```

Authorization layer thuộc capability/security runtime.

---

# 243. Investment Event Bus

Events:

```text
PriceUpdated
OrderCreated
OrderFilled
TradeBooked
SettlementCompleted
PositionChanged
NAVCalculated
RiskChanged
LimitBreached
AllocationProposed
ApprovalRequested
```

---

# 244. Event Consumers

Có thể có:

```text
RiskEngine
Dashboard
AIAnalyst
ComplianceEngine
AccountingBridge
NotificationService
SimulationMirror
```

---

# 245. Event Idempotency

Mọi financial event processing phải có:

```text
event_id
idempotency_key
source
version
```

---

# 246. Duplicate Protection

Không được double-book:

```text
trade
execution
settlement
dividend
fee
corporate action
```

---

# 247. Reprocessing

Event processors phải hỗ trợ:

```text
replay
checkpoint
rollback
reconciliation
```

---

# 248. Recovery

Sau crash:

```text
restore snapshot
replay events
reconcile external state
resume
```

---

# 249. Disaster Recovery

Hỗ trợ:

```text
checkpoint
replication
journal
immutable audit
cross-region recovery
```

---

# 250. Data Retention

Retention policy configurable theo:

```text
market_data
orders
trades
settlement
research
audit
model
simulation
```

---

# 251. Deletion

Authoritative financial records không được xóa tùy tiện.

Deletion request có thể chuyển thành:

```text
retention restriction
redaction
cryptographic erasure of eligible data
```

theo policy layer.

---

# 252. Testing Architecture

Các test classes:

```text
unit
property
invariant
numerical
determinism
simulation
integration
distributed
security
performance
reconciliation
recovery
AI evaluation
```

---

# 253. Property Tests

Ví dụ:

```text
sum(allocation) == 1
```

trong tolerance.

```text
portfolio_value =
    cash + sum(position_values)
```

theo valuation snapshot.

---

# 254. Numerical Tests

Test:

```text
precision
rounding
overflow
underflow
conditioning
solver convergence
```

---

# 255. Financial Scenario Tests

Test:

```text
market crash
rate shock
FX shock
default
liquidity freeze
corporate action
mass redemption
capital call
```

---

# 256. AI Evaluation

AI investment systems được đánh giá về:

```text
factuality
calibration
data provenance
lookahead leakage
hallucination
constraint compliance
explanation fidelity
action authorization
```

Không dùng performance backtest đơn độc để chứng minh AI "đúng".

---

# 257. Security Tests

Test:

```text
unauthorized trade
cross-tenant access
capability escalation
audit tampering
order replay
settlement replay
data leakage
agent privilege escalation
```

---

# 258. Reconciliation Tests

Synthetic external providers phải tạo:

```text
matched
missing
duplicate
stale
incorrect_quantity
incorrect_price
```

và engine phải phân loại chính xác.

---

# 259. Minimum Test Target

`AXINVEST` phải đạt tối thiểu:

```text
18,000 automated tests
1,500 architecture invariants
```

trước khi tuyên bố `AXINVEST 5.0` production-ready.

---

# 260. Architecture Invariants

Một số invariant bắt buộc:

```text
INV-001:
Price != Value

INV-002:
Recommendation != Execution

INV-003:
Forecast != Fact

INV-004:
Simulation != ProductionState

INV-005:
Execution != Settlement

INV-006:
Settlement != CustodyAuthority

INV-007:
NAV != MarketPrice

INV-008:
RiskEstimate != ActualLoss

INV-009:
ModelOutput requires provenance

INV-010:
Authoritative money calculations require explicit numeric policy

INV-011:
Unauthorized agent cannot execute financial action

INV-012:
Historical backtest cannot consume future information

INV-013:
Financial event processing is idempotent

INV-014:
Corrections append events instead of mutating history

INV-015:
Optimization failure cannot produce successful solution

INV-016:
Unknown compliance state != Pass

INV-017:
Portfolio snapshots are immutable

INV-018:
External provider data != canonical authority by default

INV-019:
Cross-tenant investment data requires explicit capability

INV-020:
Simulation output cannot mutate live state implicitly
```

---

# 261. Compiler Integration

Compiler phải hiểu các semantic types:

```text
Money
Currency
SecurityId
PortfolioId
Quantity
Price
Rate
Probability
Duration
Timestamp
```

---

# 262. Type Safety

Không cho implicit:

```text
Money<USD> + Money<EUR>
```

Phải:

```axiom
convert(EUR, USD, fx_rate)
```

---

# 263. Dimensional Safety

Compiler có thể kiểm tra:

```text
price * quantity = money
money / money = dimensionless
money / time = rate
```

---

# 264. Compile-Time Financial Units

```axiom
type USD = Money<USD>
type EUR = Money<EUR>

type Rate = Ratio
type Probability = Ratio<0,1>
```

---

# 265. Generic Financial Algorithms

Algorithms phải generic trên:

```text
Currency
Precision
RiskModel
ValuationModel
ExecutionModel
```

---

# 266. Zero-Copy

Market data pipelines nên hỗ trợ:

```text
memory map
shared memory
borrowed immutable views
column views
SIMD slices
```

Nhưng không bắt programmer quản lý pointer/reference complexity thủ công trong ordinary application code.

---

# 267. Ownership Model

Axiom memory semantics tiếp tục dùng native value/region/arena semantics.

Investment runtime không yêu cầu GC.

Long-lived objects có thể dùng:

```text
arena
pool
region
persistent snapshot
```

---

# 268. Persistent Portfolio

Portfolio snapshot có thể:

```text
share immutable backing storage
copy-on-write modifications
```

giảm memory duplication.

---

# 269. Parallel Portfolio

```axiom
parallel for position in portfolio.positions {
    evaluate(position)
}
```

Compiler có thể vectorize hoặc distribute.

---

# 270. GPU Portfolio

```axiom
gpu for scenario in scenarios {
    evaluate(portfolio, scenario)
}
```

---

# 271. Actor Integration

Investment services có thể chạy như actors:

```text
MarketActor
PortfolioActor
RiskActor
ExecutionActor
SettlementActor
```

---

# 272. Async

Async được dùng cho:

```text
market feeds
broker APIs
custody
research sources
distributed simulation
```

Không biến toàn bộ numerical computation thành async.

---

# 273. Concurrency

Data model ưu tiên:

```text
immutable snapshots
message passing
atomic counters
partition ownership
lock-minimized structures
```

---

# 274. Lock-Free Market Data

High-frequency feed ingestion có thể dùng:

```text
ring buffer
single-writer
multi-reader
atomic sequence
```

---

# 275. Snapshot Consistency

Risk engine phải tính trên một coherent snapshot:

```text
market_snapshot
portfolio_snapshot
fx_snapshot
model_snapshot
```

---

# 276. Versioned State

```text
PortfolioVersion
MarketVersion
ModelVersion
PolicyVersion
```

Risk result references exact versions.

---

# 277. Global Investment State

Global state không được tồn tại như một mutable singleton.

Dùng:

```text
versioned state
partitioned state
event stream
```

---

# 278. Configuration

Investment configuration phải tách:

```text
runtime config
market config
risk config
policy config
model config
execution config
```

---

# 279. Secret Handling

Broker credentials:

```text
secret reference
```

không nằm plaintext trong portfolio/order object.

---

# 280. Auditability

Một investment decision phải có thể tái dựng:

```text
what data existed
what model ran
what assumptions existed
what constraints existed
what recommendation was produced
who/what approved
what execution occurred
```

---

# 281. Explainability

AI recommendation có thể yêu cầu:

```text
evidence
assumptions
uncertainty
counterarguments
sensitivity
constraint effects
```

---

# 282. Counterfactual Analysis

```axiom
portfolio.counterfactual(
    change = sector_weight -0.05
)
```

trả:

```text
risk_change
return_distribution_change
liquidity_change
constraint_change
```

---

# 283. Decision Record

Investment decision:

```text
DecisionRecord {
    objective
    alternatives
    evidence
    assumptions
    risks
    constraints
    selected_action
    authorization
}
```

---

# 284. Human-AI Collaboration

AI có thể:

```text
discover
analyze
simulate
propose
explain
monitor
```

Human hoặc authorized controller quyết định execution tùy mandate.

---

# 285. Investment Agent Society

Nhiều agents:

```text
ResearchAgent
RiskAgent
PortfolioAgent
ExecutionAgent
ComplianceAgent
OperationsAgent
```

có thể phối hợp nhưng capability isolation bắt buộc.

---

# 286. Agent Negotiation

Agents có thể trao đổi:

```text
proposal
counterproposal
constraint
evidence
approval
```

Không được tự cấp thêm capability.

---

# 287. Agent Reputation

Agent performance có thể lưu:

```text
forecast_accuracy
calibration
constraint_violations
data_quality
decision_outcomes
```

Nhưng metric không tự động cấp quyền execution.

---

# 288. Learning Loop

```text
Prediction
→ Outcome
→ Evaluation
→ Calibration
→ ModelUpdate
→ Validation
→ Approval
→ Production
```

Không tự động deploy model mới vào production.

---

# 289. Model Promotion

```text
Experimental
→ Evaluated
→ Validated
→ Approved
→ Production
```

---

# 290. Shadow Mode

Model mới có thể chạy:

```text
shadow
```

song song production mà không được execute.

---

# 291. Canary

Investment model deployment có thể:

```text
small scope
limited portfolio
limited users
read-only
```

trước production.

---

# 292. Rollback

Model registry phải hỗ trợ:

```text
rollback(previous_version)
```

---

# 293. Benchmark Suite

Benchmark:

```text
portfolio_valuation
risk_10k_assets
risk_1m_assets
monte_carlo_1m_paths
optimization_10k_assets
historical_backtest
order_pipeline
reconciliation
```

---

# 294. Memory Benchmark

Đo:

```text
bytes/position
bytes/security
bytes/price
snapshot_size
cache_hit_rate
```

---

# 295. CPU Benchmark

Đo:

```text
valuation/sec
risk/sec
scenario/sec
orders/sec
events/sec
```

---

# 296. GPU Benchmark

Đo:

```text
paths/sec
portfolio-scenarios/sec
matrix throughput
optimization throughput
```

---

# 297. Distributed Benchmark

Đo:

```text
horizontal scaling
network overhead
partition skew
recovery time
checkpoint time
```

---

# 298. Failure Injection

Chaos tests:

```text
market feed disconnect
broker disconnect
custodian mismatch
database failure
node crash
network partition
stale prices
duplicate events
```

---

# 299. Recovery Guarantee

Sau recovery:

```text
no duplicate settlement
no lost authoritative event
no silent position mutation
no unauthorized execution
```

---

# 300. Reference Architecture

```text
                ┌──────────────────────┐
                │      AXCIVILIZATION  │
                └──────────┬───────────┘
                           │
                  ┌────────▼────────┐
                  │     AXINVEST    │
                  └────────┬────────┘
                           │
       ┌───────────────────┼────────────────────┐
       │                   │                    │
   Securities          Portfolio             Funds
       │                   │                    │
    Markets             Risk                 Wealth
       │                   │                    │
   Orders             Valuation            Allocation
       │                   │                    │
 Execution           Optimization          Capital
       │                   │                    │
 Settlement          Simulation             Research
       └───────────────────┼────────────────────┘
                           │
                    Investment AI
                           │
          ┌────────────────┼────────────────┐
          │                │                │
      AXFINANCE        AXBANKING       AXINSURANCE
          │                │                │
          └────────────────┼────────────────┘
                           │
        AXCOMMERCE / AXLABOR / AXHOUSING
                           │
        AXMANUFACTURING / AXAGRI / AXTRANSPORT
                           │
                     AXCIVILIZATION
```

---

# 301. Economic Feedback Loop

```text
SAVINGS
   ↓
CAPITAL
   ↓
INVESTMENT
   ↓
ENTERPRISE
   ↓
PRODUCTION
   ↓
INCOME
   ↓
SAVINGS
```

Risk feedback:

```text
RISK
 ↓
INSURANCE
 ↓
CAPITAL PROTECTION
 ↓
INVESTMENT
 ↓
PRODUCTION
```

---

# 302. Civilization Capital Loop

```text
HOUSEHOLDS
   ↓
BANKS / FUNDS
   ↓
CAPITAL MARKETS
   ↓
COMPANIES / PROJECTS
   ↓
INFRASTRUCTURE / PRODUCTION
   ↓
EMPLOYMENT
   ↓
INCOME
   ↓
HOUSEHOLDS
```

Các domain trước đó trở thành interconnected economic runtime.

---

# 303. Integration Contract

`AXINVEST` phải tích hợp với:

```text
AXFINANCE
AXBANKING
AXINSURANCE
AXCOMMERCE
AXLABOR
AXHOUSING
AXCONSTRUCTION
AXMANUFACTURING
AXAGRI
AXTRANSPORT
AXRESOURCE
AXSCIENCE
AXLAW
AXGOV
AXCIVILIZATION
```

---

# 304. Explicit Non-Goals

`AXINVEST` không trực tiếp trở thành:

```text
general ledger
banking core
insurance claims engine
legal authority
tax authority
exchange matching engine
custodian of record
government regulator
```

Các hệ thống này được tích hợp qua contract.

---

# 305. Minimal Core

Nếu build profile cực nhỏ:

```text
AXINVEST_CORE
    Asset
    Security
    Price
    Position
    Portfolio
    Cash
    Valuation
    Return
```

Các module còn lại optional.

---

# 306. Full Civilization Profile

```text
AXINVEST_FULL
```

bao gồm:

```text
markets
funds
portfolio
wealth
risk
valuation
research
optimization
simulation
AI
distributed
GPU
governance
provenance
```

---

# 307. Compiler Requirement

Compiler phải:

1. type-check financial dimensions;
2. preserve numeric precision;
3. specialize portfolio kernels;
4. vectorize batch calculations;
5. lower GPU kernels;
6. preserve provenance metadata;
7. optimize immutable snapshots;
8. eliminate unused modules;
9. support deterministic builds;
10. produce native binaries without third-party compiler dependency.

---

# 308. Runtime Requirement

Runtime phải:

1. không yêu cầu GC;
2. không yêu cầu heavyweight VM;
3. hỗ trợ native CPU;
4. hỗ trợ GPU;
5. hỗ trợ distributed execution;
6. hỗ trợ memory mapping;
7. hỗ trợ persistent snapshots;
8. hỗ trợ deterministic simulation;
9. hỗ trợ audit;
10. hỗ trợ capability isolation.

---

# 309. AI-Native Requirement

AI phải được coi là native computational participant:

```text
Model
Agent
Evidence
Prediction
Scenario
Decision
Outcome
Calibration
```

đều là first-class entities.

---

# 310. Safety Requirement

Không có đường tắt:

```text
AI → unrestricted money transfer
AI → unrestricted trade execution
AI → policy bypass
AI → audit deletion
AI → cross-tenant financial data
```

---

# 311. Final Architecture Contract

`AXINVEST 5.0` định nghĩa một native financial intelligence layer có khả năng:

```text
represent assets
represent securities
represent markets
represent positions
represent portfolios
represent funds
represent investors
represent wealth
represent investment mandates
represent risk
represent valuation
represent research
represent capital allocation
represent optimization
represent simulation
represent AI investment agents
represent civilization-scale capital flows
```

và biến chúng thành native computational primitives của Axiom.

---

# 312. Completion Criteria

BOOTSTRAP-692 được coi là hoàn thành khi:

```text
[✓] Asset model
[✓] Security model
[✓] Market model
[✓] Order model
[✓] Execution model
[✓] Settlement boundary
[✓] Portfolio model
[✓] Fund model
[✓] Wealth model
[✓] Risk model
[✓] Valuation model
[✓] Research model
[✓] Optimization model
[✓] Capital allocation
[✓] Simulation
[✓] AI integration
[✓] Provenance
[✓] Governance
[✓] Capability security
[✓] Distributed execution
[✓] GPU execution
[✓] Native IR
[✓] Compiler integration
[✓] Numerical safety
[✓] Reconciliation
[✓] Recovery
[✓] Test architecture
```

---

# 313. Final Dependency Chain

```text
PHYSICAL WORLD
      ↓
RESOURCE
      ↓
AGRICULTURE
      ↓
MANUFACTURING
      ↓
CONSTRUCTION
      ↓
HOUSING
      ↓
TRANSPORT
      ↓
COMMERCE
      ↓
LABOR
      ↓
FINANCE
      ↓
BANKING
      ↓
INSURANCE
      ↓
INVESTMENT
      ↓
CAPITAL ALLOCATION
      ↓
CIVILIZATION
```

Và feedback:

```text
CIVILIZATION
    ↓
SAVINGS
    ↓
CAPITAL
    ↓
INVESTMENT
    ↓
PRODUCTION
    ↓
EMPLOYMENT
    ↓
INCOME
    ↓
CONSUMPTION
    ↓
SAVINGS
```

---

# 314. BOOTSTRAP-692 Final Status

```text
STATUS: ARCHITECTURALLY COMPLETE

NAMESPACE:
    AXINVEST

TEST TARGET:
    >= 18,000 automated tests

ARCHITECTURE INVARIANTS:
    >= 1,500

PRIMARY OUTPUT:
    Native Investment & Capital Allocation Runtime 5.0
```

---

# 315. Next Bootstrap

```text
BOOTSTRAP-693
Native AI Civilization-Scale Accounting, General Ledger,
Financial Reporting, Tax Computation, Treasury, Corporate Finance,
Audit, Consolidation & Global Financial Truth Runtime 5.0
```

Mục tiêu tiếp theo là xây lớp **financial truth/accounting authority** bên dưới `AXBANKING + AXINSURANCE + AXINVEST`, đặc biệt tách rõ `economic event → accounting event → ledger → reporting → tax → audit`, để hệ thống tài chính của Axiom có một nguồn sự thật có thể đối soát ở quy mô civilization.
:::

BOOTSTRAP-692 hoàn tất. Chuỗi tiếp tục tự động sang **BOOTSTRAP-693 — Accounting, General Ledger, Financial Reporting, Tax, Treasury, Corporate Finance & Audit Runtime 5.0**.