Tiếp tục với **BOOTSTRAP-693** — lớp hạ tầng thực thi của `AXINVEST`, tách rõ thị trường vốn khỏi portfolio/đầu tư và financial ledger.

:::writing{variant="document" id="74136" title="BOOTSTRAP-693 — Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Clearing, Settlement, Market Infrastructure & Global Financial Market Runtime 5.0"}

# BOOTSTRAP-693
## Native AI Civilization-Scale Capital Markets, Securities Trading, Exchanges, Brokerage, Clearing, Settlement, Market Infrastructure & Global Financial Market Runtime 5.0

**Status:** Architecture Specification  
**Version:** 5.0  
**Namespace:** `AXMARKET`  
**Layer:** Global Financial Market Infrastructure  
**Primary role:** cung cấp native runtime cho thị trường vốn, securities, exchange, order management, matching, brokerage, clearing, settlement, custody interfaces, market data, market microstructure và market-wide simulation.

---

# 1. Mục tiêu

`AXMARKET` là lớp thực thi giữa:

```text
AXINVEST
    ↓
AXMARKET
    ↓
AXFINANCE
```

Nó phải biểu diễn được:

- securities;
- financial instruments;
- exchanges;
- trading venues;
- order books;
- orders;
- executions;
- brokers;
- dealers;
- market makers;
- participants;
- auctions;
- matching engines;
- price discovery;
- market data;
- clearing;
- netting;
- settlement;
- custody interfaces;
- collateral;
- margin;
- securities lending;
- repo;
- primary issuance;
- secondary markets;
- OTC markets;
- derivatives venues;
- cross-market routing;
- market surveillance;
- circuit breakers;
- market simulation;
- high-frequency event processing.

---

# 2. Boundary tuyệt đối

`AXMARKET` phải giữ các boundary:

```text
InvestmentDecision ≠ Order
Order ≠ Execution
Execution ≠ Clearing
Clearing ≠ Settlement
Settlement ≠ Accounting
MarketPrice ≠ FundamentalValue
Quote ≠ Trade
Bid ≠ Ask
IndicativePrice ≠ ExecutedPrice
MarketData ≠ FinancialTruth
Simulation ≠ LiveMarket
Broker ≠ Exchange
Exchange ≠ ClearingHouse
Custodian ≠ Owner
EconomicExposure ≠ LegalOwnership
```

---

# 3. Kiến trúc tổng thể

```text
                    AXINVEST
                       │
                Investment Intent
                       │
                       ▼
                  AXMARKET
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      ORDER          MARKET         BROKER
      MGMT           DATA           GATEWAY
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                TRADING VENUE
                       │
                  MATCH ENGINE
                       │
                    TRADE
                       │
                       ▼
                   CLEARING
                       │
                    NETTING
                       │
                  COLLATERAL
                       │
                       ▼
                  SETTLEMENT
                       │
                       ▼
                  AXFINANCE
```

---

# 4. Market participant

Core actor:

```axiom
struct MarketParticipant {
    id: ParticipantId
    legal_entity: EntityRef
    participant_type: ParticipantType
    permissions: CapabilitySet
}
```

Types:

```text
Individual
Institution
Broker
Dealer
MarketMaker
InvestmentFund
Bank
InsuranceCompany
PensionFund
Government
CentralBank
ExchangeOperator
ClearingMember
Custodian
LiquidityProvider
Issuer
AuthorizedAgent
AITradingAgent
```

---

# 5. Participant ≠ account

Một participant có thể có:

```text
TradingAccount
CustodyAccount
MarginAccount
ClearingAccount
SettlementAccount
```

Không được coi chúng là cùng một object.

---

# 6. Security model

Base:

```axiom
struct Security {
    id: SecurityId
    issuer: EntityRef
    class: SecurityClass
    currency: Currency
    lifecycle: SecurityLifecycle
}
```

Các loại:

```text
Equity
Bond
Note
CommercialPaper
Certificate
FundUnit
ETF
REIT
Derivative
StructuredProduct
Warrant
Option
Future
Forward
Swap
```

---

# 7. Instrument identity

Instrument phải có:

```text
InstrumentId
IssuerId
SecurityClass
IssueId
SeriesId
Currency
Jurisdiction
Version
```

Không dùng symbol làm identity duy nhất.

---

# 8. Symbol

`Symbol` chỉ là market identifier:

```text
Symbol
Ticker
VenueSymbol
ExternalCode
```

Một instrument có thể có nhiều symbol trên nhiều venue.

---

# 9. Venue

```axiom
struct TradingVenue {
    id: VenueId
    name: String
    venue_type: VenueType
    currency: Currency
    trading_calendar: CalendarRef
}
```

Types:

```text
Exchange
ATS
ECN
OTC
DarkPool
AuctionVenue
DerivativeVenue
BondVenue
DigitalVenue
InternalCrossingVenue
```

---

# 10. Venue lifecycle

```text
Planned
→ Registered
→ Opening
→ Open
→ Halted
→ Closing
→ Closed
→ Suspended
→ Retired
```

---

# 11. Trading session

```axiom
struct TradingSession {
    venue: VenueId
    date: Date
    phase: SessionPhase
    open_time: Timestamp
    close_time: Timestamp
}
```

Phases:

```text
PreOpen
OpeningAuction
Continuous
IntradayAuction
Halt
ClosingAuction
PostClose
Closed
```

---

# 12. Trading calendar

Calendar phải hỗ trợ:

```text
timezone
holidays
special_sessions
early_close
late_open
halt_windows
auction_windows
```

Không được hard-code một thị trường duy nhất.

---

# 13. Order

```axiom
struct Order {
    id: OrderId
    participant: ParticipantId
    account: AccountId
    instrument: InstrumentId
    side: Side
    quantity: Decimal
    order_type: OrderType
    time_in_force: TimeInForce
}
```

---

# 14. Order types

Core:

```text
Market
Limit
Stop
StopLimit
Pegged
Iceberg
Hidden
Auction
MarketToLimit
ImmediateOrCancel
FillOrKill
GoodTillCancel
GoodTillDate
Day
```

Provider-specific types phải nằm trong extension layer.

---

# 15. Side

```text
Buy
Sell
SellShort
BuyToCover
Exercise
Assignment
```

Derivative-specific semantics có thể mở rộng.

---

# 16. Order lifecycle

```text
Created
→ Validating
→ Accepted
→ Working
→ PartiallyFilled
→ Filled
```

Branches:

```text
Rejected
Cancelled
Expired
Suspended
Replaced
```

---

# 17. Order validation

Trước matching:

```text
instrument validity
venue availability
account authorization
quantity validity
price validity
risk limits
credit limits
margin
short-sale permission
market phase
```

---

# 18. Order rejection reasons

```text
InvalidInstrument
InvalidQuantity
InvalidPrice
InsufficientFunds
InsufficientMargin
RiskLimit
MarketClosed
VenueUnavailable
Unauthorized
RestrictedSecurity
InvalidTimeInForce
DuplicateOrder
```

---

# 19. Order replacement

Không overwrite order cũ.

```text
Order A
   ↓
ReplaceRequest
   ↓
Order B
```

