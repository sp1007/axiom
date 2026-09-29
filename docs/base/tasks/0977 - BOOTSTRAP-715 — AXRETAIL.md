# BOOTSTRAP-715 — AXRETAIL

**Namespace:** `AXRETAIL`  
**Phase:** Axiom Civilization Runtime / Commerce & Retail Infrastructure  
**Status:** ARCHITECTURAL BASELINE — FROZEN TARGET  
**Depends on:** `AXLAW`, `AXIDENTITY`, `AXCIVIL`, `AXGOV`, `AXFINANCE`, `AXTRANSPORT`, `AXFOOD`

---

# 715.0 — Mục tiêu

`AXRETAIL` là native runtime cho **commerce và retail lifecycle**, bao phủ:

```text
product catalog
product variants
merchandising
pricing
offers
customers
stores
warehouses
inventory
POS
shopping carts
orders
payments references
fulfillment
shipping
returns
refunds
exchanges
promotions
discounts
subscriptions
marketplaces
seller/buyer relationships
product reviews
warranties
customer service
commerce analytics
```

Mục tiêu:

```text
Product
   ↓
Catalog
   ↓
Offer
   ↓
Customer
   ↓
Cart
   ↓
Order
   ↓
Payment
   ↓
Fulfillment
   ↓
Shipment
   ↓
Delivery
   ↓
Return / Warranty
```

phải được biểu diễn thành **immutable commerce events + derived projections**.

---

# 715.1 — Domain Boundary

```text
                         AXRETAIL
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
    CATALOG               COMMERCE            FULFILLMENT
       │                    │                    │
 products                cart/order           inventory
 variants                pricing             warehouse
 attributes              promotion            shipment ref
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                     CUSTOMER SERVICES
                            │
                 returns / warranty / support
```

---

# 715.2 — Strong Boundaries

`AXRETAIL` **không sở hữu**:

```text
AXFINANCE
    authoritative money / ledger / settlement

AXTRANSPORT
    vehicle / route / transportation state

AXFOOD
    food production / food safety state

AXAGRICULTURE
    agricultural production state

AXIDENTITY
    canonical person / organization identity

AXCIVIL
    civil ownership / household / legal-person facts

AXGOV
    permits / administrative authority

AXLAW
    legal rules
```

`AXRETAIL` sở hữu:

```text
commerce semantics
catalog semantics
offers
orders
retail inventory semantics
fulfillment state
returns
commerce relationships
```

---

# 715.3 — Fundamental Distinctions

```text
product
    ≠
product variant

catalog item
    ≠
sellable offer

price
    ≠
payment

order
    ≠
invoice

order
    ≠
shipment

inventory quantity
    ≠
available-to-sell quantity

reservation
    ≠
sale

promotion
    ≠
discount actually applied

return request
    ≠
approved return

refund instruction
    ≠
money movement

customer identity
    ≠
commerce profile

seller
    ≠
product manufacturer

review
    ≠
verified fact

AI recommendation
    ≠
purchase decision
```

---

# 715.4 — Product

```axiom
retail_product {
    product_id
    category
    brand_reference
    title
    description
    attributes
    status
}
```

Product identity không phụ thuộc vào SKU.

---

# 715.5 — Product Variant

```axiom
product_variant {
    variant_id
    product
    attributes
    dimensions
    weight
    barcode_refs
    status
}
```

Ví dụ:

```text
shirt
 ├── size:S / color:black
 ├── size:M / color:black
 └── size:L / color:white
```

---

# 715.6 — SKU

```axiom
retail_sku {
    sku
    variant
    seller
    status
}
```

SKU là commerce identifier.

---

# 715.7 — Barcode

```axiom
retail_barcode {
    barcode
    sku
    barcode_type
    issuer_reference
    status
}
```

Một SKU có thể có nhiều barcode theo context.

---

# 715.8 — Product Category

```axiom
product_category {
    category_id
    parent
    name
    attributes_schema
    version
}
```

Category hierarchy phải hỗ trợ DAG nếu business taxonomy cần nhiều classification.

---

# 715.9 — Product Attribute

```axiom
product_attribute {
    attribute
    type
    value
    unit
    locale
}
```

