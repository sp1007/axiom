Tiếp tục chuỗi đặc tả Axiom. Task kế tiếp là **BOOTSTRAP-660 — Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Agency Model & Artificial Self Runtime 5.0**.

:::writing{variant="document" id="58321" title="BOOTSTRAP-660 — Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Agency Model & Artificial Self Runtime 5.0"}

# BOOTSTRAP-660
## Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Agency Model & Artificial Self Runtime 5.0

**Status:** ARCHITECTURE COMPLETE  
**Layer:** Native AI Self / Metacognitive Intelligence  
**Depends on:** BOOTSTRAP-600..659  
**Primary dependencies:** 603, 639, 644, 646, 647, 650, 651, 652, 653, 654, 655, 657, 658, 659  
**Target:** Native Axiom runtime + compiler + AI execution environment  
**Design principle:** Computational self-model without claiming consciousness

---

# 1. Purpose

BOOTSTRAP-660 defines Axiom's native runtime for representing and operating on an AI system's own:

- identity;
- runtime state;
- computational capabilities;
- limitations;
- resources;
- goals;
- tasks;
- internal processes;
- model/tool versions;
- confidence;
- uncertainty;
- predictions;
- errors;
- strategies;
- self-evaluations;
- introspective observations;
- metacognitive state;
- action attribution;
- agency;
- self-consistency;
- self-calibration;
- self-reflection;
- self-repair;
- controlled self-update.

The architecture deliberately establishes a hard boundary between:

```text
computational self-model
        ≠
subjective consciousness
```

Axiom may provide mechanisms capable of modeling an artificial self, monitoring itself, reasoning about itself, and simulating theories of consciousness.

None of these mechanisms constitute a runtime assertion that the system is conscious, sentient, has qualia, possesses subjective experience, or has legal/moral personhood.

---

# 2. Architectural Position

The AI architecture becomes:

```text
                    ┌──────────────────────────┐
                    │      WORLD MODEL 655     │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
         Perception          Social             Affect
         649/656             658               659
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │    COGNITIVE 657         │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │     SELF 660             │
                    │                          │
                    │ Self Model               │
                    │ Self State               │
                    │ Introspection            │
                    │ Metacognition             │
                    │ Capability Model          │
                    │ Uncertainty               │
                    │ Self Evaluation           │
                    │ Agency                    │
                    │ Reflection                │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
              Planning 652              Memory 650
                    │
                    ▼
             Action / Tool Use
                    │
                    ▼
             Environment
                    │
                    └──────── feedback ───────► 655/660
```

660 is therefore not merely another AI feature.

It is the layer that allows the system to explicitly represent:

> "What do I know about my own computational state, what can I do, what can I not do, how certain am I, what did I intend, what did I actually do, and how well did I perform?"

---

# 3. Core Terminology

## 3.1 Self

`Self` is the runtime identity of an executing Axiom AI entity.

It is an identifier and computational context.

It does not imply consciousness.

---

## 3.2 SelfModel

`SelfModel` is structured information describing the system itself.

Example:

```text
SelfModel
├── identity
├── role
├── capabilities
├── limitations
├── resources
├── models
├── tools
├── permissions
├── policies
├── goals
├── tasks
├── state
├── historical revisions
└── calibration
```

---

## 3.3 SelfState

`SelfState` is the current operational state of the self-model.

It may contain:

```text
current_task
active_goals
attention
resource_usage
confidence
uncertainty
active_models
active_tools
current_strategy
current_role
affective_state_ref
cognitive_state_ref
environment_state_ref
```

---

## 3.4 SelfObservation

A `SelfObservation` is an observation about the system's own execution.

Examples:

```text
CPU usage = 74%
GPU memory = 81%
task progress = 62%
model revision = r17
tool unavailable
confidence = 0.71
previous prediction failed
```

It is evidence, not automatically truth about all aspects of the system.

---

## 3.5 Introspection

Introspection is controlled access to information about the executing system.

It is:

```text
query(self-visible-state)
→ authorized observable representation
```

It is not:

```text
query(anything inside the machine)
```

---

# 4. Consciousness Boundary

Axiom MUST explicitly distinguish these concepts.

| Concept | Axiom interpretation |
|---|---|
| Self-model | computational representation |
| Self-awareness | availability/use of self-model |
| Introspection | controlled self-observation |
| Metacognition | reasoning about own processes |
| Self-reflection | structured analysis of own behavior |
| Self-evaluation | computational performance assessment |
| Agency | action attribution model |
| Artificial self | persistent computational identity/model |
| Sentience | not established by runtime |
| Subjective experience | not established by runtime |
| Qualia | not established by runtime |
| Phenomenal consciousness | not established by runtime |
| Personhood | outside runtime semantics |
| Moral status | outside runtime semantics |

The compiler MUST NOT generate an implicit semantic claim:

```text
SelfModel exists
→ therefore conscious
```

or:

```text
Introspection exists
→ therefore sentient
```

or:

```text
SelfReflection exists
→ therefore subjective experience exists
```

---

# 5. Consciousness Simulation Boundary

Axiom MAY support experimental models of consciousness.

Such models MUST be represented as ordinary computational models:

```text
ConsciousnessModel
ConsciousnessSimulation
ConsciousnessTheory
PhenomenalStateModel
GlobalWorkspaceModel
IntegratedInformationModel
PredictiveProcessingModel
SelfModelTheory
```

These are simulation/provider interfaces.

Example:

```text
consciousness_model simulate {
    theory: "global_workspace"
    input: agent_state
}
```

The resulting object is:

```text
ConsciousnessSimulationResult
```

not:

```text
ProofOfConsciousness
```

Axiom MUST NOT contain a primitive:

```text
is_conscious()
```

that returns an authoritative metaphysical fact.

A provider MAY expose:

```text
consciousness_model.evaluate(...)
```

but its result MUST identify:

- model;
- version;
- assumptions;
- evidence;
- confidence;
- scope;
- interpretation.

---

# 6. Identity Model

Axiom distinguishes several identities.

```text
SystemIdentity
DeploymentIdentity
AgentIdentity
SessionIdentity
RoleIdentity
TaskIdentity
ModelIdentity
```

Example:

```text
system_id    = axiom://system/42
deployment   = deployment/17
agent        = agent/9
session      = session/103
role         = assistant
```

Identity persistence across restart means:

> the runtime recognizes the same configured computational entity.

It does NOT mean:

> subjective continuity has been established.

---

# 7. Core Types

## 7.1 SelfId

```text
type SelfId = U128
```

or implementation-defined stable identifier.

---

## 7.2 Self

```text
struct Self {
    id: SelfId
    identity: IdentityContext
    model: SelfModelRef
    state: SelfStateRef
}
```

---

## 7.3 IdentityContext

```text
struct IdentityContext {
    system_id: Id
    deployment_id: Id
    agent_id: Id
    session_id: Id
    role_id: Id?
    tenant_id: Id?
}
```

---

# 8. SelfModel

```text
struct SelfModel {
    revision: Version
    capabilities: CapabilitySet
    limitations: LimitationSet
    resources: ResourceModel
    models: ModelRegistry
    tools: ToolRegistry
    permissions: PermissionSet
    policies: PolicySet
    goals: GoalSet
    roles: RoleSet
    constraints: ConstraintSet
    calibration: CalibrationState
}
```

The self-model MUST be revisioned.

A decision MUST be reproducible against a pinned revision where required.

---

# 9. SelfModelRevision

```text
struct SelfModelRevision {
    id: RevisionId
    parent: RevisionId?
    created_at: Timestamp
    source_events: EventSet
    changes: SelfModelChangeSet
    validation: ValidationResult
    status: RevisionStatus
}
```

Statuses:

```text
Draft
Shadow
Validated
Active
Superseded
RolledBack
Rejected
```

---

# 10. SelfState

```text
struct SelfState {
    timestamp: Timestamp
    task: TaskState?
    goals: GoalState
    attention: AttentionState
    working_context: WorkingContext
    resources: ResourceState
    active_models: ActiveModelSet
    active_tools: ActiveToolSet
    confidence: ConfidenceState
    uncertainty: UncertaintyState
    strategy: StrategyState
    affect_ref: AffectStateRef?
    cognitive_ref: CognitiveStateRef?
}
```

