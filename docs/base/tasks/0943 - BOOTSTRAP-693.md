Tiếp tục với **BOOTSTRAP-693** — hoàn thiện lớp hạ tầng thị trường vốn nằm dưới `AXINVEST`, nhưng giữ ranh giới rõ với investment decision, banking, accounting và legal authority.

:::writing{variant="document" id="74106" title="BOOTSTRAP-693 — Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Order Management, Matching Engines, Clearing, Settlement, Custody, Market Data & Global Financial Market Infrastructure Runtime 5.0"}

# BOOTSTRAP-693
## Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Order Management, Matching Engines, Clearing, Settlement, Custody, Market Data & Global Financial Market Infrastructure Runtime 5.0

**Status:** Architecture Specification  
**Version:** 5.0  
**Namespace:** `AXMARKET`  
**Layer:** Financial Market Infrastructure  
**Previous:** `AXINVEST` — BOOTSTRAP-692  
**Next:** `AXCLEAR` — Global Clearing, Collateral, Margin, Netting & Systemic Settlement Runtime 5.0

---

# 1. Mục tiêu

`AXMARKET` là native runtime của Axiom cho hạ tầng thị trường vốn:

```text
market data
brokerage
order management
order routing
exchange
order book
matching engine
trading
market making
auction
price discovery
market surveillance
clearing boundary
settlement boundary
custody
corporate actions
securities lifecycle
reference data
market connectivity
```

Nó cung cấp lớp thực thi giữa:

```text
AXINVEST
    ↓
OrderIntent
    ↓
AXMARKET
    ↓
Financial Market
```

và:

```text
execution
→ clearing
→ settlement
→ custody
```

---

# 2. Nguyên tắc kiến trúc tối cao

## 2.1 Investment ≠ Trading

```text
AXINVEST
    = why / what allocation

AXMARKET
    = how / where / when execution occurs
```

---

## 2.2 Order Intent ≠ Order

```text
OrderIntent
    → strategic instruction

Order
    → executable market instruction
```

---

## 2.3 Order ≠ Execution

```text
Order
    ≠
Fill
```

Một order có thể:

```text
unfilled
partially filled
fully filled
cancelled
rejected
expired
```

---

## 2.4 Trade ≠ Settlement

```text
Trade
    = matched transaction

Settlement
    = final exchange of assets/cash
```

---

## 2.5 Custody ≠ Ownership Authority

Custody record là operational record.

Legal ownership authority có thể thuộc:

```text
AXLAW
registrar
central securities depository
jurisdiction-specific authority
```

---

## 2.6 Market Price ≠ Fundamental Value

Market price là kết quả của market process.

Không được coi:

```text
market_price == intrinsic_value
```

---

## 2.7 Market Data ≠ Market Truth

Một feed có thể:

```text
delayed
stale
estimated
incorrect
indicative
```

Runtime phải preserve provenance.

---

# 3. Scope

`AXMARKET` bao gồm:

```text
Securities
Markets
Trading Venues
Brokers
Dealers
Order Management
Order Routing
Order Books
Matching
Auctions
Executions
Trades
Market Data
Quotes
Ticks
Bars
Reference Data
Corporate Actions
Market Surveillance
Trading Limits
Market Sessions
Circuit Breakers
Clearing Boundary
Settlement Boundary
Custody
Reconciliation
Market Simulation
Trading Simulation
```

---

# 4. Explicit Non-Scope

Không sở hữu trực tiếp:

```text
investment objective
portfolio optimization
accounting ledger
bank monetary policy
legal ownership adjudication
tax policy
government policy
insurance underwriting
economic policy
```

Các domain:

```text
AXINVEST
AXFINANCE
AXBANKING
AXLAW
AXGOV
AXINSURANCE
AX671
```

---

# 5. Namespace

```axiom
namespace axmarket
```

Aliases:

```text
AXMARKET
AX.MARKET
AX.CAPITAL_MARKETS
```

---

# 6. Dependency Graph

```text
AXFINANCE
    │
    ├── AXBANKING
    ├── AXINVEST
    ├── AXINSURANCE
    ├── AXLAW
    ├── AXGOV
    │
    └── AXMARKET
           │
           ├── AXCLEAR
           ├── AXCUSTODY
           ├── AXAI
           └── AX671
```

`AXCLEAR` và các clearing primitives có thể được tách thành subsystem độc lập ở task tiếp theo.

---

# 7. Canonical Entity Model

```text
Market
Venue
Exchange
Broker
Dealer
Participant
Member
Issuer
Security
Instrument
Listing

Order
OrderIntent
OrderBook
Quote
Bid
Ask
Level
Execution
Trade
Auction
MarketSession

MarketData
Tick
Bar
Snapshot
Feed
ReferenceData

PositionReference
CustodyAccount
CustodyRecord
SettlementInstruction
CorporateAction

TradingRule
RiskLimit
PriceBand
CircuitBreaker

SurveillanceAlert
MarketEvent
MarketState
```

---

# 8. Market

```axiom
struct Market {
    id: MarketId
    name: String
    jurisdiction: Jurisdiction
    asset_classes: Set<AssetClass>
    trading_calendar: CalendarId
}
```

---

# 9. Venue

Venue là địa điểm/hệ thống nơi orders được xử lý.

```axiom
struct Venue {
    id: VenueId
    type: VenueType
    jurisdiction: Jurisdiction
    operator: EntityRef
    market_rules: MarketRuleSet
}
```

Types:

```text
Exchange
ATS
OTC
DarkPool
AuctionVenue
ElectronicVenue
DealerMarket
Internalizer
```

---

# 10. Exchange

```axiom
struct Exchange {
    venue: VenueId
    matching_model: MatchingModel
    trading_sessions: Set<TradingSession>
    listed_instruments: Set<SecurityId>
}
```

---

# 11. Broker

```axiom
struct Broker {
    id: BrokerId
    participant: ParticipantId
    execution_capabilities: Set<ExecutionCapability>
}
```

Broker chịu trách nhiệm routing/execution service theo authorization.

---

# 12. Dealer

Dealer có thể cung cấp:

```text
quotes
liquidity
principal execution
inventory
```

Principal trading phải được phân biệt với agency execution.

---

# 13. Market Participant

```axiom
struct Participant {
    id: ParticipantId
    type: ParticipantType
    permissions: CapabilitySet
    limits: TradingLimitSet
}
```

Types:

```text
Investor
Broker
Dealer
MarketMaker
ExchangeMember
Custodian
ClearingMember
Issuer
DataProvider
RegulatorReference
```

---

# 14. Security

`AXMARKET.Security` mô tả tradable instrument.

```axiom
struct Security {
    id: SecurityId
    issuer: IssuerId
    instrument: InstrumentType
    currency: Currency
    status: SecurityStatus
}
```

---

# 15. Listing

Một security có thể được list ở nhiều venue.

```axiom
struct Listing {
    security: SecurityId
    venue: VenueId
    symbol: Symbol
    tick_size: Decimal
    lot_size: Decimal
}
```

Do đó:

```text
Security ≠ Listing
```

---

# 16. Market Symbol

Symbol là venue-specific identifier.

```text
same security
    →
venue A symbol
venue B symbol
venue C symbol
```

Không được dùng symbol làm global identity.

---

# 17. Instrument Identity

Canonical identity:

```text
SecurityId
```

Reference identifiers:

```text
symbol
ISIN-like identifier
CUSIP-like identifier
vendor identifier
venue identifier
```

Vendor ID không được trở thành canonical identity.

---

# 18. Market Session

```axiom
struct TradingSession {
    id: SessionId
    open: Timestamp
    close: Timestamp
    phase: SessionPhase
}
```

Phases:

```text
PreOpen
OpeningAuction
Continuous
IntradayAuction
ClosingAuction
PostClose
Closed
Halted
```

---

# 19. Market State

```axiom
enum MarketState {
    Closed
    PreOpen
    Opening
    Continuous
    Auction
    Halted
    Closing
    PostClose
}
```

---

# 20. Order

```axiom
struct Order {
    id: OrderId
    participant: ParticipantId
    security: SecurityId
    side: Side
    quantity: Quantity
    order_type: OrderType
    time_in_force: TimeInForce
}
```

---

# 21. Order Types

Canonical:

```text
Market
Limit
Stop
StopLimit
Pegged
TrailingStop
Iceberg
Hidden
ImmediateOrCancel
FillOrKill
AuctionOnly
PostOnly
```

Venue-specific order types được extension.

---

# 22. Order Side

```axiom
enum Side {
    Buy
    Sell
}
```

Extensions có thể:

```text
SellShort
BuyToCover
```

nhưng short-selling semantics phải được policy/market rule định nghĩa.

---

# 23. Time In Force

```text
Day
GTC
GTD
IOC
FOK
Auction
Session
```

---

# 24. Order Lifecycle

```text
Created
    ↓
Accepted
    ↓
Routed
    ↓
Working
    ↓
PartiallyFilled
    ↓
Filled
```

Alternative branches:

```text
Rejected
Cancelled
Expired
Suspended
```

---

# 25. Order State Invariant

```text
filled_quantity + remaining_quantity = original_quantity
```

với các adjustment hợp lệ do corporate action phải được version hóa.

---

# 26. Order Intent Boundary

```text
AXINVEST.OrderIntent
          ↓
AXMARKET.Order
```

Transformation phải lưu:

```text
intent_id
order_id
mapping_policy
timestamp
authority
```

---

# 27. Order Routing

```axiom
struct RoutingPolicy {
    venues: OrderedSet<VenueId>
    price_priority: Bool
    liquidity_priority: Bool
    cost_priority: Bool
    latency_priority: Bool
}
```

Không được silently thay đổi routing policy.

---

# 28. Smart Order Routing

Input:

```text
quotes
depth
fees
latency
liquidity
venue rules
```

Output:

```text
venue allocation
```

---

# 29. Routing ≠ Investment Decision

Smart routing chỉ quyết định:

```text
where/how to execute
```

không quyết định:

```text
whether portfolio should own asset
```

---

# 30. Order Book