Không hard-code mọi loại product attribute vào compiler.

---

# 715.10 — Catalog

```axiom
retail_catalog {
    catalog_id
    name
    products
    variants
    locale
    currency
    version
    status
}
```

---

# 715.11 — Catalog Publication

```axiom
catalog_publication {
    catalog
    channel
    version
    published_at
    status
}
```

Catalog nội bộ và catalog public là các projections khác nhau.

---

# 715.12 — Commerce Channel

```axiom
commerce_channel {
    channel_id
    type
    configuration
    status
}
```

Types:

```text
STORE
WEB
MOBILE
MARKETPLACE
POS
WHOLESALE
API
```

---

# 715.13 — Seller

```axiom
seller {
    seller_id
    identity_reference
    commerce_profile
    status
}
```

Identity canonical thuộc `AXIDENTITY`.

---

# 715.14 — Buyer / Customer

```axiom
customer {
    customer_id
    identity_reference
    profile
    preferences
    status
}
```

Không tạo một identity system riêng.

---

# 715.15 — Customer Commerce Profile

```axiom
customer_profile {
    customer
    contact_preferences
    loyalty_reference
    segmentation
    created_at
}
```

Segmentation là derived commerce data.

---

# 715.16 — Address Reference

```axiom
commerce_address {
    owner
    address_reference
    usage
    valid_from
    valid_to
}
```

Canonical address nếu thuộc hệ thống địa lý/civil khác phải được reference, không duplicate authority.

---

# 715.17 — Store

```axiom
retail_store {
    store_id
    organization
    location_reference
    capabilities
    inventory_location
    status
}
```

---

# 715.18 — Store Register

```axiom
pos_register {
    register_id
    store
    device
    configuration
    status
}
```

---

# 715.19 — POS Session

```axiom
pos_session {
    session_id
    register
    operator
    opened_at
    closed_at
    opening_state
    closing_state
}
```

---

# 715.20 — POS Transaction

```axiom
pos_transaction {
    transaction_id
    session
    items
    totals
    customer_reference
    status
}
```

---

# 715.21 — Product Offer

```axiom
product_offer {
    offer_id
    seller
    product_variant
    channel
    price_reference
    availability
    validity
    conditions
    status
}
```

Offer là thứ **được bán** trong một commerce context cụ thể.

---

# 715.22 — Price

```axiom
retail_price {
    price_id
    amount
    currency
    price_type
    validity
}
```

Authoritative monetary amount phải tuân theo `AXFINANCE`.

Không dùng floating-point cho monetary authority.

---

# 715.23 — Price Rule

```axiom
price_rule {
    rule_id
    scope
    conditions
    calculation
    priority
    validity
}
```

---

# 715.24 — Price History

Mọi thay đổi authoritative price phải versioned:

```text
PRICE_CREATED
PRICE_CHANGED
PRICE_EXPIRED
PRICE_REPLACED
```

Không overwrite lịch sử.

---

# 715.25 — Promotion

```axiom
promotion {
    promotion_id
    conditions
    benefits
    validity
    channels
    status
}
```

---

# 715.26 — Discount

```axiom
discount {
    discount_id
    promotion
    order_or_line
    calculated_amount
    calculation_reference
}
```

Promotion là rule.

Discount là **result được áp dụng**.

---

# 715.27 — Coupon

```axiom
coupon {
    coupon_id
    promotion
    code
    validity
    usage_limits
    status
}
```

---

# 715.28 — Shopping Cart

```axiom
shopping_cart {
    cart_id
    customer
    channel
    items
    created_at
    updated_at
    status
}
```

Cart không phải order.

---

# 715.29 — Cart Item

```axiom
cart_item {
    item_id
    variant
    quantity
    selected_offer
    price_snapshot
}
```

Price snapshot cần thiết để giải thích checkout.

---

# 715.30 — Checkout

```axiom
checkout {
    cart
    customer
    shipping_reference
    pricing_result
    promotion_result
    payment_reference
    status
}
```

Checkout là process.

---

# 715.31 — Order

```axiom
retail_order {
    order_id
    customer
    channel
    lines
    totals
    fulfillment_plan
    status
    created_at
}
```

