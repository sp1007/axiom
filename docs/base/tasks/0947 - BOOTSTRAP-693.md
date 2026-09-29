Tiếp tục với **BOOTSTRAP-693**, xây lớp hạ tầng thị trường vốn nằm ngay dưới `AXINVEST`: từ order intent → order → matching → trade → clearing → settlement → custody → market data.

:::writing{variant="document" id="74126" title="BOOTSTRAP-693 — Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Order Books, Market Data, Clearing, Settlement, Custody & Global Financial Market Infrastructure Runtime 5.0"}
# BOOTSTRAP-693
## Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Order Books, Market Data, Clearing, Settlement, Custody & Global Financial Market Infrastructure Runtime 5.0

**Status:** Architecture Specification  
**Version:** 5.0  
**Namespace:** `AXMARKET`  
**Layer:** Financial Market Infrastructure  
**Primary role:** securities markets, exchanges, brokers, order management, matching, market data, clearing, settlement, custody và global capital-market infrastructure.

---

# 1. Mục tiêu

`AXMARKET` là lớp native biến:

```text
Investment Decision
      ↓
Order Intent
      ↓
Order
      ↓
Market
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

thành một pipeline có thể:

- chạy local;
- chạy exchange-scale;
- chạy distributed;
- deterministic;
- low-latency;
- high-throughput;
- auditable;
- fault-tolerant;
- multi-market;
- multi-currency;
- multi-asset;
- AI-assisted;
- civilization-scale.

---

# 2. Vị trí kiến trúc

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
    │
    ├── Securities
    ├── Exchange
    ├── Broker
    ├── OMS
    ├── Matching Engine
    ├── Market Data
    ├── Clearing
    ├── Settlement
    ├── Custody
    └── Market Surveillance
```

---

# 3. Ranh giới với AXINVEST

`AXINVEST` quyết định:

```text
what to buy
what to sell
how much capital
which portfolio
which strategy
which constraints
```

`AXMARKET` quyết định:

```text
how order enters market
how order is prioritized
how order matches
how trade is recorded
how trade is cleared
how settlement occurs
how asset is held
```

---

# 4. Các phân biệt bắt buộc

```text
OrderIntent ≠ Order
Order ≠ Execution
Execution ≠ Trade
Trade ≠ Settlement
Settlement ≠ Custody
MarketPrice ≠ FundamentalValue
Quote ≠ Trade
Bid ≠ Offer
ReferencePrice ≠ ExecutionPrice
IndicativePrice ≠ ExecutedPrice
Clearing ≠ Settlement
Custody ≠ OwnershipAdjudication
MarketData ≠ Truth
SuspiciousActivity ≠ ProvenWrongdoing
```

---

# 5. Core Entity Model

```text
Market
Exchange
Venue
Broker
Dealer
Participant
Client
Account

Instrument
Security
SecurityClass
Listing
Issuer

Order
OrderIntent
ExecutionInstruction
Execution
Trade
TradeAllocation

OrderBook
Bid
Ask
Quote
MarketDepth
MarketSnapshot

MatchingEngine
MatchingPolicy
Auction
TradingSession

ClearingHouse
ClearingMember
ClearingPosition
MarginAccount
Collateral
SettlementInstruction
SettlementCycle

Custodian
CustodyAccount
Holding
AssetMovement

CorporateAction
Dividend
Split
Merger
Redemption

MarketDataFeed
MarketDataEvent
Tick
QuoteUpdate
TradeUpdate
ReferenceData

SurveillanceCase
MarketAlert
ManipulationSignal
ComplianceEvent
```

---

# 6. Market

```axiom
struct Market {
    id: MarketId
    jurisdiction: Jurisdiction
    currency: Currency
    venues: VenueSet
    calendar: MarketCalendar
    status: MarketStatus
}
```

---

# 7. Exchange

```axiom
struct Exchange {
    id: ExchangeId
    operator: OrganizationRef
    markets: MarketSet
    matching_engine: MatchingEngineRef
    rulebook: RulebookRef
}
```

---

# 8. Venue

Không phải mọi trading venue đều là exchange.

```text
Exchange
ATS
ECN
DarkPool
OTC
RFQVenue
AuctionVenue
Internalizer
```

`Venue` là abstraction chung.

---

# 9. Listing

Một security có thể có nhiều listing:

```text
Security
 ├── Listing A
 ├── Listing B
 └── Listing C
```

Mỗi listing có:

```text
Venue
Currency
TradingHours
TickSize
LotSize
SettlementCycle
```

---

# 10. Instrument

```axiom
struct Instrument {
    id: InstrumentId
    class: InstrumentClass
    currency: Currency
    issuer: IssuerRef?
}
```

---

# 11. Instrument Classes

```text
Equity
Bond
ETF
FundUnit
REIT
Warrant
Option
Future
Forward
SwapReference
Certificate
StructuredProduct
MoneyMarket
CommodityReference
```

Derivative semantics có thể được mở rộng bởi provider/domain module.

---

# 12. Security Identity

Mỗi security phải có stable identity:

```text
SecurityId
```

Không được dùng ticker làm primary identity.

Ticker có thể thay đổi.

---

# 13. Symbol

```axiom
struct Symbol {
    market: MarketId
    venue: VenueId
    text: String
}
```

---

# 14. Market Participant

```axiom
struct Participant {
    id: ParticipantId
    kind: ParticipantKind
    permissions: CapabilitySet
    status: ParticipantStatus
}
```

Kinds:

```text
Exchange
Broker
Dealer
MarketMaker
Institution
Fund
Bank
Insurance
Retail
Custodian
ClearingMember
LiquidityProvider
AITradingAgent
```

---

# 15. Broker

Broker cung cấp:

```text
ClientAccess
OrderRouting
OrderManagement
ExecutionServices
Reporting
```

Không tự động là exchange.

---

# 16. Dealer

Dealer có thể:

```text
quote
buy
sell
inventory
internalize
```

theo market rules.

---

# 17. Market Maker

Market maker abstraction:

```axiom
struct MarketMaker {
    participant: ParticipantRef
    instruments: InstrumentSet
    quoting_policy: QuotingPolicy
}
```

---

# 18. Trading Account

```axiom
struct TradingAccount {
    id: AccountId
    owner: ParticipantRef
    cash_account: CashAccountRef
    custody_account: CustodyAccountRef
    permissions: TradingPermissionSet
}
```

---

# 19. Order

Order là instruction gửi vào market.

```axiom
struct Order {
    id: OrderId
    account: TradingAccountRef
    instrument: InstrumentRef
    side: Side
    quantity: Quantity
    order_type: OrderType
    time_in_force: TimeInForce
    price: Price?
    timestamp: Timestamp
}
```

---

# 20. Order Types

Core:

```text
Market
Limit
Stop
StopLimit
MarketToLimit
Pegged
Iceberg
Auction
```

Advanced types có thể là extensions.

---

# 21. Side

```text
Buy
Sell
SellShort
BuyToCover
```

Short selling policy phải được market/regulatory profile kiểm soát.

---

# 22. Time in Force

```text
Day
GTC
IOC
FOK
GTD
Session
AuctionOnly
Immediate
```

---

# 23. Order State

```text
Draft
Submitted
Accepted
Rejected
Queued
PartiallyFilled
Filled
Cancelled
Expired
Suspended
```

---

# 24. Order Lifecycle

```text
Draft
  ↓
Submitted
  ↓
Validated
  ↓
Accepted
  ↓
Queued
  ↓
Matched
  ↓
Executed
  ↓
Cleared
  ↓
Settled
```

Nhánh:

```text
Rejected
Cancelled
Expired
Failed
Suspended
```

---

# 25. Order Validation

Trước khi vào order book:

```text
identity
permission
instrument
quantity
price
tick_size
lot_size
market_session
account
margin
short_sale
risk_limits
```

---

# 26. Pre-Trade Risk

```axiom
check_pretrade(order)
    -> PreTradeResult
```

Có thể kiểm tra:

```text
PositionLimit
NotionalLimit
PriceBand
Margin
Credit
FatFinger
OrderRate
Position
ShortSale
MarketStatus
```

---

# 27. Fat-Finger Protection

Reject/suspend order nếu:

```text
quantity > limit
notional > limit
price deviation > band
rate > limit
```

Threshold phải configurable.

---

# 28. Order Intent Boundary

`AXINVEST` gửi:

```text
OrderIntent
```

`AXMARKET` chuyển thành:

```text
Order
```

không được bỏ qua authorization boundary.

---

# 29. Order Management System

OMS quản lý:

```text
Order
OrderGroup
ParentOrder
ChildOrder
Execution
Allocation
Cancellation
Amendment
```

---

# 30. Parent Order

```text
ParentOrder
    ↓
ChildOrder A
ChildOrder B
ChildOrder C
```

dùng cho execution algorithms.

---

# 31. Execution Algorithm

Ví dụ:

```text
TWAP
VWAP
POV
ImplementationShortfall
ArrivalPrice
Iceberg
Adaptive
```

Các algorithm chỉ là execution policies.

---

# 32. Algorithmic Execution

```axiom
execute parent_order {
    algorithm = TWAP
    duration = 60m
    participation_limit = 10%
}
```

---

# 33. Execution ≠ Trade

