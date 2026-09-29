# BOOTSTRAP-718 — AXCONSTRUCTION

**Namespace:** `AXCONSTRUCTION`  
**Phase:** Axiom Civilization Runtime / Construction & Built-Environment Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXLAW`, `AXIDENTITY`, `AXCIVIL`, `AXGOV`, `AXFINANCE`, `AXENVIRONMENT`, `AXENERGY`, `AXWATER`, `AXTRANSPORT`, `AXLOGISTICS`, `AXMANUFACTURING`

---

# 718.0 — Mục tiêu

`AXCONSTRUCTION` là runtime native quản lý vòng đời xây dựng từ:

```text
Concept
  ↓
Site
  ↓
Design
  ↓
Planning
  ↓
Permit
  ↓
Procurement
  ↓
Construction
  ↓
Inspection
  ↓
Commissioning
  ↓
Handover
  ↓
Operation / Asset
```

Phạm vi:

```text
building construction
civil engineering
roads
bridges
tunnels
dams
industrial facilities
utilities
residential projects
commercial projects
public infrastructure
site management
BIM
structural models
MEP
materials
contractors
subcontractors
work packages
construction schedules
progress tracking
quality inspection
safety management
change orders
defects
commissioning
handover
construction digital twin
```

Mục tiêu quan trọng:

> `AXCONSTRUCTION` quản lý **construction state**, không trở thành hệ thống thay thế CAD/BIM chuyên dụng, GIS, finance, transport, energy hay water.

---

# 718.1 — Boundary Architecture

```text
                         AXCONSTRUCTION
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
       DESIGN                 PROJECT               SITE
          │                     │                     │
      BIM Model            Schedule              Site State
      Structure             Budget Ref            Work
      MEP                    Contracts             Safety
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                         CONSTRUCTION
                                │
       ┌────────────────────────┼────────────────────────┐
       │                        │                        │
   MATERIALS                 QUALITY                  SAFETY
       │                        │                        │
 AXMANUFACTURING          Inspection              Incidents
 AXLOGISTICS              Defects                 Controls
```

---

# 718.2 — Strong Domain Boundaries

### AXCONSTRUCTION sở hữu

```text
construction project
site
building/structure definition
BIM construction semantics
work packages
construction schedule
construction progress
construction inspection
construction defects
site activities
contractor execution state
handover state
commissioning state
```

### AXGOV sở hữu

```text
permit authority
administrative approval
inspection authority
legal administrative decisions
```

### AXLAW sở hữu

```text
building regulations
legal requirements
standards references
contract law
safety rules
```

### AXFINANCE sở hữu

```text
money
payments
financial ledger
actual project accounting
```

### AXMANUFACTURING sở hữu

```text
manufactured components
factory production
production lots
manufacturing genealogy
```

### AXLOGISTICS sở hữu

```text
warehouse
shipment
freight
physical logistics execution
```

### AXTRANSPORT sở hữu

```text
vehicles
transport routes
transport execution
```

### AXENERGY sở hữu

```text
electrical grid
generation
energy network state
```

### AXWATER sở hữu

```text
water network
water resources
water distribution
wastewater
```

### AXENVIRONMENT sở hữu

```text
environmental observations
emissions
environmental monitoring
```

---

# 718.3 — Fundamental Distinctions

```text
project
    ≠
building

design
    ≠
as-built state

BIM model
    ≠
physical structure

planned quantity
    ≠
installed quantity

work package
    ≠
actual work

schedule
    ≠
progress

inspection observation
    ≠
approval

defect
    ≠
legal violation

permit application
    ≠
permit approval

contract
    ≠
payment

cost estimate
    ≠
financial ledger

material order
    ≠
material delivery

material delivery
    ≠
material installation

construction completion
    ≠
commissioning

commissioning
    ≠
legal occupancy approval

AI prediction
    ≠
