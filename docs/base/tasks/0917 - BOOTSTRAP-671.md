Tiếp tục với task kế tiếp trong chuỗi Axiom: **BOOTSTRAP-671 — Native AI Civilization-Scale Economy, Markets, Production, Finance, Trade, Monetary Systems & Economic Simulation Runtime 5.0**.

Đây là lớp kinh tế nằm **trên 669 + 670**, nhưng **không biến Axiom thành một hệ thống quyết định chính sách kinh tế**. Nó cung cấp primitive để mô hình hóa, kế toán, mô phỏng và thực thi các hoạt động kinh tế một cách trung lập.

:::writing{variant="document" id="58321" title="BOOTSTRAP-671 — Native AI Civilization-Scale Economy, Markets, Production, Finance, Trade, Monetary Systems & Economic Simulation Runtime 5.0"}
# BOOTSTRAP-671
## Native AI Civilization-Scale Economy, Markets, Production, Finance, Trade, Monetary Systems & Economic Simulation Runtime 5.0

**Status:** ARCHITECTURE COMPLETE  
**Layer:** Civilization-Scale Economic Systems  
**Task ID:** BOOTSTRAP-671  
**Depends on:** BOOTSTRAP-603 … BOOTSTRAP-670  
**Primary dependencies:** 639, 642, 648, 652, 653, 655, 661, 663, 664, 665, 667, 668, 669, 670  
**Target:** ≥ 4,000 tests, ≥ 320 invariants  
**Execution modes:** local / distributed / deterministic simulation / real-world connected execution  
**Default:** optional, capability-gated, policy-gated, privacy-gated, safety-gated  
**Zero-cost requirement:** no economic runtime cost when unused

---

# 1. Purpose

BOOTSTRAP-671 defines Axiom's native economic substrate.

It models and executes:

- economic agents;
- households and firms;
- goods and services;
- production;
- consumption;
- supply and demand;
- markets;
- prices;
- orders and trades;
- money;
- currencies;
- accounts;
- double-entry accounting;
- payments;
- clearing and settlement;
- banking;
- credit;
- loans;
- debt;
- collateral;
- investment;
- securities;
- portfolios;
- insurance;
- trade;
- foreign exchange;
- supply chains;
- inventories;
- economic shocks;
- macroeconomic aggregates;
- economic simulations;
- economic forecasts;
- economic scenarios;
- economic networks.

The layer must support multiple economic models without embedding one economic ideology, policy regime, or normative objective into the language runtime.

---

# 2. Architectural Position

The economic layer sits between civilization infrastructure/human systems and higher-level governance/intelligence.

```text
603  Capability / Security
        ↓
639  Policy / Authority
        ↓
667  Organizations / Institutions
668  Federation / Inter-Organization
        ↓
669  Physical / Digital Civilization Systems
670  Human / Population / Labor Systems
        ↓
671  Economic Systems
        ↓
642  Analytics
648  Simulation
652  Optimization
653  Causal / Probabilistic Reasoning
655  World Model
661  Objectives
663  Evaluation
664  Safety
665  Human Oversight
```

### Boundary

**669 asks:**

> What resources, infrastructure and production capacities exist?

**670 asks:**

> What people, households, labor and social systems exist?

**671 asks:**

> How are economic resources, goods, services, money, contracts, markets, production, finance and trade exchanged and accounted for?

**668 asks:**

> Which organizations/federations have authority to establish shared rules or agreements?

**639 asks:**

> What policy or authority rules apply?

671 consumes those rules as explicit inputs.

It does not silently invent them.

---

# 3. Non-Goals

671 does not define:

- a preferred economic ideology;
- a preferred monetary policy;
- a preferred taxation system;
- a preferred distribution of wealth;
- a preferred ownership model;
- a preferred market structure;
- a preferred social welfare function;
- human worth;
- political authority;
- legal sovereignty;
- mandatory economic policy.

Axiom must be able to represent:

- market economies;
- planned economies;
- mixed systems;
- cooperative systems;
- decentralized systems;
- centralized systems;
- barter systems;
- monetary systems;
- multi-currency systems;
- simulated economies;
- fictional economies;
- experimental economic models.

The runtime provides mechanisms, not ideological conclusions.

---

# 4. Core Design Principles

## 4.1 Accounting must be explicit

Economic state must be auditable.

Every balance-changing operation must have an explicit accounting representation.

---

## 4.2 Money is not value

Axiom must never equate:

```text
price == value
```

A price is an observed or negotiated economic quantity.

Value may be modeled separately.

---

## 4.3 Quote is not trade

```text
Quote
Order
Match
Execution
Settlement
```

are separate states.

A displayed price does not imply a transaction occurred.

---

## 4.4 Forecast is not observation

Economic forecasts must never overwrite observed data.

```text
Observation
Forecast
Scenario
SimulationResult
```

remain distinct types.

---

## 4.5 Policy is external input

For example:

```text
tax_rate
subsidy
tariff
interest_rule
reserve_requirement
capital_requirement
price_control
transfer_rule
```

are model inputs.

671 executes declared rules.

It does not silently decide them.

---

# 5. Economic Core Type System

## 5.1 Economy

```axiom
struct Economy {
    id: EconomyId
    model: EconomicModelId
    currency_set: CurrencySet
    market_set: MarketSet
    participant_set: ParticipantSet
    accounting_period: Duration
}
```

---

## 5.2 EconomicSystem

```axiom
struct EconomicSystem {
    id: EconomicSystemId
    state: EconomicState
    institutions: []InstitutionRef
    markets: []MarketRef
    currencies: []CurrencyRef
    policies: []PolicyRef
}
```

---

# 6. Economic Participants

671 must integrate with 667 and 670.

Participants may be:

- human;
- household;
- firm;
- cooperative;
- institution;
- government entity;
- nonprofit;
- AI organization;
- software service;
- autonomous economic agent;
- federation;
- market maker;
- financial institution.

