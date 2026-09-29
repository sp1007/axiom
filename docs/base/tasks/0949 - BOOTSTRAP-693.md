Tiếp tục tự động với **BOOTSTRAP-693** — lớp hạ tầng thị trường vốn nối `AXINVEST` với giao dịch, sàn, broker, market data, clearing, settlement và custody.

:::writing{variant="document" id="74136" title="BOOTSTRAP-693 — Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Order Management, Market Data, Clearing, Settlement, Custody & Global Financial Market Infrastructure Runtime 5.0"}
# BOOTSTRAP-693
## Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Order Management, Market Data, Clearing, Settlement, Custody & Global Financial Market Infrastructure Runtime 5.0

**Status:** Architecture Specification  
**Version:** 5.0  
**Namespace:** `AXCAPITALMARKET`

---

# 1. Mục tiêu

`AXCAPITALMARKET` là native runtime của Axiom cho toàn bộ **market infrastructure layer** nằm giữa investment intent và financial settlement.

Nó phải mô hình hóa được:

```text
Investor
   ↓
Investment Decision
   ↓
Order Intent
   ↓
Broker
   ↓
Order Management
   ↓
Exchange / Trading Venue
   ↓
Matching
   ↓
Trade
   ↓
Clearing
   ↓
Settlement
   ↓
Custody
   ↓
Position
```

ở quy mô:

```text
INDIVIDUAL
INSTITUTION
MARKET
NATIONAL FINANCIAL SYSTEM
GLOBAL FINANCIAL SYSTEM
```

---

# 2. Vị trí trong Axiom

```text
AXFINANCE
    │
    ├── AXBANKING
    ├── AXINSURANCE
    ├── AXINVEST
    │      │
    │      └──────────────┐
    │                     ↓
    │             AXCAPITALMARKET
    │                     │
    │       ┌─────────────┼──────────────┐
    │       ↓             ↓              ↓
    │   Trading       Clearing        Settlement
    │       ↓             ↓              ↓
    │   Exchange       CCP/Clearing    Custody
    │       │
    │       ↓
    │   Market Data
    │
    └────────────────────────→ AXFINANCE
```

---

# 3. Core distinction

Runtime bắt buộc phân biệt:

```text
InvestmentDecision
OrderIntent
Order
Execution
Trade
ClearedTrade
SettlementInstruction
Settlement
CustodyPosition
LedgerEntry
```

Không được gộp chúng thành một `Transaction`.

---

# 4. Fundamental invariants

```text
Order ≠ Trade
Trade ≠ Settlement
Settlement ≠ Custody
Quote ≠ ExecutedPrice
MarketPrice ≠ FairValue
OrderBook ≠ MarketState
Execution ≠ Clearing
Clearing ≠ Settlement
CustodyPosition ≠ EconomicOwnership
Recommendation ≠ Order
Order ≠ Authorization
Authorization ≠ Execution
Prediction ≠ MarketFact
Simulation ≠ LiveMarket
MarketData ≠ AccountingTruth
```

---

# 5. Phạm vi

Bao gồm:

```text
Market
Exchange
TradingVenue
Broker
Dealer
Order
OrderManagement
Execution
OrderBook
Matching
Auction
Quote
Trade
MarketData
ReferenceData
Clearing
CCP
Margin
Collateral
Settlement
Custody
Depository
CorporateActions
SecuritiesLending
Repo
ShortSelling
MarketSurveillance
MarketRisk
Liquidity
MarketSimulation
MarketAI
```

---

# 6. Không thuộc core

Không trực tiếp sở hữu:

```text
portfolio optimization
wealth planning
fund strategy
general accounting ledger
bank deposit
insurance underwriting
legal ownership authority
government regulatory authority
```

Các phần này thuộc:

```text
AXINVEST
AXFINANCE
AXBANKING
AXINSURANCE
AXLAW
AXGOV
```

---

# 7. Market ecosystem

```text
Investor
Broker
Dealer
Exchange
TradingVenue
MarketMaker
ClearingMember
CCP
Custodian
Depository
SettlementBank
Regulator
Issuer
DataProvider
```

---

# 8. Market

```axiom
struct Market {
    id: MarketId
    name: String
    jurisdiction: JurisdictionRef
    currency: Currency
    venues: VenueSet
    calendar: MarketCalendarRef
}
```

---

# 9. Trading venue

```axiom
struct TradingVenue {
    id: VenueId
    market: MarketRef
    venue_type: VenueType
    instruments: InstrumentSet
    matching_engine: MatchingEngineRef
    trading_calendar: MarketCalendarRef
}
```

---

# 10. Venue types

```text
Exchange
AlternativeTradingSystem
ElectronicCommunicationNetwork
DarkPool
OTC
AuctionVenue
RFQVenue
PeriodicMarket
InternalCrossingVenue
```

---

# 11. Instrument

```axiom
struct Instrument {
    id: InstrumentId
    security: SecurityRef
    instrument_type: InstrumentType
    currency: Currency
    tick_size: Decimal
    lot_size: Quantity
}
```

---

# 12. Instrument types

```text
Equity
Bond
ETF
FundUnit
Future
Option
Forward
Swap
Warrant
Certificate
StructuredProduct
CommodityContract
FXInstrument
Repo
SecuritiesLoan
```

---

# 13. Security identity

Instrument identity phải ổn định.

Không dùng:

```text
ticker
display_name
```

làm primary identity.

Primary identity:

```text
InstrumentId
SecurityId
VenueInstrumentId
```

---

# 14. Listing

Một security có thể được list tại nhiều venue.

```axiom
struct Listing {
    security: SecurityRef
    venue: VenueRef
    symbol: Symbol
    currency: Currency
    trading_rules: TradingRuleSet
}
```

---

# 15. Symbol

Ticker/symbol chỉ là alias:

```text
Symbol
    ↓
InstrumentIdentity
```

Không được coi symbol là globally unique.

---

# 16. Market calendar

```axiom
struct MarketCalendar {
    timezone: TimeZone
    sessions: SessionSet
    holidays: HolidaySet
}
```

---

# 17. Trading session

```text
PreOpen
Open
Continuous
Auction
PreClose
Close
PostClose
Halted
Closed
```

---

# 18. Session state

```axiom
struct TradingSession {
    id: SessionId
    venue: VenueRef
    state: SessionState
    opens_at: DateTime
    closes_at: DateTime
}
```

---

# 19. Order

```axiom
struct Order {
    id: OrderId
    account: InvestmentAccountRef
    instrument: InstrumentRef
    side: Side
    quantity: Quantity
    order_type: OrderType
    duration: OrderDuration
    constraints: OrderConstraintSet
    authority: OrderAuthority
}
```

---

# 20. Order types

Core:

```text
Market
Limit
Stop
StopLimit
MarketOnClose
LimitOnClose
Pegged
Iceberg
ImmediateOrCancel
FillOrKill
GoodTillCancel
GoodTillDate
```

Advanced types phải nằm ở extension profile nếu venue không hỗ trợ.

---

# 21. Order side

```text
Buy
Sell
ShortSell
BuyToCover
Subscribe
Redeem
Exercise
Assign
```

---

# 22. Order lifecycle

```text
Draft
Submitted
Accepted
Rejected
Working
PartiallyFilled
Filled
Cancelled
Expired
Suspended
Replaced
Done
```

---

# 23. Order state machine

```text
Draft
 ↓
Submitted
 ↓
Accepted
 ↓
Working
 ├── PartiallyFilled
 │       ↓
 │    Working
 │
 ├── Filled
 ├── Cancelled
 ├── Rejected
 └── Expired
```

---

# 24. Order authority

Mỗi order phải có:

```text
principal
actor
capability
mandate
policy_version
timestamp
```

---

# 25. Order Intent

`AXINVEST` tạo:

```axiom
OrderIntent
```

`AXCAPITALMARKET` chuyển thành:

```axiom
Order
```

chỉ sau khi authority/policy được kiểm tra.

---

# 26. Order validation

Trước khi gửi venue:

```text
instrument_valid
quantity_valid
price_valid
session_valid
account_authorized
risk_allowed
capital_available
position_available
shorting_allowed
venue_allowed
```

---

# 27. Pre-trade risk

```axiom
struct PreTradeRiskCheck {
    buying_power
    position_limit
    exposure_limit
    concentration
    leverage
    margin
    short_sale
    restricted_list
}
```

---

# 28. Risk result

```text
Allowed
Rejected
RequiresApproval
RequiresReview
Unknown
```

---

# 29. Buying power

```axiom
struct BuyingPower {
    cash_available: Money
    margin_available: Money
    collateral_available: Money
    total_available: Money
}
```

Không được đồng nhất với net worth.

---

# 30. Order reservation