construction fact
```

---

# 718.4 — Construction Project

```axiom
construction_project {
    project_id
    name
    project_type
    owner_reference
    location_reference
    lifecycle_state
    planned_start
    planned_end
}
```

Project types:

```text
building
road
bridge
tunnel
dam
rail
airport
industrial
utility
public_infrastructure
renovation
demolition
```

---

# 718.5 — Project Phase

```axiom
construction_phase {
    phase_id
    project
    name
    sequence
    start
    end
    status
}
```

Default lifecycle:

```text
CONCEPT
DESIGN
APPROVAL
PROCUREMENT
CONSTRUCTION
COMMISSIONING
HANDOVER
CLOSED
```

---

# 718.6 — Construction Site

```axiom
construction_site {
    site_id
    project
    location_reference
    boundaries
    access_rules
    safety_state
    status
}
```

---

# 718.7 — Site Zone

```axiom
construction_zone {
    zone_id
    site
    geometry
    type
    access_policy
    hazards
}
```

Ví dụ:

```text
excavation_zone
lifting_zone
storage_zone
restricted_zone
worker_zone
vehicle_zone
temporary_structure_zone
```

---

# 718.8 — Built Asset Definition

```axiom
built_asset {
    asset_id
    project
    type
    design_reference
    lifecycle_state
}
```

Ví dụ:

```text
building
floor
room
bridge
road_segment
tunnel
pipe
foundation
structural_frame
```

---

# 718.9 — Structure

```axiom
construction_structure {
    structure_id
    asset
    structural_type
    materials
    geometry_reference
    engineering_reference
}
```

---

# 718.10 — Building

```axiom
building {
    building_id
    project
    floors
    spaces
    structural_system
    envelope
    systems
}
```

---

# 718.11 — Building Space

```axiom
building_space {
    space_id
    building
    level
    geometry_reference
    function
    occupancy_class
}
```

---

# 718.12 — BIM Model

```axiom
bim_model {
    model_id
    project
    version
    discipline
    coordinate_reference
    elements
    metadata
}
```

BIM là **structured project model**, không nhất thiết là một renderer.

---

# 718.13 — BIM Element

```axiom
bim_element {
    element_id
    model
    type
    geometry
    properties
    material_reference
    system_reference
}
```

---

# 718.14 — BIM Revision

```axiom
bim_revision {
    model
    revision
    created_at
    author_reference
    change_set
    status
}
```

Revision được immutable khi đã trở thành cơ sở của execution record.

---

# 718.15 — As-Built Model

```axiom
as_built_model {
    project
    source_design
    installed_elements
    deviations
    verified_at
    verification_reference
}
```

Điểm quan trọng:

```text
design geometry
    ≠
actual geometry
```

---

# 718.16 — Construction Material

```axiom
construction_material {
    material_id
    type
    specification
    manufacturer_reference
    standard_reference
    properties
}
```

---

# 718.17 — Material Batch

```axiom
construction_material_lot {
    lot_id
    material
    supplier_reference
    production_lot_reference
    quantity
    certificates
    received_at
}
```

Có thể reference:

```text
AXMANUFACTURING
AXFOOD
AXLOGISTICS
```

nhưng không duplicate production genealogy.

---

# 718.18 — Material Delivery

```axiom
material_delivery {
    delivery_id
    project
    material_lots
    quantity
    shipment_reference
    received_at
    inspection_state
}
```

---

# 718.19 — Material Installation

```axiom
material_installation {
    installation_id
    project
    material_lot
    bim_element
    quantity
    location
    installed_at
    work_order_reference
}
```

Cho phép:

```text
trace installed component
        ↓
material lot
        ↓
supplier
        ↓
manufacturing lot
```

---

# 718.20 — Work Package

```axiom
construction_work_package {
    work_package_id
    project
    scope
    dependencies
    responsible_party
    planned_start
    planned_end
    status
}
```

---

# 718.21 — Construction Activity

```axiom
construction_activity {
    activity_id
    work_package
    type
    planned_quantity
    unit
    planned_duration
    actual_quantity
    actual_duration
    status
}
```

---

# 718.22 — Construction Work Order

```axiom
construction_work_order {
    work_order_id
    project
    work_package
    activity
    contractor_reference
    site_zone
    status
}
```

---

# 718.23 — Construction State Machine

```text
PLANNED
   ↓