Một execution là fill của order.

Một trade có thể được tạo từ một hoặc nhiều executions tùy market model.

---

# 34. Execution

```axiom
struct Execution {
    id: ExecutionId
    order: OrderRef
    quantity: Quantity
    price: Price
    venue: VenueRef
    timestamp: Timestamp
}
```

---

# 35. Trade

```axiom
struct Trade {
    id: TradeId
    instrument: InstrumentRef
    buy_side: ParticipantRef
    sell_side: ParticipantRef
    quantity: Quantity
    price: Price
    venue: VenueRef
    trade_time: Timestamp
}
```

---

# 36. Trade Allocation

Institutional order có thể allocate:

```text
Trade
 ↓
Account A
Account B
Account C
```

Allocation policy phải được lưu.

---

# 37. Order Book

Core structure:

```text
Bid Book
Ask Book
```

Mỗi level:

```text
Price
Quantity
OrderQueue
```

---

# 38. Price-Time Priority

Default matching policy:

```text
higher_bid first
lower_ask first
earlier_order first
```

Nhưng policy phải configurable theo venue.

---

# 39. Matching Engine

```axiom
match(order_book)
    -> ExecutionSet
```

Matching engine phải deterministic với cùng:

```text
input event sequence
matching policy
market state
```

---

# 40. Matching Policies

```text
PriceTime
ProRata
SizeTime
Auction
Hybrid
Custom
```

---

# 41. Continuous Trading

```text
Order
→ Book
→ Match
→ Execution
```

---

# 42. Call Auction

```text
CollectOrders
→ DetermineClearingPrice
→ Match
→ PublishAuctionResult
```

---

# 43. Opening Auction

```text
PreOpen
→ Auction
→ Open
→ Continuous
```

---

# 44. Closing Auction

```text
Continuous
→ ClosingAuction
→ Close
→ PostMarket
```

---

# 45. Trading Session

```axiom
struct TradingSession {
    id: SessionId
    phase: SessionPhase
    open: Timestamp
    close: Timestamp
}
```

Phases:

```text
Closed
PreOpen
OpeningAuction
Continuous
ClosingAuction
PostMarket
Halted
```

---

# 46. Trading Halt

```text
Normal
→ Halted
→ Resuming
→ Normal
```

Halt reason:

```text
Volatility
Technical
Information
Regulatory
Liquidity
Emergency
```

---

# 47. Price Bands

Venue có thể định nghĩa:

```text
StaticBand
DynamicBand
LimitUp
LimitDown
VolatilityInterruption
```

---

# 48. Tick Size

Price phải conform:

```text
price % tick_size == 0
```

theo market rounding policy.

---

# 49. Lot Size

Quantity phải conform:

```text
quantity % lot_size == 0
```

nếu venue yêu cầu.

---

# 50. Market Data

Market data categories:

```text
Reference
Quote
Trade
OrderBook
Auction
CorporateAction
Status
Statistics
```

---

# 51. Quote

```axiom
struct Quote {
    bid: Price?
    bid_size: Quantity?
    ask: Price?
    ask_size: Quantity?
    timestamp: Timestamp
}
```

---

# 52. NBBO / Best Quote

Venue aggregation có thể tạo:

```text
BestBid
BestAsk
Spread
```

---

# 53. Market Depth

```axiom
struct MarketDepth {
    bids: PriceLevel[]
    asks: PriceLevel[]
}
```

---

# 54. Trade Tape

```text
TradeEvent[]
```

mỗi event:

```text
price
quantity
timestamp
venue
```

---

# 55. Market Snapshot

```axiom
struct MarketSnapshot {
    instrument: InstrumentRef
    timestamp: Timestamp
    bid: Price?
    ask: Price?
    last: Price?
    volume: Quantity
    depth: MarketDepth?
}
```

---

# 56. Market Data Event

```text
QuoteUpdate
TradeUpdate
BookAdd
BookModify
BookCancel
AuctionUpdate
StatusUpdate
ReferenceUpdate
```

---

# 57. Sequence Numbers

Mỗi market-data stream phải có:

```text
sequence_number
```

để phát hiện:

```text
gap
duplicate
replay
out_of_order
```

---

# 58. Market Data Recovery

Nếu phát hiện gap:

```text
pause_consumer
→ request_snapshot
→ validate_sequence
→ resume
```

---

# 59. Feed Handler

```text
Network
 ↓
Decode
 ↓
Validate
 ↓
Sequence
 ↓
Normalize
 ↓
Publish
```

---

# 60. Normalized Market Data

Nhiều venue có format khác nhau.

`AXMARKET` cung cấp:

```text
NativeMarketData
```

và adapter:

```text
ExternalMarketDataProvider
```

---

# 61. Market Data Timestamp

Phải phân biệt:

```text
SourceTimestamp
ReceiveTimestamp
NormalizeTimestamp
PublishTimestamp
```

---

# 62. Clock Synchronization

Low-latency market infrastructure phải hỗ trợ:

```text
MonotonicClock
WallClock
ExchangeClock
```

---

# 63. Event Ordering

Không được giả định network arrival order = market event order.

Sequence/order metadata phải được dùng.

---

# 64. Market Data Replay

Native replay:

```axiom
replay market_data {
    from = t1
    to = t2
    speed = 10x
}
```

---

# 65. Market Simulator

```text
MarketSimulator
```

có thể mô phỏng:

```text
OrderArrival
OrderCancellation
Liquidity
Volatility
Matching
Auction
Latency
MarketMaker
```

---

# 66. Synthetic Market

AI simulation có thể tạo:

```text
SyntheticOrderFlow
SyntheticParticipants
SyntheticLiquidity
SyntheticPriceProcess
```

Phải đánh dấu synthetic.

---

# 67. Clearing

Clearing xác định:

```text
who owes what
who receives what
net obligations
margin
collateral
default exposure
```

---

# 68. Clearing ≠ Settlement

```text
Clearing
    = obligation calculation

Settlement
    = final transfer
```

---

# 69. Clearing House

```axiom
struct ClearingHouse {
    id: ClearingHouseId
    members: ClearingMemberSet
    markets: MarketSet
    margin_policy: MarginPolicy
}
```

---

# 70. Clearing Member

```axiom
struct ClearingMember {
    id: ClearingMemberId
    participant: ParticipantRef
    collateral_account: CollateralAccountRef
    risk_limits: RiskLimitSet
}
```

---

# 71. Clearing Position

```text
GrossPosition
NetPosition
LongExposure
ShortExposure
```

---

# 72. Netting

Ví dụ:

```text
Buy 100
Sell 60
```

Net obligation:

```text
Buy 40
```

nhưng gross trade history vẫn được bảo tồn.

---

# 73. Multilateral Netting

Nhiều participants:

```text
A → B
B → C
C → A
```

có thể net theo clearing rules.

---

# 74. Margin

Margin types:

```text
InitialMargin
VariationMargin
MaintenanceMargin
AdditionalMargin
IntradayMargin
```

---

# 75. Margin Engine

```axiom
calculate_margin(
    positions,
    market_state,
    margin_policy
)
```

---

# 76. Margin Method

Provider boundary:

```text
PortfolioMargin
SPANLike
ScenarioMargin
VaRMargin
CustomMargin
```

---

# 77. Variation Margin

Mark-to-market changes tạo:

```text
MarginCall
MarginCredit
```

---

# 78. Collateral

Collateral classes:

```text
Cash
GovernmentBond
EligibleSecurity
OtherEligibleAsset
```

Eligibility policy phải explicit.

---

# 79. Haircut

```axiom
struct CollateralRule {
    asset_class: AssetClass
    haircut: Rate
}
```

---

# 80. Collateral Value

```text
CollateralValue
=
MarketValue × (1 - Haircut)
```

theo policy.

---

# 81. Default Management

Clearing phải có:

```text
DefaultEvent
PositionFreeze
CollateralLiquidation
DefaultFund
Auction
CloseOut
Recovery
```

---

# 82. Default Waterfall

Ví dụ abstraction:

```text
DefaulterCollateral
→ MemberResources
→ DefaultFund
→ AdditionalAssessment
→ Recovery
```

Thứ tự phải do market rulebook định nghĩa.

---

# 83. Settlement

Settlement flow:

```text
Trade
→ Clearing
→ SettlementInstruction
→ Matching
→ Asset/Cash Transfer
→ Final
```

---

# 84. Settlement Cycle

Market có thể cấu hình:

```text
T+0
T+1
T+2
Custom
```

Không hard-code một settlement cycle.

---

# 85. Settlement Instruction

```axiom
struct SettlementInstruction {
    id: SettlementInstructionId
    trade: TradeRef
    delivery_account: CustodyAccountRef
    payment_account: CashAccountRef
    value_date: Date
}
```

---

# 86. Delivery Versus Payment

Core invariant:

```text
AssetDelivery
↔
CashPayment
```

phải atomic theo settlement model nếu DvP được yêu cầu.

---

# 87. Free of Payment

Một số transfers có thể:

```text
FoP
```

nhưng phải explicit.

---

# 88. Settlement Failure

States:

```text
Pending
Matched
Ready
PartiallySettled
Settled
Failed
Cancelled
```

---

# 89. Settlement Retry

Retry policy phải tránh duplicate settlement.

