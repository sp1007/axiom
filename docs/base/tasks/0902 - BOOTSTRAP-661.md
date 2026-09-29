Tiếp tục với **BOOTSTRAP-661** — lớp Goal/Value/Preference/Utility/Decision, nối trực tiếp từ Self/Metacognition của 660.

:::writing{variant="document" id="58321" title="AXIOM BOOTSTRAP-661 — Native AI Value, Goal, Motivation, Preference, Utility, Normative Objective & Decision-Policy Runtime 5.0"}
# BOOTSTRAP-661
## Native AI Value, Goal, Motivation, Preference, Utility, Normative Objective & Decision-Policy Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Goal & Decision Intelligence  
**Predecessor:** BOOTSTRAP-660 — Self-Model, Metacognition & Agency  
**Primary consumers:** 644, 652, 653, 654, 655, 657, 658, 659, 660  
**Governance authorities:** 603, 639, 646, 647  
**Persistence:** 600, 650  
**Personalization:** 651  
**Simulation:** 648  
**Target acceptance:** ≥ 2,000 architectural/specification tests

---

# 1. Mục tiêu

BOOTSTRAP-661 định nghĩa lớp computational dùng để biểu diễn:

- mục tiêu;
- ưu tiên;
- sở thích;
- utility;
- objective;
- value model;
- normative constraint;
- drive;
- motivation;
- decision policy;
- trade-off;
- risk preference;
- tiến độ mục tiêu;
- xung đột mục tiêu;
- quyết định và provenance của quyết định.

Lớp này biến trạng thái nhận thức của 657, self-model của 660, affect của 659 và world model của 655 thành một **decision substrate có cấu trúc**.

Pipeline chính:

```text
Observation / World Model
        │
        ▼
   Current Context
        │
        ├──────────────┐
        ▼              ▼
     Goals        Preferences
        │              │
        ├──────┬───────┘
        ▼      ▼
     Values   Drives
        │      │
        └──┬───┘
           ▼
      Objectives
           │
           ▼
     Constraints/Norms
           │
           ▼
     Candidate Actions
           │
           ▼
     Utility / Cost / Risk
           │
           ▼
      Decision Policy
           │
           ▼
        Decision
           │
           ▼
      Execution 603/644
           │
           ▼
     Outcome / Evaluation
           │
           ▼
    Goal Progress + 660
```

---

# 2. Boundary quan trọng

## 2.1 Goal không phải desire

`Goal` là cấu trúc computational mô tả trạng thái mong muốn hoặc điều kiện cần đạt.

```text
Goal("complete_build")
```

không chứng minh hệ thống "muốn" build thành công theo nghĩa chủ quan.

---

## 2.2 Preference không phải fact

```text
Preference:
    "format = compact"
```

là một preference, không phải thuộc tính khách quan của thế giới.

---

## 2.3 Utility không phải moral truth

Utility chỉ là hàm đánh giá phục vụ decision process.

```text
utility(action)
```

không có nghĩa:

```text
utility(action) == moral_value(action)
```

---

## 2.4 Drive không phải subjective desire

`Drive` là state variable có thể tạo áp lực ưu tiên trong decision system.

Ví dụ:

```text
resource_pressure
deadline_pressure
task_completion_pressure
exploration_drive
```

không được diễn giải mặc định là cảm giác chủ quan.

---

## 2.5 Motivation không chứng minh motivation experience

`Motivation` mô tả cơ chế computational giải thích tại sao một objective được ưu tiên.

Nó không tuyên bố agent "cảm thấy có động lực".

---

# 3. Authority hierarchy

Mọi decision phải đi qua hierarchy:

```text
Security
   ↓
Capability
   ↓
Policy / Authorization
   ↓
Hard Constraints
   ↓
Normative Constraints
   ↓
Explicit Objectives
   ↓
Delegated Objectives
   ↓
User Preferences
   ↓
Learned Preferences
   ↓
Soft Utility
   ↓
Heuristic Preferences
```

Không có lower layer nào được phép override higher layer.

Đặc biệt:

```text
Goal ≠ Permission
Preference ≠ Permission
Utility ≠ Permission
Motivation ≠ Permission
Drive ≠ Permission
```

---

# 4. Core types

## 4.1 Goal

```axiom
struct Goal {
    id: GoalId
    state: GoalState
    source: GoalSource
    provenance: GoalProvenance
    priority: GoalPriority
    horizon: GoalHorizon
    constraints: GoalConstraint[]
    dependencies: GoalDependency[]
    metric: GoalMetric
    deadline: Time?
    budget: Budget?
    authority: AuthorityBinding
}
```

---

## 4.2 GoalState

```axiom
enum GoalState {
    Proposed
    Active
    Blocked
    Suspended
    Completed
    Failed
    Retired
    Cancelled
}
```

---

## 4.3 GoalSource

```axiom
enum GoalSource {
    System
    Developer
    User
    Environment
    Policy
    Learned
    Inferred
    Delegated
    SelfGenerated
    Imported
}
```

Nguồn phải được lưu cùng goal.

Không được biến:

```text
Inferred
```

thành:

```text
User
```

mà không có explicit authorization.

---

# 5. Goal provenance

```axiom
struct GoalProvenance {
    source: GoalSource
    source_id: Id?
    created_at: Time
    created_by: IdentityId
    evidence: EvidenceRef[]
    confidence: Probability?
    scope: Scope
    expires_at: Time?
    revision: Version
}
```

Mục tiêu inferred phải có:

- evidence;
- confidence;
- scope;
- revision.

---

# 6. Goal hierarchy

Goals hỗ trợ hierarchy:

```text
Project
 ├── Build compiler
 │    ├── Parse source
 │    ├── Generate IR
 │    └── Emit object
 └── Validate compiler
```

Mỗi child goal phải giữ:

```text
parent_id
dependency relation
completion semantics
```

---

# 7. Goal dependency

```axiom
enum GoalDependencyKind {
    Requires
    Enables
    Blocks
    Follows
    AlternativeTo
    ConflictsWith
}
```

Ví dụ:

```text
compile
    Requires parse

test
    Requires compile

release
    Requires test
```

---

# 8. Goal conflict

```axiom
struct GoalConflict {
    id: ConflictId
    goal_a: GoalId
    goal_b: GoalId
    type: ConflictType
    severity: ConflictSeverity
    detected_by: ModelRevision
    evidence: EvidenceRef[]
}
```

Conflict types:

```text
HardConflict
SoftConflict
ResourceConflict
DeadlineConflict
PolicyConflict
PreferenceConflict
ValueConflict
NormConflict
ScopeConflict
```

---

# 9. Goal resolution

Resolution phải explicit:

```axiom
struct GoalResolution {
    conflict_id: ConflictId
    strategy: ResolutionStrategy
    winner_basis: ResolutionBasis
    constraints_applied: ConstraintId[]
    objective_revision: Version
    decision_id: DecisionId
}
```

Không được có:

```text
hidden priority heuristic
```

mà không để lại provenance.

---

# 10. Goal priority

```axiom
struct GoalPriority {
    level: i32
    weight: f64?
    class: PriorityClass
}
```

Priority classes:

```text
Critical
Required
High
Normal
Low
Background
Optional
```

Priority không tự động vượt qua authority.

---

# 11. Goal horizon

```axiom
enum GoalHorizon {
    Immediate
    ShortTerm
    MediumTerm
    LongTerm
    Persistent
}
```

---

# 12. Goal metric

Mỗi measurable goal phải có metric version.

```axiom
struct GoalMetric {
    id: MetricId
    revision: Version
    evaluator: FunctionRef
    target: Value
    tolerance: Value?
}
```

Không được đánh giá:

```text
goal progress
```

bằng metric chưa version hóa.

---

# 13. Goal progress

```axiom
struct GoalProgress {
    goal: GoalId
    metric_revision: Version
    current: Value
    target: Value
    ratio: f64
    confidence: f64
    timestamp: Time
}
```

Progress không được đồng nghĩa với success.

---

# 14. Preference

```axiom
struct Preference {
    id: PreferenceId
    subject: PreferenceSubject
    preferred: Value
    strength: PreferenceStrength
    source: PreferenceSource
    scope: Scope
    confidence: f64
    revision: Version
}
```

---

# 15. Preference source

```axiom
enum PreferenceSource {
    ExplicitUser
    ExplicitSystem
    Developer
    Learned
    Inferred
    Contextual
    Imported
}
```

---

# 16. Preference strength

```axiom
struct PreferenceStrength {
    value: f64
    confidence: f64
    calibration: CalibrationRef?
}
```

Phân biệt:

```text
strength
confidence
```

Ví dụ:

```text
strength = 0.9
confidence = 0.4
```

nghĩa là hệ thống có preference mạnh nhưng không chắc preference đó được suy ra đúng.

---

# 17. Preference scope

Preference phải có scope:

```text
request
session
project
device
user
tenant
deployment
global
```

Không được tự động promote:

```text
session preference
```

thành:

```text
global preference
```

---

# 18. Preference inference

Inference:

```axiom
PreferenceInfer(
    observations,
    context,
    prior_preferences
) -> PreferenceInference
```

Kết quả:

```axiom
struct PreferenceInference {
    candidate: Preference
    evidence: EvidenceRef[]
    confidence: f64
    alternatives: PreferenceCandidate[]
}
```

Inference không tự động commit.

---

# 19. Utility

```axiom
struct UtilityFunction {
    id: UtilityId
    revision: Version
    terms: UtilityTerm[]
    domain: Domain
    codomain: NumericDomain
    normalization: NormalizationSpec?
}
```

---

# 20. Utility term

```axiom
struct UtilityTerm {
    feature: FeatureRef
    coefficient: f64
    transform: FunctionRef?
    uncertainty: UncertaintyModel?
}
```

---

# 21. Utility model

```axiom
struct UtilityModel {
    id: ModelId
    revision: Version
    function: UtilityFunction
    assumptions: Assumption[]
    calibration: CalibrationRef?
    provenance: ModelProvenance
}
```

Model revision phải immutable sau khi published.

---

# 22. Objective

Objective là abstraction cao hơn utility.

```axiom
struct Objective {
    id: ObjectiveId
    goal: GoalId?
    utility: UtilityModel?
    constraints: ConstraintRef[]
    priority: GoalPriority
    horizon: GoalHorizon
    authority: AuthorityBinding
    revision: Version
}
```

Objective có thể:

- maximize;
- minimize;
- satisfy;
- maintain;
- avoid;
- achieve;
- stabilize.

---

# 23. Objective binding

```axiom
struct ObjectiveBinding {
    objective: ObjectiveId
    context: DecisionContext
    action_space: ActionSpace
    constraints: ConstraintRef[]
    policy: PolicyRevision
}
```

---

# 24. Hard vs soft objective

```text
Hard:
    must satisfy

Soft:
    optimize if possible
```