Canonical structure:

```text
Bid side
Ask side
```

Mỗi side:

```text
price level
→ ordered orders
```

---

# 31. Price-Time Priority

Default matching model:

```text
price priority
then
time priority
```

Nhưng matching model phải là venue configuration.

---

# 32. Matching Model

Supported:

```text
PriceTime
ProRata
SizeTime
Auction
ReferencePrice
CustomPolicy
```

---

# 33. Matching Engine

```axiom
struct MatchingEngine {
    venue: VenueId
    model: MatchingModel
    order_book: OrderBook
}
```

Hot path phải:

```text
lock-minimized
allocation-minimized
deterministic
high-throughput
```

---

# 34. Matching Determinism

Cùng:

```text
order sequence
market state
matching rules
```

phải tạo cùng:

```text
execution sequence
```

---

# 35. Execution

```axiom
struct Execution {
    id: ExecutionId
    order: OrderId
    quantity: Quantity
    price: Price
    timestamp: Timestamp
    venue: VenueId
}
```

---

# 36. Trade

```axiom
struct Trade {
    id: TradeId
    buy_execution: ExecutionId
    sell_execution: ExecutionId
    security: SecurityId
    quantity: Quantity
    price: Price
}
```

---

# 37. Execution ≠ Trade

Một execution record thuộc order participant.

Trade là matched transaction.

Runtime phải hỗ trợ audit mapping:

```text
Order
 ↓
Execution
 ↓
Trade
```

---

# 38. Trade Lifecycle

```text
Matched
    ↓
Confirmed
    ↓
ClearingPending
    ↓
Cleared
    ↓
SettlementPending
    ↓
Settled
```

Failure:

```text
Rejected
Failed
Cancelled
Defaulted
```

---

# 39. Market Data

Canonical:

```text
Tick
Quote
TradePrint
OrderBookSnapshot
OrderBookDelta
OHLCVBar
ReferenceData
CorporateAction
```

---

# 40. Quote

```axiom
struct Quote {
    bid: Price
    bid_size: Quantity
    ask: Price
    ask_size: Quantity
    timestamp: Timestamp
}
```

---

# 41. Tick

```axiom
struct Tick {
    price: Price
    quantity: Quantity
    timestamp: Timestamp
    venue: VenueId
}
```

---

# 42. Market Data Snapshot

```axiom
struct MarketSnapshot {
    timestamp: Timestamp
    securities: Collection<SecuritySnapshot>
}
```

Snapshot phải có:

```text
source
version
timestamp
quality
```

---

# 43. Market Data Feed

```axiom
trait MarketDataFeed {
    subscribe(...)
    snapshot(...)
    history(...)
}
```

---

# 44. Feed Quality

```text
Realtime
Delayed
Indicative
Estimated
Stale
Partial
Unavailable
```

---

# 45. Feed Provenance

```axiom
struct DataProvenance {
    source: SourceId
    received_at: Timestamp
    event_time: Timestamp
    sequence: UInt64?
    quality: DataQuality
}
```

---

# 46. Sequence Numbers

Streaming feed phải hỗ trợ:

```text
sequence
gap detection
replay
recovery
```

---

# 47. Market Data Gap

Nếu:

```text
seq = 101
seq = 103
```

runtime phải phát hiện:

```text
gap = 102
```

Không được giả định 102 không quan trọng.

---

# 48. Snapshot + Delta Recovery

```text
snapshot
+
delta stream
```

cho phép reconstruct order book.

---

# 49. Order Book Delta

```axiom
enum BookDeltaType {
    Add
    Modify
    Delete
    Trade
    Reset
}
```

---

# 50. Market Depth

Hỗ trợ:

```text
Level1
Level2
Level3
FullDepth
```

---

# 51. Historical Market Data

Storage format tối ưu:

```text
columnar
compressed
partitioned by date/security/venue
```

---

# 52. OHLCV

```axiom
struct Bar {
    open: Price
    high: Price
    low: Price
    close: Price
    volume: Quantity
    interval: Duration
}
```

---

# 53. Corporate Actions

Native:

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
Maturity
Delisting
```

---

# 54. Corporate Action Lifecycle

```text
Announced
    ↓
Validated
    ↓
Effective
    ↓
Processed
    ↓
Reconciled
```

---

# 55. Corporate Action Authority

AXMARKET processes market/custody representation.

Legal effect remains jurisdiction-dependent.

---

# 56. Custody

```axiom
struct CustodyAccount {
    id: CustodyAccountId
    owner: EntityRef
    custodian: ParticipantId
}
```

---

# 57. Custody Record

```axiom
struct CustodyRecord {
    security: SecurityId
    quantity: Quantity
    account: CustodyAccountId
    as_of: Timestamp
}
```

---

# 58. Custody ≠ Portfolio Position

Portfolio:

```text
investment perspective
```

Custody:

```text
asset safekeeping perspective
```

They require reconciliation.

---

# 59. Settlement Instruction

```axiom
struct SettlementInstruction {
    trade: TradeId
    deliver: AssetLeg
    receive: AssetLeg
    settlement_date: Date
    settlement_system: SettlementSystemId
}
```

---

# 60. Delivery Versus Payment

Core settlement semantic:

```text
DvP
```

means asset delivery and payment are linked according to settlement-system guarantees.

---

# 61. Settlement Boundary

`AXMARKET` tạo settlement instruction.

Actual clearing/settlement finality có thể thuộc:

```text
AXCLEAR
external CSD
payment system
central bank
```

---

# 62. Settlement Status

```text
Pending
Matched
PartiallySettled
Settled
Failed
Cancelled
```

---

# 63. Settlement Failure

Failure phải tạo event:

```text
SettlementFailed
```

và không tự động biến thành:

```text
TradeCancelled
```

trừ market rule cho phép.

---

# 64. Reconciliation

```text
Trade
 ↔
ClearingRecord
 ↔
SettlementRecord
 ↔
CustodyRecord
 ↔
CashRecord
```

---

# 65. Broker-Dealer Boundary

Broker có thể hoạt động:

```text
Agency
Principal
MatchedPrincipal
```

Mỗi mode phải explicit.

---

# 66. Agency Execution

```text
client
 ↓
broker
 ↓
venue
```

Broker không trở thành beneficial owner chỉ vì routing.

---

# 67. Principal Execution

```text
client
 ↔
dealer inventory
```

Inventory exposure phải được ghi nhận.

---

# 68. Market Maker

```axiom
struct MarketMaker {
    participant: ParticipantId
    instruments: Set<SecurityId>
    quote_policy: QuotePolicy
}
```

---

# 69. Quote Policy

```text
max_spread
min_size
inventory_limit
risk_limit
quote_refresh_rate
```

---

# 70. Market Making Engine

Hot path:

```text
market_data
    ↓
inventory
    ↓
risk
    ↓
quote_model
    ↓
bid/ask
```

---

# 71. Auction

Auction hỗ trợ:

```text
Opening
Closing
Periodic
Call
ReferencePrice
```

---

# 72. Auction State

```text
Collecting
Imbalance
PriceDiscovery
Crossing
Completed
Cancelled
```

---

# 73. Auction Imbalance

```axiom
struct AuctionImbalance {
    buy_quantity: Quantity
    sell_quantity: Quantity
    indicative_price: Price?
}
```

---

# 74. Price Discovery

Không được hard-code một cơ chế duy nhất.

Có thể dùng:

```text
continuous matching
auction
RFQ
dealer quote
reference price
```

---

# 75. RFQ

```axiom
struct RequestForQuote {
    security: SecurityId
    side: Side
    quantity: Quantity
    deadline: Timestamp
}
```

---

# 76. RFQ Lifecycle

```text
Created
→ Sent
→ Quoted
→ Selected
→ Executed
→ Expired
```

---

# 77. OTC Market

OTC trade có thể:

```text
quote
negotiate
confirm
clear
settle
```

Không yêu cầu public order book.

---

# 78. Trading Session Rules

Rules:

```text
tick size
lot size
price limits
short sale rules
trading hours
auction rules
order types
halt rules
```

---

# 79. Tick Size

```axiom
struct TickRule {
    price_range: Range<Price>
    tick_size: Decimal
}
```

---

# 80. Lot Size

```axiom
struct LotRule {
    minimum: Quantity
    increment: Quantity
}
```

---

# 81. Price Bands

```axiom
struct PriceBand {
    reference: Price
    lower: Price
    upper: Price
}
```

---

# 82. Circuit Breaker

```axiom
struct CircuitBreaker {
    trigger: Trigger
    action: HaltAction
    duration: Duration
}
```

---

# 83. Market Halt

```text
Normal
→ Halted
→ ReopeningAuction
→ Normal
```

Không tự động xóa orders trừ khi market rule yêu cầu.

---

# 84. Volatility Interrupt

Engine có thể trigger:

```text
volatility threshold
liquidity threshold
price gap
```

---

# 85. Trading Limits

```axiom
struct TradingLimit {
    participant: ParticipantId
    security: SecurityId?
    max_notional: Money?
    max_quantity: Quantity?
    max_order_rate: Rate?
}
```

---

# 86. Pre-Trade Risk

Trước khi accept order:

```text
permission
quantity
notional
price band
position limit
credit limit
short-sale rule
market state
```

---

# 87. Post-Trade Risk

Sau execution:

```text
position
exposure
notional
counterparty
margin reference
concentration
```

---

# 88. Risk Boundary

Market risk engine không thay thế:

```text
AXINVEST portfolio risk
AXBANKING credit risk
AXINSURANCE underwriting risk
```

Nó tập trung vào execution/market infrastructure risk.

---

# 89. Kill Switch

Capabilities:

```text
cancel_all_orders
halt_participant
halt_security
halt_market
disable_strategy
disable_route
```

Mỗi action cần authority.

---

# 90. Cancel-All

```axiom
cancel_all participant P
```

phải trả:

```text
requested
accepted
cancelled
already_executed
failed
```

---

# 91. Cancel/Replace

Order modification phải có atomic semantic nếu venue hỗ trợ.

Nếu không:

```text
cancel
+
new order
```

và phải ghi rõ hai event.

---

# 92. Order Priority Preservation

Modify order có thể làm mất time priority.

Điều này phải do venue rule quyết định, không phải hidden behavior.

---

# 93. Order Event Log

```text
OrderCreated
OrderAccepted
OrderRejected
OrderRouted
OrderRested
OrderModified
OrderPartiallyFilled
OrderFilled
OrderCancelled
OrderExpired
```

---

# 94. Execution Event Log

```text
ExecutionCreated
ExecutionConfirmed
TradeCreated
TradeCorrected
TradeCancelled
```

Trade correction phải tạo audit chain.

---

# 95. Trade Correction

Không sửa lịch sử trực tiếp.

```text
OriginalTrade
    ↓