AUTHORIZED
   ↓
READY
   ↓
STARTED
   ↓
IN_PROGRESS
   ↓
COMPLETED
   ↓
VERIFIED
```

Alternative:

```text
ON_HOLD
CANCELLED
REJECTED
REWORK_REQUIRED
```

---

# 718.24 — Schedule

```axiom
construction_schedule {
    schedule_id
    project
    activities
    dependencies
    resources
    milestones
    baseline
    version
}
```

---

# 718.25 — Schedule Dependency

```axiom
schedule_dependency {
    predecessor
    successor
    dependency_type
    lag
}
```

Hỗ trợ:

```text
finish_to_start
start_to_start
finish_to_finish
start_to_finish
```

---

# 718.26 — Construction Progress

```axiom
construction_progress {
    project
    activity
    planned_quantity
    actual_quantity
    completion_ratio
    measurement_method
    timestamp
}
```

`completion_ratio` không được tự động hiểu là financial payment percentage.

---

# 718.27 — Milestone

```axiom
construction_milestone {
    milestone_id
    project
    name
    planned_date
    actual_date
    evidence
    status
}
```

---

# 718.28 — Contractor

```axiom
construction_contractor_reference {
    party_reference
    project
    scope
    authorization_reference
    contract_reference
}
```

Identity của contractor thuộc `AXIDENTITY/AXCIVIL`.

---

# 718.29 — Subcontractor

```axiom
construction_subcontractor_reference {
    contractor
    party_reference
    scope
    authorization_reference
}
```

---

# 718.30 — Construction Contract Reference

```axiom
construction_contract_reference {
    project
    parties
    scope
    contract_reference
    commercial_terms_reference
}
```

AXCONSTRUCTION chỉ giữ **construction semantics** của contract.

Actual financial obligations:

```text
AXFINANCE
```

---

# 718.31 — Permit Reference

```axiom
construction_permit_reference {
    project
    permit_type
    authority_reference
    application_reference
    approval_reference
    validity
    conditions
}
```

Không tự biến `permit_application` thành `permit_approval`.

---

# 718.32 — Inspection

```axiom
construction_inspection {
    inspection_id
    project
    target
    inspector_reference
    inspection_type
    observations
    evidence
    status
}
```

---

# 718.33 — Inspection Observation

```axiom
inspection_observation {
    inspection
    parameter
    observed_value
    expected_value
    unit
    result
    evidence
}
```

---

# 718.34 — Construction Defect

```axiom
construction_defect {
    defect_id
    project
    target
    description
    severity_reference
    evidence
    discovered_at
    status
}
```

Không tự gán legal liability.

---

# 718.35 — Defect Lifecycle

```text
DETECTED
   ↓
ASSESSED
   ↓
ASSIGNED
   ↓
REPAIRING
   ↓
REPAIRED
   ↓
VERIFIED
   ↓