The existence of an economic participant does not grant legal status.

---

## 6.1 Participant

```axiom
struct EconomicParticipant {
    id: ParticipantId
    identity: IdentityRef
    kind: ParticipantKind
    accounts: []AccountRef
    permissions: CapabilitySet
}
```

---

## 6.2 Household

671 references 670 household objects.

```axiom
struct HouseholdEconomicProfile {
    household: HouseholdRef
    income: Flow
    consumption: Flow
    savings: Balance
    debt: Balance
    assets: AssetSet
    liabilities: LiabilitySet
}
```

---

## 6.3 Firm

```axiom
struct Firm {
    id: FirmId
    organization: OrganizationRef
    production: ProductionSystem
    accounts: []AccountRef
    inventories: []InventoryRef
    liabilities: []LiabilityRef
    assets: []AssetRef
}
```

---

# 7. Goods and Services

```axiom
struct Good {
    id: GoodId
    unit: UnitId
    quality: QualityModel
    category: GoodCategory
}
```

```axiom
struct Service {
    id: ServiceId
    unit: UnitId
    capacity: Capacity
    quality: QualityModel
}
```

```axiom
struct Commodity {
    id: CommodityId
    good: GoodRef
    grade: CommodityGrade
    location: Location
}
```

A good may have:

- physical quantity;
- digital quantity;
- quality;
- location;
- ownership;
- custody;
- provenance;
- expiration;
- production batch.

---

# 8. Economic Quantities

671 extends the quantity system from 669.

Supported dimensions include:

```text
money
quantity
price
rate
interest
yield
exchange_rate
production
consumption
income
expense
profit
loss
debt
credit
capital
inventory
capacity
time
risk
probability
```

Compile-time dimensional checking is required where statically possible.

Example:

```axiom
price: Money / Quantity
revenue: Money
quantity: Quantity
```

Invalid:

```axiom
price + quantity
```

must fail type checking.

---

# 9. Currency

```axiom
struct Currency {
    id: CurrencyId
    code: String
    scale: UInt32
    issuer: IssuerRef?
    monetary_model: MonetaryModel
}
```

Supported models:

```text
fiat
commodity
tokenized
digital
local
community
asset_backed
algorithmic
simulation_only
```

The runtime must not assume one monetary model.

---

# 10. Money

```axiom
struct Money {
    currency: CurrencyId
    amount: Decimal
}
```

Money must use exact arithmetic where required.

Binary floating-point must not be the default representation for financial settlement.

Recommended representations:

```text
Int128
Int256
Decimal
FixedPoint
Rational
```

depending on target/profile.

---

# 11. Money Supply

```axiom
struct MoneySupply {
    currency: CurrencyId
    circulating: Money
    reserve: Money
    locked: Money
    destroyed: Money
}
```

Money creation/destruction must be explicit.

```text
MoneyIssue
MoneyMint
MoneyBurn
MoneyRetire
```

must generate audit records.

---

# 12. Accounts

```axiom
struct Account {
    id: AccountId
    owner: ParticipantId
    currency: CurrencyId
    balance: Money
    account_type: AccountType
}
```

Types:

```text
asset
liability
equity
revenue
expense
cash
deposit
reserve
escrow
clearing
settlement
inventory
capital
```

---

# 13. Double-Entry Ledger

The core accounting primitive is a balanced journal.

```axiom
struct JournalEntry {
    id: JournalEntryId
    timestamp: Instant
    transaction: TransactionId
    postings: []Posting
}
```

```axiom
struct Posting {
    account: AccountId
    amount: Decimal
    side: DebitCredit
}
```

Invariant:

```text
Σ debit == Σ credit
```

for every balanced journal entry under a single accounting basis.

---

# 14. Ledger

```axiom
struct Ledger {
    id: LedgerId
    accounts: []AccountRef
    entries: []JournalEntryRef
    currency_policy: CurrencyPolicy
    consistency: LedgerConsistency
}
```

Ledger consistency:

```text
strong
serializable
append_only
event_sourced
distributed_consensus
```

---

# 15. Transaction

A transaction is not necessarily a payment.

```axiom
struct Transaction {
    id: TransactionId
    participants: []ParticipantId
    entries: []JournalEntryRef
    state: TransactionState
}
```

States:

```text
DRAFT
AUTHORIZED
POSTED
CLEARED
SETTLED
REVERSED
CANCELLED
FAILED
```

---

# 16. Payment

```axiom
struct Payment {
    id: PaymentId
    payer: ParticipantId
    payee: ParticipantId
    amount: Money
    instrument: PaymentInstrument
    state: PaymentState
}
```

Lifecycle:

```text
CREATE
AUTHORIZE
SUBMIT
CLEAR
SETTLE
CONFIRM
```

Optional:

```text
REVERSE
REFUND
DISPUTE
```

---

# 17. Settlement

Settlement means economic obligations are finalized according to the configured settlement model.

```axiom
struct Settlement {
    id: SettlementId
    obligations: []Obligation
    finality: SettlementFinality
    timestamp: Instant
}
```

Finality models:

```text
immediate
probabilistic
consensus_final
batch_final
contractual
simulation
```

---

# 18. Markets

```axiom
struct Market {
    id: MarketId
    good: GoodRef
    currency: CurrencyId
    mechanism: MarketMechanism
    participants: []ParticipantId
}
```

Supported mechanisms:

```text
fixed_price
bilateral
negotiation
continuous_auction
batch_auction
double_auction
matching_engine
market_maker
automated_market
simulation_market
```

---

# 19. Quotes

```axiom
struct Quote {
    market: MarketId
    bid: Price?
    ask: Price?
    quantity: Quantity?
    timestamp: Instant
}
```

Quote does not imply execution.

---

# 20. Orders

```axiom
struct Order {
    id: OrderId
    participant: ParticipantId
    market: MarketId
    side: BuySell
    quantity: Quantity
    limit_price: Price?
    time_policy: TimeInForce
}
```