Khi order được accepted:

```text
AvailableCapital
        ↓
ReservedCapital
```

Nhưng chưa phải settlement.

---

# 31. Reservation lifecycle

```text
Created
Active
PartiallyConsumed
Released
Expired
Cancelled
```

---

# 32. Order replacement

Order replace phải tạo event:

```text
OriginalOrder
    ↓
ReplaceRequest
    ↓
ReplacementOrder
```

Không sửa lịch sử order cũ.

---

# 33. Order event sourcing

```axiom
struct OrderEvent {
    id: EventId
    order: OrderId
    type: OrderEventType
    timestamp: DateTime
    payload: EventPayload
}
```

---

# 34. Order book

```axiom
struct OrderBook {
    instrument: InstrumentRef
    bids: PriceLevelSet
    asks: PriceLevelSet
    sequence: UInt64
    timestamp: DateTime
}
```

---

# 35. Price level

```axiom
struct PriceLevel {
    price: Price
    quantity: Quantity
    order_count: UInt64
}
```

---

# 36. Order priority

Default matching priority:

```text
Price
↓
Time
```

nhưng venue có thể khai báo algorithm khác.

---

# 37. Matching engine

```axiom
interface MatchingEngine {
    submit(order)
    cancel(order)
    replace(order)
    match()
}
```

---

# 38. Matching result

```axiom
struct Match {
    buy_order: OrderId
    sell_order: OrderId
    quantity: Quantity
    price: Price
    timestamp: DateTime
}
```

---

# 39. Trade

```axiom
struct Trade {
    id: TradeId
    venue: VenueRef
    instrument: InstrumentRef
    buyer: ParticipantRef
    seller: ParticipantRef
    quantity: Quantity
    price: Price
    executed_at: DateTime
}
```

---

# 40. Trade ≠ Settlement

Trade chỉ chứng nhận execution.

Settlement xảy ra sau đó theo settlement cycle.

---

# 41. Execution report

```axiom
struct ExecutionReport {
    order: OrderId
    execution: ExecutionId
    filled_quantity: Quantity
    remaining_quantity: Quantity
    price: Price
    fees: FeeSet
}
```

---

# 42. Partial fill

Một order có thể tạo:

```text
Order
 ├── Execution 1
 ├── Execution 2
 ├── Execution 3
 └── ...
```

---

# 43. Average execution price

```axiom
weighted_average_price(
    executions
)
```

không được thay thế các execution records.

---

# 44. Market data

Core categories:

```text
TradeData
QuoteData
OrderBookData
ReferenceData
CorporateActionData
FundamentalData
DerivedData
```

---

# 45. Quote

```axiom
struct Quote {
    instrument: InstrumentRef
    bid: Price?
    bid_size: Quantity?
    ask: Price?
    ask_size: Quantity?
    timestamp: DateTime
}
```

---

# 46. Last trade

```axiom
struct LastTrade {
    price: Price
    quantity: Quantity
    timestamp: DateTime
}
```

Last trade không phải guaranteed current market value.

---

# 47. Market data tick

```axiom
struct MarketTick {
    instrument: InstrumentRef
    event_type: MarketEventType
    sequence: UInt64
    timestamp: DateTime
    payload: MarketPayload
}
```

---

# 48. Sequence integrity

Market stream phải detect:

```text
Gap
Duplicate
OutOfOrder
Reset
LateData
```

---

# 49. Market data stream

```axiom
stream market_ticks(instrument)
```

---

# 50. Replay

Market data phải hỗ trợ:

```axiom
replay(
    instrument,
    time_range,
    sequence_range
)
```

---

# 51. Deterministic replay

Replay cùng:

```text
dataset version
sequence
timestamps
```

phải tạo cùng event stream.

---

# 52. Market data normalization

Provider-specific formats phải chuyển thành:

```text
NativeMarketDataIR
```

---

# 53. Level 1

```text
BestBid
BestAsk
LastTrade
Volume
Timestamp
```

---

# 54. Level 2

```text
BidLevels
AskLevels
Depth
OrderCount
```

---

# 55. Level 3

Nếu provider hỗ trợ:

```text
IndividualOrderEvents
OrderId
Modify
Cancel
Add
Execute
```

---

# 56. Market microstructure

Native analytics:

```text
Spread
MidPrice
Depth
Imbalance
Turnover
Volatility
PriceImpact
Liquidity
```

---

# 57. Mid price

```text
mid = (bid + ask) / 2
```

chỉ khi cả bid và ask tồn tại và hợp lệ.

---

# 58. Spread

```text
spread = ask - bid
```

---

# 59. Market impact

```axiom
struct MarketImpactEstimate {
    expected_price_impact: Rate
    confidence: Probability
    model: ModelRef
}
```

---

# 60. Execution quality

Analytics:

```text
VWAP
TWAP
ImplementationShortfall
ArrivalPrice
Slippage
MarketImpact
```

---

# 61. VWAP

```axiom
vwap(
    executions,
    period
)
```

---

# 62. TWAP

```axiom
twap(
    prices,
    period
)
```

---

# 63. Implementation shortfall

```axiom
implementation_shortfall(
    decision_price,
    executions
)
```

---

# 64. Broker

```axiom
struct Broker {
    id: BrokerId
    legal_entity: EntityRef
    venues: VenueSet
    services: BrokerServiceSet
    permissions: BrokerPermissionSet
}
```

---

# 65. Broker account

```axiom
struct BrokerAccount {
    id: BrokerAccountId
    owner: EntityRef
    broker: BrokerRef
    custody: CustodyAccountRef?
}
```

---

# 66. Broker routing

```axiom
struct RoutingPolicy {
    allowed_venues: VenueSet
    price_policy: PricePolicy
    liquidity_policy: LiquidityPolicy
    cost_policy: CostPolicy
}
```

---

# 67. Smart order routing

```axiom
route order {
    optimize {
        price
        liquidity
        latency
        cost
    }

    subject_to {
        allowed_venues
    }
}
```

Output là routing proposal/order child set.

---

# 68. Routing ≠ Execution

Router chỉ quyết định destination.

Venue matching mới tạo execution.

---

# 69. Dealer

```axiom
struct Dealer {
    entity: EntityRef
    instruments: InstrumentSet
    inventory: InventoryRef
    risk_limits: RiskLimitSet
}
```

---

# 70. Market maker

```axiom
struct MarketMaker {
    participant: ParticipantRef
    quoting_policy: QuotingPolicy
    inventory_limits: InventoryLimitSet
}
```

---

# 71. RFQ

```axiom
struct RFQ {
    requester: ParticipantRef
    instrument: InstrumentRef
    quantity: Quantity
    side: Side
    expiry: DateTime
}
```

---

# 72. Quote response

```axiom
struct RFQQuote {
    rfq: RFQId
    provider: ParticipantRef
    price: Price
    quantity: Quantity
    valid_until: DateTime
}
```

---

# 73. Auction

Supported:

```text
OpeningAuction
ClosingAuction
PeriodicAuction
CallAuction
```

---

# 74. Auction state

```text
Collecting
Locked
Calculated
Published
Executed
Cancelled
```

---

# 75. Auction algorithm

Venue phải khai báo:

```text
price_discovery
tie_break
uncrossing
allocation
```

Không hard-code vào instrument.

---

# 76. Trading halt

```axiom
struct TradingHalt {
    instrument: InstrumentRef
    reason: HaltReason
    started_at: DateTime
    expected_resume: DateTime?
}
```

---

# 77. Circuit breaker

Venue policy có thể định nghĩa:

```text
price_band
volatility_threshold
order_imbalance
market_wide_halt
```

---

# 78. Market state

```text
Normal
Halted
Auction
Closed
Emergency
Degraded
```

---

# 79. Clearing

Sau trade:

```text
Trade
 ↓
Clearing
 ↓
Netting
 ↓
Margin
 ↓
Settlement
```

---

# 80. Clearing member

```axiom
struct ClearingMember {
    id: ClearingMemberId
    participant: ParticipantRef
    ccp: CCPRef
    collateral_account: CollateralAccountRef
}
```

---

# 81. CCP

```axiom
struct CCP {
    id: CCPId
    clearing_rules: ClearingRuleSet
    margin_model: MarginModel
    default_fund: FundRef
}
```

---

# 82. Central counterparty

CCP có thể đứng giữa:

```text
Buyer ↔ CCP ↔ Seller
```

và tạo novation theo market rules.

---

# 83. Cleared trade

```axiom
struct ClearedTrade {
    trade: TradeRef
    clearing_member_buyer: ClearingMemberRef
    clearing_member_seller: ClearingMemberRef
    netting_set: NettingSetRef
    margin: MarginRequirement
}
```

---

