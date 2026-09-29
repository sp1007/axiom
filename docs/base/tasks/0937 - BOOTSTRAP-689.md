Tiếp tục với **BOOTSTRAP-689**. Đây là lớp nối trực tiếp từ `AXCONSTRUCTION`, `AXCOMMERCE`, `AXFINANCE`, `AXLAW` và `AXCIVILIZATION`, tập trung vào **nhà ở, bất động sản, đất đai, quyền sử dụng, cho thuê, thế chấp và thị trường nhà ở** nhưng không lặp lại phần hạ tầng xây dựng đã có.

:::writing{variant="document" id="58321" title="BOOTSTRAP-689 — Native AI Civilization-Scale Housing, Real Estate, Land Property, Rental, Mortgage, Urban Housing Markets, Buildings & Residential Systems Runtime 5.0"}
# BOOTSTRAP-689
## Native AI Civilization-Scale Housing, Real Estate, Land Property, Rental, Mortgage, Urban Housing Markets, Buildings & Residential Systems Runtime 5.0

**Status:** Architecture Specification  
**Layer:** Civilization / Economic / Physical-Digital Systems  
**Depends on:** AXCONSTRUCTION, AXCOMMERCE, AXFINANCE, AXLAW, AXGOV, AXTRANSPORT, AXRESOURCE, AX670  
**Primary namespace:** `AXHOUSING`

---

# 1. Mục tiêu

`AXHOUSING` là runtime và semantic domain của Axiom dành cho:

- nhà ở;
- căn hộ;
- nhà riêng;
- phòng ở;
- khu dân cư;
- tòa nhà dân cư;
- bất động sản;
- parcel/land;
- quyền sử dụng và quyền sở hữu dưới dạng tham chiếu pháp lý;
- mua bán bất động sản;
- cho thuê;
- thuê nhà;
- tiền thuê;
- đặt cọc;
- hợp đồng thuê;
- thế chấp;
- khoản vay liên quan đến nhà ở;
- valuation;
- appraisal;
- affordability;
- housing supply/demand;
- vacancy;
- housing inventory;
- residential development;
- urban housing market;
- housing policy simulation;
- residential digital twin;
- housing analytics;
- housing AI;
- housing-market simulation.

Mục tiêu không phải xây một hệ thống quản lý bất động sản đơn thuần.

Mục tiêu là tạo một **native semantic runtime** để Axiom có thể biểu diễn đồng thời:

```text
LAND
  ↓
PROPERTY
  ↓
BUILDING
  ↓
DWELLING
  ↓
HOUSEHOLD / OCCUPANT
  ↓
TENANCY / OWNERSHIP
  ↓
FINANCE
  ↓
URBAN HOUSING MARKET
  ↓
CIVILIZATION SIMULATION
```

---

# 2. Nguyên tắc kiến trúc

## 2.1. Không đồng nhất vật thể với quyền

Phải phân biệt:

```text
Land
Property
Building
Dwelling
Ownership
Possession
Occupancy
Lease
Mortgage
LegalRight
```

Ví dụ:

```text
House ≠ OwnershipOfHouse
House ≠ Person
Occupant ≠ Owner
Tenant ≠ Owner
Mortgage ≠ Ownership
Listing ≠ Property
```

---

# 3. Ranh giới domain

## 3.1. AXCONSTRUCTION

`AXCONSTRUCTION` chịu trách nhiệm:

- thiết kế;
- BIM;
- vật liệu;
- xây dựng;
- công trường;
- tiến độ xây dựng;
- kết cấu;
- contractor;
- construction equipment.

`AXHOUSING` chịu trách nhiệm:

- residential property;
- dwelling;
- occupancy;
- residential inventory;
- rental;
- housing market;
- residential lifecycle.

---

# 4. AXLAW boundary

Các khái niệm sau chỉ được tham chiếu:

```text
OwnershipRightRef
LandUseRightRef
LeaseRightRef
MortgageLienRef
PropertyRegistrationRef
ZoningRef
PermitRef
HousingRegulationRef
```

`AXHOUSING` không trở thành authority cuối cùng quyết định quyền sở hữu.

Nguyên tắc:

```text
HousingFact ≠ LegalAuthority
PropertyRecord ≠ CourtJudgment
MarketListing ≠ LegalTitle
```

---

# 5. AXFINANCE boundary

`AXHOUSING` không sở hữu ledger tài chính.

Các object:

```text
Mortgage
RentPayment
Deposit
PropertyTaxRef
LoanRef
SettlementRef
```

chỉ chứa reference đến `AXFINANCE`.

Nguyên tắc:

```text
RentSchedule ≠ FinancialLedger
MortgageAgreement ≠ LoanLedger
PropertyPrice ≠ SettlementAmount
```

---

# 6. AXGOV boundary

Chính quyền có thể cung cấp:

```text
ZoningRef
PermitRef
AddressRef
PropertyRegistryRef
HousingProgramRef
BuildingCodeRef
```

Nhưng:

```text
GovernmentRecord
    ≠
HousingRuntimeTruth
```

Axiom phải hỗ trợ provenance để biết nguồn dữ liệu nào đang được sử dụng.

---

# 7. Mô hình thế giới

## 7.1. Land

```text
LandParcel
LandBoundary
LandUse
LandUseRestriction
LandRegion
LandZone
```

Ví dụ:

```axiom
land parcel "P-001" {
    area: 120.5 m2
    zone: residential
}
```

---

# 8. Property

```text
Property
PropertyUnit
PropertyComponent
PropertyAddress
PropertyIdentifier
PropertyStatus
PropertyHistory
```

Một property có thể là:

```text
House
Apartment
Condominium
Room
DormitoryUnit
Villa
Townhouse
MixedUseUnit
ResidentialLand
```

---

# 9. Building

Building thuộc semantic layer của housing khi mục đích sử dụng là residential.

```text
ResidentialBuilding
BuildingUnit
Floor
Entrance
CommonArea
SharedFacility
BuildingSystemRef
```