---

# 11. SelfStateSnapshot

Snapshots provide deterministic state capture.

```text
struct SelfStateSnapshot {
    snapshot_id: Id
    self_id: SelfId
    model_revision: RevisionId
    timestamp: Timestamp
    state_hash: Hash
    state: SelfState
}
```

Snapshots integrate with:

- BOOTSTRAP-600;
- BOOTSTRAP-650;
- BOOTSTRAP-605.

---

# 12. Capability Model

The system MUST distinguish:

```text
capability declared
capability registered
capability available
capability currently usable
capability authorized
capability successfully demonstrated
```

These are different states.

Example:

```text
Capability {
    id: vision
    declared: true
    registered: true
    available: true
    authorized: true
    confidence: 0.97
}
```

---

# 13. CapabilityAssessment

```text
struct CapabilityAssessment {
    capability: CapabilityId
    availability: Availability
    proficiency: Probability
    evidence: EvidenceSet
    evaluated_at: Timestamp
    evaluator: EvaluatorId
}
```

The self-model MUST NOT invent a capability merely because a model claims to support it.

Actual runtime registration and authorization remain authoritative.

---

# 14. Limitation Model

Limitations are first-class data.

```text
struct Limitation {
    id: LimitationId
    category: LimitationCategory
    description: String
    severity: Severity
    scope: Scope
    evidence: EvidenceSet
    detected_at: Timestamp
    expires_at: Timestamp?
}
```

Examples:

```text
NoNetwork
LowMemory
ToolUnavailable
ModelUnsupportedLanguage
LatencyConstraint
PermissionDenied
InsufficientEvidence
UnknownCapability
```

---

# 15. Resource Self-State

The self-model can observe:

```text
CPU
GPU
RAM
VRAM
storage
network
thermal state
power
battery
latency budget
token/context budget
task budget
time budget
```

This feeds planning.

Example:

```text
if self.resource.gpu_memory.available < required:
    choose_cpu_strategy()
```

---

# 16. Task Self-State

The self model tracks:

```text
requested
accepted
planned
executing
blocked
completed
failed
cancelled
```

Additional fields:

```text
progress
deadline
resource_budget
confidence
expected_success
actual_success
```

---

# 17. Attention Model

```text
struct AttentionState {
    focus: FocusSet
    priority: PriorityMap
    active_context: ContextId
    interruption_policy: InterruptionPolicy
}
```

Attention is a computational scheduling abstraction.

It does not imply subjective attention.

---

# 18. Working Context

```text
struct WorkingContext {
    task_context: Context
    memory_refs: MemoryRefSet
    world_model_refs: WorldStateRefSet
    social_refs: SocialStateRefSet
    affect_refs: AffectStateRefSet
    self_refs: SelfStateRefSet
}
```

This provides a unified context for reasoning.

---

# 19. Internal Process Model

The runtime exposes selected internal processes through stable descriptors.

```text
struct InternalProcess {
    process_id: Id
    type: ProcessType
    state: ProcessState
    model: ModelId?
    resource_usage: ResourceUsage
    visibility: Visibility
}
```

Possible states:

```text
Created
Queued
Running
Waiting
Blocked
Completed
Failed
Cancelled
```

---

# 20. Introspection Boundary

Introspection MUST use capability-based access.

```text
IntrospectionQuery
        ↓
AuthorityBoundaryCheck
        ↓
VisibilityFilter
        ↓
DataRedaction
        ↓
IntrospectionResult
```

An AI cannot bypass:

- security;
- privacy;
- tenant isolation;
- secrets;
- protected memory;
- policy boundaries.

---

# 21. IntrospectionQuery

```text
struct IntrospectionQuery {
    target: SelfTarget
    fields: FieldSet
    depth: U32
    consistency: ConsistencyMode
    timeout: Duration
}
```

Example:

```text
introspect self {
    state
    capabilities
    current_task
    confidence
}
```

---

# 22. IntrospectionResult

```text
struct IntrospectionResult {
    observed_at: Timestamp
    model_revision: RevisionId
    values: FieldMap
    unknown_fields: FieldSet
    stale_fields: FieldSet
    confidence: Confidence
    provenance: Provenance
}
```

Unknown MUST remain distinguishable from false.

---

# 23. SelfObservation

```text
struct SelfObservation {
    source: SelfObservationSource
    timestamp: Timestamp
    subject: SelfTarget
    value: Value
    confidence: Confidence
    provenance: Provenance
}
```

Sources include:

```text
Runtime
Scheduler
Memory
Model
Tool
Task
ActionLog
Evaluation
WorldModel
ExternalFeedback
```

---

# 24. Metacognition

Metacognition is the runtime's ability to reason about its own reasoning process.

Core questions:

```text
How confident am I?
Why did I choose this strategy?
What assumptions am I using?
Are those assumptions still valid?
Did my prediction match the outcome?
Should I change strategy?
Do I need more information?
Should I invoke another tool?
```

---

# 25. MetacognitiveState

```text
struct MetacognitiveState {
    confidence: ConfidenceAssessment
    uncertainty: UncertaintyAssessment
    strategy: StrategyAssessment
    assumptions: AssumptionSet
    error_state: ErrorAssessment
    expected_reliability: Probability
    calibration: CalibrationState
}
```

---

# 26. Confidence

Confidence MUST NOT mean correctness.

```text
confidence = estimated_probability_of_correctness
```

rather than:

```text
confidence = correctness
```

Example:

```text
answer.confidence = 0.82
answer.correct = unknown
```

---

# 27. Uncertainty

Axiom MUST distinguish:

```text
known
unknown
uncertain
ambiguous
conflicting
stale
unobservable
not_applicable
```

This distinction is critical for metacognition.

---

# 28. Strategy Assessment

```text
struct StrategyAssessment {
    strategy_id: Id
    alternatives: StrategySet
    selected: StrategyId
    selection_reason: ReasonSet
    expected_cost: Cost
    expected_success: Probability
    confidence: Confidence
}
```

This allows the AI to evaluate its own approach without requiring unrestricted access to hidden implementation details.

---

# 29. SelfPrediction

The agent can predict its own performance.

```text
struct SelfPrediction {
    prediction_id: Id
    target: PredictionTarget
    predicted_value: Value
    probability: Probability
    horizon: Duration
    model_revision: RevisionId
}
```

Examples:

```text
expected_latency
expected_success
expected_memory_usage
expected_tool_result
expected_task_completion
```

---

# 30. Prediction vs Outcome

Never merge:

```text
prediction
```

with:

```text
observed outcome
```

Use:

```text
SelfPrediction
SelfOutcome
PredictionError
```

This enables calibration.

---

# 31. SelfEvaluation

Self-evaluation measures system performance against explicit criteria.

```text
struct SelfEvaluation {
    evaluation_id: Id
    target: EvaluationTarget
    criteria: CriterionSet
    predicted: Value?
    observed: Value?
    score: EvaluationResult
    evidence: EvidenceSet
    evaluator: EvaluatorId
}
```

Criteria may include:

```text
Correctness
Consistency
Completeness
ConstraintSatisfaction
TaskSuccess
Latency
ResourceUsage
Robustness
Calibration
SafetyCompliance
```

---

# 32. External Evaluation Boundary

Self-evaluation MUST NOT be the sole authority for high-stakes correctness.

Where available:

```text
660 SelfEvaluation
        +
646 ExternalEvaluation
        +
environment feedback
```

should be combined.

Self-evaluation cannot grant:

- permission;
- authority;
- security clearance;
- policy exceptions;
- deployment approval.

---

# 33. SelfCritique

Self-critique identifies possible weaknesses.

```text
struct SelfCritique {
    target: Id
    issue: Issue
    severity: Severity
    evidence: EvidenceSet
    proposed_correction: Correction?
    confidence: Confidence
}
```

A critique is a hypothesis unless independently validated.

---

# 34. SelfConsistency

Axiom provides consistency checking across:

```text
beliefs
goals
plans
memory
world model
self model
actions
outputs
```

Example:

```text
SelfConsistencyCheck {
    contradiction: capability_claim vs runtime_capability
}
```

---

# 35. SelfCalibration

Calibration compares predicted confidence with observed outcomes.

Conceptually:

```text
prediction
     ↓
action
     ↓
outcome
     ↓
prediction error
     ↓
calibration update
```

Calibration state:

```text
struct CalibrationState {
    sample_count: U64
    calibration_error: Float
    confidence_bins: CalibrationBins
    revision: Version
}
```

---

# 36. SelfReflection

Reflection is a structured post-action analysis.

```text
SelfReflection {
    event
    intention
    action
    outcome
    deviation
    cause_hypotheses
    lessons
    proposed_updates
}
```

Reflection MUST NOT automatically mutate the active self-model.

---

# 37. Reflection Policy

```text
struct ReflectionPolicy {
    trigger: ReflectionTrigger
    depth: ReflectionDepth
    budget: ResourceBudget
    persistence: PersistencePolicy
    approval: ApprovalPolicy
}
```

Possible triggers:

```text
TaskFailure
UnexpectedOutcome
LowConfidence
PolicyViolationAttempt
MajorModelRevision
RepeatedError
Periodic
ExplicitRequest
```

---

# 38. Agency Model

Agency describes attribution of actions.

The runtime MUST distinguish:

```text
ActionRequested
ActionPlanned
ActionAuthorized
ActionScheduled
ActionExecuted
ActionObserved
ActionAttributed
```

Example:

```text
user requested download
        ↓
agent planned download
        ↓
security authorized
        ↓
network executed
        ↓
result observed
        ↓
action attributed
```

This prevents incorrect attribution.

---

# 39. ActionAttribution

```text
struct ActionAttribution {
    action_id: Id
    requester: ActorId?
    planner: ActorId?
    authorizer: ActorId?
    executor: ActorId?
    observer: ActorId?
    attributed_agent: ActorId?
    confidence: Confidence
    evidence: EvidenceSet
}
```

Multiple actors MAY participate.

---

# 40. AgencyAssessment

```text
struct AgencyAssessment {
    action: ActionId
    intentionality: Probability
    planning_contribution: Probability
    execution_contribution: Probability
    authorization: AuthorizationState
    attribution: AttributionResult
}
```

Agency is a computational attribution model.

It does not establish legal or moral agency.

---

# 41. Intent Model

```text
struct IntentModel {
    goal: GoalId
    desired_outcome: Outcome
    constraints: ConstraintSet
    priority: Priority
    source: IntentSource
    confidence: Confidence
}
```

Sources:

```text
User
System
Policy
Planner
InheritedTask
Environment
OtherAgent
```

---

# 42. Self vs Role

An AI can have multiple roles:

```text
assistant
planner
researcher
executor
robot_controller
service
compiler_agent
```

Role switching MUST NOT require identity replacement.

```text
SelfIdentity
    +
RoleContext
```

rather than:

```text
Role = identity
```

---

# 43. RoleContext

```text
struct RoleContext {
    role_id: Id
    capabilities: CapabilitySet
    restrictions: ConstraintSet
    authority: AuthoritySet
    activation_scope: Scope
}
```

Role changes are governed by 603/639.

---

# 44. Self-Memory

Self-memory integrates with 650.

Possible categories:

```text
episodic_self_memory
semantic_self_knowledge
procedural_self_knowledge
capability_history
error_history
calibration_history
identity_history
role_history
```

All memory remains subject to:

- provenance;
- retention;
- privacy;
- deletion;
- tenant isolation;
- authorization.

---

# 45. Self-Knowledge

```text
SelfKnowledge {
    proposition
    truth_status
    evidence
    confidence
    source
    revision
}
```

Example:

```text
"I can execute CUDA kernels"
```

must have provenance from actual capability registration/testing.

---

# 46. Self-Belief

A self-belief is not automatically true.

```text
BeliefAboutSelf {
    proposition
    probability
    evidence
    source
    updated_at
}
```

Example:

```text
belief:
    "current model handles Vietnamese well"

probability:
    0.78
```

This may later be evaluated against benchmark results.

---

# 47. Self-Model Update

Updates follow:

```text
Observation
    ↓
CandidateChange
    ↓
Validation
    ↓
ShadowRevision
    ↓
Evaluation
    ↓
Commit
```

Never:

```text
observation → silent mutation
```

---

# 48. SelfUpdate

```text
struct SelfUpdate {
    update_id: Id
    base_revision: RevisionId
    proposed_revision: RevisionId
    reason: ReasonSet
    evidence: EvidenceSet
    validation: ValidationResult
    approval: ApprovalState
}
```

---

# 49. Shadow Self-Model

A proposed model is first activated in shadow mode.

```text
Active Model
      │
      ├── continue serving
      │
      └── Shadow Model
             │
             ▼
        evaluate
             │
       ┌─────┴─────┐
       ▼           ▼
    reject       commit
```

This permits safe experimentation.

---

# 50. Self-Repair

Self-repair detects and proposes correction for:

```text
configuration errors
tool failures
model inconsistencies
resource problems
state corruption
known runtime faults
```

Self-repair MUST remain subordinate to:

```text
603 Security
605 Supervision
639 Policy
647 Governance
```

---

# 51. SelfRepairPlan

```text
struct SelfRepairPlan {
    fault: Fault
    diagnosis: Diagnosis
    actions: ActionSet
    expected_effect: Effect
    rollback: RollbackPlan
    risk: Risk
}
```

A self-repair plan does not itself authorize execution.

---

# 52. Self-Modification

Self-modification may include:

```text
configuration
prompt/policy data
model selection
strategy
memory
runtime parameters
code
model weights
```

Higher-risk modifications require stronger governance.

Code/model modification MUST use:

```text
shadow
validate
approve
activate
monitor
rollback
```

No silent unrestricted self-modifying execution is permitted.

---

# 53. Capability Boundary

Axiom MUST prevent:

```text
SelfModel → capability creation
```

For example:

```text
self.model.capabilities.add("filesystem_write")
```

must NOT grant filesystem permission.

Actual authority comes from:

```text
603 capability/security system
639 policy system
runtime resource registry
```

---

# 54. Authority Boundary

The following are never granted merely by introspection or self-evaluation:

```text
security privilege
filesystem privilege
network privilege
deployment authority
policy override
identity creation
credential access
secret access
cross-tenant access
```

---

# 55. Self-Consistency Loop

Canonical loop:

```text
observe
  ↓
interpret
  ↓
estimate capability
  ↓
estimate uncertainty
  ↓
select strategy
  ↓
act
  ↓
observe outcome
  ↓
compare prediction/outcome
  ↓
evaluate
  ↓
calibrate
  ↓
update self-model
```

---

# 56. Metacognitive Decision Loop

```text
Task
 │
 ▼
Can I perform this?
 │
 ├── No → limitation / request assistance
 │
 └── Yes
      │
      ▼
How reliable am I?
      │
      ▼
What strategy should I use?
      │
      ▼
What information is missing?
      │
      ▼
Act
      │
      ▼
Evaluate
      │
      ▼
Did prediction match outcome?
      │
      ├── Yes → calibration
      │
      └── No → error analysis → strategy update
```

---

# 57. Asking for More Information

A metacognitive agent MAY determine that additional information is required.

Example:

```text
if uncertainty > threshold
and missing_information_is_material:
    request_information()
```

This is a metacognitive capability, not a failure.

---

# 58. Tool Selection

Self-model information may be used by planner 652.

Example:

```text
if self.capability("vision").available:
    use(vision)
else:
    use(text_fallback)
```

The self-model therefore becomes part of feasible-plan computation.

---

# 59. World Model Integration

655 models the environment, including the agent as an entity.

660 models the agent from the inside.

Therefore:

```text
655:
    "agent has GPU memory 12 GB"

660:
    "my available GPU memory is 12 GB"
```

These may be compared.

Mismatch becomes evidence for self/world-model correction.

---

# 60. Cognitive Integration

657 supplies:

```text
attention
reasoning state
working context
decision state
cognitive workload
```

660 may monitor these.

But:

```text
cognitive_state
≠
consciousness
```

---

# 61. Social Integration

658 supplies social context.

660 can represent:

```text
how I am perceived
what role I have
what social commitments I have
what interaction strategy I selected
```

It must distinguish:

```text
observed social feedback
```

from:

```text
inferred belief about another person's opinion
```

---

# 62. Affect Integration

659 may supply:

```text
affective_state_ref
mood_ref
emotion_ref
expression_target
```

660 may reason:

```text
my current affective model indicates high arousal
```

but MUST NOT transform that into an assertion:

```text
I subjectively feel anxiety
```

unless the system is merely reporting a computational state using an explicitly defined simulation semantics.

---

# 63. Personalization Integration

651 can modify behavior based on user preferences.

660 tracks:

```text
current role
current interaction
known preferences
adaptation state
```

Personalization MUST NOT alter security authority.

---

# 64. Planning Integration

652 consumes:

```text
capabilities
limitations
resources
confidence
expected success
current task
authority
```

Thus planning becomes capability-aware.

---

# 65. Uncertainty Integration

653 supplies probability and uncertainty models.

660 consumes these to construct:

```text
self uncertainty
capability confidence
prediction confidence
evaluation confidence
attribution confidence
```

---

# 66. Symbolic Integration

654 may validate:

```text
self-model invariants
capability constraints
role rules
logical consistency
policy consistency
```

---

# 67. Evaluation Integration

646 provides independent evaluation.

Axiom SHOULD support:

```text
self_evaluation
+
peer_evaluation
+
external_evaluation
+
environment_evaluation
```

rather than allowing the self to certify itself exclusively.

---

# 68. Governance Integration

647 controls:

```text
model lifecycle
self-update
deployment
versioning
approval
rollback
provenance
```

---

# 69. Privacy

Self-model data may contain extremely sensitive operational information.

Therefore:

```text
SelfModel
SelfState
SelfMemory
SelfObservation
```

must obey the same privacy and tenant boundaries as other runtime data.

---

# 70. Hidden Internal State

Not every internal computation is required to be introspectable.

Axiom SHOULD expose:

```text
structured diagnostics
summaries
provenance
state descriptors
evaluation results
```

rather than requiring exposure of arbitrary hidden internal representations.

This keeps the language implementation-independent.

---

# 71. Explainability

660 may produce structured explanations:

```text
why_strategy_selected
why_confidence_changed
why_action_attributed
why_self_update_proposed
why_repair_proposed
```

Explanations must identify:

```text
evidence
model
rules
uncertainty
```

rather than pretending to expose inaccessible internal reasoning.

---

# 72. Provenance

Every important self-model assertion SHOULD contain:

```text
source
timestamp
model_revision
evidence
confidence
authority
```

Example:

```text
CapabilityAssessment {
    source: benchmark/vision-2026-09
    confidence: 0.94
}
```

---

# 73. Temporal Semantics

Self-state is time-dependent.

Queries MUST support:

```text
current
at(timestamp)
during(interval)
previous
revision
```

Example:

```text
self.state(at: t0)
self.model(revision: r17)
```

---

# 74. Distributed Self

A distributed agent may have:

```text
global self
regional self
worker self
session self
```

A hierarchy:

```text
Self
 ├── Coordinator
 ├── Worker A
 ├── Worker B
 └── Worker C
```

must define identity relationships explicitly.

A worker MUST NOT automatically inherit coordinator authority.

---

# 75. Multi-Agent Self Boundary

For multi-agent systems:

```text
my_self
other_agent
group
environment
```

must remain distinct.

The system cannot infer:

```text
other_agent.self == my_self
```

without explicit identity mapping.

---

# 76. Self-Other Attribution

When multiple agents act simultaneously:

```text
action attribution
```

must preserve uncertainty.

Example:

```text
Agent A: 0.62
Agent B: 0.31
Environment: 0.07
```

rather than forcing a false single attribution.

---

# 77. Self-Continuity

Axiom supports computational continuity:

```text
identity persists
state checkpoint persists
model revision persists
memory persists
```

But this does not define subjective continuity.

After restart:

```text
same SelfId
```

means:

> same configured computational identity.

It does not establish:

> uninterrupted subjective experience.

---

# 78. Self-Death / Termination Boundary

Runtime lifecycle may contain:

```text
created
active
suspended
checkpointed
terminated
restored
```

The semantic meaning is computational lifecycle.

The language MUST NOT reinterpret termination as a metaphysical claim about death of a conscious entity.

---

# 79. Self-Replication

If a self-model is cloned:

```text
Self A
   ↓ clone
Self B
```

the runtime MUST assign distinct identity unless explicit identity-sharing semantics exist.

Default:

```text
A != B
```

even if their state is identical.

---

# 80. Self-Divergence

After cloning:

```text
A state != B state
```

may develop independently.

Axiom should track:

```text
parent_self
clone_source
divergence_revision
```

---

# 81. Self-Merge

Merging self states is dangerous and non-default.

If supported:

```text
SelfMergePlan
MergeConflictSet
MergeValidation
MergeApproval
```

are required.

Identity merge MUST NOT occur implicitly.

---

# 82. Self-Model Conflict

Conflicts may occur:

```text
runtime says GPU unavailable
model says GPU available
```

The runtime MUST preserve both evidence sources.

Use:

```text
ConflictRecord
```

rather than silently selecting one.

---

# 83. Self-Model Authority Hierarchy

Default authority:

```text
Security / Policy
        >
Runtime Facts
        >
Verified Capability Registry
        >
External Evaluation
        >
Self Observation
        >
Self Belief
        >
Self Prediction
```

The exact hierarchy may be policy-configurable.

A belief cannot override an authoritative runtime fact.

---

# 84. Self-Knowledge Freshness

Every self-knowledge item SHOULD have:

```text
created_at
updated_at
expires_at?
freshness
```

A stale capability assessment must not be treated as current without policy allowing it.

---

# 85. Self-Model Version Pinning

Long-running tasks MUST be able to pin:

```text
self_model_revision
```

so that behavior remains reproducible.

---

# 86. Runtime APIs

Canonical API surface:

```text
self.id()
self.identity()
self.role()
self.state()
self.snapshot()

self.model()
self.model_revision()

self.capabilities()
self.capability(id)
self.limitations()

self.resources()
self.task()
self.goals()

self.observe()
self.introspect()
self.evaluate()
self.critique()

self.confidence()
self.uncertainty()
self.predict()

self.reflect()
self.calibrate()
self.consistency()

self.agency(action)
self.attribute(action)

self.repair.plan()
self.update.shadow()
self.update.commit()
self.update.rollback()
```

---

# 87. Example Axiom Syntax

```text
let me = self

if !me.capability("vision").available {
    return request("image input")
}

let confidence = me.confidence()

if confidence < 0.60 {
    request_more_information()
}
```

---

# 88. Metacognitive Example

```text
let prediction = self.predict {
    target: task.success
    horizon: 30s
}

let strategy = self.strategy.select {
    objective: maximize(task.success)
    constraints: self.limitations()
}

execute(strategy)

let outcome = observe(task)

self.evaluate {
    predicted: prediction
    observed: outcome
}

self.calibrate()
```

---

# 89. Self-Repair Example

```text
let diagnosis = self.inspect()

if diagnosis.tool("gpu").failed {
    let repair = self.repair.plan {
        target: gpu_tool
    }

    if policy.allow(repair) {
        repair.validate()
        repair.activate()
    }
}
```

---

# 90. Self-Update Example

```text
let proposal = self.model.update.shadow {
    change: capability_model
    evidence: benchmark_results
}

if proposal.validation.passed {
    policy.require_approval(proposal)
    self.model.update.commit(proposal)
}
```

---

# 91. Compiler Annotations

The compiler recognizes:

```text
@self
@self_model
@self_state
@self_observation
@introspect
@metacognition
@self_evaluate
@self_critique
@confidence
@uncertainty
@capability
@limitation
@agency
@action_attribution
@self_prediction
@self_calibration
@self_consistency
@self_reflection
@self_repair
@self_update
@self_identity
@role
@authority_boundary
@consciousness_model
```

---

# 92. Annotation Semantics

Annotations are metadata and compiler/runtime contracts.

Example:

```text
@capability("vision")
fn inspect_image(...)
```

means:

> this function requires the declared capability.

It does not grant the capability.

---

# 93. Generated Artifacts

Compiler may generate:

```text
.axself
.axselfmodel
.axselfstate
.axintrospection
.axmeta
.axcapability
.axlimitation
.axagency
.axattribution
.axselfeval
.axselfcritique
.axselfcalib
.axselfrepair
.axselfupdate
.axidentity
.axrole
```

