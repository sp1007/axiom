Tiếp tục với **BOOTSTRAP-688** — xây lớp lao động và việc làm nối `AXEDUCATION → AXLABOR → AXENTERPRISE → AXCOMMERCE → AXFINANCE`, đồng thời giữ tách biệt **con người, kỹ năng, công việc, hợp đồng, năng suất, thu nhập và đánh giá AI**.

:::writing{variant="document" id="31648" title="BOOTSTRAP-688 — Native AI Civilization-Scale Labor, Employment, Workforce, Jobs, Skills, Human Capital, Enterprise Work & Global Labor-Market Runtime 5.0"}
# BOOTSTRAP-688
## Native AI Civilization-Scale Labor, Employment, Workforce, Jobs, Skills, Human Capital, Enterprise Work & Global Labor-Market Runtime 5.0

**Layer:** Labor / Employment / Workforce / Jobs / Skills / Human Capital / Enterprise Work / Labor Market  
**Target:** Axiom 5.0  
**Status:** Architecture Specification

---

# 1. Mục tiêu

`AXLABOR` là native runtime của Axiom cho toàn bộ hệ thống:

- người lao động;
- nghề nghiệp;
- vị trí công việc;
- job;
- vacancy;
- recruitment;
- candidate;
- skill;
- competency;
- qualification;
- certification reference;
- training;
- career;
- employment;
- work schedule;
- shift;
- attendance;
- timesheet;
- payroll reference;
- compensation;
- benefits;
- leave;
- performance;
- workforce planning;
- labor supply;
- labor demand;
- labor market;
- human capital;
- enterprise work;
- contractor;
- freelancer;
- gig work;
- remote work;
- AI-assisted work;
- workforce simulation;
- labor-market digital twin.

Mục tiêu:

```text
AXEDUCATION
      ↓
SKILL / QUALIFICATION
      ↓
AXLABOR
      ↓
EMPLOYMENT / WORK
      ↓
AXCOMMERCE
      ↓
AXFINANCE
```

---

# 2. Nguyên tắc nền tảng

AXLABOR phải phân biệt:

```text
Person
≠ Worker
≠ Candidate
≠ Employee
≠ Contractor
≠ Job
≠ Position
≠ Employment
≠ Skill
≠ Qualification
≠ Certification
≠ Experience
≠ Performance
≠ Compensation
≠ Payroll
```

Đây là invariant nền tảng.

---

# 3. Human Boundary

AXLABOR không trở thành hệ thống authoritative về toàn bộ danh tính con người.

Dùng:

```text
PersonRef
IdentityRef
ConsentRef
```

Identity authority thuộc identity/security/government layer phù hợp.

---

# 4. Person ≠ Worker

Một `Person` có thể:

```text
student
worker
employer
founder
volunteer
contractor
job seeker
```

tùy context.

---

# 5. Worker

```text
Worker {
    worker_id
    person_ref
    worker_type
    skills[]
    qualifications[]
}
```

---

# 6. Worker Types

```text
Employee
Contractor
Freelancer
TemporaryWorker
Intern
Apprentice
Volunteer
GigWorker
SelfEmployed
```

Legal classification phải có `ClassificationRef`, không được hard-code một jurisdiction.

---

# 7. Employer

```text
Employer {
    employer_id
    organization_ref
    workforce[]
    jobs[]
}
```

Organization semantics thuộc organization/governance layer.

---

# 8. Job

`Job` là loại công việc hoặc mô tả nhu cầu lao động.

```text
Job {
    job_id
    title
    description
    skills[]
    responsibilities[]
    work_conditions
}
```

---

# 9. Position

`Position` là một slot công việc cụ thể.

```text
Position {
    position_id
    job_ref
    organization_ref
    location
    schedule
    status
}
```

Một Job có thể có nhiều Position.

---

# 10. Vacancy

```text
Vacancy {
    vacancy_id
    position_ref
    openings
    requirements
    compensation_reference
    validity
}
```

---

# 11. Candidate

```text
Candidate {
    candidate_id
    person_ref
    profile_ref
    applications[]
}
```

Candidate không đồng nghĩa với Employee.

---

# 12. Application

```text
JobApplication {
    application_id
    candidate
    vacancy
    submitted_at
    status
}
```

Lifecycle:

```text
Draft
→ Submitted
→ Screening
→ Interview
→ Assessment
→ Offer
→ Accepted
→ Rejected
→ Withdrawn
```

---

# 13. Recruitment Pipeline

```text
Vacancy
 ↓
Candidate Discovery
 ↓
Application
 ↓
Screening
 ↓
Interview
 ↓
Assessment
 ↓
Offer
 ↓
Employment
```

---

# 14. Skill

```text
Skill {
    skill_id
    name
    category
    description
}
```

---

# 15. Skill Taxonomy

Có thể tổ chức:

```text
Skill
├── Technical
├── Domain
├── Language
├── Creative
├── Operational
├── Management
├── Social
└── Cognitive
```

Taxonomy có version.

---

# 16. Skill Level

```text
SkillLevel {
    skill
    level
    evidence[]
    assessed_at
}
```

Không coi level là thuộc tính bất biến của con người.

---

# 17. Competency

```text
Competency {
    competency_id
    skills[]
    behaviors[]
    evidence[]
}
```

Competency có thể được xác định theo nghề nghiệp hoặc organization.

---

# 18. Qualification

```text
Qualification {
    qualification_id
    issuer_ref
    requirements
    validity
}
```

---

# 19. Certification

```text
Certification {
    certification_id
    issuer_ref
    qualification_ref
    issue_date
    expiry_date
}
```

Certification authority là issuer.

---

# 20. Credential

Có thể reference:

```text
CredentialRef
DigitalCredential
EducationCredential
ProfessionalCredential
LicenseRef
```

AXEDUCATION hoặc AXLAW/AXGOV có thể là authority tùy loại.

---

# 21. Skill Evidence

Skill không nên chỉ là self-declared label.

```text
SkillEvidence {
    type
    source
    timestamp
    artifact_ref
    verification
}
```

Ví dụ:

```text
CourseCompletion
Project
Exam
Certification
EmployerAssessment
Portfolio
WorkExperience
```

---

# 22. Experience