---

# 715.32 — Order Line

```axiom
order_line {
    line_id
    offer
    quantity
    unit_price
    discounts
    tax_reference
    total
}
```

---

# 715.33 — Order State Machine

```text
DRAFT
 ↓
PLACED
 ↓
CONFIRMED
 ↓
ALLOCATED
 ↓
FULFILLING
 ↓
SHIPPED
 ↓
DELIVERED
```

Alternative:

```text
CANCELLED
ON_HOLD
PARTIALLY_FULFILLED
RETURNED
COMPLETED
```

Order state không được suy ra đơn giản từ shipment state.

---

# 715.34 — Payment Boundary

Order có:

```axiom
payment_reference
```

nhưng payment ledger thuộc:

```text
AXFINANCE
```

Flow:

```text
AXRETAIL
   ↓ payment intent/reference
AXFINANCE
   ↓ settlement
AXRETAIL
   ↓ payment status projection
```

---

# 715.35 — Invoice Reference

```axiom
invoice_reference {
    order
    finance_document
    status
}
```

Invoice authoritative thuộc financial/accounting subsystem.

---

# 715.36 — Tax Reference

```axiom
retail_tax_reference {
    order
    jurisdiction_reference
    tax_rule_reference
    calculated_amount
}
```

`AXRETAIL` có thể giữ calculation result/reference.

Tax law thuộc `AXLAW`.

---

# 715.37 — Inventory

```axiom
retail_inventory {
    inventory_id
    sku
    location
    quantity
    reserved
    available
    status
}
```

---

# 715.38 — Inventory States

```text
ON_HAND
RESERVED
ALLOCATED
DAMAGED
QUARANTINED
IN_TRANSIT
RETURNED
UNAVAILABLE
```

Không được cộng tất cả thành sellable inventory.

---

# 715.39 — Inventory Movement

```axiom
inventory_movement {
    movement_id
    sku
    source
    destination
    quantity
    reason
    reference
    timestamp
}
```

---

# 715.40 — Inventory Reservation

```axiom
inventory_reservation {
    reservation_id
    sku
    location
    quantity
    order
    expires_at
    status
}
```

---

# 715.41 — Available-to-Sell

```axiom
available_to_sell =
    eligible_on_hand
    - active_reservations
    - unavailable_quantity
```

Không được coi `on_hand` là `available_to_sell`.

---

# 715.42 — Warehouse

```axiom
retail_warehouse {
    warehouse_id
    organization
    location_reference
    zones
    capabilities
    status
}
```

---

# 715.43 — Warehouse Location

```axiom
warehouse_location {
    location_id
    warehouse
    zone
    bin
    capacity
    status
}
```

---

# 715.44 — Fulfillment Order

```axiom
fulfillment_order {
    fulfillment_id
    order
    lines
    source_location
    destination
    status
}
```

---

# 715.45 — Fulfillment Strategy

```axiom
fulfillment_strategy {
    order
    eligible_locations
    allocation_rules
    priority
    version
}
```

AI có thể tối ưu fulfillment nhưng execution vẫn phải obey authorization/constraints.

---

# 715.46 — Pick / Pack

```axiom
pick_operation {
    fulfillment
    items
    operator
    timestamp
}
```

```axiom
pack_operation {
    fulfillment
    package
    items
    timestamp
}
```

---

# 715.47 — Package

```axiom
retail_package {
    package_id
    fulfillment
    dimensions
    weight
    contents
    packaging
}
```

---

# 715.48 — Shipment Boundary

```text
AXRETAIL
    ↓
shipment request
    ↓
AXTRANSPORT
    ↓
vehicle / route / carrier / delivery
    ↓
delivery status
    ↓
AXRETAIL
```

---

# 715.49 — Delivery

```axiom
delivery_event {
    shipment_reference
    event_type
    timestamp
    evidence
}
```

Types:

```text
DISPATCHED
IN_TRANSIT
OUT_FOR_DELIVERY
DELIVERED
FAILED
RETURNED
```

---

# 715.50 — Return Request

```axiom
return_request {
    return_id
    order
    lines
    reason
    requested_at
    status
}
```

---

# 715.51 — Return State Machine