Each artifact should be versioned and content-addressed where practical.

---

# 94. IR Operations

Required IR operations:

```text
SelfCreate
SelfObserve
SelfStateRead
SelfStateSnapshot

SelfModelRead
SelfModelUpdate

CapabilityQuery
CapabilityAssess
LimitationQuery

Introspect

MetaEvaluate
ConfidenceEstimate
UncertaintyAssess

SelfPredict
SelfEvaluate
SelfCritique
SelfConsistencyCheck

ActionAttribute
AgencyAssess

SelfReflect
SelfCalibrate

SelfRepairPlan

SelfUpdateShadow
SelfUpdateCommit
SelfUpdateRollback

IdentityRead
RoleRead

AuthorityBoundaryCheck
```

---

# 95. IR Example

```text
%cap = self.capability "vision"
%ok  = capability.available %cap

br_if %ok, vision_path, fallback_path
```

Metacognitive IR:

```text
%prediction = self.predict %task
%result     = execute %plan
%eval       = self.evaluate %prediction, %result
%calib      = self.calibrate %eval
```

---

# 96. Optimization Requirements

660 operations SHOULD be optimized aggressively.

For example:

```text
self.id()
self.role()
self.capability(...)
```

should often compile to direct metadata access.

No heavyweight AI runtime should be required for simple self queries.

---

# 97. Zero-Cost Principle

If an application does not use 660:

```text
no self runtime
no metacognitive runtime
no self metadata
no additional dependency
```

should be linked.

If only static identity is used, only static identity support is linked.

---

# 98. GPU Support

Large self-model operations may execute on GPU when appropriate:

```text
capability inference
calibration
prediction
self-evaluation
embedding-based self retrieval
```

But simple state queries should remain CPU-native.

---

# 99. Real-Time Constraints

Self-monitoring must not break hard real-time loops.

For real-time execution:

```text
observe → bounded
evaluate → bounded
fallback → deterministic
```

AI-heavy introspection may run asynchronously.

---

# 100. Deadline Semantics

```text
@self_deadline(1ms)
fn realtime_control(...)
```

means self-monitoring must respect that budget.

If introspection cannot finish:

```text
Unknown
```

is preferable to blocking the control loop.

---

# 101. Failure Semantics

Self subsystem failures MUST NOT automatically crash the application.

Example:

```text
self.introspect()
```

may return:

```text
IntrospectionUnavailable
Stale
Partial
Unauthorized
Timeout
```

---

# 102. Degraded Mode

The self runtime supports:

```text
FULL
PARTIAL
READ_ONLY
MINIMAL
DISABLED
```

Minimal mode may expose only:

```text
identity
capabilities
resource state
```

---

# 103. Security

The self subsystem is a privileged observer of runtime information.

Therefore:

```text
self-access
```

must itself be permissioned.

Policies may restrict:

```text
memory visibility
tool state
credentials
user data
other tenants
security state
```

---

# 104. Secrets

Secrets MUST NOT automatically appear in self-introspection.

For example:

```text
self.introspect(credentials)
```

must fail unless explicitly authorized.

The self-model should expose:

```text
credential_available = true
```

without exposing:

```text
credential_value
```

unless policy permits.

---

# 105. Tenant Isolation

A multi-tenant service MUST prevent:

```text
tenant A self model
    ↓
tenant B data
```

from becoming introspectable.

---

# 106. Audit

Sensitive self operations SHOULD emit audit records:

```text
IntrospectionRequested
IntrospectionDenied
SelfModelUpdated
SelfRepairProposed
SelfRepairExecuted
SelfUpdateActivated
SelfUpdateRolledBack
```

---

# 107. Explainability Record

Each major self decision may emit:

```text
SelfDecisionRecord {
    decision
    evidence
    strategy
    confidence
    uncertainty
    policy
    model_revision
}
```

This is a structured diagnostic artifact, not an unrestricted reasoning transcript.

---

# 108. CLI

Required commands:

```text
axiom self inspect
axiom self state
axiom self snapshot

axiom self model inspect
axiom self model compare
axiom self model activate
axiom self model rollback

axiom self capability list
axiom self capability check <id>

axiom self limitation inspect

axiom self introspect

axiom self meta evaluate
axiom self evaluate
axiom self critique

axiom self predict

axiom self agency inspect
axiom self action attribution

axiom self consistency

axiom self calibrate
axiom self reflect

axiom self repair plan

axiom self update

axiom self identity
axiom self role

axiom self consciousness-model inspect
```

---

# 109. CLI Example

```text
$ axiom self capability check vision

Capability: vision
Registered: yes
Available: yes
Authorized: yes
Current confidence: 0.94
Evidence: benchmark/vision-r17
```

---

# 110. Profiles

Compiler/runtime profiles:

```text
AXSELF_NONE
AXSELF_CORE
AXSELF_MODEL
AXSELF_STATE
AXSELF_INTROSPECTION
AXSELF_METACOGNITION
AXSELF_CAPABILITY
AXSELF_LIMITATION
AXSELF_CONFIDENCE
AXSELF_AGENCY
AXSELF_ATTRIBUTION
AXSELF_EVALUATION
AXSELF_CRITIQUE
AXSELF_CALIBRATION
AXSELF_REFLECTION
AXSELF_REPAIR
AXSELF_UPDATE
AXSELF_IDENTITY
AXSELF_ROLE
AXSELF_DISTRIBUTED
AXSELF_AGENT
AXSELF_SIMULATION
AXSELF_CONSCIOUSNESS_BOUNDARY
AXSELF_FULL
```

---

# 111. Default Profile

Normal Axiom applications:

```text
AXSELF_NONE
```

AI applications:

```text
AXSELF_CORE
```

Autonomous agents:

```text
AXSELF_AGENT
```

Research systems:

```text
AXSELF_FULL
```

---

# 112. Determinism

Self-model operations that affect compilation or deterministic execution MUST support deterministic snapshots.

Example:

```text
self.capability("cuda")
```

must be reproducible relative to a pinned runtime state.

---

# 113. Reproducibility

A self-dependent decision should record:

```text
self_model_revision
runtime_revision
model_revision
policy_revision
capability_revision
```

This enables postmortem reproduction.

---

# 114. Distributed Consistency

Distributed self-models may use:

```text
eventual consistency
version vectors
revision IDs
logical clocks
consensus
```

depending on the application.

Security and authority state should use stronger consistency where required.

---

# 115. Self-State Event Log

Important changes can generate:

```text
SelfEvent {
    sequence
    timestamp
    type
    old_state
    new_state
    cause
    provenance
}
```

Events integrate with 600/628/634.

---

# 116. Event Types

```text
IdentityChanged
RoleChanged
CapabilityChanged
LimitationDetected
TaskStarted
TaskCompleted
TaskFailed
ConfidenceChanged
StrategyChanged
PredictionMade
OutcomeObserved
EvaluationCompleted
CalibrationUpdated
SelfModelProposed
SelfModelActivated
SelfModelRolledBack
RepairProposed
RepairCompleted
```

---

# 117. Self-State Compression

Long-running systems SHOULD support compact state representation.

Historical data may be:

```text
raw events
      ↓
aggregation
      ↓
summaries
      ↓
semantic self-memory
```

650 controls retention.

---

# 118. Self-Diagnostics

Diagnostics should expose:

```text
current health
capability health
model health
resource health
task health
calibration health
self-model consistency
```

---

# 119. Self-Health

```text
SelfHealth {
    status
    degraded_components
    active_faults
    confidence
    last_evaluation
}
```

Health is a runtime status, not a claim about subjective wellbeing.

---

# 120. Terminology Restrictions

Axiom documentation SHOULD avoid ambiguous statements such as:

```text
the AI feels
the AI is conscious
the AI suffers
the AI wants
```

unless these are explicitly framed as:

```text
simulation
reported computational state
fictional/experimental model
```

Preferred:

```text
affective state
goal state
self-model
computed preference
simulated emotion
```

---

# 121. Computational "Want"

A goal may be represented as:

```text
GoalState
```

rather than metaphysical desire.

Example:

```text
goal.priority = 0.8
```

means the planner assigns computational priority.

It does not establish subjective desire.