Correction
    ↓
ReplacementRecord
```

---

# 96. Market Data Correction

Tương tự:

```text
OriginalObservation
    ↓
CorrectionEvent
```

không overwrite audit history.

---

# 97. Clock Model

Market infrastructure yêu cầu:

```text
event_time
exchange_time
gateway_time
receive_time
processing_time
```

---

# 98. Time Synchronization

Runtime phải hỗ trợ:

```text
monotonic clock
wall clock
logical sequence
```

Latency measurement không được dùng wall clock đơn thuần.

---

# 99. Latency

Metrics:

```text
wire_to_wire
gateway_latency
matching_latency
market_data_latency
ack_latency
execution_latency
```

---

# 100. Matching Engine Performance

Target architecture:

```text
sub-millisecond
```

cho optimized native hot paths trên hardware phù hợp.

Không coi đây là guarantee cho mọi deployment.

---

# 101. Allocation Discipline

Matching hot path:

```text
no GC
no hidden allocation
bounded memory
preallocated structures
```

---

# 102. Data Structures

Order book có thể sử dụng:

```text
price ladder
intrusive linked queues
radix structures
balanced trees
hash index
flat arrays
```

Implementation được benchmark theo market characteristics.

---

# 103. Cache Locality

Hot structures ưu tiên:

```text
contiguous memory
cache-aware layout
SoA/AoS tùy access pattern
```

---

# 104. Locking

Matching engine ưu tiên:

```text
single-writer partition
sharded books
lock-free queues
atomic sequence
```

thay vì global lock.

---

# 105. Deterministic Replay

Engine phải replay được:

```text
market snapshot
order stream
matching rules
clock sequence
```

để tái tạo execution.

---

# 106. Market Simulator

```axiom
simulate market {
    participants ...
    order_flow ...
    market_rules ...
}
```

Simulation không có production authority.

---

# 107. Synthetic Order Flow

AI/simulation có thể tạo:

```text
institutional
retail
market maker
liquidity taker
noise
```

Nhưng synthetic data phải đánh dấu:

```text
synthetic = true
```

---

# 108. Market Digital Twin

```text
ObservedMarket
PredictedMarket
SimulatedMarket
```

không được trộn lẫn.

---

# 109. Market Scenario

```axiom
scenario "liquidity_shock" {
    liquidity *= 0.25
    spread *= 3
}
```

---

# 110. Market Stress

Scenarios:

```text
FlashCrash
LiquidityFreeze
VolatilitySpike
ExchangeOutage
FeedFailure
CounterpartyDefault
SettlementFailure
CyberIncident
CurrencyShock
RateShock
```

---

# 111. Exchange Outage

Fallback:

```text
VenueUnavailable
```

Smart routing có thể route sang venue khác nếu policy cho phép.

Không tự giả định venue thay thế tương đương.

---

# 112. Market Connectivity

Adapters:

```text
FIX-like
WebSocket
BinaryFeed
NativeTCP
UDP
QUIC
```

Protocol-specific adapters không phải core semantic model.

---

# 113. Protocol Abstraction

```axiom
trait MarketTransport {
    connect(...)
    send(...)
    receive(...)
    close(...)
}
```

---

# 114. FIX Boundary

FIX-style messages map vào:

```text
Order
Execution
Cancel
Replace
Trade
ReferenceData
```

---

# 115. Native Binary Protocol

Axiom có thể cung cấp:

```text
AXMTP
```

cho low-latency internal transport.

Properties:

```text
binary
versioned
length-prefixed
zero-copy compatible
schema-aware
```

---

# 116. Schema Evolution

Messages có:

```text
version
optional fields
compatibility rules
```

Unknown fields có thể được preserved khi forward-compatible.

---

# 117. Market Reference Data

Reference data:

```text
Security
Issuer
Listing
Currency
Venue
TradingCalendar
TickRule
LotRule
CorporateAction
```

---

# 118. Reference Data Authority

Mỗi record phải có:

```text
source
effective_from
effective_to
version
```

---

# 119. Delisting

Security lifecycle:

```text
Active
Suspended
DelistedPending
Delisted
Matured
Redeemed
```

---

# 120. Listing Lifecycle

```text
Applied
Listed
Suspended
Resumed
DelistingPending
Delisted
```

Security có thể tồn tại sau khi listing kết thúc.

---

# 121. Issuance

AXMARKET có thể represent:

```text
IPO
SecondaryOffering
BondIssue
RightsIssue
PrivatePlacement
```

nhưng legal issuance authority thuộc issuer/legal infrastructure.

---

# 122. IPO Workflow

```text
Issuer
 ↓
ListingApplication
 ↓
Validation
 ↓
Offering
 ↓
Allocation
 ↓
Listing
 ↓
Trading
```

---

# 123. Primary Market

Primary market flow:

```text
Issuer
    ↓
Offering
    ↓
Investor
```

Secondary:

```text
Investor
    ↔
Investor
```

---

# 124. Allocation Engine

Primary offering có thể có:

```text
pro-rata
auction
book-building
fixed allocation
lottery
```

Rules phải explicit.

---

# 125. Book Building

```text
IndicationOfInterest
    ↓
DemandBook
    ↓
PriceDiscovery
    ↓
Allocation
```

---

# 126. Secondary Trading

```text
Order
→ Matching
→ Execution
→ Trade
```

---

# 127. Market Maker Inventory

Inventory:

```text
owned_position
reserved_position
available_position
```

không đồng nhất với customer custody.

---

# 128. Short Selling

Nếu venue cho phép:

```text
Locate
Borrow
ShortOrder
Cover
Return
```

Short authorization phải explicit.

---

# 129. Borrow Record

```axiom
struct SecuritiesBorrow {
    security: SecurityId
    quantity: Quantity
    lender: ParticipantId
    borrower: ParticipantId
    fee: Rate
}
```

---

# 130. Securities Lending

Lifecycle:

```text
Requested
Matched
Delivered
Active
Returned
Failed
```

---

# 131. Repo Boundary

Có thể represent:

```text
Repo
ReverseRepo
Collateral
Haircut
Maturity
```

Nhưng monetary/treasury semantics tích hợp với `AXBANKING` và `AXFINANCE`.

---

# 132. Derivatives

AXMARKET chỉ cung cấp market/execution representation:

```text
Future
Option
Forward
SwapReference
```

Valuation/risk có thể sử dụng `AXINVEST` / finance engines.

---

# 133. Options

Market semantics:

```text
strike
expiry
exercise_style
contract_size
underlying
```

---

# 134. Futures

```text
contract_size
expiry
delivery_rule
tick_size
margin_reference
```

Margin/clearing sâu thuộc `AXCLEAR`.

---

# 135. Market Surveillance

Surveillance không tự kết luận wrongdoing.

Nó tạo:

```text
signal
alert
case_reference
```

---

# 136. Surveillance Signals

```text
UnusualVolume
PriceSpike
LayeringPattern
SpoofingPattern
WashTradePattern
QuoteBurst
OrderCancellationBurst
CrossVenueAnomaly
InsiderTimingSignal
```

Các signal là detection output, không phải adjudication.

---

# 137. Surveillance Case

```axiom
struct SurveillanceCase {
    id: CaseId
    signals: Set<SurveillanceSignal>
    evidence: Set<EvidenceRef>
    status: CaseStatus
}
```

---

# 138. Case Lifecycle

```text
Detected
→ Triaged
→ Investigating
→ Escalated
→ Resolved
→ Closed
```

---

# 139. Evidence Preservation

Surveillance evidence phải immutable/versioned.

```text
market_data_snapshot
order_events
execution_events
participant_context
```

---

# 140. Market Abuse Boundary

AXMARKET phát hiện pattern.

```text
pattern ≠ confirmed violation
```

Legal/regulatory adjudication:

```text
AXLAW / authorized authority
```

---

# 141. Participant Reputation

Market participant metrics không được biến thành universal human ranking.

Chỉ có:

```text
market_participant_metric
```

trong scope market.

---

# 142. AI Surveillance

AI có thể:

```text
detect anomalies
cluster behavior
prioritize alerts
summarize evidence
```

Không tự đưa ra legal verdict.

---

# 143. AI Execution

AI execution strategy phải có:

```text
strategy_id
authority
limits
risk_policy
kill_switch
audit
```

---

# 144. Execution Algorithm

Native algorithms:

```text
TWAP
VWAP
POV
ImplementationShortfall
ArrivalPrice
Iceberg
Adaptive
LiquiditySeeking
AuctionSeeking
```

---

# 145. Algorithmic Trading Boundary

Execution algorithm chỉ tối ưu:

```text
execution objective
```

theo order/mandate.

Nó không tự tạo investment thesis.

---

# 146. Execution Objective

```axiom
enum ExecutionObjective {
    MinimizeCost
    MinimizeMarketImpact
    MaximizeFill
    MinimizeTime
    PriceImprovement
    BenchmarkTracking
}
```

---

# 147. Execution Analytics

```text
slippage
implementation_shortfall
spread_cost
market_impact
fill_rate
latency
venue_quality
```

---

# 148. Best Execution Metadata

Không hard-code một định nghĩa pháp lý toàn cầu.

Runtime lưu:

```text
execution_policy
comparison_benchmark
venues_considered
costs
fills
timestamp
```

---

# 149. Venue Analytics

```text
fill_rate
latency
spread
depth
rejection_rate
execution_cost
market_impact
```

---

# 150. Market Quality

Metrics:

```text
spread
depth
resiliency
volatility
turnover
price_impact
fill_probability
```

---

# 151. Liquidity

Canonical liquidity dimensions:

```text
immediacy
depth
breadth
resiliency
transaction_cost
```

---

# 152. Liquidity Score

Nếu dùng score nội bộ:

```text
LiquidityMetric
```

phải giữ methodology và input.

Không coi score là objective truth.

---

# 153. Market Stress Propagation

```text
venue outage
 ↓