```text
REQUESTED
 ↓
AUTHORIZED
 ↓
IN_TRANSIT
 ↓
RECEIVED
 ↓
INSPECTED
 ↓
ACCEPTED / REJECTED
 ↓
DISPOSITION
```

---

# 715.52 — Return Inspection

```axiom
return_inspection {
    return
    item_condition
    evidence
    inspector
    result
}
```

---

# 715.53 — Return Disposition

```axiom
return_disposition {
    return
    action
    quantity
    inventory_reference
    timestamp
}
```

Actions:

```text
RESTOCK
REFURBISH
REPAIR
RECYCLE
DISPOSE
SUPPLIER_RETURN
```

---

# 715.54 — Refund

```axiom
refund_request {
    return
    amount_reference
    reason
    authorization
    status
}
```

Actual money movement:

```text
AXFINANCE
```

---

# 715.55 — Exchange

```axiom
exchange {
    original_order
    returned_lines
    replacement_lines
    price_difference_reference
    status
}
```

---

# 715.56 — Warranty

```axiom
warranty {
    product
    seller
    duration
    conditions
    version
}
```

---

# 715.57 — Warranty Claim

```axiom
warranty_claim {
    customer
    product
    purchase_reference
    defect
    evidence
    status
}
```

---

# 715.58 — Customer Support Case

```axiom
commerce_case {
    case_id
    customer
    order_reference
    category
    messages
    attachments
    status
}
```

---

# 715.59 — Review

```axiom
product_review {
    review_id
    customer_reference
    product
    rating
    content_reference
    verified_purchase
    status
}
```

Review là customer-generated content.

Không biến review thành authoritative product fact.

---

# 715.60 — Loyalty

```axiom
loyalty_account {
    customer
    program
    balance_reference
    status
}
```

Điểm có thể được model ở retail.

Nếu điểm có monetary redemption/financial value, settlement interface phải đi qua appropriate financial boundary.

---

# 715.61 — Subscription

```axiom
retail_subscription {
    customer
    offer
    schedule
    quantity
    fulfillment
    status
}
```

---

# 715.62 — Marketplace

```axiom
marketplace {
    marketplace_id
    sellers
    catalog
    orders
    settlement_reference
}
```

Marketplace payment settlement thuộc `AXFINANCE`.

---

# 715.63 — Seller Offer Graph

```text
Product
   ↓
Variant
   ↓
Seller
   ↓
Offer
   ↓
Channel
   ↓
Price
   ↓
Availability
```

Một product có thể có nhiều offers.

---

# 715.64 — Product Availability

```axiom
availability {
    offer
    location
    quantity
    available_from
    available_until
}
```

Availability không đồng nghĩa với inventory ownership.

---

# 715.65 — Order Allocation

```axiom
allocation {
    order
    line
    inventory_location
    quantity
    reservation
}
```

Allocation phải deterministic khi chạy cùng:

```text
same state
same rules
same inputs
```

---

# 715.66 — Commerce Event Model

```text
PRODUCT_CREATED
PRODUCT_UPDATED
PRODUCT_VARIANT_CREATED

SKU_CREATED
BARCODE_REGISTERED

CATALOG_CREATED
CATALOG_VERSIONED
CATALOG_PUBLISHED

OFFER_CREATED
OFFER_UPDATED
OFFER_EXPIRED

PRICE_CREATED
PRICE_CHANGED
PRICE_EXPIRED

PROMOTION_CREATED
PROMOTION_ACTIVATED
PROMOTION_EXPIRED
DISCOUNT_APPLIED

COUPON_CREATED
COUPON_REDEEMED

CUSTOMER_CREATED
CUSTOMER_PROFILE_UPDATED

STORE_CREATED
POS_REGISTER_CREATED
POS_SESSION_OPENED
POS_SESSION_CLOSED
POS_TRANSACTION_CREATED

CART_CREATED
CART_ITEM_ADDED
CART_ITEM_REMOVED
CHECKOUT_STARTED
CHECKOUT_COMPLETED

ORDER_CREATED
ORDER_PLACED
ORDER_CONFIRMED
ORDER_ALLOCATED
ORDER_CANCELLED

INVENTORY_RECEIVED
INVENTORY_MOVED
INVENTORY_RESERVED
INVENTORY_RELEASED
INVENTORY_ADJUSTED

FULFILLMENT_CREATED
ITEM_PICKED
ITEM_PACKED

SHIPMENT_REQUESTED
SHIPMENT_DISPATCHED
SHIPMENT_DELIVERED

RETURN_REQUESTED
RETURN_AUTHORIZED
RETURN_RECEIVED
RETURN_INSPECTED
RETURN_ACCEPTED
RETURN_REJECTED

REFUND_REQUESTED
EXCHANGE_CREATED

WARRANTY_CREATED
WARRANTY_CLAIM_CREATED

CUSTOMER_CASE_CREATED
CUSTOMER_CASE_UPDATED

REVIEW_CREATED
REVIEW_MODERATED

LOYALTY_EVENT_RECORDED

SUBSCRIPTION_CREATED
SUBSCRIPTION_RENEWED
SUBSCRIPTION_CANCELLED

MARKETPLACE_SELLER_CREATED
MARKETPLACE_OFFER_CREATED

AI_RECOMMENDATION_CREATED
COMMERCE_SIMULATION_CREATED
```