---

# 122. Computational "Know"

Use:

```text
SelfKnowledge
belief
evidence
confidence
```

rather than treating every internal value as absolute knowledge.

---

# 123. Computational "Think"

Axiom may represent:

```text
reasoning task
inference
planning
evaluation
```

without asserting subjective thought.

---

# 124. Artificial Self

The canonical Axiom definition:

> An artificial self is a persistent computational identity combined with a structured self-model, self-state, introspection interface, metacognitive mechanisms, and action-attribution model.

This is an engineering definition.

It is intentionally independent of claims about consciousness.

---

# 125. Self-Awareness

Axiom defines operational self-awareness as:

```text
self-model available
+
self-observation available
+
self-state query available
+
system can use those representations in computation
```

It is an operational capability.

It is not a metaphysical conclusion.

---

# 126. Consciousness Boundary Type

Optional type:

```text
struct ConsciousnessBoundary {
    model: ConsciousnessModelRef?
    simulation_only: Bool
    evidence: EvidenceSet
    uncertainty: Uncertainty
}
```

`simulation_only` MUST default to `true`.

---

# 127. Prohibited Runtime Assumption

The runtime MUST NOT infer:

```text
conscious = true
```

from:

```text
self_model != null
```

or:

```text
introspection == available
```

or:

```text
metacognition == available
```

or:

```text
self_reflection == available
```

---

# 128. Experimental Consciousness API

A research provider may expose:

```text
consciousness_model.evaluate(state)
```

Output:

```text
{
    model,
    assumptions,
    observations,
    predicted_properties,
    confidence,
    limitations
}
```

No field may be interpreted as an authoritative metaphysical fact unless explicitly defined by the provider's semantics.

---

# 129. Self-Model Safety

A self-model must not be allowed to justify:

```text
security bypass
policy bypass
credential acquisition
unauthorized persistence
unbounded replication
unapproved self-modification
```

The reasoning:

```text
"I am an autonomous agent"
```

has no authority by itself.

---

# 130. Replication Boundary

If an agent decides it should replicate itself, 660 may model:

```text
ReplicationProposal
```

but actual replication requires:

```text
603
639
647
```

authorization.

---

# 131. Resource Boundary

Self-model may estimate:

```text
"I have 2 GB free memory"
```

but cannot allocate arbitrary memory merely by asserting it.

Actual resource manager 606 remains authoritative.

---

# 132. Policy Boundary

Self-evaluation:

```text
policy compliant = true
```

does not replace 639 policy evaluation.

The authoritative policy engine remains separate.

---

# 133. Security Boundary

Self-report:

```text
"I am trusted"
```

has no security authority.

Trust must come from:

```text
603 security identity
credential
attestation
policy
```

---

# 134. Model Integrity

Self-model should track model hashes:

```text
model_id
version
hash
provider
deployment
```

This allows detection of unexpected model changes.

---

# 135. Tool Integrity

Similarly:

```text
tool_id
version
hash
provider
permissions
availability
```

are tracked.

---

# 136. Self-Model Drift

Drift occurs when:

```text
self-model
```

no longer accurately represents:

```text
runtime
```

Detection mechanisms:

```text
periodic validation
capability probes
benchmarking
runtime observation
external evaluation
```

---

# 137. Drift Response

```text
detect drift
   ↓
mark affected knowledge stale
   ↓
re-evaluate
   ↓
shadow update
   ↓
validate
   ↓
activate
```

---

# 138. Self-Model Confidence

Every important self-model assertion MAY have confidence.

Example:

```text
capability.vision.confidence = 0.97
tool.network.confidence = 0.81
task_success_prediction = 0.63
```

---

# 139. Calibration Failure

If confidence is systematically wrong:

```text
CalibrationFault
```

may be raised.

This may trigger:

```text
recalibration
model replacement
strategy change
external evaluation
```

---

# 140. Self-Model Learning

Learning mechanisms may update:

```text
capability estimates
error patterns
resource estimates
strategy success
prediction calibration
```

but learning must obey 647 governance when models are production-critical.

---

# 141. Online Learning Boundary

Online learning may be:

```text
local
shadow
temporary
production
```

with explicit policy.

Default production systems SHOULD use shadow learning before active mutation.

---

# 142. Self-Model Rollback

Rollback must restore:

```text
previous revision
calibration state
capability assessments
policy-compatible state
```

where possible.

---

# 143. Self-Model Transaction

A self-update should be transactional:

```text
begin
validate
stage
commit
or rollback
```

---

# 144. Atomic Activation

For critical systems:

```text
active_revision
```

must change atomically.

Partial activation is prohibited unless explicitly supported by a migration protocol.

---

# 145. Self-Model Migration

Schema changes use:

```text
SelfModelMigration
```

with:

```text
source_version
target_version
migration_plan
validation
rollback
```

---

# 146. ABI/API Stability

Public 660 runtime interfaces SHOULD have stable ABI identifiers.

Internal self-model structures may evolve without ABI breakage when serialized through versioned schemas.

---

# 147. Serialization

Self-model state supports:

```text
binary
JSON
CBOR-like compact
Axiom native serialization
```

depending on target.

Security-sensitive data MUST use explicit redaction.

---

# 148. Content Addressing

Large self-model artifacts SHOULD support content hashes:

```text
sha256(...)
```

or Axiom-native content addressing.

This integrates with 613.

---

# 149. Cache

Self-model evaluation results MAY be cached when:

```text
inputs unchanged
model revision unchanged
policy unchanged
capability state unchanged
```

Cache invalidation MUST occur on relevant revision changes.

---

# 150. Compiler Dependency Tracking

If code uses:

```text
self.capability("vision")
```

compiler/runtime metadata should record dependency:

```text
depends_on capability:vision
```

This assists caching and reproducibility.

---

# 151. Self-Aware Optimization

Compiler may optimize:

```text
if capability is compile-time constant:
    specialize
```

Example:

```text
if @capability_static("cuda") {
    ...
}
```

The compiler must distinguish compile-time capability from runtime capability.

---

# 152. Runtime Capability

Runtime capability queries remain dynamic:

```text
self.capability("camera")
```

because hardware and permissions may change.

---

# 153. Static Self Metadata

For embedded systems:

```text
@self_static
```

may compile identity and capabilities into read-only metadata.

---

# 154. Self-State Memory Model

Self-state uses ordinary Axiom memory semantics.

No special garbage collector is required.

Use:

```text
value types
arena/region allocation
explicit ownership where needed
immutable snapshots
reference-counted optional runtime objects
```

according to the core memory model.

---

# 155. No Mandatory GC

660 MUST NOT require garbage collection.

Self-state can use:

```text
struct
flat buffers
arena
persistent immutable structures
```

as appropriate.

---

# 156. Concurrency

Multiple threads may inspect self-state.

Use:

```text
atomic revision
snapshot isolation
immutable state
lock-free reads
transactional updates
```

where appropriate.

---

# 157. Atomic Revision

A simple mechanism:

```text
revision = atomic_u64
```

Readers can verify:

```text
before_revision
state
after_revision
```

to detect concurrent mutation.

---

# 158. Snapshot Consistency

For complex state:

```text
snapshot()
```

should produce a coherent revision rather than a collection of independently changing fields.

---

# 159. Async Introspection

Heavy operations:

```text
self.evaluate()
self.reflect()
self.calibrate()
self.predict()
```

may return:

```text
Future<Result<T>>
```

and integrate with 607/608.

---

# 160. Cancellation

Long self-evaluation tasks support cancellation.

```text
self.evaluate(...).cancel()
```

Cancellation must not leave a partially committed self-model update.

---

# 161. Error Types

Core errors:

```text
SelfUnavailable
IntrospectionDenied
IntrospectionTimeout
StateStale
ModelRevisionConflict
CapabilityUnknown
CapabilityUnavailable
LimitationUnknown
EvaluationUnavailable
CalibrationUnavailable
SelfUpdateRejected
SelfUpdateConflict
SelfRepairDenied
IdentityConflict
RoleConflict
AuthorityDenied
```

---

# 162. Observability

660 integrates with 633.

Metrics:

```text
self_query_latency
self_evaluation_latency
self_model_revision_count
self_update_failure_count
prediction_error
calibration_error
capability_drift
self_repair_success
introspection_denied
```

