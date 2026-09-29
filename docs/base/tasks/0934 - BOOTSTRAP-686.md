Tiếp tục với **BOOTSTRAP-686** — xây lớp thương mại trực tiếp nối `AXAGRI → AXMANUFACTURING → AXTRANSPORT` với `AXECON`, nhưng giữ tách biệt rõ giữa **hàng hóa, thị trường, giao dịch, thanh toán, quyền sở hữu và pháp lý**.

:::writing{variant="document" id="74126" title="BOOTSTRAP-686 — Native AI Civilization-Scale Retail, Commerce, Distribution, Marketplaces, Consumer Systems, Supply-Demand Networks & Global Commerce Runtime 5.0"}
# BOOTSTRAP-686
## Native AI Civilization-Scale Retail, Commerce, Distribution, Marketplaces, Consumer Systems, Supply-Demand Networks & Global Commerce Runtime 5.0

**Layer:** Commerce / Retail / Wholesale / Marketplace / Distribution / Consumer / Supply-Demand / Global Commerce  
**Target:** Axiom 5.0  
**Status:** Architecture Specification

---

# 1. Mục tiêu

`AXCOMMERCE` là native runtime của Axiom cho toàn bộ lớp:

- thương mại;
- bán lẻ;
- bán buôn;
- marketplace;
- cửa hàng;
- catalog;
- sản phẩm;
- SKU;
- inventory;
- pricing;
- quotation;
- cart;
- order;
- checkout;
- fulfillment;
- delivery reference;
- returns;
- refunds;
- customer;
- merchant;
- supplier;
- distributor;
- promotion;
- subscription;
- marketplace settlement reference;
- demand;
- supply;
- commerce analytics;
- recommendation;
- commerce AI;
- global commerce simulation.

Mục tiêu là cho phép Axiom xây dựng:

```text
Store
Marketplace
E-commerce
POS
Wholesale Platform
B2B Commerce
B2C Commerce
C2C Marketplace
Subscription Commerce
Global Commerce Network
```

mà không cần một commerce runtime bên thứ ba.

---

# 2. Vị trí trong Civilization Stack

```text
AXAGRI
     ↓
AXMANUFACTURING
     ↓
AXTRANSPORT
     ↓
AXCOMMERCE
     ↓
AXECON
```

Trong đó:

```text
AXCOMMERCE
=
physical/digital commercial operations
```

còn:

```text
AXECON
=
economic/financial authoritative semantics
```

---

# 3. Fundamental Commerce Model

Commerce được mô hình hóa:

```text
Supply
   ↓
Catalog
   ↓
Offer
   ↓
Discovery
   ↓
Cart
   ↓
Order
   ↓
Fulfillment
   ↓
Delivery
   ↓
Return / Support
```

Tài chính:

```text
Order
 ↓
Pricing
 ↓
TaxReference
 ↓
PaymentReference
 ↓
SettlementReference
```

Financial authority thuộc `AXECON`.

---

# 4. Core Architectural Principle

Không được đồng nhất:

```text
Product
≠ SKU
≠ Inventory
≠ Offer
≠ Order
≠ Payment
≠ Ownership
≠ Delivery
≠ Revenue
```

Đây là invariant nền tảng của AXCOMMERCE.

---

# 5. Commerce Entity Hierarchy

```text
CommerceSystem
├── Merchant
├── Supplier
├── Distributor
├── Store
├── Marketplace
├── Catalog
├── Product
├── Variant
├── SKU
├── Offer
├── Inventory
├── Customer
├── Cart
├── Order
├── Fulfillment
├── ShipmentReference
└── Return
```

---

# 6. CommerceSystem

```text
CommerceSystem {
    system_id
    merchants[]
    catalogs[]
    marketplaces[]
    stores[]
    policies[]
}
```

---

# 7. Merchant

```text
Merchant {
    merchant_id
    profile
    catalogs[]
    offers[]
    fulfillment_policy
}
```

Merchant identity/legal authority có thể link AXGOV/AXLAW.

---

# 8. Supplier

```text
Supplier {
    supplier_id
    capabilities
    products[]
    fulfillment
}
```

Supplier ≠ manufacturer.

---

# 9. Distributor

```text
Distributor {
    distributor_id
    regions[]
    inventory_nodes[]
}
```

---

# 10. Store

Store có thể là:

```text
PhysicalStore
OnlineStore
HybridStore
PopUpStore
AutomatedStore
```

---

# 11. Marketplace

```text
Marketplace {
    marketplace_id
    sellers[]
    catalog
    discovery
    order_routing
    policy_reference
}
```

Marketplace không mặc định sở hữu hàng hóa của seller.

---

# 12. Product

Product là conceptual commercial product:

```text
Product {
    product_id
    identity
    description
    category
    attributes
}
```

---

# 13. Product Variant

```text
ProductVariant {
    product
    variant_attributes
}
```

Ví dụ:

```text
Model
Size
Color
Configuration
Region
```

---

# 14. SKU

```text
SKU {
    sku_id
    product_variant
    inventory_unit
    barcode_reference
}
```

SKU là operational identifier.

---

# 15. Serial Unit

Một số sản phẩm yêu cầu:

```text
SerialUnit {
    sku
    serial
    provenance
}
```

---

# 16. Batch

Food/agricultural/industrial goods có thể sử dụng:

```text
Batch
Lot
Serial
```