---

# 715.67 — Native APIs

```axiom
create_product()
create_product_variant()
create_sku()
register_barcode()

create_category()
create_catalog()
publish_catalog()

create_seller()
create_customer()
create_customer_profile()

create_store()
create_pos_register()
open_pos_session()
close_pos_session()
create_pos_transaction()

create_offer()
create_price()
create_price_rule()

create_promotion()
apply_promotion()
create_coupon()
redeem_coupon()

create_cart()
add_cart_item()
remove_cart_item()
start_checkout()
complete_checkout()

create_order()
place_order()
confirm_order()
cancel_order()

create_inventory()
receive_inventory()
move_inventory()
reserve_inventory()
release_inventory()
adjust_inventory()
calculate_available_to_sell()

create_warehouse()
create_warehouse_location()

create_fulfillment()
allocate_order()
pick_items()
pack_items()

create_shipment_request()
record_delivery_event()

create_return()
authorize_return()
receive_return()
inspect_return()
accept_return()
reject_return()
create_return_disposition()

create_refund_request()
create_exchange()

create_warranty()
create_warranty_claim()

create_customer_case()
create_product_review()

create_loyalty_account()
record_loyalty_event()

create_subscription()

create_marketplace()
create_marketplace_seller()
create_marketplace_offer()

trace_order()
trace_inventory()
trace_product()

reconcile_inventory()
reconcile_order()
reconcile_fulfillment()

simulate_order()
simulate_fulfillment()
simulate_inventory()
simulate_recall()

create_commerce_digital_twin()
replay_commerce_state()
```

---

# 715.68 — Canonical Purchase Flow

```text
Catalog
   ↓
Offer
   ↓
Cart
   ↓
Pricing
   ↓
Promotion
   ↓
Checkout
   ↓
Order
   ↓
Payment Reference
   ↓
Inventory Reservation
   ↓
Fulfillment
   ↓
Shipment
   ↓
Delivery
```

---

# 715.69 — Canonical Store/POS Flow

```text
Customer
   ↓
POS
   ↓
Scan SKU
   ↓
Offer / Price
   ↓
Promotion
   ↓
Cart
   ↓
Order
   ↓
Payment Reference
   ↓
Inventory Movement
   ↓
Receipt Projection
```

---

# 715.70 — Canonical Return Flow

```text
Customer
   ↓
Return Request
   ↓
Authorization
   ↓
Return Shipment
   ↓
Receiving
   ↓
Inspection
   ↓
Disposition
   ├── Restock
   ├── Repair
   ├── Refurbish
   ├── Recycle
   └── Dispose
   ↓
Refund / Exchange Reference
   ↓
AXFINANCE
```

---

# 715.71 — Canonical Inventory Flow

```text
Supplier / Production
       ↓
Receiving
       ↓
Inventory
       ↓
Reservation
       ↓
Allocation
       ↓
Pick
       ↓
Pack
       ↓
Shipment
       ↓
Delivery
```

---

# 715.72 — Food Integration