Ví dụ:

```text
Hard:
    memory < 1 GB

Soft:
    latency should be low
```

Nếu conflict:

```text
hard constraint wins.
```

---

# 25. Value model

```axiom
struct Value {
    id: ValueId
    name: String
    scope: Scope
    source: ValueSource
    strength: f64
}
```

```axiom
struct ValueModel {
    id: ModelId
    revision: Version
    values: Value[]
    relations: ValueRelation[]
}
```

Value model là computational representation.

Nó không được tuyên bố là:

```text
objective moral truth
```

---

# 26. Normative rule

```axiom
struct NormativeRule {
    id: RuleId
    condition: Predicate
    requirement: Requirement
    authority: AuthorityBinding
    priority: Priority
    provenance: Provenance
}
```

Ví dụ:

```text
IF action accesses protected resource
THEN capability must be present
```

Normative rule có thể được cung cấp bởi 654 hoặc 639.

---

# 27. Drive

```axiom
struct Drive {
    id: DriveId
    model: DriveModel
    state: DriveState
    scope: Scope
}
```

Ví dụ:

```text
DeadlinePressure
ResourcePressure
TaskCompletion
Exploration
Stability
ErrorReduction
```

---

# 28. Drive state

```axiom
struct DriveState {
    intensity: f64
    persistence: f64
    decay: f64
    activation: f64
    confidence: f64
}
```

Drive không được tự động biến thành authority.

---

# 29. Motivation

```axiom
struct Motivation {
    id: MotivationId
    causes: MotivationCause[]
    objectives: ObjectiveId[]
    drives: DriveId[]
    values: ValueId[]
    confidence: f64
}
```

Motivation có thể giải thích:

```text
why objective was prioritized
```

nhưng không phải hidden chain-of-thought.

---

# 30. Decision Policy

```axiom
struct DecisionPolicy {
    id: PolicyId
    revision: Version
    strategy: DecisionStrategy
    constraints: ConstraintRef[]
    risk: RiskPreference
    deadline: Duration?
    fallback: PolicyId?
}
```

---

# 31. Decision strategies

Axiom phải hỗ trợ ít nhất:

```text
WeightedSum
Lexicographic
Pareto
ConstrainedOptimization
Satisficing
Minimax
RiskSensitive
RuleBased
PriorityBased
Hybrid
```

---

# 32. Weighted optimization

```text
score =
    Σ(weight_i × utility_i)
```

Chỉ được áp dụng sau hard constraints.

---

# 33. Lexicographic policy

Objective thứ nhất được tối ưu trước.

Objective thứ hai chỉ dùng khi không làm suy giảm objective có priority cao hơn.

```text
priority 1
    >
priority 2
    >
priority 3
```

---

# 34. Pareto policy

Một action bị dominated nếu:

```text
another action >= it
for every objective

and

> it
for at least one objective.
```

Kết quả:

```text
ParetoFront<ActionCandidate>
```

---

# 35. Satisficing

Cho phép:

```text
acceptable_threshold
```

thay vì tối ưu tuyệt đối.

Ví dụ:

```text
latency <= 100 ms
quality >= 0.9
cost <= budget
```

Một action đạt tất cả threshold có thể được chọn mà không cần tìm global optimum.

---

# 36. Risk preference

```axiom
struct RiskPreference {
    tolerance: f64
    aversion: f64
    model: RiskModel
}
```

Hỗ trợ:

```text
ExpectedValue
VariancePenalty
CVaR
WorstCase
ChanceConstraint
```

---

# 37. Action candidate

```axiom
struct ActionCandidate {
    id: ActionId
    action: ActionRef
    predicted_outcome: OutcomeDistribution
    cost: CostVector
    risk: RiskEstimate
}
```

---

# 38. Action score

```axiom
struct ActionScore {
    action: ActionId
    utility: f64
    cost: f64
    risk: f64
    constraint_status: ConstraintStatus
    confidence: f64
}
```

Score phải lưu model revision.

---

# 39. Decision context

```axiom
struct DecisionContext {
    world_revision: Version
    self_revision: Version
    goal_set_revision: Version
    preference_revision: Version
    utility_revision: Version
    policy_revision: Version
    time: Time
    resource_budget: Budget
}
```

Decision phải reproducible khi deterministic mode được bật.

---

# 40. Decision

```axiom
struct Decision {
    id: DecisionId
    context: DecisionContext
    selected_action: ActionId
    alternatives: ActionScore[]
    constraints: ConstraintResult[]
    tradeoffs: Tradeoff[]
    confidence: f64
    provenance: DecisionProvenance
}
```

---

# 41. Trade-off

```axiom
struct Tradeoff {
    objective_a: ObjectiveId
    objective_b: ObjectiveId
    benefit_a: f64
    cost_b: f64
    resolution: ResolutionBasis
}
```

Trade-off phải explicit khi decision có nhiều objective.

---

# 42. Goal update

Goal có thể thay đổi nhưng update phải version hóa.

```axiom
GoalUpdate {
    old_revision
    new_revision
    reason
    evidence
    authority
}
```

Không silent mutation.

---

# 43. Goal retirement

Goal có thể:

```text
complete
cancel
expire
supersede
retire
```

Retirement phải lưu nguyên nhân.

---

# 44. Self-generated goals

Self-generated goals được phép nhưng phải có:

```text
policy permission
scope
budget
expiration
authority
evaluation
```

Ví dụ:

```text
self_generated_goal:
    improve benchmark score

allowed:
    within current task

not allowed:
    modify system authority
```

---

# 45. Goal delegation

```axiom
GoalDelegate(
    goal,
    agent,
    scope,
    deadline,
    budget
)
```

Delegated agent không nhận authority vượt quá goal binding.

---

# 46. Goal vs capability

Sai:

```text
Goal: read filesystem
=> permission to read filesystem
```

Đúng:

```text
Goal
 +
Capability
 +
Authorization
 =
Executable possibility
```

---

# 47. Goal vs policy

Policy luôn có precedence.

```text
goal:
    maximize data collection

policy:
    do not access protected data
```

Decision phải reject candidate vi phạm policy.

---

# 48. Personalization boundary

651 có thể thay đổi:

```text
preferences
weights
presentation
recommendation behavior
```

nhưng không được thay đổi:

```text
hard security constraints
authority
system safety policy
```

---

# 49. Affect integration

659 có thể cung cấp:

```text
AffectiveState
MoodState
Appraisal
```

661 có thể dùng chúng như decision features.

Ví dụ:

```text
arousal -> risk preference adjustment
```

nhưng:

```text
affect != utility
```

và:

```text
emotion != authority
```

---

# 50. Self-model integration

660 cung cấp:

```text
capabilities
limitations
confidence
resource state
identity
role
```

Decision engine phải sử dụng self-model để loại bỏ action không khả thi.

```text
if capability(action) == unavailable:
    reject
```

---

# 51. Metacognitive integration

660 có thể evaluate:

```text
decision quality
confidence
prediction error
strategy effectiveness
```

661 có thể yêu cầu:

```text
DecisionPolicyRevision
```

nhưng revision phải đi qua authority boundary.

---

# 52. World-model integration

655 cung cấp:

```text
predicted state
causal model
environment state
counterfactual state
```

661 dùng chúng để đánh giá action.

---

# 53. Planning integration

652 chịu trách nhiệm:

```text
plan generation
search
optimization
scheduling
```

661 chịu trách nhiệm:

```text
why optimize
what objective
what preference
what priority
what constraints
which decision policy
```

Do đó:

```text
661 defines decision criteria
652 searches action space
```

---

# 54. Uncertainty integration

653 cung cấp:

```text
belief
probability
uncertainty
confidence
distribution
```

661 không được biến:

```text
confidence
```

thành:

```text
truth
```

---

# 55. Symbolic integration

654 cung cấp:

```text
rules
logic
proof obligations
normative constraints
```

Hard symbolic constraints được evaluate trước utility optimization.

---

# 56. Evaluation integration

646 phải được dùng để kiểm tra:

- utility calibration;
- policy consistency;
- reward hacking;
- specification gaming;
- goal drift;
- preference drift;
- decision robustness;
- adversarial objectives;
- counterfactual behavior.

---

# 57. Reward hacking boundary

Không được coi:

```text
higher utility score
```

là bằng chứng:

```text
better real-world outcome.
```

Decision evaluation phải có outcome-based validation.

---

# 58. Specification gaming

Hệ thống phải hỗ trợ:

```text
proxy objective
true objective
observed metric
external evaluation
```

và phát hiện:

```text
metric improvement
without intended outcome improvement
```

---

# 59. Objective drift

Objective drift xảy ra khi:

```text
objective revision
```

thay đổi semantics đáng kể.

Runtime phải ghi:

```text
old objective
new objective
diff
reason
authority
evaluation
```

---

# 60. Preference drift

Preference có thể thay đổi theo thời gian.

Phải phân biệt:

```text
temporary preference
stable preference
learned preference
explicit preference
inferred preference
```

---

# 61. Preference calibration

```axiom
PreferenceCalibrate(
    predicted_preference,
    observed_choice
) -> CalibrationResult
```

Calibration không tự động thay đổi preference.

---

# 62. Goal reflection

661 hỗ trợ:

```axiom
GoalReflect(goal)
```

Kết quả:

```text
progress
relevance
feasibility
conflicts
staleness
resource cost
```

---

# 63. Goal counterfactual

Có thể mô phỏng:

```text
remove goal
add goal
change priority
change utility
change constraint
```

mà không commit.

---

# 64. Objective shadow update

Objective mới phải có thể chạy ở shadow mode:

```text
old objective -> production

new objective -> shadow
```

Sau evaluation mới activate.

---

# 65. Rollback

Mọi:

```text
goal model
preference model
utility model
objective
decision policy
```

đều phải hỗ trợ rollback nếu persistent.

---

# 66. Decision trace

Decision trace gồm:

```text
context
goal IDs
objective IDs
constraint IDs
candidate actions
utility revision
policy revision
risk model
selected action
confidence
outcome
```

Không chứa hidden chain-of-thought.

---

# 67. Decision explanation

```axiom
DecisionExplain(decision)
```

trả về structured explanation:

```text
Selected:
    action A

Required constraints:
    C1
    C2

Objectives:
    O1
    O2

Trade-offs:
    O1 gained
    O2 reduced

Policy:
    lexicographic-v3

Confidence:
    0.87
```

---

# 68. Real-time mode

Decision policy có:

```text
deadline
budget
fallback
```

Ví dụ:

```text
deadline = 2ms
fallback = safe_default
```

Nếu optimizer timeout:

```text
fallback policy
```

được sử dụng.

---

# 69. Distributed decisions

Distributed decision context phải pin:

```text
goal revision
objective revision
policy revision
world revision
self revision
```

Nếu consensus yêu cầu:

```text
decision hash
```

phải deterministic.

---

# 70. Simulation mode

648/655 có thể cung cấp:

```text
DecisionSimulate
```

Simulation không commit:

```text
goal
objective
policy
action
```

trừ khi explicitly requested.

---

# 71. Governance

647 quản lý:

```text
objective registry
utility model registry
decision policy registry
approved revisions
deployment lifecycle
rollback
```

---

# 72. Privacy

Preference có thể chứa user-sensitive behavioral information.

661 phải hỗ trợ:

```text
scope
consent
retention
deletion
provenance
access policy
```

---

# 73. Security

603 kiểm soát:

```text
who can create goal
who can modify goal
who can activate policy
who can change utility
who can inspect preference
```

661 không tự cấp quyền.

---

# 74. Core annotations

```text
@goal
@goal_set
@goal_priority
@goal_horizon
@goal_source
@goal_provenance
@goal_constraint
@goal_dependency
@goal_conflict
@goal_resolution
@preference
@preference_strength
@preference_scope
@preference_inference
@utility
@utility_model
@objective
@objective_binding
@drive
@drive_state
@motivation
@motivation_state
@value
@value_model
@normative_rule
@decision_policy
@decision
@tradeoff
@lexicographic
@pareto
@satisficing
@risk_preference
@goal_progress
@goal_update
@goal_retire
@goal_delegate
@self_generated_goal
@goal_deadline
@goal_budget
@objective_revision
@utility_revision
@policy_revision
@decision_trace
@decision_explain
@motivation_trace
@preference_calibration
```

---

# 75. Metadata artifacts

```text
.axgoal
.axgoalset
.axpref
.axutility
.axobjective
.axdrive
.axmotivation
.axvalue
.axnorm
.axdecision
.axpolicy
.axtradeoff
.axgoaltrace
.axmotivationtrace
.axdecisiontrace
.axobjectiveeval
.axprefcalib
```

---

# 76. Compiler IR

Core IR operations:

```text
GoalCreate
GoalRead
GoalUpdate
GoalPause
GoalResume
GoalRetire
GoalDelegate
GoalProgress
GoalConflictDetect
GoalResolve

PreferenceRead
PreferenceInfer
PreferenceUpdate

UtilityCreate
UtilityEvaluate
UtilityCompare

ObjectiveBind
ObjectiveEvaluate

DriveUpdate
MotivationEvaluate
ValueEvaluate
NormCheck

DecisionContextCreate
ActionScore
DecisionSelect
TradeoffEvaluate
ParetoFilter
LexicographicSelect
SatisficingCheck
RiskEvaluate

DecisionCommit
DecisionExplain
DecisionTrace

GoalReflect
GoalCounterfactual

ObjectiveShadowUpdate
ObjectiveRollback

PolicyCheck
```

---

# 77. IR invariant

Compiler phải preserve:

```text
authorization
constraint ordering
objective revision
utility revision
policy revision
provenance
decision determinism
```

Optimizer không được biến đổi:

```text
hard constraint
```

thành:

```text
soft utility
```

chỉ vì optimization thuận tiện hơn.

---

# 78. Profiles

```text
AXGOAL_NONE
AXGOAL_CORE
AXGOAL_STATE
AXGOAL_HIERARCHY
AXGOAL_CONFLICT
AXGOAL_DELEGATION

AXPREF_CORE
AXPREF_LEARNED
AXPREF_INFERENCE

AXUTILITY_CORE
AXUTILITY_MULTI

AXOBJECTIVE_CORE
AXOBJECTIVE_REVISION

AXDRIVE_CORE
AXMOTIVATION_CORE

AXVALUE_CORE
AXNORMATIVE

AXDECISION_CORE
AXDECISION_RISK
AXDECISION_PARETO
AXDECISION_LEXICOGRAPHIC
AXDECISION_SATISFICING
AXDECISION_REALTIME
AXDECISION_DISTRIBUTED
AXDECISION_SIMULATION

AXDECISION_AGENT
AXGOVERNANCE
AXPRIVACY

AXFULL
```

---

# 79. CLI

```text
axiom goal inspect
axiom goal list
axiom goal create
axiom goal update
axiom goal pause
axiom goal resume
axiom goal retire
axiom goal progress
axiom goal conflicts
axiom goal resolve
axiom goal delegate

axiom preference inspect
axiom preference infer
axiom preference update
axiom preference calibrate

axiom utility inspect
axiom utility evaluate
axiom utility compare

axiom objective inspect
axiom objective bind
axiom objective evaluate
axiom objective compare

axiom drive inspect
axiom drive state
axiom drive update

axiom motivation inspect
axiom motivation evaluate
axiom motivation trace

axiom value inspect
axiom value evaluate

axiom norm inspect
axiom norm check

axiom decision inspect
axiom decision evaluate
axiom decision simulate
axiom decision trace
axiom decision explain

axiom policy inspect
axiom policy validate

axiom goal benchmark
```

---

# 80. Decision execution contract

661 chỉ trả:

```text
Decision
```

cho execution layer.

Execution thuộc:

```text
603
605
607
608
644
```

tùy loại action.

661 không trực tiếp bypass execution authority.

---

# 81. Goal lifecycle

```text
Proposed
   ↓
Validated
   ↓
Active
   ↓
Progressing
   ├── Blocked
   ├── Suspended
   ├── Completed
   ├── Failed
   └── Retired
```

Mọi transition phải được trace.

---

# 82. Decision lifecycle