AXCOMMERCE chỉ tham chiếu lineage authoritative từ upstream domains.

---

# 17. Catalog

```text
Catalog {
    catalog_id
    products[]
    categories[]
    attributes[]
    version
}
```

---

# 18. Catalog Version

Catalog phải versioned:

```text
Draft
Published
Deprecated
Archived
```

---

# 19. Category

```text
Category {
    category_id
    parent
    children[]
}
```

Không ép một sản phẩm chỉ có một category nếu marketplace cần taxonomy đa chiều.

---

# 20. Attribute

```text
ProductAttribute {
    name
    type
    value
    unit
}
```

Units phải dùng dimension-safe model của Axiom.

---

# 21. Product Specification

```text
ProductSpec {
    version
    attributes
    constraints
    compatibility
}
```

---

# 22. Offer

Offer là lời chào bán cụ thể:

```text
Offer {
    offer_id
    seller
    sku
    quantity
    price_reference
    availability
    terms
}
```

---

# 23. Offer ≠ Product

Một product có thể có:

```text
OfferA
OfferB
OfferC
```

từ nhiều seller.

---

# 24. Price

Commerce có thể lưu:

```text
PriceReference
PriceRule
PriceSnapshot
```

Financial semantics authoritative thuộc AXECON.

---

# 25. Dynamic Pricing

Có thể hỗ trợ:

```text
DynamicPriceRule {
    inputs
    constraints
    objective
    validity
}
```

Objective phải explicit.

---

# 26. Price Snapshot

Order phải có snapshot hoặc immutable reference:

```text
OrderLine
→ PriceSnapshot
```

Không được tự thay đổi historical order khi catalog/price thay đổi.

---

# 27. Promotion

```text
Promotion {
    promotion_id
    conditions
    benefit
    validity
}
```

---

# 28. Coupon

```text
Coupon {
    code
    rule
    usage_limit
    validity
}
```

---

# 29. Loyalty

```text
LoyaltyProgram
LoyaltyAccount
LoyaltyPoint
Reward
Tier
```

Điểm thưởng ≠ tiền pháp định.

---

# 30. Subscription

```text
Subscription {
    plan
    customer
    cycle
    status
    renewal
}
```

Billing/payment thuộc AXECON/payment boundary.

---

# 31. Customer

```text
Customer {
    customer_id
    profile_reference
    addresses[]
    preferences_reference
}
```

Sensitive personal data phải nằm trong identity/privacy systems.

---

# 32. Customer Identity Boundary

AXCOMMERCE không tự trở thành authoritative identity provider.

Có thể reference:

```text
CustomerIdentityRef
AccountRef
ConsentRef
```

---

# 33. Cart

```text
Cart {
    customer
    items[]
    pricing_snapshot
    reservation_reference
}
```

Cart không phải Order.

---

# 34. Cart State

```text
Active
Abandoned
CheckedOut
Expired
Cancelled
```

---

# 35. Inventory

```text
Inventory {
    sku
    location
    available
    reserved
    damaged
    quarantined
}
```

---

# 36. Inventory Equation

```text
Opening
+ Received
+ ProducedReference
- Sold
- Shipped
- Lost
- Damaged
- Returned
=
Closing
```

Sai số phải được explicit.

---

# 37. Inventory State

```text
Available
Reserved
Allocated
Picked
Packed
Shipped
Returned
Damaged
Quarantined
Disposed
```

---

# 38. Inventory Reservation

Reservation:

```text
Inventory
→ Reserved
```

không đồng nghĩa với:

```text
OwnershipTransfer
```

---

# 39. Overselling

Invariant:

```text
Available + Reserved
≤
UsableStock + ExplicitBackorder
```

Không được silent oversell.

---

# 40. Backorder

```text
Backorder {
    sku
    requested_quantity
    expected_supply
    priority_policy
}
```

Priority policy phải explicit.

---

# 41. Order

```text
Order {
    order_id
    customer
    lines[]
    price_snapshot
    fulfillment
    status
}
```

---

# 42. Order Lifecycle

```text
Draft
→ Submitted
→ Confirmed
→ Allocated
→ Fulfillment
→ Shipped
→ Delivered
→ Completed
```

Alternative:

```text
Cancelled
Failed
Returned
PartiallyReturned
```

---

# 43. Order Line

```text
OrderLine {
    sku
    quantity
    unit_price_snapshot
    discount_snapshot
    tax_reference
}
```

---

# 44. Order Immutability

Sau confirmation:

```text
historical_order
```

không được silently mutate.

Corrections phải là explicit events.

---

# 45. Checkout

```text
Cart
→ Validate
→ Price
→ Reserve
→ PaymentReference
→ Order
```

Payment execution thuộc payment/financial subsystem.

---

# 46. Payment Boundary

AXCOMMERCE có:

```text
PaymentIntentRef
PaymentStatusRef
PaymentTransactionRef
```

AXECON/payment system giữ authoritative financial state.

---

# 47. Ownership Boundary

Order:

```text
OrderConfirmed
```

không nhất thiết có nghĩa:

```text
LegalOwnershipTransferred
```

Ownership rule phải explicit.

---

# 48. Tax Boundary

Commerce có:

```text
TaxCalculationReference
TaxRuleReference
TaxSnapshot
```

Legal tax authority thuộc AXLAW/AXGOV/AXECON tùy architecture.

