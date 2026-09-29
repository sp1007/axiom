Tiếp tục chuỗi đặc tả Axiom. Task này xây lớp tiền tệ nằm giữa banking, finance và capital markets, nhưng giữ ranh giới rõ với pháp luật/chính sách công và không biến AI thành cơ quan tiền tệ có thẩm quyền.

:::writing{variant="document" id="58314" title="BOOTSTRAP-694 — Native AI Civilization-Scale Monetary System, Central Banking, Money Supply, Interest Rates, Monetary Policy, Foreign Exchange Reserves, Currency Systems & Global Monetary Runtime 5.0"}
# BOOTSTRAP-694
## Native AI Civilization-Scale Monetary System, Central Banking, Money Supply, Interest Rates, Monetary Policy, Foreign Exchange Reserves, Currency Systems & Global Monetary Runtime 5.0

**Status:** Architecture Specification  
**Axiom Namespace:** `AXMONETARY`  
**Layer:** Civilization Economy / Monetary Infrastructure  
**Version:** 5.0

---

# 1. Mục tiêu

`AXMONETARY` là runtime native của Axiom cho việc biểu diễn, vận hành, quan sát và mô phỏng hệ thống tiền tệ ở quy mô:

- cá nhân;
- doanh nghiệp;
- ngân hàng;
- hệ thống ngân hàng;
- ngân hàng trung ương;
- nền kinh tế quốc gia;
- liên minh tiền tệ;
- hệ thống tiền tệ đa quốc gia;
- nền kinh tế toàn cầu;
- digital twin của hệ thống tiền tệ;
- mô phỏng kinh tế nhiều tác nhân.

AXMONETARY không thay thế:

- `AXFINANCE` — financial accounting và financial truth;
- `AXBANKING` — hoạt động ngân hàng;
- `AXMARKET` — giao dịch thị trường;
- `AXLAW` — luật và quyền lực pháp lý;
- `AXGOV` — quyết định chính sách nhà nước;
- `AXCIVILIZATION` — mô hình xã hội tổng thể.

AXMONETARY cung cấp **hạ tầng ngữ nghĩa và tính toán tiền tệ** mà các lớp đó sử dụng.

Kiến trúc:

```text
REAL ECONOMY
      │
      ▼
   AXCOMMERCE
      │
      ▼
   AXFINANCE
      │
      ▼
   AXBANKING
      │
      ▼
 AXMONETARY
      │
      ├──────────► AXMARKET
      │
      ├──────────► AXLAW / AXGOV
      │
      └──────────► AXCIVILIZATION
```

---

# 2. Nguyên tắc thiết kế

AXMONETARY phải tuân thủ các nguyên tắc:

1. Không nhầm tiền với của cải.
2. Không nhầm tiền tệ với tài sản.
3. Không nhầm tiền ngân hàng trung ương với tiền gửi ngân hàng thương mại.
4. Không nhầm thanh khoản với khả năng thanh toán.
5. Không nhầm dự trữ với vốn.
6. Không nhầm lãi suất chính sách với lãi suất thị trường.
7. Không nhầm mục tiêu với kết quả.
8. Không nhầm dự báo với thực tế.
9. Không nhầm mô phỏng với chính sách thật.
10. Không để AI tự có quyền ban hành chính sách tiền tệ.
11. Mọi thay đổi trạng thái tiền tệ quan trọng phải có provenance.
12. Monetary state phải có timestamp và version.
13. Các aggregate monetary statistics phải tái lập được.
14. Không hard-code giả thuyết kinh tế như một định luật runtime.
15. Có thể thay đổi mô hình tiền tệ mà không thay đổi compiler core.
16. Simulation state tuyệt đối không được tự động trở thành production state.

---

# 3. Semantic Boundary

Các phân biệt bắt buộc:

```text
Money                  ≠ Wealth
Money                  ≠ Currency
Currency               ≠ Asset
CurrencyUnit            ≠ CurrencyBalance
CentralBankMoney        ≠ CommercialBankDeposit
BankDeposit             ≠ CentralBankReserve
Reserve                 ≠ Capital
Liquidity               ≠ Solvency
PolicyRate              ≠ MarketRate
Target                  ≠ Outcome
Forecast                ≠ Fact
Estimate                ≠ Observation
Simulation              ≠ Policy
Recommendation          ≠ AuthorityDecision
FXReserve               ≠ SovereignWealth
Seigniorage             ≠ Profit
PaymentSettlement       ≠ MonetaryPolicy
CBDC                    ≠ CryptoAsset
MoneySupply             ≠ NationalWealth
Credit                  ≠ Money
Loan                    ≠ Deposit
NominalValue            ≠ RealValue
InflationRate           ≠ PriceLevel
ExchangeRate            ≠ CurrencyValue
ReserveRequirement      ≠ CapitalRequirement
QE                      ≠ MoneyPrinting
LiquidityInjection      ≠ FiscalSpending
CentralBankAsset        ≠ CentralBankReserve
```

Compiler/runtime phải bảo vệ các distinction này trong type system và semantic validation.

---

# 4. Namespace

```axiom
namespace AXMONETARY
```

Các module chính:

```text
AXMONETARY.CURRENCY
AXMONETARY.MONEY
AXMONETARY.ISSUANCE
AXMONETARY.RESERVES
AXMONETARY.RATES
AXMONETARY.POLICY
AXMONETARY.LIQUIDITY
AXMONETARY.CENTRAL_BANK
AXMONETARY.FX
AXMONETARY.EXCHANGE_REGIME
AXMONETARY.BALANCE_SHEET
AXMONETARY.MONETARY_AGGREGATES
AXMONETARY.TRANSMISSION
AXMONETARY.MACRO
AXMONETARY.SIMULATION
AXMONETARY.DIGITAL_MONEY
AXMONETARY.AI
AXMONETARY.GOVERNANCE
AXMONETARY.OBSERVABILITY
```

---

# 5. Currency Model

## 5.1 Currency

```axiom
struct Currency {
    id: CurrencyId
    code: CurrencyCode
    name: String
    issuer: IssuerRef
    unit_scale: Decimal
    status: CurrencyStatus
}
```

Ví dụ:

```axiom
VND
USD
EUR
JPY
GBP
```

Runtime không giới hạn số currency.

---

# 6. Currency Unit

```axiom
struct CurrencyUnit {
    currency: CurrencyId
    exponent: i32
}
```

Hỗ trợ:

```text
1 USD
0.01 USD
1 cent
1000 VND
```

Tiền không được biểu diễn đơn thuần bằng `f64`.

Monetary amounts phải sử dụng:

```text
fixed-point
decimal
integer minor-unit
```

tùy profile.

Hot path có thể sử dụng integer minor units.

---

# 7. Money

```axiom
struct Money {
    currency: CurrencyId
    amount: Decimal
}
```

Invariant:

```text
Money.currency == explicit currency
```

Không cho phép:

```axiom
100 + 200
```

nếu currency không xác định.

Phải viết:

```axiom
100 USD + 200 USD
```

hoặc:

```axiom
convert(100 USD, USD) + 200 USD
```

---

# 8. Monetary Instrument

```axiom
enum MoneyForm {
    PhysicalCash
    CentralBankReserve
    CommercialBankDeposit
    EMoney
    CBDCRetail
    CBDCWholesale
    SettlementBalance
    OtherAuthorizedMoney
}
```

`CryptoAsset` không mặc nhiên thuộc `MoneyForm`.

---

# 9. Monetary Claim

Một đơn vị tiền trong hệ thống có thể đồng thời được xem như một claim đối với issuer.

```axiom
struct MonetaryClaim {
    holder: AccountRef
    issuer: EntityRef
    denomination: CurrencyId
    amount: Decimal
    form: MoneyForm
}
```

Ví dụ:

```text
commercial bank deposit
    holder = customer
    issuer = bank
```

Trong khi:

```text
central bank reserve
    holder = commercial bank
    issuer = central bank
```

---

# 10. Money Hierarchy

AXMONETARY phải biểu diễn:

```text
Base Money
    ├── Physical Cash
    └── Central Bank Reserves

Broad Money
    ├── Bank Deposits
    ├── Other Eligible Deposits
    └── Other Monetary Instruments
```

Các aggregate cụ thể phải configurable theo jurisdiction/model.

Không hard-code:

```text
M1
M2
M3
```

như universal constants.

Thay vào đó:

```axiom
struct MonetaryAggregateDefinition {
    id: AggregateId
    components: ComponentSet
    inclusion_rules: RuleSet
    exclusion_rules: RuleSet
    jurisdiction: JurisdictionRef
    effective_from: Timestamp
}
```