Order history immutable.

---

# 20. Order cancel

Cancellation phải có:

```text
CancelRequest
CancelAccepted
CancelRejected
CancelEffective
```

Cancel request không đồng nghĩa order đã cancelled.

---

# 21. Order book

```axiom
struct OrderBook {
    instrument: InstrumentId
    venue: VenueId
    bids: PriceLevel[]
    asks: PriceLevel[]
}
```

Mỗi `PriceLevel`:

```text
price
aggregate_quantity
order_count
queue
```

---

# 22. Bid/ask invariant

```text
best_bid < best_ask
```

trong trạng thái continuous order book hợp lệ.

Crossed book chỉ tồn tại tạm thời trong event processing hoặc trạng thái lỗi được đánh dấu.

---

# 23. Price-time priority

Default matching policy:

```text
price priority
→ time priority
```

Matching policy phải là configurable venue rule.

---

# 24. Matching engine

```axiom
match(order, book) -> MatchResult
```

Output:

```text
Trade[]
RemainingOrder?
BookMutation
```

---

# 25. Matching policies

Native policies:

```text
PriceTime
ProRata
SizeTime
Auction
ReferencePrice
CustomPolicy
```

---

# 26. Atomic matching

Một matching operation phải atomic đối với:

```text
book mutation
trade creation
order quantity update
sequence number
```

Không được tạo trade mà không update order book tương ứng.

---

# 27. Trade

```axiom
struct Trade {
    id: TradeId
    instrument: InstrumentId
    venue: VenueId
    buy_order: OrderId
    sell_order: OrderId
    quantity: Decimal
    price: Price
    timestamp: Timestamp
}
```

---

# 28. Trade price

Trade price là:

```text
ExecutedPrice
```

Không được thay thế bằng:

```text
ModelValue
FairValue
ReferencePrice
```

---

# 29. Trade lifecycle

```text
Matched
→ Confirmed
→ Cleared
→ Settling
→ Settled
```

Branches:

```text
Busted
CancelledByVenue
FailedSettlement
Disputed
```

---

# 30. Trade bust

Trade cancellation sau execution phải tạo event mới:

```text
Trade
→ BustRequest
→ BustApproved
→ TradeBusted
```

Không xóa trade history.

---

# 31. Market data

Core feeds:

```text
Quote
Trade
OrderBook
OHLCV
ReferenceData
CorporateAction
AuctionState
TradingStatus
```

---

# 32. Quote

```axiom
struct Quote {
    bid: Price
    bid_size: Decimal
    ask: Price
    ask_size: Decimal
    timestamp: Timestamp
}
```

Quote ≠ executable guarantee.

---

# 33. Market snapshot

```axiom
struct MarketSnapshot {
    venue: VenueId
    instrument: InstrumentId
    timestamp: Timestamp
    quote: Quote
    last_trade: TradeRef
    book: OrderBookSnapshot
}
```

---

# 34. Market data sequence

Mọi event phải có:

```text
sequence_number
source_timestamp
receive_timestamp
process_timestamp
```

để tái tạo market state.

---

# 35. Market data correctness

Runtime phải phát hiện:

```text
duplicate
out_of_order
gap
stale
invalid
corrupted
```

---

# 36. Market data replay

```axiom
replay(
    venue,
    from,
    to
)
```

phải tái tạo order-book state nếu dataset đầy đủ.

---

# 37. Price discovery

Price discovery có thể sử dụng:

```text
continuous_matching
opening_auction
closing_auction
reference_price
VWAP
TWAP
```

---

# 38. Auction engine

Auction phases:

```text
CollectOrders
CalculateIndicativePrice
Freeze
Match
PublishResult
```

---

# 39. Indicative price

```text
IndicativePrice
```

không phải:

```text
ExecutedPrice
```

cho đến khi auction match hoàn tất.

---

# 40. VWAP

```text
VWAP =
Σ(price × quantity) / Σ(quantity)
```

Window phải explicit.

---

# 41. TWAP

TWAP phải lưu:

```text
window
sampling_method
source
```

Không được coi TWAP là universally executable price.

---

# 42. Circuit breaker

Venue có thể khai báo:

```text
price_band
volatility_band
halt_threshold
cooldown
auction_after_halt
```

---

# 43. Market halt

```text
Normal
→ Halted
→ Auction
→ Resumed
```

Halt reason:

```text
Volatility
Operational
Regulatory
InformationEvent
Technical
Emergency
```

---

# 44. Market-wide halt

Hệ thống có thể dừng:

```text
venue
asset_class
market_segment
region
```

Nhưng phải giữ scope rõ ràng.

---

# 45. Broker

```axiom
struct Broker {
    id: BrokerId
    participant: ParticipantId
    venues: VenueSet
    clients: ClientSet
}
```

Broker cung cấp:

```text
order_routing
client_gateway
risk_checks
execution_services
```

---

# 46. Broker ≠ exchange

Broker gửi order tới venue.

Exchange/venue thực hiện matching.

---

# 47. Smart order routing

```text
Order
→ VenueDiscovery
→ LiquidityAnalysis
→ CostAnalysis
→ RouteSelection
→ ChildOrders
```

---

# 48. Routing policy

Inputs:

```text
price
liquidity
latency
fees
market_impact
fill_probability
venue_constraints
```

Output:

```text
RoutePlan
```

Không phải guaranteed fill.

---

# 49. Execution algorithm

Native abstractions:

```text
TWAP
VWAP
POV
ImplementationShortfall
ArrivalPrice
LiquiditySeeking
IcebergExecution
CustomExecution
```

---

# 50. Execution parent/child model

```text
ParentOrder
 ├── ChildOrder
 ├── ChildOrder
 └── ChildOrder
```

Parent quantity phải reconcile với children.

---

# 51. Execution report

```axiom
struct ExecutionReport {
    order: OrderId
    trade: TradeId
    quantity: Decimal
    price: Price
    fees: Money
    venue: VenueId
    timestamp: Timestamp
}
```

---

# 52. Slippage

Phải hỗ trợ:

```text
arrival_price
decision_price
mid_price
VWAP
benchmark_price
```

và tính:

```text
implementation_shortfall
```

với benchmark explicit.

---

# 53. Transaction cost analysis

```text
SpreadCost
Commission
VenueFee
MarketImpact
TimingCost
OpportunityCost
Tax
```

---

# 54. Clearing

Sau trade:

```text
Trade
→ Clearing
```

Clearing xác định:

```text
obligations
net_positions
margin
collateral
counterparty_exposure
```

---

# 55. Clearing member

```axiom
struct ClearingMember {
    id: ClearingMemberId
    participant: ParticipantId
    collateral_account: AccountRef
}
```

---

# 56. Clearing house

```axiom
struct ClearingHouse {
    id: ClearingHouseId
    members: MemberSet
    products: ProductSet
    risk_model: RiskModelRef
}
```

---

# 57. Central counterparty

Optional CCP model:

```text
Buyer
  ↓
CCP
  ↑
Seller
```

CCP semantics phải được explicit.

---

# 58. Netting

Netting:

```text
gross obligations
→ net obligations
```

