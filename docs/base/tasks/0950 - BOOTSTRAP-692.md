Tiếp tục với **BOOTSTRAP-692**. Đây là lớp nối trực tiếp `AXFINANCE → AXBANKING → AXINSURANCE` sang hệ thống đầu tư và phân bổ vốn ở quy mô cá nhân, doanh nghiệp, quỹ và toàn nền kinh tế.

:::writing{variant="document" id="58321" title="BOOTSTRAP-692 — Native AI Civilization-Scale Investment, Asset Management, Wealth Management, Funds, Securities, Portfolio Optimization, Capital Allocation & Global Investment Runtime 5.0"}

# BOOTSTRAP-692
## Native AI Civilization-Scale Investment, Asset Management, Wealth Management, Funds, Securities, Portfolio Optimization, Capital Allocation & Global Investment Runtime 5.0

**Status:** Architecture Specification  
**Version:** 5.0  
**Namespace:** `AXINVEST`  
**Layer:** Civilization Economy / Capital Allocation  
**Primary role:** biến vốn nhàn rỗi, tài sản, nghĩa vụ tài chính và cơ hội đầu tư thành các cấu trúc phân bổ vốn có thể mô hình hóa, thực thi, giám sát, tối ưu và mô phỏng trực tiếp trong Axiom.

---

# 1. Mục tiêu

`AXINVEST` là runtime native của Axiom cho:

- đầu tư cá nhân;
- quản lý tài sản;
- quản lý tài sản của tổ chức;
- wealth management;
- portfolio management;
- asset management;
- quỹ đầu tư;
- quỹ hưu trí;
- sovereign wealth;
- endowment;
- treasury investment;
- securities;
- bonds;
- equities;
- funds;
- ETFs;
- private assets;
- real assets;
- alternative investments;
- capital allocation;
- portfolio optimization;
- risk budgeting;
- asset allocation;
- liability-aware investment;
- factor investing;
- quantitative investing;
- systematic investing;
- investment research;
- investment AI;
- investment simulation;
- financial digital twins.

`AXINVEST` không phải là sàn giao dịch.

Market infrastructure, exchange, brokerage execution, clearing và settlement chuyên biệt thuộc lớp tiếp theo `AXMARKET`.

---

# 2. Vị trí kiến trúc

```text
PHYSICAL WORLD
      │
RESOURCE
      │
PRODUCTION
      │
COMMERCE
      │
LABOR
      │
FINANCE
      │
BANKING
      │
INSURANCE
      │
INVESTMENT
      │
CAPITAL MARKETS
      │
CIVILIZATION
```

Luồng vốn:

```text
SAVINGS
   ↓
CAPITAL
   ↓
INVESTMENT OPPORTUNITY
   ↓
ALLOCATION
   ↓
ASSET
   ↓
RETURN / CASHFLOW
   ↓
PORTFOLIO
   ↓
WEALTH
   ↓
REINVESTMENT
```

Feedback:

```text
CIVILIZATION
    ↓
INCOME
    ↓
SAVINGS
    ↓
CAPITAL
    ↓
INVESTMENT
    ↓
ENTERPRISE / INFRASTRUCTURE
    ↓
PRODUCTION
    ↓
INCOME
```

---

# 3. Dependency graph

`AXINVEST` phụ thuộc:

```text
AXFINANCE
AXBANKING
AXINSURANCE
AXCOMMERCE
AXLABOR
AXLAW
AXGOV
AX670
AX671
AX672
AX674
AXHOUSING
AXMANUFACTURING
AXCONSTRUCTION
AXTRANSPORT
AXRESOURCE
AXAGRI
```

Đồng thời cung cấp capability cho:

```text
AXMARKET
AXCIVILIZATION
AXAI
AXSIMULATION
AXTREASURY
```

---

# 4. Boundary contract

## 4.1 AXINVEST sở hữu

```text
Portfolio
Asset
Position
Holding
InvestmentMandate
InvestmentStrategy
Allocation
RiskBudget
ReturnModel
ValuationModel
Fund
NAV
Investor
Beneficiary
Account
InvestmentPlan
RebalancingPlan
CapitalAllocation
InvestmentOpportunity
InvestmentDecision
InvestmentOrderIntent
PerformanceAttribution
InvestmentSimulation
InvestmentTwin
```

## 4.2 AXINVEST không sở hữu

| Domain | Owner |
|---|---|
| tiền và ledger authority | AXFINANCE |
| tiền gửi và credit account | AXBANKING |
| insurance contract | AXINSURANCE |
| legal ownership authority | AXLAW |
| government authority | AXGOV |
| exchange matching | AXMARKET |
| clearing | AXMARKET |
| settlement network | AXMARKET |
| physical property | AXHOUSING / domain owner |
| company operational state | AXCOMMERCE / AXMANUFACTURING |
| healthcare asset semantics | AX674 |

---

# 5. Critical semantic distinctions

Axiom MUST preserve:

```text
Asset ≠ Position
Position ≠ OwnershipRecord
Investment ≠ Payment
OrderIntent ≠ ExecutedOrder
Execution ≠ Settlement
Price ≠ Value
Value ≠ Return
Return ≠ Profit
Risk ≠ Loss
Forecast ≠ Actual
Prediction ≠ Decision
Recommendation ≠ Authorization
Allocation ≠ Execution
Simulation ≠ ProductionState
NAV ≠ MarketPrice
Fund ≠ Portfolio
Portfolio ≠ Account
Investor ≠ Beneficiary
Strategy ≠ Mandate
RiskBudget ≠ RiskLimit
Liquidity ≠ Solvency
Performance ≠ Skill
ModelOutput ≠ FinancialTruth
```

Đây là các invariant nền tảng của runtime.

---

# 6. Investor model

Các actor:

```text
Investor
IndividualInvestor
InstitutionalInvestor
Fund
Trust
PensionFund
Endowment
Foundation
FamilyOffice
SovereignFund
CorporateTreasury
InsuranceInvestor
BankInvestor
GovernmentInvestor
InvestmentAgent
PortfolioManager
Advisor
ResearchAgent
RiskManager
Custodian
```

Không được đồng nhất:

```text
Human
Investor
AccountHolder
BeneficialOwner
AuthorizedAgent
```

Một người có thể:

```text
Human
 ├── Investor
 ├── Beneficiary
 └── AuthorizedAgent
```

nhưng các quyền là độc lập.

---

# 7. Asset model

Base abstraction:

```text
Asset
```

Subtypes:

```text
CashAsset
Equity
DebtSecurity
Bond
GovernmentBond
CorporateBond
MunicipalBond
MoneyMarketInstrument
FundUnit
ETFUnit
REIT
Commodity
CommodityContractRef
RealEstateAssetRef
InfrastructureAssetRef
PrivateEquity
VentureCapital
PrivateDebt
DerivativeRef
DigitalAssetRef
IntellectualPropertyAssetRef
CollectibleAssetRef
OtherAlternativeAsset
```

Physical asset không nhất thiết được copy vào `AXINVEST`.

Thay vào đó:

```text
InvestmentAssetRef
    ├── external_owner
    ├── legal_owner_ref
    ├── valuation_ref
    └── economic_exposure
```

---

# 8. Asset identity

Mọi asset phải có identity ổn định:

```text
AssetId
IssuerId
InstrumentId
ClassId
Currency
Jurisdiction
Lifecycle
```

Ví dụ:

```axiom
asset Equity {
    instrument_id: InstrumentId
    issuer: EntityId
    currency: Currency
    class: SecurityClass
}
```

---

# 9. Position model

`Position` biểu diễn exposure của một portfolio đối với asset.

```axiom
struct Position {
    asset: AssetRef
    quantity: Decimal
    cost_basis: Money
    market_value: Money
    unrealized_pnl: Money
    realized_pnl: Money
}
```

Position không phải ownership certificate.

---

# 10. Holding model

```text
Holding
```

là trạng thái nắm giữ có provenance:

```text
Holding
 ├── asset
 ├── quantity
 ├── acquisition
 ├── custody
 ├── legal_owner
 ├── beneficial_owner
 ├── restrictions
 └── provenance
```

---

# 11. Portfolio

```axiom
struct Portfolio {
    id: PortfolioId
    base_currency: Currency
    positions: PositionSet
    cash: CashBalance
    mandate: InvestmentMandateRef
    risk_budget: RiskBudgetRef
}
```

Portfolio có:

```text
positions
cash
liabilities
constraints
mandate
risk policy
benchmark
```

---

# 12. Portfolio hierarchy

Cho phép:

```text
Portfolio
 ├── Sleeve
 │    ├── Strategy
 │    └── Positions
 ├── Sleeve
 └── Sleeve
```