Order lifecycle:

```text
NEW
OPEN
PARTIAL
FILLED
CANCELLED
EXPIRED
REJECTED
```

---

# 21. Order Book

```axiom
struct OrderBook {
    bids: OrderedSet<Order>
    asks: OrderedSet<Order>
}
```

Matching must be deterministic under deterministic mode.

Default matching policy must be explicitly configured.

Possible policies:

```text
price_time
pro_rata
size_priority
custom
```

---

# 22. Trade

```axiom
struct Trade {
    id: TradeId
    market: MarketId
    buyer: ParticipantId
    seller: ParticipantId
    quantity: Quantity
    price: Price
    timestamp: Instant
}
```

A trade records execution.

Settlement is a separate operation.

---

# 23. Market Clearing

```axiom
struct ClearingResult {
    market: MarketId
    clearing_price: Price
    clearing_quantity: Quantity
    unmatched_buy: Quantity
    unmatched_sell: Quantity
}
```

The engine must support:

- supply/demand curves;
- auction clearing;
- partial fills;
- shortages;
- surpluses;
- rationing rules as explicit policies.

---

# 24. Supply and Demand

```axiom
struct SupplyCurve {
    points: []SupplyPoint
}
```

```axiom
struct DemandCurve {
    points: []DemandPoint
}
```

```axiom
struct Demand {
    good: GoodId
    quantity: Quantity
    price_limit: Price?
    time_window: TimeWindow
}
```

```axiom
struct Supply {
    good: GoodId
    quantity: Quantity
    minimum_price: Price?
    time_window: TimeWindow
}
```

---

# 25. Elasticity

```axiom
struct Elasticity {
    variable_x: EconomicVariable
    variable_y: EconomicVariable
    coefficient: Decimal
    estimation_method: EstimationMethod
}
```

Elasticity is an estimated/model quantity, not an intrinsic property unless explicitly defined.

---

# 26. Production

Production bridges 671 with 669.

```axiom
struct ProductionProcess {
    id: ProcessId
    inputs: []ProductionInput
    outputs: []ProductionOutput
    capacity: Capacity
    duration: Duration
}
```

Example:

```axiom
process steel:
    input iron_ore: 2.0 t
    input energy: 5.0 MWh
    output steel: 1.0 t
```

---

# 27. Production Function

```axiom
struct ProductionFunction {
    inputs: []Factor
    output: Factor
    function: EconomicExpression
}
```

Supported forms:

```text
linear
constant_returns
CobbDouglas
Leontief
CES
piecewise
table
neural
custom
```

No model is mandatory.

---

# 28. Bill of Materials

```axiom
struct BillOfMaterials {
    product: GoodId
    components: []MaterialRequirement
}
```

Each component may specify:

- quantity;
- quality;
- substitution;
- tolerance;
- lead time;
- source.

---

# 29. Production Capacity

Production capacity consumes 669 capacity data.

```axiom
struct EconomicProductionCapacity {
    facility: FacilityRef
    product: GoodId
    maximum_rate: Rate
    available_rate: Rate
    reserved_rate: Rate
}
```

---

# 30. Inventory

```axiom
struct Inventory {
    id: InventoryId
    owner: ParticipantId
    good: GoodId
    quantity: Quantity
    location: Location
    valuation: ValuationMethod
}
```

Supported valuation methods:

```text
FIFO
LIFO
weighted_average
specific_identification
market
replacement_cost
custom
```

The method is explicit.

---

# 31. Supply Chain

```axiom
struct SupplyChain {
    id: SupplyChainId
    nodes: []SupplyNode
    links: []SupplyLink
}
```

Nodes:

```text
supplier
factory
warehouse
distribution_center
retailer
consumer
port
transport_hub
```

Links include:

```text
capacity
lead_time
cost
reliability
risk
```

---

# 32. Shipment

```axiom
struct Shipment {
    id: ShipmentId
    origin: Location
    destination: Location
    cargo: []CargoItem
    route: RouteRef
    status: ShipmentStatus
}
```

---

# 33. Supply Chain Disruption

The runtime must model:

```text
delay
capacity_loss
facility_failure
transport_failure
inventory_shortage
supplier_failure
energy_shortage
communication_failure
demand_shock
```

It must not assume a particular recovery policy.

---

# 34. Contracts

```axiom
struct EconomicContract {
    id: ContractId
    parties: []ParticipantId
    obligations: []Obligation
    consideration: []Consideration
    lifecycle: ContractLifecycle
}
```

Contract execution remains subject to:

- capability;
- authority;
- policy;
- safety;
- human approval where required.

---

# 35. Invoice

```axiom
struct Invoice {
    id: InvoiceId
    issuer: ParticipantId
    recipient: ParticipantId
    lines: []InvoiceLine
    total: Money
    due: Instant
    status: InvoiceStatus
}
```

---

# 36. Debt

```axiom
struct Debt {
    id: DebtId
    creditor: ParticipantId
    debtor: ParticipantId
    principal: Money
    interest: InterestRule
    maturity: Instant
}
```

---

# 37. Credit

```axiom
struct CreditLine {
    id: CreditLineId
    borrower: ParticipantId
    limit: Money
    drawn: Money
    rate: InterestRate
    collateral: []CollateralRef
}
```

Credit availability must never be confused with actual debt.

---

# 38. Loan

```axiom
struct Loan {
    id: LoanId
    principal: Money
    rate: InterestRate
    schedule: RepaymentSchedule
    collateral: []CollateralRef
}
```

Supported repayment models:

```text
amortizing
interest_only
bullet
variable
custom
```

---

# 39. Interest

```axiom
struct InterestRate {
    value: Decimal
    period: Duration
    compounding: CompoundingMethod
}
```

Methods:

```text
simple
compound
continuous
custom
```

Exact arithmetic is mandatory for settlement calculations.

---

# 40. Collateral

