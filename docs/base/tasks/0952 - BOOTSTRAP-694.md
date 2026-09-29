Tiếp tục với **BOOTSTRAP-694** — lớp tiền tệ và ngân hàng trung ương, tách khỏi banking thương mại, finance ledger và capital markets.

:::writing{variant="document" id="58321" title="BOOTSTRAP-694 — Native AI Civilization-Scale Monetary System, Central Banking, Money Supply, Interest Rates, Monetary Policy, Foreign Exchange Reserves, Currency Systems & Global Monetary Runtime 5.0"}

# BOOTSTRAP-694
## Native AI Civilization-Scale Monetary System, Central Banking, Money Supply, Interest Rates, Monetary Policy, Foreign Exchange Reserves, Currency Systems & Global Monetary Runtime 5.0

**Status:** Architecture Specification  
**Version:** 5.0  
**Namespace:** `AXMONETARY`  
**Layer:** Global Monetary Infrastructure  
**Primary role:** native runtime cho tiền tệ, currency, monetary aggregates, central-bank operations, monetary policy, reserves, interest-rate transmission, foreign exchange, liquidity operations, payment-system interfaces và civilization-scale monetary simulation.

---

# 1. Mục tiêu

`AXMONETARY` phải mô hình hóa được:

- currency;
- money;
- monetary aggregates;
- central bank;
- monetary authority;
- reserves;
- reserve accounts;
- policy rates;
- interest-rate corridors;
- open-market operations;
- standing facilities;
- reserve requirements;
- liquidity management;
- foreign-exchange reserves;
- FX intervention;
- exchange-rate regimes;
- currency issuance;
- redemption;
- central-bank balance sheet;
- bank reserves;
- settlement balances;
- monetary transmission;
- inflation/price-level models;
- monetary statistics;
- macroeconomic monetary simulation;
- cross-currency monetary networks.

---

# 2. Boundary kiến trúc

Các distinction bắt buộc:

```text id="monetary-boundary"
Money ≠ Wealth
MoneySupply ≠ NationalWealth
Currency ≠ BankDeposit
CentralBankReserve ≠ CommercialBankDeposit
PolicyRate ≠ MarketRate
MarketRate ≠ GuaranteedRate
MoneyCreation ≠ WealthCreation
Liquidity ≠ Solvency
LiquidityProvision ≠ Bailout
ReserveAsset ≠ DomesticMoney
FXRate ≠ FundamentalValue
Inflation ≠ PriceOfOneAsset
MonetaryPolicy ≠ FiscalPolicy
Forecast ≠ PolicyDecision
Simulation ≠ ActualEconomy
PolicyRecommendation ≠ PolicyAuthority
```

---

# 3. Vị trí trong Axiom

```text id="monetary-stack"
AXCIVILIZATION
      │
      ▼
AX671 — ECONOMY
      │
      ├──────────────┐
      ▼              ▼
AXFINANCE        AXMONETARY
      │              │
      ▼              ├── Currency
AXBANKING           ├── Central Bank
      │              ├── Policy
      ▼              ├── Reserves
AXMARKET             ├── FX
                     └── Monetary Simulation
```

---

# 4. Monetary system

```axiom id="mon-system"
struct MonetarySystem {
    id: MonetarySystemId
    jurisdiction: JurisdictionRef
    currencies: CurrencyId[]
    monetary_authority: EntityRef
    exchange_regime: ExchangeRateRegime
    policy_framework: MonetaryPolicyFramework
}
```

---

# 5. Currency

Currency là đơn vị monetary denomination.

```axiom id="mon-currency"
struct Currency {
    id: CurrencyId
    code: String
    name: String
    minor_unit: u8
    issuer: EntityRef
    status: CurrencyStatus
}
```

---

# 6. Currency ≠ money

Một currency có thể được biểu diễn bởi nhiều monetary instruments:

```text id="currency-money"
Currency
├── PhysicalCash
├── CentralBankReserve
├── CommercialBankDeposit
├── ElectronicMoney
└── OtherMonetaryInstrument
```

Tùy legal/monetary framework.

---

# 7. Currency lifecycle

```text id="currency-life"
Proposed
→ Authorized
→ Issued
→ Circulating
→ Restricted
→ Redeemable
→ Withdrawn
→ Retired
```

---

# 8. Monetary unit

Canonical representation:

```axiom id="mon-unit"
struct MonetaryAmount {
    currency: CurrencyId
    value: Decimal
}
```

Không cho phép cộng trực tiếp:

```text
USD + EUR
```

nếu không có conversion context.

---

# 9. FX conversion

```axiom id="fx-conversion"
convert(
    amount,
    from_currency,
    to_currency,
    fx_rate,
    timestamp
)
```

FX rate phải có provenance.

---

# 10. Exchange rate

```axiom id="fx-rate"
struct FXRate {
    base: CurrencyId
    quote: CurrencyId
    rate: Decimal
    timestamp: Timestamp
    source: FXRateSource
}
```

---

# 11. FX rate ≠ fixed truth

Một FX rate có thể là:

```text id="fx-rate-types"
Spot
Forward
Reference
Indicative
Official
Market
Interbank
Model
Simulation
```

Phải giữ type.

---

# 12. Currency pair

```axiom id="currency-pair"
struct CurrencyPair {
    base: CurrencyId
    quote: CurrencyId
}
```

Canonical:

```text
EUR/USD
USD/JPY
GBP/USD
```

---

# 13. FX market

```axiom id="fx-market"
struct FXMarket {
    id: FXMarketId
    pairs: CurrencyPair[]
    venues: VenueRef[]
    settlement_system: SettlementProviderRef
}
```

Trading semantics delegate cho `AXMARKET`.

---

# 14. Central bank

```axiom id="central-bank"
struct CentralBank {
    id: CentralBankId
    jurisdiction: JurisdictionRef
    currencies: CurrencyId[]
    policy_framework: MonetaryPolicyFramework
    balance_sheet: BalanceSheetRef
}
```

---

# 15. Monetary authority

Central bank không nhất thiết là toàn bộ monetary authority.

```text id="authority"
MonetaryAuthority
├── CentralBank
├── CurrencyBoard
├── MonetaryCouncil
└── OtherAuthorizedInstitution
```

---

# 16. Authority boundary

`AXMONETARY` biểu diễn authority và policy execution interfaces.

Legal authority vẫn thuộc:

```text id="authority-law"
AXLAW
AXGOV
```

---

# 17. Central-bank account

```axiom id="cb-account"
struct CentralBankAccount {
    id: AccountId
    institution: EntityRef
    currency: CurrencyId
    balance: MonetaryAmount
    account_type: CentralBankAccountType
}
```

Types:

```text id="cb-account-types"
CommercialBankReserve
Government
ForeignOfficial
Clearing
Settlement
OtherAuthorized
```

---

# 18. Reserve balance

Reserve balance là liability/claim trong central-bank monetary system theo applicable framework.

Không đồng nhất với commercial-bank customer deposits.

---

# 19. Reserve lifecycle

```text id="reserve-life"
Created
→ Credited
→ Available
→ Encumbered
→ Transferred
→ Settled
→ Redeemed/Extinguished
```

---

# 20. Reserve transfer

```axiom id="reserve-transfer"
transfer_reserves(
    from,
    to,
    amount,
    settlement_context
)
```