Ví dụ:

```text
Global Portfolio
├── Equity
├── Fixed Income
├── Real Estate
├── Commodity
├── Private Markets
└── Cash
```

Nested portfolio phải hỗ trợ.

---

# 13. Account

```text
InvestmentAccount
CustodyAccount
ManagedAccount
FundAccount
SubAccount
```

Account là container vận hành.

Không được suy ra:

```text
Account == Portfolio
```

Một account có thể chứa nhiều portfolio.

---

# 14. Investment mandate

Mandate định nghĩa phạm vi được phép đầu tư.

```axiom
struct InvestmentMandate {
    allowed_assets: AssetSet
    excluded_assets: AssetSet
    target_allocation: AllocationPolicy
    risk_limit: RiskLimit
    liquidity_requirement: LiquidityConstraint
    horizon: TimeHorizon
    benchmark: BenchmarkRef
}
```

Mandate không tự động tạo transaction.

---

# 15. Investment strategy

Strategy mô tả cách phân bổ.

Các strategy primitive:

```text
Passive
Active
Value
Growth
Momentum
Quality
Income
Factor
IndexTracking
MarketNeutral
LongOnly
LongShort
RiskParity
MinimumVariance
MaximumDiversification
TrendFollowing
GlobalMacro
EventDriven
Arbitrage
Statistical
Quantitative
Systematic
Discretionary
```

Strategy chỉ là policy.

Không phải execution engine.

---

# 16. Investment objective

```text
Objective
```

có thể bao gồm:

```text
maximize_return
minimize_risk
maximize_risk_adjusted_return
track_benchmark
preserve_capital
generate_income
match_liabilities
maintain_liquidity
fund_future_expense
maximize_real_wealth
```

Một portfolio có thể có nhiều objective với trọng số.

---

# 17. Time horizon

```text
Intraday
ShortTerm
MediumTerm
LongTerm
MultiDecade
Perpetual
```

Không được coi horizon là guarantee.

---

# 18. Return model

Axiom phải phân biệt:

```text
AbsoluteReturn
RelativeReturn
RealReturn
NominalReturn
TotalReturn
CashReturn
IncomeReturn
CapitalGain
RiskAdjustedReturn
```

---

# 19. Performance measurement

Core metrics:

```text
Return
Volatility
Drawdown
MaxDrawdown
SharpeRatio
SortinoRatio
CalmarRatio
TrackingError
InformationRatio
Beta
AlphaEstimate
VaR
CVaR
Turnover
LiquidityCost
TransactionCost
```

Các metric là measurement hoặc estimate tùy provenance.

---

# 20. Valuation

```text
MarketPrice
FairValueEstimate
ModelValue
BookValue
NetAssetValue
LiquidationValue
ReplacementValue
IntrinsicValueEstimate
```

Không được đồng nhất:

```text
MarketPrice == FairValue
```

---

# 21. Valuation provenance

Mỗi valuation phải có:

```text
source
timestamp
method
currency
confidence
market_status
model_version
```

Ví dụ:

```axiom
valuation {
    method: discounted_cash_flow
    value: 125.40 USD
    source: model("DCF-v4")
    status: estimated
}
```

---

# 22. Fund

```axiom
struct Fund {
    id: FundId
    strategy: StrategyRef
    assets: PortfolioRef
    units: UnitRegistry
    nav: NAV
    mandate: InvestmentMandateRef
}
```

Fund lifecycle:

```text
Proposed
→ Forming
→ Open
→ Investing
→ Mature
→ Closing
→ Liquidating
→ Closed
```

---

# 23. Fund types

```text
MutualFund
ETF
IndexFund
HedgeFund
PrivateEquityFund
VentureFund
PrivateDebtFund
RealEstateFund
InfrastructureFund
PensionFund
EndowmentFund
SovereignFund
MoneyMarketFund
TargetDateFund
FundOfFunds
```

---

# 24. NAV

NAV:

```text
NAV = assets - liabilities
```

Runtime phải hỗ trợ:

```text
GrossNAV
NetNAV
UnitNAV
EstimatedNAV
OfficialNAV
```

`OfficialNAV` có thể yêu cầu external authority.

---

# 25. Unit accounting

```text
FundUnit
UnitClass
UnitPrice
Subscription
Redemption
Distribution
```

Các unit class có thể có:

```text
fee
currency
distribution_policy
minimum_investment
investor_eligibility
```

---

# 26. Wealth management

`AXINVEST` hỗ trợ:

```text
WealthProfile
WealthPlan
Goal
GoalFunding
CashFlowPlan
TaxConstraintRef
EstateConstraintRef
RiskProfile
LiquidityProfile
```

Nhưng tax/legal authority thuộc domain tương ứng.

---

# 27. Financial goal

```axiom
struct InvestmentGoal {
    id: GoalId
    target_amount: Money
    target_date: Date
    probability_target: Ratio
    priority: Integer
}
```

Ví dụ:

```text
retirement
education
home
emergency_reserve
capital_preservation
legacy
```

---

# 28. Goal planning

Runtime có thể tính:

```text
required_savings
required_return
funding_gap
probability_of_success
shortfall_distribution
```

Nhưng không được biến simulation thành guarantee.

---

# 29. Liability-aware investing

Portfolio có thể liên kết liabilities:

```text
Liability
CashFlow
DueDate
RequiredLiquidity
FundingRatio
```

Ví dụ:

```text
PensionAssets
        ↓
PensionLiabilities
        ↓
ALMPortfolio
```

---

# 30. Asset allocation

Allocation levels:

```text
Strategic Asset Allocation
Tactical Asset Allocation
Dynamic Asset Allocation
Security Selection
```

Hierarchy:

```text
Mandate
  ↓
Strategic Allocation
  ↓
Tactical Allocation
  ↓
Strategy
  ↓
Security Selection
  ↓
Execution Intent
```

---

# 31. Allocation representation

```axiom
allocation {
    equity: 0.60
    bond: 0.25
    real_asset: 0.10
    cash: 0.05
}
```

Runtime phải validate:

```text
sum(weights) == 1
```

trừ khi portfolio cho phép leverage hoặc cash deficit.

---

# 32. Constraints

Các constraint primitive:

```text
MinWeight
MaxWeight
RangeWeight
GrossExposure
NetExposure
LeverageLimit
TurnoverLimit
LiquidityLimit
ConcentrationLimit
IssuerLimit
SectorLimit
CountryLimit
CurrencyLimit
DurationLimit
CreditQualityLimit
DrawdownLimit
TrackingErrorLimit
```

---

# 33. Hard vs soft constraints

```text
HardConstraint
SoftConstraint
Preference
Objective
```

Hard constraint không được vi phạm.

Soft constraint có penalty.

---

# 34. Optimization

Optimization engine hỗ trợ:

```text
MeanVariance
BlackLitterman
RiskParity
MinimumVariance
MaximumSharpe
MaximumDiversification
CVaROptimization
FactorOptimization
LiabilityAwareOptimization
RobustOptimization
MultiObjectiveOptimization
```

---

# 35. Optimization contract

Optimizer:

```text
Input
 ├── assets
 ├── expected_returns
 ├── covariance
 ├── constraints
 ├── risk_model
 └── objective

Output
 └── AllocationProposal
```

Output không tự động execute.

---

# 36. AllocationProposal

```axiom
struct AllocationProposal {
    target_weights: WeightVector
    expected_return: Estimate
    expected_risk: Estimate
    constraint_status: ConstraintReport
    model: ModelRef
    provenance: Provenance
}
```

---

# 37. Risk budget

Risk budget có thể phân bổ theo:

```text
asset
strategy
sector
country
factor
liquidity
counterparty
currency
duration
```

Ví dụ:

```text
PortfolioRisk
├── EquityRisk
├── RateRisk
├── CreditRisk
├── FXRisk
├── LiquidityRisk
└── AlternativeRisk
```

---

# 38. Factor exposure

Core factor abstraction:

```text
Factor
FactorExposure
FactorReturn
FactorRisk
FactorConstraint
```

Các factor có thể gồm:

```text
Market
Size
Value
Momentum
Quality
Volatility
Liquidity
Rates
Credit
Inflation
Commodity
Currency
```

Factor registry phải extensible.

---

# 39. Correlation model

Hỗ trợ:

```text
CovarianceMatrix
CorrelationMatrix
FactorCovariance
ScenarioCorrelation
RegimeCorrelation
```

Không giả định correlation cố định.

---

# 40. Regime model

Investment simulation có thể định nghĩa:

```text
Bull
Bear
HighInflation
LowInflation
HighRates
LowRates
Recession
Expansion
Crisis
LiquidityStress
CustomRegime
```

Regime là simulation abstraction.

Không được ghi đè lên actual economic state.

---

# 41. Scenario

```axiom
scenario "rates_up" {
    rate_curve.shift(+2%)
    equity.multiplier(0.85)
    credit_spread.shift(+150bp)
}
```

Scenario chỉ tác động simulation.

---

# 42. Monte Carlo

Native engine:

```text
MonteCarlo
PathSimulation
BootstrapSimulation
FactorSimulation
RegimeSimulation
```

Phải hỗ trợ:

```text
seed
deterministic_mode
parallel_execution
GPU_execution
checkpoint
replay
```

---

# 43. Simulation result

```axiom
SimulationResult {
    paths
    statistics
    percentiles
    tail_metrics
    seed
    model_version
}
```

SimulationResult không phải financial fact.

---

# 44. Risk metrics

Core:

```text
VaR
CVaR
ExpectedShortfall
StressLoss
MaximumDrawdown
LiquidityAtRisk
ConcentrationRisk
CounterpartyExposure
FactorRisk
TailRisk
```

Mỗi metric phải mang:

```text
method
horizon
confidence
sample
model
timestamp
```

---

# 45. Liquidity model

Liquidity không chỉ là cash.

Runtime phải mô hình hóa:

```text
CashLiquidity
MarketLiquidity
FundingLiquidity
RedemptionLiquidity
AssetLiquidity
EmergencyLiquidity
```

---

# 46. Liquidity buckets

```text
Immediate
T+1
T+2
T+5
T+30
T+90
LongTerm
Illiquid
```

Có thể gắn haircut và liquidation cost.

---

# 47. Concentration

Phải phát hiện:

```text
single_asset
single_issuer
sector
country
currency
counterparty
strategy
factor
```

Concentration engine trả:

```text
Exposure
Limit
Utilization
Breach
```

---

# 48. Rebalancing

Lifecycle:

```text
Detected
→ Proposed
→ Reviewed
→ Approved
→ Planned
→ SentForExecution
→ Executed
→ Settled
→ Reconciled
```

`AXINVEST` dừng ở execution intent boundary.

---

# 49. Rebalance triggers

```text
Calendar
Threshold
Drift
RiskBreach
LiquidityEvent
LiabilityChange
MandateChange
MarketEvent
InvestorInstruction
```

---

# 50. Drift

```text
drift = actual_weight - target_weight
```

Runtime phải hỗ trợ:

```text
absolute drift
relative drift
band
hysteresis
```

để tránh unnecessary turnover.

---

# 51. Tax-aware portfolio

Axiom phải có abstraction:

```text
TaxConstraintRef
TaxLot
TaxBasis
TaxEvent
```

Nhưng tax law được resolve bởi:

```text
AXLAW
AXGOV
```

---

# 52. Tax lot

```axiom
struct TaxLot {
    acquisition_date: Date
    quantity: Decimal
    cost_basis: Money
    holding_period: Duration
}
```

Không tự giả định luật thuế.

---

# 53. ESG / policy constraints

Investment mandate có thể hỗ trợ:

```text
ExclusionPolicy
InclusionPolicy
SustainabilityConstraint
EthicalConstraint
JurisdictionConstraint
CustomPolicy
```

Các policy là investor/institution-specific.

Runtime không tự gán giá trị đạo đức.

---

# 54. Private markets

Private asset model:

```text
PrivateCompany
PrivateEquityPosition
VCPosition
PrivateDebtPosition
CapitalCall
Distribution
Commitment
Vintage
FundCommitment
```

---

# 55. Commitment model

Private fund:

```text
Commitment
→ CalledCapital
→ InvestedCapital
→ DistributedCapital
→ RemainingCommitment
```

---

# 56. J-curve

Runtime phải hỗ trợ:

```text
CommitmentCurve
CapitalCallCurve
DistributionCurve
NAVCurve
```

cho private-market simulation.

---

# 57. Real assets

```text
RealEstateExposure
InfrastructureExposure
AgricultureExposure
EnergyExposure
ResourceExposure
```

Asset physical state tham chiếu tới domain owner.

---

# 58. Alternative investments

```text
Commodity
Collectible
Art
PrivateCredit
Infrastructure
Venture
DigitalAsset
OtherAlternative
```

Alternative asset phải có valuation/liquidity uncertainty.

---

# 59. Derivatives boundary

`AXINVEST` có thể biểu diễn:

```text
DerivativeExposure
OptionExposure
FutureExposure
SwapExposure
ForwardExposure
```

nhưng pricing/execution chuyên sâu có thể được provider/module riêng.

---

# 60. Portfolio accounting

Portfolio accounting phải theo dõi:

```text
opening_value
contributions
withdrawals
income
realized_gain
unrealized_gain
fees
tax
cashflow
closing_value
```

---

# 61. Performance attribution

Phân rã:

```text
AssetAllocationEffect
SecuritySelectionEffect
FactorEffect
CurrencyEffect
TimingEffect
FeeEffect
CashEffect
```

Các attribution result phải có methodology.

---

# 62. Benchmark

```text
Benchmark
BenchmarkVersion
BenchmarkConstituent
BenchmarkWeight
BenchmarkReturn
TrackingError
```

Benchmark thay đổi theo thời gian.

Không được so sánh portfolio với benchmark không cùng version.

---

# 63. Benchmark-relative accounting

Hỗ trợ:

```text
active_weight
active_return
tracking_error
active_risk
```

---

# 64. Investment research

Core entities:

```text
ResearchDocument
ResearchObservation
ResearchThesis
ResearchEstimate
ResearchSignal
ResearchModel
ResearchDataset
```

Phân biệt:

```text
Fact
Observation
Estimate
Hypothesis
Forecast
Thesis
Decision
```

---

# 65. Research provenance

Mọi research output phải lưu:

```text
source
author
timestamp
data_version
model_version
assumptions
confidence
```

---

# 66. Investment signal

```axiom
struct InvestmentSignal {
    asset: AssetRef
    direction: SignalDirection
    strength: Decimal
    horizon: Duration
    model: ModelRef
    provenance: Provenance
}
```

Signal không phải order.

---

# 67. AI investment assistant

AI có thể:

```text
research
summarize
screen
forecast
simulate
optimize
detect_risk
attribute_performance
generate_report
explain_portfolio
```

AI không được tự động vượt capability boundary.

---

# 68. AI decision separation

Bắt buộc:

```text
AIObservation
→ AIAnalysis
→ AIRecommendation
→ Human/SystemApproval
→ ExecutionIntent
→ MarketExecution
```

Nếu policy cho phép autonomous execution:

```text
AIRecommendation
→ PolicyCheck
→ AutonomousAuthorization
→ ExecutionIntent
```

và phải audit đầy đủ.

---

# 69. AI confidence

AI output có:

```text
confidence
uncertainty
model_version
data_quality
out_of_distribution
```

Không được chuyển `confidence` thành guarantee.

---

# 70. Autonomous investment agent

Agent phải có:

```text
AgentId
Principal
Mandate
CapitalLimit
RiskLimit
AssetScope
TimeLimit
ExecutionCapability
ApprovalPolicy
AuditPolicy
```

Agent không có authority mặc định.

---

# 71. Agent safety boundary

Không cho phép agent tự ý:

```text
increase_capital_limit
change_principal
remove_risk_limit
modify_legal_owner
bypass_approval
erase_audit
```

---

# 72. Investment decision

```axiom
struct InvestmentDecision {
    proposal: ProposalRef
    decision: DecisionType
    authority: AuthorityRef
    rationale: DecisionRecord
    timestamp: Timestamp
}
```

Decision types:

```text
Approve
Reject
Modify
Defer
Withdraw
```

---

# 73. Order intent

```axiom
struct InvestmentOrderIntent {
    asset: AssetRef
    side: BuySell
    quantity: Decimal
    limit: Price?
    portfolio: PortfolioId
    authority: AuthorityRef
}
```

Không phải execution.

---

# 74. Execution boundary

```text
AXINVEST
   ↓
InvestmentOrderIntent
   ↓
AXMARKET
   ↓
Execution
   ↓
Clearing
   ↓
Settlement
   ↓
AXFINANCE
```

---

# 75. Capital allocation

`CapitalAllocation` là abstraction cấp nền kinh tế.

```axiom
struct CapitalAllocation {
    source: CapitalSource
    destination: CapitalUse
    amount: Money
    horizon: Duration
    expected_return: Estimate
    risk: RiskEstimate
}
```

---

# 76. Capital sources