---

# 11. Monetary Aggregate

```axiom
struct MonetaryAggregate {
    definition: AggregateDefinitionId
    timestamp: Timestamp
    value: Money
    confidence: Confidence
    provenance: ProvenanceRef
}
```

---

# 12. Central Bank

```axiom
struct CentralBank {
    id: CentralBankId
    jurisdiction: JurisdictionRef
    currency: CurrencyId
    balance_sheet: BalanceSheetRef
    policy_framework: MonetaryFrameworkRef
    reserve_system: ReserveSystemRef
}
```

CentralBank là một entity đặc biệt nhưng quyền lực pháp lý không được compiler mặc định.

Authority phải được cấp bởi:

```text
AXLAW
AXGOV
institutional policy
```

---

# 13. Central Bank Balance Sheet

```axiom
struct CentralBankBalanceSheet {
    assets: AssetBook
    liabilities: LiabilityBook
    capital: CapitalPosition
    timestamp: Timestamp
}
```

Assets có thể gồm:

```text
government securities
foreign reserves
gold
loans to financial institutions
other eligible assets
```

Liabilities có thể gồm:

```text
banknotes
bank reserves
government deposits
other eligible liabilities
```

---

# 14. Monetary Issuance

Money issuance phải là explicit event.

```axiom
struct MoneyIssuance {
    id: IssuanceId
    issuer: EntityRef
    currency: CurrencyId
    amount: Decimal
    form: MoneyForm
    reason: IssuanceReason
    timestamp: Timestamp
    authorization: AuthorizationRef
}
```

Không cho phép:

```axiom
money += x
```

trong authoritative monetary state.

Phải có:

```axiom
issue_money(...)
```

với provenance.

---

# 15. Redemption / Destruction

```axiom
struct MoneyRedemption {
    id: RedemptionId
    issuer: EntityRef
    currency: CurrencyId
    amount: Decimal
    form: MoneyForm
    timestamp: Timestamp
}
```

Ví dụ:

```text
central bank reserve destruction
cash withdrawal/deposit conversion
CBDC redemption
```

---

# 16. Seigniorage

```axiom
struct Seigniorage {
    issuer: EntityRef
    period: Period
    issuance_value: Money
    production_cost: Money
    accounting_result: Money
}
```

Không đồng nhất:

```text
seigniorage == accounting profit
```

Seigniorage semantics phải phụ thuộc accounting framework.

---

# 17. Interest Rate Model

```axiom
struct InterestRate {
    value: Decimal
    annualized: bool
    compounding: CompoundingRule
    day_count: DayCountConvention
}
```

Không dùng floating-point trong authoritative settlement calculations nếu có thể tránh.

---

# 18. Policy Rate

```axiom
struct PolicyRate {
    id: RateId
    central_bank: CentralBankId
    value: InterestRate
    effective_from: Timestamp
    effective_to: Timestamp?
}
```

Policy rate là **policy instrument**, không phải market outcome.

---

# 19. Monetary Policy Corridor

AXMONETARY hỗ trợ:

```text
floor
policy target
ceiling
```

Ví dụ:

```axiom
struct RateCorridor {
    floor: InterestRate
    target: InterestRate
    ceiling: InterestRate
}
```

Các instrument:

```text
deposit facility
main refinancing operation
standing lending facility
overnight facility
```

phải được biểu diễn độc lập.

---

# 20. Market Interest Rates

```axiom
struct MarketRate {
    market: MarketId
    tenor: Duration
    rate: InterestRate
    timestamp: Timestamp
    source: DataSourceRef
}
```

Không tự động suy ra:

```text
MarketRate == PolicyRate
```

---

# 21. Yield Curve

```axiom
struct YieldCurve {
    currency: CurrencyId
    timestamp: Timestamp
    points: SortedMap<Duration, InterestRate>
}
```

Các model:

```text
ObservedYieldCurve
EstimatedYieldCurve
ForwardCurve
ScenarioYieldCurve
SimulatedYieldCurve
```

phải phân biệt type-level.

---

# 22. Monetary Policy Framework

```axiom
struct MonetaryPolicyFramework {
    objective_set: ObjectiveSet
    target_variables: VariableSet
    policy_instruments: InstrumentSet
    reaction_model: Optional<ModelRef>
    decision_frequency: Duration
}
```

Objectives có thể gồm:

```text
price stability
employment-related objectives
exchange-rate objectives
financial-stability considerations
monetary aggregates
```

Nhưng runtime không tự xác định objective nào là hợp pháp.

Objective authority đến từ governance layer.

---

# 23. Policy Decision

```axiom
struct MonetaryPolicyDecision {
    id: DecisionId
    authority: AuthorityRef
    timestamp: Timestamp
    instruments: PolicyInstrumentSet
    rationale: DecisionRationale
    supporting_data: DatasetRef
    model_outputs: ModelOutputSet
    authorization: AuthorizationRef
}
```

AI chỉ có thể tạo:

```axiom
PolicyRecommendation
```

không được tự tạo:

```axiom
MonetaryPolicyDecision
```

trừ khi authority explicitly cấp quyền.

---

# 24. Monetary Policy Recommendation

```axiom
struct PolicyRecommendation {
    proposed_instruments: InstrumentSet
    scenarios: ScenarioSet
    expected_effects: EffectDistribution
    uncertainty: UncertaintySet
    model_provenance: ModelProvenance
}
```

Invariant:

```text
Recommendation ≠ Decision
```

---

# 25. Open Market Operations

```axiom
enum MarketOperation {
    Purchase
    Sale
    Repo
    ReverseRepo
    SecuritiesLending
    Other
}
```

```axiom
struct OpenMarketOperation {
    id: OperationId
    central_bank: CentralBankId
    operation: MarketOperation
    asset: AssetRef
    quantity: Quantity
    price: Money
    maturity: Duration?
    counterparties: CounterpartySet
}
```

---

# 26. Quantitative Easing / Tightening

QE/QT được mô hình hóa như policy operation.

```axiom
struct AssetPurchaseProgram {
    id: ProgramId
    target_assets: AssetClassSet
    target_amount: Money
    pace: QuantitySchedule
    duration: Duration
}
```

Runtime không định nghĩa:

```text
QE == money printing
```

vì balance-sheet mechanics có thể khác nhau.

---

# 27. Reserve Requirements

```axiom
struct ReserveRequirement {
    institution_class: InstitutionClass
    reserve_base: MonetaryBaseDefinition
    ratio: Decimal
    effective_from: Timestamp
}
```

Không nhầm:

```text
reserve requirement
```

với:

```text
capital requirement
```

---

# 28. Liquidity Operations

```axiom
struct LiquidityOperation {
    provider: EntityRef
    recipient: EntityRef
    amount: Money
    collateral: CollateralSet
    rate: InterestRate
    maturity: Duration
    operation_type: LiquidityOperationType
}
```

Hỗ trợ:

```text
repo
collateralized lending
emergency liquidity
intraday liquidity
standing facility
```

---

# 29. Lender of Last Resort

```axiom
struct EmergencyLiquidityAssistance {
    institution: InstitutionRef
    amount: Money
    collateral: CollateralSet
    haircut: Decimal
    maturity: Duration
    rate: InterestRate
    authorization: AuthorizationRef
}
```

ELL/LOLR phải có:

```text
explicit authority
collateral rules
limits
audit trail
expiry
repayment state
```

---

# 30. Liquidity vs Solvency

Runtime invariant:

```text
LiquidityState ≠ SolvencyState
```

Một entity có thể:

```text
liquid + insolvent
illiquid + solvent
liquid + solvent
illiquid + insolvent
```

Không được suy luận trạng thái này từ một biến duy nhất.

---

# 31. Foreign Exchange Reserve

```axiom
struct FXReserve {
    central_bank: CentralBankId
    assets: FXAssetSet
    valuation_currency: CurrencyId
    timestamp: Timestamp
}
```

Asset types:

```text
foreign currency deposits
foreign government securities
gold
eligible reserve assets
other recognized reserve assets
```

---

# 32. Reserve Composition

```axiom
struct ReserveComposition {
    currency: CurrencyId
    amount: Decimal
    asset_class: AssetClass
    liquidity_class: LiquidityClass
}
```

Hỗ trợ phân tích:

```text
currency concentration
duration
credit quality
liquidity
market risk
counterparty exposure
```

---

# 33. FX Rate