Ví dụ:

```text
Building
 ├── Floor
 │    ├── Unit
 │    └── Unit
 ├── CommonArea
 └── SharedFacility
```

---

# 10. Dwelling

`Dwelling` là đơn vị nhà ở có thể được một household hoặc occupant sử dụng.

```text
Dwelling {
    id
    property
    building
    unit
    type
    area
    room_count
    occupancy_capacity
    condition
    accessibility
    utilities
}
```

---

# 11. Household

Không đồng nhất:

```text
Household ≠ Person
Household ≠ Family
```

Một household có thể chứa:

```text
PersonRef[]
AgentRef[]
```

và có thể thay đổi theo thời gian.

```text
HouseholdMembership {
    household
    member
    start
    end
    role
}
```

---

# 12. Occupancy

Occupancy biểu diễn việc một dwelling đang được sử dụng.

```text
Occupancy {
    dwelling
    occupant
    household
    start
    end
    basis
}
```

`basis` có thể:

```text
owner
tenant
guest
institutional
temporary
authorized
unknown
```

Không được suy luận quyền sở hữu từ occupancy.

---

# 13. Ownership

Housing chỉ lưu:

```text
OwnershipRef
OwnershipShare
OwnershipPeriod
OwnershipSource
```

Ví dụ:

```text
Property
 ├── OwnerRef A: 50%
 └── OwnerRef B: 50%
```

Quyền pháp lý thực tế được xác nhận bởi `AXLAW`.

---

# 14. Tenancy

Mô hình thuê:

```text
Lease
Tenant
Landlord
RentalUnit
RentSchedule
Deposit
LeaseTerm
LeaseCondition
LeaseEvent
```

Lifecycle:

```text
Draft
→ Offered
→ Accepted
→ Active
→ Renewed
→ Expired
→ Terminated
```

Nhánh:

```text
Rejected
Cancelled
Disputed
```

---

# 15. Rental Listing

Phân biệt:

```text
Property
Listing
Offer
Lease
```

Một property có thể có nhiều listing theo thời gian.

```text
Property
   ↓
Listing
   ↓
Inquiry
   ↓
Offer
   ↓
Lease
```

Không được coi:

```text
Listing = Availability
```

và:

```text
Listing ≠ LegalAvailability
```

---

# 16. Rent

```text
RentSchedule {
    amount
    currency
    period
    due_date
    escalation_rule
}
```

Rent có thể:

```text
fixed
indexed
variable
usage_based
tiered
```

Payment thực tế thuộc `AXFINANCE`.

---

# 17. Deposit

```text
SecurityDeposit {
    amount
    currency
    holder_ref
    conditions
    status
}
```

Lifecycle:

```text
Required
→ Collected
→ Held
→ PartiallyReturned
→ Returned
```

---

# 18. Mortgage

Mortgage phải được mô hình hóa thành nhiều lớp:

```text
Property
    ↓
MortgageRef
    ↓
LoanRef
    ↓
FinancialLedger
```

Housing chỉ giữ:

```text
MortgageRef
CollateralPropertyRef
LoanStatusRef
LienRef
```

Không tự trở thành loan engine.

---

# 19. Property valuation

Hỗ trợ:

```text
MarketValue
AppraisedValue
AssessedValue
RentalValue
ReplacementValue
LandValue
ImprovementValue
```

Không được đồng nhất:

```text
MarketValue = SalePrice
```

Một transaction thực tế có thể xảy ra với:

```text
SalePrice != MarketValue
```

---

# 20. Valuation model

```text
Valuation {
    property
    value
    currency
    valuation_type
    timestamp
    method
    confidence
    source
}
```

Methods:

```text
ComparableSales
IncomeApproach
CostApproach
LandResidual
HybridModel
AIModel
HumanAppraisal
ObservedTransaction
```

---

# 21. AI valuation

AI có thể tạo:

```text
EstimatedValue
PriceRange
RentalEstimate
DemandEstimate
LiquidityEstimate
```

nhưng:

```text
Estimate ≠ Fact
Estimate ≠ LegalAppraisal
Estimate ≠ TransactionPrice
```

---

# 22. Housing affordability

Định nghĩa:

```text
AffordabilityAssessment
```

có thể sử dụng:

```text
income
rent
housing_cost
debt_service
household_size
location
transport_cost
utility_cost
```

Nhưng hệ thống phải phân biệt:

```text
ObservedIncome
EstimatedIncome
DeclaredIncome
ProjectedIncome
```

---

# 23. Housing cost

Tổng chi phí nhà ở có thể gồm:

```text
Rent
MortgagePaymentRef
PropertyTaxRef
InsuranceRef
UtilityCostRef
MaintenanceCostRef
ManagementFee
TransportExternalityEstimate
```

Không được cộng các giá trị có semantic khác nhau mà không khai báo.

---

# 24. Housing inventory

Housing inventory:

```text
HousingInventory {
    region
    total_units
    occupied_units
    vacant_units
    under_construction
    planned_units
    unavailable_units
}
```

Trạng thái:

```text
Occupied
Vacant
Available
Reserved
UnderConstruction
Uninhabitable
Demolished
Planned
```

---

# 25. Vacancy

Phân biệt:

```text
PhysicalVacancy
MarketVacancy
FunctionalVacancy
TemporaryVacancy
LongTermVacancy
```

Ví dụ:

```text
Unit có người sở hữu nhưng không rao bán
```

không đồng nghĩa:

```text
AvailableForSale
```

---

# 26. Housing supply

Supply model:

```text
HousingSupply {
    existing
    available
    under_construction
    planned
    potential
}
```

Không được coi:

```text
PotentialSupply = ActualSupply
```

---

# 27. Housing demand

```text
HousingDemand {
    observed
    expressed
    effective
    latent
    forecast
}
```

Phân biệt:

```text
SearchDemand
RentalDemand
PurchaseDemand
OccupancyDemand
```