Types:

```text
TradeNetting
PaymentNetting
PositionNetting
CrossProductNetting
```

---

# 59. Netting invariant

Netting không được làm mất:

```text
gross_trade_history
```

Nó chỉ tạo net obligation.

---

# 60. Margin

Types:

```text
InitialMargin
VariationMargin
MaintenanceMargin
AdditionalMargin
IntradayMargin
```

---

# 61. Collateral

```axiom
struct CollateralPosition {
    asset: AssetRef
    quantity: Decimal
    value: Money
    haircut: Ratio
    eligibility: EligibilityStatus
}
```

---

# 62. Collateral valuation

```text
market_value
→ haircut
→ collateral_value
```

Valuation source phải explicit.

---

# 63. Margin call

Lifecycle:

```text
Detected
→ Calculated
→ Issued
→ Funded
→ Verified
→ Closed
```

Branches:

```text
Disputed
Failed
Escalated
```

---

# 64. Settlement

Settlement có:

```text
Delivery
Payment
DvP
PvP
FreeOfPayment
```

---

# 65. Delivery-versus-payment

Core invariant:

```text
security delivery
AND
payment
```

phải được atomically linked khi settlement model là DvP.

---

# 66. Settlement cycle

Settlement instruction:

```text
TradeDate
SettlementDate
SettlementStatus
```

Không hard-code T+2/T+1; cycle là venue/instrument rule.

---

# 67. Settlement failure

```text
Pending
→ Failed
→ Repair
→ Resubmit
→ Settled
```

Failure không được tự động coi là fraud.

---

# 68. Settlement instruction

```axiom
struct SettlementInstruction {
    trade: TradeId
    buyer_account: AccountRef
    seller_account: AccountRef
    security_quantity: Decimal
    cash_amount: Money
    settlement_date: Date
}
```

---

# 69. Settlement agent

```text
SettlementAgent
CentralSecuritiesDepository
Custodian
PayingAgent
TransferAgent
```

Provider abstraction.

---

# 70. Custody

Custody interface:

```text
Position
→ CustodyAccount
→ Settlement
```

Custody ≠ ownership semantics.

---

# 71. Central securities depository

```text
CSD
SecurityRegister
BookEntry
SettlementAccount
```

Legal authority có thể thuộc external jurisdiction.

---

# 72. Securities register

```axiom
struct SecurityHoldingRecord {
    security: SecurityId
    account: AccountId
    quantity: Decimal
    status: HoldingStatus
}
```

---

# 73. Primary market

Primary issuance lifecycle:

```text
Proposed
→ Registered
→ Offered
→ Allocated
→ Issued
→ Listed
```

---

# 74. Issuance

Core entities:

```text
Issuer
Issue
Offering
Subscription
Allocation
Settlement
```

---

# 75. IPO / public offering

Generic pipeline:

```text
Issuer
→ Offering
→ Orders
→ Allocation
→ Settlement
→ Listing
```

Regulatory approval thuộc `AXLAW/AXGOV`.

---

# 76. Allocation mechanism

Có thể hỗ trợ:

```text
ProRata
Priority
Auction
BookBuilding
FixedPrice
Custom
```

---

# 77. Book building

Entities:

```text
InvestorIndication
PriceRange
DemandCurve
AllocationRule
FinalPrice
```

Indication ≠ binding trade.

---

# 78. Secondary market

```text
ListedSecurity
→ Order
→ Match
→ Trade
→ Clear
→ Settle
```

---

# 79. OTC market

OTC supports:

```text
QuoteRequest
Quote
Negotiation
TradeConfirmation
Clearing
Settlement
```

---

# 80. RFQ

```axiom
RFQ {
    instrument
    quantity
    side
    settlement_terms
    expiry
}
```

---

# 81. Dealer quote

```axiom
Quote {
    dealer
    bid
    ask
    size
    expiry
}
```

Quote validity phải explicit.

---

# 82. OTC confirmation

Hai bên phải reconcile:

```text
instrument
quantity
price
counterparty
settlement
fees
```

---

# 83. Derivatives

Generic:

```text
DerivativeContract
Underlying
Strike
Expiry
SettlementMethod
Payoff
Margin
```

---

# 84. Option

```text
Call
Put
American
European
Bermudan
Asian
Barrier
Digital
CustomPayoff
```

---

# 85. Future

```text
FutureContract
ContractSize
Expiry
SettlementMethod
VariationMargin
```

---

# 86. Swap

```text
SwapContract
Leg[]
PaymentSchedule
ReferenceRate
Notional
```

---

# 87. Derivative valuation boundary

Pricing engine:

```text
AXMARKET
  └── PricingProvider
```

có thể gọi native or external implementation.

---

# 88. Securities lending

```text
LoanRequest
Loan
Collateral
Recall
Return
```

---

# 89. Repo

```text
RepoAgreement
Collateral
CashLeg
RepurchaseDate
RepoRate
Haircut
```

---

# 90. Short selling

Short sale phải yêu cầu explicit capability:

```text
short_sell
borrow_security
```

Không tự động cho phép negative position.

---

# 91. Borrow lifecycle

```text
Locate
→ Borrow
→ Sell
→ Maintain
→ Recall
→ Return
```

---

# 92. Corporate actions

Market infrastructure must distribute:

```text
Dividend
Coupon
Split
Merger
SpinOff
Rights
Redemption
Tender
Conversion
```

---

# 93. Corporate action processing

```text
Announcement
→ EligibilityDate
→ RecordDate
→ ExDate
→ Payment/EffectiveDate
→ Reconciliation
```

Dates phải là instrument-specific.

---

# 94. Market reference data

```text
Issuer
Instrument
Venue
Currency
Calendar
Sector
Country
TradingStatus
```

---

# 95. Reference-data versioning

Không overwrite lịch sử reference data.

```text
InstrumentVersion
VenueVersion
ClassificationVersion
```

---

# 96. Market surveillance

Signals:

```text
AbnormalVolume
PriceSpike
LayeringSignal
SpoofingSignal
WashTradeSignal
CrossMarketAnomaly
InsiderTradingSignal
MarketManipulationSignal
```

Các signal chỉ là detection outputs.

---

# 97. Legal determination boundary

```text
AnomalySignal ≠ LegalViolation
Suspicion ≠ Finding
Detection ≠ EnforcementDecision
```

Legal determination chuyển sang `AXLAW/AXGOV`.

---

# 98. Surveillance engine

```text
MarketEvents
→ FeatureExtraction
→ PatternDetection
→ RiskScore
→ Alert
→ InvestigationRef
```

---

# 99. AI surveillance

AI có thể:

```text
cluster_trades
detect_patterns
detect_anomalies
summarize_events
prioritize_investigation
```

Không tự tạo legal finding.

---

# 100. AI trading agent

Agent có:

```text
Principal
Strategy
CapitalLimit
OrderLimit
RiskLimit
VenueScope
InstrumentScope
TimeWindow
KillSwitch
```

---

# 101. AI execution boundary

```text
AI
→ Signal
→ Strategy
→ OrderProposal
→ RiskCheck
→ Authorization
→ Order
```

---

# 102. Kill switch