Sử dụng:

```text
SettlementInstructionId
IdempotencyKey
```

---

# 90. Custody

Custody quản lý:

```text
asset holdings
entitlements
corporate actions
asset movements
account segregation
```

---

# 91. Custody Account

```axiom
struct CustodyAccount {
    id: CustodyAccountId
    owner: ParticipantRef
    type: CustodyAccountType
}
```

---

# 92. Segregated Custody

Hỗ trợ:

```text
Omnibus
Segregated
SubAccount
ClientAsset
HouseAsset
```

---

# 93. Custody Movement

```text
Receive
Deliver
Transfer
Pledge
Release
Freeze
Unfreeze
```

---

# 94. Holding

Custody holding:

```axiom
struct CustodyHolding {
    account: CustodyAccountRef
    security: SecurityRef
    quantity: Quantity
    encumbrance: Encumbrance?
}
```

---

# 95. Encumbrance

```text
Pledged
Collateralized
Frozen
Restricted
Lent
Borrowed
```

---

# 96. Securities Lending

Native abstraction:

```text
Loan
Borrow
Lend
Collateral
Recall
Return
Fee
```

---

# 97. Repo Boundary

Repo can reference:

```text
Security
Cash
Collateral
RepurchaseTerms
```

Detailed banking/treasury semantics remain in `AXBANKING` where applicable.

---

# 98. Corporate Actions

Core events:

```text
Dividend
Interest
StockSplit
ReverseSplit
RightsIssue
BonusIssue
Merger
Acquisition
SpinOff
TenderOffer
Redemption
Conversion
Maturity
```

---

# 99. Corporate Action Lifecycle

```text
Announced
→ Validated
→ Pending
→ ExDate
→ RecordDate
→ PayDate
→ Completed
```

---

# 100. Corporate Action Entitlement

```axiom
calculate_entitlement(
    holding,
    record_date,
    corporate_action
)
```

---

# 101. Ex-Date / Record-Date

Các dates phải là first-class fields.

Không được suy luận ngầm từ pay date.

---

# 102. Fractional Entitlement

Policy phải quy định:

```text
fractional_cash
fractional_security
round_down
round_up
```

---

# 103. Market Reference Data

```text
SecurityMaster
IssuerMaster
VenueMaster
CurrencyMaster
CalendarMaster
SettlementRule
TickSizeRule
LotSizeRule
```

---

# 104. Security Master

Security master là canonical metadata layer, không phải price source.

---

# 105. Issuer

```axiom
struct Issuer {
    id: IssuerId
    legal_entity: LegalEntityRef
    securities: SecuritySet
}
```

Legal identity authoritative từ `AXLAW`.

---

# 106. Reference Data Versioning

Mọi reference data phải versioned:

```text
effective_from
effective_to
version
source
```

---

# 107. Market Rules

```axiom
struct MarketRuleSet {
    order_types
    matching_policy
    tick_rules
    lot_rules
    trading_hours
    price_bands
    halt_rules
    settlement_cycle
}
```

---

# 108. Rulebook

Rulebook phải có:

```text
version
jurisdiction
effective_date
authority
```

---

# 109. Brokerage

Broker workflow:

```text
Client
→ Order
→ Risk
→ Routing
→ Venue
→ Execution
→ Allocation
→ Clearing
→ Settlement
```

---

# 110. Smart Order Routing

```axiom
route order {
    venues = [A, B, C]

    objective:
        minimize_cost

    constraints:
        max_latency = 5ms
}
```

---

# 111. Routing Objective

Có thể tối ưu:

```text
Price
Fees
Spread
Liquidity
Latency
MarketImpact
FillProbability
VenueRisk
```

---

# 112. Routing ≠ Matching

Router chọn venue.

Matching engine quyết định execution trong venue.

---

# 113. Internalization

Broker/dealer có thể internalize nếu market rule cho phép.

```text
ClientOrder
→ InternalLiquidity
```

Nếu không fill:

```text
→ ExternalVenue
```

---

# 114. RFQ

Hỗ trợ:

```text
RequestForQuote
Quote
CounterQuote
Accept
Reject
Expire
Trade
```

---

# 115. OTC

OTC market không bắt buộc order book.

Flow:

```text
Inquiry
→ Quote
→ Negotiation
→ Agreement
→ Trade
→ Clearing/Settlement
```

---

# 116. Auction Market

Auction types:

```text
Opening
Closing
Periodic
Call
Liquidation
Tender
```

---

# 117. Dark / Non-Displayed Liquidity

Architecture có thể support hidden orders:

```text
displayed = false
```

nhưng visibility policy phải explicit.

---

# 118. Hidden Order Invariant

Hidden order không được leak vào public market data ngoài fields được phép.

---

# 119. Market Surveillance

Native surveillance engine:

```text
PriceManipulationSignal
SpoofingSignal
LayeringSignal
WashTradeSignal
FrontRunningSignal
InsiderTradingReference
AbnormalVolume
AbnormalOrderRate
```

Các signal là:

```text
Signal ≠ ProvenWrongdoing
```

---

# 120. Surveillance Event

```axiom
struct SurveillanceEvent {
    id: EventId
    type: SurveillanceType
    participants: ParticipantSet
    evidence: EvidenceSet
    confidence: Probability?
    timestamp: Timestamp
}
```

---

# 121. Surveillance Case

```text
Detected
→ Reviewed
→ Escalated
→ Resolved
→ Closed
```

---

# 122. AI Surveillance

AI có thể:

```text
detect
cluster
rank_for_review
summarize
explain
```

nhưng không tự biến signal thành legal finding.

---

# 123. Market Anomaly

Anomaly types:

```text
Price
Volume
OrderRate
Cancellation
Spread
CrossVenue
Participant
Latency
```

---

# 124. Cross-Venue Surveillance

Có thể correlate:

```text
Venue A
Venue B
Venue C
```

để phát hiện cross-market anomalies.

---

# 125. Market Integrity

System phải preserve:

```text
order history
amendment history
cancel history
execution history
timestamp
participant identity
venue
```

theo retention policy.

---

# 126. Order Amendment

Amendment phải tạo event:

```text
OrderAmended
```

không overwrite history.

---

# 127. Cancel/Replace

```text
OriginalOrder
→ CancelReplace
→ NewOrder
```

Priority consequences phải theo market rules.

---

# 128. Idempotency

Mọi external mutation hỗ trợ:

```text
IdempotencyKey
```

---

# 129. Replay Protection

Duplicate command không được tạo duplicate:

```text
Order
Execution
Trade
Settlement
```

---

# 130. Disaster Recovery

Market infrastructure phải hỗ trợ:

```text
checkpoint
snapshot
event_log
replay
failover
recovery
```

---

# 131. Matching Engine Recovery

Có thể reconstruct:

```text
OrderBook
```

từ:

```text
snapshot + event log
```

---

# 132. Deterministic Matching

Cùng:

```text
initial_book
event_sequence
matching_policy
```

phải tạo cùng executions.

---

# 133. Hot Failover

Primary:

```text
MatchingEngine A
```

Backup:

```text
MatchingEngine B
```

Backup phải có state đủ để takeover theo configured consistency model.

---

# 134. Market Partition

Distributed market có thể partition theo:

```text
Instrument
Market
Venue
Shard
```

---

# 135. Ordering Boundary

Trong cùng matching partition phải có authoritative event order.

---

# 136. Cross-Market Atomicity

Không giả định atomicity giữa hai independent venues.

Cross-market strategy phải dùng explicit coordination protocol.

---

# 137. Latency

Core matching path phải tối ưu:

```text
parse
→ validate
→ risk
→ enqueue
→ match
→ emit
```

---

# 138. Memory Architecture

Order book ưu tiên:

```text
contiguous arrays
intrusive queues
arena allocation
object pools
cache-friendly structures
```

Không yêu cầu GC.

---

# 139. Zero-Copy Market Data

Feed pipeline hỗ trợ:

```text
DMA buffer
zero-copy decode
slice/view
ring buffer
```

khi platform cho phép.

---

# 140. Lock-Free Structures

Hot paths có thể sử dụng:

```text
SPSC
MPSC
MPMC
lock-free ring
atomic queue
```

theo concurrency profile.

---

# 141. NUMA Awareness

Server profile hỗ trợ:

```text
CPU affinity
NUMA locality
memory affinity
shard affinity
```

---

# 142. FPGA / Accelerator Boundary

`AXMARKET` cho phép:

```text
MatchingProvider
MarketDataProvider
RiskProvider
```

được implement bằng:

```text
CPU
GPU
FPGA
NIC offload
```

---

# 143. Native Risk Pre-Trade

Hot-path risk:

```text
position
notional
margin
credit
price band
order rate
```

phải có fast path.

Complex analytics có thể chạy asynchronous.

---

# 144. Fast Path / Slow Path

```text
FAST:
order validation
basic risk
matching
execution

SLOW:
deep risk
analytics
surveillance
reporting
AI
```

---

# 145. Market Data Fanout

```text
Feed
 ↓
Normalizer
 ↓
EventBus
 ├── OMS
 ├── Risk
 ├── Surveillance
 ├── Analytics
 └── ExternalSubscribers
```

---

# 146. Subscriber Isolation

Slow consumer không được block matching engine.