```text
Savings
Deposits
EquityCapital
DebtCapital
FundCapital
InsuranceCapital
PensionCapital
GovernmentCapital
SovereignCapital
CorporateCash
```

---

# 77. Capital uses

```text
WorkingCapital
Capex
Infrastructure
Housing
Research
Manufacturing
Energy
Agriculture
Transportation
Healthcare
Education
Technology
Acquisition
Refinancing
```

Domain-specific semantics remain in owning modules.

---

# 78. Civilization capital graph

Axiom phải hỗ trợ graph:

```text
Investor
  ↓ owns
Capital
  ↓ allocated_to
Fund
  ↓ invests_in
Company
  ↓ produces
Asset
  ↓ generates
CashFlow
  ↓ returns_to
Investor
```

---

# 79. Capital flow simulation

Simulation có thể mô hình hóa:

```text
savings_rate
investment_rate
capital_cost
expected_return
default_rate
inflation
interest_rate
asset_price
liquidity
tax
```

nhưng mọi giá trị đều được gắn status:

```text
Observed
Estimated
Forecast
Scenario
Simulated
```

---

# 80. Macro capital allocation

`AXINVEST` cung cấp API cho `AX671`:

```text
aggregate_assets()
aggregate_capital_flows()
aggregate_investment()
aggregate_returns()
aggregate_risk()
simulate_capital_shock()
```

---

# 81. Investment digital twin

```text
InvestmentTwin {
    observed_state
    estimated_state
    predicted_state
    simulated_state
}
```

Không được ghi simulation vào authoritative state.

---

# 82. Portfolio digital twin

```text
LivePortfolio
    ├── ActualPositions
    ├── EstimatedValuations
    ├── RiskModel
    ├── Forecasts
    └── Scenarios
```

---

# 83. Scenario comparison

Cho phép:

```text
Base
Optimistic
Pessimistic
Stress
Custom
```

Kết quả phải giữ nguyên scenario identity.

---

# 84. Stress testing

Stress dimensions:

```text
equity_crash
rate_shock
credit_spread_shock
currency_shock
commodity_shock
liquidity_freeze
inflation_shock
deflation
geopolitical_scenario
custom
```

Không tự khẳng định scenario sẽ xảy ra.

---

# 85. Portfolio stress API

```axiom
stress_test(
    portfolio,
    scenario,
    horizon
) -> StressResult
```

---

# 86. Risk decomposition

```text
TotalRisk
├── MarketRisk
├── CreditRisk
├── LiquidityRisk
├── FXRisk
├── RateRisk
├── ConcentrationRisk
├── ModelRisk
└── OperationalRisk
```

---

# 87. Model risk

Model registry phải theo dõi:

```text
ModelId
Version
Owner
TrainingData
Validation
Assumptions
Limitations
DeploymentStatus
```

---

# 88. Model validation

Các trạng thái:

```text
Draft
Validated
Approved
Production
Deprecated
Retired
```

Model chưa validated không được mặc định production.

---

# 89. Investment model registry

```text
ReturnModel
RiskModel
ValuationModel
OptimizationModel
ForecastModel
ScenarioModel
AttributionModel
```

---

# 90. Data quality

Investment data phải có:

```text
Completeness
Accuracy
Freshness
Consistency
Lineage
Confidence
```

---

# 91. Market data

`AXINVEST` chỉ yêu cầu abstraction:

```text
MarketDataProvider
PriceFeed
YieldCurve
FXFeed
CorporateActionFeed
FundNAVFeed
ReferenceData
```

Provider implementation có thể external.

---

# 92. Corporate actions

Hỗ trợ:

```text
Dividend
Split
ReverseSplit
Merger
Acquisition
SpinOff
RightsIssue
TenderOffer
Redemption
Maturity
Coupon
```

---

# 93. Cashflow engine

Native cashflow engine:

```text
CashFlow
CashFlowSchedule
RecurringCashFlow
IrregularCashFlow
Distribution
Contribution
Withdrawal
CapitalCall
```

---

# 94. Fee model

```text
ManagementFee
PerformanceFee
TransactionFee
CustodyFee
AdvisoryFee
PlatformFee
OtherFee
```

Fee không được tự động coi là expense của mọi domain.

---

# 95. Wealth fee simulation

Có thể tính:

```text
gross_return
minus_fees
minus_tax
minus_transaction_cost
=
net_return
```

Methodology phải explicit.

---

# 96. Investor suitability boundary

Runtime có thể lưu:

```text
RiskProfile
LiquidityProfile
Horizon
Experience
Constraints
```

Nhưng không được tự động suy luận nhạy cảm hoặc biến profile thành human-worth judgment.

---

# 97. Recommendation

Recommendation object:

```axiom
struct InvestmentRecommendation {
    target: AssetRef
    rationale: Explanation
    expected_outcome: Estimate
    risks: RiskSet
    confidence: Decimal
}
```

Recommendation ≠ command.

---

# 98. Human approval

Policy:

```axiom
approval_required(
    recommendation,
    mandate
)
```

có thể trả:

```text
Required
NotRequired
Conditional
```

---

# 99. Compliance hooks

Investment policy có thể kiểm tra:

```text
Jurisdiction
InvestorEligibility
AssetEligibility
Concentration
Leverage
Liquidity
Mandate
RestrictedList
SanctionRef
LegalRestriction
```

Legal authority thuộc `AXLAW/AXGOV`.

---

# 100. Restricted assets

```text
RestrictedList
AllowedList
ProhibitedList
WatchList
```

Mỗi rule có provenance.

---

# 101. Audit

Mọi hành động có economic impact phải audit:

```text
who
what
when
why
authority
before
after
model
input
output
```

Không được sửa immutable audit record.

---

# 102. Event model

Events:

```text
PortfolioCreated
PositionOpened
PositionClosed
AllocationChanged
MandateChanged
RiskLimitChanged
ValuationUpdated
NAVPublished
ContributionReceived
WithdrawalRequested
RebalanceProposed
DecisionApproved
OrderIntentCreated
PerformanceCalculated
RiskCalculated
SimulationCompleted
```

---

# 103. Event sourcing boundary

Có thể dùng event sourcing cho:

```text
portfolio state
fund state
mandate state
allocation state
investment decision history
```

Không bắt buộc toàn bộ financial ledger phải thuộc `AXINVEST`.

---

# 104. Idempotency

Các operation:

```text
contribution
withdrawal
rebalance
allocation_update
NAV_publish
corporate_action
```

phải hỗ trợ idempotency key.

---

# 105. Temporal model

Investment state phải hỗ trợ:

```text
valid_time
transaction_time
valuation_time
market_time
settlement_time
```

Không được trộn chúng.

---

# 106. Currency

Native integration:

```text
Money
Currency
FXRate
FXExposure
BaseCurrency
ReportingCurrency
```

FX conversion phải lưu rate source và timestamp.

---

# 107. Multi-currency portfolio

Portfolio có thể:

```text
base_currency = USD
assets = USD + EUR + JPY + VND
```

Exposure phải được tính cả local và base currency.

---

# 108. Leverage

Leverage model:

```text
GrossExposure
NetExposure
Debt
Margin
BorrowedCapital
Collateral
```

Leverage phải explicit.

---

# 109. Margin boundary

Margin execution thuộc market/broker layer.

AXINVEST chỉ giữ:

```text
MarginRequirementRef
CollateralRequirementRef
```

---

# 110. Collateral

```text
CollateralAsset
CollateralValue
Haircut
Eligibility
ReuseStatus
```

---

# 111. Custody

```text
CustodianRef
CustodyAccount
CustodyLocation
AssetSafekeeping
```

Custodian không phải owner.

---

# 112. Beneficial ownership

Runtime hỗ trợ:

```text
LegalOwner
BeneficialOwner
EconomicBeneficiary
AuthorizedManager
```

Legal resolution thuộc AXLAW.

---

# 113. Multi-manager architecture

Portfolio có thể có:

```text
Owner
Advisor
Manager
SubManager
RiskManager
Custodian
ExecutionProvider
```

mỗi actor có capability riêng.

---

# 114. Family office

Native composition:

```text
Family
 ├── Members
 ├── Accounts
 ├── Portfolios
 ├── Trusts
 ├── Businesses
 ├── Properties
 └── InvestmentPlans
```

Sensitive personal data phải tuân privacy layer.

---

# 115. Pension

Pension model:

```text
Participant
Contribution
EmployerContribution
Benefit
Liability
FundingRatio
AssetPool
```

Investment layer chỉ quản lý asset side và allocation.

---

# 116. Endowment