---

# 28. Housing market

```text
HousingMarket {
    region
    property_type
    time_window
    supply
    demand
    transactions
    listings
    rents
    prices
    vacancy
}
```

---

# 29. Market state

Mọi dữ liệu thị trường phải mang provenance:

```text
Observed
Estimated
Forecast
Simulated
Derived
Imported
Synthetic
```

Invariant:

```text
Observed ≠ Forecast
Forecast ≠ Simulated
Simulated ≠ Transaction
```

---

# 30. Property transaction

Workflow:

```text
Listing
→ Inquiry
→ Viewing
→ Offer
→ Negotiation
→ Agreement
→ DueDiligence
→ Settlement
→ Transfer
```

`Settlement` thuộc `AXFINANCE`.

`Transfer` pháp lý thuộc `AXLAW`.

---

# 31. Due diligence

Housing runtime hỗ trợ:

```text
TitleCheckRef
PermitCheckRef
BuildingConditionRef
EncumbranceRef
TaxStatusRef
UtilityStatusRef
EnvironmentalRiskRef
```

Không tự kết luận legal validity nếu không có authoritative source.

---

# 32. Property condition

```text
ConditionAssessment {
    structural
    electrical
    plumbing
    envelope
    interior
    safety
    accessibility
    energy
}
```

Condition có thể:

```text
Excellent
Good
Fair
Poor
Critical
Unknown
```

Đây là classification dữ liệu, không phải legal safety certification.

---

# 33. Residential utilities

Housing có thể tham chiếu:

```text
ElectricityConnectionRef
WaterConnectionRef
GasConnectionRef
WasteConnectionRef
InternetConnectionRef
DistrictHeatingRef
CoolingSystemRef
```

Resource accounting thuộc `AXRESOURCE`.

---

# 34. Residential energy

Hỗ trợ:

```text
EnergyRating
EnergyConsumption
EnergyGeneration
EnergyStorage
EfficiencyMeasure
RetrofitPlan
```

Ví dụ:

```text
Dwelling
 ├── Consumption
 ├── SolarGeneration
 └── BatteryStorage
```

---

# 35. Building maintenance

Housing lifecycle:

```text
Operational
→ MaintenanceDue
→ Maintenance
→ Renovation
→ Rehabilitated
```

Maintenance execution có thể delegate cho:

```text
AXCONSTRUCTION
AXMANUFACTURING
AXRESOURCE
```

---

# 36. Housing lifecycle

```text
Land
→ Development
→ Construction
→ Completion
→ Occupancy
→ Maintenance
→ Renovation
→ Reuse
→ Abandonment
→ Demolition
```

---

# 37. Housing development

```text
HousingDevelopment {
    site
    project_ref
    units_planned
    units_completed
    schedule
    cost_ref
    permits_ref
    financing_ref
}
```

`Project`, `construction schedule`, `contractor` thuộc `AXCONSTRUCTION`.

---

# 38. Residential development pipeline

```text
Land
→ Feasibility
→ Planning
→ Approval
→ Financing
→ Construction
→ Completion
→ Marketing
→ Occupancy
```

Mỗi stage phải có:

```text
state
timestamp
source
authority
```

---

# 39. Urban housing topology

Housing phải có spatial model:

```text
Continent
→ Country
→ Region
→ City
→ District
→ Neighborhood
→ Block
→ Parcel
→ Building
→ Unit
→ Room
```

Đây là logical topology.

Không bắt buộc toàn bộ layer phải tồn tại.

---

# 40. Address

Address:

```text
Address {
    country
    region
    city
    district
    locality
    street
    number
    postal_code
    geo_ref
}
```

Address không phải identity của property.

Một property có thể:

```text
có nhiều address representation
```

---

# 41. Geospatial integration

Hỗ trợ:

```text
Point
Polygon
MultiPolygon
Line
BoundingBox
SpatialReference
```

Có thể tích hợp GIS provider nhưng semantic core không phụ thuộc provider cụ thể.

---

# 42. Housing accessibility

Housing có thể mô tả:

```text
WheelchairAccess
Elevator
AccessibleBathroom
AccessibleEntrance
VisualAccessibility
AuditoryAccessibility
EmergencyAccess
```

Không được suy luận tình trạng sức khỏe cá nhân từ các thuộc tính này.

---

# 43. Household housing preferences

Có thể lưu:

```text
LocationPreference
SizePreference
RoomPreference
BudgetConstraint
AccessibilityRequirement
AmenityPreference
CommuteConstraint
```

Nhưng:

```text
Preference ≠ Identity
Preference ≠ SensitiveAttribute
```

---

# 44. Housing matching

Matching engine:

```text
Household
+
HousingInventory
+
Constraints
→
CandidateSet
```

Kết quả:

```text
Match
Compatibility
ConstraintViolation
Explanation
```

Không biến recommendation thành automatic allocation nếu chưa được cấp authority.

---

# 45. Housing recommendation

AI có thể:

```text
recommend_property()
recommend_rental()
recommend_location()
estimate_affordability()
estimate_commute()
estimate_total_housing_cost()
```

Phải trả về:

```text
Recommendation {
    candidates
    rationale
    constraints
    confidence
    provenance
}
```

---

# 46. AI housing agent

Agent có thể thực hiện:

```text
search
compare
schedule_viewing
prepare_application
estimate_cost
monitor_market
```

Các hành động có tác động pháp lý/tài chính phải yêu cầu capability riêng:

```text
housing.transaction.write
finance.payment.execute
law.contract.execute
```

---

# 47. Housing simulation

Simulation state:

```text
HousingSimulation {
    scenario
    geography
    population
    housing_stock
    supply
    demand
    prices
    rents
    policy
    financing
    transport
}
```

Ví dụ:

```text
simulate {
    new_units += 10000
    interest_rate = scenario.rate
    migration = scenario.migration
}
```

Kết quả:

```text
ProjectedHousingStock
ProjectedVacancy
ProjectedRent
ProjectedPrice
ProjectedAffordability
```

Không được ghi đè live state.

---

# 48. Urban digital twin

```text
HousingTwin
 ├── Land
 ├── Buildings
 ├── Units
 ├── Households
 ├── Occupancy
 ├── InfrastructureRefs
 ├── MarketState
 ├── Energy
 └── SimulationState
```

Mỗi field phải có:

```text
source
timestamp
confidence
state_type
```

---

# 49. Housing policy simulation

Có thể mô phỏng:

```text
zoning_change
new_housing_supply
rent_policy
tax_change
subsidy
mortgage_condition
infrastructure_change
population_change
migration
```

Kết quả phải được đánh dấu:

```text
SIMULATED
```

không được coi là observed fact.

---

# 50. Affordability simulation

Input:

```text
income_distribution
rent_distribution
house_price_distribution
interest_rate
household_size
housing_supply
```

Output:

```text
affordability_distribution
rent_burden_distribution
ownership_access_distribution
```

Không suy luận giá trị cá nhân của con người từ các chỉ số này.

---

# 51. Housing economics

Housing analytics hỗ trợ:

```text
PriceIndex
RentIndex
VacancyRate
AbsorptionRate
HousingStarts
HousingCompletions
TurnoverRate
MedianPrice
MeanPrice
PricePerArea
RentPerArea
RentToPriceRatio
AffordabilityIndex
```

Các statistic phải giữ:

```text
population
geography
time_window
method
```

để tránh sử dụng sai ngữ cảnh.

---

# 52. Temporal model

Property state thay đổi theo thời gian.

Không được lưu:

```text
property.owner = X
```

nếu hệ thống cần historical correctness.

Thay vào đó:

```text
OwnershipRecord {
    owner
    valid_from
    valid_to
}
```

Tương tự:

```text
LeaseRecord
OccupancyRecord
ValuationRecord
ListingRecord
ConditionRecord
```

---

# 53. Event model

Các event chính:

```text
PropertyCreated
PropertyUpdated
PropertyListed
ListingWithdrawn
ViewingScheduled
OfferSubmitted
OfferAccepted
TransactionCreated
TransactionCompleted
LeaseCreated
LeaseStarted
LeaseRenewed
LeaseEnded
OccupancyStarted
OccupancyEnded
ValuationRecorded
MortgageLinked
MaintenanceStarted
MaintenanceCompleted
RenovationStarted
RenovationCompleted
PropertyTransferred
```

---

# 54. Event sourcing boundary

Housing có thể sử dụng event sourcing:

```text
PropertyAggregate
LeaseAggregate
BuildingAggregate
HousingMarketAggregate
```

Nhưng authoritative legal/financial event phải giữ provenance đến domain owner.

---

# 55. Core type system

Các type chuẩn:

```text
LandParcel
Property
PropertyUnit
ResidentialBuilding
Dwelling
Room
Household
Occupancy
OwnershipRef
Lease
TenantRef
LandlordRef
RentalListing
RentalOffer
SaleListing
PurchaseOffer
PropertyTransaction
PropertyValuation
PropertyCondition
PropertyMaintenance
MortgageRef
HousingInventory
HousingSupply
HousingDemand
HousingMarket
HousingIndex
HousingSimulation
HousingTwin
HousingPolicyScenario
HousingRecommendation
HousingEvent
```

---

# 56. Property identity

Property ID phải ổn định:

```text
PropertyId
```

không được dùng:

```text
address
listing_id
owner_id
```

làm identity chính.

---

# 57. Listing identity

Listing có lifecycle riêng:

```text
ListingId
PropertyId
ListingType
Status
CreatedAt
ClosedAt
```

Một property có thể:

```text
listing_001
listing_002
listing_003
```

theo thời gian.

---

# 58. Rental state machine

```text
DRAFT
→ PUBLISHED
→ INQUIRY
→ OFFERED
→ ACCEPTED
→ ACTIVE
→ RENEWED
→ EXPIRED
```

Branches:

```text
WITHDRAWN
REJECTED
CANCELLED
TERMINATED
DISPUTED
```

---

# 59. Sale state machine

```text
DRAFT
→ LISTED
→ OFFER_RECEIVED
→ NEGOTIATION
→ UNDER_CONTRACT
→ DUE_DILIGENCE
→ SETTLEMENT
→ TRANSFERRED
```

Branches:

```text
WITHDRAWN
FAILED
CANCELLED
DISPUTED
```

---

# 60. Housing transaction atomicity

Một transaction hoàn chỉnh có thể liên quan:

```text
Housing
Finance
Law
Registry
```

Không được giả định:

```text
housing.commit()
```

đồng nghĩa toàn bộ các domain đã commit.

Phải hỗ trợ:

```text
CrossDomainTransaction
Saga
Compensation
ExternalConfirmation
```

---

# 61. Capability model

Các capability chuẩn:

```text
housing.read
housing.write
property.read
property.write
land.read
land.write
building.read
building.write
dwelling.read
dwelling.write
occupancy.read
occupancy.write
ownership.read
lease.read
lease.write
listing.read
listing.write
transaction.read
transaction.write
valuation.read
valuation.write
mortgage.read
inventory.read
market.read
analytics.run
recommendation.run
simulation.run
digital_twin.read
digital_twin.write
maintenance.write
development.write
admin
```

---

# 62. Privacy

Housing data có thể liên quan trực tiếp đến đời sống riêng tư.

Phải hỗ trợ:

```text
FieldLevelAccess
HouseholdScopedAccess
PropertyScopedAccess
TemporalAccess
PurposeBinding
AuditLog
Redaction
DataMinimization
```

---

# 63. Sensitive inference protection

Không được tự động suy luận từ housing data:

```text
health condition
religion
political affiliation
sexual orientation
ethnicity
```

Ví dụ:

```text
address
+
household pattern
```

không được mặc nhiên chuyển thành sensitive profile.

---