---

# 147. Backpressure

Market data subscribers có:

```text
drop_policy
buffer_limit
snapshot_recovery
```

---

# 148. Market Data Quality

Metrics:

```text
GapRate
DuplicateRate
Latency
Staleness
OutOfOrderRate
DecodeError
```

---

# 149. Reference Price

Reference price types:

```text
PreviousClose
IndicativeOpen
VWAP
Mid
Mark
SettlementPrice
IndexPrice
```

Mỗi loại có semantic riêng.

---

# 150. Settlement Price

Settlement price ≠ last trade price.

Có thể được tính từ market rule.

---

# 151. Index

Market infrastructure có thể host:

```text
IndexDefinition
IndexConstituent
IndexCalculation
IndexLevel
IndexEvent
```

---

# 152. Index Calculation

```axiom
calculate_index(
    constituents,
    weights,
    prices
)
```

---

# 153. Index Rebalance

```text
Announced
→ Effective
→ Applied
```

---

# 154. Benchmark Boundary

Benchmark analytics thuộc `AXINVEST`; market index infrastructure cung cấp raw index state.

---

# 155. Derivatives

Architecture phải support:

```text
Option
Future
Forward
Swap
Warrant
```

nhưng detailed pricing models có thể nằm trong derivative extension.

---

# 156. Option Contract

```axiom
struct Option {
    underlying: InstrumentRef
    strike: Price
    expiry: Timestamp
    style: OptionStyle
    type: CallPut
}
```

---

# 157. Future Contract

```axiom
struct Future {
    underlying: ReferenceAssetRef
    expiry: Date
    contract_size: Quantity
}
```

---

# 158. Derivative Margin

Derivative positions phải đi qua:

```text
Clearing
→ Margin
→ Settlement
```

theo market rules.

---

# 159. Expiry

Derivative lifecycle:

```text
Open
→ Expiring
→ Exercised/Settled
→ Closed
```

---

# 160. Exercise

Option exercise có thể:

```text
Physical
Cash
```

---

# 161. Delivery

Physical delivery reference phải integrate với relevant physical-domain systems.

---

# 162. Securities Lending / Borrowing

Lifecycle:

```text
Requested
→ Matched
→ Delivered
→ Open
→ Recalled
→ Returned
→ Closed
```

---

# 163. Repo / Collateral Market

Có thể share:

```text
Collateral
Margin
Settlement
Custody
```

với banking/treasury layers.

---

# 164. Market Liquidity

Native metrics:

```text
Spread
Depth
Turnover
Volume
AmihudLike
MarketImpact
FillRate
```

---

# 165. Market Impact Model

```axiom
estimate_impact(
    order,
    market_state
)
```

Output:

```text
EstimatedImpact
```

không phải guaranteed execution outcome.

---

# 166. Slippage

```text
Slippage
=
ExecutionPrice - ReferencePrice
```

với side-aware semantics.

---

# 167. Transaction Cost Analysis

TCA:

```text
ArrivalPrice
DecisionPrice
VWAP
TWAP
ImplementationShortfall
Fees
Taxes
MarketImpact
Slippage
```

---

# 168. Execution Quality

TCA là measurement.

Không tự động coi execution là tốt/xấu nếu không có benchmark/policy.

---

# 169. Market Microstructure Simulation

Simulation phải support:

```text
agents
order arrival
cancellation
latency
queue
liquidity
matching
price formation
```

---

# 170. AI Market Agents

Agent types:

```text
MarketMaker
LiquidityTaker
InstitutionalInvestor
RetailInvestor
Broker
ArbitrageAgent
Hedger
```

Mỗi agent có:

```text
capital
inventory
constraints
strategy
latency
authority
```

---

# 171. Agent Simulation Boundary

Synthetic agents không được truy cập live market state ngoài explicit simulation input.

---

# 172. Market Replay

Historical event replay:

```axiom
market.replay(
    start,
    end,
    speed,
    strategy
)
```

---

# 173. Strategy Replay

Có thể chạy:

```text
HistoricalMarket
+
HistoricalOrderFlow
+
Strategy
```

để kiểm tra execution behavior.

---

# 174. No Future Leakage

Replay engine phải preserve event availability timestamp.

---

# 175. Market Twin

Digital twin:

```text
ObservedMarket
EstimatedLiquidity
PredictedFlow
SimulatedMarket
```

---

# 176. Market State Authority

Chỉ designated market source mới có thể tạo:

```text
AuthoritativeTrade
AuthoritativeOrder
AuthoritativeSettlement
```

---

# 177. Synthetic vs Authoritative

Mọi synthetic event phải có:

```text
source_kind = synthetic
```

và không được nhập nhầm vào live ledger.

---

# 178. Market Ledger

Native immutable event log:

```text
OrderEvent
ExecutionEvent
TradeEvent
ClearingEvent
SettlementEvent
CustodyEvent
```

---

# 179. Trade Audit

Một trade phải truy ngược được:

```text
Trade
→ Execution
→ Order
→ Account
→ Participant
→ Authorization
```

---

# 180. Settlement Audit

```text
Settlement
→ Trade
→ Clearing
→ Instruction
→ AssetMovement
→ CashMovement
```

---

# 181. Custody Audit

```text
Holding
→ Settlement
→ CorporateAction
→ Transfer
```

---

# 182. Corporate Action Audit

```text
Announcement
→ Eligibility
→ Entitlement
→ Allocation
→ Settlement
```

---

# 183. Market Identity

Participant identity phải tách:

```text
LegalIdentity
TradingIdentity
AccountIdentity
SessionIdentity
```

---

# 184. Session Authentication

Trading session phải có:

```text
Authentication
Authorization
SessionKey
Expiry
Revocation
```

---

# 185. Trading Capability

Capabilities:

```text
market.read
market.trade

order.create
order.modify
order.cancel

execution.read
trade.read

marketdata.read
marketdata.subscribe

clearing.read
clearing.write

margin.read
margin.write

settlement.read
settlement.write

custody.read
custody.write

corporate_action.read
corporate_action.process

surveillance.read
surveillance.manage

market.admin
```

---

# 186. Capability Separation

```text
market.read
≠
order.create
≠
order.approve
≠
order.execute
≠
settlement.finalize
```

---

# 187. AI Trading Agent

Default:

```axiom
agent TraderAI {
    can:
        read_market
        analyze
        propose_order

    cannot:
        submit_order
}
```

---

# 188. Bounded Trading Agent

```axiom
agent TreasuryTrader {
    authority {
        submit_order
        max_notional = 1_000_000
        instruments = fixed_income
    }
}
```

Compiler/runtime enforce limits.

---

# 189. Self-Escalation Prevention

AI cannot:

```text
grant itself capability
modify own limits
modify market rules
modify clearing rules
delete audit records
```

---

# 190. Kill Switch

```text
pause_trading_agent
revoke_session
cancel_open_orders
freeze_account
halt_market
```

Authority must be explicit.

---

# 191. Emergency Mode

Emergency policy may:

```text
halt
cancel
freeze
restrict
```

nhưng phải audit.

---

# 192. Market Recovery

After crash:

```text
restore snapshot
→ replay event log
→ verify checksum
→ validate sequence
→ resume
```

---

# 193. State Checksum

Critical market state có:

```text
state_hash
event_sequence
timestamp
version
```

---

# 194. Snapshot Frequency

Configurable:

```text
time_based
event_based
size_based
```

---

# 195. Event Log Durability

Critical market events phải durable theo market consistency profile trước khi authoritative acknowledgement nếu policy yêu cầu.

---

# 196. Settlement Atomicity

Settlement transaction phải support:

```text
prepare
→ validate
→ lock
→ transfer
→ commit
```

---

# 197. Double Settlement Prevention

Invariant:

```text
one SettlementInstruction
→ max one final settlement
```

---

# 198. Asset Conservation

Trong custody system:

```text
TotalAssetQuantity
```

phải được conservation-check theo instrument/lifecycle rules.

---

# 199. Cash Conservation

Settlement engine phải preserve:

```text
cash_debit = cash_credit
```

trừ fee/tax flows explicitly represented.

---

# 200. Trade Conservation

Trade creation không được tự tạo asset supply ngoài:

```text
issuance
corporate_action
minting
```

được phép bởi instrument rules.

---

# 201. Short Position

Short position phải explicit:

```text
position.quantity < 0
```

hoặc dedicated short representation.

Không được nhầm với custody ownership.

---

# 202. Borrow Requirement

Short sale có thể yêu cầu:

```text
Locate
Borrow
Availability
Collateral
```

theo market rule.

---

# 203. Position Reconciliation

Hàng ngày hoặc configurable:

```text
InternalPosition
vs
CustodianPosition
vs
ClearingPosition
```

---

# 204. Reconciliation Result

```text
Matched
Difference
Missing
Unexpected
Pending
```

---

# 205. Break Management

```text
BreakDetected
→ Investigating
→ Correcting
→ Reconciled
→ Closed
```

---

# 206. Market Data Reconciliation

Cross-feed:

```text
Feed A
Feed B
Reference
```

có thể detect discrepancy.

---

# 207. Market Data Confidence

Data point có thể có:

```text
Observed
Validated
Estimated
Derived
Synthetic
```

---

# 208. Data Lineage