`AXFOOD` có authoritative:

```text
food product
food lot
food safety
food expiry
food cold-chain requirements
```

`AXRETAIL` owns:

```text
retail offer
catalog presentation
retail inventory
order
fulfillment
customer purchase
```

Ví dụ:

```text
AXFOOD
  Food Lot F-123
       ↓
AXRETAIL
  SKU MILK-001
       ↓
Offer
       ↓
Order
```

Không duplicate food safety state.

---

# 715.73 — Agriculture Integration

Agricultural provenance:

```text
AXAGRICULTURE
      ↓
raw material
      ↓
AXFOOD
      ↓
finished food
      ↓
AXRETAIL
      ↓
retail offer
```

---

# 715.74 — Transport Integration

```text
AXRETAIL
    shipment_request
         ↓
AXTRANSPORT
    route / vehicle / carrier
         ↓
    delivery event
         ↓
AXRETAIL
```

---

# 715.75 — Finance Integration

```text
AXRETAIL
   │
   ├── payment intent
   ├── refund request
   ├── settlement reference
   ├── invoice reference
   └── tax calculation reference
              ↓
         AXFINANCE
```

Không được mutate balance trực tiếp.

---

# 715.76 — AI Architecture

AI có thể hỗ trợ:

```text
product recommendation
search ranking
demand forecasting
inventory forecasting
fraud/anomaly detection
dynamic assortment
warehouse optimization
fulfillment optimization
customer support
product classification
catalog enrichment
image classification
price estimation
return anomaly detection
```

AI output phải:

```text
derived
versioned
explainable where required
auditable
non-authoritative by default
```

---

# 715.77 — AI Boundary

Không:

```text
AI recommendation
    =
customer intent

AI fraud score
    =
fraud determination

AI return score
    =
return rejection

AI price prediction
    =
authoritative price

AI demand forecast
    =
inventory fact

AI review classifier
    =
truth determination

AI customer segmentation
    =
identity fact
```

---

# 715.78 — Commerce Personalization

```axiom
personalization_result {
    customer
    context
    candidate_items
    model
    ranking
    confidence
    generated_at
}
```

Personalization là projection.

Không mutate product catalog.

---

# 715.79 — Search

```axiom
commerce_search {
    query
    filters
    sort
    channel
    locale
    result
}
```

Search index là derived state.

Canonical product data vẫn nằm ở source-of-truth domain.

---

# 715.80 — Commerce Analytics

```axiom
commerce_metric {
    metric
    dimensions
    period
    value
    source
    methodology
}
```

Ví dụ:

```text
sales
conversion
inventory_turnover
return_rate
fulfillment_time
stockout_rate
```

Metrics không được coi là authoritative transaction state.

---

# 715.81 — Event Sourcing

Core architecture:

```text
Command
   ↓
Authorization
   ↓
Validation
   ↓
Deterministic Domain Logic
   ↓
Immutable Event
   ↓
Projection
   ↓
Query
```

Không:

```text
UPDATE orders SET status = ...
```

là authoritative mutation.

---

# 715.82 — Idempotency

Các command external phải hỗ trợ:

```axiom
idempotency_key
```

Đặc biệt:

```text
create_order
place_order
reserve_inventory
create_payment_reference
ship_order
create_return
request_refund
```

---

# 715.83 — Exactly-Once Semantic Boundary

Network không đảm bảo exactly-once.

Axiom phải cung cấp:

```text
at-least-once transport
+
idempotent command
+
deduplicated event identity
```

để tạo **exactly-once business effect**.

---

# 715.84 — Offline POS

POS có thể hoạt động offline:

```text
POS
 ↓
local event log
 ↓
local inventory projection
 ↓
transaction
 ↓
reconnect
 ↓
sync
 ↓
reconciliation
```

Offline POS không được tự giả định authoritative global inventory.

---

# 715.85 — Inventory Conflict

Nếu hai node offline cùng bán:

```text
Store A → quantity 1
Store B → quantity 1
Global quantity = 1
```

Axiom phải giữ:

```text
both events
conflict
reconciliation state
```

Không silently discard một transaction.

---

# 715.86 — Security Capabilities