```axiom
struct Collateral {
    asset: AssetRef
    pledged_value: Money
    haircut: Decimal
    status: CollateralStatus
}
```

Lifecycle:

```text
REGISTER
LOCK
VALUE
REVALUE
RELEASE
LIQUIDATE
```

---

# 41. Banking

```axiom
struct Bank {
    id: BankId
    institution: InstitutionRef
    deposits: []AccountRef
    loans: []LoanRef
    reserves: []AccountRef
    capital: Money
}
```

The type represents a banking model.

It does not grant legal banking authority.

---

# 42. Deposit

```axiom
struct Deposit {
    account: AccountId
    amount: Money
    maturity: Duration?
    rate: InterestRate?
}
```

---

# 43. Clearing

```axiom
struct ClearingHouse {
    id: ClearingHouseId
    participants: []ParticipantId
    obligations: []Obligation
    netting_policy: NettingPolicy
}
```

Supported:

```text
gross_settlement
bilateral_netting
multilateral_netting
batch_netting
```

---

# 44. Foreign Exchange

```axiom
struct ExchangeRate {
    base: CurrencyId
    quote: CurrencyId
    rate: Decimal
    timestamp: Instant
}
```

```axiom
struct FXTrade {
    base_amount: Money
    quote_amount: Money
    rate: ExchangeRate
}
```

Multi-currency accounting must preserve currency identity.

---

# 45. Investment

```axiom
struct Investment {
    id: InvestmentId
    investor: ParticipantId
    asset: AssetRef
    principal: Money
    expected_return: Rate?
    risk_model: RiskModel?
    maturity: Instant?
}
```

---

# 46. Securities

Generic security representation:

```axiom
struct Security {
    id: SecurityId
    issuer: ParticipantId
    security_type: SecurityType
    face_value: Money?
    maturity: Instant?
    cashflows: []CashFlow
}
```

Types:

```text
equity
bond
note
fund_unit
certificate
derivative
tokenized_asset
custom
```

No security is inherently safe or profitable.

---

# 47. Portfolio

```axiom
struct Portfolio {
    id: PortfolioId
    owner: ParticipantId
    positions: []Position
    cash: []Money
}
```

Portfolio operations:

```text
BUY
SELL
TRANSFER
REBALANCE
VALUATE
LIQUIDATE
```

---

# 48. Risk

Risk must be represented explicitly.

```axiom
struct RiskModel {
    distribution: Distribution
    horizon: Duration
    confidence: Decimal?
    assumptions: []ModelAssumption
}
```

Supported methods may include:

```text
variance
covariance
VaR
CVaR
scenario
MonteCarlo
stress_test
custom
```

Risk metrics are model outputs, not guarantees.

---

# 49. Insurance

```axiom
struct InsurancePolicy {
    id: PolicyId
    insurer: ParticipantId
    insured: ParticipantId
    coverage: Coverage
    premium: Money
    deductible: Money
    term: TimeWindow
}
```

Claims:

```axiom
struct InsuranceClaim {
    id: ClaimId
    policy: PolicyId
    event: EventRef
    claimed_amount: Money
    approved_amount: Money?
    status: ClaimStatus
}
```

Support:

- reserves;
- claims;
- loss distributions;
- reinsurance;
- deductibles;
- limits;
- exclusions;
- scenario simulation.

---

# 50. Economic Policy Inputs

Policy must be represented as data.

```axiom
struct EconomicPolicyInput {
    id: PolicyId
    issuer: AuthorityRef
    effective_period: TimeWindow
    rules: []EconomicRule
}
```

Possible rule categories:

```text
tax
subsidy
transfer
tariff
price_limit
interest_rule
credit_rule
reserve_rule
capital_rule
trade_rule
labor_rule
monetary_rule
fiscal_rule
```

671 does not determine whether a policy should exist.

---

# 51. Trade

```axiom
struct TradeFlow {
    exporter: ParticipantId
    importer: ParticipantId
    good: GoodId
    quantity: Quantity
    currency: CurrencyId
    value: Money
}
```

Trade metadata:

```text
origin
destination
route
currency
exchange_rate
tariff
tax
subsidy
insurance
shipping
customs
```

These are independent fields.

---

# 52. Import / Export

```axiom
struct ImportRecord {
    shipment: ShipmentId
    importer: ParticipantId
    origin: JurisdictionId
}
```

```axiom
struct ExportRecord {
    shipment: ShipmentId
    exporter: ParticipantId
    destination: JurisdictionId
}
```

Cross-jurisdiction rules are provided by 639/668.

---

# 53. Economic Aggregates

671 provides generic aggregate metrics.

```axiom
struct AggregateMetric {
    id: MetricId
    name: String
    value: Decimal
    unit: UnitId
    population_scope: Scope
    period: TimeWindow
}
```

Possible metrics:

```text
output
income
consumption
investment
employment
unemployment
productivity
price_index
inflation_rate
money_supply
credit
debt
trade_balance
capital_stock
inventory
```

Axiom does not hard-code a single definition of GDP or national welfare.

---

# 54. Macroeconomic State

```axiom
struct MacroState {
    output: AggregateMetric
    consumption: AggregateMetric
    investment: AggregateMetric
    government_spending: AggregateMetric?
    imports: AggregateMetric
    exports: AggregateMetric
    prices: AggregateMetric
    employment: AggregateMetric
    money: AggregateMetric?
    credit: AggregateMetric?
}
```

Fields may be absent.

---

# 55. Economic Models

A generic economic model interface:

```axiom
trait EconomicModel {
    init(state: EconomicState) -> EconomicState
    step(state: EconomicState, dt: Duration) -> EconomicState
    observe(state: EconomicState) -> []Observation
}
```

Implementations may include:

```text
AgentBasedModel
MicroeconomicModel
MacroeconomicModel
InputOutputModel
StockFlowModel
EquilibriumModel
PartialEquilibriumModel
DisequilibriumModel
SystemDynamicsModel
MonteCarloModel
HybridEconomicModel
CustomEconomicModel
```