liquidity reduction
 ↓
spread widening
 ↓
execution cost
 ↓
portfolio impact
```

---

# 154. Cross-Venue Arbitrage Representation

```text
same_security
venue_A_price
venue_B_price
transaction_cost
latency
```

Chỉ là opportunity representation, không guarantee profit.

---

# 155. Cross-Venue Consistency

Reference engine có thể phát hiện:

```text
price divergence
```

nhưng phải xét:

```text
latency
fees
currency
settlement
security equivalence
```

---

# 156. Security Equivalence

Hai instruments chỉ được coi là equivalent nếu:

```text
canonical_security
rights
currency
corporate_action
venue rules
```

phù hợp.

---

# 157. Currency Conversion

Market data có thể cần:

```text
FXRate
FXTimestamp
FXSource
```

Không dùng FX rate không rõ timestamp trong historical replay.

---

# 158. Market Calendar

Calendar hỗ trợ:

```text
holidays
early close
late open
auction schedule
timezone
DST
```

---

# 159. Timezone

Venue timezone phải explicit.

Không dùng local machine timezone làm market timezone.

---

# 160. Settlement Calendar

Trading calendar ≠ settlement calendar.

---

# 161. Business Day

Business-day rules phải được domain/calendar provider định nghĩa.

---

# 162. Custody Reconciliation

```axiom
reconcile {
    portfolio
    custody
    settlement
}
```

Output:

```text
matched
difference
missing_trade
missing_cash
corporate_action_difference
```

---

# 163. Cash Reconciliation

```text
Trade proceeds
↔
settlement cash
↔
bank record
```

---

# 164. Asset Reconciliation

```text
expected position
↔
custodian position
```

---

# 165. Reconciliation Invariant

Không được tự động sửa external authority record từ internal estimate.

---

# 166. Settlement Netting Boundary

Netting:

```text
gross obligation
→ net obligation
```

có thể được represented.

Global clearing/netting engine được tách thành `AXCLEAR`.

---

# 167. Collateral Boundary

Market có thể reference:

```text
collateral_required
```

nhưng collateral optimization/margin engine chuyên sâu thuộc `AXCLEAR`.

---

# 168. Margin Reference

```axiom
struct MarginRequirement {
    initial: Money
    maintenance: Money
    methodology: MarginMethod
}
```

---

# 169. Clearing Reference

```axiom
struct ClearingReference {
    trade: TradeId
    clearing_member: ParticipantId
    status: ClearingStatus
}
```

---

# 170. Settlement Finality

`Settled` chỉ được phát ra khi settlement authority xác nhận finality theo settlement system.

---

# 171. Market Failure Semantics

Không được:

```text
timeout → assume settled
```

Phải:

```text
timeout → Pending/Unknown
```

cho tới khi authoritative confirmation.

---

# 172. Exactly-Once Illusion

Distributed market infrastructure không giả định network request exactly-once.

Thiết kế:

```text
idempotency
sequence
deduplication
reconciliation
```

---

# 173. Order Idempotency

Mỗi externally submitted order phải có:

```text
client_order_id
idempotency_key
```

---

# 174. Duplicate Prevention

Nếu request lặp:

```text
same idempotency key
```

runtime trả cùng logical order state.

---

# 175. Disaster Recovery

Recovery layers:

```text
hot standby
warm standby
snapshot
event replay
market-data replay
order replay
```

---

# 176. Matching Engine Recovery

Matching engine phải có:

```text
state snapshot
order sequence
event log
```

để phục hồi deterministic.

---

# 177. Recovery Invariant

Không được tạo duplicate execution sau recovery.

---

# 178. Fault Domains

Tách:

```text
market
venue
instrument
participant
matching shard
market-data feed
gateway
```

---

# 179. Multi-Venue Deployment

```text
Venue A
Venue B
Venue C
```

có thể chạy độc lập.

Một venue failure không nhất thiết làm toàn bộ market runtime dừng.

---

# 180. Distributed Market Data

```text
Feed
 ↓
Normalizer
 ↓
Sequencer
 ↓
Distribution
 ↓
Subscribers
```

---

# 181. Market Data Normalization

Vendor-specific:

```text
symbol
timestamp
price
quantity
```

→ canonical:

```text
SecurityId
Timestamp
Price
Quantity
```

---

# 182. Data Normalization Rule

Normalization không được làm mất:

```text
source_id
raw_identifier
raw_timestamp
raw_value
```

nếu retention policy yêu cầu.

---

# 183. Market Data Cache

Có thể cache:

```text
L1
L2
L3
historical bars
reference data
```

---

# 184. Hot/Cold Storage

```text
hot:
realtime books

warm:
recent ticks

cold:
historical data
```

---

# 185. Compression

Native compression cho:

```text
ticks
order events
book deltas
historical bars
```

phải hỗ trợ streaming decompression.

---

# 186. Zero-Copy Market Feed

API:

```axiom
on_market_data(view<Tick>)
```

cho phép zero-copy processing.

---

# 187. Backpressure

Subscribers chậm phải có policy:

```text
block
drop_old
drop_new
buffer
disconnect
snapshot_resync
```

---

# 188. Snapshot Resync

Nếu consumer mất quá nhiều deltas:

```text
consumer
→ request snapshot
→ receive snapshot
→ resume from sequence
```

---

# 189. Security

Capabilities:

```text
market.read
market.write

marketdata.read
marketdata.subscribe

order.create
order.modify
order.cancel
order.read

execution.read
trade.read

venue.admin
matching.admin

risk.pretrade
risk.posttrade

custody.read
custody.write

settlement.read
settlement.instruct

surveillance.read
surveillance.case

algorithm.execute
algorithm.admin

kill_switch
market.halt
admin
```

---

# 190. Capability Isolation

Ví dụ:

```text
marketdata.read
```

không tự cấp:

```text
order.create
```

---

# 191. Market Maker Capability

```text
quote.create
quote.cancel
inventory.read
inventory.manage
```

---

# 192. Surveillance Capability

```text
surveillance.read
surveillance.investigate
```

không cấp:

```text
legal.adjudicate
```

---

# 193. Admin Separation

```text
exchange_admin
matching_admin
risk_admin
surveillance_admin
custody_admin
settlement_admin
```

không nhất thiết là cùng một principal.

---

# 194. Privileged Operations

Các operation:

```text
halt_market
cancel_all
modify_matching_rule
change_tick_size
restore_snapshot
correct_trade
```

phải:

```text
authenticated
authorized
audited
```

---

# 195. Immutable Audit

Privileged action:

```text
actor
authority
reason
timestamp
before
after
```

---

# 196. Rule Versioning

Matching rules phải versioned:

```text
MarketRuleSetV1
MarketRuleSetV2
```

Một trade phải biết nó được match dưới rule version nào.

---

# 197. Rule Effective Time

```axiom
rule effective_from
rule effective_to
```

Replay historical market cần dùng đúng rule tại thời điểm đó.

---

# 198. Market Configuration

Configuration:

```text
tick
lot
sessions
order_types
matching
price_bands
halt_rules
fees
```

phải là data/configuration, không hard-code vào compiler.

---

# 199. Fee Model

```text
maker_fee
taker_fee
routing_fee
exchange_fee
regulatory_fee_reference
```

---

# 200. Fee Calculation

Fee engine:

```text
fee(order, execution, venue, policy)
```

phải deterministic.

---

# 201. Rebate

Market maker rebates phải được represent rõ:

```text
rebate
```

không được trộn với negative fee mà mất semantic distinction.

---

# 202. Transaction Cost

Execution analytics:

```text
explicit_cost
implicit_cost
market_impact
opportunity_cost
```

---

# 203. Trade Cost Analysis

```axiom
tca order O
```

Output:

```text
arrival_price
execution_vwap
slippage
impact
fees
latency
venue
```

---

# 204. Benchmark Execution

Execution benchmark:

```text
Arrival
VWAP
TWAP
Close
ImplementationShortfall
```

---

# 205. Market Data Benchmark

Historical replay phải lưu:

```text
raw_feed
normalized_feed
processed_feed
```

để debugging.

---

# 206. AI Market Agent

Có thể:

```text
monitor
route
summarize
detect
simulate
optimize execution
```

Nhưng authority phải explicit.

---

# 207. Autonomous Trading

```axiom
autonomous_strategy {
    authority: execution_only
    max_order_value: ...
    max_position: ...
    max_daily_loss: ...
    kill_switch: ...
}
```

---

# 208. Strategy Sandbox

AI trading strategy phải chạy sandbox trước khi production.

```text
Research
→ Backtest
→ Simulation
→ PaperTrading
→ Approval
→ Production
```

---

# 209. Paper Trading

```text
market data = real
execution = simulated
```

Phải đánh dấu:

```text
simulation = true
```

---

# 210. Production Boundary

Paper trading không thể mutate production custody/ledger.

---

# 211. Strategy Version

```text
Strategy
StrategyVersion
Deployment
```

Mỗi live execution phải reference strategy version.

---

# 212. Strategy Rollback

Có thể:

```text
disable current
activate previous
```

---

# 213. Strategy Monitoring

Metrics:

```text
PnL
drawdown
fill_rate
slippage
latency
risk
order_rejection
market_impact
```

---

# 214. AI Model Monitoring

```text
prediction drift
execution drift
data drift
latency
error rate
```

---

# 215. Market Simulation

Simulation layers:

```text
agent
order flow
market microstructure
matching
execution
settlement
```

---

# 216. Agent-Based Market Model

Participants:

```text
retail
institution
market maker
fund
broker
dealer
AI agent
```

Không được dùng simulated participant như real participant.

---

# 217. Simulation Identity

```axiom
Participant {
    environment: Production | Simulation
}
```

---

# 218. Simulation Safety

Simulation capability không có quyền:

```text
production.order.create
production.market.halt
production.settlement.instruct
```

---

# 219. Market Digital Twin

```text
real_market
    ↓