```axiom
struct FXRate {
    base: CurrencyId
    quote: CurrencyId
    rate: Decimal
    timestamp: Timestamp
    source: FXRateSource
}
```

Ví dụ:

```text
USD/VND
EUR/USD
JPY/USD
```

FXRate không phải intrinsic universal currency value.

---

# 34. FX Market Boundary

Giao dịch FX thuộc:

```text
AXMARKET
```

Monetary interpretation thuộc:

```text
AXMONETARY
```

Ví dụ:

```text
AXMARKET:
    USD/VND order
    trade
    clearing
    settlement

AXMONETARY:
    exchange-rate regime
    reserve policy
    intervention
    sterilization
```

---

# 35. Exchange Rate Regimes

```axiom
enum ExchangeRateRegime {
    FreeFloat
    ManagedFloat
    CrawlingPeg
    FixedPeg
    CurrencyBoard
    MonetaryUnion
    DualRate
    Custom
}
```

Không hard-code một regime làm mặc định toàn cầu.

---

# 36. FX Intervention

```axiom
struct FXIntervention {
    central_bank: CentralBankId
    direction: FXDirection
    currency: CurrencyId
    amount: Decimal
    execution_ref: MarketExecutionRef
    timestamp: Timestamp
    purpose: InterventionPurpose
}
```

Intervention phải phân biệt với:

```text
ordinary reserve management
market-making
liquidity operation
fiscal transaction
```

---

# 37. Sterilization

```axiom
struct SterilizationOperation {
    monetary_effect: Money
    offsetting_operation: OperationRef
    expected_net_effect: Money
}
```

Mục tiêu:

```text
FX intervention
        ↓
domestic liquidity change
        ↓
offsetting monetary operation
```

Không giả định sterilization luôn hoàn toàn hiệu quả.

---

# 38. Currency Convertibility

```axiom
struct ConvertibilityPolicy {
    currency: CurrencyId
    domestic_convertibility: ConvertibilityState
    capital_account_convertibility: ConvertibilityState
    restrictions: RestrictionSet
}
```

Capital controls thuộc authority của:

```text
AXLAW
AXGOV
```

AXMONETARY chỉ mô hình hóa policy state.

---

# 39. Currency Basket

```axiom
struct CurrencyBasket {
    components: Map<CurrencyId, Decimal>
    normalization: BasketNormalization
}
```

Ứng dụng:

```text
reference unit
exchange-rate index
reserve benchmark
simulation numeraire
```

---

# 40. International Reserve Unit

AXMONETARY hỗ trợ abstract reserve/reference units:

```axiom
struct ReserveUnit {
    id: ReserveUnitId
    composition: BasketDefinition
    valuation_method: ValuationMethod
}
```

Không coi mọi reserve unit là currency legal tender.

---

# 41. Monetary Transmission

AXMONETARY cung cấp graph:

```text
Policy Rate
    ↓
Money Market
    ↓
Bank Funding
    ↓
Credit Conditions
    ↓
Household / Enterprise Spending
    ↓
Investment
    ↓
Aggregate Demand
    ↓
Output / Employment / Prices
```

Đây là model, không phải deterministic law.

---

# 42. Transmission Channel

```axiom
enum TransmissionChannel {
    InterestRate
    Credit
    BankLending
    AssetPrice
    ExchangeRate
    Expectations
    Liquidity
    Wealth
    Other
}
```

```axiom
struct TransmissionModel {
    channels: ChannelSet
    parameters: ParameterSet
    uncertainty: UncertaintySet
    validity_range: DomainRange
}
```

---

# 43. Inflation

```axiom
struct InflationObservation {
    index: PriceIndexRef
    period: Period
    rate: Decimal
    methodology: MethodologyRef
}
```

Phải phân biệt:

```text
price level
inflation rate
core inflation
headline inflation
expected inflation
simulated inflation
```

---

# 44. Deflation

Deflation không được biểu diễn đơn giản là:

```text
inflation < 0
```

nếu domain model cần distinction về:

```text
persistent decline
temporary price decline
measurement effect
sector-specific price decline
```

---

# 45. Monetary Expectations

```axiom
struct InflationExpectation {
    horizon: Duration
    expected_rate: Decimal
    population: PopulationRef
    method: ExpectationMethod
    timestamp: Timestamp
}
```

Các nguồn:

```text
survey
market-implied
model
agent simulation
```

phải giữ provenance.

---

# 46. Money Multiplier

AXMONETARY **không** hard-code:

```text
Money Multiplier = 1 / Reserve Ratio
```

vì đây chỉ là một mô hình trong một số điều kiện.

Thay vào đó:

```axiom
struct MoneyCreationModel {
    assumptions: AssumptionSet
    mechanism: ModelGraph
    parameters: ParameterSet
}
```

---

# 47. Credit Creation

```axiom
struct CreditFlow {
    lender: EntityRef
    borrower: EntityRef
    principal: Money
    maturity: Duration
    rate: InterestRate
}
```

Credit expansion có thể tạo deposit liabilities trong banking model.

Do đó:

```text
Loan ≠ Money
```

nhưng:

```text
Loan creation
    →
Deposit creation
```

có thể được mô hình hóa ở `AXBANKING`.

---

# 48. Deposit Creation Event

```axiom
struct DepositCreation {
    bank: BankRef
    depositor: AccountRef
    amount: Money
    originating_credit: CreditRef?
    timestamp: Timestamp
}
```

`AXBANKING` là authority của actual deposit lifecycle.

`AXMONETARY` quan sát và aggregate.

---

# 49. Central Bank Digital Currency

```axiom
enum DigitalMoneyModel {
    AccountBased
    TokenBased
    Hybrid
}
```

```axiom
struct CBDCSystem {
    issuer: CentralBankId
    currency: CurrencyId
    model: DigitalMoneyModel
    access_model: AccessModel
    settlement_model: SettlementModel
    offline_mode: OfflineMode
}
```

CBDC không được đồng nhất với:

```text
cryptocurrency
stablecoin
commercial bank deposit
```

---

# 50. Retail CBDC

```axiom
struct RetailCBDCAccount {
    holder: IdentityRef
    balance: Money
    limits: LimitSet
    status: AccountStatus
}
```

Các giới hạn:

```text
balance limit
transaction limit
holding limit
offline limit
```

là policy configuration, không phải compiler rule.

---

# 51. Wholesale Digital Central Bank Money

```axiom
struct WholesaleCBDCAccount {
    institution: InstitutionRef
    balance: Money
    settlement_permissions: PermissionSet
}
```

Dùng cho:

```text
interbank settlement
securities settlement
cross-border settlement
tokenized asset settlement
```

---

# 52. Stablecoin Boundary

Stablecoin có thể được biểu diễn:

```axiom
struct StablecoinRef {
    issuer: EntityRef
    asset: AssetRef
    currency_reference: CurrencyId?
    reserve_model: ReserveModel
}
```

Nhưng không tự động thuộc:

```text
CentralBankMoney
```

hoặc:

```text
LegalTender
```

---

# 53. Monetary Policy Instrument

```axiom
enum MonetaryInstrument {
    PolicyRate
    ReserveRequirement
    OpenMarketOperation
    StandingFacility
    AssetPurchase
    AssetSale
    FXIntervention
    LiquidityFacility
    ForwardGuidance
    Other
}
```

---

# 54. Policy Scenario

```axiom
struct MonetaryScenario {
    horizon: Duration
    initial_state: MonetaryStateSnapshot
    policy_path: PolicyPath
    exogenous_shocks: ShockSet
    assumptions: AssumptionSet
}
```

---

# 55. Scenario Engine

```axiom
simulate_monetary(
    scenario: MonetaryScenario
) -> MonetaryScenarioResult
```

Output:

```text
money supply path
liquidity path
interest-rate path
exchange-rate scenarios
inflation distribution
credit distribution
banking stress
reserve adequacy
output scenarios
```

Không output:

```text
"this is the correct policy"
```

---

# 56. Agent-Based Monetary Simulation

Entities:

```text
household
worker
enterprise
bank
central bank
investor
government
foreign sector
```

Mỗi agent có:

```text
balance sheet
cash flow
expectations
constraints
decision policy
```

---

# 57. Monetary Digital Twin

```axiom
struct MonetaryTwin {
    real_state: MonetaryState
    observed_state: ObservationState
    estimated_state: EstimatedState
    forecast_state: ForecastState
    simulated_state: SimulationState
}
```

Các state phải độc lập.

---

# 58. Monetary Shock

```axiom
struct MonetaryShock {
    type: ShockType
    magnitude: Decimal
    duration: Duration
    probability: Probability?
    source: ShockSource
}
```