Phải atomic.

---

# 21. Central-bank ledger boundary

Central-bank ledger phải phân biệt:

```text id="cb-ledger"
Assets
Liabilities
Capital/Equity
ContingentItems
OffBalanceSheet
```

Không dùng `AXFINANCE` ledger semantics để thay thế monetary-state semantics.

---

# 22. Monetary base

Canonical aggregate:

```text id="mon-base"
MonetaryBase =
CurrencyInCirculation
+
EligibleCentralBankReserves
```

Exact statistical definition có thể phụ thuộc framework.

---

# 23. Monetary aggregates

Native abstraction:

```axiom id="money-aggregate"
struct MonetaryAggregate {
    id: AggregateId
    definition: AggregateDefinition
    value: MonetaryAmount
    timestamp: Timestamp
}
```

Có thể biểu diễn:

```text id="aggregates"
MB
M0
M1
M2
M3
CustomAggregate
```

Không hard-code một country's statistical definition.

---

# 24. Aggregate composition

Mỗi aggregate phải có machine-readable definition:

```text id="aggregate-definition"
components
inclusion_rules
exclusion_rules
institution_scope
instrument_scope
residency_scope
valuation_method
```

---

# 25. Money stock

Money stock là measurement tại một thời điểm.

Không coi:

```text id="money-stock"
MoneyStock
```

là immutable fact nếu underlying data có revision.

---

# 26. Monetary statistics

Data states:

```text id="mon-stat"
Observed
Estimated
Revised
SeasonallyAdjusted
ModelDerived
Simulated
```

---

# 27. Statistical vintage

Mọi macro monetary series phải hỗ trợ:

```axiom id="vintage"
struct DataVintage {
    observation_date: Date
    publication_date: Date
    revision: u32
    source: DataSourceRef
}
```

---

# 28. Policy rate

```axiom id="policy-rate"
struct PolicyRate {
    id: RateId
    authority: CentralBankId
    rate_type: PolicyRateType
    rate: Rate
    effective_from: Timestamp
    effective_to: Timestamp?
}
```

---

# 29. Policy-rate types

```text id="policy-rate-types"
TargetRate
DepositRate
LendingFacilityRate
MarginalLendingRate
DiscountRate
ReserveRemunerationRate
CorridorFloor
CorridorCeiling
CustomPolicyRate
```

---

# 30. Rate corridor

```axiom id="rate-corridor"
struct RateCorridor {
    floor: Rate
    target: Rate?
    ceiling: Rate
    effective_period: TimeRange
}
```

Invariant:

```text id="corridor-invariant"
floor <= target <= ceiling
```

nếu target tồn tại.

---

# 31. Policy-rate change

```text id="rate-change"
Proposed
→ Approved
→ Announced
→ Effective
→ Expired
```

---

# 32. Announcement ≠ implementation

```text id="announcement"
PolicyAnnouncement ≠ PolicyImplementation
```

Một announcement có thể có future effective date.

---

# 33. Monetary policy

```axiom id="mon-policy"
struct MonetaryPolicy {
    authority: CentralBankId
    objective: PolicyObjective[]
    framework: MonetaryPolicyFramework
    instruments: PolicyInstrument[]
    decision: PolicyDecision
}
```

---

# 34. Policy objectives

Framework có thể khai báo:

```text id="policy-objectives"
PriceStability
InflationTarget
ExchangeRateStability
MonetaryStability
FinancialStability
EmploymentConsideration
GrowthConsideration
MultipleObjectives
```

Axiom không mặc định một objective universal.

---

# 35. Policy instrument

```text id="policy-instruments"
PolicyRate
ReserveRequirement
OpenMarketOperation
StandingFacility
AssetPurchase
AssetSale
FXIntervention
LiquidityFacility
CollateralRule
ForwardGuidance
OtherAuthorizedInstrument
```

---

# 36. Monetary policy decision

```axiom id="policy-decision"
struct PolicyDecision {
    id: PolicyDecisionId
    authority: CentralBankId
    decision_time: Timestamp
    instrument_changes: PolicyChange[]
    rationale_ref: DocumentRef?
    effective_time: Timestamp
}
```

---

# 37. Policy decision ≠ forecast

Một policy decision có thể dựa trên forecast nhưng hai object khác nhau.

---

# 38. Open market operation

```axiom id="omo"
struct OpenMarketOperation {
    id: OperationId
    type: OMOperationType
    instrument: InstrumentRef
    amount: MonetaryAmount
    price_or_rate: Decimal?
    maturity: Date?
}
```

Types:

```text id="omo-types"
Purchase
Sale
Repo
ReverseRepo
Swap
Other
```

---

# 39. Central-bank asset purchase

```text id="cb-purchase"
CentralBank
→ PurchaseOrder
→ MarketExecution
→ Settlement
→ BalanceSheetUpdate
```

Market execution delegate:

```text id="cb-market"
AXMARKET
```

---

# 40. Central-bank asset sale

Ngược lại:

```text id="cb-sale"
Asset
→ MarketSale
→ Cash/ReserveReceipt
→ BalanceSheetUpdate
```

---

# 41. Repo operation

```axiom id="cb-repo"
struct CentralBankRepo {
    counterparty: EntityRef
    collateral: CollateralRef
    cash: MonetaryAmount
    rate: Rate
    maturity: Date
}
```

---

# 42. Standing facilities

```text id="standing"
DepositFacility
LendingFacility
EmergencyLiquidityFacility
DiscountWindowLikeFacility
FXSwapFacility
```

---

# 43. Facility eligibility

Mỗi facility có:

```text id="facility-eligibility"
eligible_counterparties
eligible_collateral
haircuts
maturity
pricing
limits
documentation
```

---

# 44. Liquidity operation

```axiom id="liquidity-operation"
struct LiquidityOperation {
    facility: FacilityId
    participant: ParticipantId
    amount: MonetaryAmount
    collateral: CollateralRef?
    rate: Rate
    maturity: Date
}
```

---

# 45. Liquidity ≠ solvency

Runtime phải giữ invariant:

```text id="liquidity-solvency"
LiquiditySupport ≠ SolvencySupport
```

Một institution nhận liquidity không đồng nghĩa institution đó solvent.

---

# 46. Emergency liquidity

Emergency facility có:

```text id="emergency-liquidity"
authorization
eligibility
collateral
limit
maturity
pricing
disclosure_policy
```

Legal authority thuộc jurisdiction layer.

---

# 47. Reserve requirement

```axiom id="reserve-requirement"
struct ReserveRequirement {
    institution_class: InstitutionClass
    reserve_ratio: Ratio
    calculation_base: AggregateDefinition
    maintenance_period: TimeRange
}
```

---

# 48. Reserve requirement calculation

```text id="reserve-calc"
RequiredReserve =
EligibleBase × ReserveRatio
```

---

# 49. Reserve remuneration

```axiom id="reserve-remuneration"
struct ReserveRemuneration {
    eligible_balance: Money
    rate: Rate
    period: TimeRange
}
```

---

# 50. Monetary policy transmission

Canonical graph:

```text id="transmission"
PolicyRate
 ↓
MoneyMarketRate
 ↓
BankFundingCost
 ↓
Loan/DepositRates
 ↓
CreditDemand
 ↓
Spending / Investment
 ↓
AggregateDemand
 ↓
Prices / Output / Employment
```