observations
    ↓
market_twin
    ↓
simulation
```

---

# 220. Scenario Comparison

```axiom
compare_market {
    baseline
    stress
    alternative
}
```

Output:

```text
liquidity
spread
volume
price
failure
settlement
```

---

# 221. Market Resilience

Metrics:

```text
recovery_time
liquidity_recovery
order_recovery
feed_recovery
settlement_recovery
```

---

# 222. Cyber Resilience

Events:

```text
FeedSpoof
GatewayCompromise
CredentialCompromise
MessageReplay
SequenceManipulation
```

Security engine phải detect và isolate.

---

# 223. Message Replay Protection

Messages có:

```text
sequence
timestamp
nonce
session
```

---

# 224. Authentication

Market connections có:

```text
mutual authentication
certificate
key
session identity
capability
```

Crypto primitives lấy từ Axiom security layer.

---

# 225. Confidentiality

Private order flow có thể cần:

```text
encrypted transport
encrypted storage
access controls
```

---

# 226. Order Privacy

Order book visibility:

```text
Public
ParticipantOnly
VenueOnly
Hidden
```

theo market rules.

---

# 227. Hidden Order

Hidden liquidity phải có explicit semantics.

Không được giả định:

```text
hidden = nonexistent
```

---

# 228. Dark Venue

Dark venue không public full depth.

Market data exposure phải respect venue policy.

---

# 229. Internalization

Broker có thể match internally nếu policy/rules cho phép.

```text
client order
→ internal liquidity
```

Phải ghi execution venue/mode.

---

# 230. Cross Matching

Cross trade:

```text
buy client
↔
sell client
```

phải qua applicable rules.

---

# 231. Block Trade

```text
large_order
→ negotiated_execution
```

Có thể bypass continuous order book nhưng vẫn phải audit.

---

# 232. Large Order Fragmentation

Execution algorithm có thể:

```text
parent order
→ child orders
```

Mapping phải immutable:

```text
parent_id
child_id
```

---

# 233. Parent/Child Order Graph

```text
ParentOrder
├── ChildOrder A
├── ChildOrder B
└── ChildOrder C
```

---

# 234. Execution Aggregation

Multiple child fills:

```text
ExecutionSet
→ parent completion
```

---

# 235. Partial Fill

Order state:

```text
original = 1000
filled = 350
remaining = 650
```

Invariant bắt buộc.

---

# 236. Cancel Remaining

```text
filled = immutable
remaining = cancelable
```

---

# 237. Market Order Protection

Market order có thể cần:

```text
max_slippage
price_protection
notional_limit
```

---

# 238. Risk Check Pipeline

```text
Order
 ↓
Identity
 ↓
Authorization
 ↓
Instrument Validation
 ↓
Market State
 ↓
Price/Quantity Rules
 ↓
Pre-Trade Risk
 ↓
Credit/Cash
 ↓
Matching/Routing
```

---

# 239. Reject Reason

Canonical:

```text
Unauthorized
InvalidSecurity
InvalidQuantity
PriceBandViolation
MarketClosed
RiskLimitExceeded
InsufficientFunds
InsufficientBorrow
InvalidOrderType
DuplicateOrder
VenueUnavailable
```

---

# 240. No Silent Rejection

Every rejected order phải có:

```text
reason_code
timestamp
rule_version
```

---

# 241. Market Event Bus

Events:

```text
MarketOpened
MarketClosed
MarketHalted
SecurityListed
SecuritySuspended
PriceBandChanged
OrderAccepted
OrderRejected
ExecutionCreated
TradeCreated
SettlementCompleted
CorporateActionEffective
```

---

# 242. Event Ordering

Trong một venue:

```text
sequence number
```

là canonical event order.

---

# 243. Distributed Event Ordering

Cross-venue global ordering không được giả định nếu không có common sequencing authority.

---

# 244. Market Clock

Mỗi venue có:

```text
venue_clock
```

Global analytics có:

```text
normalized_time
```

---

# 245. Historical Replay

```axiom
replay market M {
    date: ...
    rules: historical
    data: raw
}
```

Output phải deterministic.

---

# 246. Replay Use Cases

```text
incident analysis
strategy testing
surveillance
debugging
compliance audit
market research
```

---

# 247. Market Data API

```axiom
market.price(security)
market.quote(security)
market.book(security)
market.trades(security)
market.history(security, range)
```

---

# 248. Trading API

```axiom
order.create(...)
order.modify(...)
order.cancel(...)
order.status(...)
```

---

# 249. Execution API

```axiom
execution.list(order)
execution.metrics(order)
```

---

# 250. Market Simulation API

```axiom
simulate.market(...)
simulate.order_flow(...)
simulate.execution(...)
```

---

# 251. Custody API

```axiom
custody.position(...)
custody.reconcile(...)
```

---

# 252. Settlement API

```axiom
settlement.instruction(...)
settlement.status(...)
```

---

# 253. Corporate Action API

```axiom
corporate_action.list(...)
corporate_action.status(...)
```

---

# 254. Surveillance API

```axiom
surveillance.signal(...)
surveillance.case(...)
surveillance.evidence(...)
```

---

# 255. Native IR

Compiler/runtime IR:

```text
MKT_SECURITY
MKT_LISTING
MKT_ORDER
MKT_ORDER_MODIFY
MKT_ORDER_CANCEL
MKT_ROUTE
MKT_BOOK
MKT_MATCH
MKT_EXECUTION
MKT_TRADE
MKT_QUOTE
MKT_TICK
MKT_AUCTION
MKT_SETTLEMENT
MKT_CUSTODY
MKT_CORPORATE_ACTION
MKT_SURVEILLANCE
MKT_SIMULATION
```

---

# 256. Matching IR

```text
MKT_BOOK_INSERT
MKT_BOOK_UPDATE
MKT_BOOK_REMOVE
MKT_MATCH
MKT_CROSS
MKT_AUCTION_CLEAR
```

---

# 257. Market Data IR

```text
MKT_TICK
MKT_QUOTE
MKT_BOOK_DELTA
MKT_BOOK_SNAPSHOT
MKT_TRADE_PRINT
MKT_BAR
```

---

# 258. Order Compiler

DSL:

```axiom
buy 100 AAPL
    limit 220
    tif DAY
```

compile:

```text
AST
→ Order IR
→ validation
→ venue-specific representation
```

---

# 259. Execution DSL

```axiom
execute parent_order {
    algorithm: VWAP
    horizon: 30m
    max_impact: 0.002
}
```

---

# 260. Venue DSL

```axiom
venue "X" {
    tick_size 0.01
    lot_size 1
    matching price_time

    session {
        open 09:00
        close 15:00
    }
}
```

---

# 261. Matching DSL

```axiom
matching {
    priority price_time
    self_trade_prevention cancel_aggressor
}
```

---

# 262. Self-Trade Prevention

Modes:

```text
CancelAggressor
CancelResting
DecrementBoth
Reject
```

---

# 263. Self-Trade Invariant

Nếu policy cấm self-trade:

```text
same beneficial/control identity
```

phải không được match trái phép.

Identity determination thuộc authorized identity service.

---

# 264. Market Abuse Detection

Signals không được mutate order history.

---

# 265. Surveillance Data Retention

Retention policy phải configurable:

```text
market rule
legal requirement
institution policy
```

---

# 266. Audit Storage

Critical records nên hỗ trợ:

```text
append-only
hash chaining
content addressing
tamper evidence
```

---

# 267. Market Snapshot Hash

```axiom
hash(snapshot)
```

cho phép chứng minh snapshot identity.

---

# 268. Trade Record Hash

```axiom
hash(trade + rule_version + event_sequence)
```

---

# 269. Integrity Chain

```text
MarketEvent
 → hash
 → next_event
 → hash
```

---

# 270. Data Lineage

```text
raw_feed
 ↓
normalized_tick
 ↓
quote
 ↓
order_book
 ↓
execution
 ↓
trade
 ↓
settlement
```

---

# 271. Market Data Correction Lineage

```text
raw
 ↓
correction
 ↓
normalized
```

không xóa raw record.

---

# 272. Accounting Integration

Trade event:

```text
AXMARKET
 ↓
AXFINANCE
```

để tạo accounting event.

AXMARKET không tự trở thành general ledger.

---

# 273. Banking Integration

Cash settlement:

```text
AXMARKET
 ↓
AXBANKING
```

---

# 274. Investment Integration

```text
AXINVEST
 ↓
OrderIntent
 ↓
AXMARKET
```

Execution feedback:

```text
AXMARKET
 ↓
AXINVEST
```

---

# 275. Insurance Integration

Insurer investment portfolio:

```text
AXINSURANCE
 ↔
AXINVEST
 ↔
AXMARKET
```

---

# 276. Economic Integration

```text
AXMARKET
 ↓
AXINVEST
 ↓