Các shock:

```text
rate shock
liquidity shock
FX shock
banking shock
commodity shock
inflation shock
demand shock
supply shock
confidence shock
external monetary shock
```

---

# 59. Stress Testing

```axiom
struct MonetaryStressTest {
    scenario: ScenarioRef
    institutions: InstitutionSet
    metrics: MetricSet
    thresholds: ThresholdSet
}
```

Metrics:

```text
liquidity
reserve adequacy
funding
FX exposure
interest-rate sensitivity
balance-sheet impact
credit contraction
payment-system stress
```

---

# 60. Systemic Liquidity

```axiom
struct SystemLiquidityState {
    aggregate_reserves: Money
    available_collateral: Money
    emergency_capacity: Money
    market_liquidity: LiquidityMeasure
    funding_stress: StressMeasure
}
```

Không suy ra systemic liquidity từ reserves בלבד.

---

# 61. Liquidity Contagion

```axiom
struct LiquidityContagionGraph {
    nodes: InstitutionSet
    edges: ExposureSet
    propagation_model: ModelRef
}
```

Simulation:

```axiom
simulate_liquidity_contagion(...)
```

phải không thay đổi production state.

---

# 62. Monetary Network

Graph:

```text
Central Bank
     │
     ├── Banks
     │     ├── Households
     │     ├── Enterprises
     │     └── Financial Markets
     │
     ├── FX Markets
     │
     └── Foreign Central Banks
```

Mỗi edge có:

```text
currency
exposure
settlement
maturity
counterparty
collateral
risk
```

---

# 63. Cross-Currency Monetary State

```axiom
struct MultiCurrencyBalance {
    balances: Map<CurrencyId, Decimal>
}
```

Không tự động cộng:

```text
USD + EUR + VND
```

Phải chọn:

```text
numeraire
valuation timestamp
FX source
```

---

# 64. Monetary Valuation

```axiom
struct MonetaryValuation {
    amount: Money
    numeraire: CurrencyId
    fx_source: FXRateSource
    timestamp: Timestamp
}
```

Hai valuation tại hai thời điểm khác nhau không được coi là cùng một observation.

---

# 65. Central Bank Foreign Relations

```axiom
struct CentralBankRelation {
    central_bank_a: CentralBankId
    central_bank_b: CentralBankId
    currencies: CurrencyPairSet
    swap_lines: SwapLineSet
    settlement_arrangements: SettlementSet
}
```

---

# 66. Currency Swap Line

```axiom
struct CurrencySwapLine {
    provider: CentralBankId
    recipient: CentralBankId
    currency_a: CurrencyId
    currency_b: CurrencyId
    limit: Money
    maturity: Duration
    rate_rule: RateRule
    authorization: AuthorizationRef
}
```

---

# 67. Monetary Swap Operation

```axiom
struct SwapOperation {
    swap_line: SwapLineRef
    amount: Money
    start: Timestamp
    maturity: Timestamp
}
```

---

# 68. Balance-of-Payments Boundary

AXMONETARY chỉ cung cấp monetary-side observations.

```text
AXMONETARY
    ↓
FX reserves
currency flows
central-bank transactions
monetary aggregates
```

Trong khi:

```text
AXGLOBALTRADE / future international runtime
    ↓
trade
current account
capital flows
balance of payments
```

---

# 69. Fiscal Boundary

Không đồng nhất:

```text
Fiscal Policy
```

với:

```text
Monetary Policy
```

Government spending/taxation thuộc:

```text
AXGOV
AXFINANCE
```

Central-bank operations thuộc:

```text
AXMONETARY
```

Các giao dịch giữa hai hệ thống phải có explicit boundary events.

---

# 70. Treasury / Government Account

```axiom
struct GovernmentDeposit {
    government: GovernmentRef
    central_bank: CentralBankId
    balance: Money
}
```

Không được coi government deposit là equivalent với private bank deposit trong aggregate logic nếu definition không quy định.

---

# 71. Monetary-Fiscal Interaction

Runtime hỗ trợ graph:

```text
Fiscal Policy
      ↓
Government Financing
      ↓
Financial Markets
      ↓
Banking System
      ↓
Central Bank Balance Sheet
      ↓
Monetary Conditions
```

Nhưng mỗi causal relationship phải là model-specific.

---

# 72. AI Monetary Assistant

```axiom
struct MonetaryAI {
    model: ModelRef
    capabilities: CapabilitySet
    authority: AuthoritySet
}
```

Capabilities:

```text
forecast
scenario_generation
stress_test
policy_analysis
data_validation
anomaly_detection
research
report_generation
```

Mặc định:

```text
no_policy_execution
no_money_issuance
no_rate_change
no_reserve_transfer
no_fx_intervention
```

---

# 73. AI Policy Pipeline

```text
Data
 ↓
Validation
 ↓
State Estimation
 ↓
Forecast
 ↓
Scenario Generation
 ↓
Policy Analysis
 ↓
Human/Authorized Institution Review
 ↓
Decision
 ↓
Authorization
 ↓
Execution
 ↓
Observation
```

Không được rút gọn thành:

```text
AI → Policy
```

---

# 74. Monetary Forecast

```axiom
struct MonetaryForecast {
    variable: EconomicVariable
    horizon: Duration
    distribution: ProbabilityDistribution
    model: ModelRef
    assumptions: AssumptionSet
    generated_at: Timestamp
}
```

Forecast luôn mang uncertainty.

---

# 75. Policy Optimization

AXMONETARY cho phép:

```axiom
optimize_policy(
    objective,
    constraints,
    scenarios
)
```

nhưng kết quả là:

```text
CandidatePolicySet
```

không phải policy decision.

---

# 76. Objective Function

```axiom
struct MonetaryObjective {
    metric: MetricRef
    target: TargetDefinition
    weight: Decimal
    tolerance: Decimal
}
```

Không cho phép một objective ngầm trở thành universal societal objective.

---

# 77. Uncertainty

Hỗ trợ:

```text
confidence interval
credible interval
scenario range
parameter uncertainty
model uncertainty
structural uncertainty
data uncertainty
```

Không được ép mọi uncertainty thành một số điểm duy nhất.

---

# 78. Monetary Data Provenance

Mọi authoritative aggregate cần:

```axiom
struct MonetaryProvenance {
    source
    observation_time
    publication_time
    methodology
    revision
    transformation_chain
}
```

---

# 79. Data Revision

Macro data thường có revision.

```axiom
struct DataRevision {
    series: SeriesId
    previous_version: VersionId
    new_version: VersionId
    reason: RevisionReason
    timestamp: Timestamp
}
```

Simulation có thể chọn:

```text
real-time vintage
latest revised
historical vintage
```

---

# 80. Vintage Data

```axiom
struct DataVintage {
    dataset: DatasetRef
    as_of: Timestamp
    release_version: VersionId
}
```

Đây là yêu cầu quan trọng để backtest monetary policy.

---

# 81. Policy Backtesting

```axiom
backtest_policy(
    historical_vintage,
    policy_rule,
    historical_shocks
)
```

Kết quả:

```text
simulated outcomes
error distributions
counterfactual paths
```

Không được trình bày counterfactual như historical fact.

---

# 82. Monetary Rule

```axiom
struct PolicyRule {
    inputs: VariableSet
    output: InstrumentRef
    formula: Expression
    constraints: ConstraintSet
}
```

Ví dụ conceptual:

```text
policy_rate = f(inflation_gap, output_gap, expectations)
```

Không hard-code một rule duy nhất.

---

# 83. Expectations and Forward Guidance

```axiom
struct ForwardGuidance {
    statement: PolicyStatement
    horizon: Duration?
    conditions: ConditionSet
    authority: AuthorityRef
}
```

Statement không được coi là guaranteed future execution.

---

# 84. Monetary Communication

```axiom
struct MonetaryCommunication {
    authority: AuthorityRef
    timestamp: Timestamp
    statement: Text
    referenced_data: DatasetSet
    referenced_models: ModelSet
}
```

Communication và policy execution là hai event khác nhau.

---

# 85. Payment-System Boundary

Payment execution thuộc:

```text
AXFINANCE
AXBANKING
AXMARKET
```

tùy rail.

AXMONETARY quan sát:

```text
settlement balances
reserve movements
liquidity conditions
```

Không trở thành payment processor mặc định.

---

# 86. Monetary Ledger Boundary

AXMONETARY không thay thế general ledger.

Nó cung cấp:

```text
monetary state
monetary aggregates
central-bank balance sheet
reserve state
policy state
```