Market data lineage:

```text
Source
→ Decode
→ Normalize
→ Transform
→ Aggregate
→ Publish
```

---

# 209. Privacy

Public market data có thể public.

Nhưng:

```text
client identity
account
beneficial owner
private order flow
```

phải được access-controlled.

---

# 210. Beneficial Ownership

Beneficial ownership authority thuộc legal/custody/compliance systems.

`AXMARKET` chỉ giữ reference cần thiết.

---

# 211. Regulatory Reporting

Market infrastructure có thể produce:

```text
TradeReport
OrderReport
PositionReport
MarginReport
SettlementReport
SurveillanceReport
```

Reporting rules inject qua jurisdiction profile.

---

# 212. Transaction Reporting

Mỗi report phải giữ:

```text
source_trade
report_version
jurisdiction
submission_status
submission_timestamp
```

---

# 213. Reporting Lifecycle

```text
Generated
→ Validated
→ Submitted
→ Accepted
```

hoặc:

```text
Rejected
→ Corrected
→ Resubmitted
```

---

# 214. Rule Engine

Market rule engine:

```axiom
rule price_band {
    reject order
    when abs(order.price - reference_price)
        > allowed_deviation
}
```

---

# 215. Rule Determinism

Rule evaluation phải deterministic trong cùng:

```text
rule_version
input_state
timestamp
```

---

# 216. Rule Versioning

Không sửa historical rule.

Tạo:

```text
RuleSet v1
RuleSet v2
```

---

# 217. Market Configuration

Không hard-code:

```text
tick size
lot size
hours
settlement cycle
fees
price bands
```

Tất cả thuộc configuration/rule data.

---

# 218. Fee Engine

Fees:

```text
TradingFee
ClearingFee
SettlementFee
CustodyFee
MarketDataFee
BrokerFee
RegulatoryFee
```

---

# 219. Fee Calculation

```axiom
calculate_fee(
    trade,
    fee_schedule
)
```

Fee schedule phải versioned.

---

# 220. Tax Boundary

Tax calculation có thể consume từ `AXLAW/AXFINANCE`.

Market layer records tax references, không hard-code global tax law.

---

# 221. Currency Settlement

Cross-currency trade cần:

```text
TradeCurrency
SettlementCurrency
FXRateReference
FXExecutionReference
```

---

# 222. FX Settlement Risk

Nếu two-leg settlement không atomic:

```text
SettlementRisk
```

phải được represented.

---

# 223. PvP

Foreign exchange market có thể dùng:

```text
PaymentVersusPayment
```

theo settlement provider.

---

# 224. Cross-Asset Settlement

Một transaction có thể tạo:

```text
cash_leg
asset_leg
collateral_leg
fee_leg
tax_leg
```

---

# 225. Settlement Graph

```text
Trade
 ├── AssetLeg
 ├── CashLeg
 ├── FeeLeg
 └── TaxLeg
```

---

# 226. Settlement Netting Graph

Multiple trades có thể tạo:

```text
Gross obligations
      ↓
Netting
      ↓
Settlement obligations
```

---

# 227. DvP Invariant

Nếu settlement mode = DvP:

```text
asset_final
iff
cash_final
```

trừ explicitly configured partial settlement semantics.

---

# 228. Partial Settlement

Có thể support:

```text
partial quantity
partial cash
```

nhưng state phải rõ ràng.

---

# 229. Failed Settlement

Failure reasons:

```text
InsufficientCash
InsufficientSecurity
AccountFrozen
InstructionMismatch
MarketClosed
CounterpartyFailure
OperationalError
```

---

# 230. Settlement Penalty

Penalty calculation là policy-driven.

---

# 231. Market Closure

Market state:

```text
Open
Closed
Halted
Emergency
Maintenance
```

---

# 232. Venue Availability

Order router phải kiểm tra:

```text
venue.status
session.phase
instrument.status
```

---

# 233. Security Suspension

Security có thể:

```text
Active
Suspended
Delisted
Matured
Cancelled
```

---

# 234. Delisting

Lifecycle:

```text
Announced
→ Suspended
→ Delisted
→ FinalSettlement
```

---

# 235. Issuance Boundary

New security issuance có thể integrate với:

```text
AXFINANCE
AXLAW
AXMARKET
```

Market layer cung cấp listing/trading infrastructure.

---

# 236. Primary Market

Primary market workflow:

```text
Issuer
→ Offering
→ Allocation
→ Issuance
→ Settlement
→ Listing
```

---

# 237. IPO / Offering

Entities:

```text
Offering
Subscription
Allocation
UnderwriterRef
Investor
Security
```

---

# 238. Primary Allocation

Allocation rules:

```text
ProRata
Auction
BookBuild
Fixed
Custom
```

---

# 239. Secondary Market

```text
Investor A
↔
Market
↔
Investor B
```

---

# 240. Primary ≠ Secondary

Primary issuance changes supply.

Secondary trade changes ownership.

---

# 241. Securities Supply Invariant

Secondary trade không tạo thêm shares.

---

# 242. Tokenized Securities Boundary

Nếu security được tokenized:

```text
TokenRepresentation
↔
UnderlyingSecurity
```

phải giữ explicit mapping.

Token ≠ automatically legal security.

---

# 243. Digital Asset Boundary

Crypto/digital asset markets có thể được hỗ trợ:

```text
DigitalAsset
Wallet
ExchangeAccount
Custody
Settlement
```

nhưng asset semantics/configuration phải explicit.

---

# 244. Wallet Boundary

Blockchain wallet implementation thuộc provider/module.

Market core chỉ yêu cầu:

```text
AssetAccount
TransferInstruction
SettlementReference
```

---

# 245. Blockchain Settlement

Có thể có:

```text
OnChainSettlement
OffChainSettlement
HybridSettlement
```

---

# 246. Consensus Boundary

Distributed ledger consensus không nằm trong market core.

Provider interface:

```text
LedgerProvider
```

---

# 247. Smart Contract Boundary

Market runtime có thể emit:

```text
ContractCall
SettlementInstruction
```

nhưng contract execution thuộc execution environment.

---

# 248. Market Graph

Graph:

```text
Participant
 → Account
 → Order
 → Execution
 → Trade
 → Clearing
 → Settlement
 → Custody
```

---

# 249. Query Examples

```axiom
market("X").orderbook("ABC")
```

```axiom
trade("T123").audit_trail()
```

```axiom
account("A").open_orders()
```

```axiom
security("ABC").corporate_actions()
```

---

# 250. Market DSL

```axiom
market NASDAQ {
    currency = USD

    session {
        preopen = 09:00
        open = 09:30
        close = 16:00
    }

    matching = price_time
    settlement = T_PLUS_1
}
```

---

# 251. Venue DSL

```axiom
venue X {
    instrument = equity

    tick_size = 0.01
    lot_size = 1

    matching = price_time
}
```

---

# 252. Order DSL

```axiom
order buy 100 ABC {
    limit = 125.50
    tif = DAY
}
```

---

# 253. Execution DSL

```axiom
execute parent {
    algorithm = VWAP
    duration = 2h
    max_participation = 15%
}
```

---

# 254. Clearing DSL

```axiom
clearing default {
    margin = portfolio
    netting = multilateral
    collateral = eligible_assets
}
```

---

# 255. Settlement DSL

```axiom
settlement {
    cycle = T_PLUS_1
    mode = DVP
    partial = true
}
```

---

# 256. Surveillance DSL

```axiom
surveillance {
    detect spoofing
    detect wash_trade
    detect abnormal_volume

    require human_review
}
```

---

# 257. Market Simulation DSL

```axiom
simulate market {
    participants = 100000
    instruments = 10000
    horizon = 30d

    liquidity = dynamic
    volatility = stochastic
}
```

---

# 258. AI Market-Maker DSL

```axiom
agent MarketMakerAI {
    authority {
        quote
        cancel
        replace
    }

    limits {
        inventory = 1_000_000
        max_order = 100_000
    }

    cannot:
        modify_market_rules
}
```

---

# 259. Investment Integration

```text
AXINVEST
   │
   │ OrderIntent
   ▼
AXMARKET
   │
   │ Execution
   ▼
AXINVEST
```

Feedback:

```text
Execution
→ Position
→ Performance
→ Risk
→ Rebalance
```

---

# 260. Banking Integration

```text
Trade
 ↓
Cash Obligation
 ↓
AXBANKING
```

---

# 261. Insurance Integration

Insurance portfolios:

```text
AXINSURANCE
→ AXINVEST
→ AXMARKET
```

---

# 262. Pension Integration

```text
AXLABOR / AX670
→ Pension
→ AXINVEST
→ AXMARKET
```

---

# 263. Civilization Integration

```text
Civilization
→ Capital
→ Investment
→ Market
→ Production
→ Employment
→ Consumption
→ Civilization
```

---

# 264. Capital Market Simulation

At civilization scale:

```text
Millions of participants
Millions of orders
Millions of securities
Thousands of venues
Continuous market data
Distributed clearing
Distributed settlement
```

must be representable through sharded simulation.

---

# 265. Market Sharding

Possible partitions:

```text
ByMarket
ByVenue
ByInstrument
ByRegion
ByAssetClass
```

---

# 266. Global Market Federation