```text
WorkExperience {
    organization
    role
    start
    end
    responsibilities[]
    evidence[]
}
```

Experience ≠ skill tự động.

---

# 23. Career Profile

```text
CareerProfile {
    skills[]
    qualifications[]
    experience[]
    preferences[]
    availability
}
```

---

# 24. Employment

```text
Employment {
    employment_id
    worker
    employer
    position
    agreement_ref
    start_date
    end_date
    status
}
```

---

# 25. Employment Lifecycle

```text
Proposed
→ Offered
→ Accepted
→ Active
→ Suspended
→ Ended
```

---

# 26. Employment ≠ Contract

Employment references:

```text
EmploymentAgreementRef
```

Contract legal semantics thuộc AXLAW.

---

# 27. Employment Agreement

Có thể reference:

```text
role
schedule
compensation
benefits
location
duration
termination_rules
```

nhưng legal authority không nằm trong AXLABOR.

---

# 28. Work Assignment

```text
WorkAssignment {
    assignment_id
    worker
    task
    start
    end
    priority
}
```

---

# 29. Task

```text
WorkTask {
    task_id
    description
    required_skills[]
    dependencies[]
    status
}
```

---

# 30. Work Graph

```text
TaskA
 ↓
TaskB ──→ TaskD
 ↓
TaskC
```

Hỗ trợ DAG scheduling.

---

# 31. Project Work

```text
WorkProject {
    project_id
    tasks[]
    workers[]
    milestones[]
    resources[]
}
```

Project management có thể liên kết AX629/AX630.

---

# 32. Team

```text
Team {
    team_id
    members[]
    roles[]
    responsibilities[]
}
```

Team membership ≠ employment status.

---

# 33. Role

```text
WorkRole {
    role_id
    permissions[]
    responsibilities[]
    required_skills[]
}
```

---

# 34. Shift

```text
Shift {
    shift_id
    start
    end
    location
    role
}
```

---

# 35. Schedule

```text
WorkSchedule {
    worker
    assignments[]
    shifts[]
    availability
}
```

---

# 36. Availability

```text
AvailabilityWindow {
    start
    end
    location
    work_type
}
```

Availability ≠ willingness to accept every assignment.

---

# 37. Attendance

```text
AttendanceEvent {
    worker
    timestamp
    type
    source
}
```

Types:

```text
ClockIn
ClockOut
BreakStart
BreakEnd
RemoteStart
RemoteEnd
```

---

# 38. Timesheet

```text
Timesheet {
    worker
    period
    work_entries[]
    approval_status
}
```

---

# 39. Time Entry

```text
TimeEntry {
    task
    start
    end
    duration
    source
}
```

Duration phải có unit-safe representation.

---

# 40. Overtime

```text
OvertimeRecord {
    worker
    period
    hours
    authorization_ref
}
```

Legal overtime rules thuộc jurisdiction-specific labor law.

---

# 41. Leave

```text
LeaveRequest {
    worker
    leave_type
    start
    end
    status
}
```

---

# 42. Leave Types

```text
Vacation
SickLeaveRef
ParentalLeaveRef
PersonalLeave
TrainingLeave
UnpaidLeave
```

Actual legal categories phải được policy layer xác định.

---

# 43. Compensation

```text
Compensation {
    base
    variable
    bonus
    allowance[]
    currency
    period
}
```

Compensation không tự động đồng nghĩa với payroll settlement.

---

# 44. Compensation Plan

```text
CompensationPlan {
    worker
    base
    incentives
    effective_date
    version
}
```

---

# 45. Payroll Boundary

AXLABOR tạo:

```text
PayrollInput
WorkHours
CompensationReference
LeaveReference
```

AXFINANCE xử lý authoritative:

```text
PayrollPayment
Ledger
Tax
Settlement
```

---

# 46. Payroll Input

```text
PayrollInput {
    worker
    period
    approved_hours
    compensation
    deductions_reference
}
```

---

# 47. Benefits

```text
Benefit {
    benefit_id
    type
    eligibility
    value_reference
}
```

---

# 48. Benefit Types

```text
Health
Retirement
Insurance
Transport
Meal
Housing
Education
Leave
```

Các semantics chuyên biệt có thể link AX674, AXFINANCE, AXEDUCATION.

---

# 49. Performance

Performance phải phân biệt:

```text
ObservedOutput
Target
Evaluation
Feedback
Prediction
```

---

# 50. Performance Record

```text
PerformanceRecord {
    worker
    period
    objectives[]
    outcomes[]
    evidence[]
    evaluator_ref
}
```

---

# 51. Performance ≠ Human Worth

Không cho phép runtime suy luận:

```text
performance_score
→ human_value
```

Performance là contextual operational measurement.

---

# 52. Productivity

```text
ProductivityMetric {
    output
    input
    period
    unit
    context
}
```

Không so sánh metric giữa hai context nếu units/conditions không tương thích.

---

# 53. Performance Target

```text
PerformanceTarget {
    metric
    target
    period
    conditions
}
```

Target ≠ observed outcome.

---

# 54. Feedback

```text
Feedback {
    source
    subject
    text
    structured_signals[]
    timestamp
}
```

---

# 55. Performance Review

```text
PerformanceReview {
    worker
    period
    evidence[]
    goals[]
    feedback[]
    result
}
```

---

# 56. Skill Gap

```text
SkillGap {
    worker
    required_skill
    current_level
    target_level
    evidence
}
```

---

# 57. Learning Plan

AXLABOR có thể tạo:

```text
LearningPlan {
    worker
    skill_gaps[]
    courses[]
    target_dates[]
}
```

Training content authority thuộc AXEDUCATION.

---

# 58. Career Path

```text
CareerPath {
    current_role
    target_role
    required_skills[]
    required_experience[]
    milestones[]
}
```

Career recommendation ≠ guaranteed promotion.

---

# 59. Job Matching

```text
JobMatch {
    candidate
    vacancy
    matched_skills[]
    missing_skills[]
    compatibility
    model_reference
}
```

---

# 60. Matching Score

Score phải có context:

```text
score
model
version
features
timestamp
```

Không phải một giá trị “giá trị con người”.

---

# 61. AI Recruitment

AI có thể:

```text
parse_resume
extract_skills
find_matching_jobs
summarize_application
schedule_interview
detect_missing_requirements
```