# 64. AI explanation

Housing AI recommendation phải có:

```text
WhyMatched
ConstraintsSatisfied
ConstraintsFailed
DataSources
Timestamp
Confidence
ModelVersion
```

Ví dụ:

```text
Recommendation {
    property: P123

    satisfied:
        budget
        area
        location

    failed:
        parking

    source:
        listing
        map
        price_model

    model_version:
        housing-v5
}
```

---

# 65. Anti-manipulation boundary

Housing recommendation không được âm thầm thay đổi:

```text
ranking
price
availability
eligibility
```

mà không khai báo policy.

Phải có:

```text
RankingPolicyRef
PricingPolicyRef
EligibilityPolicyRef
```

---

# 66. Fairness observability

Không tạo một “fairness score” duy nhất cho mọi hệ thống.

Thay vào đó:

```text
Metric
Population
TimeWindow
Policy
DataSource
Method
```

được lưu độc lập.

AI system có thể được audit mà không biến metric thành quyết định tự động.

---

# 67. Housing fraud signals

Có thể phát hiện:

```text
DuplicateListing
ImpossibleAddress
PriceAnomaly
DocumentMismatch
IdentityMismatchRef
TransactionPatternAnomaly
```

Nhưng:

```text
FraudSignal ≠ Fraud
Anomaly ≠ Crime
```

---

# 68. Property provenance

Mỗi property record có thể chứa:

```text
Source
SourceType
ObservedAt
ImportedAt
VerifiedAt
VerifierRef
Confidence
```

Source types:

```text
Registry
Owner
Agent
Tenant
Survey
Sensor
Market
AI
Import
Simulation
```

---

# 69. Sensor integration

Building IoT có thể cung cấp:

```text
temperature
humidity
energy
water
occupancy
air_quality
security_state
equipment_state
```

Sensor facts phải giữ:

```text
device_id
timestamp
measurement
unit
quality
calibration
```

---

# 70. Smart building

Hỗ trợ integration với:

```text
HVAC
Lighting
AccessControl
EnergyManagement
WaterManagement
FireSafetyRef
ElevatorRef
SecurityRef
```

Execution domain có thể thuộc `AXDEVICE`/`AXRESOURCE`.

---

# 71. Residential automation

Axiom agent có thể:

```text
set_temperature()
schedule_maintenance()
detect_leak()
optimize_energy()
notify_occupant()
```

Nhưng safety-critical action phải yêu cầu explicit capability.

---

# 72. CLI

Ví dụ:

```text
axiom housing property list
axiom housing property show P123
axiom housing dwelling list
axiom housing listing search
axiom housing lease list
axiom housing market stats
axiom housing valuation estimate
axiom housing simulation run
axiom housing twin inspect
```

---

# 73. Programmatic API

```axiom
use axhousing

let p = housing.property.get(property_id)

let valuation =
    housing.valuation.estimate(
        property: p,
        method: .hybrid
    )

let listings =
    housing.market.search(
        region: region,
        type: .apartment,
        budget: budget
    )
```

---

# 74. Async API

Các thao tác network/distributed:

```axiom
let registry = await housing.registry.lookup(property_id)
let market = await housing.market.fetch(region)
let valuation = await housing.ai.estimate(property)
```

Compiler phải duy trì semantic distinction giữa:

```text
local read
remote read
transaction
simulation
```

---

# 75. Compiler IR

Housing semantic IR:

```text
PROPERTY_CREATE
PROPERTY_UPDATE
PROPERTY_QUERY
DWELLING_QUERY
OCCUPANCY_CREATE
LEASE_CREATE
LEASE_UPDATE
LISTING_CREATE
LISTING_SEARCH
TRANSACTION_CREATE
VALUATION_ESTIMATE
MARKET_QUERY
HOUSING_SIMULATE
HOUSING_TWIN_QUERY
```

---

# 76. Typed references

Ví dụ:

```text
PropertyRef
DwellingRef
HouseholdRef
LeaseRef
MortgageRef
ListingRef
ValuationRef
MarketRef
SimulationRef
```

Compiler không cho phép:

```text
PropertyRef → FinanceLedgerRef
```

nếu không có explicit conversion/reference bridge.

---

# 77. Units

Housing phải sử dụng typed units:

```text
m
m2
m3
currency
currency/m2
currency/month
currency/year
percent
ratio
```

Không cho:

```text
rent = 20
```

nếu semantic context yêu cầu currency.

---

# 78. Spatial calculations

Native operations:

```text
area()
distance()
contains()
intersects()
overlaps()
centroid()
buffer()
nearest()
```

Phải hỗ trợ coordinate reference system.

---

# 79. Query engine integration

Housing query có thể sử dụng:

```text
property
where
region == Hanoi
and
type == apartment
and
area >= 70m2
and
rent <= 20_000_000 VND/month
```

Compiler có thể push down predicate vào storage/index.

---

# 80. Search indexes

Native index types:

```text
PropertySpatialIndex
ListingIndex
PriceIndex
AvailabilityIndex
TemporalPropertyIndex
MarketIndex
```

---

# 81. Performance

Housing runtime phải tối ưu cho:

- millions of properties;
- billions of historical records;
- large listing indexes;
- temporal queries;
- spatial queries;
- streaming market events;
- simulation workloads.

Ưu tiên:

```text
SoA
columnar analytics
spatial indexing
temporal indexing
memory mapping
zero-copy references
batch query
parallel execution
SIMD
GPU analytics
```

---

# 82. Memory model

Housing object graph không nên tạo hàng triệu heap objects nhỏ.

Khuyến nghị:

```text
PropertyTable
DwellingTable
LeaseTable
OccupancyTable
ListingTable
ValuationTable
EventTable
```

với stable IDs.

Relationship:

```text
PropertyId
DwellingId
LeaseId
```

thay vì pointer graph khổng lồ.

Điều này phù hợp với triết lý Axiom:

```text
flat data + explicit identity + indexed relationships
```