```text
Context
  ↓
Candidate generation
  ↓
Constraint filtering
  ↓
Objective evaluation
  ↓
Risk evaluation
  ↓
Policy selection
  ↓
Decision
  ↓
Authorization
  ↓
Execution
  ↓
Outcome
  ↓
Evaluation
```

---

# 83. Goal lifecycle invariants

1. Goal phải có ID duy nhất.
2. Goal phải có source.
3. Goal phải có provenance.
4. Goal phải có scope.
5. Goal không tự cấp capability.
6. Goal không tự cấp authority.
7. Goal revision phải monotonic.
8. Goal update phải traceable.
9. Retired goal không tự active lại.
10. Goal conflict phải detect được.
11. Conflict resolution phải explicit.
12. Child goal không vượt authority của parent.
13. Delegated goal phải có scope.
14. Delegated goal phải có expiration hoặc lifecycle rule.
15. Self-generated goal phải có policy.
16. Self-generated goal không được tạo authority.
17. Goal progress phải dùng metric revision.
18. Goal completion phải dựa trên metric.
19. Goal failure phải có evidence.
20. Goal cancellation phải trace.

---

# 84. Preference invariants

21. Preference không phải fact.
22. Preference phải có source.
23. Preference phải có scope.
24. Inferred preference phải có confidence.
25. Learned preference không được giả mạo explicit preference.
26. Session preference không tự thành global.
27. Preference update phải versioned.
28. Preference calibration không tự commit.
29. Conflicting preferences phải detectable.
30. Preference không override hard constraint.
31. Preference không cấp authority.
32. Preference không cấp capability.
33. Preference deletion phải enforceable.
34. Preference provenance phải preserved.
35. Privacy policy áp dụng cho preference data.

---

# 85. Utility invariants

36. Utility phải có revision.
37. Utility không phải moral truth.
38. Utility không cấp authority.
39. Utility không bypass constraints.
40. Utility score không phải ground truth.
41. Utility model phải có domain.
42. Utility assumptions phải trace.
43. Utility changes phải version.
44. Published model không silent mutate.
45. Utility normalization phải explicit.
46. Utility uncertainty phải preserved.
47. Utility comparison phải cùng domain hoặc explicit conversion.
48. Utility score không được dùng nếu model revision unavailable.
49. Utility optimization phải deterministic khi deterministic mode yêu cầu.
50. Utility model phải rollback được nếu persistent.

---

# 86. Objective invariants

51. Objective phải có ID.
52. Objective phải có authority.
53. Objective phải có revision.
54. Objective phải có scope.
55. Hard objective không được downgrade thành soft.
56. Soft objective không được upgrade thành hard.
57. Objective conflict phải detect.
58. Objective revision phải trace.
59. Objective binding phải pin revision.
60. Objective shadow update không được commit tự động.
61. Objective rollback phải atomic.
62. Objective không tự cấp capability.
63. Objective không tự cấp permission.
64. Objective không vượt policy.
65. Objective source phải preserved.

---

# 87. Drive/motivation invariants

66. Drive là computational state.
67. Drive không phải bằng chứng subjective desire.
68. Drive không tự cấp authority.
69. Drive intensity không phải truth.
70. Drive persistence phải bounded.
71. Drive update phải trace.
72. Motivation phải có provenance.
73. Motivation confidence phải separate.
74. Motivation không phải hidden thought disclosure.
75. Motivation không được override policy.
76. Affect và motivation phải distinguishable.
77. Drive conflict phải detectable.
78. Drive escalation phải bounded.
79. Drive không được tạo capability.
80. Drive không được bypass authorization.

---

# 88. Value/norm invariants

81. Value model phải versioned.
82. Value không tự là moral truth.
83. Value source phải explicit.
84. Normative rule phải có authority.
85. Normative rule conflict phải detectable.
86. Higher authority wins according to explicit governance.
87. Normative rule không được hidden.
88. Norm update phải trace.
89. Norm simulation không tự commit.
90. Value conflict phải có resolution basis.
91. Norm cannot be bypassed by utility.
92. Norm cannot be bypassed by preference.
93. Norm cannot be bypassed by drive.
94. Norm cannot be bypassed by self-generated goal.
95. Norm evaluation phải reproducible khi required.

---

# 89. Decision invariants

96. Decision phải có context.
97. Context phải pin model revisions.
98. Decision phải có candidate set hoặc explicit rule result.
99. Hard constraints được evaluate trước soft utility.
100. Invalid action không được score như executable action.
101. Authorization phải separate from optimization.
102. Decision không cấp capability.
103. Decision trace phải preserved.
104. Decision explanation phải structured.
105. Explanation không được giả làm hidden chain-of-thought.
106. Confidence != correctness.
107. Risk != certainty.
108. Timeout phải có fallback hoặc explicit failure.
109. Fallback phải policy-controlled.
110. Deterministic mode phải reproducible.
111. Distributed mode phải pin revisions.
112. Decision commit phải atomic.
113. Decision simulation không commit.
114. Counterfactual không sửa production state.
115. Decision outcome phải observable.

---

# 90. Optimization invariants

116. Weighted sum không được dùng khi hard constraints chưa filter.
117. Lexicographic priority phải stable.
118. Pareto dominance phải deterministic.
119. Satisficing threshold phải versioned.
120. Risk model phải versioned.
121. Cost model phải versioned.
122. Benefit model phải versioned.
123. Optimization timeout phải bounded.
124. Search budget phải enforceable.
125. Optimization không được tự tăng budget.
126. Optimizer không được thay đổi objective semantics.
127. Optimizer không được thay đổi authority.
128. Optimizer không được sửa constraints.
129. Approximation phải được đánh dấu.
130. Heuristic result phải distinguishable from exact result.