```text
Market A
Market B
Market C
   ↓
GlobalMarketFederation
```

Cross-market links:

```text
Liquidity
Arbitrage
FX
CapitalFlow
Collateral
Settlement
```

---

# 267. Cross-Market Arbitrage

Simulation can represent:

```text
same_asset
different_venue
different_price
```

but actual execution requires real authorization and liquidity.

---

# 268. Latency Arbitrage Simulation

Simulation can include:

```text
network_latency
feed_latency
processing_latency
execution_latency
```

No claim about real-world profitability is implied.

---

# 269. Market Impact Feedback

Large orders can alter:

```text
liquidity
spread
depth
price
```

through explicit market model.

---

# 270. Liquidity Crisis Simulation

```text
liquidity ↓
spread ↑
depth ↓
margin ↑
forced_sales ↑
```

Each arrow must be model-defined, not assumed universally.

---

# 271. Systemic Risk Interface

Exports:

```text
CrossOwnership
CounterpartyGraph
CollateralGraph
FundingGraph
LiquidityGraph
SettlementGraph
```

---

# 272. Contagion Simulation

```text
Default
→ MarginCall
→ Liquidation
→ PriceImpact
→ MarginCall
```

Simulation only.

---

# 273. AI Systemic Risk

AI can detect:

```text
concentration
shared collateral
common exposures
liquidity dependencies
```

and produce:

```text
RiskSignal
```

---

# 274. AI Market Research

AI can consume:

```text
market_data
trades
orderbook
news
research
fundamentals
```

but source provenance must remain attached.

---

# 275. AI Order Generation

AI-generated orders must be marked:

```text
origin = AI
model_id
model_version
decision_id
authority
```

---

# 276. AI Execution Audit

Every AI order must trace:

```text
AI Agent
→ Model
→ Input
→ Decision
→ Authority
→ Order
→ Execution
```

---

# 277. Model Versioning

Trading model lifecycle:

```text
Draft
→ Backtest
→ Paper
→ Validated
→ Approved
→ Live
→ Suspended
→ Retired
```

---

# 278. Model Rollback

Live model must support:

```text
rollback
```

to previous approved version.

---

# 279. AI Kill Criteria

Possible policy triggers:

```text
loss_limit
risk_limit
data_failure
model_drift
unexpected_order_rate
authority_change
```

---

# 280. Market Abuse Prevention

Controls:

```text
order_rate_limit
cancel_rate_limit
position_limit
self_trade_prevention
fat_finger
price_band
credit_limit
```

---

# 281. Self-Trade Prevention

System must detect:

```text
same beneficial/controlled participant
Buy
vs
Sell
```

according to venue policy.

---

# 282. Self-Match Policies

Possible:

```text
CancelOlder
CancelNewer
CancelBoth
Decrement
PreventBeforeMatch
```

---

# 283. Self-Trade Audit

Every prevention event should be observable.

---

# 284. Order Rate Limiting

Per:

```text
Participant
Account
Session
Instrument
Venue
IP/Endpoint
Agent
```

where applicable.

---

# 285. Session Isolation

A compromised client session must not automatically gain authority over other accounts.

---

# 286. API Gateway Boundary

External API:

```text
REST
WebSocket
FIX-like adapter
Native RPC
Binary protocol
```

are adapters over core order APIs.

---

# 287. Native Binary Protocol

For high performance:

```text
AXMTP
```

can define compact binary market messages.

---

# 288. Protocol Requirements

Messages support:

```text
version
sequence
timestamp
message_type
payload_length
checksum
```

---

# 289. Zero-Copy Decode

Native protocol should support direct views over buffers.

---

# 290. Network Failure

On disconnect:

```text
session invalidated
pending commands reconciled
open orders queried
state resynchronized
```

---

# 291. Order Reconciliation

After reconnect:

```text
ClientState
vs
MarketState
```

must reconcile.

---

# 292. Exactly-Once Semantics

Where technically possible:

```text
command_id
idempotency_key
sequence
```

provide exactly-once logical effect.

Transport itself need not guarantee exactly-once delivery.

---

# 293. Observability

Metrics:

```text
order_latency
matching_latency
feed_latency
execution_rate
cancel_rate
reject_rate
trade_rate
settlement_rate
settlement_failures
margin_calls
reconciliation_breaks
```

---

# 294. Percentile Latency

Report:

```text
p50
p90
p95
p99
p99.9
max
```

---

# 295. Distributed Tracing

Trace:

```text
Order
→ Gateway
→ Risk
→ OMS
→ Matching
→ Execution
→ Clearing
→ Settlement
→ Custody
```

---

# 296. Security Threat Model

Phải chống:

```text
OrderInjection
Replay
SessionHijack
PrivilegeEscalation
MarketDataPoisoning
OrderBookTampering
TimestampForgery
TradeForgery
SettlementReplay
CustodyTampering
AIPrivilegeEscalation
InsiderDataLeak
CrossTenantAccess
```

---

# 297. Cryptographic Integrity

Critical events có thể có:

```text
hash
signature
chain_hash
```

---

# 298. Tamper Evidence

Event log phải hỗ trợ phát hiện:

```text
deletion
modification
reordering
```

---

# 299. Immutable Audit

Historical:

```text
Order
Execution
Trade
Settlement
Custody
```

không overwrite.

Corrections tạo compensating events.

---

# 300. Compensation

Nếu event sai:

```text
OriginalEvent
→ CorrectionEvent
```

không sửa lịch sử.

---

# 301. Market State Machine

Global:

```text
BOOT
 ↓
INITIALIZING
 ↓
PRE_OPEN
 ↓
OPEN
 ↓
CLOSING
 ↓
CLOSED
```

Emergency:

```text
ANY
 ↓
HALTED
 ↓
RECOVERY
 ↓
OPEN/CLOSED
```

---

# 302. Exchange State

```text
Configured
→ Ready
→ Open
→ Halted
→ Closing
→ Closed
→ Recovery
```

---

# 303. Clearing State

```text
Open
→ Processing
→ Netting
→ Margining
→ ReadyForSettlement
→ Closed
```

---

# 304. Settlement State

```text
Open
→ Matching
→ Processing
→ Finalizing
→ Closed
```

---

# 305. Custody State

```text
Open
→ Reconciling
→ Frozen
→ Recovery
→ Open
```

---

# 306. Recovery Invariant

Không được resume trading nếu:

```text
order_book_checksum != expected
```

hoặc event sequence chưa reconcile.

---

# 307. Market Halt Invariant

Khi market halted:

```text
new_order
```

phải tuân thủ halt policy.

Một số cancel requests vẫn có thể được phép.

---

# 308. Market Data During Halt

Market status event phải được publish.

---

# 309. Settlement During Halt

Existing settlement obligations không mặc định bị hủy chỉ vì market halt.

Settlement policy quyết định.

---

# 310. Market Closure vs Suspension

```text
ScheduledClosure
≠
EmergencyHalt
```

---

# 311. Trading Calendar

Calendar phải hỗ trợ:

```text
timezone
holidays
special_session
early_close
late_open
emergency_close
```

---

# 312. Timezone

Mọi market timestamp phải giữ timezone/offset hoặc canonical UTC mapping.

---

# 313. Date Boundary

Không dùng local date một cách implicit cho settlement calculations.

---

# 314. Settlement Calendar

Settlement date được tính bằng:

```text
trade_date
+
settlement_rule
+
business_calendar
```

---

# 315. Market Fees

Fee schedule versioned theo:

```text
venue
participant
instrument
tier
effective_date
```

---

# 316. Participant Tiers

Có thể có:

```text
Retail
Professional
Institutional
MarketMaker
ClearingMember
LiquidityProvider
```

---

# 317. Fee Transparency

Mỗi trade phải có breakdown:

```text
gross_value
trading_fee
clearing_fee
settlement_fee
tax
other_fee
net_value
```

---

# 318. Trade Confirmation

```axiom
trade.confirmation()
```

phải chứa:

```text
trade_id
instrument
side
quantity
price
fees
timestamp
settlement_date
venue
```

---

# 319. Settlement Confirmation

```text
settlement_id
trade_id
asset_quantity
cash_amount
status
value_date
```

---

# 320. Custody Statement

```text
account
security
opening
movements
closing
encumbrances
```

---

# 321. Market Statement

Participant có thể query:

```text
orders
executions
trades
fees
positions
margin
settlements
```

---

# 322. Primary Market Issuance

```text
Offering
→ Subscription
→ Allocation
→ Issuance
→ Settlement
→ Listing
```

---

# 323. Issuance Invariant

Issued quantity phải conform với authorized issuance policy.

---

# 324. Corporate Action Supply Change

Split/bonus/merger có thể thay đổi quantity nhưng phải preserve event provenance.

---

# 325. Dividend

Dividend lifecycle:

```text
Declared
→ ExDate
→ RecordDate
→ PayDate
→ Settled
```

---

# 326. Bond Lifecycle

```text
Issued
→ Listed
→ Trading
→ Coupon
→ Matured
```

---

# 327. Bond Coupon

Coupon event phải tạo:

```text
Entitlement
PaymentInstruction
Settlement
```

---

# 328. Maturity

At maturity:

```text
Principal
+
FinalCoupon
```

được settled theo instrument rules.