---

# 62. Recruitment AI Boundary

AI không được mặc định:

```text
AIScore
→ AutomaticEmploymentDecision
```

nếu policy yêu cầu human/authorized decision.

---

# 63. Sensitive Attribute Boundary

Không mặc định infer từ:

```text
name
photo
language
location
behavior
```

các thuộc tính nhạy cảm để quyết định tuyển dụng.

---

# 64. Employment Recommendation

Recommendation pipeline:

```text
Candidate
 ↓
Evidence
 ↓
Matching
 ↓
Recommendation
 ↓
Authorized Review
 ↓
Decision
```

---

# 65. Labor Market

```text
LaborMarket {
    employers[]
    workers[]
    jobs[]
    skills[]
    wages[]
    regions[]
}
```

---

# 66. Labor Demand

```text
LaborDemandObservation
LaborDemandForecast
LaborDemandScenario
```

---

# 67. Labor Supply

```text
LaborSupplyObservation
LaborSupplyForecast
LaborSupplyScenario
```

---

# 68. Wage Observation

```text
WageObservation {
    occupation
    region
    period
    wage
    sample_reference
}
```

Observed wage ≠ recommended wage.

---

# 69. Wage Forecast

```text
WageForecast {
    occupation
    region
    horizon
    estimate
    uncertainty
}
```

Forecast ≠ actual wage.

---

# 70. Labor Market Equilibrium

Simulation có thể model:

```text
LaborSupply
+
LaborDemand
+
WageRule
→
SimulatedMarketState
```

Không được coi simulation là actual market truth.

---

# 71. Labor Shortage

```text
LaborGap =
Demand
-
AvailableSupply
```

phải xác định:

```text
skill
region
time
employment_type
```

---

# 72. Workforce Planning

```text
WorkforcePlan {
    horizon
    demand
    current_workforce
    skill_gaps
    hiring_plan
    training_plan
}
```

---

# 73. Hiring Plan

```text
HiringPlan {
    positions[]
    timing
    skills
    budget_reference
}
```

Financial budget thuộc AXFINANCE.

---

# 74. Workforce Optimization

Objective có thể là:

```text
minimize_skill_gap
minimize_overtime
minimize_hiring_delay
maximize_coverage
minimize_cost_reference
```

Objective phải explicit.

---

# 75. No Hidden Objective

Không tự thêm:

```text
maximize_worker_exploitation
maximize_hours
```

hoặc mục tiêu ngoài policy.

---

# 76. Work Allocation

```text
Worker
+
Skills
+
Availability
+
Tasks
+
Constraints
→
AssignmentPlan
```

---

# 77. Assignment Constraints

```text
required_skill
availability
schedule
location
capacity
qualification
safety
policy
```

---

# 78. Safety Qualification

Một task có thể yêu cầu:

```text
RequiredCertification
RequiredTraining
RequiredLicenseRef
```

Không được coi skill prediction là giấy phép pháp lý.

---

# 79. Workplace Safety Boundary

Safety-critical work có thể reference:

```text
AXLAW
AXRESOURCE
AXMANUFACTURING
AXCONSTRUCTION
AXTRANSPORT
```

---

# 80. Remote Work

```text
WorkMode {
    OnSite
    Remote
    Hybrid
    Mobile
}
```

---

# 81. Location

Không lưu precise location nếu task không cần.

```text
WorkLocationRef
RegionRef
SiteRef
```

Privacy-aware.

---

# 82. Gig Work

```text
GigAssignment {
    worker
    task
    compensation_reference
    acceptance
    completion
}
```

Legal classification không được hard-code.

---

# 83. Freelancer

```text
FreelanceEngagement {
    contractor
    client
    deliverables[]
    payment_reference
}
```

Contract authority thuộc AXLAW.

---

# 84. Contractor

Contractor ≠ Employee.

Runtime giữ explicit:

```text
WorkerClassification
```

---

# 85. Platform Work

Marketplace-style labor platform:

```text
LaborMarketplace {
    workers[]
    clients[]
    jobs[]
    assignments[]
}
```

---

# 86. Worker Profile

```text
WorkerProfile {
    skills
    experience
    availability
    portfolio_reference
    preferences
}
```

---

# 87. Worker Reputation

Có thể lưu:

```text
WorkFeedback
CompletionRate
ReliabilityMetric
ClientFeedback
```

Nhưng:

```text
metric ≠ human worth
```

---

# 88. Reputation Context

Mọi reputation metric phải có:

```text
domain
period
sample_size
method
```

---

# 89. Labor Marketplace Ranking

Ranking phải explicit:

```text
RankingPolicy {
    inputs
    objective
    constraints
    version
}
```

Không có universal worker ranking.

---

# 90. Compensation Marketplace

Có thể hỗ trợ:

```text
OfferCompensation
Bid
Proposal
Rate
ContractTermsReference
```

---

# 91. Labor Auction Boundary

Nếu có labor bidding:

```text
Bid
→ Matching
→ Contract
```

Legal constraints phải được áp dụng.

---

# 92. Enterprise Work

```text
Enterprise {
    departments[]
    teams[]
    workers[]
    jobs[]
    projects[]
    processes[]
}
```

---

# 93. Department

```text
Department {
    department_id
    parent
    roles[]
    teams[]
}
```

---

# 94. Organization Chart

```text
OrganizationGraph {
    nodes
    reporting_edges
    functional_edges
}
```

Reporting relationship ≠ ownership relationship.

---

# 95. Responsibility

```text
Responsibility {
    role
    scope
    authority
    accountability
}
```

---

# 96. Work Authority

```text
WorkCapability {
    worker
    action
    scope
}
```

Kết nối AX603 capability system.

---

# 97. Delegation

```text
Delegation {
    delegator
    delegate
    scope
    start
    expiry
}
```

Delegation phải có expiry hoặc explicit indefinite policy.

---

# 98. Approval Workflow

```text
Task
→ Worker
→ Reviewer
→ Approver
→ Completion
```

---

# 99. Work State

```text
Planned
Assigned
Accepted
Started
Blocked
Completed
Cancelled
Rejected
```

---

# 100. Dependency

```text
TaskDependency {
    predecessor
    successor
    relation
}
```

Relations:

```text
FinishToStart
StartToStart
FinishToFinish
StartToFinish
```

---

# 101. Workforce Event

```text
WorkerHired
WorkerAssigned
ShiftStarted
ShiftCompleted
LeaveApproved
SkillVerified
CertificationExpired
PromotionRecorded
CompensationChanged
EmploymentEnded
```

---

# 102. Employment History

Employment events phải append-only hoặc versioned.

Không rewrite:

```text
historical_employment
```

---

# 103. Promotion

```text
PromotionEvent {
    worker
    from_position
    to_position
    effective_time
    authority
}
```

Promotion event ≠ guaranteed career progression.

---

# 104. Transfer

```text
WorkerTransfer {
    worker
    from_team
    to_team
    effective_time
}
```

---

# 105. Termination

```text
EmploymentEnd {
    worker
    employer
    effective_time
    reason_reference
    authority
}
```

Reason semantics có thể bị giới hạn bởi privacy/legal policy.

---

# 106. Workforce Analytics

Metrics:

```text
headcount
vacancy_rate
turnover
absence
skill_coverage
training_completion
time_to_hire
time_to_fill
labor_utilization
overtime
```

Không coi metric nào là absolute judgment về con người.

---

# 107. Turnover

```text
TurnoverObservation {
    period
    population
    definition
    value
}
```

---

# 108. Workforce Forecast

```text
WorkforceForecast {
    horizon
    demand
    supply
    skill_gaps
    uncertainty
}
```

---

# 109. Human Capital

```text
HumanCapitalModel {
    skills
    experience
    qualifications
    organizational_knowledge
    learning_state
}
```

Đây là aggregate/operational model, không phải monetary valuation của con người.

---

# 110. Organizational Knowledge

```text
KnowledgeContribution {
    worker
    artifact
    project
    expertise_reference
}
```

Knowledge authority có thể liên kết AX645/AX672.

---

# 111. Institutional Memory

```text
WorkKnowledgeBase {
    procedures
    lessons
    decisions
    artifacts
}
```

---

# 112. AI Worker Assistant

Agent có thể:

```text
plan_tasks
summarize_work
search_knowledge
schedule
draft_reports
identify_skill_gaps
suggest_training
```

---

# 113. AI Supervisor Boundary

AI có thể:

```text
monitor workflow
detect bottlenecks
forecast workload
recommend assignments
```

Nhưng employment action phải qua authorized policy.

---

# 114. AI Performance Analysis

Input:

```text
observed_work
tasks
outcomes
context
```

Output:

```text
PerformanceAnalysis
```

Không tự biến thành employment decision.

---

# 115. AI Hiring Analysis

```text
Candidate
→ EvidenceExtraction
→ SkillMatch
→ RequirementMatch
→ Recommendation
```

Final employment decision phải theo declared authority.

---

# 116. Bias Monitoring

Có thể đo:

```text
SelectionRate
ErrorRate
Calibration
Consistency
```

nhưng không tự infer protected attributes nếu không có lawful/authorized basis.

---

# 117. Model Governance

Mỗi employment AI model:

```text
model_id
version
training_reference
evaluation
validation
deployment_policy
```

---

# 118. Human Override

AI recommendation phải hỗ trợ:

```text
Accept
Reject
Modify
Escalate
RequestReview
```

---

# 119. Worker Consent

Các operation có ảnh hưởng đến worker data có thể reference:

```text
ConsentRef
PolicyRef
LegalBasisRef
```

---

# 120. Data Minimization

Chỉ thu thập:

```text
data
```

cần cho:

```text
purpose
```

---

# 121. Sensitive Data

Không mặc định đưa vào matching:

```text
health
religion
political beliefs
sexual life
genetic data
```

hoặc các sensitive attributes tương tự.

---

# 122. Health Boundary

Nếu workplace health cần:

```text
HealthRecordRef
FitnessForWorkRef
AccommodationRef
```

health authority thuộc AX674.

AXLABOR không tự suy đoán tình trạng sức khỏe.

---

# 123. Education Boundary

Skill acquisition:

```text
AXEDUCATION
```

Employment application:

```text
AXLABOR
```

Credential verification:

```text
AXEDUCATION / issuer
```

---

# 124. Finance Boundary

Compensation:

```text
AXLABOR
```

Payment:

```text
AXFINANCE
```

Payroll ledger:

```text
AXFINANCE
```

---

# 125. Commerce Boundary

Workforce producing:

```text
goods
services
```

được reference bởi:

```text
AXCOMMERCE
```

---

# 126. Manufacturing Boundary

Factory workers/tasks:

```text
AXMANUFACTURING
```

workforce semantics:

```text
AXLABOR
```

---

# 127. Construction Boundary

Construction workers:

```text
AXCONSTRUCTION
```

labor identity/work assignment:

```text
AXLABOR
```

---

# 128. Transport Boundary

Drivers/operators:

```text
AXTRANSPORT
```

employment/workforce:

```text
AXLABOR
```

---

# 129. Healthcare Workforce

Doctors/nurses/etc.:

```text
AX674
```

employment semantics:

```text
AXLABOR
```

---

# 130. Labor Simulation

```text
LaborSimulation {
    workers
    employers
    jobs
    skills
    wages
    policies
    geography
    seed
}
```

---

# 131. Labor Scenario

```text
Scenario {
    automation_rate
    migration
    training_capacity
    demand_shock
    wage_change
    technology_change
}
```

---

# 132. Automation Simulation

Có thể mô hình:

```text
HumanTask
→ AutomationCandidate
→ AI/RPA/Robot
→ TaskTransformation
```

Output:

```text
TaskAutomationScenario
```

không phải chắc chắn về tương lai việc làm.

---

# 133. AI Labor Market Simulation

```text
TechnologyShock
+
SkillDemand
+
Training
+
WorkerMobility
+
EmployerDemand
→
LaborMarketScenario
```

---

# 134. Workforce Digital Twin

```text
WorkforceTwin {
    workers
    skills
    positions
    vacancies
    assignments
    demand
    supply
}
```

---

# 135. Twin State

Phải phân biệt:

```text
Observed
Estimated
Predicted
Planned
Simulated
```

---

# 136. Labor Market Digital Twin

```text
Education
   ↓
Skills
   ↓
Workers
   ↓
Jobs
   ↓
Employment
   ↓
Income
```