Đây là model relationship, không phải guarantee.

---

# 51. Transmission model

```axiom id="transmission-model"
struct MonetaryTransmissionModel {
    variables: Variable[]
    relationships: Relationship[]
    lags: LagModel[]
    uncertainty: UncertaintyModel
}
```

---

# 52. Policy lag

Các lag phải explicit:

```text id="policy-lag"
decision_lag
implementation_lag
transmission_lag
data_lag
response_lag
```

---

# 53. Inflation

Axiom phải phân biệt:

```text id="inflation"
PriceLevel
PriceIndex
InflationRate
CoreInflation
HeadlineInflation
ExpectedInflation
ObservedInflation
ForecastInflation
```

---

# 54. Inflation rate

Generic:

```text id="inflation-rate"
InflationRate =
(P_t / P_{t-k}) - 1
```

với frequency `k` explicit.

---

# 55. Price index

```axiom id="price-index"
struct PriceIndex {
    id: IndexId
    basket: BasketDefinition
    base_period: Period
    methodology: IndexMethod
    value: Decimal
}
```

---

# 56. Inflation expectation

```axiom id="inflation-expectation"
struct InflationExpectation {
    horizon: Duration
    expected_rate: Rate
    source: ExpectationSource
}
```

Sources:

```text id="expectation-source"
Survey
MarketImplied
Model
AgentBased
CentralBankProjection
```

---

# 57. Inflation target

```axiom id="inflation-target"
struct InflationTarget {
    target: Rate
    tolerance: Band?
    horizon: Duration
}
```

---

# 58. Target ≠ guarantee

```text id="target-not-guarantee"
InflationTarget ≠ InflationOutcome
```

---

# 59. Monetary shock

Simulation primitives:

```text id="mon-shocks"
PolicyRateShock
MoneySupplyShock
LiquidityShock
FXShock
ReserveShock
DemandShock
SupplyShock
ConfidenceShock
```

---

# 60. Monetary scenario

```axiom id="mon-scenario"
struct MonetaryScenario {
    baseline: ScenarioRef
    shocks: Shock[]
    policy_rule: PolicyRuleRef?
    horizon: Duration
}
```

---

# 61. Policy rule

Abstract:

```axiom id="policy-rule"
struct PolicyRule {
    inputs: Variable[]
    target: Variable
    response_function: FunctionRef
}
```

Không hard-code một specific policy rule.

---

# 62. Scenario result

```axiom id="scenario-result"
struct MonetaryScenarioResult {
    path: VariablePath[]
    confidence: ConfidenceInterval[]
    assumptions: Assumption[]
    provenance: Provenance
}
```

---

# 63. Simulation status

Mọi model output phải mang:

```text id="simulation-status"
Observed
Estimated
Forecast
Simulated
StressScenario
Counterfactual
```

---

# 64. Central-bank balance sheet

```axiom id="cb-bs"
struct CentralBankBalanceSheet {
    assets: BalanceSheetItem[]
    liabilities: BalanceSheetItem[]
    capital: BalanceSheetItem[]
    timestamp: Timestamp
}
```

---

# 65. Typical asset categories

```text id="cb-assets"
GovernmentSecurities
ForeignReserves
LoansToBanks
RepoClaims
Gold
OtherReserveAssets
```

---

# 66. Typical liability categories

```text id="cb-liabilities"
CurrencyInCirculation
BankReserves
GovernmentDeposits
ForeignOfficialDeposits
OtherLiabilities
```

Exact composition remains jurisdiction-specific.

---

# 67. Monetary issuance

Issuance operation:

```axiom id="money-issuance"
issue_currency(
    currency,
    amount,
    authority,
    reason
)
```

Must create:

```text id="issuance-state"
MonetaryEvent
BalanceSheetMutation
AuditEvent
```

---

# 68. Monetary withdrawal

```axiom id="money-withdrawal"
withdraw_currency(
    currency,
    amount,
    authority,
    reason
)
```

Không xóa historical issuance records.

---

# 69. Cash

Physical cash representation:

```axiom id="cash"
struct CashPosition {
    currency: CurrencyId
    amount: MonetaryAmount
    form: CashForm
}
```

---

# 70. Cash issuance

```text id="cash-issuance"
Design
→ ManufactureRef
→ Issue
→ Circulation
→ Withdrawal
→ Destruction
```

Physical production thuộc appropriate manufacturing layer.

---

# 71. Digital central-bank money

Runtime có thể biểu diễn:

```text id="digital-cb-money"
CentralBankDigitalMoney
Wholesale
Retail
TokenBased
AccountBased
```

Không mặc định rằng mọi monetary system phải có CBDC.

---

# 72. CBDC architecture

```axiom id="cbdc"
struct DigitalCentralBankMoney {
    currency: CurrencyId
    model: CBDCModel
    account_or_token_system: DigitalMoneyProvider
}
```

---

# 73. CBDC model

```text id="cbdc-model"
AccountBased
TokenBased
Hybrid
WholesaleOnly
RetailOnly
```

---

# 74. CBDC privacy

Policy attributes:

```text id="cbdc-privacy"
transaction_visibility
identity_requirement
offline_support
programmability
holding_limits
```

---

# 75. Programmable money boundary

Programmability must not silently grant arbitrary authority.

```text id="programmable-money"
MoneyRule ≠ LegalAuthority
MoneyRule ≠ UniversalPolicy
```

---

# 76. Monetary settlement

Central-bank money can serve as settlement asset:

```text id="mon-settlement"
Participant
→ ReserveTransfer
→ FinalSettlement
```

Settlement infrastructure integration:

```text
AXMARKET
AXBANKING
AXFINANCE
```

---

# 77. Payment-system interface

```axiom id="payment-interface"
struct MonetarySettlementEndpoint {
    currency: CurrencyId
    settlement_type: SettlementType
    finality_model: FinalityModel
}
```

---

# 78. Settlement finality

Types:

```text id="finality"
Immediate
Batch
Deferred
Conditional
Reversible
Irrevocable
```

---

# 79. Finality invariant

A settlement marked `Irrevocable` cannot be silently reversed.

Reversal must be a separate compensating event where legally applicable.

---

# 80. Foreign-exchange reserves

```axiom id="fx-reserves"
struct FXReservePortfolio {
    authority: CentralBankId
    assets: ReserveAsset[]
    valuation_currency: CurrencyId
    valuation_time: Timestamp
}
```

---

# 81. Reserve assets

```text id="reserve-assets"
ForeignCurrency
ForeignGovernmentSecurity
Gold
SDRLikeAsset
Deposits
OtherAuthorizedReserveAsset
```

---

# 82. Reserve asset ≠ money

Foreign government securities held as reserves are assets of the central bank, not automatically domestic money.

---

# 83. Reserve adequacy

Runtime can calculate metrics:

```text id="reserve-adequacy"
ImportCoverage
ShortTermDebtCoverage
BroadMoneyCoverage
ExternalLiquidityCoverage
StressCoverage
```

Methodology must be explicit.

---

# 84. FX intervention

```axiom id="fx-intervention"
struct FXIntervention {
    authority: CentralBankId
    currency_pair: CurrencyPair
    side: FXSide
    amount: MonetaryAmount
    execution_ref: TradeRef?
    reserve_impact: MonetaryAmount
}
```