---

# 56. Agent-Based Economy

Agents may contain:

```text
preferences
constraints
budgets
production
consumption
expectations
assets
liabilities
strategies
information
```

No default preference model is imposed.

---

# 57. Equilibrium

```axiom
struct EquilibriumResult {
    state: EconomicState
    residual: Decimal
    convergence: ConvergenceStatus
    assumptions: []ModelAssumption
}
```

The engine must distinguish:

```text
equilibrium found
equilibrium approximated
not converged
multiple equilibria
no feasible equilibrium
```

---

# 58. Disequilibrium

The simulation engine must support economies where:

```text
supply != demand
```

and where prices do not immediately clear markets.

This is important for:

- shortages;
- excess inventory;
- unemployment;
- queues;
- rationing;
- delayed adjustment;
- supply-chain disruption.

---

# 59. Economic Shock

```axiom
struct EconomicShock {
    id: ShockId
    kind: ShockKind
    target: EconomicEntity
    magnitude: Quantity
    duration: Duration
    distribution: Distribution?
}
```

Kinds:

```text
supply
demand
price
financial
monetary
credit
trade
energy
infrastructure
demographic
health
technology
environmental
policy
```

---

# 60. Business Cycle

Business-cycle analysis is represented as an observation/modeling facility.

```axiom
struct CycleState {
    phase: CyclePhase
    duration: Duration
    indicators: []AggregateMetric
}
```

It must not assert causality merely because two indicators correlate.

Causal analysis belongs to 653.

---

# 61. Economic Simulation

```axiom
struct EconomicSimulation {
    id: SimulationId
    model: EconomicModelId
    state: EconomicState
    clock: SimulationClock
    seed: UInt64
    determinism: DeterminismMode
}
```

Operations:

```text
create
initialize
step
run
pause
checkpoint
restore
branch
compare
terminate
```

---

# 62. Simulation Scales

Supported scales:

```text
individual
household
firm
market
sector
city
region
country-like jurisdiction
federation
global
```

The runtime must support mixed-resolution models.

Example:

```text
individual agents
    ↓
household aggregates
    ↓
regional market
    ↓
global trade model
```

---

# 63. Simulation Time

Simulation supports:

```text
discrete_event
fixed_step
adaptive_step
continuous_approximation
hybrid
```

Events include:

```text
trade
payment
production
consumption
default
price_update
inventory_update
policy_change
shock
migration
infrastructure_failure
```

---

# 64. Economic Forecast

```axiom
struct EconomicForecast {
    model: EconomicModelId
    target: EconomicVariable
    horizon: TimeWindow
    predictions: []ForecastPoint
    uncertainty: []Interval
}
```

A forecast must retain:

- model;
- version;
- training/estimation period;
- assumptions;
- uncertainty;
- timestamp.

---

# 65. Scenario

```axiom
struct EconomicScenario {
    baseline: ScenarioRef
    assumptions: []ScenarioAssumption
    shocks: []EconomicShock
    policies: []EconomicPolicyInput
}
```

Scenario comparison must preserve the distinction between:

```text
observed
counterfactual
simulated
forecast
```

---

# 66. Accounting Invariants

The compiler/runtime must enforce or validate the following.

### AINV-001 — Balanced journal

```text
Σ debit = Σ credit
```

### AINV-002 — Currency correctness

Money of incompatible currencies cannot be directly added.

### AINV-003 — Explicit FX

Cross-currency conversion requires an exchange operation or declared conversion rule.

### AINV-004 — No implicit money creation

Money supply changes require explicit issuance/mint/burn events.

### AINV-005 — Settlement consistency

A settled obligation cannot silently return to unsettled state.

### AINV-006 — Account identity

An account has exactly one configured accounting owner.

### AINV-007 — Asset/liability consistency

A financial instrument must declare whether it represents an asset, liability, equity, or another class.

### AINV-008 — Order/trade separation

An order does not become a trade without a matching/execution event.

### AINV-009 — Quote/trade separation

A quote is not an executed price.

### AINV-010 — Forecast/observation separation

Forecasts cannot overwrite observations.

### AINV-011 — Production conservation

Production cannot consume resources that do not exist unless the model explicitly permits external creation.

### AINV-012 — Inventory conservation

Inventory changes must be attributable to:

```text
receive
produce
consume
transfer
adjust
dispose
loss
```

### AINV-013 — Loan conservation

Loan principal creation and repayment must be explicitly represented.

### AINV-014 — Collateral uniqueness

The same collateral cannot be simultaneously exclusively pledged to incompatible obligations.

### AINV-015 — Contract obligation consistency

Executed obligations must have a traceable originating contract/order/event.

### AINV-016 — Trade conservation

Executed quantity must be compatible with available sell-side quantity.

### AINV-017 — Supply-chain capacity

Shipment cannot exceed declared route/capacity unless an explicit overflow model exists.

### AINV-018 — Economic unit correctness

Incompatible units cannot be silently combined.

### AINV-019 — Policy provenance

Policy-derived economic changes retain policy provenance.

### AINV-020 — Simulation isolation

Simulation state cannot mutate real-world state unless an explicit execution bridge is invoked.

---

# 67. Financial Data Privacy

Financial data may contain highly sensitive information.

671 must integrate with:

- 603 capability control;
- 627 identity;
- 640 data governance;
- 610 cryptography;
- 665 human oversight.

Supported mechanisms:

```text
field-level access
account-level access
aggregate-only access
privacy-preserving aggregation
redaction
encryption
audit
retention
deletion policy
```

---

# 68. Real-World Financial Execution Boundary

Simulation:

```text
EconomicSimulation
```

must be isolated from:

```text
PaymentNetwork
Bank
Exchange
RealAccount
RealAsset
```

until an explicit execution capability is granted.

Example:

```axiom
simulate scenario

authorize finance.execute

execute settlement
```