---

# 49. Fulfillment

```text
Fulfillment {
    order
    warehouse
    lines[]
    picking
    packing
    shipment_reference
}
```

---

# 50. Fulfillment Lifecycle

```text
Pending
→ Allocated
→ Picking
→ Packed
→ HandedToCarrier
→ Shipped
→ Delivered
```

---

# 51. Warehouse Boundary

Warehouse execution có thể link:

```text
AXTRANSPORT
AXMANUFACTURING
AXCONSTRUCTION
AXAGRI
```

AXCOMMERCE owns commerce-facing inventory state.

---

# 52. Shipment Boundary

Physical shipment authoritative:

```text
AXTRANSPORT
```

Commerce giữ:

```text
ShipmentRef
TrackingRef
DeliveryStatusRef
```

---

# 53. Delivery

```text
Delivery {
    order
    shipment
    destination
    status
    proof_reference
}
```

---

# 54. Proof of Delivery

```text
ProofOfDelivery {
    timestamp
    recipient_reference
    evidence
    signature_reference
}
```

---

# 55. ETA

```text
ETAPrediction
ArrivalObservation
DeliveryConfirmation
```

phải tách biệt.

---

# 56. Return

```text
ReturnRequest {
    order
    items
    reason
    evidence
}
```

---

# 57. Return Lifecycle

```text
Requested
→ Authorized
→ InTransit
→ Received
→ Inspected
→ Accepted
→ RefundedReference
→ Closed
```

---

# 58. Refund Boundary

Commerce tạo:

```text
RefundRequest
RefundReference
```

Financial system xác nhận:

```text
RefundExecuted
```

---

# 59. Return Inspection

```text
ReturnInspection {
    condition
    quantity
    defect_reference
    disposition
}
```

---

# 60. Reverse Logistics

```text
Customer
 ↓
Return
 ↓
ReverseShipment
 ↓
Warehouse
 ↓
Inspection
 ↓
Restock / Repair / Recycle / Dispose
```

Transport semantics thuộc AXTRANSPORT.

Manufacturing repair thuộc AXMANUFACTURING.

---

# 61. Marketplace Order Routing

Một order có thể:

```text
Order
 ├── SellerA
 ├── SellerB
 └── SellerC
```

Do đó:

```text
Order
→ SubOrder[]
```

---

# 62. Seller Fulfillment

```text
Seller
→ Inventory
→ Fulfillment
→ Shipment
```

---

# 63. Marketplace Settlement

AXCOMMERCE giữ:

```text
SettlementReference
CommissionReference
PayoutReference
```

AXECON giữ authoritative accounting.

---

# 64. B2B Commerce

Core:

```text
BusinessCustomer
PurchaseAgreementRef
Quote
PurchaseOrder
SalesOrder
InvoiceReference
CreditReference
```

---

# 65. Quote

```text
Quote {
    customer
    lines[]
    price
    validity
    terms_reference
}
```

---

# 66. Quote Lifecycle

```text
Draft
→ Issued
→ Accepted
→ Rejected
→ Expired
→ ConvertedToOrder
```

---

# 67. Purchase Order

```text
PurchaseOrder {
    buyer
    seller
    lines
    terms_reference
}
```

---

# 68. Commerce Contract Boundary

Contract authoritative semantics thuộc AXLAW/AXECON.

AXCOMMERCE chỉ reference:

```text
ContractRef
TermsRef
ObligationRef
```

---

# 69. Wholesale

```text
WholesaleOrder
WholesaleOffer
BulkPriceRule
MinimumOrderQuantity
VolumeDiscount
```

---

# 70. Marketplace Discovery

Discovery pipeline:

```text
Catalog
→ Index
→ Query
→ Filter
→ Retrieve
→ Rank
→ Display
```

---

# 71. Search

Hỗ trợ:

```text
Keyword
Category
Attribute
SemanticReference
VectorReference
Availability
PriceRange
LocationReference
```

Search engine implementation có thể link AX641.

---

# 72. Recommendation Boundary

AX651 sở hữu generic personalization/recommendation.

AXCOMMERCE cung cấp commerce context:

```text
Product
Offer
Availability
Price
Context
```

---

# 73. Recommendation Output

```text
Recommendation {
    item
    reason_reference
    model
    score
    uncertainty
}
```

Score chỉ có ý nghĩa trong model/context tương ứng.

---

# 74. No Hidden Manipulation

Commerce AI không được mặc định tối ưu:

```text
addiction
compulsion
deceptive_conversion
```

Mục tiêu phải explicit.

---

# 75. Advertising Boundary

Có thể reference:

```text
AdvertisementRef
CampaignRef
PlacementRef
```

Advertising system có thể nằm domain riêng.

---

# 76. Merchandising

```text
MerchandisingPlan
ProductPlacement
Collection
FeaturedItem
PromotionPlacement
```

---

# 77. Demand

```text
DemandObservation
DemandForecast
DemandScenario
```

---

# 78. Demand Forecast

```text
DemandForecast {
    product
    region
    horizon
    quantity
    uncertainty
    model
}
```

Forecast ≠ actual demand.

---

# 79. Supply

```text
SupplyObservation
SupplyForecast
SupplyScenario
```

---

# 80. Supply-Demand Graph

```text
Supplier
→ Production
→ Inventory
→ Distribution
→ Marketplace
→ CustomerDemand
```