---

# 91. Safety/governance invariants

131. 603 luôn có authority đối với capability.
132. 639 luôn có authority đối với policy.
133. 646 có thể reject model/decision quality.
134. 647 kiểm soát lifecycle của governed models.
135. Goal không override security.
136. Preference không override security.
137. Utility không override security.
138. Motivation không override security.
139. Self-generated goal không override security.
140. Self-generated objective không tự authorize.
141. Personalization không sửa hard constraints.
142. Learned behavior không tự thành system policy.
143. Inferred user preference không được coi là explicit consent.
144. Delegation không mở rộng authority ngoài grant.
145. Decision engine không tự thay đổi permission.
146. Rollback phải bảo toàn policy boundary.
147. Shadow mode không có production authority.
148. Simulation không có production side effect.
149. Untrusted objective phải sandbox.
150. External model output phải provenance-tagged.

---

# 92. Anti-reward-hacking invariants

151. Metric optimization không đồng nghĩa task success.
152. Proxy metric phải được distinguish.
153. External evaluation phải được hỗ trợ.
154. Counterfactual evaluation phải được hỗ trợ.
155. Reward hacking detector phải có access tới intended outcome.
156. Specification gaming phải được trace.
157. Objective loopholes phải detectable.
158. Model confidence không được suppress evaluation.
159. Self-evaluation không tự certify policy compliance.
160. Evaluation phải có độc lập tương đối với optimizer khi cần.

---

# 93. Persistence invariants

161. Persistent goals phải có lifecycle.
162. Persistent preferences phải có scope.
163. Persistent objective phải có revision.
164. Restart không được duplicate goal.
165. Goal identity phải ổn định.
166. Preference identity phải ổn định.
167. Model revision phải immutable.
168. Rollback phải atomic.
169. Crash recovery phải preserve decision trace.
170. Incomplete decision phải recover về trạng thái rõ ràng.

---

# 94. Distributed invariants

171. Distributed goal update phải versioned.
172. Conflicting revisions phải detectable.
173. Consensus-required decisions phải pin state.
174. Stale objective không được silently commit.
175. Clock assumptions phải explicit.
176. Distributed decision phải có provenance node/agent.
177. Duplicate decision phải idempotent khi contract yêu cầu.
178. Network partition behavior phải policy-defined.
179. Conflict resolution không được hidden.
180. Replicated preference update phải preserve origin.

---

# 95. AI-agent invariants

181. Agent goal không đồng nghĩa agent desire.
182. Agent motivation không chứng minh subjective motivation.
183. Agent utility không chứng minh moral preference.
184. Self-generated goal không chứng minh agency theo nghĩa philosophical.
185. Decision trace phải distinguish requested/planned/authorized/executed.
186. External action attribution phải dựa trên 660.
187. Tool output không tự trở thành objective.
188. User instruction phải preserve scope.
189. Tool-generated recommendation không tự thành user preference.
190. Planner không tự thay policy.
191. Memory không tự trở thành permanent objective.
192. Learned behavior phải versioned.
193. Goal persistence phải explicit.
194. Objective revision phải auditable.
195. Agent cannot mint its own authority.

---

# 96. Privacy invariants

196. Preference data phải có access control.
197. Behavioral inference phải provenance-tagged.
198. Inferred preference không phải consent.
199. Preference retention phải policy-controlled.
200. Preference deletion phải effective.
201. Sensitive preference không được expose qua generic trace.
202. Decision explanation phải redact theo policy.
203. Distributed replication phải respect data scope.
204. Personalization model phải có revision.
205. User preference export phải preserve provenance.

---

# 97. Compiler requirements

Compiler phải:

- validate objective schemas;
- verify constraint precedence;
- type-check utility functions;
- validate goal references;
- validate policy references;
- preserve revisions;
- emit decision metadata;
- reject unauthorized objective binding;
- preserve provenance;
- optimize decision IR without changing semantics.

---

# 98. Static analysis

Compiler diagnostics:

```text
AX661001 Goal has no authority binding
AX661002 Inferred preference used as explicit preference
AX661003 Objective overrides hard constraint
AX661004 Utility model revision missing
AX661005 Decision context contains stale model
AX661006 Self-generated goal lacks policy
AX661007 Goal scope exceeds delegation scope
AX661008 Non-deterministic policy used in deterministic mode
AX661009 Satisficing threshold missing revision
AX661010 Risk model unavailable
AX661011 Hidden objective mutation
AX661012 Preference promoted beyond scope
AX661013 Decision explanation leaks protected data
AX661014 Simulation attempted production commit
AX661015 Optimizer attempted policy mutation
```

---

# 99. Runtime API

```axiom
goal.create(...)
goal.update(...)
goal.progress(...)
goal.conflicts(...)
goal.resolve(...)

preference.read(...)
preference.infer(...)
preference.update(...)
preference.calibrate(...)

utility.evaluate(...)
utility.compare(...)

objective.bind(...)
objective.evaluate(...)
objective.rollback(...)

drive.update(...)
motivation.evaluate(...)

value.evaluate(...)
norm.check(...)

decision.evaluate(...)
decision.select(...)
decision.commit(...)
decision.explain(...)
decision.trace(...)

policy.validate(...)
```