---

# 85. Intervention lifecycle

```text id="intervention-life"
Proposed
→ Authorized
→ Executing
→ Executed
→ Settled
→ Reconciled
```

---

# 86. Sterilized intervention

Support:

```text id="sterilized"
FXPurchase
+
LiquidityOffsetOperation
```

Simulation must track both legs.

---

# 87. Unsterilized intervention

```text id="unsterilized"
FXPurchase
→ DomesticLiquidityChange
```

unless offset elsewhere.

---

# 88. Exchange-rate regime

```text id="fx-regime"
FreeFloat
ManagedFloat
CrawlingPeg
FixedPeg
CurrencyBoard
MonetaryUnion
MultipleRateSystem
Other
```

---

# 89. Peg

```axiom id="peg"
struct ExchangeRatePeg {
    pair: CurrencyPair
    central_rate: Decimal
    band: Ratio?
    intervention_rule: InterventionRule
}
```

---

# 90. Currency board

```text id="currency-board"
CurrencyBoard
├── reserve_rule
├── issuance_rule
├── redemption_rule
└── exchange_rate_rule
```

---

# 91. Monetary union

Một monetary union:

```text id="union"
MonetaryUnion
├── MemberJurisdiction[]
├── SharedCurrency
├── SharedMonetaryAuthority
└── SharedPolicyFramework
```

---

# 92. Multiple currencies

Một civilization instance có thể chứa:

```text id="multi-currency"
domestic_currency
foreign_currency
regional_currency
reserve_currency
digital_currency
```

---

# 93. Currency conversion graph

```text id="fx-graph"
USD
├── EUR
├── JPY
├── GBP
└── VND
```

FX engine có thể tìm conversion path.

---

# 94. Triangular consistency

Nếu rates A/B, B/C và A/C tồn tại, engine có thể phát hiện:

```text id="triangular"
implied_rate ≠ quoted_rate
```

và tạo arbitrage/anomaly signal.

---

# 95. FX arbitrage boundary

Signal:

```text id="fx-arbitrage"
FXInconsistencySignal
```

không phải guaranteed executable arbitrage.

Fees, latency, liquidity và settlement phải được tính.

---

# 96. Interest-rate curve

```axiom id="rate-curve"
struct InterestRateCurve {
    currency: CurrencyId
    tenor_points: CurvePoint[]
    methodology: CurveMethod
    timestamp: Timestamp
}
```

---

# 97. Yield curve

Có thể biểu diễn:

```text id="yield-curve"
PolicyRate
Overnight
1M
3M
6M
1Y
2Y
5Y
10Y
30Y
```

Nhưng tenor set không fixed.

---

# 98. Term structure

Native abstraction:

```axiom id="term-structure"
struct TermStructure {
    reference: ReferenceRate
    points: CurvePoint[]
}
```

---

# 99. Reference rate

```text id="reference-rate"
Official
MarketObserved
TransactionBased
ModelDerived
Policy
```

---

# 100. Interest-rate expectations

```text id="rate-expectation"
ExpectedPolicyPath
ForwardRate
MarketImpliedPath
SurveyPath
ModelPath
```

Không nhầm expected path với actual future policy.

---

# 101. Monetary transmission to banking

```text id="mon-banking"
AXMONETARY
    ↓
Reserve / Policy Conditions
    ↓
AXBANKING
    ↓
Funding
    ↓
Credit
    ↓
AXFINANCE
```

---

# 102. Credit-money interaction

Runtime có thể model:

```text id="credit-money"
LoanCreation
→ DepositCreation
→ Repayment
→ DepositReduction
```

Đây là model accounting/monetary-system behavior, không phải assertion rằng every lending event mechanically creates identical broad-money effects under every framework.

---

# 103. Bank money

```axiom id="bank-money"
struct BankMoney {
    bank: EntityRef
    account: AccountRef
    currency: CurrencyId
    amount: MonetaryAmount
}
```

---

# 104. Bank deposit boundary

Commercial-bank deposit thuộc:

```text id="deposit-boundary"
AXBANKING
```

AXMONETARY chỉ mô hình hóa aggregate/monetary-system effects và central-bank interface.

---

# 105. Deposit aggregation

```axiom id="deposit-aggregate"
aggregate_deposits(
    institution_scope,
    currency,
    date
)
```

---

# 106. Money multiplier model

Không đưa một fixed multiplier vào core.

Thay vào đó:

```axiom id="money-multiplier"
struct MoneyCreationModel {
    reserve_behavior
    lending_behavior
    currency_preference
    capital_constraints
    liquidity_constraints
}
```

---

# 107. Velocity

```axiom id="velocity"
struct MoneyVelocity {
    aggregate: AggregateId
    nominal_output: MonetaryAmount
    money_stock: MonetaryAmount
    period: Period
}
```

---

# 108. Velocity calculation

```text id="velocity-formula"
V = NominalOutput / MoneyStock
```

Methodology phải ghi rõ nominal-output definition và aggregate.

---

# 109. Monetary identity

Runtime có thể represent identities như:

```text id="mon-identity"
M × V = P × Y
```

nhưng không coi identity accounting này là causal law.

---

# 110. Seigniorage

```axiom id="seigniorage"
struct Seigniorage {
    currency: CurrencyId
    issuance_value: MonetaryAmount
    production_cost: MonetaryAmount
    related_income: MonetaryAmount
    period: Period
}
```

---

# 111. Central-bank profit

```text id="cb-profit"
InterestIncome
+
FeeIncome
+
ValuationChanges
-
InterestExpense
-
OperatingCosts
-
OtherCosts
```

Accounting semantics delegate to `AXFINANCE`.

---

# 112. Central-bank balance-sheet risk

Metrics:

```text id="cb-risk"
DurationRisk
FXRisk
CreditRisk
MarketRisk
LiquidityRisk
CollateralRisk
```

---

# 113. Reserve currency risk

Foreign reserve portfolio must expose:

```text id="reserve-risk"
currency_exposure
duration
credit_quality
liquidity
concentration
```

---

# 114. Gold reserve

Gold can be represented as:

```axiom id="gold-reserve"
ReserveAsset {
    asset_class: Gold
    quantity
    valuation_source
}
```

No assumption that gold is money.

---

# 115. SDR-like reserve asset

Generic abstraction:

```axiom id="reserve-unit"
struct ReserveUnit {
    name: String
    issuer: EntityRef
    composition: BasketDefinition
}
```

---

# 116. Reserve basket

```text id="reserve-basket"
CurrencyWeight[]
valuation_method
rebalance_schedule
```

---

# 117. Monetary crisis

Simulation state:

```text id="mon-crisis"
Normal
→ Stress
→ LiquidityStress
→ CurrencyStress
→ BankingSpillover
→ Stabilization
→ Recovery
```

Không phải mọi stress event đều phải đi qua toàn bộ chain.

---

# 118. Currency crisis simulation

Variables:

```text id="currency-crisis"
FXReserve
CapitalFlow
InterestDifferential
ImportDemand
ExportRevenue
ExternalDebt
Confidence
```

---

# 119. Bank run monetary simulation