---

# 81. Supply Gap

```text
Demand
-
AvailableSupply
=
SupplyGap
```

Phải ghi rõ time window.

---

# 82. Inventory Allocation

```text
Inventory
→ AllocationPlan
→ CustomerOrders
```

Objective có thể là:

```text
minimize lateness
maximize fill rate
minimize transport cost reference
preserve safety stock
```

Không có hidden objective.

---

# 83. Safety Stock

```text
SafetyStockPolicy {
    target
    horizon
    uncertainty
}
```

---

# 84. Replenishment

```text
Inventory
→ DemandForecast
→ ReorderDecision
→ PurchaseOrderReference
```

---

# 85. Reorder Point

Có thể model:

```text
ReorderPoint
LeadTime
DemandDistribution
SafetyStock
```

---

# 86. Supply Chain Event

```text
Purchase
Receipt
Production
Transfer
Allocation
Sale
Shipment
Delivery
Return
Loss
```

---

# 87. Supply Chain Traceability

```text
Supplier
→ Batch
→ Warehouse
→ Order
→ Shipment
→ Customer
```

---

# 88. Product Recall

Recall pipeline:

```text
RecallSignal
→ AffectedBatchDetection
→ InventoryFreeze
→ ShipmentBlock
→ CustomerNotificationReference
→ Return
→ Disposition
```

---

# 89. Inventory Freeze

```text
Available
→ Frozen
```

Frozen inventory không được allocate mới nếu policy không cho phép.

---

# 90. Product Compatibility

```text
CompatibilityRule {
    product_a
    product_b
    relation
    conditions
}
```

Relations:

```text
Compatible
Incompatible
Requires
Optional
Replacement
```

---

# 91. Bundles

```text
Bundle {
    components[]
    pricing_rule
    inventory_policy
}
```

---

# 92. Kit

```text
Kit {
    components[]
    assembly_reference
}
```

Physical assembly có thể chuyển AXMANUFACTURING.

---

# 93. Digital Goods

Commerce hỗ trợ:

```text
DigitalProduct
LicenseReference
DownloadReference
AccessEntitlement
```

Software execution/license semantics có thể link AX623/AX675.

---

# 94. Entitlement

```text
Entitlement {
    product
    customer
    scope
    validity
}
```

---

# 95. Service Commerce

Không phải mọi commerce item là physical goods:

```text
ServiceOffer
AppointmentReference
ServiceOrder
ServiceCompletion
```

---

# 96. Service Completion

```text
ServiceOrder
→ Scheduled
→ Started
→ Completed
→ Accepted
```

---

# 97. Reservation

Commerce có thể dùng:

```text
Reservation
AvailabilityWindow
Capacity
Hold
```

nhưng reservation ≠ guaranteed service execution.

---

# 98. Subscription Commerce

```text
Subscription
→ Renewal
→ Fulfillment
→ Pause
→ Resume
→ Cancel
```

---

# 99. Commerce Event Model

```text
ProductPublished
OfferCreated
PriceChanged
InventoryReceived
InventoryReserved
OrderSubmitted
OrderConfirmed
FulfillmentStarted
ShipmentReferenceCreated
DeliveryConfirmed
ReturnRequested
RefundReferenceCreated
```

---

# 100. Event Sourcing

Critical commerce state có thể reconstruct từ:

```text
Snapshot
+
EventLog
```

---

# 101. Event Idempotency

Mỗi mutation quan trọng nên có:

```text
command_id
event_id
causation_id
correlation_id
```

Duplicate commands phải idempotent hoặc explicit reject.

---

# 102. Commerce Time

Phân biệt:

```text
event_time
order_time
effective_time
settlement_time
delivery_time
expiry_time
forecast_time
```

---

# 103. Global Commerce

Global commerce graph:

```text
Supplier
→ Manufacturer
→ Distributor
→ Warehouse
→ Marketplace
→ Customer
```

có thể xuyên quốc gia.

---

# 104. Border Reference

AXCOMMERCE có:

```text
CustomsReference
ImportReference
ExportReference
BorderClearanceReference
```

Authoritative customs/legal state thuộc AXLAW/AXGOV.

---

# 105. Currency

Commerce dùng:

```text
Money<Currency>
```

dimension/type safety.

Ví dụ:

```text
100.USD
100000.VND
```

không được cộng trực tiếp nếu currency khác nhau mà không có conversion context.

---

# 106. Exchange Rate

```text
ExchangeRateSnapshot {
    base
    quote
    rate
    timestamp
    source
}
```

Không silent dùng rate hiện tại để rewrite historical transaction.

---

# 107. Financial Boundary

AXCOMMERCE:

```text
PriceSnapshot
PaymentRef
RefundRef
SettlementRef
```

AXECON:

```text
Ledger
Asset
Liability
Revenue
Expense
Payment
Settlement
Tax
```

---

# 108. Fraud Signals

Có thể tạo:

```text
FraudCandidate
Anomaly
RiskSignal
```

Không tự biến anomaly thành confirmed fraud.

---

# 109. Fraud Decision

Authoritative enforcement phải:

```text
policy
evidence
decision
authority
audit
```

---

# 110. Account Abuse

Có thể model:

```text
AbuseSignal
RateLimitEvent
AccountRestrictionReference
```

Restriction phải có policy và audit.

---

# 111. Commerce Privacy

Potentially sensitive:

```text
purchase_history
location
preferences
search_history
payment_reference
behavioral_profile
```

Không được mặc định infer sensitive attributes.

---

# 112. Data Minimization

Customer personalization nên dùng:

```text
purpose
scope
retention
consent/reference
```

---

# 113. Consent

```text
ConsentReference {
    purpose
    scope
    granted_at
    revoked_at
}
```

---

# 114. AI Customer Profile

AI profile phải phân biệt:

```text
ExplicitPreference
ObservedBehavior
InferredPreference
```

Không được coi inferred preference là explicit fact.

---

# 115. Commerce AI

Workloads:

```text
DemandForecast
InventoryForecast
Replenishment
PricingAnalysis
Search
Recommendation
FraudDetection
ReturnPrediction
WarehouseOptimization
AssortmentOptimization
SupplyRiskPrediction
DeliveryPrediction
CustomerSupport
```

---

# 116. AI Provenance

Mọi AI output quan trọng:

```text
model_id
model_version
input_snapshot
feature_version
timestamp
uncertainty
policy
```

---

# 117. Pricing AI

Pricing optimizer phải nhận:

```text
objective
constraints
validity
authority
```

Không tự override contractual/legal price constraints.

---

# 118. Multi-Objective Commerce Optimization

Ví dụ:

```text
maximize_fill_rate
minimize_stockout
minimize_waste
minimize_delivery_delay
minimize_cost_reference
```

Trả:

```text
ParetoCommercePlanSet
```

nếu nhiều objective.

---

# 119. No Hidden Objective

Không cho optimizer tự thêm:

```text
maximize_customer_spend
```

nếu application không khai báo objective đó.

---

# 120. Commerce Simulation

```text
CommerceSimulation
MarketSimulationReference
DemandSimulation
InventorySimulation
MarketplaceSimulation
SupplyChainSimulation
```

---

# 121. Marketplace Simulation

Mô phỏng:

```text
buyers
sellers
offers
inventory
demand
prices
orders
```

Simulation state không được mutate live marketplace.

---

# 122. Consumer Simulation

Có thể model aggregate:

```text
ConsumerSegment
DemandModel
PreferenceModel
PurchaseProbability
```

Không tự suy luận individual sensitive profile.

---

# 123. Supply Shock Simulation

```text
FactoryShutdown
CropFailure
PortDisruption
TransportDisruption
EnergyShortage
DemandSpike
```

Các event chỉ là scenario khi chạy simulation.

---

# 124. Commerce Digital Twin

```text
CommerceTwin {
    catalog
    offers
    inventory
    orders
    fulfillment
    supply
    demand
}
```

---

# 125. Twin Pipeline

```text
LiveEvents
→ Observations
→ TwinState
→ Simulation
→ Forecast
→ Recommendation
→ AuthorizedAction
```

---

# 126. Twin State Classes

```text
Observed
Estimated
Predicted
Simulated
Planned
```

---

# 127. Edge Commerce

Có thể chạy:

```text
POS
StoreEdge
WarehouseEdge
OfflineCommerceNode
```

---

# 128. Offline POS

Offline mode cần:

```text
local_catalog
local_price_snapshot
inventory_cache
transaction_queue
reconciliation
```

Không giả định network luôn có.

---

# 129. Offline Conflict

Khi reconnect:

```text
LocalOrder
→ Validate
→ Reconcile
→ Conflict
→ Resolve
```

Conflict không được silent overwrite.

---

# 130. Distributed Inventory

Inventory có thể được giữ tại:

```text
Store
Warehouse
RegionalHub
Marketplace
```

Distributed reservation cần consistency policy rõ:

```text
Strong
Eventual
LeaseBased
Custom
```

---

# 131. Reservation Lease

```text
ReservationLease {
    inventory
    quantity
    expiry
}
```

Expired lease tự release theo policy.

---

# 132. Commerce Consistency

Không ép mọi operation thành global transaction.

Mỗi workflow khai báo:

```text
consistency
durability
idempotency
compensation
```

---

# 133. Saga

Order workflow có thể:

```text
ReserveInventory
→ PaymentReference
→ Fulfillment
→ Shipment
```

Nếu bước sau fail:

```text
Compensate
```

Không giả định physical rollback.

---

# 134. Compensation

Ví dụ:

```text
OrderCancelled
→ ReleaseReservation
→ CancelFulfillment
→ RefundReference
```

---

# 135. Physical Irreversibility

Sau:

```text
ShipmentDispatched
```

không được giả định:

```text
RollbackShipment
```

mà phải tạo reverse workflow.

---

# 136. Commerce Security

Capabilities:

```text
commerce.read
catalog.write
offer.write
price.write
inventory.read
inventory.write
order.create
order.modify
fulfillment.execute
return.process
refund.request
marketplace.admin
customer.read
customer.profile
recommendation.run
pricing.optimize
simulation.run
```

---

# 137. High-Risk Operations

Audit bắt buộc:

```text
PriceOverride
InventoryAdjustment
OrderCancellation
RefundApproval
SellerSuspensionReference
PromotionActivation
BulkInventoryMutation
```

---

# 138. Inventory Adjustment

Không:

```text
inventory = 500
```

mà:

```text
InventoryAdjustment {
    previous
    delta
    reason
    authority
    evidence
}
```

---

# 139. Audit Trail