---

# 83. Cache

Housing runtime hỗ trợ:

```text
PropertyCache
ListingCache
MarketSnapshotCache
ValuationCache
SpatialCache
```

Cache phải có:

```text
TTL
Version
Source
InvalidationPolicy
```

---

# 84. Offline mode

Mobile/WASM có thể sử dụng:

```text
HousingOfflineStore
```

với:

```text
snapshot
delta
conflict
sync
```

Không tự ghi đè authoritative state khi conflict.

---

# 85. Conflict resolution

Ví dụ:

```text
local listing update
+
remote listing update
```

Có thể:

```text
LastWriterWins
VersionCheck
FieldMerge
ManualResolution
DomainSpecificResolution
```

Housing không được dùng LWW mặc định cho legal/financial records.

---

# 86. Distributed architecture

```text
HousingEdge
HousingService
HousingMarketNode
PropertyRegistryAdapter
FinanceAdapter
LawAdapter
ConstructionAdapter
ResourceAdapter
```

Có thể chạy:

```text
single process
desktop
mobile
server
cluster
edge
WASM
```

---

# 87. Event streaming

Topics:

```text
housing.property
housing.listing
housing.lease
housing.occupancy
housing.transaction
housing.market
housing.valuation
housing.maintenance
housing.simulation
```

Events phải versioned.

---

# 88. Schema evolution

Không được phá dữ liệu cũ khi thêm field.

Ví dụ:

```text
Dwelling.v1
Dwelling.v2
```

Compiler/runtime hỗ trợ migration:

```text
migrate dwelling 1 → 2
```

---

# 89. AI model registry integration

Valuation/recommendation models phải tham chiếu:

```text
ModelId
ModelVersion
TrainingDataRef
EvaluationRef
DeploymentRef
```

Không lưu model binary trực tiếp trong property record.

---

# 90. Simulation reproducibility

Simulation phải có:

```text
seed
scenario_id
model_version
dataset_version
configuration_hash
code_hash
timestamp
```

để có thể tái tạo kết quả.

---

# 91. Digital twin reproducibility

Twin snapshot:

```text
TwinSnapshot {
    snapshot_id
    timestamp
    source_versions
    property_versions
    market_version
    simulation_version
}
```

---

# 92. Housing scenario DSL

Axiom có thể cung cấp DSL:

```axiom
scenario housing_supply {
    region: "city"
    new_units: 50_000
    completion_year: 2030

    simulate(
        vacancy,
        rent,
        price,
        affordability
    )
}
```

DSL chỉ là declarative layer phía trên core.

---

# 93. Housing policy DSL

```axiom
policy housing_program {
    target: rental_units

    constraint:
        income <= threshold

    intervention:
        subsidy = amount
}
```

Policy execution phải đi qua authority domain thích hợp.

---

# 94. API security

Một agent chỉ có:

```text
housing.read
```

không thể:

```text
lease.write
transaction.write
property.write
```

Agent có:

```text
recommendation.run
```

không được tự động:

```text
transaction.execute
```

---

# 95. Audit

Mọi mutation quan trọng phải ghi:

```text
actor
principal
capability
timestamp
object
before
after
source
reason
correlation_id
```

---

# 96. Emergency mode

Hỗ trợ:

```text
EmergencyHousingState
TemporaryShelter
DisasterHousing
EvacuationHousing
Relocation
```

Nhưng emergency housing phải được tách khỏi normal ownership/lease semantics.

---

# 97. Disaster integration

Housing có thể nhận:

```text
FloodRisk
EarthquakeRisk
StormRisk
FireRisk
LandslideRisk
HeatRisk
```

Risk data có provenance.

Không được coi:

```text
RiskModel ≠ ActualEvent
```

---

# 98. Climate/urban integration

Housing simulation có thể kết hợp:

```text
climate
transport
energy
water
population
employment
commerce
```

để tạo:

```text
UrbanResidentialSimulation
```

---

# 99. Employment-housing integration

Từ `AXLABOR` có:

```text
employment_location
work_schedule
income
```

Housing có:

```text
dwelling_location
housing_cost
commute_distance
```

Có thể tính:

```text
HousingWorkAccessibility
```

nhưng không được biến nó thành đánh giá giá trị con người.

---

# 100. Commerce integration

Từ `AXCOMMERCE`:

```text
shops
services
retail_access
```

Housing có thể tính:

```text
AmenityAccessibility
```

---

# 101. Transport integration

Từ `AXTRANSPORT`:

```text
road
rail
bus
metro
travel_time
```

Housing có thể tính:

```text
TransitAccessibility
CommuteEstimate
```

Đây là dữ liệu phân tích, không phải guarantee.

---

# 102. Resource integration

Từ `AXRESOURCE`:

```text
water
electricity
waste
energy
```

Housing có:

```text
ResidentialResourceProfile
```

---

# 103. Construction integration

```text
HousingDevelopment
        ↓
AXCONSTRUCTION.Project
        ↓
Building
        ↓
Dwelling
```

Không duplicate construction execution model.

---

# 104. Finance integration

```text
Property
 ↓
MortgageRef
 ↓
AXFINANCE.Loan
 ↓
Ledger
```

Housing chỉ giữ reference và housing-specific semantics.

---

# 105. Law integration

```text
Property
 ↓
LegalPropertyRef
 ↓
AXLAW
```

Các vấn đề:

```text
title
ownership
lease law
zoning
tenant rights
property restrictions
```

được authority layer xử lý.

---

# 106. Government integration

Government housing systems có thể cung cấp:

```text
HousingRegistry
PlanningRegistry
AddressRegistry
PermitRegistry
PublicHousingProgram
```

Mỗi record phải có:

```text
issuer
authority
validity
version
```

---

# 107. Civilization model

Housing trở thành một node trong civilization graph:

```text
PERSON
HOUSEHOLD
HOUSING
EMPLOYMENT
COMMERCE
TRANSPORT
ENERGY
WATER
GOVERNMENT
FINANCE
LAW
```