CLOSED
```

Có thể:

```text
REOPENED
```

---

# 718.36 — Rework

```axiom
construction_rework {
    defect
    work_order
    scope
    cause_reference
    status
}
```

---

# 718.37 — Quality Plan

```axiom
construction_quality_plan {
    project
    inspection_points
    acceptance_criteria
    sampling_rules
    evidence_requirements
}
```

---

# 718.38 — Test

```axiom
construction_test {
    test_id
    project
    target
    test_type
    procedure_reference
    result
    evidence
    performed_at
}
```

Ví dụ:

```text
concrete_strength
weld_test
pressure_test
electrical_test
waterproofing_test
load_test
```

---

# 718.39 — Safety Plan

```axiom
construction_safety_plan {
    project
    hazards
    controls
    emergency_procedures
    inspection_schedule
}
```

---

# 718.40 — Hazard

```axiom
construction_hazard {
    hazard_id
    site
    zone
    type
    risk_reference
    controls
    status
}
```

---

# 718.41 — Safety Control

```axiom
construction_safety_control {
    hazard
    control_type
    requirement
    responsible_party
    verification
    status
}
```

---

# 718.42 — Safety Incident

```axiom
construction_safety_incident {
    incident_id
    project
    site
    timestamp
    observation
    evidence
    response
    status
}
```

Không tự kết luận trách nhiệm pháp lý.

---

# 718.43 — Equipment

```axiom
construction_equipment {
    equipment_id
    type
    capabilities
    site
    status
    transport_reference
}
```

Ví dụ:

```text
crane
excavator
bulldozer
concrete_pump
drill
generator
lifting_equipment
```

---

# 718.44 — Equipment Allocation

```axiom
equipment_allocation {
    equipment
    project
    work_package
    start
    end
    operator_reference
}
```

---

# 718.45 — Temporary Structure

```axiom
temporary_structure {
    structure_id
    project
    type
    location
    design_reference
    inspection_state
    removal_requirement
}
```

---

# 718.46 — Utility Connection

```axiom
construction_utility_connection {
    project
    utility_type
    provider_reference
    connection_reference
    capacity
    status
}
```

Có thể reference:

```text
AXENERGY
AXWATER
AXTRANSPORT
```

---

# 718.47 — Change Order

```axiom
construction_change_order {
    change_id
    project
    affected_design
    affected_scope
    reason
    impact
    approval_reference
    status
}
```

Không sửa trực tiếp baseline.

---

# 718.48 — Design Change

```axiom
construction_design_change {
    project
    source_revision
    target_revision
    affected_elements
    change_set
    approval_reference
}
```

---

# 718.49 — Construction Baseline

```axiom
construction_baseline {
    project
    design_revision
    schedule_revision
    scope_revision
    material_plan
    created_at
}
```

Baseline immutable.

---

# 718.50 — Quantity Measurement

```axiom
construction_quantity_measurement {
    activity
    quantity
    unit
    location
    method
    evidence
    timestamp
}
```

Ví dụ:

```text
m3 concrete
m2 wall
m road
ton steel
```

---

# 718.51 — Cost Estimate Reference

```axiom
construction_cost_estimate {
    project
    quantity_reference
    rate_reference
    currency
    estimate_version
}
```

Đây là **estimate**, không phải ledger.

---

# 718.52 — Payment Progress Reference

```axiom
construction_payment_reference {
    project
    milestone
    amount_reference
    financial_transaction_reference
}
```

Actual payment:

```text
AXFINANCE
```

---

# 718.53 — Commissioning

```axiom
commissioning_plan {
    project
    systems
    tests
    acceptance_criteria
    sequence
}
```

---

# 718.54 — Commissioning Test

```axiom
commissioning_test {
    plan
    system
    procedure
    result
    evidence
    status
}
```

---

# 718.55 — System Handover

```axiom
construction_handover {
    project
    asset
    as_built_model
    manuals
    certificates
    commissioning_results
    defects
    handover_date
    status
}
```

---

# 718.56 — Handover Boundary

Sau handover:

```text
AXCONSTRUCTION
       ↓
built asset
       ↓
future AXASSET / facility runtime
```

Không biến construction project thành permanent operational asset state.

---

# 718.57 — Construction Digital Twin

```axiom
construction_digital_twin {
    project_snapshot
    bim_model
    site_state
    schedule
    progress
    equipment
    materials
    environmental_references
    timestamp
    model_version
}
```

Có thể:

```text
simulate_construction()
simulate_schedule()
simulate_site()
simulate_material_flow()
simulate_crane_operations()
simulate_progress()
simulate_design_change()
```

---

# 718.58 — Digital Twin Rule

```text
digital_twin
    ≠