```text
Actor
Action
Target
Before
After
Reason
Authority
Timestamp
Correlation
```

---

# 140. Commerce Observability

Metrics:

```text
order_rate
conversion_rate_reference
fill_rate
stockout_rate
return_rate
delivery_delay_reference
inventory_turnover
cart_abandonment
```

Metric ≠ universal business judgment.

---

# 141. Performance

Large commerce systems cần:

```text
compact IDs
columnar analytics
SoA order lines
batch event processing
incremental inventory projections
memory-mapped catalogs
cache-aware indexes
parallel demand simulation
GPU recommendation/inference
```

---

# 142. Search Index

Product catalogs có thể sử dụng:

```text
inverted_index
attribute_index
vector_index_reference
geo_index
availability_index
price_index
```

AX641 là authoritative search/query engine layer.

---

# 143. Catalog Compilation

Catalog có thể compile thành:

```text
CatalogIndexArtifact
```

để startup nhanh.

---

# 144. Precompiled Commerce State

Axiom compiler/runtime có thể cache:

```text
catalog schema
product metadata
pricing rules
tax references
search indexes
promotion rules
```

miễn source/version chưa thay đổi.

---

# 145. WASM

Commerce WASM profile:

```text
catalog viewer
shopping UI
cart
pricing preview
order tracking
merchant dashboard
```

---

# 146. Mobile

Mobile profile:

```text
shopping
POS
inventory scan
barcode
order tracking
merchant operations
delivery confirmation
```

---

# 147. GPU

GPU workloads:

```text
recommendation
search embeddings
demand simulation
large-scale pricing simulation
inventory optimization
market simulation
```

---

# 148. Module Layout

```text
axiom.commerce.core
axiom.commerce.catalog
axiom.commerce.product
axiom.commerce.variant
axiom.commerce.sku
axiom.commerce.offer
axiom.commerce.price
axiom.commerce.promotion
axiom.commerce.loyalty

axiom.commerce.customer
axiom.commerce.cart
axiom.commerce.order
axiom.commerce.checkout

axiom.commerce.inventory
axiom.commerce.fulfillment
axiom.commerce.delivery
axiom.commerce.return

axiom.commerce.marketplace
axiom.commerce.b2b
axiom.commerce.wholesale
axiom.commerce.subscription

axiom.commerce.search
axiom.commerce.discovery
axiom.commerce.recommendation

axiom.commerce.supply
axiom.commerce.demand
axiom.commerce.planning
axiom.commerce.optimization

axiom.commerce.simulation
axiom.commerce.twin
axiom.commerce.ai

axiom.commerce.security
axiom.commerce.distributed
axiom.commerce.realtime
axiom.commerce.gpu
axiom.commerce.wasm
axiom.commerce.mobile
```

---

# 149. Profiles

```text
AXCOMMERCE_NONE
AXCOMMERCE_CORE
AXCOMMERCE_CATALOG
AXCOMMERCE_PRODUCT
AXCOMMERCE_OFFER
AXCOMMERCE_PRICE
AXCOMMERCE_PROMOTION
AXCOMMERCE_CUSTOMER
AXCOMMERCE_CART
AXCOMMERCE_ORDER
AXCOMMERCE_CHECKOUT
AXCOMMERCE_INVENTORY
AXCOMMERCE_FULFILLMENT
AXCOMMERCE_DELIVERY
AXCOMMERCE_RETURN
AXCOMMERCE_MARKETPLACE
AXCOMMERCE_B2B
AXCOMMERCE_WHOLESALE
AXCOMMERCE_SUBSCRIPTION
AXCOMMERCE_SEARCH
AXCOMMERCE_DISCOVERY
AXCOMMERCE_RECOMMENDATION
AXCOMMERCE_SUPPLY
AXCOMMERCE_DEMAND
AXCOMMERCE_OPTIMIZATION
AXCOMMERCE_SIMULATION
AXCOMMERCE_TWIN
AXCOMMERCE_AI
AXCOMMERCE_SECURITY
AXCOMMERCE_DISTRIBUTED
AXCOMMERCE_REALTIME
AXCOMMERCE_GPU
AXCOMMERCE_WASM
AXCOMMERCE_MOBILE
AXCOMMERCE_GLOBAL
AXCOMMERCE_FULL
```

---

# 150. Annotations

```text
@commerce
@merchant
@supplier
@distributor
@store
@marketplace

@catalog
@product
@variant
@sku
@offer
@price
@promotion
@coupon
@loyalty

@customer
@cart
@checkout
@order
@order_line

@inventory
@reservation
@backorder
@fulfillment
@delivery
@return
@refund

@wholesale
@b2b
@subscription

@search
@discovery
@recommendation

@supply
@demand
@replenishment
@forecast

@commerce_simulation
@commerce_twin
@commerce_ai
@commerce_optimization
```

---

# 151. File Extensions

```text
.axcommerce
.axmerchant
.axsupplier
.axstore
.axmarketplace

.axcatalog
.axproduct
.axvariant
.axsku
.axoffer
.axprice
.axpromotion
.axcoupon
.axloyalty

.axcustomer
.axcart
.axcheckout
.axorder
.axinventory
.axreservation
.axfulfillment
.axdelivery
.axreturn
.axrefund

.axb2b
.axwholesale
.axsubscription

.axsearch
.axdiscovery
.axrecommendation

.axsupply
.axdemand
.axreplenish
.axcommerceplan

.axcommercesim
.axcommercetwin
.axcommerceai
.axcommerceopt
```