```text id="bank-run"
DepositWithdrawal
→ BankLiquidity
→ ReserveDemand
→ InterbankMarket
→ CentralBankFacility
→ FX/AssetMarket
```

---

# 120. Liquidity cascade

```text id="liquidity-cascade"
Shock
↓
Withdrawals
↓
ReserveDemand
↓
AssetSales
↓
MarketPriceImpact
↓
CollateralValue
↓
MarginPressure
↓
FurtherSales
```

---

# 121. Monetary-fiscal interaction

`AXMONETARY` có interface:

```text id="mon-fiscal"
AXMONETARY ↔ AXGOV
```

để model:

```text
government deposits
government securities
fiscal transfers
tax flows
debt issuance
```

Không gộp monetary policy và fiscal policy thành một object.

---

# 122. Government account

```axiom id="gov-account"
struct GovernmentMonetaryAccount {
    authority: EntityRef
    currency: CurrencyId
    balance: MonetaryAmount
}
```

---

# 123. Government debt interface

Government securities thuộc:

```text id="gov-debt"
AXFINANCE / AXMARKET
```

Central-bank holdings có thể được tham chiếu từ `AXMONETARY`.

---

# 124. Debt monetization model

Nếu simulation cần model:

```text id="debt-monetization"
GovernmentDebt
→ CentralBankPurchase
→ ReserveCreation
```

đây phải là explicit scenario, không phải implicit accounting rule.

---

# 125. Fiscal dominance scenario

Simulation abstraction:

```axiom id="fiscal-dominance"
struct FiscalMonetaryScenario {
    fiscal_path
    debt_path
    monetary_rule
    financing_rule
}
```

---

# 126. Monetary sovereignty

Model attribute:

```axiom id="mon-sovereignty"
struct MonetaryFramework {
    currency_issuer
    exchange_regime
    reserve_framework
    convertibility
    capital_controls
}
```

---

# 127. Capital controls

```text id="capital-controls"
InflowControl
OutflowControl
FXPurchaseControl
FXSaleControl
TransferControl
AccountRestriction
```

Legal authority thuộc `AXLAW/AXGOV`.

---

# 128. Capital-flow statistics

```axiom id="capital-flow"
struct CapitalFlow {
    direction: FlowDirection
    currency: CurrencyId
    amount: MonetaryAmount
    sector: SectorRef
    period: Period
}
```

---

# 129. Balance of payments interface

```text id="bop"
CurrentAccount
CapitalAccount
FinancialAccount
ReserveAssets
ErrorsAndOmissions
```

Statistical framework versioned.

---

# 130. External position

```axiom id="external-position"
struct ExternalPosition {
    assets: MonetaryAmount
    liabilities: MonetaryAmount
    currency: CurrencyId
    valuation_time: Timestamp
}
```

---

# 131. Net international position

```text id="nipp"
NetInternationalPosition =
ExternalAssets - ExternalLiabilities
```

Methodology must include valuation and currency conversion.

---

# 132. Monetary statistics API

```text id="mon-api"
monetary.aggregate()
monetary.base()
monetary.reserves()
monetary.currency()
monetary.policy_rate()
monetary.fx_rate()
monetary.balance_sheet()
monetary.liquidity()
```

---

# 133. Policy API

```text id="policy-api"
monetary.policy.propose()
monetary.policy.announce()
monetary.policy.schedule()
monetary.policy.execute()
monetary.policy.history()
```

`execute()` yêu cầu authority capability.

---

# 134. Reserve API

```text id="reserve-api"
reserve.balance()
reserve.transfer()
reserve.requirement()
reserve.excess()
reserve.collateral()
```

---

# 135. FX API

```text id="fx-api"
fx.quote()
fx.convert()
fx.forward()
fx.intervention()
fx.reserve()
fx.exposure()
```

---

# 136. Simulation API

```text id="mon-sim-api"
monetary.simulate()
monetary.stress()
monetary.counterfactual()
monetary.forecast()
monetary.replay()
```

---

# 137. DSL — monetary authority

```axiom id="dsl-authority"
monetary_authority StateBank {
    currency: VND

    objectives {
        price_stability
        financial_stability
    }

    policy_rate: target_rate
}
```

---

# 138. DSL — currency

```axiom id="dsl-currency"
currency VND {
    issuer: StateBank
    minor_unit: 2
    status: circulating
}
```

---

# 139. DSL — policy rule

```axiom id="dsl-policy-rule"
policy_rule InflationResponse {
    input inflation_gap
    input output_gap

    response {
        inflation_gap * alpha
        output_gap * beta
    }
}
```

---

# 140. DSL — reserve requirement

```axiom id="dsl-reserve"
reserve_requirement CommercialBanks {
    ratio: 0.05
    base: eligible_deposits
    maintenance: monthly
}
```

---

# 141. DSL — FX regime

```axiom id="dsl-fx"
exchange_regime ManagedFloat {
    currency: VND
    reference: USD
    intervention: rule_based
}
```

---

# 142. DSL — monetary simulation

```axiom id="dsl-simulation"
simulate_monetary_system {
    horizon: 20y

    shocks {
        policy_rate: +200bp
        oil_price: +30%
        capital_outflow: +15%
    }

    outputs {
        inflation
        fx
        reserves
        credit
        output
    }
}
```

---

# 143. Native IR

```text id="mon-ir"
MON_CURRENCY
MON_ISSUE
MON_WITHDRAW
MON_RESERVE
MON_RESERVE_TRANSFER
MON_POLICY
MON_POLICY_RATE
MON_OMO
MON_REPO
MON_FACILITY
MON_MARGIN
MON_FX
MON_FX_CONVERT
MON_FX_INTERVENTION
MON_RESERVE_PORTFOLIO
MON_MONEY_AGGREGATE
MON_BALANCE_SHEET
MON_PRICE_INDEX
MON_INFLATION
MON_YIELD_CURVE
MON_TRANSMISSION
MON_SIMULATION
MON_STRESS
MON_REPLAY
```

---

# 144. Deterministic monetary simulation

Same:

```text id="mon-determinism"
initial_state
+
event_stream
+
model_version
+
parameters
+
random_seed
```

phải tạo cùng deterministic output.

---

# 145. Simulation reproducibility

Mọi simulation phải lưu:

```text id="mon-provenance"
seed
model_version
parameter_set
data_vintage
software_version
scenario_id
```

---

# 146. Model provenance

Không cho phép output:

```text id="mon-provenance-rule"
Forecast
```

mà không biết model/data provenance.

---

# 147. AI monetary analyst

AI có thể:

```text id="mon-ai"
summarize_data
detect_regime_change
analyze_transmission
generate_scenarios
stress_test
compare_policy_paths
explain_model_output
```

---

# 148. AI policy recommendation

AI có thể tạo:

```text id="mon-ai-recommend"
PolicyProposal
```

nhưng:

```text id="mon-ai-authority"
PolicyProposal ≠ PolicyDecision
```

---

# 149. Policy authority capability

```text id="mon-policy-cap"
monetary.policy.read
monetary.policy.propose
monetary.policy.announce
monetary.policy.execute
monetary.policy.emergency
```

Các capability phải độc lập.

---

# 150. AI authority boundary

AI agent mặc định chỉ có:

```text id="mon-ai-default"
monetary.data.read
monetary.analysis.run
monetary.simulation.run
```