Mọi autonomous trading agent phải hỗ trợ:

```text
pause
cancel_open_orders
disable_new_orders
disable_strategy
revoke_capability
```

Kill switch phải nằm ngoài agent authority.

---

# 103. Fat-finger protection

Pre-trade checks:

```text
max_quantity
max_notional
max_price_deviation
max_order_rate
max_daily_loss
max_position
```

---

# 104. Rate limiting

Market participant có:

```text
orders_per_second
messages_per_second
cancels_per_second
notional_per_day
```

---

# 105. Order throttling

Nếu vượt limit:

```text
Throttle
Reject
Queue
Escalate
```

policy quyết định.

---

# 106. Pre-trade risk

```text
CreditLimit
Margin
PositionLimit
NotionalLimit
PriceBand
Concentration
RestrictedList
MarketStatus
```

---

# 107. Post-trade risk

```text
Exposure
P&L
Margin
Liquidity
Counterparty
Settlement
Concentration
```

---

# 108. Market risk

Có thể expose:

```text
Delta
Gamma
Vega
Theta
Duration
DV01
CS01
Beta
FactorExposure
```

Derivative-specific metrics optional.

---

# 109. Position limit

Venue/member policy có:

```text
MaxPosition
MaxOrder
MaxNotional
MaxExposure
```

---

# 110. Counterparty risk

```axiom
struct CounterpartyExposure {
    counterparty: EntityRef
    gross: Money
    net: Money
    collateral: Money
    replacement_cost: Money
}
```

---

# 111. Default management

Generic lifecycle:

```text
DefaultDetected
→ Freeze
→ MarginReview
→ Closeout
→ Netting
→ CollateralLiquidation
→ Settlement
→ Resolution
```

Legal insolvency semantics thuộc legal layer.

---

# 112. Market resilience

Venue phải hỗ trợ:

```text
failover
replication
checkpoint
replay
sequence_recovery
hot_standby
cold_recovery
```

---

# 113. Matching-engine determinism

Cùng:

```text
initial_book
event_sequence
matching_rules
```

phải tạo cùng:

```text
trade_sequence
final_book
```

trong deterministic mode.

---

# 114. Event sequencing

Global event:

```text
EventId
Sequence
VenueSequence
Timestamp
Source
```

Không dùng timestamp làm唯一 ordering key.

---

# 115. Nanosecond timestamps

Runtime có thể hỗ trợ:

```text
TimestampNs
```

nhưng semantic ordering vẫn dựa vào sequence number khi venue cung cấp sequence.

---

# 116. Market event log

Append-only:

```text
OrderAccepted
OrderRejected
OrderCancelled
OrderReplaced
TradeCreated
TradeBusted
AuctionStarted
AuctionMatched
MarketHalted
MarketResumed
CorporateActionPublished
```

---

# 117. Replay

```axiom
market.replay(
    venue,
    sequence_start,
    sequence_end
)
```

trả reconstructed market state.

---

# 118. Historical market database

Native schema:

```text
Instrument
Venue
Event
Quote
Trade
BookSnapshot
CorporateAction
Session
```

Columnar storage được ưu tiên.

---

# 119. Tick data

Hỗ trợ:

```text
TradeTick
QuoteTick
BookDelta
BookSnapshot
```

---

# 120. Book delta

```axiom
struct BookDelta {
    side
    price
    quantity_delta
    sequence
}
```

---

# 121. Full-depth market data

Profile có thể bật:

```text
L1
L2
L3
```

Trong đó:

```text
L1 = top-of-book
L2 = aggregated depth
L3 = order-level depth
```

---

# 122. Market data subscriptions

```axiom
subscribe_quotes()
subscribe_trades()
subscribe_book()
subscribe_auction()
subscribe_corporate_actions()
```

---

# 123. Backpressure

Market-data consumer phải có:

```text
buffer
drop_policy
checkpoint
resume_sequence
overflow_policy
```

Không được âm thầm mất dữ liệu trong authoritative replay mode.

---

# 124. Data compression

Hot market data hỗ trợ:

```text
delta_encoding
dictionary_encoding
bitpacking
columnar_compression
batch_compression
```

---

# 125. Zero-copy

Native APIs ưu tiên:

```text
BookView
QuoteView
TradeView
EventView
```

tránh copy trong hot path.

---

# 126. Memory layout

Matching engine ưu tiên:

```text
SoA
intrusive queues
arena allocation
preallocated pools
lock-free structures where proven
```

---

# 127. Concurrency model

Matching engine có thể chạy:

```text
single-thread deterministic core
+
parallel feed handlers
+
parallel risk calculators
+
parallel market-data publishers
```

Không parallelize critical book mutation nếu làm mất deterministic ordering.

---

# 128. Multi-venue concurrency

Mỗi venue có thể có:

```text
independent matching loop
```

Cross-venue routing hoạt động ở tầng trên.

---

# 129. Distributed exchange

Có thể phân vùng:

```text
venue
market_segment
instrument
partition
```

Nhưng một order book authoritative chỉ có một serialization authority tại một thời điểm.

---

# 130. Consensus boundary

Distributed control plane có thể dùng:

```text
membership
leader election
replication
consensus provider
```

nhưng matching semantics không được mơ hồ.

---

# 131. Exchange recovery

Recovery sequence:

```text
snapshot
→ event replay
→ sequence verification
→ book validation
→ trading resume
```

---

# 132. Book validation

Invariant:

```text
quantity >= 0
price valid
order references valid
aggregate == order sum
sequence monotonic
```

---

# 133. Trade validation

Trade phải reference:

```text
valid buy order
valid sell order
valid venue
valid instrument
valid quantity
valid price
```

---

# 134. Settlement validation

Settlement instruction phải reference:

```text
valid trade
valid account
valid security
valid cash amount
valid date
```

---

# 135. Settlement atomicity

DvP:

```text
if security_delivery && cash_delivery
    commit both
else
    commit neither
```

trừ settlement model có partial settlement explicit.

---

# 136. Partial settlement

Nếu venue cho phép:

```text
PartialDelivery
PartialPayment
PartialSettlement
```

phải explicit và audit.

---

# 137. Failed settlement queue

```text
SettlementExceptionQueue
```

cho phép:

```text
repair
retry
substitute
escalate
cancel
```

---

# 138. Reconciliation

Reconcile:

```text
Orders
↔ Trades
↔ Clearing
↔ Settlement
↔ Custody
↔ AXFINANCE
```

Mismatch phải tạo immutable exception.

---

# 139. Market fees

```text
ExchangeFee
BrokerFee
ClearingFee
SettlementFee
RegulatoryFee
DataFee
```

Fee schedule versioned.

---

# 140. Fee calculation

```text
FeeSchedule
→ FeeRule
→ FeeCalculation
→ FeeAmount
```

Không hard-code fee trong matching engine.

---

# 141. Tick size

Instrument rule:

```text
TickSize
PriceBand
LotSize
MinQuantity
```

---

# 142. Quantity constraints

```text
MinOrderSize
LotSize
StepSize
MaxOrderSize
```

---

# 143. Price validation

```text
price % tick_size == 0
```