---

# 152. CLI

```bash
axiom commerce create
axiom commerce inspect

axiom catalog create
axiom catalog publish
axiom catalog index

axiom product create
axiom product variant
axiom product inspect

axiom offer create
axiom offer publish
axiom offer expire

axiom price set
axiom price rule
axiom price simulate

axiom promotion create
axiom coupon create
axiom loyalty create

axiom customer create
axiom cart create
axiom cart add
axiom cart checkout

axiom order create
axiom order inspect
axiom order cancel

axiom inventory inspect
axiom inventory reserve
axiom inventory release
axiom inventory adjust

axiom fulfillment allocate
axiom fulfillment pick
axiom fulfillment pack

axiom delivery track
axiom delivery confirm

axiom return request
axiom return inspect
axiom return close

axiom marketplace create
axiom marketplace seller
axiom marketplace route

axiom supply forecast
axiom demand forecast
axiom replenish plan

axiom commerce search
axiom commerce recommend

axiom commerce simulate
axiom commerce twin

axiom commerce-ai forecast
axiom commerce-ai optimize
axiom commerce-ai detect
```

---

# 153. Core IR

Catalog:

```text
CommerceSystemCreate
CatalogCreate
CatalogPublish
ProductCreate
VariantCreate
SKUCreate
OfferCreate
OfferPublish
PriceSet
PromotionCreate
CouponCreate
```

Customer:

```text
CustomerCreate
ConsentAttach
PreferenceAttach
```

Cart/order:

```text
CartCreate
CartItemAdd
CartItemRemove
CheckoutValidate
OrderCreate
OrderConfirm
OrderCancel
```

Inventory:

```text
InventoryCreate
InventoryReceive
InventoryReserve
InventoryRelease
InventoryAllocate
InventoryAdjust
InventoryFreeze
InventoryUnfreeze
```

Fulfillment:

```text
FulfillmentCreate
PickStart
PickComplete
PackStart
PackComplete
ShipmentReferenceCreate
DeliveryConfirm
```

Return:

```text
ReturnRequestCreate
ReturnAuthorize
ReturnReceive
ReturnInspect
RefundRequest
ReturnClose
```

Marketplace:

```text
MarketplaceCreate
SellerCreate
SellerOfferCreate
SubOrderCreate
SettlementReferenceCreate
```

Supply/demand:

```text
DemandObserve
DemandForecast
SupplyObserve
SupplyForecast
ReplenishmentCreate
InventoryAllocate
```

AI:

```text
DemandPredict
PriceAnalyze
RecommendationGenerate
FraudSignalDetect
InventoryOptimize
CommerceOptimize
AIRecommendation
ActuationAuthorize
```

Simulation:

```text
CommerceSimCreate
CommerceSimStep
CommerceSimRun
ScenarioCreate
TwinCreate
TwinSync
```

---

# 154. State Machines

## Order

```text
Draft
→ Submitted
→ Confirmed
→ Allocated
→ Fulfillment
→ Shipped
→ Delivered
→ Completed
```

## Inventory

```text
Available
→ Reserved
→ Allocated
→ Picked
→ Packed
→ Shipped
```

## Return

```text
Requested
→ Authorized
→ Received
→ Inspected
→ Accepted
→ Closed
```

## Offer

```text
Draft
→ Published
→ Suspended
→ Expired
```

---

# 155. Critical Invariants

Tối thiểu:

```text
C-001 Product ≠ SKU
C-002 SKU ≠ Inventory
C-003 Offer ≠ Product
C-004 Cart ≠ Order
C-005 Order ≠ Payment
C-006 Order ≠ Ownership
C-007 Delivery ≠ Payment
C-008 Inventory cannot silently go negative
C-009 Reservation cannot exceed available capacity
C-010 Reservation expiry releases inventory
C-011 Historical price snapshot immutable
C-012 Confirmed order cannot silently mutate
C-013 Corrections use explicit events
C-014 Fulfillment references valid order
C-015 Shipment movement belongs AXTRANSPORT
C-016 Payment authority belongs AXECON/payment
C-017 Legal ownership belongs legal/economic layer
C-018 Tax authority remains external
C-019 Return references valid order line
C-020 Refund cannot silently fabricate financial settlement
C-021 Marketplace seller remains identifiable
C-022 Marketplace ownership is not implied
C-023 Split orders preserve parent order lineage
C-024 Product batch lineage preserved
C-025 Recall cannot delete historical transactions
C-026 Forecast ≠ observation
C-027 ETA ≠ confirmed arrival
C-028 Demand prediction ≠ actual demand
C-029 Fraud signal ≠ confirmed fraud
C-030 AI recommendation ≠ execution
C-031 Pricing optimizer cannot bypass explicit constraints
C-032 Inventory optimizer has explicit objective
C-033 No hidden objective
C-034 Simulation ≠ live commerce
C-035 Twin state distinguishes observed/estimated/predicted/simulated
C-036 Simulation cannot mutate live orders
C-037 Duplicate mutation commands idempotent/rejected
C-038 Physical shipment cannot be assumed rollbackable
C-039 Currency types must be compatible
C-040 Historical FX snapshot immutable
C-041 Consent scope explicit
C-042 Inferred preference ≠ explicit preference
C-043 Sensitive profile inference restricted
C-044 Offline conflicts visible
C-045 Distributed inventory consistency explicit
C-046 Reservation lease has expiry
C-047 Inventory adjustment has reason/audit
C-048 Bulk mutation audited
C-049 AI model/version/provenance retained
C-050 Recommendation score scoped to model/context
C-051 Marketplace ranking does not imply universal seller/product quality
C-052 Search result ≠ recommendation
C-053 Recommendation ≠ advertisement
C-054 Advertisement ≠ product fact
C-055 Product specification versioned
C-056 Catalog publication versioned
C-057 Offer validity explicit
C-058 Promotion validity explicit
C-059 Return inspection ≠ automatic refund
C-060 Delivery evidence explicit when required
C-061 Supply gap includes time window
C-062 Demand forecast includes horizon
C-063 Backorder explicitly represented
C-064 No silent overselling
C-065 Financial ledger remains outside commerce operational state
C-066 Legal/regulatory authority remains outside commerce runtime
C-067 Physical goods movement remains AXTRANSPORT
C-068 Agricultural provenance remains AXAGRI
C-069 Manufacturing provenance remains AXMANUFACTURING
C-070 No human-worth ranking from purchasing behavior
```