Có thể chạy scenario:

```text
EducationPolicy
TechnologyChange
IndustryGrowth
Migration
Automation
```

---

# 137. Mobility

```text
WorkerMobility {
    origin
    destination
    skill
    time
    constraints
}
```

Không tự suy luận rằng worker có thể hoặc nên di chuyển.

---

# 138. Geography

Labor market có thể phân vùng:

```text
country
region
city
district
site
remote
```

---

# 139. Global Labor Market

```text
GlobalLaborNetwork {
    regions[]
    workers[]
    employers[]
    skills[]
    jobs[]
    mobility_rules[]
}
```

Migration/legal authorization thuộc AXGOV/AXLAW.

---

# 140. Cross-Border Work

```text
CrossBorderEmployment {
    worker
    employer
    jurisdiction[]
    work_location
    legal_reference
}
```

---

# 141. Remote Cross-Border Work

Phải giữ riêng:

```text
worker_location
employer_location
service_location
tax_reference
legal_reference
```

---

# 142. Labor Economics Interface

AX671 có thể nhận aggregate:

```text
employment
wages
labor_supply
labor_demand
productivity
```

AXLABOR giữ operational records.

---

# 143. Macroeconomic Boundary

```text
AXLABOR
=
micro/operational labor system

AX671
=
macro labor/economic system
```

---

# 144. Security Capabilities

```text
labor.read
worker.read
worker.profile
worker.write
job.read
job.create
vacancy.create
application.create
application.review
employment.create
employment.modify
schedule.write
attendance.write
timesheet.approve
compensation.read
compensation.write
performance.read
performance.write
skill.verify
credential.verify
workforce.plan
labor.analytics
labor.simulation
labor.ai
labor.admin
```

---

# 145. High-Risk Operations

Audit bắt buộc:

```text
employment_create
employment_end
compensation_change
performance_finalize
worker_restriction
credential_revocation
job_requirement_change
bulk_assignment
bulk_schedule_change
```

---

# 146. Capability Separation

Có thể yêu cầu:

```text
Recruiter
≠
PayrollOperator
≠
PerformanceReviewer
≠
SystemAdministrator
```

---

# 147. Work Authorization

```text
@requires_capability("work.assign")
```

để ngăn agent tự ý assign worker.

---

# 148. Labor Event Audit

```text
Actor
Action
Worker
Target
Policy
Authority
Before
After
Timestamp
Evidence
```

---

# 149. Performance Privacy

Performance records nên có:

```text
visibility_scope
retention
purpose
review_authority
```

---

# 150. Immutable Employment Events

Các event quan trọng:

```text
Hire
Promotion
Transfer
CompensationChange
EmploymentEnd
CertificationChange
```

phải preserve history.

---

# 151. Modules

```text
axiom.labor.core
axiom.labor.person
axiom.labor.worker
axiom.labor.employer

axiom.labor.skill
axiom.labor.competency
axiom.labor.qualification
axiom.labor.credential
axiom.labor.experience

axiom.labor.job
axiom.labor.position
axiom.labor.vacancy
axiom.labor.application
axiom.labor.recruitment
axiom.labor.matching

axiom.labor.employment
axiom.labor.assignment
axiom.labor.task
axiom.labor.team
axiom.labor.role
axiom.labor.schedule
axiom.labor.shift
axiom.labor.attendance
axiom.labor.timesheet
axiom.labor.leave

axiom.labor.compensation
axiom.labor.benefit
axiom.labor.payroll

axiom.labor.performance
axiom.labor.career
axiom.labor.learning

axiom.labor.market
axiom.labor.supply
axiom.labor.demand
axiom.labor.workforce
axiom.labor.planning

axiom.labor.ai
axiom.labor.risk
axiom.labor.simulation
axiom.labor.twin
axiom.labor.analytics

axiom.labor.security
axiom.labor.distributed
axiom.labor.realtime
axiom.labor.gpu
axiom.labor.wasm
axiom.labor.mobile
axiom.labor.global
```

---

# 152. Profiles

```text
AXLABOR_NONE
AXLABOR_CORE
AXLABOR_WORKER
AXLABOR_EMPLOYER
AXLABOR_SKILL
AXLABOR_COMPETENCY
AXLABOR_CREDENTIAL
AXLABOR_JOB
AXLABOR_POSITION
AXLABOR_VACANCY
AXLABOR_RECRUITMENT
AXLABOR_MATCHING
AXLABOR_EMPLOYMENT
AXLABOR_ASSIGNMENT
AXLABOR_TASK
AXLABOR_TEAM
AXLABOR_SCHEDULE
AXLABOR_ATTENDANCE
AXLABOR_TIMESHEET
AXLABOR_LEAVE
AXLABOR_COMPENSATION
AXLABOR_BENEFIT
AXLABOR_PAYROLL
AXLABOR_PERFORMANCE
AXLABOR_CAREER
AXLABOR_LEARNING
AXLABOR_MARKET
AXLABOR_WORKFORCE
AXLABOR_PLANNING
AXLABOR_ANALYTICS
AXLABOR_AI
AXLABOR_SIMULATION
AXLABOR_TWIN
AXLABOR_SECURITY
AXLABOR_DISTRIBUTED
AXLABOR_REALTIME
AXLABOR_GPU
AXLABOR_WASM
AXLABOR_MOBILE
AXLABOR_GLOBAL
AXLABOR_FULL
```

---

# 153. Annotations

```text
@labor
@worker
@employer
@candidate

@skill
@competency
@qualification
@credential
@experience

@job
@position
@vacancy
@application
@recruitment
@job_match

@employment
@assignment
@task
@team
@role
@schedule
@shift
@attendance
@timesheet
@leave

@compensation
@benefit
@payroll

@performance
@career
@learning

@labor_market
@labor_supply
@labor_demand
@workforce
@workforce_plan

@labor_ai
@labor_simulation
@labor_twin
@labor_analytics
```

---

# 154. File Extensions