hoặc venue-specific rounding rule.

---

# 144. Currency precision

Price precision và money precision phải độc lập:

```text
PricePrecision
CurrencyMinorUnit
QuantityPrecision
```

---

# 145. Market status

```text
Open
Closed
Halted
PreOpen
Auction
Suspended
Emergency
```

---

# 146. Instrument status

```text
Active
Suspended
Matured
Redeemed
Delisted
Cancelled
Expired
```

---

# 147. Delisting

```text
Announced
LastTradingDate
TradingStopped
Settlement
Archived
```

Không xóa historical trades.

---

# 148. Maturity

Debt instrument:

```text
Issued
Active
Matured
Redeemed
```

Derivative:

```text
Active
Expired
Exercised
Settled
```

---

# 149. Exercise

Option exercise:

```text
ExerciseRequest
→ EligibilityCheck
→ Exercise
→ Assignment
→ Settlement
```

---

# 150. Assignment

Assignment event phải có:

```text
option
quantity
assigned_participant
timestamp
method
```

---

# 151. Primary/secondary integration

```text
PRIMARY MARKET
     ↓
ISSUANCE
     ↓
SECURITY
     ↓
SECONDARY MARKET
     ↓
TRADING
```

---

# 152. Market registry

Global registry:

```text
MarketRegistry
 ├── Venues
 ├── Instruments
 ├── Participants
 ├── ClearingHouses
 ├── SettlementSystems
 └── Calendars
```

---

# 153. Jurisdiction

Market object có:

```text
jurisdiction
regulatory_ref
legal_entity
```

Không hard-code một legal system.

---

# 154. Regulatory integration

Interfaces:

```text
AXLAW
AXGOV
AX639
AX640
```

cho:

```text
market_rule
participant_eligibility
reporting
retention
audit
compliance
```

---

# 155. Market reporting

Reports:

```text
TradeReport
OrderReport
PositionReport
TransactionReport
ShortPositionReport
RiskReport
SettlementReport
MarketActivityReport
```

---

# 156. Regulatory reporting boundary

AXMARKET tạo structured facts.

Regulatory submission format thuộc jurisdiction/provider layer.

---

# 157. Privacy

Market transparency policy phải phân biệt:

```text
public
participant-visible
regulator-visible
internal
private
```

---

# 158. Confidentiality

Order-level information phải được capability-protected.

Không được để một participant đọc private orders của participant khác nếu venue policy không cho phép.

---

# 159. Fairness of market access

Venue policy có thể khai báo:

```text
latency_class
access_fee
order_type_access
participant_class
```

Market infrastructure phải expose các rule này minh bạch trong machine-readable form.

---

# 160. AI market simulation

Simulation entities:

```text
MarketAgent
InvestorAgent
BrokerAgent
MarketMakerAgent
LiquidityAgent
ArbitrageAgent
```

---

# 161. Agent market behavior

Simulation có thể mô hình hóa:

```text
order_submission
cancellation
market_making
inventory_management
liquidity_provision
risk_response
```

---

# 162. Market microstructure simulation

Variables:

```text
spread
depth
queue_position
order_arrival
cancellation_rate
trade_rate
market_impact
latency
```

---

# 163. Market simulator

```axiom
simulate_market {
    venue: NYSE_like
    participants: 100000
    instruments: 10000

    model {
        order_arrival: stochastic
        cancellation: stochastic
        liquidity: regime_based
    }
}
```

Tên venue chỉ là simulation label nếu không kết nối venue thật.

---

# 164. Flash-event simulation

Có thể mô phỏng:

```text
liquidity_shock
mass_cancellation
price_gap
venue_outage
latency_spike
margin_cascade
```

---

# 165. Systemic market simulation

```text
Market
→ Banks
→ Funds
→ Insurers
→ Corporations
→ Households
```

kết nối với:

```text
AXBANKING
AXINVEST
AXINSURANCE
AX671
```

---

# 166. Market contagion

Simulation graph:

```text
Participant
→ Position
→ Market
→ Price
→ Margin
→ Funding
→ ForcedSale
→ Price
```

Kết quả chỉ là scenario.

---

# 167. Forced-sale simulation

Có thể tính:

```text
liquidation_quantity
market_impact
margin_effect
liquidity_gap
```

---

# 168. Market stress

Stress dimensions:

```text
volatility
spread
depth
latency
default
funding
margin
settlement
```

---

# 169. AI market maker

Agent cần:

```text
inventory_limit
spread_policy
risk_limit
capital_limit
kill_switch
```

---

# 170. Market maker quote

```axiom
quote {
    bid
    ask
    bid_size
    ask_size
    expiry
}
```

Quote phải có TTL.

---

# 171. Market maker inventory

```text
TargetInventory
CurrentInventory
InventoryRisk
InventoryLimit
```

---

# 172. Liquidity metrics

```text
BidAskSpread
Depth
AmihudLikeMetric
Turnover
Volume
MarketImpactEstimate
FillRate
OrderBookImbalance
```

Metric methodology phải explicit.

---

# 173. Queue position

L3 engine phải hỗ trợ:

```text
OrderQueuePosition
EstimatedQueuePosition
ActualQueuePosition
```

Không nhầm estimated với actual.

---

# 174. Latency model

Có thể đo:

```text
client_to_gateway
gateway_to_matching
matching_to_ack
matching_to_trade
trade_to_marketdata
```

---

# 175. Latency timestamp provenance

Mỗi latency measurement phải biết:

```text
clock_source
clock_precision
measurement_point
synchronization_status
```

---

# 176. Clock model

Runtime hỗ trợ:

```text
MonotonicClock
WallClock
ExchangeClock
LogicalSequence
```

Matching không dùng wall clock làm primary ordering mechanism.

---

# 177. Market data normalization

Different providers map vào canonical:

```text
CanonicalInstrument
CanonicalVenue
CanonicalQuote
CanonicalTrade
CanonicalBookEvent
```

---

# 178. Symbol mapping

```text
ProviderSymbol
→ SymbolMapping
→ InstrumentId
```

Mapping phải versioned.

---

# 179. Data correction

Market data correction:

```text
OriginalEvent
→ CorrectionEvent
```

không overwrite raw historical evidence.

---

# 180. Corporate action adjustment

Historical prices có thể có:

```text
RawPrice
AdjustedPrice
```

Cả hai phải tồn tại khi applicable.

---

# 181. Backtest integration

```text
AXINVEST
    ↓
AXMARKET Historical Simulator
    ↓
ExecutionModel
    ↓
Portfolio
```

---

# 182. Real-vs-simulation boundary

```text
MarketSimulator
≠
LiveExchange
```

Compiler/runtime phải enforce mode.

---

# 183. Paper trading

Paper exchange có:

```text
simulated_order_book
simulated_execution
simulated_settlement
```

không chạm production market.

---

# 184. Sandbox

Capabilities:

```text
market.simulate
market.replay
market.paper_trade
```

không bao gồm:

```text
market.live_order
```

---

# 185. Live trading capability

Explicit:

```text
market.live_order.create
```

phải là high-trust capability.

---

# 186. Capability separation