```text
retail.catalog.read
retail.catalog.write

retail.product.read
retail.product.write

retail.price.read
retail.price.manage

retail.offer.read
retail.offer.manage

retail.customer.read
retail.customer.write

retail.order.read
retail.order.create
retail.order.manage

retail.inventory.read
retail.inventory.manage
retail.inventory.adjust

retail.fulfillment.read
retail.fulfillment.execute

retail.return.read
retail.return.manage

retail.refund.request

retail.pos.execute
retail.pos.admin

retail.marketplace.manage

retail.analytics.read

retail.ai.execute
retail.simulation.execute

retail.admin
```

---

# 715.87 — Privacy

Customer data phải tách:

```text
identity
commerce profile
purchase history
preferences
support cases
behavioral analytics
```

Không mặc định cho mọi service truy cập toàn bộ customer history.

---

# 715.88 — Fraud / Abuse Boundary

Fraud/anomaly engine có thể tạo:

```axiom
commerce_risk_signal {
    subject
    signal
    model
    confidence
    evidence
}
```

Nhưng:

```text
risk_signal
    ≠
fraud_fact
```

Các quyết định adverse cần policy + authorization + appropriate review mechanism.

---

# 715.89 — Formal Invariants

```text
RTL-INV-01   Product identity is distinct from SKU.
RTL-INV-02   Product variant is distinct from offer.
RTL-INV-03   Offer is channel/seller contextual.
RTL-INV-04   Price is versioned.
RTL-INV-05   Monetary authority belongs to AXFINANCE.
RTL-INV-06   Promotion is distinct from applied discount.
RTL-INV-07   Cart is distinct from order.
RTL-INV-08   Checkout is distinct from payment settlement.
RTL-INV-09   Order is distinct from shipment.
RTL-INV-10   Inventory is distinct from available-to-sell.

RTL-INV-11   Reservation is distinct from sale.
RTL-INV-12   Inventory movements are immutable events.
RTL-INV-13   Inventory reservations are bounded by policy.
RTL-INV-14   Available-to-sell cannot exceed eligible inventory.
RTL-INV-15   Fulfillment allocation is traceable.
RTL-INV-16   Package contents are traceable to order lines.
RTL-INV-17   Shipment state belongs to AXTRANSPORT.
RTL-INV-18   Delivery evidence is preserved.
RTL-INV-19   Return request is distinct from return authorization.
RTL-INV-20   Return inspection is distinct from refund.

RTL-INV-21   Refund does not directly mutate financial balance.
RTL-INV-22   Exchange preserves original order lineage.
RTL-INV-23   Warranty is versioned.
RTL-INV-24   Customer identity belongs to AXIDENTITY.
RTL-INV-25   Product safety state belongs to source domain.
RTL-INV-26   Food safety state belongs to AXFOOD.
RTL-INV-27   Agricultural provenance belongs to AXAGRICULTURE.
RTL-INV-28   Transport state belongs to AXTRANSPORT.
RTL-INV-29   Legal rules belong to AXLAW.
RTL-INV-30   Administrative authority belongs to AXGOV.

RTL-INV-31   Review is customer-generated content.
RTL-INV-32   Review cannot become authoritative product fact.
RTL-INV-33   AI recommendation is derived.
RTL-INV-34   AI fraud signal is not a fraud determination.
RTL-INV-35   AI demand forecast is not inventory fact.
RTL-INV-36   Search index is derived.
RTL-INV-37   Analytics metrics are derived.
RTL-INV-38   Offline events retain provenance.
RTL-INV-39   Duplicate external commands cannot duplicate business effects.
RTL-INV-40   Simulation cannot mutate authoritative commerce state.
```

---

# 715.90 — Test Matrix