physical_site
```

Twin phải luôn lưu:

```text
snapshot
timestamp
model_version
assumptions
source_references
```

---

# 718.59 — BIM + AI

AI có thể hỗ trợ:

```text
BIM element classification
design clash detection
schedule optimization
progress estimation
site image analysis
material quantity estimation
defect detection
safety hazard detection
construction delay analysis
resource optimization
cost anomaly detection
quality anomaly detection
digital twin forecasting
```

---

# 718.60 — AI Boundary

AI không được tự động:

```text
approve construction permit
approve structural safety
declare building legally compliant
authorize unsafe work
change engineering design
approve change order
certify construction completion
release financial payment
declare legal liability
```

AI output:

```text
prediction
classification
recommendation
anomaly
candidate finding
```

phải được phân biệt với authoritative state.

---

# 718.61 — Site Computer Vision

```axiom
construction_visual_observation {
    camera_reference
    site_zone
    timestamp
    detected_objects
    measurements
    confidence
    model_version
}
```

Ví dụ:

```text
helmet detection
vehicle detection
progress estimation
material detection
structural element detection
site occupancy
```

Computer vision result không tự trở thành incident hoặc violation.

---

# 718.62 — IoT / Sensor Integration

```axiom
construction_sensor {
    sensor_id
    type
    location
    parameter
    unit
    calibration_reference
}
```

Telemetry:

```axiom
construction_telemetry {
    sensor
    value
    unit
    timestamp
    quality
}
```

---

# 718.63 — Environmental Construction State

Reference:

```text
noise
dust
temperature
rain
wind
vibration
water
emissions
```

Canonical environmental state thuộc `AXENVIRONMENT`.

---

# 718.64 — Weather Constraint

```axiom
construction_weather_constraint {
    project
    activity
    weather_parameter
    threshold
    source_reference
    validity
}
```

Ví dụ:

```text
crane operation
concrete pouring
roof installation
excavation
```

---

# 718.65 — Offline Construction Site

```text
Sensors / Devices
       ↓
Site Edge Node
       ↓
Local Event Log
       ↓
Local Construction State
       ↓
Network Sync
       ↓
AXCONSTRUCTION
```

Site không được phụ thuộc hoàn toàn vào cloud để thực hiện các operation cần hoạt động cục bộ.

---

# 718.66 — Event Model

```text
CONSTRUCTION_PROJECT_CREATED
CONSTRUCTION_PHASE_CREATED
CONSTRUCTION_SITE_CREATED
CONSTRUCTION_ZONE_CREATED

BUILT_ASSET_CREATED
BUILDING_CREATED
SPACE_CREATED
STRUCTURE_CREATED

BIM_MODEL_CREATED
BIM_MODEL_VERSIONED
BIM_ELEMENT_CREATED
AS_BUILT_MODEL_CREATED

MATERIAL_REGISTERED
MATERIAL_LOT_REGISTERED
MATERIAL_DELIVERED
MATERIAL_INSPECTED
MATERIAL_INSTALLED

WORK_PACKAGE_CREATED
CONSTRUCTION_ACTIVITY_CREATED
CONSTRUCTION_WORK_ORDER_CREATED
WORK_ORDER_AUTHORIZED
WORK_ORDER_STARTED
WORK_ORDER_COMPLETED

SCHEDULE_CREATED
SCHEDULE_VERSIONED
MILESTONE_CREATED
PROGRESS_RECORDED

CONTRACTOR_ASSIGNED
EQUIPMENT_REGISTERED
EQUIPMENT_ALLOCATED

INSPECTION_CREATED
INSPECTION_OBSERVATION_RECORDED
QUALITY_TEST_RECORDED

DEFECT_CREATED
REWORK_CREATED
DEFECT_REPAIRED
DEFECT_VERIFIED
DEFECT_CLOSED

SAFETY_PLAN_CREATED
HAZARD_CREATED
SAFETY_CONTROL_CREATED
SAFETY_INCIDENT_CREATED

PERMIT_REFERENCED
DESIGN_CHANGE_CREATED
CHANGE_ORDER_CREATED
BASELINE_CREATED

QUANTITY_MEASURED
COST_ESTIMATE_CREATED
PAYMENT_REFERENCE_CREATED