```text
market.data.read
market.order.create
market.order.cancel
market.order.replace
market.execution.read
market.clearing.read
market.settlement.read
market.admin
```

Không gộp thành một quyền `market.full` trong core security model.

---

# 187. Autonomous live trading

Phải yêu cầu:

```text
principal
mandate
risk_limit
capital_limit
execution_limit
kill_switch
audit
```

---

# 188. Emergency shutdown

System-level capability:

```text
market.emergency_halt
```

không thể bị agent trading thu hồi.

---

# 189. Audit

Immutable records:

```text
Order
OrderChange
Trade
TradeBust
RiskCheck
RouteDecision
Clearing
Settlement
MarginCall
CollateralChange
CorporateAction
MarketHalt
```

---

# 190. Event integrity

Event chain có thể dùng:

```text
hash
previous_hash
signature
sequence
```

để phát hiện tampering.

---

# 191. Cryptographic integration

Signing primitives lấy từ:

```text
AX610
```

AXMARKET không tự tạo cryptography implementation thứ hai.

---

# 192. High availability

Critical services:

```text
Matching
OrderGateway
MarketData
RiskGateway
Clearing
Settlement
```

phải có HA profile.

---

# 193. Recovery Point Objective

Market runtime phải định nghĩa:

```text
RPO
RTO
```

theo deployment profile.

---

# 194. Hot failover

Matching engine failover phải preserve:

```text
last_committed_sequence
order_book_snapshot
open_orders
session_state
```

---

# 195. Split-brain protection

Chỉ một matching authority được phép commit trades cho một `(venue, instrument, partition)` tại một thời điểm.

---

# 196. Duplicate execution prevention

Trade identity phải idempotent:

```text
TradeId
ExecutionId
VenueSequence
```

---

# 197. Settlement idempotency

Settlement instruction phải có:

```text
SettlementInstructionId
```

retry không tạo duplicate settlement.

---

# 198. Clearing idempotency

Netting batch có:

```text
ClearingBatchId
```

Replay không double-net.

---

# 199. Market integrity invariant

Không được có:

```text
trade.quantity >
buy_remaining_quantity
```

hoặc:

```text
trade.quantity >
sell_remaining_quantity
```

---

# 200. Order-book integrity

Sau mỗi event:

```text
book_quantity >= 0
order_quantity >= 0
```

---

# 201. Execution integrity

Mỗi fill phải:

```text
reduce order remaining quantity
create execution/trade record
```

atomic trong matching transaction.

---

# 202. Clearing integrity

Mọi cleared trade phải trace về:

```text
original trade
```

---

# 203. Settlement integrity

Mọi settled instruction phải trace về:

```text
cleared obligation
```

---

# 204. Financial integrity

Mọi cash settlement phải reconcile với:

```text
AXFINANCE
```

---

# 205. Position integrity

Mọi security movement phải reconcile với:

```text
custody / securities register
```

---

# 206. Market-state integrity

Market state phải có:

```text
snapshot_version
event_sequence
venue
instrument
timestamp
```

---

# 207. Deterministic replay invariant

```text
same snapshot
+
same event stream
+
same rules
=
same state
```

trong deterministic profile.

---

# 208. Performance target

Reference targets:

```text
sub-millisecond internal matching
high-throughput order ingestion
millions of events/second per optimized deployment
zero-copy market data path
bounded allocation in hot path
```

Benchmark cuối cùng phụ thuộc hardware và deployment architecture.

---

# 209. Memory architecture

Hot path ưu tiên:

```text
preallocated pools
arena allocation
intrusive queues
compact IDs
SoA
cache-aligned structures
lock-free queues where justified
```

---

# 210. No GC requirement

Matching engine không được phụ thuộc garbage collector.

Object lifetime phải deterministic hoặc pool-managed.

---

# 211. Compiler optimization

Compiler được phép:

```text
inline
devirtualize
specialize
vectorize
unroll
constant_fold
dead-code eliminate
layout-optimize
```

khi semantic contract được giữ nguyên.

---

# 212. Native IR

```text
MKT_INSTRUMENT
MKT_VENUE
MKT_SESSION
MKT_ORDER
MKT_ORDER_CANCEL
MKT_ORDER_REPLACE
MKT_BOOK
MKT_MATCH
MKT_TRADE
MKT_AUCTION
MKT_QUOTE
MKT_CLEAR
MKT_NET
MKT_MARGIN
MKT_COLLATERAL
MKT_SETTLE
MKT_CORPORATE_ACTION
MKT_SURVEILLANCE
MKT_REPLAY
MKT_SIMULATION
```

---

# 213. SIMD kernels

Có thể vectorize:

```text
risk checks
price-band checks
fee calculation
market-data normalization
portfolio exposure aggregation
surveillance features
```

Matching queue mutation vẫn giữ ordering semantics.

---

# 214. GPU boundary

GPU phù hợp:

```text
surveillance
risk
simulation
pricing
historical analytics
Monte Carlo
```

Không mặc định đưa serial order matching lên GPU.

---

# 215. Distributed market analytics

Có thể partition theo:

```text
instrument
venue
time
market_segment
```

---

# 216. Global market graph

```text
GlobalMarket
├── Region
│   ├── Venue
│   ├── Participant
│   ├── Clearing
│   └── Settlement
└── CrossMarketLinks
```

---

# 217. Cross-market trading

Một strategy có thể:

```text
VenueA
→ VenueB
→ VenueC
```

nhưng mỗi venue vẫn có independent execution semantics.

---

# 218. Cross-market arbitrage simulation

Simulation có thể tính:

```text
price_difference
latency
fees
slippage
settlement_risk
```

Không giả định arbitrage là risk-free.

---

# 219. Cross-currency trading

```text
SecurityCurrency
TradingCurrency
SettlementCurrency
BaseCurrency
```

phải explicit.

---

# 220. FX market

AXMARKET có thể represent:

```text
FXPair
FXQuote
FXOrder
FXTrade
FXSettlement
```

FX-specific venue implementations là extension.

---

# 221. Fixed-income market

Hỗ trợ:

```text
Bond
Yield
Coupon
Duration
Maturity
CreditSpread
Quote
RFQ
Trade
Settlement
```

---

# 222. Yield curve

```text
YieldCurve
CurvePoint
InterpolationMethod
BootstrappingMethod
```

Curve versioned theo timestamp.

---

# 223. Bond accrued interest

```text
CleanPrice
DirtyPrice
AccruedInterest
```

phải tách biệt.

---

# 224. Money-market instruments

```text
TBill
CommercialPaper
CertificateOfDepositRef
Repo
```

---

# 225. Fund trading

Fund unit transactions:

```text
Subscription
Redemption
Transfer
Distribution
```

NAV calculation thuộc `AXINVEST`; market venue có thể list fund units.

---

# 226. ETF

ETF có:

```text
PrimaryCreation
PrimaryRedemption
SecondaryTrading
Basket
NAV
IndicativeNAV
```

---

# 227. Creation/redemption

```text
CreationRequest
→ BasketDelivery
→ UnitIssuance
```

và:

```text
RedemptionRequest
→ UnitReturn
→ BasketDelivery
```