```text
product_tests
variant_tests
sku_tests
barcode_tests

category_tests
catalog_tests
publication_tests

seller_tests
customer_tests
store_tests
pos_tests

offer_tests
price_tests
promotion_tests
coupon_tests

cart_tests
checkout_tests
order_tests
order_state_tests

inventory_tests
reservation_tests
allocation_tests
warehouse_tests

fulfillment_tests
pick_pack_tests
shipment_boundary_tests

return_tests
inspection_tests
disposition_tests
refund_boundary_tests
exchange_tests

warranty_tests
support_case_tests
review_tests
loyalty_tests
subscription_tests

marketplace_tests

food_integration_tests
agriculture_integration_tests
transport_integration_tests
finance_integration_tests
identity_integration_tests
civil_integration_tests
law_integration_tests
government_integration_tests

offline_pos_tests
distributed_inventory_tests
reconciliation_tests
idempotency_tests

AI_boundary_tests
privacy_tests
security_tests
audit_tests
replay_tests
simulation_tests
digital_twin_tests
```

---

# 715.91 — Property Tests

```text
create_order()
    creates exactly one logical order under same idempotency key

reserve_inventory()
    never reserves unavailable quantity

release_inventory()
    never creates inventory from nothing

inventory_replay(events)
    == reconstructed inventory

trace_order(order)
    reaches only related commerce entities

return(order_line)
    cannot exceed eligible purchased quantity

refund(return)
    cannot exceed authorized refund amount

split_inventory()
    preserves total quantity

merge_inventory()
    preserves lineage

price_projection(version)
    reproduces price valid for requested timestamp

promotion_evaluation()
    deterministic for same inputs/version

offline_sync()
    preserves every valid event

duplicate_delivery_event()
    cannot duplicate business effect

simulation(snapshot)
    leaves authoritative state unchanged
```

---

# 715.92 — Completion Criteria

`BOOTSTRAP-715` hoàn thành khi đã freeze:

1. Product model.
2. Product variant.
3. SKU.
4. Barcode.
5. Category.
6. Catalog.
7. Catalog publication.
8. Seller.
9. Customer.
10. Store.
11. POS.
12. Offer.
13. Price.
14. Promotion.
15. Coupon.
16. Cart.
17. Checkout.
18. Order.
19. Order line.
20. Inventory.
21. Reservation.
22. Warehouse.
23. Fulfillment.
24. Pick/pack.
25. Shipment boundary.
26. Delivery projection.
27. Return.
28. Return inspection.
29. Return disposition.
30. Refund boundary.
31. Exchange.
32. Warranty.
33. Customer support.
34. Review.
35. Loyalty.
36. Subscription.
37. Marketplace.
38. Traceability.
39. Event model.
40. Idempotency.
41. Offline POS.
42. Distributed inventory reconciliation.
43. AI boundary.
44. Privacy.
45. Security.
46. Audit/replay.
47. Simulation.
48. Digital twin.
49. Finance integration.
50. Transport integration.
51. Food integration.
52. Agriculture integration.
53. Identity/Civil integration.
54. Law/Government integration.
55. Formal invariants.
56. Test matrix.

---

# 715.93 — Definition of Done

```text
BOOTSTRAP-715
STATUS: COMPLETE / FROZEN

AXRETAIL 5.0
    ├── Product & Catalog
    ├── Product Variants / SKU
    ├── Sellers / Customers
    ├── Stores / POS
    ├── Offers
    ├── Pricing
    ├── Promotions
    ├── Coupons
    ├── Cart / Checkout
    ├── Orders
    ├── Inventory
    ├── Warehouses
    ├── Reservations
    ├── Fulfillment
    ├── Packaging
    ├── Shipment Integration
    ├── Delivery
    ├── Returns
    ├── Refund Integration
    ├── Exchanges
    ├── Warranty
    ├── Customer Service
    ├── Reviews
    ├── Loyalty
    ├── Subscription
    ├── Marketplace
    ├── Traceability
    ├── Offline POS
    ├── Distributed Reconciliation
    ├── AI
    ├── Privacy
    ├── Security
    ├── Audit
    ├── Replay
    ├── Simulation
    └── Digital Twin
```

**BOOTSTRAP-715 / AXRETAIL — ARCHITECTURAL BASELINE FROZEN.**

---

## Tiếp theo trong chuỗi kiến trúc

**BOOTSTRAP-716 — AXLOGISTICS**

**Native Logistics, Warehousing, Freight, Shipment Planning, Fleet Coordination, Supply Chain, Inventory Movement, Routing Interfaces, Customs/Trade References, Delivery Networks & Supply-Chain Runtime 5.0.**