---

# 156. Test Architecture

Target:

```text
≥ 10,000 automated tests
≥ 820 architecture invariants
```

Test groups:

```text
catalog
product
SKU
offer
pricing
promotion
customer
cart
checkout
order
inventory
fulfillment
delivery
returns
marketplace
B2B
subscription
search
recommendation
supply
demand
distributed
offline
security
privacy
AI
simulation
cross-domain
performance
```

---

# 157. Cross-Domain Integration

```text
AXAGRI
 └── agricultural products / food batches

AXMANUFACTURING
 └── manufactured products / production references

AXTRANSPORT
 └── shipment / delivery / physical movement

AXCONSTRUCTION
 └── construction material commerce references

AXRESOURCE
 └── resource quantity / energy / water

AXECON
 └── money / market / accounting / settlement

AXLAW
 └── contract / consumer law / ownership / regulation

AXGOV
 └── permits / public commerce regulation

AX641
 └── search / query

AX651
 └── generic personalization

AX644
 └── agents

AX650
 └── long-term AI memory
```

---

# 158. Physical Civilization Commerce Chain

Sau BOOTSTRAP-686:

```text
RESOURCE
   ↓
AGRICULTURE
   ↓
MANUFACTURING
   ↓
CONSTRUCTION
   ↓
TRANSPORT
   ↓
COMMERCE
   ↓
CONSUMPTION
```

và reverse flow:

```text
CONSUMPTION
   ↓
RETURNS
   ↓
RECYCLING
   ↓
RESOURCE
```

---

# 159. Commerce Civilization Graph

```text
                  ┌──────────────┐
                  │  PRODUCTION  │
                  └──────┬───────┘
                         ↓
                  ┌──────────────┐
                  │   INVENTORY  │
                  └──────┬───────┘
                         ↓
                  ┌──────────────┐
                  │   COMMERCE   │
                  └──────┬───────┘
                         ↓
                  ┌──────────────┐
                  │  CONSUMER    │
                  └──────┬───────┘
                         ↓
                  ┌──────────────┐
                  │ RETURN/WASTE │
                  └──────┬───────┘
                         ↓
                  ┌──────────────┐
                  │  RECOVERY    │
                  └──────────────┘
```

---

# 160. Final Architecture Contract

`AXCOMMERCE` phải cung cấp native substrate cho:

```text
Retail
Wholesale
Marketplace
Catalog
Product
SKU
Offer
Pricing
Promotion
Customer
Cart
Checkout
Order
Inventory
Fulfillment
Delivery
Returns
Subscription
B2B
Demand
Supply
Replenishment
Commerce Search
Commerce Discovery
Commerce Recommendation
Commerce AI
Commerce Simulation
Commerce Digital Twin
```

và giữ nguyên:

```text
Product
    ≠
Offer
    ≠
Inventory
    ≠
Order
    ≠
Payment
    ≠
Ownership
    ≠
LegalAuthority
```

Đây là boundary quan trọng để Axiom không biến một commerce runtime thành một hệ thống tài chính/pháp lý không kiểm soát được.

---

# 161. Physical + Economic Civilization Stack

Đến đây architecture chain có dạng:

```text
                CIVILIZATION
                     │
        ┌────────────┴────────────┐
        │                         │
     SOCIETY                  ECONOMY
        │                         │
        │                     AXECON
        │                         │
        └──────────┬──────────────┘
                   │
               COMMERCE
              AXCOMMERCE
                   │
               TRANSPORT
              AXTRANSPORT
                   │
             MANUFACTURING
            AXMANUFACTURING
                   │
              AGRICULTURE
                AXAGRI
                   │
               RESOURCES
               AXRESOURCE
```

Đây là nền tảng để các task sau có thể xây tiếp các domain **dịch vụ, tài chính, việc làm, nhà ở, tiêu dùng và hệ thống kinh tế-xã hội** mà không phá vỡ domain boundary đã thiết lập.

**Task kế tiếp: BOOTSTRAP-687 — Native AI Civilization-Scale Finance, Banking, Payments, Accounting, Capital, Insurance, Investment & Monetary Systems Runtime 5.0.**
:::