# 84. Netting

```axiom
net(
    trades,
    participant,
    settlement_cycle
)
```

---

# 85. Netting invariant

Netting không được làm mất:

```text
gross_trade_history
```

---

# 86. Margin

```text
InitialMargin
VariationMargin
MaintenanceMargin
AdditionalMargin
LiquidityMargin
DefaultMargin
```

---

# 87. Margin requirement

```axiom
struct MarginRequirement {
    initial: Money
    variation: Money
    maintenance: Money
    methodology: MarginMethod
}
```

---

# 88. Variation margin

```axiom
variation_margin(
    position,
    settlement_price
)
```

---

# 89. Collateral

```axiom
struct Collateral {
    asset: AssetRef
    value: Money
    haircut: Rate
    eligible: Bool
}
```

---

# 90. Collateral eligibility

CCP/counterparty policy có thể quy định:

```text
eligible_asset
minimum_rating
currency
maturity
haircut
concentration
```

---

# 91. Haircut

```text
collateral_value =
    market_value × (1 - haircut)
```

---

# 92. Collateral lifecycle

```text
Posted
Valued
Adjusted
Substituted
Released
Liquidated
```

---

# 93. Default management

```axiom
struct DefaultEvent {
    participant: ParticipantRef
    exposure: Money
    collateral: Money
    recovery: Money?
}
```

---

# 94. Default waterfall

CCP phải có configurable:

```text
DefaulterCollateral
Guarantee
DefaultFund
CCPResources
AdditionalAssessment
```

Không hard-code một jurisdiction's rules.

---

# 95. Settlement

```axiom
struct SettlementInstruction {
    trade: TradeRef
    deliver: AssetDelivery
    receive: CashDelivery
    settlement_date: Date
    settlement_system: SettlementSystemRef
}
```

---

# 96. Delivery versus payment

Core settlement mode:

```text
DVP
```

nghĩa là asset delivery và cash payment phải được liên kết theo settlement protocol.

---

# 97. Settlement states

```text
Pending
Matched
Affirmed
Ready
PartiallySettled
Settled
Failed
Cancelled
```

---

# 98. Settlement failure

```text
SettlementFail
```

không được tự động coi là:

```text
Fraud
Default
Crime
```

---

# 99. Settlement retry

```axiom
retry_settlement(
    instruction,
    policy
)
```

---

# 100. Settlement reconciliation

```text
Trade
↕
ClearingRecord
↕
SettlementInstruction
↕
CustodyMovement
↕
CashMovement
```

phải reconcile được.

---

# 101. Custody

```axiom
struct CustodyAccount {
    id: CustodyAccountId
    owner: EntityRef
    custodian: EntityRef
    depository: DepositoryRef?
}
```

---

# 102. Custody position

```axiom
struct CustodyPosition {
    account: CustodyAccountRef
    instrument: InstrumentRef
    quantity: Quantity
    status: CustodyPositionStatus
}
```

---

# 103. Custody states

```text
Available
Pledged
Blocked
Lent
Borrowed
PendingSettlement
Restricted
```

---

# 104. Beneficial ownership

Custody position có thể đại diện cho asset held for:

```text
beneficial_owner
nominee
fund
client
omnibus_account
```

Legal ownership authority nằm ngoài core.

---

# 105. Depository

```axiom
struct Depository {
    id: DepositoryId
    jurisdiction: JurisdictionRef
    securities: SecuritySet
    settlement_system: SettlementSystemRef
}
```

---

# 106. Omnibus custody

Hỗ trợ:

```text
Client
 ↓
Custodian
 ↓
OmnibusAccount
 ↓
Depository
```

---

# 107. Segregated custody

Hỗ trợ:

```text
Client
 ↓
DedicatedCustodyAccount
 ↓
Depository
```

---

# 108. Securities lending

```axiom
struct SecuritiesLoan {
    lender: ParticipantRef
    borrower: ParticipantRef
    instrument: InstrumentRef
    quantity: Quantity
    collateral: Collateral
    fee: Rate
    maturity: DateTime?
}
```

---

# 109. Repo

```axiom
struct Repo {
    seller: ParticipantRef
    buyer: ParticipantRef
    collateral: AssetSet
    cash: Money
    maturity: DateTime
    repo_rate: Rate
}
```

---

# 110. Short selling

Short position phải được biểu diễn riêng:

```axiom
struct ShortPosition {
    instrument: InstrumentRef
    quantity: Quantity
    borrow: SecuritiesLoanRef
}
```

Không được biểu diễn short bằng negative quantity một cách mơ hồ nếu semantics yêu cầu borrow state.

---

# 111. Borrow lifecycle

```text
Requested
Approved
Borrowed
Active
Recalled
Returned
Failed
```

---

# 112. Corporate actions

Market infrastructure phải phát:

```text
Dividend
Split
Merger
Tender
Redemption
Rights
SpinOff
Conversion
Delisting
```

---

# 113. Corporate action processing

```text
Announcement
↓
Eligibility
↓
Entitlement
↓
Processing
↓
Settlement
↓
Reconciliation
```

---

# 114. Entitlement

```axiom
struct CorporateActionEntitlement {
    holder: ParticipantRef
    instrument: InstrumentRef
    quantity: Quantity
    entitlement: EntitlementValue
}
```

---

# 115. Record date

Eligibility phải tính theo:

```text
record_date
```

và settlement/custody policy tương ứng.

---

# 116. Ex-date

Market calendar phải hỗ trợ:

```text
ex_date
record_date
payment_date
```

---

# 117. Delisting

```text
Active
→ DelistingAnnounced
→ Suspended
→ Delisted
```

---

# 118. Instrument lifecycle

```text
Proposed
Issued
Listed
Trading
Suspended
Matured
Redeemed
Delisted
```

---

# 119. Issuer

```axiom
struct Issuer {
    id: EntityRef
    instruments: InstrumentSet
    corporate_actions: CorporateActionSet
}
```

---

# 120. Primary market

Primary issuance phải hỗ trợ:

```text
IPO
BondIssue
RightsIssue
PrivatePlacement
FollowOnOffering
FundLaunch
```

---

# 121. Primary order

```axiom
struct SubscriptionOrder {
    investor: ParticipantRef
    instrument: InstrumentRef
    quantity: Quantity
    price: Price?
}
```

---

# 122. Allocation

Primary offering allocation:

```text
Submitted
Validated
Allocated
PartiallyAllocated
Unallocated
Settled
```

---

# 123. Secondary market

Secondary market bắt đầu từ:

```text
Order
```

và kết thúc tại:

```text
Settlement
```

---

# 124. Market data reference hierarchy

```text
RawProviderData
 ↓
NormalizedMarketData
 ↓
ValidatedMarketData
 ↓
DerivedMarketData
 ↓
Analytics
```

---

# 125. Data quality

Market data validator phải detect:

```text
InvalidPrice
NegativeQuantity
TimestampError
SequenceGap
Duplicate
CrossedBook
LockedBook
Outlier
StaleQuote
```

---

# 126. Locked/crossed book

Venue-specific semantics phải được cấu hình.

Validator không được tự động sửa dữ liệu mà không ghi transformation provenance.

---

# 127. Market data provenance

```axiom
struct MarketDataProvenance {
    provider: ProviderRef
    source_sequence: UInt64
    received_at: DateTime
    transformed_at: DateTime
    schema_version: Version
}
```

---

# 128. Market data normalization

```axiom
normalize_market_data(
    provider_message
)
```

trả:

```text
NativeMarketTick
```

---

# 129. Market data cache

Hỗ trợ:

```text
LatestQuote
OrderBookSnapshot
TradeCache
ReferenceCache
CorporateActionCache
```

---

# 130. Historical market data

Storage phải hỗ trợ:

```text
Tick
Second
Minute
Daily
CorporateActionAdjusted
Raw
```

---

# 131. Adjusted price

Adjusted series phải ghi rõ transformation:

```text
SplitAdjusted
DividendAdjusted
TotalReturnAdjusted
```

Không overwrite raw price.

---

# 132. Market index

```axiom
struct MarketIndex {
    id: IndexId
    methodology: IndexMethodology
    constituents: ConstituentSet
    divisor: Decimal?
}
```

---

# 133. Index calculation

```axiom
calculate_index(
    constituents,
    prices,
    methodology
)
```

---

# 134. Index rebalance

```text
Announcement
↓
EffectiveDate
↓
ConstituentUpdate
```

---

# 135. ETF / index fund interaction

ETF có thể reference:

```text
underlying_index
creation_basket
redemption_basket
```

---

# 136. Creation/redemption

```axiom
struct CreationRedemption {
    fund: FundRef
    participant: AuthorizedParticipantRef
    units: Quantity
    basket: AssetSet
    cash_component: Money?
}
```