must be distinct.

An AI agent cannot silently convert a simulation result into a real financial transaction.

---

# 69. Human Approval Boundary

High-impact operations may require 665:

```text
large transfer
asset liquidation
credit issuance
loan approval
portfolio rebalance
financial contract activation
policy change
real-money execution
```

Approval requirements are policy/capability configuration.

---

# 70. Optimization Boundary

671 may expose economic objectives to 652:

```axiom
objective maximize_profit
objective minimize_cost
objective minimize_risk
objective maximize_throughput
objective minimize_delay
```

But 671 must not declare any objective universally correct.

The objective is supplied by the caller/model/policy.

---

# 71. AI Integration

AI agents may use economic APIs for:

- market analysis;
- accounting;
- simulation;
- forecasting;
- planning;
- optimization;
- scenario generation;
- supply-chain analysis;
- financial modeling.

Agent access is capability-scoped.

An AI agent does not gain:

```text
money
ownership
legal authority
financial authority
policy authority
```

merely by using 671.

---

# 72. Economic Knowledge Graph Integration

Economic entities may be represented in 645:

```text
Firm
Household
Good
Market
Contract
Asset
Liability
Trade
ProductionProcess
SupplyChain
Bank
Currency
Policy
```

Relationships:

```text
owns
produces
consumes
supplies
demands
trades_with
owes
lends_to
invests_in
insures
depends_on
imports
exports
```

---

# 73. Event Model

671 emits structured events.

Examples:

```text
EconomyCreated
AccountCreated
TransactionPosted
PaymentAuthorized
PaymentSettled
MoneyIssued
MoneyBurned
OrderSubmitted
OrderMatched
TradeExecuted
InventoryChanged
ProductionStarted
ProductionCompleted
LoanCreated
LoanDrawn
LoanRepaid
LoanDefaulted
CollateralLocked
CollateralReleased
InvestmentCreated
SecurityTraded
InsuranceClaimed
ShipmentStarted
ShipmentDelivered
EconomicShockInjected
ForecastGenerated
SimulationCheckpointed
```

---

# 74. Economic Audit

Every economically significant state transition must optionally produce:

```text
event_id
actor
capability
timestamp
previous_state_hash
new_state_hash
transaction_id
policy_provenance
model_version
```

Audit can be:

```text
local
distributed
append_only
cryptographically chained
```

---

# 75. Deterministic Economic Simulation

For reproducible research:

```axiom
simulation deterministic {
    seed: 12345
}
```

must produce identical results when:

- same model version;
- same seed;
- same input;
- same floating-point mode;
- same event ordering;
- same dependency versions.

Parallel simulations must provide deterministic reduction modes where requested.

---

# 76. Parallel Simulation

Supported decomposition:

```text
market parallelism
agent parallelism
region parallelism
scenario parallelism
Monte Carlo parallelism
time-window parallelism
```

Synchronization boundaries must be explicit.

---

# 77. Distributed Economic State

Different consistency levels are allowed.

### Settlement

Prefer:

```text
strong consistency
```

### Market analytics

May use:

```text
eventual consistency
```

### Forecasts

May use:

```text
asynchronous
```

### Simulation

May use:

```text
deterministic distributed execution
```

Consistency model must never be implicit.

---

# 78. Economic Model Versioning

Every economic model must have:

```text
model_id
model_version
schema_version
parameter_version
data_version
code_hash
```

This permits exact reproduction.

---

# 79. Model Assumptions

```axiom
struct ModelAssumption {
    name: String
    value: Value
    provenance: Provenance
    sensitivity: Sensitivity?
}
```

Economic simulation results without assumptions are incomplete.

---

# 80. Sensitivity Analysis

```axiom
struct SensitivityResult {
    parameter: ParameterId
    baseline: Decimal
    perturbed: Decimal
    output_delta: Decimal
}
```

Supports:

```text
one_at_a_time
local
global
MonteCarlo
Sobol
custom
```

---

# 81. Economic Validation

Models must support:

```text
calibration
backtesting
out_of_sample
cross_validation
stress_test
scenario_test
sensitivity_test
conservation_test
accounting_test
```

Model validation belongs to 663.

671 supplies the economic execution substrate.

---

# 82. Economic Simulation Safety

Simulation must clearly mark:

```text
SIMULATED
COUNTERFACTUAL
FORECAST
OBSERVED
EXECUTED
```

These states must not be silently interchangeable.

---

# 83. Native Metadata

Recommended annotations:

```text
@economy
@economic_system
@participant
@firm
@household_economy
@good
@service
@commodity
@money
@currency
@account
@ledger
@journal
@transaction
@payment
@settlement
@price
@quote
@order
@order_book
@trade
@market
@contract
@invoice
@debt
@loan
@credit
@interest
@collateral
@bank
@clearing
@finance
@investment
@security
@portfolio
@insurance
@production
@inventory
@supply
@demand
@supply_chain
@shipment
@trade_flow
@exchange_rate
@macro
@aggregate
@economic_model
@economic_simulation
@forecast
@scenario
@shock
@risk
```

---

# 84. Economic File Formats

Recommended metadata extensions:

```text
.axeconomy
.axfirm
.axgood
.axmarket
.axmoney
.axcurrency
.axaccount
.axledger
.axtransaction
.axpayment
.axprice
.axorder
.axtrade
.axcontract
.axdebt
.axloan
.axcredit
.axbank
.axfinance
.axinvestment
.axportfolio
.axinsurance
.axproduction
.axinventory
.axsupply
.axdemand
.axsupplychain
.axfx
.axmacro
.axeconmodel
.axecsim
.axeconforecast
.axeconshock
.axrisk
```

These are logical formats; physical serialization may use Axiom's common serialization layer.

---

# 85. Compiler IR

Required economic IR operations:

```text
EconomyCreate
EconomicModelDefine

ParticipantCreate
FirmCreate
HouseholdEconomicProfileCreate

GoodDefine
ServiceDefine
CommodityDefine

MarketCreate
MarketRegister
QuoteCreate

OrderCreate
OrderCancel
OrderMatch
TradeExecute

CurrencyCreate
MoneyIssue
MoneyMint
MoneyBurn

AccountCreate
LedgerCreate
JournalCreate
JournalPost
LedgerReconcile

TransactionCreate
PaymentCreate
PaymentAuthorize
PaymentClear
PaymentSettle
PaymentReverse

FXQuote
FXTrade

InvoiceCreate
InvoicePay

ContractCreate
ContractExecute

DebtCreate
LoanCreate
LoanDraw
LoanRepay
LoanDefault

CreditLineCreate
CreditDraw
CreditRepay

InterestAccrue

CollateralLock
CollateralRelease
CollateralLiquidate

BankCreate
DepositCreate
DepositWithdraw

ClearingCreate
ClearingNet
ClearingSettle

SecurityCreate
SecurityBuy
SecuritySell
SecurityMature

InvestmentCreate
PortfolioCreate
PortfolioRebalance

InsurancePolicyCreate
InsurancePremiumPay
InsuranceClaimCreate
InsuranceClaimSettle

ProductionDefine
ProductionPlan
ProductionRun
ProductionComplete

InventoryCreate
InventoryReceive
InventoryIssue
InventoryReserve
InventoryTransfer
InventoryAdjust

SupplyRegister
DemandRegister

SupplyChainCreate
SupplyChainRoute
ShipmentCreate
ShipmentDispatch
ShipmentDeliver

TradeImport
TradeExport

AggregateCompute
MacroStateCreate

EconomicModelCreate
EconomicSimulationCreate
EconomicSimulationStep
EconomicSimulationRun
EconomicSimulationCheckpoint
EconomicSimulationRestore
EconomicSimulationBranch

EconomicScenarioCreate
EconomicShockInject

EconomicForecastCreate

EconomicReconcile
EconomicAudit
```

---

# 86. CLI

Core CLI:

```text
axiom economy list
axiom economy inspect
axiom economy create
axiom economy status
```

Participants:

```text
axiom firm list
axiom firm inspect
axiom firm create

axiom household-economy inspect
```

Goods:

```text
axiom good list
axiom good create
axiom service list
axiom commodity list
```

Markets:

```text
axiom market list
axiom market create
axiom market inspect
axiom market quote
axiom market orderbook
axiom market trade
```

Accounting:

```text
axiom account list
axiom account create
axiom account balance

axiom ledger inspect
axiom ledger post
axiom ledger reconcile

axiom transaction inspect
```

Payments:

```text
axiom payment create
axiom payment authorize
axiom payment clear
axiom payment settle
axiom payment reverse
```

Money:

```text
axiom money currencies
axiom money issue
axiom money burn
axiom money supply
```

FX:

```text
axiom fx rates
axiom fx quote
axiom fx trade
```

Credit:

```text
axiom credit list
axiom credit create
axiom credit draw
axiom credit repay
axiom credit default
```

Loans:

```text
axiom loan list
axiom loan create
axiom loan amortize
axiom loan repay
```

Banking:

```text
axiom bank list
axiom bank inspect
axiom bank deposits
axiom bank loans
axiom bank liquidity
```

Finance:

```text
axiom finance securities
axiom finance portfolio
axiom finance buy
axiom finance sell
```

Insurance:

```text
axiom insurance policies
axiom insurance claims
axiom insurance settle
```

Production:

```text
axiom production capacity
axiom production plan
axiom production run
```

Inventory:

```text
axiom inventory list
axiom inventory inspect
axiom inventory reserve
```

Supply chain:

```text
axiom supply-chain graph
axiom supply-chain route
axiom supply-chain ship
```

Trade:

```text
axiom trade imports
axiom trade exports
axiom trade balance
```

Macro:

```text
axiom macro state
axiom macro aggregate
axiom macro forecast
```

Simulation:

```text
axiom economy simulation create
axiom economy simulation run
axiom economy simulation step
axiom economy simulation checkpoint
axiom economy simulation restore
axiom economy simulation branch
```

Shock:

```text
axiom economy shock inject
```

Audit:

```text
axiom economy audit
axiom economy reconcile
```

---

# 87. Profiles

```text
AXECO_NONE
AXECO_CORE
AXECO_ACCOUNTING
AXECO_LEDGER
AXECO_MARKET
AXECO_MONEY
AXECO_CURRENCY
AXECO_PAYMENT
AXECO_SETTLEMENT
AXECO_FX
AXECO_CONTRACT
AXECO_CREDIT
AXECO_LOAN
AXECO_BANKING
AXECO_CLEARING
AXECO_FINANCE
AXECO_INVESTMENT
AXECO_SECURITIES
AXECO_PORTFOLIO
AXECO_INSURANCE
AXECO_PRODUCTION
AXECO_INVENTORY
AXECO_SUPPLY
AXECO_DEMAND
AXECO_SUPPLY_CHAIN
AXECO_TRADE
AXECO_MACRO
AXECO_EQUILIBRIUM
AXECO_SIMULATION
AXECO_FORECAST
AXECO_SCENARIO
AXECO_RISK
AXECO_DISTRIBUTED
AXECO_GLOBAL
AXECO_WASM
AXECO_MOBILE
AXECO_EDGE
AXECO_FULL
```

---

# 88. Performance Requirements

671 must not require a heavyweight runtime.

Hot paths must support:

- contiguous structures;
- SoA layouts;
- cache-friendly order books;
- integer/fixed-point arithmetic;
- SIMD;
- parallel matching;
- batch accounting;
- event batching;
- zero-copy serialization;
- memory mapping;
- deterministic parallel execution.

---

# 89. Memory Requirements

Large simulations must support:

```text
streaming
paged state
memory-mapped datasets
snapshot compression
columnar storage
event logs
incremental checkpoints
```