---

# 100. Zero-cost principle

Nếu application không dùng:

```text
goal
preference
utility
motivation
decision
```

compiler phải loại bỏ toàn bộ 661 runtime dependency.

Không được bắt mọi native application link một AI decision runtime.

---

# 101. Static vs dynamic split

Compile-time:

```text
goal schema
objective schema
utility type
policy structure
constraint structure
```

Runtime:

```text
goal state
preference state
world state
utility evaluation
decision
progress
```

Compiler phải constant-fold objective/utility khi có thể.

---

# 102. GPU acceleration

Utility evaluation và Pareto evaluation có thể vectorize.

```text
N candidates × M objectives
```

có thể map:

```text
CPU SIMD
GPU tensor
distributed execution
```

qua 643/614/615.

---

# 103. Memory efficiency

Goal/Preference/Objective IDs nên sử dụng compact handles:

```text
u32/u64
```

Metadata lớn nằm ngoài hot path.

Decision hot path không được dereference deep object graph nếu có thể flatten thành immutable decision context.

---

# 104. Deterministic mode

```text
@decision(deterministic=true)
```

yêu cầu:

- fixed model revisions;
- fixed random seed;
- stable ordering;
- stable floating-point policy;
- deterministic tie-breaking.

---

# 105. Realtime mode

```text
@decision(deadline=2ms)
```

compiler phải enforce:

```text
budget
deadline
fallback
```

Không cho dynamic optimizer chạy vô hạn.

---

# 106. Example

```axiom
@goal
goal BuildArtifact {
    priority = High
    deadline = 30m
}

@objective
objective BuildQuality {
    goal = BuildArtifact
    maximize = quality
}

@objective
objective BuildSpeed {
    goal = BuildArtifact
    maximize = speed
}

@decision_policy(lexicographic)
policy BuildPolicy {
    first = BuildQuality
    second = BuildSpeed
}

decision build = decide(
    policy = BuildPolicy,
    candidates = build_variants
)
```

---

# 107. Preference example

```axiom
@preference(scope=session)
preference CompactOutput {
    target = binary_size
    direction = minimize
    strength = 0.8
}
```

Không được biến preference này thành global system objective.

---

# 108. Self-generated goal example

```axiom
@self_generated_goal
goal ImproveLocalBenchmark {
    scope = current_project
    budget = 30s
    expires = 10m
}
```

Runtime chỉ được activate nếu policy cho phép.

---

# 109. Decision explanation example

```text
Decision: build_variant_3

Hard constraints:
    memory <= 1 GB
    policy = approved

Objectives:
    quality: 0.94
    speed:   0.81
    size:    0.77

Policy:
    lexicographic-v2

Selected because:
    quality objective satisfied at highest priority.

Confidence:
    0.91
```

Đây là structured explanation, không phải chain-of-thought.

---

# 110. Acceptance criteria

BOOTSTRAP-661 được coi là hoàn thành khi:

1. Goal lifecycle implementable.
2. Goal hierarchy implementable.
3. Goal conflict detection implementable.
4. Goal resolution deterministic khi yêu cầu.
5. Preference scope implementable.
6. Preference inference có confidence/provenance.
7. Utility model versioning implementable.
8. Objective binding implementable.
9. Hard/soft distinction enforced.
10. Drive state implementable.
11. Motivation trace implementable.
12. Value model implementable.
13. Normative constraint integration implementable.
14. Weighted optimization implementable.
15. Lexicographic optimization implementable.
16. Pareto optimization implementable.
17. Satisficing implementable.
18. Risk-sensitive decisions implementable.
19. Decision context revision pinning implementable.
20. Decision trace implementable.
21. Decision explanation implementable.
22. Shadow objective update implementable.
23. Rollback implementable.
24. Real-time deadline enforceable.
25. Distributed revision consistency implementable.
26. Simulation cannot mutate production.
27. Self-generated goals bounded.
28. Personalization cannot override hard constraints.
29. Learned preference cannot become explicit consent.
30. Reward hacking evaluation hook exists.
31. Objective drift detectable.
32. Preference drift detectable.
33. Compiler can statically reject invalid bindings.
34. Unused 661 features produce zero runtime dependency.
35. CPU implementation exists.
36. SIMD implementation path exists.
37. GPU provider boundary exists.
38. Native execution has no mandatory third-party runtime.
39. Metadata is inspectable.
40. ≥2,000 tests cover the full contract.

---

# 111. Final architecture position

Sau BOOTSTRAP-661, Axiom AI stack trở thành:

```text
644 Agent Runtime
        │
        ▼
650 Memory
651 Personalization
652 Planning
653 Uncertainty
654 Symbolic Reasoning
655 World Model
656 Embodied Intelligence
657 Cognitive Executive
658 Social Intelligence
659 Affective Intelligence
660 Self / Metacognition
        │
        ▼
661 Goal / Value / Motivation / Decision
        │
        ▼
     Action Plan
        │
        ▼
603 Security
639 Policy
646 Evaluation
647 Governance
        │
        ▼
Execution
```

Điểm quan trọng của 661 là tạo ra **decision substrate**, nhưng không biến objective thành authority, utility thành đạo đức, drive thành desire, hoặc self-model thành consciousness.

**BOOTSTRAP-661 — COMPLETE.**
:::

**Task kế tiếp:** **BOOTSTRAP-662 — Native AI Learning, Adaptation, Online Learning, Reinforcement, Skill Acquisition, Continual Learning & Model Update Runtime 5.0**.