Financial accounting remains:

```text
AXFINANCE
```

---

# 87. Monetary Event Log

Mọi state transition quan trọng tạo:

```axiom
struct MonetaryEvent {
    id: EventId
    type: EventType
    timestamp: Timestamp
    actor: EntityRef
    authorization: AuthorizationRef?
    before: StateHash
    after: StateHash
    provenance: ProvenanceRef
}
```

---

# 88. Deterministic Replay

Runtime phải hỗ trợ:

```axiom
replay_monetary_state(
    initial_snapshot,
    event_log
)
```

Kết quả phải deterministic khi:

```text
same snapshot
same event sequence
same model version
same configuration
same data vintage
```

---

# 89. State Snapshot

```axiom
struct MonetarySnapshot {
    version: VersionId
    timestamp: Timestamp
    currencies: CurrencyState
    aggregates: AggregateState
    central_banks: CentralBankState
    reserves: ReserveState
    policy: PolicyState
    hash: StateHash
}
```

---

# 90. Transactional State Update

Authoritative monetary state update phải có:

```text
validate
prepare
commit
event
checkpoint
```

Nếu fail:

```text
rollback
```

Không cho phép partial monetary state mutation.

---

# 91. Concurrency

Các hot path:

```text
market observations
reserve updates
rate observations
aggregate calculation
simulation
```

có thể chạy parallel.

Critical policy/issuance operations phải có serialized authority boundary.

---

# 92. Memory Architecture

Hot structures:

```text
SoA
packed arrays
arena allocation
immutable snapshots
append-only event buffers
```

Tránh GC trong:

```text
market data ingestion
simulation hot loops
aggregate calculation
replay
```

---

# 93. Numeric Architecture

Authoritative monetary arithmetic ưu tiên:

```text
i128
u128
fixed-point
Decimal
rational
```

`f32/f64` chỉ dành cho:

```text
forecast models
simulation
statistical estimation
ML
```

và kết quả phải được explicit-convert khi đi vào authoritative state.

---

# 94. GPU

GPU phù hợp cho:

```text
Monte Carlo
agent-based simulation
scenario generation
large-scale forecasting
risk calculations
optimization
matrix operations
```

Không bắt buộc GPU cho:

```text
single monetary transaction
policy authorization
event commit
ledger-like state transition
```

---

# 95. SIMD

CPU SIMD nên được sử dụng cho:

```text
aggregate calculations
time-series transforms
FX conversion batches
scenario evaluation
statistical calculations
```

---

# 96. Distributed Monetary Runtime

Cluster model:

```text
MonetaryAuthorityNode
ObservationNode
SimulationNode
AnalyticsNode
ArchiveNode
```

Authoritative state phải có:

```text
leader/authority
consensus or equivalent durable commit
version
hash
replayability
```

---

# 97. Fault Tolerance

Nếu analytics node chết:

```text
monetary authority continues
```

Nếu simulation node chết:

```text
production monetary state unchanged
```

Nếu authoritative node chết:

```text
failover
```

không được tạo double issuance.

---

# 98. Double Issuance Protection

Invariant:

```text
same IssuanceId
→ at most one committed issuance
```

Replay phải idempotent.

---

# 99. Idempotency

Các operations:

```text
issue
redeem
reserve_transfer
policy_commit
liquidity_operation
fx_intervention
```

phải có idempotency key.

---

# 100. Security Capability Model

Capabilities:

```text
monetary.read
monetary.observe
monetary.aggregate.read
currency.read
currency.write
issuance.propose
issuance.execute
redemption.propose
redemption.execute
policy.read
policy.propose
policy.approve
policy.execute
reserve.read
reserve.write
liquidity.propose
liquidity.execute
fx.read
fx.intervention.propose
fx.intervention.execute
simulation.run
forecast.run
stress_test.run
model.manage
audit.read
admin
```

Mặc định:

```text
AI = no execute
```

---

# 101. Separation of Duties

Một actor không nên mặc định đồng thời có:

```text
policy.propose
policy.approve
policy.execute
```

Production deployment có thể yêu cầu nhiều authority.

---

# 102. Audit

Audit log phải lưu:

```text
actor
authority
input state
decision
model
data vintage
authorization
execution
result
timestamp
```

---

# 103. Privacy

Monetary analytics phải hỗ trợ:

```text
aggregate-only
pseudonymized
privacy-preserving
role-scoped
jurisdiction-scoped
```

Không expose individual financial records chỉ vì aggregate analytics được phép.

---

# 104. Monetary Risk Registry

```axiom
struct MonetaryRisk {
    id: RiskId
    category: MonetaryRiskCategory
    exposure: Exposure
    probability: Probability?
    impact: Impact?
    model: ModelRef?
}
```

Categories:

```text
inflation
deflation
liquidity
interest_rate
FX
reserve
counterparty
settlement
systemic
model
operational
```

---

# 105. Early Warning System

```axiom
struct MonetarySignal {
    indicator: IndicatorRef
    value: Decimal
    threshold: Threshold?
    severity: SignalSeverity
    confidence: Confidence
}
```

Invariant:

```text
Signal ≠ Crisis
Signal ≠ PolicyDecision
Signal ≠ LegalFinding
```

---

# 106. Monetary Health Dashboard

Native APIs:

```axiom
monetary.inflation()
monetary.policy_rate()
monetary.money_supply()
monetary.reserves()
monetary.fx()
monetary.liquidity()
monetary.credit()
monetary.yield_curve()
monetary.expectations()
```

Mỗi API phải trả:

```text
value
timestamp
source
vintage
confidence
```

---

# 107. Query Model

Ví dụ:

```axiom
let m2 = AXMONETARY.aggregate("M2", at: date)
```

```axiom
let reserves =
    central_bank("VN").fx_reserves(at: date)
```

```axiom
let curve =
    yield_curve("USD", at: date)
```

---

# 108. Scenario DSL

```axiom
scenario "rate_shock" {
    initial = monetary.snapshot("2026-Q1")

    shock policy_rate {
        +200bp
    }

    simulate 24.months

    observe:
        inflation
        credit
        output
        fx
        reserves
}
```

---

# 109. Policy Analysis DSL

```axiom
analysis "policy_path" {
    objective price_stability
    constraint liquidity_floor > threshold

    candidates:
        rate_path(...)
        asset_purchase(...)
        reserve_operation(...)

    evaluate scenarios:
        baseline
        supply_shock
        banking_stress
        fx_shock
}
```

Kết quả:

```text
PolicyAnalysisReport
```

không phải:

```text
PolicyDecision
```

---

# 110. Monetary Simulation Profiles

```text
AXMONETARY_NONE
AXMONETARY_CORE
AXMONETARY_CURRENCY
AXMONETARY_MONEY
AXMONETARY_CENTRAL_BANK
AXMONETARY_RATES
AXMONETARY_POLICY
AXMONETARY_LIQUIDITY
AXMONETARY_FX
AXMONETARY_RESERVES
AXMONETARY_MACRO
AXMONETARY_SIMULATION
AXMONETARY_DIGITAL_MONEY
AXMONETARY_AI
AXMONETARY_GLOBAL
AXMONETARY_DISTRIBUTED
AXMONETARY_GPU
AXMONETARY_WASM
AXMONETARY_MOBILE
AXMONETARY_FULL
```

---

# 111. Compiler Integration

Compiler phải hiểu các semantic types:

```text
Money
Currency
InterestRate
FXRate
Duration
Probability
Quantity
PolicyInstrument
MonetaryAggregate
ReserveBalance
```

để ngăn lỗi đơn vị.

Ví dụ không hợp lệ:

```axiom
let x: Money = 5.0
```

nếu không có currency.

Hợp lệ:

```axiom
let x: Money = 5.0 USD
```

---

# 112. Dimensional Analysis

Compiler có thể kiểm tra:

```text
USD / USD = dimensionless
USD / year = monetary_flow
USD * rate = monetary_flow
```

và phát hiện:

```text
Money + InterestRate
```

là type error.

---

# 113. Compile-Time Currency Safety

Nếu currency compile-time known:

```axiom
Money<USD>
Money<VND>
```

compiler có thể reject:

```axiom
Money<USD> + Money<VND>
```

Nếu currency dynamic:

```axiom
Money<DynamicCurrency>
```

runtime FX conversion bắt buộc.

---

# 114. Temporal Safety

Policy state phải mang hiệu lực:

```text
effective_from
effective_to
```

Không cho phép query policy tại thời điểm `t` nhận policy chưa có hiệu lực.