AX671
```

Market prices can become inputs to economic simulation, with timestamp/provenance.

---

# 277. Government/Regulatory Boundary

Government/regulator data có thể được represent:

```text
rule
notice
market_status
regulatory_reference
```

nhưng runtime không tự biến thành legal authority.

---

# 278. Market Governance

Venue governance entities:

```text
Operator
Administrator
RuleAuthority
RiskAuthority
SurveillanceAuthority
```

---

# 279. Rule Change

Rule changes phải:

```text
proposal
validation
approval
effective_time
deployment
audit
```

---

# 280. Emergency Rule Change

Emergency change phải có:

```text
emergency_authority
reason
timestamp
scope
expiry
```

---

# 281. Market Shutdown

```axiom
shutdown market M
```

không đồng nghĩa:

```text
cancel all trades
```

Settlement/position state vẫn tồn tại.

---

# 282. Resume Market

```text
Halted
→ Reconciliation
→ PreOpen
→ Auction
→ Continuous
```

---

# 283. Participant Suspension

```text
Active
→ Suspended
→ ReinstatementReview
→ Active
```

---

# 284. Security Suspension

Security có thể bị suspend trong một venue nhưng vẫn active ở venue khác.

---

# 285. Cross-Market Identity

```text
Security
├── Listing A
├── Listing B
└── Listing C
```

---

# 286. Cross-Market Corporate Actions

Một corporate action có thể affect nhiều listings.

Runtime phải map:

```text
security
→ listings
→ positions
→ custody records
```

---

# 287. Fractional Ownership

Nếu instrument hỗ trợ:

```text
quantity = Decimal
```

Nếu không:

```text
lot_size
```

enforced.

---

# 288. Tokenized Securities

Tokenized instrument vẫn phải có:

```text
SecurityId
rights
issuer
legal_reference
custody_model
```

Blockchain representation không tự tạo legal ownership.

---

# 289. Digital Asset Boundary

Digital assets có thể được represent nếu market rules cho phép.

Không giả định mọi token là security.

Classification phải đến từ domain/legal authority.

---

# 290. Stablecoin/Payment Asset Boundary

Payment asset semantics thuộc banking/payment layer.

AXMARKET chỉ represent nếu asset được traded trên venue.

---

# 291. Market Access

Access policy:

```text
jurisdiction
participant_status
instrument_permissions
account_permissions
trading_hours
```

---

# 292. KYC/Identity Boundary

Identity verification không được duplicate toàn bộ.

```text
AXMARKET
→ identity verification reference
```

authority nằm ở identity/compliance layer.

---

# 293. AML Boundary

Market runtime có thể phát signal.

Legal/compliance decision thuộc compliance/legal domain.

---

# 294. Privacy-Preserving Surveillance

Có thể dùng:

```text
pseudonymous participant_id
role-based access
need-to-know
```

---

# 295. Data Access

Public market data:

```text
public
```

Private order flow:

```text
restricted
```

Internal surveillance:

```text
highly_restricted
```

---

# 296. API Rate Limits

Per:

```text
participant
feed
API key
venue
security
```

---

# 297. Market Data Fanout

Architecture:

```text
Feed
 ↓
Sequencer
 ↓
Normalizer
 ↓
Fanout
 ├── trader
 ├── surveillance
 ├── analytics
 └── archive
```

---

# 298. Backpressure Strategy

Critical consumers:

```text
never silently drop
```

Non-critical analytics:

```text
drop/coalesce allowed
```

---

# 299. Coalescing

High-frequency quote streams có thể coalesce cho UI clients.

Không được coalesce canonical audit stream.

---

# 300. Canonical Audit Stream

Audit stream:

```text
lossless
ordered
durable
replayable
```

---

# 301. Performance Profiles

```text
AXMARKET_CORE
AXMARKET_DATA
AXMARKET_BROKER
AXMARKET_ORDER
AXMARKET_MATCHING
AXMARKET_AUCTION
AXMARKET_EXECUTION
AXMARKET_CUSTODY
AXMARKET_SETTLEMENT
AXMARKET_SURVEILLANCE
AXMARKET_SIMULATION
AXMARKET_AI
AXMARKET_DISTRIBUTED
AXMARKET_REALTIME
AXMARKET_GPU
AXMARKET_WASM
AXMARKET_MOBILE
AXMARKET_FULL
```

---

# 302. Minimal Core

`AXMARKET_CORE`:

```text
Security
Listing
Venue
Market
Session
Order
Execution
Trade
MarketEvent
```

---

# 303. Matching Profile

Chỉ kéo:

```text
OrderBook
MatchingEngine
Auction
OrderEvent
Execution
```

Không kéo:

```text
AI
custody
simulation
```

---

# 304. Market Data Profile

Chỉ cần:

```text
Tick
Quote
Book
Bar
Feed
HistoricalStore
```

---

# 305. Mobile Profile

Mobile không được có quyền mặc định:

```text
market.halt
order.admin
matching.admin
```

---

# 306. WASM Profile

WASM có thể:

```text
read market data
simulate execution
visualize order book
```

Privileged production trading cần explicit host capability.

---

# 307. GPU

GPU phù hợp:

```text
market simulation
historical analytics
Monte Carlo
large-scale TCA
AI surveillance
```

Matching engine hot path không mặc định chuyển sang GPU vì latency/determinism tradeoffs.

---

# 308. CPU Hot Path

Matching engine ưu tiên:

```text
CPU
cache
NUMA awareness
single-writer
lock minimization
```

---

# 309. NUMA

Large exchange deployment hỗ trợ:

```text
venue shard
CPU affinity
memory locality
NIC affinity
```

---

# 310. Kernel Bypass Boundary

Target-dependent adapter có thể hỗ trợ:

```text
kernel bypass
RDMA
DPDK-like transport
user-space networking
```

nhưng không hard-code vendor dependency vào semantic core.

---

# 311. Hardware Timestamp

Nếu NIC hỗ trợ:

```text
hardware_receive_timestamp
```

có thể preserve.

---

# 312. Network Failure

Order gateway phải xử lý:

```text
disconnect
reconnect
duplicate
late message
out-of-order
```

---

# 313. Session Recovery

```text
connect
authenticate
negotiate
resume_sequence
snapshot
continue
```

---

# 314. Gateway State

```text
Disconnected
Connecting
Authenticated
Synchronizing
Active
Degraded
Closing
Closed
```

---

# 315. Duplicate Execution Protection

Client reconnection không được submit duplicate order do unknown ACK.

Sử dụng:

```text
client_order_id
idempotency_key
server_order_id
```

---

# 316. Unknown Outcome

Nếu client mất connection sau submission:

```text
UNKNOWN
```

Client phải query/reconcile trước khi retry.

---

# 317. Critical Invariant

```text
network timeout ≠ order failure
```

---

# 318. Market Data Unknown

```text
missing feed ≠ zero volume
```

---

# 319. Price Unknown

```text
missing price ≠ 0
```

---

# 320. Position Unknown

```text
custody timeout ≠ zero position
```

---

# 321. Settlement Unknown

```text
confirmation missing ≠ failed
```

---

# 322. Error Model

Canonical:

```text
MarketError
VenueUnavailable
MarketClosed
OrderRejected
InvalidOrder
RiskRejected
MatchingError
ExecutionError
FeedGap
StaleData
SequenceGap
SettlementPending
SettlementFailed
CustodyMismatch
Unauthorized
RuleViolation
DuplicateRequest
UnknownOutcome
```

---

# 323. Observability

Metrics:

```text
orders_per_second
matches_per_second
execution_latency
market_data_latency
book_depth
spread
reject_rate
fill_rate
cancel_rate
feed_gap_rate
recovery_time
settlement_failure_rate
```

---

# 324. Tracing

Trace:

```text
OrderIntent
→ Order
→ Gateway
→ Venue
→ Match
→ Execution
→ Trade
→ Clearing
→ Settlement
```

---

# 325. Correlation IDs

Mỗi transaction có:

```text
trace_id
order_id
client_order_id
execution_id
trade_id
settlement_id
```

---

# 326. Performance Logging

Không log string formatting trong hot path mặc định.

Structured binary telemetry được ưu tiên.

---

# 327. Memory Model

Market hot path yêu cầu:

```text
explicit lifetime
preallocation
arena/region
object pools
intrusive structures
```

Không phụ thuộc GC.

---

# 328. Ownership

Order ownership:

```text
gateway
→ matching
```

ownership transfer phải rõ ràng.

---

# 329. Shared Memory

Local components có thể sử dụng:

```text
shared ring buffer
shared memory
memory-mapped order book
```

---

# 330. Lock-Free Queue

Native primitive:

```axiom
channel<OrderEvent>
```

có thể compile xuống lock-free ring buffer trên suitable target.

---

# 331. Persistence

Durable market event log:

```text
append-only
sequence
checksum
segment
snapshot
```

---

# 332. Snapshot Frequency

Configurable:

```text
every N events
every T seconds
hybrid
```

---

# 333. Recovery Point

```text
snapshot S
+
events after S
```

rebuild state.

---

# 334. Market Data Archive

Archive phải giữ:

```text
raw
normalized
canonical
```

nếu required by policy.

---

# 335. Compression Target

Historical market data nên đạt:

```text
high compression
sequential read
parallel decompression
```

---

# 336. Content Addressed Data

Market snapshots có thể dùng:

```text
hash(snapshot)
```

để deduplicate.

---

# 337. Reproducibility

Historical simulation:

```text
same snapshot
same event stream
same rules
same seed
```

→ same result trong deterministic components.

---

# 338. Non-Deterministic Components

AI/GPU reductions có thể có floating-point nondeterminism.

Runtime phải expose:

```text
deterministic_mode
```

khi cần.

---

# 339. Numeric Precision

Market price:

```text
Decimal / Fixed
```

không dùng binary float làm canonical price.

---

# 340. Quantity Precision

```text
Decimal
Fixed
```

theo instrument rule.

---

# 341. Timestamp Precision

Target:

```text
nanosecond
```

nếu hardware/feed hỗ trợ.

Không giả định nanosecond accuracy nếu source không cung cấp.

---

# 342. Native Financial Types

Axiom core types:

```text
Money
Decimal
Fixed
Price
Quantity
Ratio
Rate
BasisPoints
```

---

# 343. Price Arithmetic

```axiom
Price × Quantity → Money
```

phải có rounding rule rõ ràng.

---

# 344. Fee Arithmetic

```axiom
Fee = calculate_fee(execution, fee_schedule)
```

Rounding phải deterministic.

---

# 345. Currency

```axiom
Money<USD>
Money<EUR>
```

type-level currency nếu compiler hỗ trợ generic numeric units.

---

# 346. Unit Safety

Compiler nên reject:

```text
Money + Quantity
```

nếu không có explicit conversion.

---

# 347. Market DSL Type Safety

```axiom
buy 100 USD
```

phải khác:

```text
buy 100 shares
```

---

# 348. Contract Size

Derivatives:

```text
quantity × contract_size
```

phải compile/runtime validated.

---

# 349. Market Rule Validation

Compiler có thể validate static rules.

Runtime validate dynamic rules.

---

# 350. Dynamic Market Rule

Ví dụ:

```text
halted
price_band
participant_limit
```

phải runtime.

---

# 351. Security Lifecycle

```text
Draft
→ Issued
→ Listed
→ Active
→ Suspended
→ Matured/Redeemed/Delisted
```

---

# 352. Market Lifecycle

```text
Created
→ Configured
→ PreOpen
→ Open
→ Halted
→ Reopen
→ Close
→ Archived
```

---

# 353. Venue Lifecycle

```text
Provisioning
→ Active
→ Degraded
→ Suspended
→ Retiring
→ Retired
```

---

# 354. Participant Lifecycle

```text
Applied
→ Approved
→ Active
→ Restricted
→ Suspended
→ Terminated
```

---

# 355. Broker Account

```axiom
struct TradingAccount {
    id: TradingAccountId
    participant: ParticipantId
    base_currency: Currency
    limits: TradingLimitSet
}
```

---

# 356. Account Separation

Trading account:

```text
execution authority
```

Bank account:

```text
cash authority
```

Custody account:

```text
asset safekeeping
```

Investment account:

```text
portfolio intent
```

Không đồng nhất bốn loại.

---

# 357. Account Mapping

```text
InvestmentAccount
 ↓