```text
.axlabor
.axworker
.axemployer
.axcandidate

.axskill
.axcompetency
.axqualification
.axcredential
.axexperience

.axjob
.axposition
.axvacancy
.axapplication
.axrecruitment
.axjobmatch

.axemployment
.axassignment
.axtask
.axteam
.axrole
.axschedule
.axshift
.axattendance
.axtimesheet
.axleave

.axcompensation
.axbenefit
.axpayroll

.axperformance
.axcareer
.axlearning

.axlabormarket
.axlaborsupply
.axlabordemand
.axworkforce
.axworkforceplan

.axlaborai
.axlaborsim
.axlabortwin
.axlaboranalytics
```

---

# 155. CLI

```bash
axiom labor create
axiom labor inspect

axiom worker create
axiom worker inspect
axiom worker skills

axiom employer create
axiom employer workforce

axiom skill create
axiom skill assess
axiom skill verify

axiom credential verify
axiom qualification inspect

axiom job create
axiom job inspect
axiom vacancy create
axiom vacancy close

axiom application create
axiom application review
axiom application status

axiom employment create
axiom employment inspect
axiom employment end

axiom assignment create
axiom assignment complete

axiom schedule create
axiom shift create
axiom attendance record
axiom timesheet create
axiom timesheet approve

axiom leave request
axiom leave approve

axiom compensation create
axiom benefit assign
axiom payroll export

axiom performance create
axiom performance review

axiom career plan
axiom learning plan

axiom workforce plan
axiom workforce forecast

axiom labor supply
axiom labor demand
axiom labor market

axiom labor match
axiom labor search

axiom labor-ai match
axiom labor-ai forecast
axiom labor-ai analyze

axiom labor simulate
axiom labor twin
```

---

# 156. Core IR

Worker:

```text
WorkerCreate
WorkerProfileUpdate
WorkerSkillAttach
SkillAssessmentCreate
CredentialVerify
```

Jobs:

```text
JobCreate
PositionCreate
VacancyCreate
VacancyPublish
VacancyClose
```

Recruitment:

```text
CandidateCreate
ApplicationCreate
ApplicationScreen
InterviewSchedule
AssessmentCreate
OfferCreate
OfferAccept
```

Employment:

```text
EmploymentCreate
EmploymentActivate
EmploymentSuspend
EmploymentTransfer
EmploymentPromote
EmploymentEnd
```

Work:

```text
TaskCreate
TaskAssign
TaskStart
TaskBlock
TaskComplete

ShiftCreate
ShiftAssign
AttendanceRecord
TimesheetCreate
TimesheetApprove
LeaveRequest
LeaveApprove
```

Compensation:

```text
CompensationCreate
CompensationChange
BenefitAssign
PayrollInputCreate
```

Performance:

```text
PerformanceRecordCreate
PerformanceReviewCreate
FeedbackCreate
SkillGapDetect
CareerPlanCreate
LearningPlanCreate
```

Market:

```text
LaborDemandObserve
LaborSupplyObserve
LaborDemandForecast
LaborSupplyForecast
LaborMarketSimulate
```

AI:

```text
SkillExtract
JobMatch
CandidateMatch
WorkforceForecast
AssignmentOptimize
SkillGapPredict
LaborRecommendation
ActionAuthorize
```

Simulation:

```text
LaborSimCreate
LaborSimStep
LaborSimRun
LaborScenarioCreate
LaborTwinCreate
LaborTwinSync
```

---

# 157. Recruitment State Machine

```text
Draft
→ Submitted
→ Screening
→ Interview
→ Assessment
→ Offer
→ Accepted
```

Branches:

```text
Rejected
Withdrawn
Expired
```

---

# 158. Employment State Machine

```text
Proposed
→ Offered
→ Accepted
→ Active
```

Alternative:

```text
Suspended
→ Active
→ Ended
```

---

# 159. Work Task State Machine

```text
Planned
→ Assigned
→ Accepted
→ Started
→ Completed
```

Branches:

```text
Blocked
Cancelled
Rejected
```

---

# 160. Leave State Machine

```text
Draft
→ Submitted
→ Approved
→ Active
→ Completed
```

Alternative:

```text
Rejected
Cancelled
```

---

# 161. Credential State Machine

```text
Issued
→ Active
→ Expiring
→ Expired
```

Alternative:

```text
Revoked
Suspended
```

---

# 162. Fundamental Labor Invariants

```text
L-001 Person ≠ Worker.
L-002 Worker classification is explicit.
L-003 Job ≠ Position.
L-004 Position ≠ Employment.
L-005 Vacancy references valid position.
L-006 Application references valid candidate and vacancy.
L-007 Skill ≠ Qualification.
L-008 Qualification ≠ Certification.
L-009 Certification authority is explicit.
L-010 Experience ≠ Skill.
L-011 Skill assessment retains evidence.
L-012 Skill level is contextual/versioned.
L-013 Employment references worker and employer.
L-014 Employment history is preserved.
L-015 Employment ≠ legal contract.
L-016 Legal contract remains AXLAW authority.
L-017 Assignment requires capability.
L-018 Assignment respects explicit constraints.
L-019 Task completion requires valid state transition.
L-020 Timesheet requires explicit period.
L-021 Attendance is not automatically proof of work output.
L-022 Performance metric ≠ human worth.
L-023 Productivity metric requires context.
L-024 Performance evaluation retains evidence.
L-025 Compensation ≠ payroll settlement.
L-026 Payroll ≠ ledger authority.
L-027 Payroll financial settlement belongs AXFINANCE.
L-028 Benefit eligibility is policy-defined.
L-029 Job matching output is a recommendation/signal.
L-030 Matching score ≠ human value.
L-031 AI recommendation ≠ employment decision.
L-032 AI score ≠ legal eligibility.
L-033 Sensitive attributes are not inferred by default.
L-034 Recruitment model version is retained.
L-035 Recruitment evidence is auditable.
L-036 Human/authorized review can override AI recommendation.
L-037 Labor demand forecast ≠ actual demand.
L-038 Labor supply forecast ≠ actual supply.
L-039 Wage forecast ≠ actual wage.
L-040 Labor simulation ≠ actual labor market.
L-041 Labor twin distinguishes observed/estimated/predicted/simulated.
L-042 Workforce plan ≠ committed employment.
L-043 Career recommendation ≠ promotion.
L-044 Skill gap ≠ personal deficiency judgment.
L-045 Credential expiration is explicit.
L-046 License authority remains external.
L-047 Health information belongs health boundary.
L-048 Education credential authority belongs issuer/education domain.
L-049 Migration authority belongs legal/government domain.
L-050 Compensation currency is explicit.
L-051 Historical compensation remains versioned.
L-052 Employment changes are auditable.
L-053 Termination events preserve history.
L-054 Bulk workforce changes require authorization.
L-055 Worker data retention is policy-controlled.
L-056 Worker profile access is capability-controlled.
L-057 Delegation has scope.
L-058 Delegation has expiry unless policy explicitly allows otherwise.
L-059 Organization hierarchy ≠ ownership hierarchy.
L-060 Reporting line ≠ legal authority.
L-061 Worker reputation is contextual.
L-062 Worker ranking is policy-scoped.
L-063 No universal human ranking.
L-064 Labor marketplace ranking objective is explicit.
L-065 No hidden optimization objective.
L-066 Work assignment cannot silently violate qualification constraints.
L-067 Safety requirements are explicit.
L-068 AI cannot silently override safety policy.
L-069 Work schedule uses explicit time zone.
L-070 Historical employment events are immutable/versioned.
```