COMMISSIONING_PLAN_CREATED
COMMISSIONING_TEST_RECORDED

HANDOVER_CREATED
HANDOVER_COMPLETED

SENSOR_REGISTERED
CONSTRUCTION_TELEMETRY_RECORDED
VISUAL_OBSERVATION_CREATED

AI_CONSTRUCTION_ANALYSIS_CREATED
CONSTRUCTION_SIMULATION_CREATED
DIGITAL_TWIN_CREATED
```

---

# 718.67 — Native APIs

```axiom
create_construction_project()
create_construction_phase()
create_construction_site()
create_construction_zone()

create_built_asset()
create_building()
create_building_space()
create_structure()

create_bim_model()
version_bim_model()
create_bim_element()
create_as_built_model()

create_construction_material()
register_material_lot()
record_material_delivery()
inspect_material()
record_material_installation()

create_work_package()
create_construction_activity()
create_construction_work_order()
authorize_work_order()
start_work_order()
pause_work_order()
resume_work_order()
complete_work_order()
cancel_work_order()

create_schedule()
version_schedule()
create_milestone()
record_progress()
measure_quantity()

register_contractor()
assign_contractor()
register_equipment()
allocate_equipment()

create_inspection()
record_inspection_observation()
create_quality_test()

create_defect()
create_rework()
repair_defect()
verify_defect()
close_defect()

create_safety_plan()
create_hazard()
create_safety_control()
record_safety_incident()

reference_permit()

create_design_change()
create_change_order()
create_baseline()

create_cost_estimate()
create_payment_reference()

create_commissioning_plan()
record_commissioning_test()

create_handover()

register_sensor()
ingest_construction_telemetry()
create_visual_observation()

trace_installed_material()
trace_built_element()
trace_project_history()

create_construction_digital_twin()

simulate_construction()
simulate_schedule()
simulate_site()
simulate_material_flow()
simulate_progress()
simulate_design_change()

reconcile_construction_state()
replay_construction_state()
```

---

# 718.68 — Canonical Project Flow

```text
Project
  ↓
Site
  ↓
Design
  ↓
BIM
  ↓
Baseline
  ↓
Permit Reference
  ↓
Procurement
  ↓
Material Delivery
  ↓
Work Packages
  ↓
Schedule
  ↓
Construction
  ↓
Inspection
  ↓
Progress
  ↓
Commissioning
  ↓
As-Built
  ↓
Handover
```

---

# 718.69 — Canonical Design Change

```text
Existing Design
      ↓
Change Proposal
      ↓
Impact Analysis
      ↓
Design Revision
      ↓
Approval Reference
      ↓
New Baseline
      ↓
Construction Execution
```

Historical construction records vẫn reference revision cũ.

---

# 718.70 — Canonical Defect Flow

```text
Observation
    ↓
Defect
    ↓
Assessment
    ↓
Work Assignment
    ↓
Repair
    ↓
Inspection
    ↓
Verified
    ↓
Closed
```

---

# 718.71 — Canonical Material Traceability

```text
Manufacturer Lot
       ↓
Material Lot
       ↓
Delivery
       ↓
Site Storage
       ↓
Installation
       ↓
BIM Element
       ↓
As-Built Asset
```

Cho phép reverse tracing.

---

# 718.72 — Security Capabilities

```text
construction.read
construction.write

construction.project.read
construction.project.manage

construction.design.read
construction.design.manage

construction.bim.read
construction.bim.manage

construction.material.read
construction.material.manage

construction.schedule.read
construction.schedule.manage

construction.workorder.read
construction.workorder.execute
construction.workorder.manage

construction.inspection.read
construction.inspection.manage

construction.quality.read
construction.quality.manage

construction.safety.read
construction.safety.manage

construction.change.manage
construction.handover.manage

construction.equipment.read
construction.equipment.manage

construction.sensor.read
construction.sensor.manage

construction.ai.execute
construction.simulation.execute
construction.digitaltwin.execute