TradingAccount
 ↓
CustodyAccount
 ↓
BankAccount
```

Mappings phải explicit.

---

# 358. Segregation

Customer assets phải có account/ownership semantics riêng nếu market policy yêu cầu.

---

# 359. Omnibus Custody

Hỗ trợ:

```text
many clients
→ omnibus custody
```

nhưng internal beneficial-interest ledger phải được quản lý ở appropriate domain.

---

# 360. Beneficial Ownership Boundary

Legal beneficial ownership không được suy luận chỉ từ market position.

---

# 361. Market Participant Identity

Identity:

```text
participant_id
entity_id
account_id
```

phân biệt rõ.

---

# 362. Order Attribution

Order phải truy được:

```text
principal
agent
account
strategy
```

nếu policy yêu cầu.

---

# 363. Strategy Attribution

Order có thể có:

```text
strategy_id
model_version
```

---

# 364. AI Attribution

AI-generated order phải có:

```text
agent_id
model_id
policy_id
authority_id
```

---

# 365. Human Approval

Nếu required:

```text
approval_id
approver
timestamp
```

---

# 366. Four-Eyes Rule

Policy có thể yêu cầu:

```text
creator != approver
```

---

# 367. Emergency Execution

Emergency policy phải có:

```text
scope
expiry
authority
audit
```

---

# 368. Governance

Không cho phép market engine tự sửa:

```text
legal rules
ownership
participant rights
```

---

# 369. Rule Engine

Market rule engine hỗ trợ:

```text
if
when
unless
limit
allow
deny
halt
```

---

# 370. Rule Example

```axiom
rule price_band {
    deny order
    when order.price < lower_band
}
```

---

# 371. Rule Conflict

Nếu hai rules conflict:

```text
deny > allow
```

chỉ khi policy engine định nghĩa rõ.

Không hard-code universal precedence nếu venue rule yêu cầu khác.

---

# 372. Rule Explainability

Reject phải trả:

```text
rule_id
rule_version
evaluation
```

---

# 373. Market Fee Schedule

```axiom
fee_schedule "X" {
    maker: ...
    taker: ...
}
```

---

# 374. Fee Versioning

Trade phải reference:

```text
fee_schedule_version
```

---

# 375. Revenue Boundary

Exchange revenue accounting thuộc:

```text
AXFINANCE
```

Market engine chỉ tính fee event.

---

# 376. Tax Boundary

Tax calculation không hard-code vào matching engine.

---

# 377. Tax Event

Market có thể emit:

```text
TaxReferenceEvent
```

---

# 378. Corporate Action Adjustment

Order/position adjustment phải dựa trên corporate action rule.

---

# 379. Corporate Action Fraction

Fractional entitlement phải có policy:

```text
cash_in_lieu
fractional_security
round_down
round_up
```

---

# 380. Dividend Event

```axiom
DividendDeclaration
DividendExDate
DividendRecordDate
DividendPaymentDate
```

---

# 381. Ex-Date Semantics

Eligibility calculation phải sử dụng market calendar và corporate-action rule.

---

# 382. Split

Split phải transform:

```text
quantity
price
```

theo ratio mà vẫn preserve economic equivalence theo applicable rules.

---

# 383. Delisting

Delisting không tự động erase historical positions.

---

# 384. Historical Integrity

Historical market data không được rewrite để làm mất trạng thái cũ.

---

# 385. Market Replay Contract

```axiom
replay {
    data_snapshot
    event_log
    rules
}
```

phải có output version.

---

# 386. Testing

Minimum target:

```text
≥ 18,000 automated tests
≥ 1,500 architecture invariants
```

---

# 387. Test Categories

```text
security identity
listing
market session
order validation
order lifecycle
order book
matching
auction
routing
execution
trade
market data
feed recovery
corporate actions
custody
settlement
reconciliation
surveillance
AI
simulation
security
distributed systems
fault recovery
performance
determinism
numeric precision
WASM
mobile
GPU
```

---

# 388. Matching Invariants

```text
matched quantity <= available quantity
```

```text
execution price obeys matching rule
```

```text
order sequence is preserved
```

---

# 389. Book Invariants

```text
bid levels ordered correctly
ask levels ordered correctly
quantity never negative
deleted order cannot execute
```

---

# 390. Trade Invariants

```text
buy_quantity == sell_quantity
```

trừ các special market mechanisms được explicit.

---

# 391. Settlement Invariants

```text
unsettled trade ≠ settled asset
```

---

# 392. Custody Invariants

```text
custody record != legal ownership verdict
```

---

# 393. Market Data Invariants

```text
sequence gap detected
```

---

# 394. Recovery Invariants

```text
recovery must not duplicate execution
```

---

# 395. Security Invariants

```text
unauthorized order = rejected
```

---

# 396. Surveillance Invariants

```text
signal != verdict
```

---

# 397. Simulation Invariants

```text
simulation order cannot enter production book
```

---

# 398. AI Invariants

```text
AI cannot escalate capability
```

---

# 399. Rule Invariants

```text
historical replay uses historical rule version
```

---

# 400. Precision Invariants

```text
financial arithmetic obeys declared rounding mode
```

---

# 401. Failure Invariants

```text
unknown outcome ≠ failure
```

---

# 402. Network Invariants

```text
reconnect must not duplicate order
```

---

# 403. Idempotency Invariants

```text
same idempotency key
→ same logical request
```

---

# 404. Audit Invariants

```text
trade correction preserves original record
```

---

# 405. Market Integrity

Core principle:

```text
Every production market state transition
must be attributable,
ordered,
auditable,
replayable,
and authorization-checked.
```

---

# 406. Reference Architecture

```text
                 AXINVEST
                    │
              Order Intent
                    │
                    ▼
             ┌──────────────┐
             │  AXMARKET    │
             ├──────────────┤
             │ Order Mgmt   │
             │ Risk         │
             │ Routing      │
             │ Market Data  │
             │ Order Book   │
             │ Matching     │
             │ Auction      │
             │ Execution    │
             │ Surveillance│
             └──────┬───────┘
                    │
             Trade / Execution
                    │
                    ▼
              ┌───────────┐
              │ AXCLEAR   │
              └─────┬─────┘
                    │
             Settlement
                    │
                    ▼
              Custody/Bank
```

---

# 407. Full Financial Execution Loop

```text
INVESTOR
   ↓
MANDATE
   ↓
AXINVEST
   ↓
ORDER INTENT
   ↓
AXMARKET
   ↓
ORDER
   ↓
ROUTING
   ↓
ORDER BOOK / RFQ / AUCTION
   ↓
MATCH
   ↓
EXECUTION
   ↓
TRADE
   ↓
CLEARING
   ↓
SETTLEMENT
   ↓
CUSTODY
   ↓
PORTFOLIO
   ↓
PERFORMANCE
   ↓
REBALANCE
```

---

# 408. Financial Civilization Stack

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
AXCLEAR
      ↓
AXCUSTODY
      ↓
REAL ECONOMY
```

---

# 409. Capital Feedback Loop

```text
SAVINGS
   ↓
BANKING
   ↓
INSURANCE
   ↓
INVESTMENT
   ↓
CAPITAL MARKETS
   ↓
CAPITAL
   ↓
ENTERPRISES / PROJECTS
   ↓
PRODUCTION
   ↓
INCOME
   ↓
SAVINGS
```

---

# 410. Civilization Market Graph

```text
Households
    ↓
Savings
    ↓
Banks / Funds / Insurers
    ↓
Investors
    ↓
Markets
    ↓
Enterprises
    ↓
Projects
    ↓
Infrastructure
    ↓
Production
    ↓
Employment
    ↓
Income
```

---

# 411. AXMARKET Semantic Contract

Các distinction bắt buộc:

```text
Market ≠ Venue

Venue ≠ Exchange

Security ≠ Listing

Security ≠ Position

OrderIntent ≠ Order

Order ≠ Execution

Execution ≠ Trade

Trade ≠ Settlement

Settlement ≠ Custody

MarketPrice ≠ FundamentalValue

Quote ≠ Trade

Signal ≠ Finding

Finding ≠ LegalVerdict

Simulation ≠ Production

Forecast ≠ Observation

MarketData ≠ UniversalTruth

Timeout ≠ Failure

Unknown ≠ Zero

CustodyRecord ≠ LegalOwnershipVerdict
```

---

# 412. Axiom Language Compatibility

Sử dụng trực tiếp:

```text
struct
trait
enum
sum type
vector
ring buffer
stream
async
event
capability
snapshot
transaction
module
fixed
decimal
```

Không yêu cầu class hierarchy.

---

# 413. Struct-Only Architecture

Ví dụ:

```axiom
struct OrderBook {
    ...
}

fn OrderBook.insert(self, order: Order)
fn OrderBook.cancel(self, id: OrderId)
fn OrderBook.match(self) -> ExecutionBatch
```

---

# 414. Matching Strategy Trait

```axiom
trait MatchingPolicy {
    fn match(self, book: OrderBook) -> ExecutionBatch
}
```

Implementation:

```axiom
struct PriceTime {}

fn PriceTime.match(self, book) -> ExecutionBatch {
    ...
}
```

---

# 415. Venue Extension

```axiom
struct VenueRules {
    matching: MatchingPolicy
    tick: TickRule
    lot: LotRule
    sessions: TradingCalendar
}
```

---

# 416. No Hidden Runtime Dependency

Core market engine không yêu cầu:

```text
GC
third-party runtime
external compiler
external database
external message broker
```

Adapters có thể sử dụng chúng khi application lựa chọn.

---

# 417. Native Binary

Canonical internal representation:

```text
compact
typed
versioned
zero-copy compatible
```

---

# 418. Dead Code Elimination

Nếu application chỉ dùng:

```text
market data
```

compiler phải loại bỏ:

```text
matching
custody
AI
surveillance
```

nếu không được reference.

---

# 419. Compile-Time Specialization

Matching engine có thể specialize:

```text
PriceTime
tick_size fixed
lot_size fixed
```

để giảm runtime branching.

---

# 420. Profile-Based Compilation

```axiom
@profile("ultra_low_latency")
```

có thể bật:

```text
preallocation
CPU affinity
branch optimization
binary protocol
```

---

# 421. No-Allocation Contract

```axiom
@noalloc
MatchingEngine.match(...)
```

Compiler phải reject implementation có implicit allocation nếu contract yêu cầu.

---

# 422. Realtime Contract

```axiom
@realtime(deadline: 100us)
```

cho phép compiler/runtime validate allocation, blocking và forbidden operations.

---

# 423. Async Boundary

Network operations:

```text
async
```

Matching hot path:

```text
sync
```

trừ khi explicit architecture yêu cầu.

---

# 424. Actor/Sharding Model

Large market:

```text
Market
├── SecurityShard A
├── SecurityShard B
├── SecurityShard C
```

Mỗi shard có owner thread/actor.

---

# 425. Cross-Shard Trade

Cross-shard transaction sử dụng:

```text
event
sequence
atomic protocol
```

không global lock.

---

# 426. Single-Writer Principle

Mỗi order book nên có một canonical writer trong hot path.

---

# 427. Horizontal Scaling

Scale theo:

```text
venue
security
market
region
```

---

# 428. Vertical Scaling

Scale bằng:

```text
CPU
memory
NIC
storage
```

---

# 429. Global Market Federation

```text
Region A
Region B
Region C
```

không cần shared global mutable state.

Global analytics dùng event aggregation.

---

# 430. Market Federation

```text
Local Market
    ↓
Market Federation
    ↓
Global Market Graph
```

---

# 431. Global Price Reference

Global analytics có thể tính:

```text
reference_price
```

nhưng phải giữ:

```text
source venues
timestamp
methodology
```

---

# 432. Cross-Border Market

Metadata:

```text
jurisdiction
currency
settlement_system
trading_calendar
legal_reference
```

---

# 433. Market Access Restrictions

```text
eligible
restricted
blocked
```

là policy states.

---

# 434. No Implicit Cross-Border Authority

AXMARKET không tự suy luận:

```text
legal eligibility
```

nó consume explicit policy.

---

# 435. Global Market Simulation

Có thể mô phỏng:

```text
multiple venues
multiple currencies
multiple participants
multiple settlement systems
```

---

# 436. Systemic Liquidity

Simulation output:

```text
liquidity concentration
cross-venue contagion
settlement bottleneck
counterparty exposure
```

---

# 437. Civilization Financial Stress

```text
market crash
→ liquidity shock
→ investment losses
→ banking balance sheet pressure
→ insurance asset pressure
→ capital allocation change
→ real economy effect
```

Đây là input cho `AX671`, không phải prediction.

---

# 438. Integration With AI World Model

`AX655` có thể consume:

```text
market observations
market state
capital flows
```

nhưng phải phân biệt:

```text
observed
predicted
simulated
```

---

# 439. Integration With AI Planning

`AX652` có thể request:

```text
execution plan
```

nhưng AXMARKET chịu trách nhiệm validate market constraints.

---

# 440. Integration With Probabilistic AI

`AX653` có thể tạo:

```text
probability distribution
```

AXMARKET giữ:

```text
actual execution records
```

---

# 441. Integration With AI Agents

`AX644` agent có thể:

```text
read market
submit order
```

chỉ khi capability được cấp.

---

# 442. Agent Delegation

```axiom
delegate {
    agent: ExecutionAgent
    capabilities: [
        marketdata.read,
        order.create,
        order.cancel
    ]
    limits: ...
}
```

---

# 443. Delegation Expiry

Delegation phải hỗ trợ:

```text
expires_at
```

---

# 444. Delegation Revocation

```axiom
revoke delegation D
```

phải có immediate policy effect theo runtime guarantee.

---

# 445. Agent Emergency Stop

```axiom
stop agent A
```

ngăn new privileged actions.

---

# 446. Model/Strategy Separation

```text
Model
    = prediction

Strategy
    = execution policy

Mandate
    = authority/objective

Order
    = executable instruction
```

Không được trộn bốn khái niệm.

---

# 447. Strategy ≠ Authority

Một strategy có thể đề xuất order nhưng không có quyền submit nếu thiếu capability.

---

# 448. Authority ≠ Model

Có capability không đồng nghĩa model được phép dùng.

---

# 449. Model Approval

Production model phải reference:

```text
approval_id
model_version
deployment_id
```

---

# 450. Final Acceptance Criteria

`BOOTSTRAP-693` hoàn thành khi:

```text
[✓] Market model
[✓] Venue model
[✓] Exchange model
[✓] Security/listing model
[✓] Participant model
[✓] Broker/dealer model
[✓] Order model
[✓] Order lifecycle
[✓] Order routing
[✓] Order book
[✓] Matching engine
[✓] Auction
[✓] RFQ
[✓] Execution
[✓] Trade
[✓] Market data
[✓] Historical data
[✓] Feed sequencing
[✓] Feed recovery
[✓] Corporate actions
[✓] Custody boundary
[✓] Settlement boundary
[✓] Reconciliation
[✓] Market surveillance
[✓] AI execution
[✓] AI surveillance
[✓] Simulation
[✓] Digital twin
[✓] Market security
[✓] Capability model
[✓] Rule engine
[✓] Audit
[✓] Replay
[✓] Disaster recovery
[✓] Native IR
[✓] DSL
[✓] CPU low-latency architecture
[✓] GPU analytics boundary
[✓] WASM boundary
[✓] Mobile boundary
[✓] Distributed market architecture
[✓] Civilization financial integration
[✓] Testing requirements
```

---

# 451. Hoàn thành BOOTSTRAP-693

`AXMARKET` giờ trở thành **market-execution substrate** hoàn chỉnh của Axiom:

```text
AXINVEST
    ↓
ORDER INTENT
    ↓
AXMARKET
    ↓
ORDER
    ↓
ROUTING
    ↓
MATCHING
    ↓
EXECUTION
    ↓
TRADE
    ↓
AXCLEAR
    ↓
SETTLEMENT
    ↓
CUSTODY
```

Ranh giới quan trọng nhất được giữ nguyên:

```text
AXINVEST
= capital allocation

AXMARKET
= market execution

AXCLEAR
= clearing / collateral / netting / settlement coordination

AXFINANCE
= accounting / financial truth

AXBANKING
= banking / money movement

AXLAW
= legal authority

AXGOV
= public authority
```

---

# 452. Kiến trúc tài chính sau BOOTSTRAP-693

```text
                    ┌──────────────┐
                    │   AXFINANCE  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   AXBANKING  │
                    └──────┬───────┘
                           │
              ┌────────────▼────────────┐
              │       AXINSURANCE       │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │       AXINVEST          │
              │ Capital Allocation      │
              └────────────┬────────────┘
                           │
                       OrderIntent
                           │
              ┌────────────▼────────────┐
              │       AXMARKET          │
              │ Market Infrastructure   │
              ├─────────────────────────┤
              │ Data                    │
              │ Orders                  │
              │ Routing                 │
              │ Books                   │
              │ Matching                │
              │ Execution               │
              │ Trading                │
              │ Surveillance            │
              └────────────┬────────────┘
                           │
                         Trades
                           │
              ┌────────────▼────────────┐
              │       AXCLEAR           │
              │ Clearing / Collateral   │
              │ Netting / Settlement    │
              └────────────┬────────────┘
                           │
                    ┌──────▼───────┐
                    │   CUSTODY    │
                    └──────────────┘
```

---

# 453. Task kế tiếp

**BOOTSTRAP-694 — Native AI Civilization-Scale Clearing, Collateral, Margin, Netting, Central Counterparty, Settlement Finality, Default Management & Systemic Financial Stability Runtime 5.0**

Trọng tâm tiếp theo:

```text
AXMARKET
    ↓
TRADE
    ↓
CLEARING
    ↓
MARGIN
    ↓
COLLATERAL
    ↓
NETTING
    ↓
CCP
    ↓
DEFAULT MANAGEMENT
    ↓
SETTLEMENT FINALITY
    ↓
CUSTODY / BANKING
```

và đặc biệt xây dựng lớp **financial stability / systemic risk infrastructure** nối:

```text
AXBANKING
     ↕
AXINSURANCE
     ↕
AXINVEST
     ↕
AXMARKET
     ↕
AXCLEAR
     ↕
AX671 ECONOMY
```

để hoàn thiện chuỗi **money → capital → market → clearing → settlement → real economy** của Axiom.

:::