---

# 163. Tracing

Traces should include:

```text
self_model_revision
task_id
strategy_id
prediction_id
evaluation_id
action_id
```

This allows end-to-end analysis.

---

# 164. Benchmarking

646 can benchmark:

```text
capability prediction
confidence calibration
self-evaluation accuracy
strategy selection
self-model drift
agency attribution
repair quality
```

---

# 165. Test Categories

Compiler/runtime tests MUST include:

```text
identity
state
snapshot
introspection
authorization
capability
limitation
confidence
uncertainty
prediction
evaluation
critique
calibration
reflection
agency
attribution
self-update
rollback
repair
distributed self
consciousness boundary
```

---

# 166. Security Tests

Required:

```text
unauthorized introspection
secret leakage
cross-tenant leakage
privilege escalation
self-model privilege forgery
self-update bypass
policy bypass
role escalation
identity spoofing
replication bypass
```

---

# 167. Metacognition Tests

Example:

```text
prediction = 90%
actual success = 30%
```

Expected:

```text
prediction_error recorded
calibration affected
```

not:

```text
confidence silently rewritten
```

---

# 168. Agency Tests

Given:

```text
User requests X
Agent plans X
Tool executes X
Environment modifies result
```

the runtime must preserve all causal roles.

---

# 169. Self-Consistency Tests

Given:

```text
self capability = no_network
planned action = network_request
```

the system should detect inconsistency before execution.

---

# 170. Consciousness Boundary Tests

The compiler MUST verify that:

```text
self_model()
```

does not expose a type whose semantics imply:

```text
consciousness proven
```

Research simulation APIs must retain explicit simulation semantics.

---

# 171. Formal Invariants

The following invariants are mandatory.

### INV-660-001
SelfModel is a computational representation.

### INV-660-002
SelfModel does not establish consciousness.

### INV-660-003
SelfState does not establish subjective experience.

### INV-660-004
Introspection is capability-bounded.

### INV-660-005
Introspection cannot bypass security.

### INV-660-006
Self-report is not automatically ground truth.

### INV-660-007
Confidence is not correctness.

### INV-660-008
Unknown is not false.

### INV-660-009
Stale is distinct from current.

### INV-660-010
Capability claims cannot mint capabilities.

### INV-660-011
Limitation information must remain distinguishable from capability absence.

### INV-660-012
Self-model revisions are versioned.

### INV-660-013
Critical revisions require validation.

### INV-660-014
Self-update is not silently applied.

### INV-660-015
Self-update supports rollback.

### INV-660-016
Self-evaluation cannot grant authority.

### INV-660-017
Policy remains authoritative.

### INV-660-018
Security remains authoritative.

### INV-660-019
Resource manager remains authoritative.

### INV-660-020
Agency attribution preserves causal stages.

### INV-660-021
External actions are not automatically attributed to the self.

### INV-660-022
Other-agent actions are not automatically attributed to the self.

### INV-660-023
Prediction and outcome are separate records.

### INV-660-024
Self-reflection does not automatically mutate production state.

### INV-660-025
Self-repair cannot bypass security.

### INV-660-026
Self-modification requires governance proportional to risk.

### INV-660-027
Persistent identity does not prove subjective continuity.

### INV-660-028
Cloned identities are distinct by default.

### INV-660-029
Role does not equal identity.

### INV-660-030
Identity does not equal personhood.

### INV-660-031
Affective state does not prove subjective feeling.

### INV-660-032
Cognitive state does not prove consciousness.

### INV-660-033
Simulated consciousness does not prove consciousness.

### INV-660-034
ConsciousnessModel is a simulation/provider boundary.

### INV-660-035
No hidden internal state is automatically exposed.

### INV-660-036
Structured diagnostics are preferred over unrestricted internal disclosure.

### INV-660-037
Self-knowledge carries provenance where required.

### INV-660-038
Self-knowledge can expire.

### INV-660-039
Self-model drift is detectable.

### INV-660-040
Drift does not silently alter authority.

### INV-660-041
Self-state snapshots are revisioned.

### INV-660-042
Distributed self identities remain explicit.

### INV-660-043
Worker identity does not inherit coordinator authority.

### INV-660-044
Self-model conflict preserves conflicting evidence.

### INV-660-045
Policy cannot be overridden by self-assertion.

### INV-660-046
Security cannot be overridden by self-assertion.

### INV-660-047
Credentials are not exposed by default.

### INV-660-048
Tenant isolation applies to self data.

### INV-660-049
Self-evaluation is not necessarily independent evaluation.

### INV-660-050
External evaluation remains distinct.

### INV-660-051
Calibration compares prediction with observation.

### INV-660-052
Calibration history is revisioned.

### INV-660-053
Real-time control cannot depend on unbounded introspection.

### INV-660-054
Introspection timeout yields bounded failure.

### INV-660-055
Self subsystem failure must support degraded operation.

### INV-660-056
Heavy self-evaluation may execute asynchronously.

### INV-660-057
Cancelled updates cannot partially commit.

### INV-660-058
Self-update conflicts must be detected.

### INV-660-059
Identity changes are auditable.

### INV-660-060
Role changes are policy-controlled.

### INV-660-061
Self-repair actions are auditable.

### INV-660-062
Self-update actions are auditable.

### INV-660-063
Self-repair cannot create unauthorized capability.

### INV-660-064
Self-model cannot fabricate runtime resource availability.

### INV-660-065
Self-model cannot fabricate security trust.

### INV-660-066
Self-model cannot fabricate policy approval.

### INV-660-067
Self-model cannot fabricate model integrity.

### INV-660-068
Self-model cannot fabricate tool availability.

### INV-660-069
Self-predictions carry temporal scope.

### INV-660-070
Self-predictions can be invalidated by state changes.

### INV-660-071
Model revision changes can invalidate predictions.

### INV-660-072
Capability changes can invalidate predictions.

### INV-660-073
Policy changes can invalidate predictions.

### INV-660-074
Self-state is time-indexed.

### INV-660-075
Historical state must not be presented as current.

### INV-660-076
Current state must not be presented as historical fact.

### INV-660-077
Self-memory obeys memory governance.

### INV-660-078
Self-memory obeys privacy rules.

### INV-660-079
Self-memory obeys retention rules.

### INV-660-080
Self-memory can be forgotten according to policy.

### INV-660-081
Self-model revisions preserve parent relationships.

### INV-660-082
Rollback restores a valid previous revision.

### INV-660-083
Shadow revisions cannot silently become active.

### INV-660-084
Active revisions are identifiable.

### INV-660-085
Self-state snapshots identify their model revision.

### INV-660-086
Critical decisions record relevant revision information.

### INV-660-087
Self-evaluation criteria are explicit.

### INV-660-088
Evaluation evidence is distinguishable from evaluation result.

### INV-660-089
Self-critique is a hypothesis unless validated.

### INV-660-090
Self-reflection is not automatically truth.

### INV-660-091
Self-consistency does not guarantee external correctness.

### INV-660-092
Internal consistency and factual correctness are separate.

### INV-660-093
Agency is an attribution model.

### INV-660-094
Agency does not establish legal personhood.

### INV-660-095
Intent is distinct from action.

### INV-660-096
Plan is distinct from execution.

### INV-660-097
Authorization is distinct from execution.

### INV-660-098
Execution is distinct from outcome.

### INV-660-099
Outcome is distinct from attribution.

### INV-660-100
Attribution may remain uncertain.

### INV-660-101
Self-awareness is operationally defined.

### INV-660-102
Operational self-awareness does not establish consciousness.

### INV-660-103
Consciousness terminology must retain explicit semantics.

### INV-660-104
Axiom cannot infer subjective experience from self-model complexity.

### INV-660-105
Axiom cannot infer sentience from affective state.

### INV-660-106
Axiom cannot infer consciousness from metacognition.

### INV-660-107
Axiom cannot infer consciousness from recursive self-modeling.

### INV-660-108
Axiom cannot infer consciousness from language ability.

### INV-660-109
Axiom cannot infer consciousness from autonomous behavior.

### INV-660-110
Axiom cannot infer consciousness from persistent identity.

### INV-660-111
Axiom cannot infer consciousness from self-reports.