---

# 137. Authorized participant

```axiom
struct AuthorizedParticipant {
    entity: EntityRef
    funds: FundSet
    creation_rules: RuleSet
}
```

---

# 138. Market making

Quoting engine:

```axiom
quote(
    inventory,
    market_data,
    risk_limits
)
```

Output:

```text
QuoteProposal
```

---

# 139. Quote proposal ≠ Quote publication

Publication requires venue permission.

---

# 140. Algorithmic trading

Core supports:

```text
VWAP
TWAP
POV
ImplementationShortfall
LiquiditySeeking
SmartRouting
CustomStrategy
```

---

# 141. Algorithmic order

```axiom
struct AlgoOrder {
    parent_order: OrderRef
    algorithm: AlgoStrategy
    parameters: ParameterSet
    limits: ExecutionLimitSet
}
```

---

# 142. Child orders

```text
ParentOrder
 ├── ChildOrder
 ├── ChildOrder
 └── ChildOrder
```

---

# 143. Algo safety

Every algo must have:

```text
max_quantity
max_notional
max_rate
max_slippage
max_runtime
kill_switch
```

---

# 144. Kill switch

```axiom
kill_algo(algo_id)
```

phải có immediate local enforcement.

---

# 145. Fat-finger protection

Pre-trade engine có thể giới hạn:

```text
max_order_size
max_price_deviation
max_notional
max_position_change
```

---

# 146. Market surveillance

Runtime có thể phát hiện signals:

```text
AbnormalVolume
PriceSpike
OrderImbalance
LayeringSignal
SpoofingSignal
WashTradingSignal
MomentumAnomaly
QuoteStuffingSignal
```

---

# 147. Signal ≠ Violation

Mọi surveillance output phải là:

```text
Signal
```

không phải:

```text
ConfirmedViolation
```

trừ khi external authority xác nhận.

---

# 148. Surveillance model

```axiom
struct SurveillanceSignal {
    participant: ParticipantRef?
    instrument: InstrumentRef?
    signal_type: SignalType
    evidence: EvidenceSet
    confidence: Probability
}
```

---

# 149. AI surveillance

AI được phép:

```text
detect
cluster
rank_for_review
summarize
```

nhưng không mặc định:

```text
punish
freeze_account
declare_crime
```

---

# 150. Regulatory reporting boundary

```text
TradeReport
OrderReport
PositionReport
TransactionReport
```

có thể được tạo.

Submission authority nằm ở regulatory connector.

---

# 151. Regulatory connector

```axiom
provider RegulatoryReportingProvider {
    submit(report)
    status(report)
}
```

---

# 152. Market transparency

Market có thể cung cấp:

```text
public_trade
public_quote
public_orderbook
delayed_data
reference_data
```

theo venue policy.

---

# 153. Participant permissions

```text
MarketParticipant
Broker
Dealer
MarketMaker
ClearingMember
Custodian
DataSubscriber
Issuer
Regulator
```

mỗi role có capability riêng.

---

# 154. Capability model

```text
market.read
market.subscribe
order.create
order.cancel
order.replace
trade.read
trade.report
clear.read
clear.submit
margin.read
margin.post
settlement.instruct
custody.read
custody.move
corporate_action.process
surveillance.read
surveillance.review
admin
```

---

# 155. Critical separation

Không suy ra:

```text
order.create
```

từ:

```text
market.read
```

và không suy ra:

```text
custody.move
```

từ:

```text
trade.read
```

---

# 156. Settlement authority

```text
settlement.instruct
```

không tự động cấp:

```text
cash.transfer
```

hoặc:

```text
asset.transfer
```

---

# 157. Settlement bank

```axiom
struct SettlementBank {
    entity: EntityRef
    currency: Currency
    payment_system: PaymentSystemRef
}
```

---

# 158. Payment boundary

Cash leg có thể đi qua:

```text
AXFINANCE
AXBANKING
PaymentSystemProvider
```

`AXCAPITALMARKET` giữ settlement instruction, không sở hữu monetary ledger.

---

# 159. Securities ledger boundary

Security movement có thể đi qua:

```text
Depository
Custodian
SecuritiesLedgerProvider
```

---

# 160. Atomic settlement

Nếu infrastructure hỗ trợ atomic DVP:

```text
AssetDelivery + CashPayment
```

phải commit cùng protocol.

---

# 161. Settlement finality

```axiom
struct SettlementFinality {
    state: FinalityState
    finalized_at: DateTime?
}
```

States:

```text
Pending
Conditional
Final
Reversed
```

---

# 162. Reversal

Settlement đã final không được tùy tiện mutate.

Nếu correction cần:

```text
ReversalEvent
CorrectionEvent
```

theo system rules.

---

# 163. Net settlement

Hỗ trợ:

```text
Gross
Net
ContinuousNet
PeriodicNet
```

---

# 164. Settlement cycle

Settlement cycle là configuration:

```text
T0
T+1
T+2
Custom
```

Không hard-code một cycle vào language core.

---

# 165. Intraday settlement

Infrastructure phải hỗ trợ:

```text
intraday
continuous
real-time
```

nếu provider/venue cho phép.

---

# 166. Failed settlement management

```text
FailDetected
Reasoned
RetryScheduled
PartialResolved
Settled
Escalated
```

---

# 167. Liquidity management

Clearing/settlement phải theo dõi:

```text
CashNeed
CollateralNeed
SettlementObligation
IntradayLiquidity
StressLiquidity
```

---

# 168. Settlement liquidity simulation

```axiom
simulate settlement_liquidity {
    trade_volume
    fail_rate
    collateral_haircut
    market_shock
}
```

---

# 169. CCP systemic simulation

```axiom
simulate clearing_system {
    members
    positions
    collateral
    default_fund
    stress_scenarios
}
```

---

# 170. Default simulation

Simulation output:

```text
exposure
collateral
loss
default_fund_usage
liquidity_gap
```

không phải live CCP action.

---

# 171. Market stress

```axiom
scenario "market_crisis" {
    volatility *= 3
    liquidity *= 0.4
    spreads += 300bp
    default_rate *= 2
}
```

---

# 172. Market digital twin

```axiom
struct MarketTwin {
    observed
    estimated
    predicted
    simulated
}
```

---

# 173. Twin isolation

Digital twin không được mutate:

```text
live_orderbook
live_positions
live_settlement
```

---

# 174. Market replay

Có thể tái tạo:

```text
orderbook
trades
quotes
halts
auctions
```

từ event history.

---

# 175. Historical simulation

```axiom
simulate replay {
    market_data
    orders
    strategy
}
```

---

# 176. Strategy backtest

Backtest phải mô phỏng:

```text
latency
fees
spread
slippage
market impact
partial fills
rejections
halts
```

khi model yêu cầu realism.

---

# 177. No perfect fills

Backtest engine không được mặc định giả định:

```text
100% fill at last price
```

nếu execution model yêu cầu order-book realism.

---

# 178. Latency model

```axiom
struct LatencyModel {
    network
    broker
    venue
    matching
    market_data
}
```

---

# 179. Market impact model

```axiom
struct ImpactModel {
    temporary
    permanent
    liquidity
    participation_rate
}
```

---

# 180. Transaction costs

```text
Commission
ExchangeFee
ClearingFee
SettlementFee
BorrowFee
TaxRef
Spread
Slippage
Impact
```

---

# 181. Cost provenance

Mọi fee phải có:

```text
source
rule
effective_date
currency
```

---

# 182. Market AI

AI services:

```text
MarketResearch
ExecutionAnalysis
LiquidityForecast
AnomalyDetection
MarketSimulation
SurveillanceAssist
RoutingOptimization
SettlementPrediction
```

---

# 183. AI execution assistant

```axiom
agent ExecutionAssistant {
    tools [
        market.read,
        order.read,
        liquidity.read,
        execution.analyze
    ]

    authority [
        proposal.write
    ]
}
```

---

# 184. AI execution agent

Nếu được cấp execution authority:

```text
order.create
order.cancel
order.replace
```

vẫn phải chịu:

```text
risk limits
rate limits
kill switch
audit
```

---

# 185. Autonomous trading boundary

AI không được tự suy ra:

```text
capital.transfer
```

từ:

```text
order.create
```

---

# 186. AI market maker

Có thể có:

```axiom
agent MarketMakerAI {
    state inventory
    risk_limits
    quote_policy
}
```

---

# 187. Quote safety

AI market maker phải có:

```text
max_inventory
max_quote_size
max_spread
max_loss
kill_switch
```

---

# 188. AI model provenance

Mọi AI-generated order proposal:

```text
model_id
model_version
input_snapshot
policy_version
reasoning_artifact_ref
timestamp
```