---

# 228. REIT / listed real assets

AXMARKET chỉ xử lý listed security.

Underlying real estate thuộc `AXHOUSING`.

---

# 229. Digital securities

Có thể hỗ trợ:

```text
TokenizedSecurityRef
DigitalRegisterRef
```

nhưng legal ownership semantics vẫn external/legal.

---

# 230. Tokenized settlement

Settlement provider có thể triển khai:

```text
AtomicDelivery
ProgrammableSettlement
```

nhưng core AXMARKET không phụ thuộc blockchain.

---

# 231. Blockchain boundary

Blockchain là optional settlement provider:

```text
AXMARKET
→ SettlementProvider
→ BlockchainProvider
```

Không phải mandatory architecture.

---

# 232. Market API

Core:

```text
axmarket.instrument
axmarket.venue
axmarket.session
axmarket.order
axmarket.book
axmarket.trade
axmarket.auction
axmarket.broker
axmarket.route
axmarket.clearing
axmarket.margin
axmarket.collateral
axmarket.settlement
axmarket.custody
axmarket.data
axmarket.surveillance
axmarket.simulation
```

---

# 233. CLI

```text
axiom market venue show
axiom market instrument show
axiom market book show
axiom market orders
axiom market trades
axiom market replay
axiom market risk
axiom market clearing
axiom market settlement
axiom market surveillance
axiom market simulate
```

---

# 234. DSL — venue

```axiom
venue GlobalEquities {
    session {
        pre_open: 08:30
        continuous: 09:00..14:30
        close: 14:30
    }

    matching: price_time
    settlement: DVP
}
```

---

# 235. DSL — instrument

```axiom
security ExampleEquity {
    class: equity
    currency: USD
    tick_size: 0.01
    lot_size: 1
}
```

---

# 236. DSL — order

```axiom
order {
    instrument: ExampleEquity
    side: buy
    quantity: 100
    type: limit
    price: 125.50
    tif: day
}
```

---

# 237. DSL — trading agent

```axiom
agent ExecutionBot {
    strategy: VWAP

    limits {
        max_notional: 1000000
        max_position: 50000
        max_order_rate: 100
    }

    permissions {
        market.data.read
        market.order.create
        market.order.cancel
    }
}
```

---

# 238. DSL — surveillance

```axiom
surveillance {
    detect abnormal_volume
    detect order_book_anomaly
    detect cross_market_anomaly

    emit Alert
}
```

---

# 239. DSL — market simulation

```axiom
simulate_market {
    instruments: 10000
    agents: 100000
    duration: 1y

    market {
        liquidity: stochastic
        volatility: regime_switching
        order_flow: agent_based
    }
}
```

---

# 240. Security profiles

```text
AXMARKET_NONE
AXMARKET_CORE
AXMARKET_INSTRUMENT
AXMARKET_DATA
AXMARKET_ORDER
AXMARKET_MATCHING
AXMARKET_BROKER
AXMARKET_CLEARING
AXMARKET_MARGIN
AXMARKET_COLLATERAL
AXMARKET_SETTLEMENT
AXMARKET_CUSTODY
AXMARKET_PRIMARY
AXMARKET_DERIVATIVES
AXMARKET_SURVEILLANCE
AXMARKET_SIMULATION
AXMARKET_AI
AXMARKET_HFT
AXMARKET_DISTRIBUTED
AXMARKET_GPU
AXMARKET_WASM
AXMARKET_MOBILE
AXMARKET_GLOBAL
AXMARKET_FULL
```

---

# 241. Minimal profile

`AXMARKET_CORE`:

```text
Instrument
Venue
Session
Order
OrderBook
Trade
MarketData
```

Không cần clearing/settlement để compile một local market simulator.

---

# 242. HFT profile

`AXMARKET_HFT` bổ sung:

```text
low-latency networking
preallocated memory
lock-free queues
kernel-bypass provider boundary
high-resolution timestamps
L3 book
co-location metadata
```

Các provider low-level là optional.

---

# 243. WASM profile

WASM có thể hỗ trợ:

```text
market replay
book visualization
strategy simulation
historical analysis
```

Không expose live trading capability mặc định.

---

# 244. Mobile profile

Mobile:

```text
market data
portfolio
order status
execution reports
```

Live order capability phải được explicit.

---

# 245. Error model

```text
InstrumentNotFound
VenueNotFound
MarketClosed
OrderRejected
RiskLimitExceeded
PriceBandViolation
InsufficientMargin
InsufficientCollateral
MatchingFailure
ClearingFailure
SettlementFailure
SequenceGap
MarketDataStale
MarketDataCorrupt
DuplicateEvent
AuthorizationDenied
ProviderUnavailable
```

---

# 246. Recovery model

```text
OrderGateway
→ durable journal
→ matching
→ event log
→ clearing
→ settlement
```

Mỗi stage có checkpoint riêng.

---

# 247. Disaster recovery

Recovery phải kiểm tra:

```text
event sequence
book checksum
trade checksum
order state
clearing obligations
settlement obligations
```

---

# 248. Testing architecture

Test categories:

```text
unit
property
invariant
matching
auction
order_lifecycle
market_data
replay
clearing
netting
margin
settlement
corporate_action
surveillance
security
AI
simulation
distributed
failure
performance
```

---

# 249. Matching tests

Bắt buộc:

```text
price priority
time priority
partial fills
multiple fills
cancel race
replace race
auction
halt
resume
```

---

# 250. Determinism tests

```text
same_event_stream
→ same_trades
→ same_final_book
```

---

# 251. Concurrency tests

Kiểm tra:

```text
order arrival
cancel arrival
replace arrival
market halt
risk update
```

theo nhiều scheduling order hợp lệ.

---

# 252. Security tests

```text
unauthorized_order
cross_account_order
capability_escalation
agent_bypass
private_order_leak
settlement_authority_bypass
kill_switch_bypass
```

---

# 253. Market manipulation detection tests

Synthetic datasets:

```text
spoofing_pattern
layering_pattern
wash_pattern
volume_anomaly
cross_market_pattern
```

Detection output phải là signal, không phải legal verdict.

---

# 254. Settlement tests

```text
DVP success
DVP failure
partial settlement
duplicate instruction
late settlement
wrong account
wrong security
wrong amount
```

---

# 255. Corporate-action tests

```text
split
dividend
coupon
merger
spin-off
rights
redemption
conversion
```

---

# 256. Market-data tests

```text
sequence_gap
duplicate
out_of_order
correction
stale
provider_switch
reconnect
replay
```

---

# 257. Performance tests

Reference:

```text
order ingestion throughput
matching latency
market-data fanout
book update latency
risk calculation
surveillance throughput
replay speed
recovery speed
```

---

# 258. AI tests

Test:

```text
hallucinated order
unauthorized trading
risk-limit bypass
fake market-data injection
prompt injection
malicious strategy
capital escalation
kill-switch resistance
```

---

# 259. Simulation tests

```text
seed reproducibility
agent determinism
market-state isolation
production-state isolation
scenario provenance
```

---

# 260. Required architecture invariants