---

# 163. AI Governance Invariants

```text
AI-001 Model version is recorded.
AI-002 Input snapshot is recorded.
AI-003 Recommendation is distinguishable from decision.
AI-004 Decision authority is explicit.
AI-005 High-impact actions are auditable.
AI-006 Human review can be required by policy.
AI-007 Sensitive inference is restricted.
AI-008 Model drift can be detected.
AI-009 Evaluation dataset/version is recorded.
AI-010 Automated action requires capability.
```

---

# 164. Labor Simulation Invariants

```text
SIM-001 Simulation has isolated state.
SIM-002 Simulation has seed when deterministic behavior is required.
SIM-003 Simulation model version is recorded.
SIM-004 Scenario parameters are explicit.
SIM-005 Simulation cannot mutate production employment.
SIM-006 Simulated worker behavior ≠ actual worker behavior.
SIM-007 Forecast ≠ observed labor state.
SIM-008 Twin synchronization preserves provenance.
```

---

# 165. Performance and Scale

AXLABOR phải hỗ trợ:

```text
millions of workers
millions of jobs
large skill graphs
large scheduling graphs
large event streams
large recruitment pipelines
large labor-market simulations
```

---

# 166. Storage Layout

Hot operational data:

```text
Worker
Position
Employment
Assignment
Schedule
```

có thể dùng SoA.

Historical events:

```text
append-only event log
```

Analytics:

```text
columnar storage
```

Skill search:

```text
inverted index
vector index reference
graph index
```

---

# 167. Skill Graph

```text
SkillA
 ├── prerequisite → SkillB
 ├── related → SkillC
 └── enables → SkillD
```

---

# 168. Career Graph

```text
JuniorEngineer
       ↓
Engineer
       ↓
SeniorEngineer
       ↓
PrincipalEngineer
```

Đây là graph mô hình nghề nghiệp, không phải prediction bắt buộc.

---

# 169. Skill Ontology

Skill có thể liên kết:

```text
occupation
industry
job
course
credential
task
technology
```

---

# 170. Job Search

Search có thể kết hợp:

```text
keyword
skill
qualification
location
remote
salary_reference
schedule
employment_type
```

Search engine có thể sử dụng AX641.

---

# 171. Job Recommendation

```text
Candidate
→ Search
→ Match
→ Rank
→ Recommendation
```

Ranking policy phải explicit/versioned.

---

# 172. Employer Recommendation

Tương tự:

```text
Vacancy
→ CandidateSearch
→ Match
→ Recommendation
```

Không được tự động suy luận sensitive traits.

---

# 173. Workforce Scheduling

Optimization inputs:

```text
workers
skills
availability
tasks
shifts
constraints
```

Output:

```text
SchedulePlan
```

---

# 174. Scheduling Objective

Ví dụ:

```text
maximize_coverage
minimize_overtime
minimize_unfilled_shifts
minimize_travel_reference
```

Objective phải khai báo.

---

# 175. Scheduling Conflict

Nếu không có feasible schedule:

```text
NoFeasiblePlan {
    violated_constraints[]
}
```

Không silently relax constraint.

---

# 176. Constraint Relaxation

Nếu muốn relax:

```text
RelaxationPolicy {
    constraint
    allowed
    priority
    authorization
}
```

---

# 177. Workforce Resilience

Simulation có thể test:

```text
AbsenceShock
SkillLoss
DemandSpike
SupplyShortage
AutomationShock
InfrastructureFailure
```

---

# 178. Enterprise Digital Twin

```text
EnterpriseTwin {
    organization
    workers
    skills
    projects
    tasks
    capacity
    demand
    finance_reference
}
```

---

# 179. Work Knowledge Twin

```text
WorkerKnowledge
TeamKnowledge
ProjectKnowledge
OrganizationKnowledge
```

link AX645/AX650.

---

# 180. Agentic Workforce

AI agents có thể trở thành:

```text
PlanningAgent
SchedulingAgent
RecruitmentAssistant
TrainingAgent
KnowledgeAgent
OperationsAgent
```

Nhưng agent identity ≠ human worker.

---

# 181. AI Agent Worker

Nếu AI agent thực hiện work:

```text
AgentWorker {
    agent_ref
    capabilities[]
    authority[]
}
```

phải phân biệt:

```text
HumanWorker
AIWorker
HybridWorkUnit
```

---

# 182. Human-AI Team

```text
Team {
    human_members[]
    agent_members[]
    tasks[]
}
```

---

# 183. Work Attribution

Một task có thể có:

```text
human_contribution
ai_contribution
tool_contribution
```

---

# 184. Contribution Record

```text
Contribution {
    actor
    task
    contribution_type
    evidence
    timestamp
}
```

---

# 185. AI Work Accountability

AI-generated output phải có:

```text
agent_id
model_version
tool_trace
authorization
human_oversight_reference
```

khi policy yêu cầu.

---

# 186. Enterprise Automation

Pipeline:

```text
Task
→ AutomationAnalysis
→ Simulation
→ Approval
→ Deployment
→ Monitoring
```

Không tự động thay đổi production workforce chỉ vì simulation.

---

# 187. Human-AI Substitution Simulation

Có thể so sánh scenario:

```text
HumanOnly
AIOnly
Hybrid
```

với metrics:

```text
cost_reference
throughput
latency
quality
risk
coverage
```

Không đưa ra kết luận giá trị về con người.

---

# 188. Labor Market Digital Twin Architecture

```text
AXEDUCATION
      ↓
SkillSupply
      ↓
AXLABOR
      ↓
Employment
      ↓
AXCOMMERCE
      ↓
Demand
      ↓
AXFINANCE
      ↓
Income
```

Feedback:

```text
Income
→ Education
→ Skill Acquisition
→ Labor Supply
```

được mô phỏng trong AX671/AXLABOR simulation boundary.

---

# 189. Global Workforce Graph

```text
Country
 ├── Region
 │    ├── Employer
 │    ├── Worker
 │    ├── Skill
 │    └── Job
```

---

# 190. Labor Mobility Constraints

Có thể reference:

```text
VisaRef
WorkPermitRef
ProfessionalLicenseRef
UnionAgreementRef
EmploymentLawRef
```

Không tự cấp authorization.

---

# 191. Union Boundary

Labor organization có thể được reference:

```text
LaborOrganizationRef
CollectiveAgreementRef
RepresentationRef
```

Legal authority thuộc AXLAW/AXGOV.

---

# 192. Collective Agreement

```text
CollectiveAgreementRef {
    parties
    scope
    effective_period
}
```

---

# 193. Labor Dispute

```text
LaborDispute {
    worker
    employer
    issue
    evidence[]
    resolution_reference
}
```

Dispute resolution authority thuộc legal/civic system.

---

# 194. Grievance

```text
Grievance {
    worker
    category
    description
    status
}
```

---

# 195. Workplace Incident

```text
WorkplaceIncident {
    site
    workers[]
    event
    evidence[]
    severity
}
```

Safety investigation có thể link AXLAW/AX674/AXMANUFACTURING/AXCONSTRUCTION.

---

# 196. Workplace Safety

```text
SafetyRequirement
SafetyTraining
SafetyCertification
SafetyIncident
```

Safety state phải rõ ràng.

---

# 197. Workforce Resilience

Các KPI:

```text
critical_skill_coverage
single_point_of_failure
backup_capacity
training_readiness
succession_coverage
```

---

# 198. Succession Plan

```text
SuccessionPlan {
    critical_role
    candidate_refs[]
    skill_gaps[]
    readiness
}
```

Readiness là model output, không phải certainty.

---

# 199. Knowledge Bus

AXLABOR có thể phát event:

```text
SkillChanged
EmploymentStarted
EmploymentEnded
TaskCompleted
CertificationExpired
WorkforceGapDetected
```

để các domain khác subscribe.

---

# 200. Final Architecture Contract

`AXLABOR` phải cung cấp native substrate cho:

```text
Workers
Employers
Jobs
Positions
Vacancies
Candidates
Applications
Skills
Competencies
Qualifications
Credentials
Experience
Employment
Assignments
Tasks
Teams
Schedules
Attendance
Timesheets
Leave
Compensation
Benefits
PayrollReferences
Performance
Career
Learning
WorkforcePlanning
LaborMarkets
LaborSupply
LaborDemand
Matching
LaborAI
LaborSimulation
LaborDigitalTwin
Human-AI Work
```

và giữ nguyên:

```text
Person
    ≠
Worker
    ≠
Employee

Skill
    ≠
Qualification
    ≠
Certification

Job
    ≠
Position
    ≠
Employment

Performance
    ≠
HumanWorth

Prediction
    ≠
Decision

Recommendation
    ≠
EmploymentAction

Compensation
    ≠
PayrollSettlement

Payroll
    ≠
LedgerAuthority

Simulation
    ≠
ActualLaborMarket
```

---

# 201. Economic Civilization Stack

Sau BOOTSTRAP-688:

```text
                    CIVILIZATION
                         │
                  ┌──────┴──────┐
                  │             │
              AXECON        AXFINANCE
                  │             │
                  └──────┬──────┘
                         │
                    AXCOMMERCE
                         │
                     AXLABOR
                         │
                    AXEDUCATION
                         │
                   HUMAN CAPITAL
```

Các physical domains:

```text
AXAGRI
AXMANUFACTURING
AXCONSTRUCTION
AXTRANSPORT
```

có thể sử dụng workforce substrate này.

---

# 202. Core Civilization Feedback Loop

```text
Education
   ↓
Skills
   ↓
Labor
   ↓
Production
   ↓
Commerce
   ↓
Income
   ↓
Finance
   ↓
Education
```

Đây là một trong các feedback loops nền tảng của civilization simulation.

---

# 203. Test Target

AXLABOR phải đạt tối thiểu:

```text
≥ 11,000 automated tests
≥ 900 architecture invariants
```

với coverage cho:

```text
worker identity
skills
credentials
jobs
matching
recruitment
employment
work assignment
scheduling
attendance
timesheets
compensation
performance
privacy
AI
labor market
simulation
digital twin
distributed execution
recovery
cross-domain integration
```

---

# 204. Architecture Completion Status

Sau task này, chuỗi:

```text
AXEDUCATION
      ↓
AXLABOR
      ↓
AXCOMMERCE
      ↓
AXFINANCE
```

đã hình thành một economic-human operating layer tương đối hoàn chỉnh.

Các domain physical:

```text
AXAGRI
AXMANUFACTURING
AXCONSTRUCTION
AXTRANSPORT
```

đã có thể kết nối vào workforce/finance/commerce.

---

# 205. Task kế tiếp

**BOOTSTRAP-689 — Native AI Civilization-Scale Housing, Real Estate, Land Property, Rental, Mortgage, Urban Housing Markets, Buildings & Residential Systems Runtime 5.0.**

Domain này sẽ nối:

```text
AXCONSTRUCTION
      ↓
PROPERTY
      ↓
AXCOMMERCE
      ↓
AXFINANCE
      ↓
AXLAW
      ↓
CIVILIZATION
```

và đặc biệt phải phân biệt:

```text
Land
≠ Building
≠ PropertyTitle
≠ Occupancy
≠ Rental
≠ Mortgage
≠ MarketValue
≠ Ownership
≠ LegalRight
≠ PhysicalLocation
```
:::