phải được lưu.

---

# 189. Reasoning privacy

Không bắt buộc lưu chain-of-thought.

Chỉ cần lưu:

```text
decision_summary
evidence
inputs
model
policy
output
```

---

# 190. Market prediction

Model có thể tạo:

```text
PriceForecast
VolatilityForecast
LiquidityForecast
VolumeForecast
```

Nhưng mọi forecast phải mang:

```text
Forecast
```

type riêng.

---

# 191. Forecast ≠ Quote

Không được sử dụng forecast làm live quote mà không qua policy/strategy layer.

---

# 192. Market manipulation boundary

Runtime có thể phát hiện:

```text
ManipulationSignal
```

nhưng legal determination thuộc authority thích hợp.

---

# 193. Restricted instrument

```axiom
struct TradingRestriction {
    instrument: InstrumentRef
    participant: ParticipantRef?
    action: Action
    reason: RestrictionReason
    expires_at: DateTime?
}
```

---

# 194. Restricted list

```text
Restricted
Watch
Prohibited
ReviewRequired
```

---

# 195. Position limits

```axiom
limit position(instrument) <= 10%
limit notional(account) <= X
```

---

# 196. Market-wide limits

Venue có thể đặt:

```text
max_order_size
price_band
position_limit
message_rate
```

---

# 197. Rate limiting

Trading API phải có:

```text
orders_per_second
cancels_per_second
messages_per_second
burst_limit
```

---

# 198. Message integrity

Market protocol phải hỗ trợ:

```text
sequence
checksum
timestamp
signature
session_id
```

khi provider yêu cầu.

---

# 199. Session management

```text
Disconnected
Connecting
Authenticated
Established
Degraded
Recovering
Closed
```

---

# 200. Session recovery

Sau disconnect:

```text
Reconnect
Authenticate
Resynchronize
ReplayGap
ValidateState
Resume
```

---

# 201. Order state recovery

Không được giả định order state từ local cache sau reconnect.

Phải reconcile với venue authoritative source.

---

# 202. Drop copy

Hỗ trợ execution feeds độc lập:

```text
PrimarySession
DropCopySession
```

để reconciliation.

---

# 203. Market data recovery

```text
Snapshot
+
IncrementalUpdates
```

để reconstruct order book.

---

# 204. Snapshot sequence

Snapshot phải có:

```text
sequence_start
sequence_end
timestamp
```

---

# 205. Sequence gap handling

Nếu:

```text
expected_sequence != received_sequence
```

thì stream phải chuyển:

```text
Degraded
```

và yêu cầu recovery.

---

# 206. FIX-like protocol boundary

Protocol adapters có thể hỗ trợ:

```text
FIX
ITCH
OUCH
FAST
WebSocket
BinaryCustom
```

nhưng core semantics không phụ thuộc protocol.

---

# 207. Protocol adapter

```axiom
interface MarketProtocolAdapter {
    encode(message)
    decode(bytes)
}
```

---

# 208. Zero-copy market feed

Binary feed có thể decode bằng:

```text
borrowed byte slice
```

và map trực tiếp vào native structures khi alignment/schema cho phép.

Không bắt buộc heap allocation cho mỗi tick.

---

# 209. Memory architecture

Hot path:

```text
NIC
 ↓
RingBuffer
 ↓
Parser
 ↓
NormalizedEvent
 ↓
OrderBook
 ↓
Strategy
```

---

# 210. Lock-free path

High-frequency profile phải hỗ trợ:

```text
SPSC
MPSC
MPMC
lock-free ring buffer
atomic sequence
```

dùng concurrency primitives từ Axiom core runtime.

---

# 211. Deterministic matching

Matching engine phải deterministic với:

```text
same input event sequence
same venue rules
same initial state
```

---

# 212. Matching engine test

Golden tests phải kiểm tra:

```text
price priority
time priority
partial fill
cancel
replace
auction
halt
resume
```

---

# 213. Exchange failover

Venue infrastructure phải hỗ trợ:

```text
Primary
Secondary
Recovery
ReadOnly
Emergency
```

---

# 214. Disaster recovery

Market infrastructure phải hỗ trợ:

```text
event log
snapshot
sequence recovery
state reconstruction
cross-region replication
```

---

# 215. Market clock

Không dùng local wall-clock đơn thuần cho ordering.

Hỗ trợ:

```text
exchange_timestamp
gateway_timestamp
receive_timestamp
processing_timestamp
```

---

# 216. Clock synchronization

Runtime phải hỗ trợ clock source abstraction.

Không giả định mọi timestamp giữa participants là perfectly synchronized.

---

# 217. Time priority

Order priority dùng venue-defined timestamp/sequence.

Không dùng client timestamp nếu venue không quy định.

---

# 218. Reference data

```text
InstrumentMaster
IssuerMaster
VenueMaster
CurrencyMaster
CalendarMaster
ParticipantMaster
```

---

# 219. Reference-data versioning

Mọi reference record phải có:

```text
effective_from
effective_to
version
source
```

---

# 220. Security master

```axiom
struct SecurityMaster {
    security
    issuer
    identifiers
    listings
    terms
    corporate_actions
}
```

---

# 221. Identifier mapping

Hỗ trợ nhiều identifiers:

```text
NativeSecurityId
ISINRef
CUSIPRef
SEDOLRef
TickerRef
VendorSymbolRef
```

Vendor identifiers là references, không phải native identity.

---

# 222. Instrument terms

Derivative/instrument terms phải có typed structure:

```text
underlying
strike
maturity
settlement
multiplier
exercise
currency
```

---

# 223. Options

```axiom
struct OptionContract {
    underlying: InstrumentRef
    strike: Price
    expiry: DateTime
    style: OptionStyle
    side: OptionSide
    multiplier: Quantity
}
```

---

# 224. Futures

```axiom
struct FutureContract {
    underlying: AssetRef
    expiry: DateTime
    contract_size: Quantity
    tick_value: Money
}
```

---

# 225. Derivative lifecycle

```text
Listed
Open
Trading
Expired
Exercised
Settled
```

---

# 226. Option exercise

```text
ExerciseIntent
 ↓
ExerciseValidation
 ↓
Exercise
 ↓
Settlement
```

---

# 227. Physical vs cash settlement

```text
PhysicalDelivery
CashSettlement
```

phải là explicit.

---

# 228. Derivative margin

Derivative clearing có thể reference:

```text
InitialMargin
VariationMargin
Collateral
Liquidation
```

---

# 229. OTC derivatives

OTC contracts phải hỗ trợ:

```text
bilateral
CSA
collateral
valuation
netting
termination
```

---

# 230. Trade confirmation

```axiom
struct TradeConfirmation {
    trade: TradeRef
    parties: EntitySet
    terms: TradeTerms
    confirmed_at: DateTime
}
```

---

# 231. Affirmation

Settlement readiness có thể yêu cầu:

```text
BuyerAffirmed
SellerAffirmed
CustodianAffirmed
```

---

# 232. Matching settlement instructions

```axiom
match_settlement_instructions(
    buyer_instruction,
    seller_instruction
)
```

---

# 233. Settlement mismatch

Detect:

```text
quantity
price
currency
date
account
instrument
```

mismatch.

---

# 234. Cash reconciliation

```text
ExpectedCash
ActualCash
Difference
```

---

# 235. Asset reconciliation

```text
ExpectedPosition
CustodyPosition
Difference
```

---

# 236. Three-way reconciliation

```text
Trade
+
Settlement
+
Custody
```

phải reconcile.

---

# 237. Four-way reconciliation

Institutional profile có thể thêm:

```text
Ledger
```

→:

```text
Trade
Settlement
Custody
Ledger
```

---

# 238. Corporate action reconciliation

Expected entitlement phải reconcile với:

```text
Custody
Cash
SecurityPosition
```

---

# 239. Securities lending reconciliation

Theo dõi:

```text
LoanOutstanding
Collateral
Fees
Returns
Recall
```

---

# 240. Market risk aggregation

`AXCAPITALMARKET` có thể export:

```text
Delta
Gamma
Vega
DV01
CS01
Exposure
```

sang `AXINVEST`.

---

# 241. Greeks

Derivative analytics:

```text
Delta
Gamma
Theta
Vega
Rho
```

---

# 242. Greeks provenance

Mỗi Greek phải ghi:

```text
pricing_model
market_data
timestamp
parameters
```

---

# 243. Pricing engine

```axiom
interface PricingEngine {
    price(instrument, market_state)
    sensitivities(instrument, market_state)
}
```

---

# 244. Pricing models

Có thể hỗ trợ:

```text
BlackScholes
BinomialTree
MonteCarlo
DiscountedCashFlow
YieldCurve
Custom
```