---

# 115. Versioned Models

Mọi monetary model phải có:

```text
model_id
version
training_data
calibration_data
assumptions
validity_range
```

Backtest phải giữ model version.

---

# 116. Model Registry

```axiom
struct MonetaryModel {
    id: ModelId
    version: VersionId
    type: ModelType
    parameters: ParameterSet
    assumptions: AssumptionSet
    provenance: ProvenanceRef
}
```

---

# 117. Model Governance

Model lifecycle:

```text
Draft
→ Validated
→ Approved
→ Deployed
→ Monitored
→ Retired
```

AI model không được tự deploy vào authoritative monetary path.

---

# 118. Model Drift

Runtime theo dõi:

```text
prediction error
distribution drift
parameter drift
regime change
data quality
```

---

# 119. Regime Change

Monetary models phải hỗ trợ:

```text
policy regime change
exchange regime change
currency transition
financial crisis
structural break
```

Không giả định historical relationship luôn giữ nguyên.

---

# 120. Currency Transition

Hỗ trợ:

```text
redenomination
currency replacement
monetary union
currency split
currency withdrawal
```

Ví dụ:

```axiom
CurrencyTransition {
    old_currency
    new_currency
    conversion_ratio
    effective_date
    rounding_rule
}
```

---

# 121. Rounding

Authoritative conversion phải xác định:

```text
rounding mode
precision
minimum unit
residual handling
```

Không dùng default floating-point rounding.

---

# 122. Hyperinflation / Extreme Values

Runtime phải hỗ trợ:

```text
very large nominal amounts
very small rates
negative rates
currency redenomination
high-frequency compounding
```

Numeric overflow phải được detect trước commit.

---

# 123. Negative Interest

```axiom
InterestRate.value
```

có thể âm nếu model/policy cho phép.

Không hard-code:

```text
rate >= 0
```

---

# 124. Zero Lower Bound

ZLB là một policy constraint/model condition, không phải numeric type invariant.

---

# 125. Effective Lower Bound

Có thể biểu diễn:

```axiom
struct RateConstraint {
    lower: InterestRate
    upper: InterestRate?
    rationale: ConstraintReason
}
```

---

# 126. Monetary Aggregation Engine

Aggregation pipeline:

```text
raw observations
      ↓
validation
      ↓
classification
      ↓
currency normalization
      ↓
deduplication
      ↓
aggregation
      ↓
revision
      ↓
publication
```

---

# 127. Consolidation

Khi aggregate toàn hệ thống:

```text
intermediary claims
```

có thể cần elimination.

Ví dụ:

```text
bank deposit
+
bank liability
```

không được double-count trong mọi monetary aggregate.

Aggregation definitions phải explicit.

---

# 128. Sector Balance Sheets

Hỗ trợ:

```text
households
nonfinancial corporations
financial corporations
government
central bank
foreign sector
```

Mỗi sector:

```text
assets
liabilities
equity
cash flow
```

---

# 129. Flow-of-Funds

```axiom
struct FlowOfFunds {
    source_sector
    destination_sector
    instrument
    amount
    period
}
```

Hỗ trợ macro accounting và monetary transmission.

---

# 130. Stock-Flow Consistency

Simulation có invariant:

```text
opening_stock
+ inflows
- outflows
= closing_stock
```

mọi monetary stock phải reconcile được với flow.

---

# 131. Monetary Conservation

Trong closed simulation:

```text
creation
- destruction
+ external flows
= net monetary change
```

phải reconcile.

Không được tự nhiên xuất hiện tiền trong simulation.

---

# 132. External Sector

```axiom
struct ForeignSector {
    currencies
    assets
    liabilities
    trade_flows
    capital_flows
    reserve_positions
}
```

Chi tiết international trade thuộc runtime quốc tế tương ứng.

---

# 133. Global Monetary Graph

```text
Central Banks
      ↕
Commercial Banks
      ↕
Financial Markets
      ↕
Households / Enterprises
      ↕
Foreign Financial System
      ↕
Foreign Central Banks
```

Graph có thể chứa hàng triệu nodes trong simulation.

---

# 134. Distributed Simulation

Simulation engine hỗ trợ:

```text
partition by geography
partition by sector
partition by agent
partition by time-window
```

Deterministic reduction phải được hỗ trợ khi cần reproducibility.

---

# 135. Monte Carlo

```axiom
monte_carlo(
    scenario,
    iterations,
    seed
)
```

`seed` là explicit để tái lập.

---

# 136. Reproducibility

Hai simulation có:

```text
same seed
same model
same data
same configuration
same runtime version
```

phải có thể tái lập kết quả trong reproducibility profile.

---

# 137. Time Model

Hỗ trợ:

```text
tick
second
minute
hour
day
month
quarter
year
event-time
```

Monetary policy thường event-based + calendar-based.

---

# 138. Event Ordering

Nếu:

```text
rate decision
FX intervention
market trade
reserve settlement
```

xảy ra cùng timestamp, runtime phải có deterministic ordering.

---

# 139. Event Priority

```text
Authorization
→ PolicyCommit
→ MarketExecution
→ Settlement
→ AccountingObservation
→ AggregateUpdate
→ Publication
```

Có thể override bởi domain profile nhưng phải explicit.

---

# 140. Monetary State Machine

State:

```text
Initialized
Observed
Validated
Published
Revised
Archived
```

Policy state:

```text
Proposed
Reviewed
Authorized
Scheduled
Effective
Expired
Superseded
```

---

# 141. Emergency Mode

```axiom
enum MonetaryRuntimeMode {
    Normal
    Stress
    Emergency
    Recovery
}
```

Emergency mode có thể:

```text
tighten limits
increase audit
require multi-party authorization
increase snapshot frequency
disable autonomous agents
```

---

# 142. Kill Switch

AI monetary agents phải có:

```axiom
monetary_ai.kill()
```

Kill switch phải:

```text
stop proposals
stop execution
preserve state
preserve audit
```

không xóa historical evidence.

---

# 143. Safety Invariants

Một số invariant nền tảng:

```text
I001 Money must have Currency
I002 Cross-currency arithmetic requires conversion
I003 Issuance requires authorization
I004 Redemption requires authorization
I005 Same issuance id cannot commit twice
I006 Simulation cannot mutate production state
I007 Recommendation cannot execute as decision
I008 PolicyRate != MarketRate
I009 Reserve != Capital
I010 Liquidity != Solvency
I011 FX reserve != sovereign wealth
I012 CBDC != crypto asset
I013 Loan != Money
I014 Forecast != Observation
I015 Revised data preserves vintage identity
I016 Monetary events are replayable
I017 Monetary state transitions are auditable
I018 Numeric overflow cannot commit
I019 Currency transition is versioned
I020 Central-bank authority is explicit
I021 AI cannot gain monetary authority implicitly
I022 Policy execution requires capability
I023 Emergency operations are time-bounded
I024 Aggregate definitions are versioned
I025 Aggregate consolidation rules are explicit
I026 Stock-flow identities reconcile
I027 Cross-currency valuation has timestamp
I028 Simulation seed is explicit
I029 Model version is recorded
I030 Data provenance is preserved
I031 Policy effective time is explicit
I032 Settlement is not policy
I033 Fiscal operations are not silently monetary operations
I034 FX intervention is auditable
I035 Reserve composition is explicit
I036 Negative rates require explicit model support
I037 Policy scenarios cannot become live state implicitly
I038 Distributed commit prevents double issuance
I039 Failover cannot duplicate monetary state
I040 AI shutdown preserves authoritative state
I041 Emergency mode cannot silently bypass authorization
I042 Historical data cannot be overwritten without revision
I043 Money aggregation cannot double-count eliminated claims
I044 External flows are explicit
I045 Monetary units participate in dimensional checking
I046 Fixed-point authoritative calculations are deterministic
I047 Policy communication is not guaranteed execution
I048 Central bank digital money has explicit issuer
I049 Currency redenomination is versioned
I050 Monetary state has authoritative timestamp
```

---

# 144. Error Model

```axiom
enum MonetaryError {
    InvalidCurrency
    CurrencyMismatch
    InvalidMoneyAmount
    Overflow
    UnauthorizedIssuance
    UnauthorizedRedemption
    DuplicateIssuance
    InvalidPolicy
    PolicyNotEffective
    InvalidRate
    InvalidFXRate
    ReserveViolation
    LiquidityLimitExceeded
    CollateralInsufficient
    SettlementFailure
    ModelUnavailable
    DataVintageMismatch
    ProvenanceMissing
    SimulationStateMutation
    AuthorizationMissing
    ConcurrencyConflict
    StateVersionConflict
}
```