Không có:

```text id="mon-ai-no-default"
monetary.policy.execute
monetary.currency.issue
monetary.fx.intervene
```

nếu chưa được cấp explicit authority.

---

# 151. Currency issuance authority

Capability:

```text id="issue-cap"
monetary.currency.issue
monetary.currency.withdraw
```

là high-trust capability.

---

# 152. Reserve-transfer authority

```text id="reserve-cap"
monetary.reserve.transfer
```

phải được tách khỏi:

```text
monetary.reserve.read
```

---

# 153. Emergency policy

Emergency action phải có:

```text id="emergency-policy"
authority
reason
scope
duration
limits
audit
review
```

---

# 154. Emergency expiry

Emergency authority không được tồn tại vô thời hạn nếu policy framework yêu cầu expiration.

---

# 155. Audit

Immutable event types:

```text id="mon-audit"
CurrencyIssued
CurrencyWithdrawn
ReserveCreated
ReserveTransferred
PolicyChanged
RateChanged
FacilityGranted
CollateralAccepted
FXInterventionExecuted
ReserveAssetChanged
EmergencyAction
```

---

# 156. Monetary event sourcing

Monetary state có thể reconstruct từ:

```text id="mon-events"
MonetaryEventLog
```

với snapshots để tăng tốc recovery.

---

# 157. Monetary state checkpoint

Checkpoint:

```text id="mon-checkpoint"
currency_state
reserve_state
policy_state
facility_state
balance_sheet_state
fx_reserve_state
```

---

# 158. Recovery

```text id="mon-recovery"
snapshot
→ event_replay
→ invariant_validation
→ reconciliation
→ resume
```

---

# 159. Reconciliation

Phải reconcile:

```text id="mon-reconcile"
AXMONETARY
↔ AXBANKING
↔ AXFINANCE
↔ AXMARKET
↔ AXGOV
```

---

# 160. Monetary invariant

```text id="mon-invariant-1"
currency amount
must always carry currency identity
```

---

# 161. Currency invariant

```text id="mon-invariant-2"
A currency cannot silently change issuer or denomination.
```

---

# 162. Reserve invariant

```text id="mon-invariant-3"
reserve transfer cannot create two-sided balance inconsistencies.
```

---

# 163. Policy invariant

```text id="mon-invariant-4"
policy announcement cannot mutate effective policy before effective time.
```

---

# 164. Rate invariant

```text id="mon-invariant-5"
historical policy rates are immutable facts once finalized.
```

Revisions phải là explicit correction events nếu framework cho phép.

---

# 165. Aggregate invariant

```text id="mon-invariant-6"
monetary aggregate value must reference its definition and vintage.
```

---

# 166. FX invariant

```text id="mon-invariant-7"
FX conversion requires explicit rate source and timestamp.
```

---

# 167. FX reserve invariant

```text id="mon-invariant-8"
reserve asset valuation must include valuation currency and source.
```

---

# 168. Intervention invariant

```text id="mon-invariant-9"
FX intervention must reconcile with reserve-portfolio change.
```

---

# 169. Balance-sheet invariant

```text id="mon-invariant-10"
central-bank monetary events must produce auditable balance-sheet effects.
```

---

# 170. Policy authority invariant

```text id="mon-invariant-11"
AI analysis cannot become policy execution without explicit capability.
```

---

# 171. Simulation invariant

```text id="mon-invariant-12"
simulation cannot mutate live monetary state.
```

---

# 172. Forecast invariant

```text id="mon-invariant-13"
forecast output must not be represented as observed data.
```

---

# 173. Data-vintage invariant

```text id="mon-invariant-14"
revised data must preserve prior vintage provenance.
```

---

# 174. Monetary accounting invariant

```text id="mon-invariant-15"
currency issuance and withdrawal must be represented as explicit events.
```

---

# 175. Liquidity invariant

```text id="mon-invariant-16"
liquidity provision cannot be inferred as solvency certification.
```

---

# 176. Central-bank asset invariant

```text id="mon-invariant-17"
foreign reserve assets remain distinct from domestic monetary liabilities.
```

---

# 177. Exchange-rate invariant

```text id="mon-invariant-18"
FXRate ≠ FundamentalValue
```

---

# 178. Monetary-policy invariant

```text id="mon-invariant-19"
MonetaryPolicy ≠ FiscalPolicy
```

---

# 179. Recommendation invariant

```text id="mon-invariant-20"
PolicyRecommendation ≠ PolicyDecision
```

---

# 180. Legal authority invariant

```text id="mon-invariant-21"
AXMONETARY cannot invent legal authority not provided by AXLAW/AXGOV.
```

---

# 181. Settlement invariant

```text id="mon-invariant-22"
final settlement must have explicit finality semantics.
```

---

# 182. Replay invariant

```text id="mon-invariant-23"
same monetary event stream + same model version
=
same deterministic state
```

---

# 183. Cross-domain invariant

```text id="mon-invariant-24"
AXMONETARY cannot directly mutate AXBANKING customer balances
without the banking settlement interface.
```

---

# 184. Market invariant

```text id="mon-invariant-25"
central-bank market operations executed through AXMARKET
must retain market execution provenance.
```

---

# 185. Security profiles

```text id="mon-profiles"
AXMONETARY_NONE
AXMONETARY_CORE
AXMONETARY_CURRENCY
AXMONETARY_RESERVES
AXMONETARY_POLICY
AXMONETARY_RATES
AXMONETARY_LIQUIDITY
AXMONETARY_OMO
AXMONETARY_FX
AXMONETARY_CBDC
AXMONETARY_STATISTICS
AXMONETARY_SIMULATION
AXMONETARY_AI
AXMONETARY_ANALYTICS
AXMONETARY_DISTRIBUTED
AXMONETARY_GPU
AXMONETARY_GLOBAL
AXMONETARY_ADMIN
AXMONETARY_FULL
```

---

# 186. Minimal profile

`AXMONETARY_CORE` chỉ cần:

```text
Currency
MonetaryAmount
FXRate
MonetaryAggregate
CentralBank
Reserve
PolicyRate
MonetaryEvent
```

---

# 187. Global profile

`AXMONETARY_GLOBAL` thêm:

```text
multi_currency
FX
reserve_management
cross_border_flows
monetary_union
global_simulation
```

---

# 188. GPU profile

GPU thích hợp cho:

```text
MonteCarlo
scenario_analysis
macro_simulation
FX_risk
reserve_optimization
policy_sensitivity
```

---

# 189. Distributed profile

Có thể partition theo:

```text
jurisdiction
currency
institution
time
scenario
```

Nhưng mỗi authoritative monetary ledger domain phải có một serialization authority rõ ràng.

---

# 190. Performance architecture

Hot paths:

```text id="mon-performance"
reserve_transfer
policy_state_lookup
FX_conversion
market_operation
monetary_event
statistics_aggregation
```

ưu tiên:

```text
compact IDs
preallocated memory
SoA
batch processing
zero-copy views
SIMD aggregation
```

---

# 191. Time-series storage

Monetary data ưu tiên:

```text id="mon-storage"
columnar
compressed
versioned
append-oriented
time-indexed
```

---

# 192. No GC hot path

Central-bank settlement/reserve-transfer engine không phụ thuộc GC.

---

# 193. Numerical precision