---

# 108. Civilization housing graph

```text
Household
 ├── Occupies → Dwelling
 ├── Pays → Rent
 ├── Works → Employment
 ├── Shops → Commerce
 └── Travels → Transport
```

Các edge đều typed.

---

# 109. AI civilization simulation

Housing agent có thể mô phỏng:

```text
population_change
migration
employment_change
housing_supply
transport_change
energy_change
commerce_change
```

Output:

```text
housing_stock
occupancy
vacancy
rent
price
commute
resource_consumption
```

Mọi output là simulation nếu chưa được quan sát thực tế.

---

# 110. Native annotations

```axiom
@housing_property
@dwelling
@residential
@rental
@ownership_ref
@valuation
@housing_market
@housing_simulation
@housing_twin
@housing_sensitive
```

---

# 111. Compile-time validation

Compiler có thể kiểm tra:

```text
invalid_property_ref
invalid_lease_ref
invalid_unit
invalid_spatial_crs
invalid_currency
invalid_temporal_range
invalid_capability
invalid_cross_domain_write
```

---

# 112. Runtime validation

Runtime kiểm tra:

```text
authorization
version
provenance
state_transition
source freshness
constraint
conflict
```

---

# 113. Determinism

Các operation thuần:

```text
area()
distance()
index()
query()
derive()
```

phải deterministic.

AI/simulation có randomness phải khai báo:

```text
@stochastic
seed
```

---

# 114. Error model

Native errors:

```text
PropertyNotFound
DwellingNotFound
ListingNotFound
LeaseNotFound
OccupancyConflict
PropertyStateConflict
InvalidLeaseTransition
InvalidListingTransition
SpatialReferenceError
ValuationUnavailable
MarketDataUnavailable
AuthorizationDenied
ProvenanceMissing
CrossDomainConflict
SimulationError
```

---

# 115. Observability

Metrics:

```text
housing.property.query
housing.listing.search
housing.lease.active
housing.occupancy.rate
housing.market.snapshot
housing.valuation.latency
housing.simulation.duration
housing.twin.refresh
```

Tracing phải giữ:

```text
property_id
region_id
scenario_id
model_version
```

khi được phép.

---

# 116. Testing

Mục tiêu tối thiểu:

```text
≥ 12,000 automated tests
≥ 1,000 architecture invariants
```

Phân bổ:

```text
2,000 property/dwelling
1,500 lease/rental
1,000 transaction
1,000 valuation
1,000 market
1,000 spatial
1,000 temporal
1,000 privacy/security
1,000 distributed
1,000 simulation
1,000 AI
500 integration
```

---

# 117. Architecture invariants

Các invariant bắt buộc:

```text
PropertyId is stable.
ListingId is not PropertyId.
Occupancy does not imply ownership.
Lease does not imply ownership.
Mortgage does not imply ownership.
Listing does not imply legal availability.
MarketValue does not equal SalePrice.
Forecast does not equal Observation.
Simulation does not equal LiveState.
Recommendation does not equal Authorization.
FraudSignal does not equal Fraud.
Risk does not equal Event.
AI output requires provenance.
Legal authority remains outside AXHOUSING.
Financial settlement remains outside AXHOUSING.
```

---

# 118. Minimal core profile

```text
AXHOUSING_CORE
```

chỉ gồm:

```text
Property
Dwelling
BuildingRef
LandRef
Occupancy
Lease
Listing
Valuation
HousingMarket
HousingEvent
```

---

# 119. Extended profiles

```text
AXHOUSING_PROPERTY
AXHOUSING_RENTAL
AXHOUSING_SALE
AXHOUSING_MORTGAGE
AXHOUSING_VALUATION
AXHOUSING_MARKET
AXHOUSING_SPATIAL
AXHOUSING_URBAN
AXHOUSING_AI
AXHOUSING_SIMULATION
AXHOUSING_DIGITAL_TWIN
AXHOUSING_IOT
AXHOUSING_ENERGY
AXHOUSING_DISASTER
AXHOUSING_DISTRIBUTED
AXHOUSING_GPU
AXHOUSING_WASM
AXHOUSING_MOBILE
AXHOUSING_REALTIME
AXHOUSING_FULL
```

---

# 120. Zero-dependency architecture

Core Axiom housing semantics không được phụ thuộc bắt buộc vào:

```text
PostGIS
GIS vendor
real-estate API
MLS
mortgage provider
bank
cloud
AI provider
database vendor
```

Các hệ thống trên chỉ là provider/adapter.

---

# 121. Provider interfaces

```axiom
trait PropertyRegistryProvider
trait SpatialProvider
trait MarketDataProvider
trait ValuationProvider
trait MortgageProvider
trait HousingAnalyticsProvider
trait HousingAIProvider
trait HousingSensorProvider
```

Ứng dụng có thể thay provider mà không thay semantic model.

---

# 122. Native storage

Provider mặc định có thể dùng:

```text
memory
mmap
file
embedded database
distributed storage
```

Compiler có thể tối ưu query trực tiếp xuống storage provider.

---

# 123. Serialization

Housing object phải serialize được:

```text
AXBIN
AXJSON
AXTEXT
AXCBOR
```

`AXBIN` là format native ưu tiên.

---

# 124. Compact binary

Property binary representation phải hỗ trợ:

```text
stable IDs
dictionary encoding
delta encoding
varint
compressed coordinates
columnar snapshots
```

Mục tiêu:

```text
small
fast
memory-map friendly
versionable
```

---

# 125. AI-readable representation

Housing semantic objects có thể xuất:

```text
.axmeta
.axschema
.axgraph
```

Agent có thể đọc:

```text
entities
relations
constraints
provenance
permissions
history
```

mà không cần reverse-engineer binary.

---

# 126. Example