---

# 245. Pricing ≠ Settlement Price

Model price và actual transaction price phải là distinct values.

---

# 246. Fair-value boundary

Fair value calculation có thể được cung cấp cho:

```text
AXINVEST
AXFINANCE
```

nhưng accounting policy quyết định cách sử dụng.

---

# 247. Yield curve

```axiom
struct YieldCurve {
    currency: Currency
    observations: PointSet
    timestamp: DateTime
    methodology: CurveMethod
}
```

---

# 248. Curve interpolation

```text
Linear
Spline
NelsonSiegel
Svensson
Custom
```

---

# 249. Curve bootstrapping

```axiom
bootstrap_curve(
    instruments,
    methodology
)
```

---

# 250. Market risk scenario

```axiom
scenario "rate_shock" {
    yield_curve.shift(+100bp)
}
```

---

# 251. Liquidity risk

Market infrastructure phải đo:

```text
bid_ask
depth
turnover
market_impact
time_to_liquidate
```

---

# 252. Time-to-liquidate

```axiom
time_to_liquidate(
    position,
    participation_rate
)
```

---

# 253. Market capacity

```axiom
struct MarketCapacity {
    average_volume
    stressed_volume
    estimated_capacity
    confidence
}
```

---

# 254. Capacity ≠ Liquidity

Capacity là model estimate.

Liquidity là market state.

---

# 255. Market stress propagation

```text
Market Shock
 ↓
Order Flow
 ↓
Liquidity
 ↓
Price Impact
 ↓
Margin
 ↓
Forced Selling
 ↓
Further Liquidity Shock
```

---

# 256. Systemic simulation

```axiom
simulate financial_market {
    participants
    orderbooks
    clearing
    collateral
    settlement
    stress
}
```

---

# 257. Agent-based market simulation

Participants có thể là:

```text
RetailInvestor
Institution
MarketMaker
Broker
Bank
Fund
CCP
Custodian
AITrader
```

---

# 258. Agent authority in simulation

Simulation agents không được truy cập production credentials.

---

# 259. Market digital twin

```text
Observed
Estimated
Forecast
Simulated
```

phải tách bằng tagged state.

---

# 260. Civilization-scale market model

```text
Households
   ↓
Funds
   ↓
Banks
   ↓
Corporations
   ↓
Markets
   ↓
CCPs
   ↓
Custodians
   ↓
Settlement Systems
```

có thể được mô phỏng trong `AX648`.

---

# 261. Market topology

Graph entities:

```text
Participant
Venue
Broker
CCP
Custodian
Depository
SettlementBank
```

Edges:

```text
connects
clears
settles
custodies
routes
trades
exposes
```

---

# 262. Counterparty graph

```axiom
counterparty_exposure(
    participant
)
```

---

# 263. Concentration

Market infrastructure phải hỗ trợ:

```text
venue_concentration
broker_concentration
counterparty_concentration
clearing_member_concentration
custodian_concentration
```

---

# 264. Operational resilience

Critical infrastructure phải có:

```text
redundancy
failover
recovery
health
capacity
incident_state
```

---

# 265. Health state

```text
Healthy
Degraded
Recovering
Unavailable
ReadOnly
Emergency
```

---

# 266. Dependency health

Market service phải biết:

```text
market_data
broker
venue
clearing
settlement
custody
clock
```

dependencies health.

---

# 267. Circuit breaker

System-level circuit breaker có thể:

```text
stop_new_orders
cancel_only
read_only
emergency_mode
```

---

# 268. Emergency mode

Emergency mode không tự động liquidate positions.

---

# 269. Observability

Metrics:

```text
order_latency
execution_latency
market_data_latency
sequence_gap
reject_rate
fill_rate
cancel_rate
settlement_fail_rate
reconciliation_breaks
margin_usage
```

---

# 270. Distributed tracing

Một order phải trace được:

```text
Client
→ Gateway
→ Broker
→ Venue
→ Matching
→ Trade
→ Clearing
→ Settlement
→ Custody
```

---

# 271. Event correlation

Mọi event phải có:

```text
correlation_id
causation_id
```

---

# 272. Idempotency

Critical commands phải hỗ trợ:

```text
idempotency_key
```

để retry không tạo duplicate order/trade/settlement instruction.

---

# 273. Exactly-once boundary

Không giả định distributed network luôn exactly-once.

Runtime phải dùng:

```text
idempotency
deduplication
sequence
reconciliation
```

---

# 274. Event ordering

Ordering chỉ có ý nghĩa trong scope:

```text
venue
session
instrument
order
settlement_chain
```

Không giả định global ordering.

---

# 275. Distributed consistency

Market state có thể dùng:

```text
strong consistency
sequence consistency
eventual consistency
```

tùy subsystem.

---

# 276. Matching engine consistency

Matching engine phải có deterministic ordered event stream.

---

# 277. Settlement consistency

Settlement phải có transaction/finality semantics.

---

# 278. Market data consistency

Market data consumers phải chấp nhận:

```text
late
duplicate
missing
replayed
```

và recovery.

---

# 279. API

```axiom
module axcapitalmarket

fn submit(order)
fn cancel(order)
fn replace(order)
fn quote(instrument)
fn orderbook(instrument)
fn trades(instrument)
fn clear(trade)
fn settle(instruction)
fn reconcile(account)
```

---

# 280. Streaming API

```axiom
stream quotes(instrument)
stream trades(instrument)
stream order_events(order)
stream settlement_events(account)
```

---

# 281. Query API

```text
market.find
instrument.find
order.get
trade.get
position.get
settlement.get
```

---

# 282. CLI

```text
axiom market list
axiom market instruments
axiom market quote
axiom market book
axiom market trades
axiom market order submit
axiom market order cancel
axiom market order status
axiom market reconcile
axiom market settlement
axiom market surveillance
```

---

# 283. Simulation CLI

```text
axiom market replay
axiom market backtest
axiom market simulate
axiom market stress
```

---

# 284. Native IR

Compiler IR phải có:

```text
MarketIR
VenueIR
InstrumentIR
OrderIR
OrderBookIR
ExecutionIR
TradeIR
ClearingIR
MarginIR
CollateralIR
SettlementIR
CustodyIR
MarketDataIR
CorporateActionIR
SurveillanceIR
MarketSimulationIR
```

---

# 285. Order IR

```text
ORDER
  ACCOUNT
  INSTRUMENT
  SIDE
  QUANTITY
  TYPE
  PRICE?
  DURATION
  CONSTRAINTS
  AUTHORITY
```

---

# 286. Trade IR

```text
TRADE
  VENUE
  INSTRUMENT
  BUYER
  SELLER
  QUANTITY
  PRICE
  TIMESTAMP
```

---

# 287. Settlement IR

```text
SETTLEMENT
  TRADE
  ASSET_LEG
  CASH_LEG
  DATE
  SYSTEM
  FINALITY
```

---

# 288. MarketData IR

```text
MARKET_EVENT
  INSTRUMENT
  SEQUENCE
  TIMESTAMP
  TYPE
  PAYLOAD
```

---

# 289. Compiler validation

Compiler/runtime phải phát hiện:

```text
invalid instrument
invalid venue
invalid session
unauthorized order
invalid price tick
invalid quantity lot
insufficient buying power
position limit breach
restricted instrument
invalid settlement
duplicate command
sequence gap
```

---

# 290. Error model

```axiom
enum CapitalMarketError {
    InvalidInstrument
    VenueUnavailable
    MarketClosed
    TradingHalted
    InvalidOrder
    AuthorizationDenied
    RiskLimitExceeded
    PositionLimitExceeded
    InsufficientBuyingPower
    InsufficientCollateral
    OrderRejected
    OrderExpired
    SequenceGap
    MarketDataStale
    MatchingFailure
    ClearingFailure
    MarginFailure
    SettlementFailure
    CustodyMismatch
    ReconciliationMismatch
    CorporateActionError
    ProviderUnavailable
}
```

---

# 291. Numeric model

Financial values sử dụng:

```text
Money
Price
Quantity
Rate
Ratio
Decimal
FixedPoint
```

không implicit cast sang `f32`.

---

# 292. Price precision

Instrument phải định nghĩa:

```text
tick_size
price_precision
quantity_precision
lot_size
```

---

# 293. Quantity validation

Order quantity phải thỏa:

```text
quantity % lot_size == 0
```

nếu venue yêu cầu.

---

# 294. Tick validation

Limit price phải phù hợp tick rule.

---

# 295. Fee engine

```axiom
calculate_fee(
    trade,
    venue,
    participant
)
```

---

# 296. Fee model

```text
Commission
TieredFee
VolumeFee
MakerFee
TakerFee
ClearingFee
SettlementFee
CustodyFee
BorrowFee
```