Money:

```text id="mon-precision"
DecimalFixed
```

ưu tiên cho authoritative accounting.

Simulation có thể dùng:

```text id="mon-sim-precision"
f64
f128/provider
fixed_point
decimal
```

theo model.

---

# 194. Rounding

Rounding policy phải explicit:

```text id="mon-rounding"
Bankers
HalfUp
HalfDown
Floor
Ceiling
Truncate
Custom
```

---

# 195. Monetary calculation provenance

Mọi derived metric có:

```text id="mon-derived"
formula
inputs
input_vintages
rounding
precision
timestamp
```

---

# 196. Statistical revision

Revision event:

```axiom id="mon-revision"
revise_series(
    series,
    vintage,
    reason
)
```

Không overwrite historical publication.

---

# 197. Scenario comparison

```axiom id="mon-compare"
compare_scenarios(
    baseline,
    alternative
)
```

Output:

```text id="mon-compare-output"
delta
assumptions
uncertainty
provenance
```

---

# 198. Sensitivity analysis

Có thể chạy:

```text id="mon-sensitivity"
policy_rate
inflation_expectation
FX
money_growth
credit_growth
velocity
```

---

# 199. Monte Carlo

Native API:

```axiom id="mon-mc"
monetary.monte_carlo {
    paths: 100000
    horizon: 20y
    seed: 42
}
```

---

# 200. Distribution outputs

```text id="mon-distribution"
mean
median
percentile
variance
tail_probability
confidence_interval
```

Không biến probabilistic result thành deterministic forecast.

---

# 201. Tail-risk model

Có thể expose:

```text id="mon-tail"
VaR
CVaR
ExpectedShortfall
StressLoss
LiquidityGap
ReserveDrawdown
```

Methodology explicit.

---

# 202. Global monetary network

```text id="global-network"
CentralBank
├── Currency
├── CommercialBanks
├── FXMarkets
├── PaymentSystems
├── Government
├── SecuritiesMarkets
└── ForeignCentralBanks
```

---

# 203. Central-bank network

Cross-border:

```text id="cb-network"
CB_A
 ↕ FX Swap
CB_B
 ↕ Reserve Transfer
CB_C
```

---

# 204. Swap line

```axiom id="swap-line"
struct CentralBankSwapLine {
    provider: CentralBankId
    recipient: CentralBankId
    currency_pair: CurrencyPair
    limit: MonetaryAmount
    maturity: Duration
    pricing: Rate
}
```

---

# 205. Swap-line lifecycle

```text id="swap-life"
Agreed
→ Activated
→ Drawn
→ Outstanding
→ Repaid
→ Closed
```

---

# 206. International liquidity

Global simulation can model:

```text id="intl-liquidity"
reserve_currency_supply
swap_lines
cross_border_funding
FX_liquidity
settlement_liquidity
```

---

# 207. Dollarization / foreign-currency use

Model:

```axiom id="foreign-currency-use"
struct CurrencyUsage {
    domestic_share: Ratio
    foreign_currency_shares: Ratio[]
    measurement_method: Method
}
```

Không mặc định domestic currency là only medium.

---

# 208. Currency substitution

Simulation variable:

```text id="currency-substitution"
currency_preference
deposit_currency
cash_currency
pricing_currency
settlement_currency
```

---

# 209. Inflation regime

Simulation có thể classify:

```text id="inflation-regime"
LowStable
TargetRange
Elevated
High
Disinflation
Deflation
Volatile
```

Đây là descriptive model state, không phải judgment.

---

# 210. Monetary regime transition

```text id="regime-transition"
RegimeDetected
→ EvidenceAccumulated
→ ModelUpdated
→ PolicyAnalysis
```

Không tự động đổi policy.

---

# 211. AI regime detection

AI có thể phát hiện:

```text id="ai-regime"
inflation_regime
liquidity_regime
FX_regime
credit_regime
volatility_regime
```

Output:

```text id="ai-regime-output"
RegimeSignal
```

---

# 212. Monetary digital twin

```axiom id="mon-twin"
struct MonetaryTwin {
    jurisdiction: JurisdictionRef
    currency: CurrencyId
    observed_state: MonetaryState
    estimated_state: MonetaryState
    forecast_state: MonetaryState
    simulation_state: MonetaryState
}
```

---

# 213. Digital-twin rule

```text id="mon-twin-rule"
ObservedState
≠
EstimatedState
≠
ForecastState
≠
SimulationState
```

---

# 214. Civilization monetary twin

```text id="civil-mon-twin"
Population
↓
Income
↓
Deposits
↓
Credit
↓
Money
↓
Prices
↓
Investment
↓
Production
↓
Income
```

---

# 215. Integration với AX671

`AX671` cung cấp macroeconomic environment:

```text id="ax671-integration"
GDP
Employment
Production
Consumption
Investment
Trade
FiscalActivity
```

`AXMONETARY` cung cấp:

```text id="axmon-output"
Money
Rates
Liquidity
FX
Reserves
MonetaryPolicy
```

---

# 216. Integration với AXBANKING

```text id="axbanking-integration"
AXMONETARY
    ↓
Reserves
PolicyRates
Liquidity
Settlement
    ↓
AXBANKING
    ↓
Deposits
Loans
Credit
Interbank
```

---

# 217. Integration với AXMARKET

```text id="axmarket-integration"
CentralBank
    ↓
OMO / FX / Repo
    ↓
AXMARKET
    ↓
Trade
    ↓
Clearing
    ↓
Settlement
```

---

# 218. Integration với AXINVEST

```text id="axinvest-integration"
Rates
FX
Liquidity
Inflation
Policy
    ↓
AXINVEST
    ↓
AssetAllocation
Portfolio
CapitalFlows
```

---

# 219. Integration với AXINSURANCE

```text id="axinsurance-integration"
Rates
Inflation
FX
CreditConditions
    ↓
AXINSURANCE
    ↓
Reserves
Assets
Pricing
Solvency
```

---

# 220. Integration với AXGOV

```text id="axgov-integration"
Government
    ↔
CentralBank
    ↔
MonetarySystem
```

qua explicit interfaces.

---

# 221. Global monetary feedback loop

```text id="global-feedback"
MONETARY POLICY
      ↓
FINANCIAL CONDITIONS
      ↓
BANKING
      ↓
CREDIT
      ↓
INVESTMENT
      ↓
PRODUCTION
      ↓
EMPLOYMENT / INCOME
      ↓
DEMAND
      ↓
PRICES
      ↓
MONETARY POLICY
```

---

# 222. Global FX loop

```text id="fx-loop"
Interest Differential
       ↓
Capital Flow
       ↓
FX Demand
       ↓
Exchange Rate
       ↓
Import Prices
       ↓
Inflation
       ↓
Monetary Policy
       ↓
Interest Differential
```

Đây là simulation graph, không phải deterministic causal guarantee.

---

# 223. Monetary crisis propagation

```text id="crisis-loop"
MONETARY SHOCK
      ↓
LIQUIDITY
      ↓
BANKING
      ↓
MARKETS
      ↓
CREDIT
      ↓
PRODUCTION
      ↓
INCOME
      ↓
DEPOSITS
      ↓
LIQUIDITY
```

---

# 224. Required test target

Mục tiêu:

```text id="mon-tests"
≥ 18,000 automated tests
≥ 1,800 architecture invariants
≥ 2,000 currency/FX tests
≥ 2,000 reserve/central-bank tests
≥ 2,000 policy/rate tests
≥ 2,000 monetary-statistics tests
≥ 2,500 simulation tests
≥ 1,500 security/authority tests
≥ 1,500 distributed/recovery tests
```

---

# 225. Test categories

```text id="mon-test-categories"
currency
money
aggregate
reserve
policy
rate
OMO
repo
facility
FX
intervention
CBDC
statistics
revision
simulation
stress
AI
security
distributed
recovery
reconciliation
performance
```

---

# 226. Security tests

Phải kiểm tra:

```text id="mon-security-tests"
unauthorized_currency_issue
unauthorized_reserve_transfer
unauthorized_policy_execution
unauthorized_fx_intervention
AI_authority_escalation
simulation_live_mutation
historical_data_tampering
reserve_double_spend
```

---

# 227. Numerical tests

Kiểm tra:

```text id="mon-numeric-tests"
rounding
currency_conversion
decimal_precision
overflow
underflow
negative_amount
rate_precision
yield_curve_interpolation
aggregate_calculation
```

---

# 228. Recovery tests

```text id="mon-recovery-tests"
snapshot_restore
event_replay
duplicate_event
sequence_gap
partial_commit
failover
cross-system_reconciliation
```

---

# 229. Simulation tests

```text id="mon-sim-tests"
seed_reproducibility
parameter_reproducibility
scenario_isolation
model_versioning
data_vintage
counterfactual_isolation
```

---

# 230. Acceptance criteria

`AXMONETARY 5.0` hoàn tất khi:

1. Currency có canonical identity.
2. Money được phân biệt khỏi wealth.
3. Central bank có native representation.
4. Reserve account có lifecycle.
5. Monetary aggregates có machine-readable definitions.
6. Policy rates có effective periods.
7. Rate corridor được hỗ trợ.
8. OMO được hỗ trợ.
9. Repo/reverse repo được hỗ trợ.
10. Standing facilities tồn tại.
11. Reserve requirements được mô hình hóa.
12. FX rates có provenance.
13. FX reserves được quản lý.
14. FX intervention được hỗ trợ.
15. Exchange-rate regimes được mô hình hóa.
16. Monetary policy có explicit authority.
17. Policy recommendation tách khỏi decision.
18. Central-bank balance sheet có native representation.
19. Monetary statistics có vintage/revision.
20. Inflation/price-index model tồn tại.
21. Monetary transmission model tồn tại.
22. Monetary simulation tồn tại.
23. Stress/counterfactual tồn tại.
24. CBDC có optional architecture.
25. Payment/settlement integration tồn tại.
26. AXBANKING integration tồn tại.
27. AXMARKET integration tồn tại.
28. AXFINANCE reconciliation tồn tại.
29. AXGOV/AXLAW authority boundary tồn tại.
30. AI không có policy execution mặc định.
31. Currency issuance là high-trust capability.
32. Simulation không thể mutate live state.
33. Hot path không phụ thuộc GC.
34. Native IR tồn tại.
35. Distributed recovery tồn tại.
36. ≥18,000 tests và ≥1,800 invariants được target.

---

# 231. Final AXMONETARY architecture

```text id="final-mon-arch"
                         AXMONETARY
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
    CURRENCY              CENTRAL BANK             FX
       │                      │                      │
       │                ┌─────┼─────┐               │
       │                │     │     │               │
       │             POLICY RESERVE LIQUIDITY        │
       │                │     │     │               │
       └────────────────┼─────┼─────┼───────────────┘
                        │     │     │
                        ▼     ▼     ▼
                     MONETARY STATE
                           │
              ┌────────────┼────────────┐
              │            │            │
           BANKING       MARKET       FINANCE
              │            │            │
              └────────────┼────────────┘
                           │
                         ECONOMY
                           │
                       CIVILIZATION
```

---

# 232. Financial architecture sau BOOTSTRAP-694

```text id="financial-stack"
AXFINANCE
    │
    ├── AXBANKING
    │
    ├── AXINSURANCE
    │
    ├── AXINVEST
    │
    ├── AXMARKET
    │
    └── AXMONETARY
```

Trong đó:

```text id="financial-roles"
AXFINANCE
    = financial truth / accounting

AXBANKING
    = deposits / credit / banking services

AXINSURANCE
    = risk transfer / reserves / claims

AXINVEST
    = investment / allocation / portfolio

AXMARKET
    = trading / clearing / settlement / market infrastructure

AXMONETARY
    = money / currency / reserves / monetary policy
```

---

# 233. Civilization-scale monetary loop

```text id="civil-money-loop"
CIVILIZATION
      ↓
ECONOMIC ACTIVITY
      ↓
INCOME
      ↓
BANKING
      ↓
MONEY
      ↓
SPENDING / INVESTMENT
      ↓
PRODUCTION
      ↓
PRICES
      ↓
MONETARY CONDITIONS
      ↓
BANKING / FINANCE
      ↓
CIVILIZATION
```

---

# 234. Final semantic contract

Axiom phải giữ:

```text id="semantic-contract"
AXMONETARY
    answers:
        What is money?
        What is a currency?
        What is the monetary base?
        How are reserves represented?
        What monetary-policy instruments exist?
        How do central-bank operations affect monetary state?
        How are FX reserves represented?
        How are monetary scenarios simulated?

AXBANKING
    answers:
        How do banks provide deposits and credit?

AXMARKET
    answers:
        How are financial instruments traded and settled?

AXFINANCE
    answers:
        How are financial facts accounted for?

AX671
    answers:
        How does monetary activity interact with the economy?
```

Không một layer nào được âm thầm thay thế layer khác.

---

# 235. Final architecture contract

```text id="final-contract"
CURRENCY
    ↓
MONEY
    ↓
BANK RESERVES
    ↓
BANKING
    ↓
CREDIT
    ↓
CAPITAL MARKETS
    ↓
INVESTMENT
    ↓
PRODUCTION
    ↓
INCOME
    ↓
PRICES
    ↓
MONETARY POLICY
    ↓
CURRENCY / MONEY
```

Đây trở thành **canonical monetary feedback architecture** của Axiom civilization runtime.

---

# 236. BOOTSTRAP-694 completion

**BOOTSTRAP-694 hoàn tất.**

Các boundary quan trọng nhất đã được khóa:

```text
Money ≠ Wealth
Currency ≠ Deposit
Reserve ≠ Deposit
PolicyRate ≠ MarketRate
Liquidity ≠ Solvency
MoneyCreation ≠ WealthCreation
MonetaryPolicy ≠ FiscalPolicy
Forecast ≠ Observation
Simulation ≠ Reality
Recommendation ≠ Authority
```

**Task kế tiếp: BOOTSTRAP-695 — Native AI Civilization-Scale Fiscal System, Government Budget, Taxation, Public Debt, Treasury, Government Spending, Transfers, Public Finance & Fiscal Policy Runtime 5.0.**
:::

Task kế tiếp đã được xác định là **BOOTSTRAP-695 — Fiscal / Treasury / Tax / Public Finance Runtime 5.0**; chuỗi có thể tiếp tục tự động theo cùng kiến trúc.