```text
I-01 Order ≠ Trade
I-02 Trade ≠ Settlement
I-03 Settlement ≠ Ledger
I-04 Quote ≠ Trade
I-05 Bid ≠ Ask
I-06 Price ≠ Value
I-07 Simulation ≠ LiveMarket
I-08 Broker ≠ Exchange
I-09 Clearing ≠ Settlement
I-10 Custodian ≠ Owner
I-11 Signal ≠ LegalFinding
I-12 IndicativePrice ≠ ExecutedPrice
I-13 OrderCancel ≠ CancelEffective
I-14 TradeBust never deletes historical evidence
I-15 Order history is immutable
I-16 Trade history is immutable
I-17 Matching is deterministic in deterministic mode
I-18 Book mutation and fill creation are atomic
I-19 Trade quantity cannot exceed executable quantity
I-20 Negative position requires explicit short authority
I-21 DvP must preserve atomic delivery semantics
I-22 Settlement retry cannot duplicate settlement
I-23 Clearing retry cannot duplicate obligation
I-24 Simulation cannot mutate production
I-25 AI cannot escalate authority
I-26 Kill switch cannot be overridden by trading agent
I-27 Market-data gaps are detectable
I-28 Market-data corrections preserve original evidence
I-29 Every trade has venue and instrument identity
I-30 Every settlement has trade provenance
I-31 Every autonomous order has authorization provenance
I-32 Every market event has sequence identity
I-33 Every fee calculation has versioned schedule
I-34 Every price has precision/tick semantics
I-35 Every quantity has lot/precision semantics
I-36 Cross-market execution does not imply atomic cross-market settlement
I-37 Regulatory signal is not legal determination
I-38 Legal ownership is not inferred from trading exposure
I-39 Financial settlement reconciles with AXFINANCE
I-40 Investment intent originates from AXINVEST or authorized market participant
```

---

# 261. Required test target

Mục tiêu:

```text
≥ 20,000 automated tests
≥ 2,000 architecture invariants
≥ 3,000 matching/order-book tests
≥ 2,000 market-data/replay tests
≥ 2,000 clearing/settlement tests
≥ 1,500 security tests
≥ 1,500 AI/simulation tests
```

---

# 262. Acceptance criteria

`AXMARKET 5.0` hoàn tất khi:

1. Securities có canonical identity.
2. Venue có lifecycle và trading calendar.
3. Order lifecycle đầy đủ.
4. Order book hỗ trợ L1/L2/L3.
5. Matching engine deterministic.
6. Auction engine tồn tại.
7. Broker và exchange tách biệt.
8. Smart routing có policy.
9. Trade immutable.
10. Clearing tách khỏi settlement.
11. Netting được hỗ trợ.
12. Margin/collateral được mô hình hóa.
13. DvP được hỗ trợ.
14. Settlement failure có recovery.
15. Primary và secondary market được tách.
16. OTC/RFQ được hỗ trợ.
17. Derivative abstraction tồn tại.
18. Corporate action engine tồn tại.
19. Market data có sequence/replay.
20. Market surveillance có signal model.
21. AI trading có capability boundary.
22. Kill switch nằm ngoài agent.
23. Live và simulation bị tách.
24. Matching hot path không phụ thuộc GC.
25. Native IR tồn tại.
26. GPU/CPU analytics được hỗ trợ.
27. Distributed recovery có deterministic state.
28. Reconciliation với AXFINANCE tồn tại.
29. Investment integration với AXINVEST tồn tại.
30. Legal/regulatory boundary với AXLAW/AXGOV tồn tại.
31. Không có third-party runtime bắt buộc.
32. Có đầy đủ test/invariant contract.

---

# 263. Final AXMARKET architecture

```text
                         AXMARKET
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
   SECURITIES            VENUES              PARTICIPANTS
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                       ORDER GATEWAY
                            │
                     PRE-TRADE RISK
                            │
                    SMART ROUTING
                            │
                 ┌──────────┴──────────┐
                 │                     │
              EXCHANGE               OTC
                 │                     │
             ORDER BOOK              RFQ
                 │                     │
            MATCH ENGINE          NEGOTIATION
                 │                     │
                 └──────────┬──────────┘
                            │
                           TRADE
                            │
                        CLEARING
                            │
                    NETTING / MARGIN
                            │
                       COLLATERAL
                            │
                       SETTLEMENT
                            │
                     CUSTODY / CSD
                            │
                        AXFINANCE
```

---

# 264. Toàn bộ financial execution chain

```text
AXBANKING
    │
    ▼
CAPITAL
    │
    ▼
AXINVEST
    │
    ├── Research
    ├── Portfolio
    ├── Allocation
    ├── Risk
    └── InvestmentDecision
             │
             ▼
         AXMARKET
             │
             ├── Order
             ├── Routing
             ├── Matching
             ├── Trade
             ├── Clearing
             ├── Margin
             ├── Settlement
             └── CustodyRef
                     │
                     ▼
                 AXFINANCE
```

---

# 265. Civilization-scale capital-market loop

```text
HOUSEHOLDS
    ↓
SAVINGS
    ↓
BANKS / FUNDS / INSURERS
    ↓
AXINVEST
    ↓
CAPITAL ALLOCATION
    ↓
AXMARKET
    ↓
SECURITIES / CAPITAL
    ↓
ENTERPRISES / INFRASTRUCTURE
    ↓
PRODUCTION
    ↓
INCOME / CASH FLOW
    ↓
SAVINGS
```

Market feedback:

```text
PRICE
 ↓
VALUATION
 ↓
CAPITAL COST
 ↓
INVESTMENT
 ↓
PRODUCTION
 ↓
CASH FLOW
 ↓
VALUATION
```

---

# 266. Final semantic contract

`AXMARKET` là **execution and market-infrastructure layer**, không phải investment-advisor layer và cũng không phải accounting ledger.

Ba lớp phải giữ đúng boundary:

```text
AXINVEST
    =
WHY / WHAT TO ALLOCATE

AXMARKET
    =
HOW CAPITAL IS TRADED / CLEARED / SETTLED

AXFINANCE
    =
HOW FINANCIAL TRUTH IS ACCOUNTED AND RECORDED
```

Do đó:

```text
InvestmentDecision
        ↓
OrderIntent
        ↓
Order
        ↓
Execution
        ↓
Trade
        ↓
Clearing
        ↓
Settlement
        ↓
FinancialLedger
```

là pipeline canonical của Axiom cho thị trường vốn.

---

# 267. Architecture chain sau BOOTSTRAP-693

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

và vòng phản hồi:

```text
CIVILIZATION
    ↓
SAVINGS
    ↓
CAPITAL
    ↓
INVESTMENT
    ↓
MARKET
    ↓
ENTERPRISE
    ↓
PRODUCTION
    ↓
INCOME
    ↓
SAVINGS
```

**BOOTSTRAP-693 hoàn tất.**

**Task kế tiếp: BOOTSTRAP-694 — Native AI Civilization-Scale Monetary System, Central Banking, Money Supply, Interest Rates, Monetary Policy, Foreign Exchange Reserves, Currency Systems & Global Monetary Runtime 5.0.**

:::中文日韩