An economic simulation must not require the entire world model to reside in RAM.

---

# 90. GPU Acceleration

GPU execution may accelerate:

```text
Monte Carlo
agent simulation
matrix operations
equilibrium solving
optimization
risk calculations
forecasting
large-scale scenario evaluation
```

The economic semantic model remains identical between CPU and GPU.

---

# 91. WASM

671 WASM profile must support:

- accounting;
- simulation;
- market logic;
- economic models;
- deterministic execution.

Real financial execution APIs remain capability-gated.

---

# 92. Mobile / Edge

Mobile profile may provide:

```text
wallet/account model
local ledger
inventory
point-of-sale
offline simulation
local economic model
sync
```

Offline transactions require explicit conflict/settlement semantics.

---

# 93. Interoperability

671 can interface with external systems through adapters:

```text
banking
payment
exchange
accounting
ERP
inventory
supply-chain
market-data
financial-data
government-data
simulation-data
```

External adapters are optional.

Core Axiom does not depend on them.

---

# 94. Responsibility Map

| Capability | Owner |
|---|---|
| capability/security | 603 |
| resource governor | 606 |
| cryptography | 610 |
| identity | 627 |
| distributed data | 628 |
| observability | 633 |
| policy/authority | 639 |
| data governance/privacy | 640 |
| analytics | 642 |
| simulation infrastructure | 648 |
| optimization | 652 |
| causal/probabilistic reasoning | 653 |
| world model | 655 |
| objectives/preferences | 661 |
| evaluation/validation | 663 |
| AI safety | 664 |
| human oversight | 665 |
| organizations/institutions | 667 |
| inter-organization governance/trade agreements | 668 |
| physical resources/infrastructure | 669 |
| people/households/labor | 670 |
| economic exchange/production/finance/markets | **671** |

---

# 95. Hard Separation Rules

671 MUST NOT:

```text
assign human worth
declare an economic ideology
create political authority
override 639
override 668
override 664
override 665
silently change policy
silently create money
silently alter accounting
treat forecasts as observations
treat prices as objective human values
execute real-world financial transactions without capability
convert simulation into reality without authorization
```

---

# 96. Test Plan

Minimum target:

```text
≥ 4,000 tests
≥ 320 invariants
```

Required categories:

```text
type-system tests
quantity/unit tests
currency tests
money arithmetic tests
ledger tests
double-entry tests
transaction tests
payment tests
settlement tests
market tests
order-book tests
matching tests
price discovery tests
production tests
inventory tests
supply-chain tests
contract tests
credit tests
loan tests
interest tests
collateral tests
banking tests
clearing tests
FX tests
investment tests
portfolio tests
insurance tests
macro tests
equilibrium tests
disequilibrium tests
simulation tests
determinism tests
forecast tests
scenario tests
shock tests
privacy tests
capability tests
authorization tests
distributed-consistency tests
checkpoint/recovery tests
WASM tests
GPU equivalence tests
serialization tests
performance tests
fuzz tests
property tests
```

---

# 97. Property-Based Tests

Required properties include:

```text
balanced ledger remains balanced
currency cannot silently change
money creation is explicit
settlement is idempotent
trade quantity cannot exceed executable quantity
inventory conservation holds
production consumes declared inputs
loan repayment never silently changes principal incorrectly
interest calculation is deterministic
FX conversion is dimensionally valid
simulation checkpoint/restore is equivalent
deterministic simulation reproduces identical results
forecast does not mutate observations
policy provenance remains traceable
```

---

# 98. Failure Recovery

Economic systems must survive:

```text
process crash
network failure
partial payment
duplicate transaction
lost acknowledgement
distributed partition
market node failure
ledger node failure
simulation interruption
checkpoint corruption
external adapter failure
```

Recovery must distinguish:

```text
unknown
pending
committed
settled
reversed
failed
```

rather than guessing.

---

# 99. Economic State Machine

Global economic state may be represented as:

```text
MODEL
  ↓
INITIALIZE
  ↓
OPERATE
  ↓
TRANSACT
  ↓
CLEAR
  ↓
SETTLE
  ↓
ACCOUNT
  ↓
OBSERVE
  ↓
SIMULATE / FORECAST / ANALYZE
  ↓
RECONCILE
```

Failures enter explicit recovery states.

---

# 100. Final Contract

BOOTSTRAP-671 provides Axiom with a native economic substrate capable of representing:

```text
people
households
firms
goods
services
production
consumption
supply
demand
markets
prices
orders
trades
money
currencies
accounts
ledgers
payments
settlement
banking
credit
loans
debt
collateral
investment
securities
portfolios
insurance
foreign exchange
trade
supply chains
macroeconomic state
economic shocks
economic simulation
economic forecasting
```

It integrates with:

```text
669 → resources/infrastructure
670 → people/households/labor
667 → organizations
668 → inter-organizational agreements
639 → policy/authority
642 → analytics
648 → simulation
652 → optimization
653 → causal reasoning
655 → world models
661 → objectives
663 → evaluation
664 → safety
665 → human oversight
```

The final semantic boundary is:

> **671 can model, account for, simulate and execute explicitly authorized economic operations, but it cannot decide what an economy should value, what policy should be chosen, who should receive resources, or whether a financial action is normatively desirable.**

**Architecture status: COMPLETE.**

**BOOTSTRAP-671 is now closed.**

**Next task: BOOTSTRAP-672 — Native AI Civilization-Scale Science, Research, Knowledge Production, Technology Development, Innovation, Discovery & Scientific Simulation Runtime 5.0.**
:::

BOOTPSTRAP-671 đã hoàn tất. Theo chuỗi kiến trúc hiện tại, task tiếp theo là **BOOTSTRAP-672**, tập trung vào **khoa học, nghiên cứu, tri thức, phát minh, đổi mới công nghệ và mô phỏng khoa học**, nối 671 với 645/648/652/653/655.