construction.admin
```

---

# 718.73 — Critical Authorization

Các operation nhạy cảm:

```text
authorize_work_order()
approve_design_change()
approve_change_order()
release_quality_hold()
accept_commissioning()
complete_handover()
```

phải yêu cầu capability tương ứng.

AI không được bypass authorization.

---

# 718.74 — Event-Sourced State

Authoritative state:

```text
Project
Site
Work Package
Work Order
Material Installation
Inspection
Defect
Progress
Commissioning
Handover
```

đều phải có event lineage.

Derived state có thể rebuild:

```text
schedule_progress
completion_ratio
resource_utilization
site_statistics
AI_predictions
digital_twin
```

---

# 718.75 — Reconciliation

Hệ thống phải phát hiện:

```text
planned quantity ≠ actual quantity
BIM design ≠ as-built
schedule ≠ observed progress
material delivered ≠ material installed
inspection ≠ release state
sensor state ≠ declared state
```

Reconciliation tạo:

```text
discrepancy
evidence
resolution
```

Không silently overwrite.

---

# 718.76 — Formal Invariants

```text
CON-INV-01   Project is distinct from built asset.
CON-INV-02   Design is distinct from as-built state.
CON-INV-03   BIM model is distinct from physical structure.
CON-INV-04   BIM revisions are immutable once referenced by execution.
CON-INV-05   Construction baseline is immutable.
CON-INV-06   Work package is distinct from actual work.
CON-INV-07   Schedule is distinct from progress.
CON-INV-08   Planned quantity is distinct from actual quantity.
CON-INV-09   Material delivery is distinct from installation.
CON-INV-10   Material installation preserves lot lineage.

CON-INV-11   Construction work order has explicit project scope.
CON-INV-12   Work-order transitions are policy validated.
CON-INV-13   Progress records preserve measurement evidence.
CON-INV-14   Inspection is distinct from approval.
CON-INV-15   Inspection observation preserves source evidence.
CON-INV-16   Defect is distinct from legal violation.
CON-INV-17   Rework preserves defect lineage.
CON-INV-18   Quality tests preserve procedure references.
CON-INV-19   Safety incident does not automatically imply legal liability.
CON-INV-20   Safety controls cannot be silently bypassed.

CON-INV-21   Permit application is distinct from permit approval.
CON-INV-22   Design change does not mutate historical revision.
CON-INV-23   Change order preserves affected scope.
CON-INV-24   Financial ledger belongs to AXFINANCE.
CON-INV-25   Payment reference does not constitute payment settlement.
CON-INV-26   Material manufacturing state belongs to AXMANUFACTURING.
CON-INV-27   Shipment execution belongs to AXLOGISTICS.
CON-INV-28   Transport execution belongs to AXTRANSPORT.
CON-INV-29   Energy state belongs to AXENERGY.
CON-INV-30   Water state belongs to AXWATER.

CON-INV-31   Environmental state belongs to AXENVIRONMENT.
CON-INV-32   AI output is derived.
CON-INV-33   AI cannot authorize construction activity.
CON-INV-34   AI cannot approve structural compliance.
CON-INV-35   AI cannot bypass safety controls.
CON-INV-36   Simulation cannot mutate authoritative state.
CON-INV-37   Digital twin cannot become source of truth.
CON-INV-38   Offline events preserve causal ordering.
CON-INV-39   Reconciliation never silently destroys history.
CON-INV-40   Replay reconstructs construction state deterministically.
```

---

# 718.77 — Property Tests

```text
version_bim_model()
    preserves historical revisions

create_baseline()
    freezes referenced revisions

record_material_installation()
    preserves material-lot lineage

record_progress()
    preserves measurement evidence

complete_work_order()
    cannot exceed authorized scope without explicit change

create_defect()
    preserves inspection evidence

repair_defect()
    preserves original defect

close_defect()
    requires verification when policy requires

create_design_change()
    does not mutate historical design

create_change_order()
    preserves affected elements

complete_commissioning()
    requires required tests

create_handover()
    preserves as-built references