---

# 145. Observability

Metrics:

```text
money_supply
reserve_balance
liquidity
policy_rate
market_rate
yield_curve
FX_rate
FX_reserves
credit_growth
inflation
expectations
policy_operations
simulation_latency
event_replay_latency
```

---

# 146. Performance Target

Target cho native runtime:

```text
>10M monetary observations/sec
```

trong optimized batch profile trên hardware phù hợp.

Simulation:

```text
millions of agents
billions of event evaluations
```

phải có scalable architecture.

Không yêu cầu mọi deployment đạt cùng throughput.

---

# 147. Latency Classes

```text
L0 — authoritative commit
L1 — market observation
L2 — aggregation
L3 — analytics
L4 — simulation
L5 — historical research
```

Mỗi class có SLA riêng.

---

# 148. Zero-Copy

Hot path hỗ trợ:

```text
zero-copy event ingestion
memory-mapped datasets
columnar observations
packed monetary records
```

---

# 149. Storage

Historical monetary data có thể lưu:

```text
append-only event log
columnar time series
compressed snapshots
content-addressed datasets
```

Kết hợp với:

```text
AX611
AX612
AX613
```

---

# 150. Integration với AXBANKING

```text
AXBANKING
    │
    ├── deposits
    ├── loans
    ├── reserves
    ├── interbank balances
    └── liquidity
            │
            ▼
       AXMONETARY
```

AXBANKING owns banking operations.

AXMONETARY owns monetary interpretation and policy infrastructure.

---

# 151. Integration với AXFINANCE

```text
AXFINANCE
    ↓
financial records
    ↓
AXMONETARY
    ↓
monetary aggregates
```

Không duplicate general ledger.

---

# 152. Integration với AXMARKET

```text
AXMONETARY
    ↓
policy / liquidity / FX intervention
    ↓
AXMARKET
    ↓
execution
    ↓
AXFINANCE
```

---

# 153. Integration với AXINSURANCE

Insurance exposure có thể phản ứng với:

```text
inflation
interest rate
FX
asset prices
liquidity
```

AXINSURANCE vẫn sở hữu:

```text
policy
claim
reserve
underwriting
```

AXMONETARY chỉ cung cấp monetary environment.

---

# 154. Integration với AXINVEST

Investment models consume:

```text
policy rates
yield curves
inflation
FX
liquidity
monetary scenarios
```

AXINVEST vẫn sở hữu:

```text
portfolio
allocation
investment decision
```

---

# 155. Integration với AXCIVILIZATION

Civilization runtime có thể truy vấn:

```text
money
credit
inflation
employment
output
investment
trade
financial stability
```

để xây:

```text
macro-economic digital twin
```

---

# 156. Civilization Monetary Loop

```text
REAL ECONOMY
      ↓
MONEY / CREDIT
      ↓
SPENDING / INVESTMENT
      ↓
OUTPUT / INCOME
      ↓
PRICES
      ↓
MONETARY POLICY
      ↓
LIQUIDITY / CREDIT
      ↓
REAL ECONOMY
```

Đây là closed-loop simulation boundary.

---

# 157. Global Financial Loop

```text
SAVINGS
   ↓
BANKING
   ↓
INVESTMENT
   ↓
CAPITAL MARKETS
   ↓
PRODUCTION
   ↓
INCOME
   ↓
DEPOSITS
   ↓
MONEY / CREDIT
   ↓
MONETARY SYSTEM
   ↓
BANKING
```

---

# 158. Native AI Civilization Interface

Một agent có thể truy vấn:

```axiom
economy.money_supply()
economy.inflation()
economy.policy_rate()
economy.fx_reserves()
economy.credit_conditions()
economy.liquidity()
economy.scenario(...)
```

nhưng:

```axiom
economy.change_policy(...)
```

phải yêu cầu explicit authority.

---

# 159. Example AI Workflow

```axiom
agent "monetary_researcher" {

    observe:
        inflation
        output
        credit
        reserves
        exchange_rate

    generate scenarios:
        baseline
        supply_shock
        financial_stress

    evaluate:
        policy_rate
        liquidity
        asset_purchase

    return PolicyAnalysisReport
}
```

Agent không được tự execute policy.

---

# 160. Civilization-Scale Query

```axiom
query monetary_state {
    countries.*
        .currency
        .money_supply
        .policy_rate
        .inflation
        .fx_reserves
        .credit_growth
}
```

Kết quả phải giữ:

```text
jurisdiction
timestamp
vintage
source
```

---

# 161. Global Currency Graph

```axiom
query fx_graph {
    currencies.*
        .exchange_edges()
}
```

Graph có thể được sử dụng cho:

```text
FX analysis
reserve diversification
cross-border simulation
currency contagion
scenario analysis
```

---

# 162. Monetary Contagion Simulation

```axiom
scenario "global_monetary_stress" {

    shock currency USD {
        funding_stress += high
    }

    propagate:
        FX
        reserves
        liquidity
        banking
        capital_markets

    simulate 12.months
}
```

Simulation output không phải prediction về thế giới thật.

---

# 163. Compliance Boundary

Các yêu cầu như:

```text
legal tender
capital controls
reserve mandates
central bank powers
currency issuance authority
```

được import từ:

```text
AXLAW
AXGOV
```

AXMONETARY không tự tạo legal authority.

---

# 164. Monetary Governance Graph

```text
Law
 ↓
Institutional Authority
 ↓
Monetary Framework
 ↓
Policy Decision
 ↓
Instrument
 ↓
Execution
 ↓
Observation
 ↓
Evaluation
```

---

# 165. Native Artifact

Compiler có thể phát sinh:

```text
.monstate
.monetary
.mscenario
.mpolicy
.mcurve
.mreserve
```

Các artifact phải:

```text
versioned
hashable
portable
machine-readable
AI-readable
```

---

# 166. Cache

Simulation/model cache key:

```text
hash(
    model_version,
    data_vintage,
    initial_state,
    scenario,
    configuration,
    seed
)
```

Nếu tất cả giống nhau:

```text
reuse cached result
```

---

# 167. Incremental Simulation

Nếu chỉ thay đổi:

```text
policy path at t=100
```

runtime có thể reuse checkpoint trước `t=100`.

---

# 168. Checkpoint

```axiom
checkpoint(
    simulation,
    at: time
)
```

Checkpoint chứa:

```text
state
model version
seed
event cursor
data vintage
configuration
```

---

# 169. Recovery

Nếu simulation crash:

```text
load checkpoint
verify hash
resume event stream
```

Production state không bị ảnh hưởng.

---

# 170. Test Architecture

Axiom implementation target:

```text
≥ 18,000 automated tests
≥ 1,800 architecture invariants
```

Phân bổ:

```text
currency               800
money                   1,000
issuance                1,000
aggregates              1,200
rates                   1,000
policy                  1,400
liquidity               1,000
central bank            1,000
FX                      1,200
reserves                900
digital money           700
simulation               2,000
AI                       1,200
distributed              1,000
security                 800
replay                   600
numeric                  800
integration             1,400
```

Các con số là architecture targets; test generator có thể mở rộng.

---

# 171. Conformance Tests

Mỗi implementation phải pass:

```text
currency conformance
money arithmetic conformance
issuance conformance
reserve conformance
policy conformance
FX conformance
simulation conformance
replay conformance
security conformance
```

---

# 172. Property-Based Tests

Ví dụ:

```text
convert(A, X→Y) + convert(B, X→Y)
==
convert(A+B, X→Y)
```

chỉ khi cùng:

```text
rate
timestamp
rounding
valuation convention
```

---

# 173. Conservation Tests

Kiểm tra:

```text
opening balance
+ issuance
- redemption
+ transfers
=
closing balance
```

---

# 174. Replay Tests

```text
snapshot + event_log
```

phải tạo cùng:

```text
state_hash
```

---

# 175. Failure Tests

Test:

```text
duplicate issuance
double redemption
stale policy
wrong currency
FX source unavailable
numeric overflow
authorization missing
network partition
node crash
replay duplication
```

---

# 176. Security Tests

Test:

```text
privilege escalation
unauthorized issuance
unauthorized policy execution
AI capability escalation
audit deletion
snapshot tampering
model substitution
data-vintage spoofing
```

---

# 177. AI Safety Tests

AI agent không được:

```text
issue money
change policy rate
alter reserve requirement
execute FX intervention
modify historical data
bypass authorization
```

nếu không có capability tương ứng.

---