---

# 329. Defaulted Security

```text
Normal
→ Distressed
→ Defaulted
→ Restructuring
→ Resolved
```

---

# 330. Restructuring

Có thể tạo:

```text
ExchangeOffer
NewSecurity
RecoveryValue
Settlement
```

---

# 331. Market Price Formation

Price formation thuộc market mechanism:

```text
Orders
Quotes
Liquidity
Matching
Auction
```

Không hard-code price model trong authoritative exchange.

---

# 332. Indicative Price

Auction engine có thể publish:

```text
IndicativePrice
IndicativeVolume
```

nhưng đây không phải final trade.

---

# 333. Market Depth Privacy

Venue policy quyết định depth visibility.

---

# 334. Order Book Snapshot

Snapshot phải chứa:

```text
sequence
timestamp
levels
checksum
```

---

# 335. Market Data Compression

Native codec support:

```text
delta encoding
varint
dictionary
batching
binary packing
```

---

# 336. Market Data Storage

Storage tiers:

```text
Hot
Warm
Cold
Archive
```

---

# 337. Historical Replay Storage

Historical data phải giữ:

```text
raw
normalized
derived
```

với lineage.

---

# 338. Tick Database Boundary

Market history có thể được lưu trong:

```text
AXDATA
AXANALYTICS
```

nhưng `AXMARKET` định nghĩa semantic schema.

---

# 339. Analytics

Native market analytics:

```text
VWAP
TWAP
OHLC
Spread
Depth
VolumeProfile
Volatility
Liquidity
OrderFlow
```

---

# 340. OHLC

```text
Open
High
Low
Close
Volume
```

được derived từ event data theo explicit interval.

---

# 341. Candles

Intervals:

```text
1s
1m
5m
15m
1h
1d
```

custom intervals được phép.

---

# 342. Data Aggregation

Aggregation phải deterministic và timezone-aware.

---

# 343. Market AI

AI services:

```text
market_summary
anomaly_detection
liquidity_forecast
execution_analysis
surveillance_assistance
market_simulation
```

---

# 344. AI Market Summary

Summary phải link tới source events.

---

# 345. AI Hallucination Control

AI output:

```text
Fact
Inference
Prediction
Simulation
```

phải phân biệt.

---

# 346. AI Data Access

Agent chỉ nhận market data theo capability.

---

# 347. Sensitive Market Data

Private order flow:

```text
Restricted
```

và không được leak sang public feed.

---

# 348. Insider Boundary

Material non-public information có thể được tagged:

```text
MNPI
```

Access control phải enforce.

---

# 349. Information Barrier

Organization có thể định nghĩa:

```text
Desk A
Desk B
```

không được chia sẻ restricted information.

---

# 350. Chinese-Wall Style Boundary

Implementation:

```text
InformationDomain
AccessPolicy
Exception
Audit
```

---

# 351. Cross-Desk Aggregation

Aggregated statistics có thể được phép mà không lộ raw restricted data.

---

# 352. Market Simulation Governance

Simulation data phải marked:

```text
simulation=true
```

---

# 353. Live/Simulation Firewall

Không được:

```text
simulation_order
→ live_market
```

nếu không có explicit conversion + authorization.

---

# 354. Paper Trading

Paper order:

```text
PaperOrder
PaperExecution
PaperTrade
```

không được tạo live settlement.

---

# 355. Sandbox

Sandbox market có:

```text
SyntheticCash
SyntheticAssets
SyntheticParticipants
```

---

# 356. Test Market

Axiom compiler phải hỗ trợ:

```text
market test_market {
    deterministic = true
}
```

---

# 357. Property-Based Matching Tests

Random order streams phải kiểm tra:

```text
no negative quantity
no duplicated execution
price priority
time priority
conservation
```

---

# 358. Fuzz Testing

Fuzz:

```text
order messages
market data
settlement instructions
corporate actions
reconnect sequences
```

---

# 359. Concurrency Tests

Test:

```text
parallel orders
cancel vs fill
modify vs fill
disconnect vs execution
settlement retry
```

---

# 360. Failure Injection

Inject:

```text
network loss
disk failure
CPU stall
clock skew
feed gap
duplicate message
corrupt snapshot
participant disconnect
```

---

# 361. Recovery Tests

Must prove:

```text
snapshot + replay
```

reconstructs equivalent authoritative state.

---

# 362. Security Tests

Minimum:

```text
unauthorized order
unauthorized cancel
session replay
capability escalation
tenant isolation
audit tampering
AI escalation
```

---

# 363. Settlement Tests

Test:

```text
DVP
FoP
partial
failed
retry
duplicate
reconciliation
```

---

# 364. Corporate Action Tests

Test:

```text
split
dividend
merger
rights
redemption
maturity
```

---

# 365. Market Data Tests

Test:

```text
sequence
gap
duplicate
out-of-order
replay
snapshot
```

---

# 366. Performance Targets

Target architecture:

```text
Order validation:
microsecond-class where platform permits

Matching:
deterministic low-latency hot path

Market-data fanout:
millions of events/sec capable on scalable hardware

Simulation:
massively parallel

Recovery:
bounded by snapshot interval + replay size
```

Actual SLA remains venue/profile specific.

---

# 367. Scalability

Must support:

```text
1 venue
→ 100 venues
→ thousands of venues
```

and:

```text
1 instrument
→ millions of instruments
```

through sharding.

---

# 368. Native Profiles

```text
AXMARKET_NONE
AXMARKET_CORE
AXMARKET_ORDER
AXMARKET_OMS
AXMARKET_EXCHANGE
AXMARKET_MATCH
AXMARKET_MARKETDATA
AXMARKET_BROKER
AXMARKET_CLEARING
AXMARKET_MARGIN
AXMARKET_SETTLEMENT
AXMARKET_CUSTODY
AXMARKET_CORPORATE_ACTION
AXMARKET_SURVEILLANCE
AXMARKET_DERIVATIVES
AXMARKET_SIMULATION
AXMARKET_AI
AXMARKET_GPU
AXMARKET_DISTRIBUTED
AXMARKET_WASM
AXMARKET_MOBILE
AXMARKET_FULL
```

---

# 369. Dependency Rule

`AXMARKET_CORE` không phụ thuộc:

```text
GUI
AI
GPU
Database
Network
```

---

# 370. Provider Interfaces

```text
MatchingProvider
MarketDataProvider
ClearingProvider
SettlementProvider
CustodyProvider
LedgerProvider
MarginProvider
SurveillanceProvider
ExecutionProvider
```

---

# 371. No Mandatory Third-Party Runtime

Core exchange/matching simulation phải có native implementation.

External integrations là adapters.

---

# 372. Native IR

Compiler IR:

```text
MARKET
VENUE
INSTRUMENT
SESSION
ORDER
ORDER_BOOK
MATCH
EXECUTION
TRADE
CLEAR
MARGIN
SETTLE
CUSTODY
CORPORATE_ACTION
MARKET_DATA
SURVEILLANCE
```

---

# 373. IR Example

```text
ORDER
  ↓
VALIDATE
  ↓
RISK_CHECK
  ↓
QUEUE
  ↓
MATCH
  ↓
EXECUTION
  ↓
TRADE
  ↓
CLEAR
  ↓
SETTLE
  ↓
CUSTODY_UPDATE
```

---

# 374. Static Compiler Checks

Compiler có thể phát hiện:

```text
invalid_order_type
invalid_tick_size
invalid_lot_size
missing_market
missing_account
missing_authority
invalid_settlement_mode
invalid_currency
illegal_capability
live_simulation_crossing
```

---

# 375. Compile-Time Capability Analysis

Ví dụ:

```axiom
submit_order(order)
```

yêu cầu:

```text
market.order.create
```

Compiler/runtime phải reject nếu capability absent.

---

# 376. Settlement Type Safety

```text
Cash
Security
Collateral
```

không được implicit cast.

---

# 377. Price Type Safety

```text
Price<USD>
Price<EUR>
```

không được arithmetic trực tiếp nếu currency mismatch.

---

# 378. Quantity Type Safety

```text
Quantity<ABC>
```

không được truyền vào:

```text
Quantity<XYZ>
```

---

# 379. Instrument Type Safety

Order phải reference instrument đúng market.

---

# 380. Side Type Safety

Buy/Sell semantics phải explicit.

---

# 381. Event Type Safety

```text
TradeEvent
```

không được giả mạo bằng generic event nếu API yêu cầu authoritative trade.

---

# 382. Authority Type

```axiom
Authority<TradeExecution>
Authority<SettlementFinalization>
```

là distinct capabilities.

---

# 383. Error Model

```text
MarketError
OrderError
MatchingError
ClearingError
MarginError
SettlementError
CustodyError
CorporateActionError
MarketDataError
SurveillanceError
AuthorizationError
RecoveryError
```

---

# 384. Recovery Errors

```text
SequenceGap
SnapshotMismatch
StateChecksumMismatch
ReplayFailure
DuplicateEvent
UnknownEvent
```

---

# 385. Market Data Errors

```text
FeedDisconnected
DecodeFailure
SequenceGap
StaleData
InvalidTimestamp
InvalidPrice
InvalidQuantity
```

---

# 386. Order Errors