```axiom
property apartment {
    id: "P-1001"
    type: .apartment
    area: 82.0m2

    location {
        city: "Hanoi"
        district: "Cau Giay"
    }

    valuation {
        estimated: 5_200_000_000VND
        timestamp: now
    }
}
```

---

# 127. Rental example

```axiom
let listing = housing.rental.list(
    property: apartment,
    rent: 18_000_000VND/month,
    deposit: 36_000_000VND,
    term: 12months
)
```

Runtime tạo:

```text
RentalListing
RentSchedule
SecurityDeposit
LeaseProposal
```

chứ chưa tạo financial settlement.

---

# 128. Market query example

```axiom
let market =
    housing.market.query(
        region: hanoi,
        property_type: .apartment,
        period: last_12_months
    )

print market.median_price
print market.vacancy_rate
```

---

# 129. Simulation example

```axiom
let result = housing.simulate {
    region: city
    new_units: 25_000
    population_growth: +4%
    transport_capacity: +15%

    outputs:
        rent
        vacancy
        affordability
}
```

Kết quả được đánh dấu:

```text
SimulationResult
```

không thể tự động ghi vào:

```text
HousingMarket
```

---

# 130. Integration matrix

| Domain | AXHOUSING sử dụng | AXHOUSING sở hữu |
|---|---|---|
| AXCONSTRUCTION | project/building refs | residential lifecycle |
| AXFINANCE | loan/payment/ledger refs | housing financial semantics |
| AXLAW | title/lease/zoning refs | housing operational model |
| AXGOV | registry/program refs | housing domain state |
| AXRESOURCE | utilities/resource data | residential resource profile |
| AXTRANSPORT | travel/accessibility | housing accessibility model |
| AXCOMMERCE | amenities/retail | housing market/listings |
| AXLABOR | employment/income refs | housing-work relation |
| AX670 | population/demography | household housing state |
| AX683 | buildings/cities | residential property semantics |

---

# 131. Final architecture

Axiom civilization stack hiện có thể biểu diễn:

```text
AXRESOURCE
     ↓
AXAGRI
     ↓
AXMANUFACTURING
     ↓
AXCONSTRUCTION
     ↓
AXHOUSING
     ↓
AXTRANSPORT
     ↓
AXCOMMERCE
     ↓
AXLABOR
     ↓
AXFINANCE
     ↓
AXLAW / AXGOV
     ↓
AXCIVILIZATION
```

Trong đó `AXHOUSING` trở thành lớp trung gian quan trọng giữa:

```text
physical environment
economic systems
households
cities
finance
law
civilization simulation
```

---

# 132. Contract cuối cùng

`AXHOUSING` phải đảm bảo:

1. Nhà ở được mô hình hóa độc lập với quyền pháp lý.
2. Property identity ổn định.
3. Listing không đồng nghĩa property availability.
4. Occupancy không đồng nghĩa ownership.
5. Lease không đồng nghĩa ownership.
6. Mortgage không đồng nghĩa ownership.
7. Valuation không đồng nghĩa transaction price.
8. Forecast không đồng nghĩa observation.
9. Simulation không đồng nghĩa live state.
10. AI recommendation không đồng nghĩa authorization.
11. Fraud signal không đồng nghĩa fraud.
12. Risk không đồng nghĩa event.
13. Finance ledger thuộc `AXFINANCE`.
14. Legal authority thuộc `AXLAW`.
15. Construction execution thuộc `AXCONSTRUCTION`.
16. Resource accounting thuộc `AXRESOURCE`.
17. Spatial data có CRS/provenance.
18. Historical state có temporal validity.
19. Cross-domain mutation có authorization.
20. AI output có model/provenance.
21. Sensitive inference bị hạn chế.
22. Housing simulation có reproducibility.
23. Digital twin phân biệt observed/estimated/predicted/simulated.
24. Core không phụ thuộc vendor.
25. Native implementation ưu tiên flat data, stable IDs, indexed relations và zero-copy.
26. Có thể chạy từ embedded/mobile/WASM tới distributed civilization-scale infrastructure.
27. Compiler có thể tối ưu housing query và simulation xuống native execution.
28. Housing domain có thể được xây dựng hoàn toàn trên Axiom mà không cần third-party compiler/runtime.

---

# 133. Trạng thái hoàn thành

```text
BOOTSTRAP-689
STATUS: COMPLETE

DOMAIN:
AXHOUSING

PRIMARY CAPABILITIES:
property
land
dwelling
building
household
occupancy
ownership_ref
rental
lease
sale
mortgage_ref
valuation
housing_inventory
housing_market
affordability
urban_housing
spatial
maintenance
smart_building
housing_ai
housing_simulation
digital_twin
disaster_housing
distributed_housing

TEST TARGET:
≥ 12,000 automated tests
≥ 1,000 architecture invariants
```

---

# 134. Chuỗi kiến trúc sau BOOTSTRAP-689

Các lớp civilization-scale physical/economic hiện đã tiến tới:

```text
AXRESOURCE
AXAGRI
AXMANUFACTURING
AXCONSTRUCTION
AXHOUSING
AXTRANSPORT
AXCOMMERCE
AXLABOR
AXFINANCE
AXLAW
AXGOV
```

Lớp tiếp theo cần xử lý một domain rất lớn còn thiếu trong chuỗi kinh tế-xã hội:

**BOOTSTRAP-690 — Native AI Civilization-Scale Banking, Credit, Lending, Payments, Monetary Accounts, Financial Institutions, Capital Markets & Financial Infrastructure Runtime 5.0**

Nó sẽ tiếp tục tách `AXFINANCE` thành hạ tầng tài chính native đủ sâu để các lớp `AXHOUSING`, `AXCOMMERCE`, `AXLABOR`, `AXMANUFACTURING`, `AXTRANSPORT` và các hệ thống civilization-scale có thể sử dụng mà không biến từng domain thành một financial runtime riêng.
:::

Đã hoàn tất **BOOTSTRAP-689** và chuyển chuỗi kiến trúc sang **BOOTSTRAP-690**.