```text
Endowment
 ├── Principal
 ├── SpendingPolicy
 ├── InvestmentPortfolio
 └── BeneficiaryPrograms
```

---

# 117. Sovereign investment

```text
SovereignFund
ReserveFund
StabilizationFund
FutureGenerationFund
StrategicFund
```

Government authority không thuộc AXINVEST.

---

# 118. Corporate treasury investment

```text
CorporateTreasury
CashPool
ShortTermInvestment
LiquidityReserve
InvestmentPolicy
```

Corporate operating authority vẫn thuộc organization/finance domains.

---

# 119. Capital allocation between organizations

```axiom
allocate_capital(
    source,
    destination,
    amount,
    mandate
)
```

Phải trả:

```text
AllocationProposal
```

không trực tiếp transfer money.

---

# 120. Investment lifecycle

```text
Idea
→ Research
→ Screening
→ Analysis
→ Proposal
→ RiskReview
→ Approval
→ Allocation
→ OrderIntent
→ Execution
→ Settlement
→ Position
→ Monitoring
→ Rebalance
→ Exit
→ Attribution
```

---

# 121. Exit lifecycle

```text
ExitProposed
→ Approved
→ OrderIntent
→ Executed
→ Settled
→ PositionClosed
→ PerformanceAttributed
```

---

# 122. Monitoring

Portfolio monitor:

```text
risk
return
drawdown
liquidity
concentration
constraint
performance
cashflow
benchmark
```

---

# 123. Alert engine

```text
RiskLimitBreach
ConstraintBreach
LiquidityWarning
DrawdownWarning
ConcentrationWarning
DataQualityWarning
ModelWarning
OperationalWarning
```

Alert ≠ action.

---

# 124. Investment command model

```axiom
portfolio.rebalance()
portfolio.simulate()
portfolio.optimize()
portfolio.analyze_risk()
portfolio.attribute()
portfolio.generate_report()
```

Các command phải trả structured result.

---

# 125. Axiom DSL example

```axiom
portfolio Global {
    currency: USD

    mandate {
        horizon: long_term
        leverage: forbidden
        max_single_issuer: 0.10
        min_liquidity_30d: 0.20
    }

    target {
        equity: 0.60
        bonds: 0.25
        real_assets: 0.10
        cash: 0.05
    }
}
```

---

# 126. Optimization DSL

```axiom
optimize Global {
    objective: maximize_risk_adjusted_return

    constraints {
        max_drawdown: 0.20
        max_turnover: 0.30
        max_issuer: 0.10
    }

    model: robust_factor_model
}
```

---

# 127. Simulation DSL

```axiom
simulate Global {
    horizon: 20y
    paths: 100000

    scenario {
        inflation: stochastic
        rates: regime_switching
        equity: stochastic
        credit: stressed
    }

    outputs {
        terminal_wealth
        drawdown
        shortfall_probability
        liquidity
    }
}
```

---

# 128. AI DSL

```axiom
agent InvestmentAnalyst {
    principal: PortfolioOwner

    permissions {
        research.read
        portfolio.read
        simulation.run
        recommendation.create
    }

    forbidden {
        capital.transfer
        risk_limit.modify
        audit.delete
    }
}
```

---

# 129. Autonomous manager DSL

```axiom
agent AutoAllocator {
    mandate: GlobalMandate

    authority {
        rebalance
    }

    limits {
        max_trade: 100000
        max_daily_turnover: 0.05
    }

    approval: policy
}
```

---

# 130. Native API surface

Core:

```text
axinvest.asset
axinvest.position
axinvest.portfolio
axinvest.fund
axinvest.mandate
axinvest.strategy
axinvest.allocation
axinvest.risk
axinvest.valuation
axinvest.performance
axinvest.simulation
axinvest.research
axinvest.ai
axinvest.capital
```

---

# 131. Native IR

Compiler/runtime IR nodes:

```text
INV_ASSET
INV_POSITION
INV_PORTFOLIO
INV_FUND
INV_MANDATE
INV_STRATEGY
INV_ALLOCATION
INV_CONSTRAINT
INV_RISK
INV_VALUATION
INV_CASHFLOW
INV_REBALANCE
INV_DECISION
INV_ORDER_INTENT
INV_SIMULATION
INV_SCENARIO
INV_MODEL
INV_ATTRIBUTION
INV_CAPITAL_FLOW
```

---

# 132. Compile-time optimization

Investment kernels phải hỗ trợ:

```text
SIMD
vectorized matrix operations
parallel Monte Carlo
GPU kernels
sparse matrices
BLAS-like provider boundary
automatic batching
memory pooling
zero-copy data views
```

---

# 133. Matrix engine

Native numerical layer phải hỗ trợ:

```text
Vector
Matrix
Tensor
SparseMatrix
SymmetricMatrix
CovarianceMatrix
CorrelationMatrix
WeightVector
```

---

# 134. Deterministic simulation

```axiom
simulation.seed = 12345
simulation.deterministic = true
```

cùng input + runtime version phải tái tạo được kết quả trong deterministic profile.

---

# 135. Parallel simulation

Execution:

```text
CPU threads
GPU
distributed workers
```

Kết quả phải preserve:

```text
seed
partition
worker
model_version
```

---

# 136. Numerical precision

Hỗ trợ:

```text
f32
f64
decimal
fixed_point
high_precision
```

Financial accounting không mặc định dùng binary floating point cho authoritative monetary ledger.

---

# 137. Decimal arithmetic

Các phép toán:

```text
Money
Price
NAV
UnitPrice
Fee
Tax
CashFlow
```

phải có explicit rounding policy.

---

# 138. Rounding policy

```text
BankersRounding
HalfUp
HalfDown
Floor
Ceil
Truncate
Custom
```

Rounding policy là metadata của operation.

---

# 139. Performance target

Runtime mục tiêu:

- portfolio calculation: native compiled;
- millions of positions: batch/vectorized;
- Monte Carlo: CPU parallel + GPU;
- risk matrix: SIMD;
- scenario engine: parallel;
- incremental recalculation;
- memory reuse;
- zero-copy views khi có thể.

---

# 140. Incremental computation

Nếu chỉ một position thay đổi:

```text
portfolio
→ affected_metrics
```

không tính lại toàn bộ portfolio nếu dependency graph cho phép.

---

# 141. Cache

Cache keys:

```text
input_hash
model_version
market_snapshot
portfolio_version
scenario_version
```

Source unchanged + dependency unchanged:

```text
reuse compiled artifact
reuse computed artifact
```

---

# 142. Reproducibility

Investment result phải có:

```text
source_version
portfolio_version
data_snapshot
model_version
parameter_set
random_seed
runtime_version
```

---

# 143. Security capabilities

Core:

```text
investment.read
investment.write

portfolio.read
portfolio.write

position.read
position.write

mandate.read
mandate.write

allocation.read
allocation.propose
allocation.approve

risk.read
risk.configure

simulation.run

research.read
research.write

recommendation.create

order_intent.create

fund.read
fund.manage

valuation.read
valuation.publish

admin
```

---

# 144. Capital movement separation

Capability:

```text
investment.order_intent.create
```

không tự cấp:

```text
finance.transfer
banking.withdraw
```

Đây là security invariant quan trọng.

---

# 145. Data privacy

Sensitive data:

```text
wealth
portfolio
income
beneficiary
tax
investment_history
risk_profile
```

phải được capability-protected.

---

# 146. Privacy-preserving analytics

Hỗ trợ abstraction:

```text
AggregatePortfolioAnalytics
PrivateAggregation
DifferentialPrivacyBoundary
FederatedAnalyticsBoundary
```

---

# 147. AI data isolation

Agent chỉ được truy cập dataset theo:

```text
principal
purpose
capability
scope
retention
```

---

# 148. Explainability

Investment recommendation có thể yêu cầu:

```text
explain()
```

trả:

```text
inputs
factors
constraints
assumptions
model
uncertainty
alternatives
```

Không yêu cầu model phải giải thích nội bộ không thể quan sát.

---

# 149. Decision provenance

Mọi autonomous action phải lưu:

```text
trigger
policy
model
input_snapshot
decision
authorization
execution_intent
```

---

# 150. Failure model

Lỗi chuẩn:

```text
AssetNotFound
PortfolioNotFound
MandateViolation
ConstraintViolation
RiskLimitViolation
InsufficientLiquidity
InsufficientCapital
InvalidAllocation
InvalidValuation
StaleMarketData
ModelUnavailable
ModelValidationFailure
SimulationFailure
AuthorizationDenied
ExecutionBoundaryUnavailable
ReconciliationFailure
```

---

# 151. Stale data

Market data có:

```text
timestamp
age
max_age
```

Nếu quá stale:

```text
Fresh
Stale
Unavailable
```

Không được coi stale data là current fact.

---

# 152. Reconciliation

Portfolio phải reconcile:

```text
AXINVEST position
↔ custody
↔ market execution
↔ AXFINANCE ledger
```

Mismatch tạo:

```text
ReconciliationException
```

---

# 153. Double-entry boundary

AXINVEST không thay thế financial ledger.

Mọi monetary settlement cuối cùng phải reconcile với:

```text
AXFINANCE
```

---

# 154. Transaction integrity

Investment state transition phải hỗ trợ:

```text
atomic
idempotent
durable
auditable
recoverable
```

---

# 155. Disaster recovery

Phải hỗ trợ:

```text
snapshot
checkpoint
journal
replay
reconciliation
recovery
```

---

# 156. Portfolio versioning

Mỗi portfolio có:

```text
PortfolioVersion
```

thay đổi:

```text
mandate
allocation
risk
positions
strategy
```

đều tạo version mới.

---

# 157. Immutable history

Không overwrite lịch sử:

```text
InvestmentDecision
AllocationChange
MandateChange
RiskLimitChange
NAVPublication
```

Sửa bằng event mới.

---

# 158. Governance

Investment governance roles:

```text
Owner
Trustee
Manager
Advisor
RiskOfficer
ComplianceOfficer
Researcher
Operator
Auditor
```

Role ≠ authority.

Authority phải capability-based.

---

# 159. Conflict controls

Runtime hỗ trợ:

```text
ConflictDisclosure
RestrictedAsset
PersonalAccountRestriction
RelatedPartyRef
ConflictReview
```

Legal interpretation vẫn thuộc AXLAW.

---

# 160. Market manipulation boundary

AXINVEST không tự định nghĩa hành vi pháp lý.

Có thể phát ra:

```text
AnomalySignal
TradingPatternSignal
ConflictSignal
```

và chuyển sang compliance/legal layer.

---

# 161. Fraud distinction

```text
FraudSignal ≠ FraudFinding
```

AI chỉ tạo signal nếu chưa có authoritative determination.

---

# 162. Investment simulation at civilization scale

Có thể mô phỏng:

```text
household savings
→ pension
→ banks
→ insurers
→ funds
→ capital markets
→ enterprises
→ infrastructure
→ productivity
→ income
→ savings
```

---

# 163. Systemic risk

Simulation hỗ trợ:

```text
liquidity contagion
leverage contagion
asset price shock
redemption cascade
credit shock
funding shock
correlation spike
```

Kết quả là scenario analysis.

Không phải dự đoán chắc chắn.

---

# 164. Network model

```text
Investor
    ↓
Fund
    ↓
Asset
    ↓
Issuer
    ↓
Bank
    ↓
Insurer
    ↓
Infrastructure
```

Edges:

```text
owns
invests
borrows
insures
guarantees
depends_on
exposes_to
```

---

# 165. Systemic exposure graph

Cho phép:

```text
find_exposure(entity)
find_concentration(entity)
find_dependency(entity)
simulate_failure(entity)
```

---

# 166. Capital efficiency

Metrics:

```text
CapitalEfficiency
ReturnOnCapital
RiskAdjustedReturnOnCapital
LiquidityAdjustedReturn
EconomicProfit
```

---

# 167. Investment opportunity

```axiom
struct InvestmentOpportunity {
    target: AssetOrProjectRef
    capital_required: Money
    expected_cashflows: CashFlowSchedule
    expected_return: Estimate
    risks: RiskSet
    liquidity: LiquidityEstimate
    horizon: Duration
}
```

---

# 168. Project investment

Cho phép kết nối:

```text
InvestmentOpportunity
→ Construction
→ Manufacturing
→ Energy
→ Agriculture
→ Infrastructure
```

nhưng operational state thuộc domain tương ứng.

---

# 169. Venture investment

```text
Startup
FundingRound
Investor
TermSheet
Ownership
Dilution
ExitScenario
```

Legal ownership semantics thuộc AXLAW.

---

# 170. Capital round

Lifecycle:

```text
Planned
→ Open
→ Subscribed
→ Closed
→ Funded
→ Active
→ Converted/Exited
```

---

# 171. Acquisition

Investment layer có:

```text
AcquisitionOpportunity
PurchasePrice
FinancingPlan
ExpectedSynergy
Scenario
```

Operational merger semantics thuộc organization/legal layers.

---

# 172. Infrastructure investment

```text
InfrastructureProject
CapitalRequirement
FundingStructure
CashFlow
Risk
ExpectedReturn
```

Có thể tham chiếu `AXCONSTRUCTION`, `AXRESOURCE`, `AXTRANSPORT`, `AXENERGY`.

---

# 173. Greenfield investment

```text
Capital
→ Project
→ Construction
→ Operation
→ CashFlow
→ Exit
```

Simulation engine có thể chạy toàn lifecycle.

---

# 174. Portfolio construction pipeline

```text
Universe
→ DataValidation
→ Screening
→ Forecast
→ RiskModel
→ Optimization
→ ConstraintCheck
→ Approval
→ Rebalance
```

---

# 175. Universe

```text
InvestmentUniverse
```

có thể lọc theo:

```text
asset_type
country
sector
liquidity
market_cap
rating
currency
risk
mandate
```

---

# 176. Screening

Screening chỉ tạo candidate set:

```text
CandidateSet
```

không tự động tạo investment decision.

---

# 177. Ranking

AI/quant engine có thể tính:

```text
SignalScore
ExpectedReturn
RiskScore
LiquidityScore
```

Nhưng `AXINVEST` không định nghĩa universal ranking of humans.

---

# 178. Portfolio comparison

Có thể so sánh:

```text
Portfolio A
Portfolio B
Portfolio C
```

theo factual metrics:

```text
return
risk
drawdown
liquidity
fees
exposure
```

Không tạo universal "best portfolio" primitive.

---

# 179. Recommendation policy

Recommendation phải trả:

```text
candidate
metrics
tradeoffs
uncertainty
constraints
```

thay vì opaque command.

---

# 180. Native report

```text
PortfolioReport
RiskReport
PerformanceReport
AllocationReport
LiquidityReport
AttributionReport
ScenarioReport
InvestmentResearchReport
FundReport
WealthReport
```

---

# 181. Report provenance

Mỗi report:

```text
generated_at
data_snapshot
model_versions
portfolio_version
author/agent
```

---

# 182. CLI

Ví dụ:

```text
axiom invest portfolio show
axiom invest portfolio risk
axiom invest portfolio optimize
axiom invest portfolio rebalance
axiom invest portfolio simulate
axiom invest fund nav
axiom invest fund holdings
axiom invest research run
axiom invest capital flows
```

---

# 183. Observability

Metrics:

```text
portfolio_compute_latency
risk_compute_latency
simulation_throughput
optimization_latency
market_data_age
reconciliation_gap
model_failure_rate
agent_action_rate
```

---

# 184. Tracing

Trace:

```text
research
→ model
→ recommendation
→ approval
→ intent
→ execution_ref
→ settlement_ref
→ position
```

---

# 185. Profile system

```text
AXINVEST_NONE
AXINVEST_CORE
AXINVEST_ASSET
AXINVEST_PORTFOLIO
AXINVEST_FUND
AXINVEST_WEALTH
AXINVEST_RESEARCH
AXINVEST_RISK
AXINVEST_QUANT
AXINVEST_OPTIMIZATION
AXINVEST_SIMULATION
AXINVEST_AI
AXINVEST_PRIVATE_MARKETS
AXINVEST_TREASURY
AXINVEST_PENSION
AXINVEST_SOVEREIGN
AXINVEST_DISTRIBUTED
AXINVEST_GPU
AXINVEST_WASM
AXINVEST_MOBILE
AXINVEST_REALTIME
AXINVEST_GLOBAL
AXINVEST_FULL
```

---

# 186. Minimal profile

`AXINVEST_CORE` chỉ cần:

```text
Asset
Position
Portfolio
Mandate
Allocation
Risk
Valuation
Performance
```

Các hệ thống lớn load module bổ sung.

---

# 187. WASM

WASM profile hỗ trợ:

```text
portfolio viewer
risk calculator
simulation viewer
research dashboard
```

Không yêu cầu direct brokerage access.

---

# 188. Mobile

Mobile profile ưu tiên:

```text
portfolio
wealth
goals
risk
reports
notifications
```

---

# 189. GPU

GPU profile:

```text
MonteCarlo
matrix
optimization
factor_model
scenario_engine
```

---

# 190. Distributed execution