offline_sync()
    does not duplicate construction events

simulation()
    never mutates authoritative project state

replay_project()
    reconstructs project history
```

---

# 718.78 — Test Matrix

```text
project_tests
phase_tests
site_tests
zone_tests

building_tests
structure_tests
space_tests

bim_tests
bim_revision_tests
as_built_tests

material_tests
material_lot_tests
delivery_tests
installation_tests
traceability_tests

work_package_tests
activity_tests
work_order_tests

schedule_tests
dependency_tests
milestone_tests
progress_tests
quantity_tests

contractor_tests
subcontractor_tests

equipment_tests
allocation_tests

inspection_tests
quality_test_tests
defect_tests
rework_tests

safety_tests
hazard_tests
control_tests
incident_tests

permit_reference_tests
design_change_tests
change_order_tests
baseline_tests

cost_estimate_tests
payment_reference_tests

commissioning_tests
handover_tests

sensor_tests
telemetry_tests
computer_vision_tests

energy_integration_tests
water_integration_tests
environment_integration_tests
manufacturing_integration_tests
logistics_integration_tests
transport_integration_tests

offline_tests
distributed_tests
reconciliation_tests

AI_boundary_tests
authorization_tests
security_tests
privacy_tests

audit_tests
replay_tests
simulation_tests
digital_twin_tests
```

---

# 718.79 — Completion Criteria

`BOOTSTRAP-718` phải freeze đầy đủ:

1. Construction project.
2. Project phase.
3. Site.
4. Site zones.
5. Built assets.
6. Buildings.
7. Spaces.
8. Structures.
9. BIM model.
10. BIM element.
11. BIM revision.
12. As-built model.
13. Construction materials.
14. Material lots.
15. Material delivery.
16. Material installation.
17. Work packages.
18. Activities.
19. Work orders.
20. Schedule.
21. Dependencies.
22. Milestones.
23. Progress.
24. Contractors.
25. Equipment.
26. Inspections.
27. Quality tests.
28. Defects.
29. Rework.
30. Safety plans.
31. Hazards.
32. Safety controls.
33. Safety incidents.
34. Permit references.
35. Design changes.
36. Change orders.
37. Baselines.
38. Quantity measurement.
39. Cost references.
40. Payment references.
41. Commissioning.
42. Handover.
43. Sensor telemetry.
44. Computer vision observations.
45. Offline edge.
46. Digital twin.
47. AI boundary.
48. Security.
49. Privacy.
50. Audit/replay.
51. Reconciliation.
52. Simulation.
53. Formal invariants.
54. Property tests.
55. Integration tests.

---

# 718.80 — Definition of Done

```text
BOOTSTRAP-718
STATUS: COMPLETE / FROZEN

AXCONSTRUCTION 5.0
    ├── Project
    ├── Site
    ├── Built Assets
    ├── Buildings
    ├── Structures
    ├── BIM
    ├── As-Built
    ├── Materials
    ├── Material Traceability
    ├── Work Packages
    ├── Work Orders
    ├── Scheduling
    ├── Progress
    ├── Contractors
    ├── Equipment
    ├── Inspection
    ├── Quality
    ├── Defects
    ├── Rework
    ├── Safety
    ├── Permits
    ├── Design Changes
    ├── Change Orders
    ├── Cost References
    ├── Commissioning
    ├── Handover
    ├── Sensors
    ├── Computer Vision
    ├── Offline Edge
    ├── AI
    ├── Digital Twin
    ├── Reconciliation
    ├── Audit
    ├── Replay
    └── Simulation
```

**BOOTSTRAP-718 / AXCONSTRUCTION — ARCHITECTURAL BASELINE FROZEN.**

---

## BOOTSTRAP-719 — AXASSET

**Native Physical Asset Registry, Equipment Lifecycle, Ownership, Custody, Installation, Maintenance, Calibration, Condition, Depreciation References, Warranty, Service History, Asset Genealogy, Asset Graph, Digital Twin & Asset Lifecycle Runtime 5.0.**