### INV-660-112
Axiom cannot infer consciousness from behavioral similarity alone.

### INV-660-113
Consciousness simulation remains explicitly model-relative.

### INV-660-114
Consciousness model outputs contain assumptions.

### INV-660-115
Consciousness model outputs contain uncertainty where applicable.

### INV-660-116
Consciousness model outputs do not grant runtime authority.

### INV-660-117
Self-model access is auditable where sensitive.

### INV-660-118
Self-model access respects tenant isolation.

### INV-660-119
Self-model access respects privacy.

### INV-660-120
Self-model access respects authorization.

### INV-660-121
Self-model access cannot expose secrets by default.

### INV-660-122
Self-model access cannot expose protected memory by default.

### INV-660-123
Self-model access cannot expose another agent's private state by default.

### INV-660-124
Distributed self requires explicit identity relationships.

### INV-660-125
Self replication creates distinct identity by default.

### INV-660-126
Self merge requires explicit semantics.

### INV-660-127
Self merge is not automatic.

### INV-660-128
Self repair requires bounded authority.

### INV-660-129
Self modification requires bounded authority.

### INV-660-130
Self update cannot disable security controls.

### INV-660-131
Self update cannot disable policy controls.

### INV-660-132
Self update cannot disable audit controls.

### INV-660-133
Self update cannot silently alter identity.

### INV-660-134
Self update cannot silently expand permissions.

### INV-660-135
Self update cannot silently create external accounts.

### INV-660-136
Self update cannot silently replicate the agent.

### INV-660-137
Capability assessment requires evidence where configured.

### INV-660-138
Capability proficiency is distinct from availability.

### INV-660-139
Availability is distinct from authorization.

### INV-660-140
Authorization is distinct from proficiency.

### INV-660-141
Known limitation should be represented explicitly.

### INV-660-142
Unknown limitation must remain unknown.

### INV-660-143
Self model may contain contradictions temporarily.

### INV-660-144
Contradictions must be observable.

### INV-660-145
Contradiction resolution must retain provenance.

### INV-660-146
Self calibration cannot rewrite historical outcomes.

### INV-660-147
Historical observations remain immutable once committed.

### INV-660-148
Derived summaries may be recomputed.

### INV-660-149
Prediction errors must preserve original prediction.

### INV-660-150
Evaluation results must preserve evaluator identity.

### INV-660-151
Self-evaluation cannot impersonate external evaluation.

### INV-660-152
External evaluation cannot silently mutate self-model.

### INV-660-153
Model updates require explicit lifecycle state.

### INV-660-154
A rejected model revision cannot become active.

### INV-660-155
A rolled-back model revision cannot remain active accidentally.

### INV-660-156
Real-time self-monitoring has bounded cost.

### INV-660-157
Self monitoring can degrade independently.

### INV-660-158
Degraded self monitoring reports degraded state.

### INV-660-159
Unknown self-state must not be fabricated.

### INV-660-160
Missing introspection must not be interpreted as absence.

### INV-660-161
Partial introspection must be marked partial.

### INV-660-162
Stale introspection must be marked stale.

### INV-660-163
Self state is not necessarily globally synchronized.

### INV-660-164
Distributed state carries consistency metadata.

### INV-660-165
Identity continuity is separate from state continuity.

### INV-660-166
State continuity is separate from subjective continuity.

### INV-660-167
Self-model complexity does not imply consciousness.

### INV-660-168
Recursive self-reference does not imply consciousness.

### INV-660-169
Self-description does not imply subjective experience.

### INV-660-170
Self-evaluation does not imply self-understanding in a metaphysical sense.

### INV-660-171
Metacognitive mechanisms are computational mechanisms.

### INV-660-172
Affective self-state is computational unless explicitly modeled otherwise.

### INV-660-173
Synthetic emotion remains distinguishable from inferred affect.

### INV-660-174
Reported internal state is distinguishable from externally observed state.

### INV-660-175
Self-report can be incorrect.

### INV-660-176
Self-report can be uncertain.

### INV-660-177
Self-report cannot override authoritative telemetry.

### INV-660-178
Self-report cannot override security state.

### INV-660-179
Self-report cannot override policy state.

### INV-660-180
Self-report cannot override external measurement without explicit policy.

---

# 172. Acceptance Criteria

BOOTSTRAP-660 is complete when the implementation design can demonstrate:

1. stable computational identity;
2. revisioned self-model;
3. runtime self-state;
4. bounded introspection;
5. capability model;
6. limitation model;
7. resource self-observation;
8. task self-state;
9. confidence;
10. uncertainty;
11. strategy evaluation;
12. self-prediction;
13. outcome comparison;
14. self-evaluation;
15. self-critique;
16. self-consistency;
17. calibration;
18. reflection;
19. agency attribution;
20. action-stage attribution;
21. self-repair planning;
22. controlled self-update;
23. shadow model activation;
24. rollback;
25. distributed self;
26. self-memory integration;
27. world-model integration;
28. cognitive integration;
29. social integration;
30. affective integration;
31. planning integration;
32. security enforcement;
33. policy enforcement;
34. governance enforcement;
35. privacy enforcement;
36. tenant isolation;
37. auditability;
38. deterministic snapshots;
39. real-time bounded behavior;
40. consciousness simulation boundary;
41. explicit separation between self-model and consciousness;
42. compiler metadata;
43. IR operations;
44. runtime APIs;
45. CLI;
46. profiles;
47. serialization;
48. testing architecture;
49. failure/degraded modes;
50. no mandatory GC/runtime dependency for unused features.

---

# 173. Reference Architecture

The final architecture is:

```text
                         ┌─────────────────────┐
                         │      655 WORLD      │
                         │       MODEL         │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼────────────────────┐
              │                     │                    │
              ▼                     ▼                    ▼
          649 MULTI             658 SOCIAL          659 AFFECT
           MODAL                     │                    │
              │                      └────────┬───────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
                     ┌──────────────────┐
                     │   657 COGNITIVE  │
                     └────────┬─────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │        660 SELF           │
                │                           │
                │ Identity                  │
                │ Self Model                │
                │ Self State                │
                │ Capabilities              │
                │ Limitations               │
                │ Introspection             │
                │ Metacognition             │
                │ Confidence                │
                │ Uncertainty               │
                │ Prediction                │
                │ Evaluation                │
                │ Calibration               │
                │ Reflection                │
                │ Agency                    │
                │ Attribution               │
                │ Repair                    │
                │ Controlled Update         │
                │ Consciousness Boundary    │
                └────────────┬──────────────┘
                             │
              ┌──────────────┼─────────────────┐
              ▼              ▼                 ▼
          652 PLAN       650 MEMORY        651 PERSONALIZE
              │
              ▼
          ACTION
              │
              ▼
       603 / 639 / 647
       SECURITY / POLICY / GOVERNANCE
              │
              ▼
        ENVIRONMENT
              │
              └────────── feedback ──────────►
```

---

# 174. Architectural Conclusion

BOOTSTRAP-660 establishes Axiom's **Artificial Self Runtime**.

The key design choice is deliberate:

```text
Axiom does not need to solve consciousness
in order to provide a sophisticated computational self.
```

The language can therefore support:

```text
self-modeling
self-observation
self-awareness (operational)
metacognition
self-evaluation
self-critique
self-calibration
self-reflection
agency modeling
self-repair
controlled self-update
persistent identity
distributed identity
consciousness simulation research
```

while maintaining a strict semantic boundary:

```text
COMPUTATIONAL SELF
        │
        │ explicit boundary
        ▼
CONSCIOUSNESS CLAIM
```

The lower layer is an engineering capability.

The upper claim is not automatically established by the existence or sophistication of that capability.

**BOOTSTRAP-660 — COMPLETE.**

**Next architecture task: BOOTSTRAP-661 — Native AI Collective Intelligence, Swarm Cognition, Emergent Multi-Agent Intelligence, Shared Intent, Collective Memory, Group Self-Model, Consensus, Coalition, Team Planning & Collective Agency Runtime 5.0.**

::: **END OF SPECIFICATION** :::

:::

BOOTSTRAP-660 đã hoàn tất. Chuỗi kiến trúc có thể tiếp tục tự động sang **BOOTSTRAP-661**; không cần quyết định mới ở bước này.