```text
InvalidOrder
MarketClosed
InstrumentSuspended
PriceBandViolation
QuantityViolation
RiskLimitViolation
InsufficientMargin
Unauthorized
Duplicate
```

---

# 387. Clearing Errors

```text
InsufficientMargin
CollateralIneligible
MemberSuspended
NettingFailure
DefaultDetected
```

---

# 388. Settlement Errors

```text
InsufficientAsset
InsufficientCash
InstructionMismatch
DVPFailure
CounterpartyFailure
SettlementTimeout
```

---

# 389. Custody Errors

```text
HoldingMismatch
TransferForbidden
AccountFrozen
SecurityRestricted
DuplicateMovement
```

---

# 390. Test Target

BOOTSTRAP-693 yêu cầu tối thiểu:

**≥ 20.000 automated tests**

và:

**≥ 1.600 architecture invariants**

---

# 391. Core Invariants

### INV-MKT-001

```text
Order ≠ Trade
```

### INV-MKT-002

```text
Execution ≠ Settlement
```

### INV-MKT-003

```text
Clearing ≠ Settlement
```

### INV-MKT-004

```text
Quote ≠ Trade
```

### INV-MKT-005

```text
MarketData ≠ LegalTruth
```

### INV-MKT-006

Một execution không được tạo từ order không hợp lệ.

### INV-MKT-007

OrderBook không chứa order đã cancelled.

### INV-MKT-008

Matching phải tuân thủ venue matching policy.

### INV-MKT-009

Historical order/execution/trade không được overwrite.

### INV-MKT-010

Một settlement instruction không được final settle hai lần.

---

# 392. Clearing Invariants

```text
GrossObligations
→ NetObligations
```

phải preserve economic obligation.

Margin không được âm nếu policy cấm.

Collateral không thể được sử dụng đồng thời cho hai nghĩa vụ incompatible.

---

# 393. Settlement Invariants

```text
DVP:
asset_transfer ↔ cash_transfer
```

Không được tạo asset hoặc cash từ settlement ngoài explicit issuance/payment flows.

---

# 394. Custody Invariants

```text
opening
+ movements
+ corporate_actions
=
closing
```

theo cùng instrument/account/time context.

---

# 395. Market Data Invariants

Sequence:

```text
n
→ n+1
```

không được silently skip.

Gap phải được detect.

---

# 396. Matching Invariants

Không có:

```text
negative_fill
overfill
duplicate_fill
phantom_order
```

---

# 397. Order Invariants

```text
filled_quantity <= ordered_quantity
cancelled_quantity <= remaining_quantity
```

---

# 398. Price Invariants

Executed price phải conform với matching/auction rules.

---

# 399. Session Invariants

Order acceptance phải conform market session policy.

---

# 400. Authorization Invariants

```text
read
≠
trade
≠
clear
≠
settle
≠
custody_admin
```

---

# 401. AI Invariants

```text
AI cannot self-authorize
AI cannot self-escalate
AI cannot rewrite market rules
AI cannot erase trade history
AI cannot turn simulation into live order
AI cannot bypass pre-trade risk
AI cannot bypass settlement controls
```

---

# 402. Recovery Invariants

After recovery:

```text
state_hash(recovered)
=
state_hash(expected)
```

trong deterministic profile.

---

# 403. Replay Invariant

Replay cùng event stream phải produce equivalent authoritative state.

---

# 404. Cross-Domain Invariants

```text
AXINVEST OrderIntent
→ AXMARKET Order
```

phải preserve:

```text
portfolio
decision
authority
asset
quantity
constraints
```

---

# 405. Position Feedback

Sau settlement:

```text
AXMARKET Custody
→ AXINVEST Position
```

không được tạo position trước khi settlement state cho phép theo configured accounting semantics.

---

# 406. Banking Feedback

Cash movement:

```text
AXMARKET
→ AXBANKING
```

phải có settlement reference.

---

# 407. Insurance Feedback

Insurance investment positions:

```text
AXINSURANCE
→ AXINVEST
→ AXMARKET
→ AXINSURANCE
```

phải preserve investment provenance.

---

# 408. Civilization Feedback

```text
CAPITAL
 ↓
INVESTMENT
 ↓
MARKET
 ↓
OWNERSHIP
 ↓
PRODUCTION
 ↓
CASHFLOW
 ↓
CAPITAL
```

---

# 409. Global Financial Market Graph

```text
Investor
  ↓
Broker
  ↓
Exchange
  ↓
Clearing
  ↓
Settlement
  ↓
Custody
  ↓
Asset
  ↓
Issuer
  ↓
Economy
```

---

# 410. Civilization-Scale Market Runtime

Ở quy mô lớn:

```text
AXINVEST
      ↓
AXMARKET
      ↓
GlobalCapitalNetwork
      ↓
Banks
Funds
Insurance
Corporations
Governments
Households
AI Agents
      ↓
REAL ECONOMY
```

---

# 411. Final Architecture Contract

`AXMARKET` phải cung cấp native substrate cho:

```text
MARKET
ORDER
MATCH
TRADE
CLEAR
MARGIN
SETTLE
CUSTODY
CORPORATE ACTION
MARKET DATA
SURVEILLANCE
```

với các property:

```text
deterministic
auditable
capability-secured
fault-tolerant
replayable
low-latency
high-throughput
distributed
AI-compatible
simulation-safe
```

---

# 412. End-to-End Example

```axiom
investor H {
    portfolio = P
}

strategy S {
    target:
        Equity = 60%
        Bond = 30%
        Cash = 10%
}

rebalance P using S

    ↓

OrderIntent

    ↓

AXMARKET

    ↓

Order

    ↓

PreTradeRisk

    ↓

OrderBook

    ↓

MatchingEngine

    ↓

Execution

    ↓

Trade

    ↓

Clearing

    ↓

Margin

    ↓

SettlementInstruction

    ↓

DvP

    ↓

Custody

    ↓

PositionUpdate

    ↓

AXINVEST
```

---

# 413. Full Capital-Market Loop

```text
AXINVEST
   │
   │ OrderIntent
   ▼
AXMARKET
   │
   ├── ORDER
   ├── MATCH
   ├── TRADE
   ├── CLEAR
   ├── MARGIN
   ├── SETTLE
   └── CUSTODY
   │
   ▼
AXFINANCE / AXBANKING
   │
   ▼
AXINVEST
```

---

# 414. Final Boundary

`AXMARKET` **không** trở thành:

```text
general accounting system
general banking system
general insurance system
general investment optimizer
general legal system
general government system
```

Nó là:

> **native financial-market execution and post-trade infrastructure của Axiom.**

---

# 415. Completion Checklist

```text
[✓] Market model
[✓] Exchange
[✓] Venue
[✓] Broker
[✓] Dealer
[✓] Participant
[✓] Security
[✓] Listing
[✓] Account
[✓] Order
[✓] OMS
[✓] Execution
[✓] Trade
[✓] Order book
[✓] Matching engine
[✓] Auctions
[✓] Market sessions
[✓] Market data
[✓] Feed handling
[✓] Replay
[✓] Clearing
[✓] Margin
[✓] Collateral
[✓] Default management
[✓] Settlement
[✓] DvP
[✓] Custody
[✓] Securities lending
[✓] Corporate actions
[✓] Primary market
[✓] Secondary market
[✓] OTC
[✓] RFQ
[✓] Derivatives boundary
[✓] Market surveillance
[✓] AI surveillance
[✓] AI trading
[✓] Capability security
[✓] Recovery
[✓] Deterministic replay
[✓] Distributed scaling
[✓] GPU/FPGA provider boundary
[✓] Market simulation
[✓] Civilization-scale market graph
[✓] Native DSL
[✓] Native IR
[✓] Static capability validation
[✓] 20,000+ test target
[✓] 1,600+ invariant target
```

---

# 416. Architecture Chain After BOOTSTRAP-693

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
ORDER
    ↓
MATCHING
    ↓
TRADE
    ↓
CLEARING
    ↓
SETTLEMENT
    ↓
CUSTODY
```

Và vòng phản hồi:

```text
CUSTODY
   ↓
POSITION
   ↓
PORTFOLIO
   ↓
RISK
   ↓
INVESTMENT
   ↓
ORDER
   ↓
MARKET
```

---

# 417. Next Architecture Task

**BOOTSTRAP-694 — Native AI Civilization-Scale Accounting, General Ledger, Financial Statements, Cost Accounting, Management Accounting, Tax Accounting, Consolidation, Audit & Financial Truth Runtime 5.0**

Lớp này sẽ làm rõ một boundary rất quan trọng:

```text
AXMARKET
    = market events

AXBANKING
    = banking events

AXINSURANCE
    = insurance events

AXINVEST
    = investment decisions

        ↓

AXACCOUNTING
    = canonical financial representation
```

Từ đó Axiom sẽ có thể nối:

```text
REAL WORLD
   ↓
ECONOMIC EVENTS
   ↓
MARKET / BANK / INSURANCE / INVESTMENT
   ↓
ACCOUNTING
   ↓
FINANCIAL STATEMENTS
   ↓
ECONOMIC / CIVILIZATION SIMULATION
```
:::

Task tiếp theo đã được xác định: **BOOTSTRAP-694 — Accounting & Financial Truth Runtime 5.0**.