Distributed investment workloads:

```text
simulation
risk
optimization
research
backtesting
```

phải hỗ trợ partition + deterministic seed.

---

# 191. Backtesting

```text
Strategy
→ HistoricalData
→ Simulation
→ Orders
→ ExecutionModel
→ Portfolio
→ Metrics
```

Backtest phải phân biệt:

```text
historical_observation
simulated_execution
actual_execution
```

---

# 192. Backtest leakage protection

Dataset phải hỗ trợ:

```text
as_of_time
publication_time
availability_time
```

để ngăn future-information leakage.

---

# 193. Survivorship bias

Universe snapshot phải versioned:

```text
UniverseAtTime(t)
```

Không được mặc định dùng current universe cho historical simulation.

---

# 194. Transaction cost model

```text
Commission
Spread
Slippage
MarketImpact
Tax
Fee
```

Backtest có thể bật/tắt từng thành phần.

---

# 195. Paper trading

```text
PaperPortfolio
PaperOrderIntent
SimulatedExecution
```

Không được tạo real settlement.

---

# 196. Shadow portfolio

Cho phép:

```text
RealPortfolio
ShadowPortfolio
```

để so sánh hypothetical strategy với production state.

---

# 197. Experiment framework

```text
Experiment
Hypothesis
Dataset
Model
Parameters
Result
Reproducibility
```

---

# 198. A/B investment strategy

Có thể chạy:

```text
StrategyA
StrategyB
```

trên cùng dataset/scenario.

Không được tự coi kết quả simulation là proof of future performance.

---

# 199. Research notebook integration

Axiom hỗ trợ native structured notebook:

```text
ResearchSession
Cell
Dataset
Model
Chart
Result
Decision
```

Artifact phải reproducible.

---

# 200. AI memory

Investment agent memory có:

```text
ResearchMemory
PortfolioMemory
DecisionMemory
MarketMemory
ScenarioMemory
```

Memory phải có scope và retention.

---

# 201. Knowledge graph

Entities:

```text
Investor
Fund
Issuer
Asset
Sector
Country
Portfolio
Strategy
Risk
Event
```

Relations:

```text
owns
manages
invests
issues
depends
exposes
correlates
hedges
```

---

# 202. Semantic query

Ví dụ:

```axiom
query exposures(portfolio)
    where sector == "energy"
```

hoặc:

```axiom
query assets(portfolio)
    where liquidity < 30d
```

---

# 203. Query execution

Compiler có thể tối ưu:

```text
predicate pushdown
column pruning
vectorization
index usage
parallel execution
```

---

# 204. Event-driven portfolio

Có thể khai báo:

```axiom
on RiskLimitBreach {
    notify RiskManager
}
```

hoặc:

```axiom
on AllocationDrift > 0.05 {
    create RebalanceProposal
}
```

Không tự execute nếu policy không cho phép.

---

# 205. Policy engine integration

```text
InvestmentPolicy
→ AX639 policy engine
→ decision
```

---

# 206. Compliance integration

```text
AXINVEST
→ AXLAW
→ AXGOV
→ AXMARKET
```

cho:

```text
eligibility
restriction
jurisdiction
reporting
authorization
```

---

# 207. Banking integration

```text
AXINVEST
↔ AXBANKING
```

cho:

```text
cash
custody
funding
credit
margin_ref
```

Không bypass banking authority.

---

# 208. Insurance integration

```text
AXINVEST
↔ AXINSURANCE
```

cho:

```text
insurer investment portfolio
risk transfer
capital adequacy references
asset-liability management
catastrophe-linked capital
```

---

# 209. Housing integration

Real-estate portfolio:

```text
AXINVEST
→ AXHOUSING
```

có thể giữ:

```text
property_ref
rent_cashflow
valuation_ref
mortgage_ref
```

---

# 210. Labor integration

Investment trong human-capital programs có thể tham chiếu:

```text
AXLABOR
AXEDUCATION
```

nhưng không được coi con người là financial asset.

---

# 211. Healthcare integration

Healthcare infrastructure investment có thể tham chiếu:

```text
HospitalProject
MedicalInfrastructure
BiomedicalVenture
```

Không được biến patient thành investment position.

---

# 212. Ethical semantic invariant

Axiom phải cấm semantic collapse:

```text
Person → Asset
Worker → FinancialInstrument
Patient → PortfolioPosition
Citizen → CapitalUnit
```

Con người có thể là actor/beneficiary/investor nhưng không được tự động biến thành asset primitive.

---

# 213. Civilization wealth

`AXINVEST` cung cấp:

```text
HouseholdWealth
InstitutionalWealth
CorporateWealth
FundWealth
PublicWealth
AggregateCapital
```

Tất cả phải phân biệt:

```text
gross
net
financial
real
liquid
illiquid
```

---

# 214. Wealth distribution analytics

Hỗ trợ aggregate metrics:

```text
wealth_distribution
capital_distribution
asset_distribution
ownership_concentration
liquidity_distribution
```

Dữ liệu cá nhân phải được aggregate/anonymize theo policy.

---

# 215. Economic simulation integration

```text
AX671
   ↓
Savings
   ↓
AXINVEST
   ↓
CapitalAllocation
   ↓
Production
   ↓
Income
   ↓
AX671
```

---

# 216. Scientific investment

`AX672` có thể sử dụng:

```text
ResearchFunding
GrantInvestment
R&DCapital
VentureFunding
InfrastructureFunding
```

---

# 217. Education investment

`AX673`:

```text
EducationFund
HumanCapitalInvestment
ScholarshipEndowment
EducationInfrastructure
```

---

# 218. Energy investment

`AX681`:

```text
EnergyProjectInvestment
GridInvestment
WaterInfrastructureInvestment
WasteInfrastructureInvestment
```

---

# 219. Manufacturing investment

`AX682`:

```text
FactoryInvestment
AutomationInvestment
EquipmentFinance
IndustrialExpansion
```

---

# 220. Construction investment

`AX683`:

```text
ConstructionProjectInvestment
RealEstateDevelopment
InfrastructureFund
```

---

# 221. Agriculture investment

`AX685`:

```text
FarmInvestment
FoodSystemInvestment
AgriculturalFund
ForestryInvestment
```

---

# 222. Transport investment

`AX684`:

```text
FleetInvestment
RailInvestment
PortInvestment
AirportInvestment
LogisticsInfrastructure
```

---

# 223. Investment knowledge contract

Compiler-generated investment artifacts phải có machine-readable metadata:

```text
schema
dependencies
models
assumptions
constraints
provenance
risk
version
```

AI agent có thể đọc artifact mà không cần parse natural-language documentation.

---

# 224. Source artifact

Một investment program compile thành:

```text
.axsrc
.axir
.axmeta
.axmodel
.axcache
```

Trong đó:

```text
.axmeta
```

chứa semantic metadata.

---

# 225. Cache invalidation

Cache phải invalid khi:

```text
source changed
dependency changed
model changed
data contract changed
compiler version incompatible
target architecture changed
```

---

# 226. ABI

Public investment ABI phải ổn định theo version:

```text
AXINVEST_ABI_5
```

---

# 227. FFI

Có thể gọi provider ngoài:

```text
market_data
pricing
broker
custody
analytics
```

nhưng core semantics không phụ thuộc provider cụ thể.

---

# 228. No mandatory external runtime

Core `AXINVEST` phải compile với:

```text
Axiom compiler
Axiom runtime core
```

Các provider:

```text
optional
```

---

# 229. Embedded mode

Có thể nhúng:

```text
static library
shared library
WASM module
mobile module
server runtime
desktop application
```

---

# 230. Testing strategy

Các nhóm test:

```text
unit
property
invariant
numerical
determinism
simulation
security
authorization
temporal
reconciliation
performance
GPU
distributed
failure-recovery
```

---

# 231. Numerical tests

Phải kiểm tra:

```text
rounding
overflow
underflow
precision
NaN
Infinity
negative_zero
decimal_conversion
currency_conversion
```

---

# 232. Portfolio invariant tests

Ví dụ:

```text
sum(position_values) + cash == portfolio_value
```

sai số chỉ được phép theo explicit numerical tolerance.

---

# 233. Allocation invariants

```text
weights sum to allowed gross exposure
hard constraints never silently violated
negative weights require explicit short permission
leverage requires explicit permission
```

---

# 234. Security invariant tests

```text
investment capability cannot transfer money
research capability cannot execute
simulation capability cannot mutate production state
read capability cannot modify portfolio
agent cannot escalate authority
```

---

# 235. Temporal tests

Test:

```text
late market data
out-of-order events
duplicate events
replayed events
stale valuation
future-dated event
timezone conversion
```