---

# 297. Maker/taker

Trade có thể chứa:

```text
maker
taker
```

nếu venue cung cấp semantics.

---

# 298. Market participant registry

```axiom
struct Participant {
    id: ParticipantId
    entity: EntityRef
    participant_type: ParticipantType
    permissions: CapabilitySet
}
```

---

# 299. KYC/identity boundary

Identity verification tham chiếu:

```text
AX627
AXLAW
```

không duplicate identity system.

---

# 300. Account hierarchy

```text
Entity
 ↓
InvestmentAccount
 ↓
BrokerAccount
 ↓
TradingAccount
 ↓
CustodyAccount
```

Các account này không được đồng nhất.

---

# 301. Omnibus allocation

Một omnibus execution có thể allocate cho nhiều clients:

```text
Execution
 ↓
Allocation
 ├── Client A
 ├── Client B
 └── Client C
```

---

# 302. Allocation model

```axiom
struct TradeAllocation {
    trade: TradeRef
    account: InvestmentAccountRef
    quantity: Quantity
    price: Price
}
```

---

# 303. Allocation policy

```text
ProRata
AveragePrice
SpecificAllocation
Custom
```

---

# 304. Average-price allocation

Các client allocations phải giữ:

```text
total_allocated <= executed_quantity
```

---

# 305. Partial allocation

Nếu:

```text
executed_quantity < requested_quantity
```

allocation phải phản ánh partial fill.

---

# 306. Settlement allocation

Trade-level settlement có thể phân rã xuống:

```text
client settlement instructions
```

---

# 307. Block trade

```axiom
struct BlockTrade {
    instrument
    quantity
    price
    participants
    execution_method
}
```

---

# 308. OTC trade

OTC trade không cần order book.

```text
RFQ
Negotiation
Agreement
Confirmation
Clearing
Settlement
```

---

# 309. Negotiation state

```text
Proposed
Countered
Accepted
Rejected
Expired
Cancelled
```

---

# 310. Trade affirmation

Hai bên phải có thể xác nhận:

```text
instrument
quantity
price
currency
date
counterparty
```

---

# 311. Market data entitlement

Data access có thể phân quyền:

```text
RealTime
Delayed
Historical
Depth
Trades
Reference
Derived
```

---

# 312. Data licensing

Provider metadata phải giữ:

```text
license
usage_policy
expiry
redistribution_allowed
```

---

# 313. Data leakage prevention

Runtime không được export licensed market data nếu policy cấm.

---

# 314. AI training boundary

Market data không mặc định được đưa vào model training.

Phải có:

```text
dataset_policy
license
retention
provenance
```

---

# 315. AI market-data access

Agent capability:

```text
market.read
market.historical.read
market.realtime.read
market.depth.read
```

được tách riêng.

---

# 316. High-frequency profile

`AXCAPITALMARKET_HFT` có:

```text
zero-copy
lock-free
preallocated
SIMD
kernel-bypass provider boundary
busy-poll optional
deterministic matching
```

---

# 317. Low-latency memory

Hot objects phải tránh:

```text
virtual dispatch
unbounded allocation
GC pauses
```

---

# 318. Standard profile

Không phải application nào cũng cần HFT.

`AXCAPITALMARKET_CORE` phải hoạt động với:

```text
ordinary threads
async I/O
normal network stack
```

---

# 319. Mobile/WASM

Trading execution capability phải mặc định disabled trong untrusted WASM/mobile sandbox.

Analytics và market-data consumption vẫn có thể enabled.

---

# 320. Security

Critical secrets:

```text
broker credentials
exchange credentials
signing keys
FIX session secrets
custody credentials
```

phải dùng secure secret boundary.

---

# 321. Message signing

Nếu venue yêu cầu:

```axiom
sign(message, key)
verify(message, key)
```

key material không expose vào application memory nếu provider hỗ trợ secure enclave/HSM.

---

# 322. HSM boundary

```axiom
provider SecureKeyProvider {
    sign(...)
    decrypt(...)
}
```

---

# 323. HSM không bắt buộc

Core semantics không phụ thuộc HSM.

---

# 324. Audit

Critical events:

```text
OrderSubmitted
OrderAccepted
OrderRejected
OrderCancelled
OrderReplaced
ExecutionReceived
TradeCreated
TradeCleared
MarginChanged
SettlementSubmitted
SettlementCompleted
CustodyMoved
CorporateActionApplied
```

đều phải audit.

---

# 325. Audit immutability

```text
append-only
hash-linked
timestamped
actor-bound
```

---

# 326. Explainability

AI-generated market actions phải truy được:

```text
input
model
policy
risk check
decision
order
execution
```

---

# 327. Kill-switch audit

Mọi kill switch phải ghi:

```text
actor
reason
scope
timestamp
affected orders
result
```

---

# 328. Market-wide emergency

System có thể hỗ trợ:

```text
CancelAll
CancelByInstrument
CancelByParticipant
CancelByStrategy
CancelByVenue
```

Nhưng đây là privileged capabilities.

---

# 329. Cancel-on-disconnect

Venue/account policy có thể cấu hình:

```text
CancelAll
KeepOrders
CancelSessionOrders
```

---

# 330. Heartbeat

Trading session phải có:

```text
heartbeat
timeout
disconnect
reconnect
```

---

# 331. Health watchdog

```axiom
watch trading_session {
    heartbeat
    latency
    sequence
    errors
}
```

---

# 332. Performance target

Core market runtime phải hướng tới:

```text
low allocation
predictable latency
high throughput
deterministic event processing
horizontal scalability
```

---

# 333. Throughput architecture

Có thể partition theo:

```text
venue
instrument
market
asset_class
```

---

# 334. Single-writer principle

Một order book partition nên có single logical writer để giảm locking.

---

# 335. Parallel market

Các instrument độc lập có thể chạy song song.

Không giả định toàn market cần một global lock.

---

# 336. Distributed matching

Distributed matching chỉ được dùng khi venue semantics cho phép.

Không tự ý thay đổi ordering guarantees.

---

# 337. Persistence

Market infrastructure cần:

```text
event log
snapshot
journal
checkpoint
recovery log
```

---

# 338. Storage tiers

```text
Hot
Warm
Cold
Archive
```

---

# 339. Historical archive

Raw market data có thể rất lớn.

Storage phải hỗ trợ:

```text
columnar
compressed
partitioned
time-indexed
content-addressed
```

---

# 340. Compression

Market-data archive nên hỗ trợ:

```text
delta encoding
timestamp compression
dictionary encoding
columnar compression
```

---

# 341. Query engine

```axiom
query trades
where instrument == BTC
and timestamp between t1 and t2
```

Nếu asset không phải crypto thì ví dụ tương ứng.

---

# 342. Market analytics query

```axiom
query orderbook
where instrument == X
at timestamp T
```

---

# 343. Streaming query

```axiom
stream trades
where instrument in universe
```

---

# 344. Event-time window

```axiom
window trades
by 1s
```

---

# 345. Market surveillance window

```axiom
detect anomalies
over 5m
group_by participant
```

---

# 346. Graph integration

Counterparty and ownership analysis có thể dùng:

```text
AX645
```

---

# 347. AI integration

AI runtime có thể dùng:

```text
AX643
AX644
AX645
AX646
AX647
AX648
```

---

# 348. Investment integration

```text
AXINVEST
    ↓
OrderIntent
    ↓
AXCAPITALMARKET
    ↓
Trade
    ↓
Settlement
    ↓
AXFINANCE
```

---

# 349. Banking integration

Cash settlement:

```text
AXCAPITALMARKET
      ↓
AXBANKING
      ↓
AXFINANCE
```

---

# 350. Insurance integration

Insurance portfolios:

```text
AXINSURANCE
      ↓
AXINVEST
      ↓
AXCAPITALMARKET
```

---

# 351. Government integration

Public securities may reference:

```text
AXGOV
```

nhưng government authority vẫn ở `AXGOV`.

---

# 352. Legal integration

Security terms, ownership, restrictions:

```text
AXLAW
```

---

# 353. Civilization market graph

```text
HOUSEHOLDS
    ↓
BROKERS
    ↓
EXCHANGES
    ↓
CLEARING
    ↓
SETTLEMENT
    ↓
CUSTODY
    ↓
FINANCIAL ASSETS
    ↓
ENTERPRISES
```

---

# 354. Civilization-scale simulation

Có thể mô phỏng:

```text
participants
markets
order flows
liquidity
clearing
collateral
settlement
capital flows
```

---

# 355. Market shock propagation

```text
Shock
 ↓
Price
 ↓
Volatility
 ↓
Margin
 ↓
Liquidation
 ↓
Liquidity
 ↓
Clearing
 ↓
Settlement
```