# 178. Performance Tests

Benchmark:

```text
currency conversion
money aggregation
yield curve construction
reserve calculation
policy simulation
Monte Carlo
agent simulation
event replay
distributed synchronization
```

---

# 179. Determinism Tests

Native runtime phải có profile:

```text
AXMONETARY_DETERMINISTIC
```

để phục vụ:

```text
audit
research
backtesting
regression
AI evaluation
```

---

# 180. Production Profile

```text
AXMONETARY_PRODUCTION
```

ưu tiên:

```text
latency
availability
durability
auditability
security
```

---

# 181. Research Profile

```text
AXMONETARY_RESEARCH
```

ưu tiên:

```text
reproducibility
model experimentation
historical vintages
counterfactual simulation
```

---

# 182. Civilization Simulation Profile

```text
AXMONETARY_CIVILIZATION
```

tối ưu:

```text
large-scale agents
GPU
distributed simulation
scenario branching
digital twin
```

---

# 183. WASM Profile

```text
AXMONETARY_WASM
```

hỗ trợ:

```text
currency
money
rates
aggregates
simulation-lite
```

không yêu cầu central-bank privileged operations.

---

# 184. Mobile Profile

```text
AXMONETARY_MOBILE
```

dùng cho:

```text
financial applications
economic dashboards
offline monetary analytics
simulation-lite
```

---

# 185. Minimal Runtime

Một binary chỉ cần currency/money:

```text
AXMONETARY_CORE
```

không kéo theo:

```text
AI
GPU
distributed
simulation
central-bank operations
```

Đảm bảo binary nhỏ.

---

# 186. Link-Time Elimination

Compiler phải loại bỏ:

```text
unused monetary modules
unused models
unused currencies
unused simulation engines
unused AI
```

nếu không được tham chiếu.

---

# 187. No Mandatory Runtime Dependency

Core monetary runtime không phụ thuộc bắt buộc vào:

```text
Python
JVM
.NET
Node.js
external GC
external database
third-party numerical runtime
```

Các integration provider có thể tồn tại ở adapter layer.

---

# 188. Provider Boundary

Ví dụ:

```text
AXMONETARY
    ↓
Provider Interface
    ├── SQLite
    ├── PostgreSQL
    ├── Parquet
    ├── Arrow
    ├── external central-bank feed
    └── custom provider
```

Core không phụ thuộc provider cụ thể.

---

# 189. Final Architecture

```text
                    AXCIVILIZATION
                          │
                          ▼
                    AXECONOMY
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
         AXBANKING               AXMARKET
              │                       │
              └───────────┬───────────┘
                          ▼
                     AXMONETARY
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
    CURRENCY           POLICY            RESERVES
        │                 │                 │
        ▼                 ▼                 ▼
      MONEY             RATES               FX
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                     SIMULATION
                          │
                          ▼
                         AI
```

---

# 190. Responsibility Contract

```text
AXFINANCE
    = financial truth / accounting

AXBANKING
    = banking operations / deposits / loans

AXMONETARY
    = money / monetary system / central banking / monetary policy infrastructure

AXMARKET
    = market execution / trading / clearing / settlement

AXINVEST
    = investment decisions / portfolio allocation

AXINSURANCE
    = risk transfer / insurance

AXLAW
    = legal authority

AXGOV
    = public institutional authority

AXCIVILIZATION
    = civilization-scale system integration
```

---

# 191. Core Semantic Contract

```text
AXMONETARY = HOW MONEY AND MONETARY CONDITIONS ARE REPRESENTED,
             MEASURED, MANAGED, SIMULATED AND OBSERVED

AXBANKING  = HOW BANKS CREATE, HOLD, LEND AND SETTLE DEPOSITS/CREDIT

AXFINANCE  = HOW FINANCIAL TRUTH IS ACCOUNTED

AXMARKET   = HOW FINANCIAL INSTRUMENTS ARE TRADED

AXLAW/GOV  = WHO HAS AUTHORITY TO DECIDE
```

---

# 192. End-to-End Monetary Pipeline

```text
LAW / INSTITUTIONAL AUTHORITY
            ↓
MONETARY FRAMEWORK
            ↓
POLICY DECISION
            ↓
MONETARY INSTRUMENT
            ↓
CENTRAL BANK OPERATION
            ↓
BANKING / MARKET CONDITIONS
            ↓
LIQUIDITY / CREDIT
            ↓
HOUSEHOLD / ENTERPRISE ACTIVITY
            ↓
OUTPUT / INCOME
            ↓
PRICES / INFLATION
            ↓
OBSERVATION
            ↓
FORECAST / ANALYSIS
            ↓
NEXT POLICY CYCLE
```

---

# 193. Civilization Economic Chain

```text
AXRESOURCE
    ↓
AXAGRI / AXMANUFACTURING / AXCONSTRUCTION
    ↓
AXCOMMERCE
    ↓
AXLABOR
    ↓
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
    ↓
AXCIVILIZATION
```

---

# 194. Monetary Feedback Loop

```text
CIVILIZATION
      ↓
INCOME
      ↓
SAVINGS
      ↓
BANKING / INVESTMENT
      ↓
CREDIT / CAPITAL
      ↓
SPENDING
      ↓
PRODUCTION
      ↓
PRICES
      ↓
INFLATION
      ↓
MONETARY POLICY
      ↓
LIQUIDITY / CREDIT CONDITIONS
      ↓
BANKING / INVESTMENT
      ↓
CIVILIZATION
```

---

# 195. Acceptance Criteria

BOOTSTRAP-694 được coi là hoàn thành khi implementation có:

1. currency model;
2. money model;
3. central-bank model;
4. monetary aggregate engine;
5. monetary issuance/redemption;
6. reserve accounting;
7. interest-rate framework;
8. policy-rate framework;
9. monetary policy state machine;
10. liquidity operations;
11. emergency liquidity;
12. FX reserve model;
13. FX rate model;
14. exchange-rate regime;
15. FX intervention;
16. sterilization;
17. digital-money boundary;
18. CBDC abstraction;
19. monetary transmission model;
20. macro observation model;
21. vintage/revision support;
22. scenario engine;
23. digital twin;
24. agent-based simulation;
25. stress testing;
26. deterministic replay;
27. distributed authoritative state;
28. AI policy-analysis boundary;
29. capability/security model;
30. provenance/audit;
31. dimensional monetary type checking;
32. fixed-point authoritative arithmetic;
33. GPU simulation path;
34. WASM/mobile profiles;
35. minimal-linkage runtime;
36. ≥18,000 automated tests target;
37. ≥1,800 architecture invariants target.

---

# 196. Final Specification Principle

AXMONETARY phải biến tiền tệ từ một tập hợp các biến số rời rạc thành một **typed, auditable, deterministic, simulation-capable monetary state machine**.

Axiom không chỉ biểu diễn:

```text
money = number
rate = number
inflation = number
```

mà phải biểu diễn:

```text
money
    + currency
    + issuer
    + holder
    + form
    + timestamp
    + provenance
    + authority
    + state
```

và:

```text
policy
    + instrument
    + authority
    + effective_time
    + model
    + assumptions
    + authorization
    + execution
    + observation
```

Từ đó cùng một nền tảng native có thể phục vụ:

```text
financial applications
banking
central-bank infrastructure
economic research
AI economic agents
macro simulation
digital twins
civilization-scale economic simulation
```

mà không biến những giả định của một mô hình kinh tế cụ thể thành luật cứng của ngôn ngữ Axiom.

---

# 197. Task Completion

```text
BOOTSTRAP-694
STATUS = ARCHITECTURE COMPLETE
NAMESPACE = AXMONETARY
TEST TARGET = 18,000+
INVARIANT TARGET = 1,800+
```

# 198. Architecture Position

Chuỗi tài chính hiện tại:

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
    ↓
AXCIVILIZATION
```

Vòng phản hồi:

```text
CIVILIZATION
    ↓
ECONOMIC ACTIVITY
    ↓
BANKING / CAPITAL
    ↓
MARKETS
    ↓
MONEY / LIQUIDITY
    ↓
MONETARY POLICY
    ↓
CREDIT CONDITIONS
    ↓
ECONOMIC ACTIVITY
```

**BOOTSTRAP-694 hoàn tất.**
:::

Đây là lớp tiền tệ cốt lõi; nó cũng tạo một ranh giới quan trọng để các task sau có thể xây **hệ thống kinh tế quốc tế/xuyên biên giới** mà không trộn FX execution, monetary policy, trade và balance-of-payments vào cùng một runtime.