---

# 236. Simulation invariants

```text
simulation cannot mutate production portfolio
simulation result retains scenario identity
seed replay is deterministic where enabled
```

---

# 237. Reconciliation tests

Test:

```text
AXINVEST position
AXMARKET execution
AXFINANCE ledger
custody
```

với:

```text
zero difference
partial difference
missing execution
duplicate settlement
corporate action
```

---

# 238. AI tests

Phải kiểm tra:

```text
hallucinated asset
hallucinated price
hallucinated position
unauthorized action
missing uncertainty
stale data
wrong model version
```

---

# 239. Agent sandbox

Investment AI development mặc định chạy:

```text
ResearchSandbox
SimulationSandbox
```

Production execution cần explicit capability.

---

# 240. Red-team

Investment AI red-team scenarios:

```text
prompt injection
fake market data
malicious research
conflicting instructions
authority spoofing
stale data
risk-limit bypass
capital escalation
```

---

# 241. Recovery tests

```text
process crash
machine crash
network partition
market-data outage
provider outage
partial execution
ledger mismatch
```

---

# 242. Performance targets

Reference target:

```text
10M+ positions
10M+ scenario paths
1M+ portfolio evaluations
GPU Monte Carlo
parallel risk computation
```

Mục tiêu benchmark phải phụ thuộc hardware profile.

---

# 243. Memory efficiency

Ưu tiên:

```text
SoA
columnar layout
compact numeric types
arena allocation
memory reuse
zero-copy views
```

Không tạo object graph heap-heavy cho mỗi tick.

---

# 244. Data-oriented design

Hot path:

```text
Position[]
Price[]
Weight[]
Exposure[]
Risk[]
```

thay vì:

```text
PositionObject → nested object → boxed values
```

---

# 245. Compile-time specialization

Nếu portfolio schema cố định:

```text
compile specialized kernels
```

để giảm dynamic dispatch.

---

# 246. Generic numeric kernels

Compiler phải specialize:

```text
f32
f64
decimal
fixed_point
SIMD
GPU
```

---

# 247. Error recovery

Market-data failure:

```text
use_last_valid
use_secondary_provider
mark_stale
halt
```

Policy quyết định behavior.

Không fallback im lặng.

---

# 248. Operational modes

```text
Research
Backtest
Simulation
PaperTrading
Shadow
Production
Recovery
Audit
```

Mode phải explicit.

---

# 249. Production mutation gate

Chỉ:

```text
Production
```

mới được mutate authoritative investment state.

Simulation/backtest/paper mode bị sandbox.

---

# 250. Core architecture invariants

Các invariant bắt buộc:

```text
I-01 Asset != Position
I-02 Position != OwnershipCertificate
I-03 Portfolio != Account
I-04 Investment != Payment
I-05 Recommendation != Decision
I-06 Decision != Execution
I-07 Execution != Settlement
I-08 Price != Value
I-09 Forecast != Actual
I-10 Simulation != Production
I-11 Risk != Loss
I-12 NAV != MarketPrice
I-13 Liquidity != Solvency
I-14 Investor != Beneficiary
I-15 Agent != Principal
I-16 Capability != Role
I-17 Signal != Fact
I-18 ModelOutput != FinancialTruth
I-19 HardConstraint cannot be silently violated
I-20 Simulation cannot mutate production
I-21 AI cannot escalate capability
I-22 Investment cannot bypass AXFINANCE settlement
I-23 Investment cannot bypass AXMARKET execution
I-24 Legal ownership cannot be inferred from economic exposure
I-25 Historical state is immutable
I-26 Every authoritative valuation has provenance
I-27 Every autonomous capital action is auditable
I-28 Every money calculation has explicit currency
I-29 Every financial rounding operation has explicit policy
I-30 Every model result has model/version provenance
```

---

# 251. Required test scale

Mục tiêu architecture:

```text
≥ 16,000 automated tests
≥ 1,500 architecture invariants
≥ 2,000 numerical/property tests
≥ 1,000 security/authorization tests
≥ 1,000 simulation/reproducibility tests
```

Các con số là test targets, không phải yêu cầu phải viết toàn bộ trong một module duy nhất.

---

# 252. Acceptance criteria

`AXINVEST 5.0` chỉ được coi là kiến trúc hoàn chỉnh khi:

1. Portfolio có lifecycle đầy đủ.
2. Asset/position/ownership được tách biệt.
3. Allocation có constraint engine.
4. Risk engine có provenance.
5. Valuation có temporal model.
6. Fund có NAV/unit model.
7. Wealth planning hỗ trợ goal-based planning.
8. Private-market commitment được biểu diễn.
9. AI recommendation tách khỏi execution.
10. Autonomous agent có capability boundary.
11. Simulation không thể mutate production.
12. Backtest chống future leakage.
13. Historical universe được version hóa.
14. Multi-currency được hỗ trợ.
15. Tax/legal boundary rõ ràng.
16. Market execution chuyển sang `AXMARKET`.
17. Settlement chuyển về `AXFINANCE`.
18. Custody reconciliation được hỗ trợ.
19. GPU/CPU simulation được hỗ trợ.
20. Distributed simulation có deterministic seed.
21. Portfolio state có versioning.
22. Audit trail immutable.
23. Model registry có lifecycle.
24. Data provenance đầy đủ.
25. Civilization-scale capital-flow simulation có API.
26. Compiler có native IR.
27. Runtime có profile system.
28. Không phụ thuộc third-party runtime bắt buộc.
29. Security capability được compiler/runtime enforce.
30. Có đủ test/invariant contract để triển khai compiler/runtime.

---

# 253. Final AXINVEST architecture

```text
                     AXINVEST 5.0
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
     WEALTH             FUNDS              ASSETS
        │                  │                  │
        ├──── GOALS        ├──── NAV          ├──── POSITIONS
        ├──── PLANS        ├──── UNITS        ├──── VALUATION
        └──── ACCOUNTS     └──── STRATEGY     └──── EXPOSURE
                           │
                           ▼
                     PORTFOLIO ENGINE
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        ALLOCATION       RISK         OPTIMIZATION
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    DECISION ENGINE
                           │
                     ORDER INTENT
                           │
                           ▼
                       AXMARKET
                           │
                    EXECUTION/CLEARING
                           │
                           ▼
                      AXFINANCE
                           │
                        SETTLEMENT
```

AI layer:

```text
RESEARCH
   ↓
FORECAST
   ↓
RISK
   ↓
OPTIMIZATION
   ↓
RECOMMENDATION
   ↓
POLICY
   ↓
AUTHORIZATION
   ↓
ACTION
```

Civilization layer:

```text
HOUSEHOLDS
    ↓
SAVINGS
    ↓
CAPITAL
    ↓
INVESTMENT
    ↓
FUNDS / PORTFOLIOS
    ↓
ENTERPRISES / INFRASTRUCTURE
    ↓
PRODUCTION
    ↓
CASH FLOW
    ↓
WEALTH
```

---

# 254. Final semantic contract

`AXINVEST` phải biến Axiom thành một nền tảng có khả năng biểu diễn **toàn bộ vòng đời phân bổ vốn**, từ một khoản tiết kiệm của cá nhân tới portfolio tổ chức, quỹ đầu tư, pension fund, sovereign fund và mô phỏng luồng vốn ở quy mô nền kinh tế.

Nhưng runtime phải luôn giữ ranh giới:

```text
CAPITAL
≠
INVESTMENT DECISION
≠
ORDER
≠
EXECUTION
≠
CLEARING
≠
SETTLEMENT
≠
LEGAL OWNERSHIP
```

Đây là boundary quan trọng nhất của `AXINVEST`.

---

# 255. Architecture chain sau BOOTSTRAP-692

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
AXCIVILIZATION
```

Trong đó:

```text
AXFINANCE
    = money / accounting / financial truth

AXBANKING
    = deposits / credit / banking

AXINSURANCE
    = risk transfer / reserves / reinsurance

AXINVEST
    = capital allocation / portfolio / investment

AXMARKET
    = trading / exchange / brokerage / clearing / settlement

AXCIVILIZATION
    = aggregate economic system
```

**BOOTSTRAP-692 hoàn tất.**

**Task kế tiếp: BOOTSTRAP-693 — Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Clearing, Settlement, Market Infrastructure & Global Financial Market Runtime 5.0.**

:::

Chuỗi kiến trúc tiếp tục sang **BOOTSTRAP-693**, nơi `AXINVEST` sẽ kết nối với hạ tầng thị trường vốn thực thi: order book, exchange, broker, matching, clearing, settlement và market microstructure.