---

# 356. Contagion

Simulation có thể mô hình hóa:

```text
participant_default
counterparty_exposure
collateral_loss
forced_liquidation
market_impact
```

---

# 357. No live side effects in simulation

Simulation profile phải không có:

```text
order.create.live
capital.transfer
custody.move.live
```

---

# 358. Simulation capability

```text
market.simulate
market.replay
market.backtest
```

độc lập với:

```text
market.execute
```

---

# 359. Profiles

```text
AXCAPITALMARKET_NONE
AXCAPITALMARKET_CORE
AXCAPITALMARKET_ORDER
AXCAPITALMARKET_EXECUTION
AXCAPITALMARKET_EXCHANGE
AXCAPITALMARKET_BROKER
AXCAPITALMARKET_MARKETDATA
AXCAPITALMARKET_CLEARING
AXCAPITALMARKET_MARGIN
AXCAPITALMARKET_SETTLEMENT
AXCAPITALMARKET_CUSTODY
AXCAPITALMARKET_DERIVATIVE
AXCAPITALMARKET_SURVEILLANCE
AXCAPITALMARKET_SIMULATION
AXCAPITALMARKET_AI
AXCAPITALMARKET_HFT
AXCAPITALMARKET_DISTRIBUTED
AXCAPITALMARKET_GPU
AXCAPITALMARKET_WASM
AXCAPITALMARKET_MOBILE
AXCAPITALMARKET_FULL
```

---

# 360. Minimal profile

`AXCAPITALMARKET_CORE` chỉ gồm:

```text
Instrument
Market
Venue
Order
Execution
Trade
Event
```

Không kéo:

```text
CCP
Custody
AI
GPU
Surveillance
```

nếu không dùng.

---

# 361. Native modules

```text
axiom-capital-core
axiom-market
axiom-instrument
axiom-order
axiom-orderbook
axiom-matching
axiom-broker
axiom-execution
axiom-marketdata
axiom-clearing
axiom-margin
axiom-collateral
axiom-settlement
axiom-custody
axiom-corporate-actions
axiom-derivatives
axiom-surveillance
axiom-market-ai
axiom-market-simulation
axiom-market-replay
```

---

# 362. Dead stripping

Binary chỉ dùng:

```text
marketdata
```

không được link:

```text
matching
clearing
custody
AI
```

---

# 363. Native ABI

Stable interfaces:

```text
OrderABI
TradeABI
MarketDataABI
SettlementABI
CustodyABI
```

---

# 364. Protocol ABI

Provider adapters compile thành:

```text
NativeProviderABI
```

---

# 365. Plugin isolation

External venue adapter không được truy cập arbitrary memory của core runtime.

---

# 366. Provider crash isolation

Provider failure không được làm corrupt:

```text
live order state
trade history
settlement journal
```

---

# 367. Fault containment

Các boundary:

```text
MarketData
Broker
Venue
Clearing
Settlement
Custody
```

phải có failure isolation.

---

# 368. Backpressure

Market data consumer chậm phải xử lý:

```text
buffer
drop_policy
snapshot_recovery
slow_consumer
```

Không silently lose critical trading events.

---

# 369. Critical event durability

Order/trade/settlement events phải có durability policy rõ ràng.

---

# 370. Exactly-once command safety

Critical command dùng:

```text
command_id
idempotency_key
dedupe_store
```

---

# 371. Reconciliation as safety net

Ngay cả khi hệ thống tuyên bố exactly-once, reconciliation vẫn là mandatory architecture component.

---

# 372. Test target

`AXCAPITALMARKET 5.0` yêu cầu tối thiểu:

```text
22,000 automated tests
1,900 architecture invariants
```

---

# 373. Test categories

```text
Order
OrderBook
Matching
Auction
Broker
Routing
MarketData
Replay
Clearing
Margin
Collateral
Settlement
Custody
CorporateActions
Derivatives
Surveillance
AI
Security
Recovery
Distributed
Performance
GPU
WASM
```

---

# 374. Golden matching tests

Bắt buộc kiểm thử:

```text
price-time priority
partial fills
cancel
replace
auction
halts
resume
duplicate messages
out-of-order messages
sequence gaps
```

---

# 375. Settlement golden tests

Phải kiểm tra:

```text
DVP
partial settlement
failed settlement
retry
reconciliation
finality
reversal
```

---

# 376. Corporate action tests

```text
split
dividend
merger
rights
redemption
delisting
```

---

# 377. Security tests

```text
unauthorized order
privilege escalation
cross-account access
cross-tenant access
fake execution
duplicate settlement
audit tampering
credential leakage
```

---

# 378. Simulation tests

Simulation phải chứng minh:

```text
no live mutation
deterministic replay
state isolation
seed reproducibility
```

---

# 379. Performance tests

Benchmarks:

```text
orders/sec
market-events/sec
matching latency
market-data latency
recovery latency
settlement throughput
reconciliation throughput
```

---

# 380. Recovery tests

Test:

```text
venue disconnect
broker disconnect
market-data gap
process crash
machine failure
network partition
duplicate command
partial persistence
```

---

# 381. Numerical tests

Pricing và risk algorithms phải có reference datasets.

---

# 382. CPU/GPU equivalence

GPU result phải nằm trong tolerance so với trusted CPU implementation.

---

# 383. Final architecture contract

`AXCAPITALMARKET` phải tạo được một native chain hoàn chỉnh:

```text
INVESTMENT DECISION
        ↓
ORDER INTENT
        ↓
ORDER
        ↓
ROUTING
        ↓
EXECUTION
        ↓
TRADE
        ↓
CLEARING
        ↓
MARGIN / COLLATERAL
        ↓
SETTLEMENT
        ↓
CUSTODY
        ↓
POSITION
        ↓
RECONCILIATION
        ↓
AXINVEST
```

---

# 384. Market-data chain

```text
RAW PROVIDER
     ↓
NORMALIZATION
     ↓
VALIDATION
     ↓
ORDER BOOK
     ↓
MARKET STATE
     ↓
ANALYTICS
     ↓
AI / INVESTMENT
```

---

# 385. Capital-market safety chain

```text
INTENT
 ↓
AUTHORITY
 ↓
RISK
 ↓
POLICY
 ↓
ORDER
 ↓
EXECUTION
 ↓
CLEARING
 ↓
SETTLEMENT
 ↓
AUDIT
```

Không được bỏ qua authority hoặc risk gate chỉ vì AI agent đang chạy tự động.

---

# 386. Civilization-scale financial chain

```text
HOUSEHOLD SAVINGS
       ↓
BANKING
       ↓
INVESTMENT
       ↓
CAPITAL MARKETS
       ↓
CAPITAL ALLOCATION
       ↓
ENTERPRISES
       ↓
PRODUCTION
       ↓
INCOME
       ↓
SAVINGS
```

---

# 387. Final semantic boundary

Axiom phải luôn giữ:

```text
Market observation
        ≠
Model prediction

Prediction
        ≠
Investment recommendation

Recommendation
        ≠
Order

Order
        ≠
Execution

Execution
        ≠
Settlement

Settlement
        ≠
Ownership authority
```

Đây là invariant nền tảng của `AXCAPITALMARKET`.

---

# 388. Task completion

**BOOTSTRAP-693 — COMPLETE**

Kiến trúc hiện tại:

```text
AXFINANCE
    ↓
AXBANKING
    ↓
AXINSURANCE
    ↓
AXINVEST
    ↓
AXCAPITALMARKET
    ├── Market
    ├── Exchange
    ├── Broker
    ├── Order
    ├── OrderBook
    ├── Matching
    ├── Execution
    ├── Trade
    ├── MarketData
    ├── Clearing
    ├── Margin
    ├── Collateral
    ├── Settlement
    ├── Custody
    ├── Depository
    ├── CorporateActions
    ├── SecuritiesLending
    ├── Repo
    ├── Derivatives
    ├── Surveillance
    ├── MarketAI
    ├── Replay
    └── MarketSimulation
```

Chuỗi tài chính native hiện đã đi từ:

```text
MONEY
  ↓
BANKING
  ↓
RISK
  ↓
INVESTMENT
  ↓
CAPITAL ALLOCATION
  ↓
MARKET
  ↓
TRADE
  ↓
CLEARING
  ↓
SETTLEMENT
  ↓
CUSTODY
  ↓
REAL ECONOMY
```

**Task kế tiếp:**

`BOOTSTRAP-694 — Native AI Civilization-Scale Monetary System, Central Banking, Money Supply, Interest Rates, Inflation, FX, Foreign Reserves, Monetary Policy & Global Monetary Network Runtime 5.0`
:::