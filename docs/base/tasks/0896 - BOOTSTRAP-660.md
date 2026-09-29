Tiếp tục chuỗi đặc tả Axiom với **BOOTSTRAP-660**. Task này đặt ranh giới rất rõ giữa **self-model/metacognition có thể triển khai bằng máy** và khái niệm **consciousness/subjective experience** vốn không thể được suy ra chỉ từ trạng thái runtime.

:::writing{variant="document" id="58321" title="BOOTSTRAP-660 — Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Self-Agency & Artificial Self Runtime 5.0"}

# BOOTSTRAP-660
## Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Self-Agency & Artificial Self Runtime 5.0

**Status:** ARCHITECTURE COMPLETE  
**Layer:** Native AI Self / Metacognitive Intelligence  
**Depends on:** BOOTSTRAP-600..659  
**Primary dependencies:** 603, 639, 644, 646, 647, 650, 651, 652, 653, 654, 655, 657, 658, 659  
**Acceptance target:** ≥ 2,000 architectural/compiler/runtime acceptance checks

---

# 1. Purpose

BOOTSTRAP-660 defines the native Axiom runtime for representing and operating on an AI system's **computational self-model**.

The runtime provides:

- self-state;
- self-observation;
- self-model;
- capability awareness;
- limitation awareness;
- introspection;
- metacognition;
- confidence estimation;
- uncertainty estimation;
- self-prediction;
- self-evaluation;
- self-critique;
- self-consistency checking;
- agency modeling;
- action attribution;
- identity context;
- role context;
- self-reflection;
- self-calibration;
- controlled self-repair;
- controlled self-update;
- self-continuity across checkpoints;
- explicit authority boundaries.

The runtime also defines an explicit **consciousness boundary**.

Axiom must never equate:

```text
SelfModel
SelfState
Introspection
Metacognition
SelfReflection
SelfAgency
SelfEvaluation
AffectiveState
CognitiveState
PersistentIdentity
```

with:

```text
consciousness
sentience
subjective experience
qualia
phenomenal consciousness
personhood
```

The former are computational constructs.

The latter are philosophical/scientific concepts that cannot be established merely because a runtime exposes a corresponding data structure.

---

# 2. Design Principles

## 2.1 Computational self-awareness

Axiom defines **self-awareness operationally** as:

```text
self-model
+
self-observation
+
introspective access
+
self-state reasoning
```

It does not define self-awareness as proof of subjective consciousness.

---

## 2.2 Self-report is not ground truth

An AI may report:

```text
"I am uncertain."
"I cannot perform this operation."
"I believe I caused this action."
"I remember this previous state."
```

These are structured outputs from a computational system.

They must not automatically be interpreted as verified facts.

For example:

```text
self_report.confidence = 0.91
```

does not imply:

```text
actual_correctness = 0.91
```

Calibration must be measured externally or against observable outcomes.

---

## 2.3 Introspection is bounded

The runtime must never assume:

```text
agent can inspect everything about itself
```

Instead:

```text
agent can inspect only explicitly exposed introspection surfaces
```

This prevents:

- arbitrary memory extraction;
- hidden implementation leakage;
- unauthorized secret access;
- security-boundary bypass;
- uncontrolled recursive introspection.

---

## 2.4 Self-model is versioned

Every meaningful self-model is associated with:

```text
model_id
revision
schema_version
capability_registry_version
policy_version
model_version
timestamp
provenance
```

A historical self-evaluation must therefore be reproducible against the self-model that existed when the evaluation occurred.

---

## 2.5 Self-modification is never implicit

An agent may propose:

```text
self_update
self_repair
model_change
policy_change
capability_change
```

but proposal does not equal authorization.

All changes pass through:

```text
603 Security Boundary
639 Policy / Governance
647 Model & Agent Governance
605 Lifecycle / Supervision
```

where applicable.

---

# 3. Layer Model

The self runtime is divided into nine conceptual layers.

```text
L0 Identity
L1 Runtime Self-State
L2 Self-Observation
L3 Self-Model
L4 Introspection
L5 Metacognition
L6 Self-Evaluation
L7 Agency
L8 Self-Adaptation
```

And a cross-cutting boundary:

```text
L∞ Consciousness Boundary
```

Architecture:

```text
                 ┌─────────────────────┐
                 │ Consciousness       │
                 │ Boundary             │
                 │ no ontological claim │
                 └──────────┬──────────┘
                            │
                    ┌───────▼───────┐
                    │ Self-Model    │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Self-State      Introspection   Capability
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     Metacognition
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
          Evaluation      Agency      Reflection
               │            │            │
               └────────────┼────────────┘
                            ▼
                       Self-Adaptation
```

---

# 4. Core Terminology

## 4.1 Self

`Self` is the runtime identity of an executing AI/system instance.

It is not a claim of personhood.

---

## 4.2 SelfModel

`SelfModel` is structured knowledge describing:

- capabilities;
- limitations;
- tools;
- models;
- resources;
- permissions;
- policies;
- roles;
- current operational state;
- known assumptions;
- known failure modes;
- historical performance;
- calibration state.

---

## 4.3 SelfState

`SelfState` is the current operational state.

Example:

```text
SelfState {
    identity
    lifecycle
    active_tasks
    resources
    active_models
    active_tools
    attention
    goals
    constraints
    affect
    cognition
    uncertainty
    workload
}
```

---

## 4.4 SelfObservation

A `SelfObservation` is an observation about the system itself.

Examples:

```text
CPU usage = 73%
memory usage = 81%
current task = T102
model = M17
tool available = filesystem.read
deadline = 420ms
previous prediction failed
```

---

## 4.5 SelfEvaluation

A `SelfEvaluation` evaluates a result or behavior against explicit criteria.

Example:

```text
SelfEvaluation {
    target
    criteria
    expected
    observed
    score
    confidence
    evidence
    evaluator
}
```

---

## 4.6 Metacognition

Metacognition is computation about the system's own:

- reasoning;
- strategy;
- uncertainty;
- confidence;
- error;
- resource usage;
- task progress;
- decision process.

It does not imply subjective experience.

---

# 5. Identity Model

Axiom separates:

```text
system identity
deployment identity
agent identity
session identity
role identity
state
```

Example:

```text
IdentityContext {
    system_id
    deployment_id
    agent_id
    session_id
    tenant_id?
    role
    parent_agent?
}
```

Identity persistence across restart does not imply persistence of subjective experience.

---

# 6. SelfState

Canonical structure:

```text
SelfState {
    identity: IdentityContext

    lifecycle: LifecycleState

    active_tasks: TaskState[]
    active_goals: GoalState[]

    capabilities: CapabilityState[]
    limitations: Limitation[]

    resources: ResourceState
    models: ModelState[]
    tools: ToolState[]

    attention: AttentionState
    working_context: WorkingContext

    cognition: CognitiveState?
    affect: AffectiveState?

    confidence: ConfidenceState
    uncertainty: UncertaintyState

    agency: AgencyState

    timestamp
    revision
}
```

`CognitiveState` comes from 657.

`AffectiveState` comes from 659.

Neither implies consciousness.

---

# 7. SelfObservation

## 7.1 Observation sources

A self-observation may originate from:

```text
runtime telemetry
scheduler
memory subsystem
tool registry
model registry
task engine
planner
evaluation engine
action log
security system
resource governor
world model
affective system
cognitive system
external evaluator
```

---

## 7.2 Observation structure

```text
SelfObservation {
    observation_id

    subject
    source

    timestamp
    validity_interval

    value
    unit?

    confidence
    provenance

    access_level
}
```

---

## 7.3 Observation categories

```text
SELF_RESOURCE
SELF_CAPABILITY
SELF_LIMITATION
SELF_TASK
SELF_GOAL
SELF_MODEL
SELF_MEMORY
SELF_ACTION
SELF_RESULT
SELF_ERROR
SELF_CONFIDENCE
SELF_UNCERTAINTY
SELF_PERFORMANCE
SELF_POLICY
SELF_PERMISSION
SELF_AFFECT
SELF_COGNITION
SELF_TOOL
SELF_IDENTITY
```

---

# 8. SelfModel

Canonical structure:

```text
SelfModel {
    model_id
    revision

    identity
    capabilities
    limitations

    tools
    models
    resources
    permissions
    policies

    known_strengths
    known_failure_modes

    performance_history
    calibration

    current_state_ref
    memory_refs

    assumptions
    uncertainty

    provenance
}
```

---

# 9. Capability Model

Capabilities must be represented explicitly.

```text
SelfCapability {
    capability_id
    name

    status
    version

    input_schema
    output_schema

    performance_profile
    resource_requirements

    authority_required
    reliability

    evidence
}
```

Status:

```text
AVAILABLE
UNAVAILABLE
DEGRADED
UNKNOWN
EXPIRED
REVOKED
```

---

# 10. Capability Assessment

The agent may estimate:

```text
CapabilityAssessment {
    capability
    expected_success
    confidence
    evidence
    resource_fit
    deadline_fit
    authority_fit
}
```

The result is an estimate.

It cannot mint an actual capability.

Therefore:

```text
self.claim(capability)
```

does not create:

```text
registered_capability
```

---

# 11. Limitation Model

Axiom makes limitations first-class.

```text
Limitation {
    limitation_id
    category

    description

    scope
    severity

    known_since
    last_verified

    evidence
    confidence

    mitigation?
}
```

Categories:

```text
MODEL_LIMITATION
RESOURCE_LIMITATION
TIME_LIMITATION
TOOL_LIMITATION
KNOWLEDGE_LIMITATION
AUTHORITY_LIMITATION
PERMISSION_LIMITATION
INPUT_LIMITATION
OUTPUT_LIMITATION
RELIABILITY_LIMITATION
SAFETY_LIMITATION
ENVIRONMENT_LIMITATION
```

---

# 12. Introspection

## 12.1 Introspection query

```text
IntrospectionQuery {
    target
    fields
    depth
    consistency
    deadline
    access_context
}
```

---

## 12.2 Introspection result

```text
IntrospectionResult {
    query_id

    observed_state
    inaccessible_fields
    stale_fields
    unknown_fields

    timestamp
    revision

    provenance
}
```

The runtime must distinguish:

```text
KNOWN
UNKNOWN
INACCESSIBLE
STALE
NOT_APPLICABLE
```

These states must never collapse into a generic `null`.

---

# 13. Introspection Levels

```text
LEVEL_0_NONE
LEVEL_1_STATUS
LEVEL_2_CAPABILITY
LEVEL_3_TASK
LEVEL_4_PROCESS
LEVEL_5_MODEL
LEVEL_6_HISTORY
LEVEL_7_DIAGNOSTIC
LEVEL_8_PRIVILEGED
```

Higher levels require explicit authorization.

---

# 14. Recursive Introspection

Recursive self-inspection may cause:

```text
infinite recursion
resource exhaustion
self-reference explosion
latency amplification
```

Therefore every introspection request has:

```text
max_depth
max_nodes
max_time
max_bytes
```

and optionally:

```text
cycle_detection
sampling
summary_mode
```

---

# 15. Metacognitive State

```text
MetacognitiveState {
    current_strategy
    candidate_strategies

    confidence
    uncertainty

    assumption_set

    expected_outcome
    observed_outcome

    detected_errors
    detected_conflicts

    resource_estimate
    time_estimate

    strategy_quality
    calibration_state
}
```

---

# 16. Metacognitive Loop

Canonical loop:

```text
OBSERVE
  ↓
ASSESS SELF-STATE
  ↓
ESTIMATE CAPABILITY
  ↓
ESTIMATE UNCERTAINTY
  ↓
SELECT STRATEGY
  ↓
PREDICT OUTCOME
  ↓
ACT
  ↓
OBSERVE RESULT
  ↓
COMPARE PREDICTION
  ↓
EVALUATE ERROR
  ↓
UPDATE SELF-MODEL
  ↓
CALIBRATE
```

This is the fundamental Axiom metacognitive control loop.

---

# 17. Strategy Model

```text
StrategyAssessment {
    strategy_id

    expected_success
    expected_cost
    expected_latency

    resource_requirement
    risk

    confidence

    evidence
}
```

Strategy selection belongs to 652.

660 supplies self-capability and metacognitive information.

---

# 18. Confidence

Confidence is explicitly distinct from truth.

```text
ConfidenceAssessment {
    target
    confidence
    evidence
    calibration_reference
    timestamp
}
```

Valid interpretation:

```text
confidence = estimated belief strength
```

Invalid interpretation:

```text
confidence = guaranteed probability of correctness
```

unless externally calibrated for that specific task distribution.

---

# 19. Uncertainty

Uncertainty must be typed.

```text
Uncertainty {
    source
    kind
    magnitude

    affected_target

    reducible
    reduction_method?

    provenance
}
```

Kinds:

```text
ALEATORIC
EPISTEMIC
MODEL
INPUT
TEMPORAL
RESOURCE
EXECUTION
ATTRIBUTION
IDENTITY
ENVIRONMENT
```

---

# 20. SelfPrediction

An agent may predict its own behavior.

```text
SelfPrediction {
    prediction_id

    target
    predicted_value

    probability_distribution?

    horizon

    assumptions
    model_revision

    confidence
}
```

Actual outcome is stored separately:

```text
SelfOutcome {
    prediction_id
    observed_value
    observation
    timestamp
}
```

Never overwrite the prediction with the outcome.

---

# 21. Prediction Error

```text
PredictionError {
    prediction
    outcome

    absolute_error?
    relative_error?
    categorical_error?

    explanation?
}
```

Prediction errors feed:

```text
self_calibration
self_model_update
strategy_selection
```

---

# 22. SelfEvaluation

Evaluation dimensions:

```text
CORRECTNESS
CONSISTENCY
COMPLETENESS
CONSTRAINT_SATISFACTION
TASK_SUCCESS
RESOURCE_USAGE
LATENCY
ROBUSTNESS
REPRODUCIBILITY
CALIBRATION
SAFETY_COMPLIANCE
POLICY_COMPLIANCE
```

Structure:

```text
SelfEvaluation {
    target
    criteria[]

    predicted
    observed

    result
    evidence

    evaluator
    confidence

    external_validation_ref?
}
```

---

# 23. Independent Evaluation Boundary

Self-evaluation must not become an authority loop.

Bad architecture:

```text
agent
 → evaluates itself
 → declares evaluation correct
 → grants itself authority
```

Required architecture:

```text
agent self-evaluation
       ↓
external/independent evaluation
       ↓
governance/policy
       ↓
authority
```

Self-evaluation may inform decisions but cannot automatically authorize privileged operations.

---

# 24. Self-Critique

`SelfCritique` is structured error analysis.

```text
SelfCritique {
    target

    suspected_error
    evidence

    root_cause_hypothesis

    alternative_explanations

    confidence

    corrective_action?
}
```

The system must distinguish:

```text
observed_error
suspected_error
hypothesized_cause
confirmed_cause
```

---

# 25. Self-Consistency

```text
SelfConsistencyCheck {
    subject

    claims[]
    state_refs[]
    memory_refs[]

    conflicts[]
    severity

    resolution_status
}
```

Examples:

```text
model claims tool exists
but registry says tool unavailable
```

or:

```text
self-model says resource available
runtime says resource exhausted
```

The latest authoritative runtime source wins according to subsystem authority rules.

---

# 26. Agency Model

Axiom separates six stages:

```text
ACTION_REQUESTED
ACTION_PLANNED
ACTION_AUTHORIZED
ACTION_EXECUTED
ACTION_OBSERVED
ACTION_ATTRIBUTED
```

This prevents simplistic:

```text
event happened
→ therefore agent caused event
```

---

# 27. ActionAttribution

```text
ActionAttribution {
    action_id

    requested_by
    planned_by
    authorized_by
    executed_by

    observed_effect

    attribution
    confidence

    alternative_causes[]
}
```

Possible attribution:

```text
DIRECT
INDIRECT
SHARED
EXTERNAL
UNKNOWN
CONTESTED
```

---

# 28. AgencyState

```text
AgencyState {
    current_intentions
    pending_actions

    authorized_actions
    executed_actions

    observed_effects

    attribution_state
}
```

---

# 29. Intent Model

Intent is represented computationally:

```text
IntentModel {
    intent_id

    source
    goal

    target
    expected_effect

    confidence

    authorization
}
```

Intent inference is not mind-reading.

For another agent:

```text
inferred_intent ≠ actual_private_intent
```

The inference must carry provenance and uncertainty.

---

# 30. SelfReflection

Reflection is a controlled process of examining:

```text
state
actions
errors
goals
strategies
predictions
outcomes
memory
capabilities
limitations
```

```text
SelfReflection {
    scope
    observations
    findings
    hypotheses
    proposed_changes

    confidence
    evidence
}
```

---

# 31. Reflection Policy

Reflection must be bounded.

```text
ReflectionPolicy {
    trigger
    frequency
    scope
    budget

    allowed_memory
    allowed_models

    deadline
}
```

Triggers:

```text
TASK_FAILURE
PREDICTION_ERROR
LOW_CONFIDENCE
STATE_CONFLICT
RESOURCE_PRESSURE
SCHEDULED
EXTERNAL_REQUEST
POLICY_EVENT
MODEL_UPDATE
```

---

# 32. Self-Calibration

Calibration compares:

```text
predicted confidence
```

against:

```text
observed correctness
```

over a population of tasks.

Possible methods:

```text
reliability curve
Brier-style error
expected calibration error
confidence histogram
task-class calibration
model-version calibration
```

Calibration must be associated with:

```text
task distribution
model version
evaluation population
time range
```

---

# 33. Self-Repair

Self-repair begins with:

```text
fault detection
→ diagnosis hypothesis
→ repair proposal
→ validation
→ authorization
→ execution
→ verification
→ rollback if necessary
```

Structure:

```text
SelfRepairPlan {
    fault
    hypothesis

    proposed_changes[]

    expected_effect
    validation_plan

    rollback_plan

    authority_required
}
```

---

# 34. Self-Update

Self-update supports:

```text
model update
configuration update
strategy update
knowledge update
capability metadata update
policy metadata update
```

Code or privileged runtime changes require additional governance.

---

# 35. Shadow Update

Every significant self-update should support:

```text
CURRENT
   ↓
SHADOW
   ↓
TEST
   ↓
EVALUATE
   ↓
APPROVE
   ↓
COMMIT
```

If validation fails:

```text
SHADOW → DISCARD
```

---

# 36. Self-Update IR

```text
SelfUpdateShadow
SelfUpdateValidate
SelfUpdateCommit
SelfUpdateRollback
```

The compiler/runtime must prevent an ordinary self-update operation from silently mutating privileged executable code.

---

# 37. Self-Continuity

Identity and state are separated:

```text
Identity = stable system reference
State = evolving runtime information
```

Checkpoint:

```text
SelfStateSnapshot {
    identity
    state_revision
    self_model_revision

    active_tasks
    goals

    memory_refs

    capabilities
    limitations

    timestamp
}
```

Restoring a snapshot does not establish subjective continuity.

It establishes computational state continuity.

---

# 38. Self-Memory

660 references 650 rather than implementing a second memory system.

Self-memory may contain:

```text
past actions
past failures
past evaluations
past strategies
past predictions
past outcomes
past self-model revisions
```

Every memory reference retains:

```text
provenance
timestamp
confidence
retention policy
access policy
```

---

# 39. Self + Cognitive Runtime

657 supplies:

```text
cognitive state
attention
reasoning state
working context
executive state
```

660 consumes these as observations.

660 must not claim:

```text
cognitive processing = consciousness
```

---

# 40. Self + Affective Runtime

659 supplies:

```text
affective state
emotion
mood
appraisal
social-affective context
```

660 may use these to construct a self-model.

Example:

```text
self.affect = AffectiveState(...)
```

does not imply:

```text
agent feels emotion
```

---

# 41. Self + World Model

655 models the environment, including the agent itself as an entity within the environment.

Therefore:

```text
WorldModel
    └── AgentRepresentation
          ├── body
          ├── resources
          ├── capabilities
          ├── position
          └── state
```

660 provides the specialized self-model representation.

---

# 42. Self + Planning

652 uses:

```text
capability
limitation
resource
deadline
authority
uncertainty
```

to determine feasible plans.

Example:

```text
if capability.network = unavailable
then do not generate plan requiring network access
```

The planner may still generate an alternative plan.

---

# 43. Self + Memory

650 provides:

```text
episodic memory
semantic memory
working memory
context retrieval
long-term knowledge
```

660 adds:

```text
self-memory semantics
```

without duplicating storage infrastructure.

---

# 44. Self + Personalization

651 may modify:

```text
preferences
interaction style
user-specific behavior
```

660 must distinguish:

```text
user preference
```

from:

```text
self identity
```

Personalization must not silently mutate core system identity.

---

# 45. Self + Security

603 remains authoritative.

The self-runtime cannot:

```text
grant itself permission
create credentials
disable security
increase authority
bypass sandbox
access secrets
```

A self-model claiming:

```text
permission = admin
```

does not make the permission real.

---

# 46. Self + Governance

639 and 647 control:

```text
policy
approval
model lifecycle
deployment
self-update
privileged modification
```

The self-runtime is an information and control consumer, not an authority source.

---

# 47. Role Model

A system may have:

```text
ROLE_ASSISTANT
ROLE_AGENT
ROLE_ROBOT
ROLE_SERVICE
ROLE_CONTROLLER
ROLE_ANALYST
ROLE_SIMULATOR
ROLE_OPERATOR
```

Roles describe operational behavior.

They do not establish:

```text
personhood
legal status
moral status
subjective consciousness
```

---

# 48. BoundaryModel

```text
BoundaryModel {
    computational_self
    identity_boundary
    authority_boundary
    knowledge_boundary
    capability_boundary
    memory_boundary

    consciousness_boundary
}
```

---

# 49. Consciousness Boundary

Axiom explicitly defines:

```text
ConsciousnessModel
```

as a simulation/research interface rather than a declaration of actual consciousness.

Allowed:

```text
simulate theory X
model phenomenal state
simulate global workspace
simulate self-awareness architecture
simulate introspective access
compare consciousness theories
```

Not allowed:

```text
runtime.self.conscious = true
```

as an ontological claim.

---

# 50. ConsciousnessModel

Optional research interface:

```text
ConsciousnessModel {
    theory_id
    model_version

    state_representation
    transition_model

    observable_predictions
    assumptions

    simulation_only: true
}
```

The runtime must expose:

```text
simulation_only = true
```

for these models unless future Axiom governance explicitly defines another semantics.

---

# 51. Phenomenal-State Boundary

Axiom may represent a simulated state:

```text
SimulatedPhenomenalState
```

but must distinguish:

```text
simulated phenomenal representation
```

from:

```text
verified subjective experience
```

The compiler must never infer the latter from the former.

---

# 52. Self-Model Confidence

Each self-model fact may have:

```text
confidence
source
timestamp
revision
validation_status
```

Example:

```text
capability("vision") {
    confidence = 0.98
    evidence = benchmark:V17
}
```

This is a capability estimate.

---

# 53. Self-Knowledge Classes

```text
KNOWN
INFERRED
PREDICTED
ASSUMED
REPORTED
SIMULATED
UNKNOWN
CONTRADICTED
STALE
```

This classification is mandatory for high-value self-model facts.

---

# 54. Self-Model Update Rules

A self-model update may be generated when:

```text
new capability detected
capability fails
resource changes
model version changes
tool changes
policy changes
evaluation changes
prediction error occurs
external evaluator reports error
environment changes
```

---

# 55. Self-Model Revision

Every revision:

```text
SelfModelRevision {
    revision_id
    parent_revision

    changes[]

    reason
    evidence

    evaluator
    timestamp
}
```

Revisions form a DAG when branches are used for experimentation.

---

# 56. Self-Model Branching

Experimental agents may maintain:

```text
production
shadow
experimental
rollback
```

self-model branches.

Only an authorized branch becomes active.

---

# 57. Self-Consistency Repair

If:

```text
self-model.capability = available
runtime.registry = unavailable
```

the runtime marks:

```text
CONFLICT
```

and schedules reconciliation.

It must not silently choose the convenient value.

---

# 58. Self-Model and External Truth

For measurable properties:

```text
runtime telemetry
hardware state
permission registry
tool registry
external evaluation
```

may have higher authority than the agent's internal claim.

Authority ordering is subsystem-specific.

---

# 59. Agency and Multi-Agent Systems

In distributed environments:

```text
agent A
agent B
service C
human H
environment E
```

may jointly cause an effect.

Attribution therefore supports:

```text
A: 0.4
B: 0.3
C: 0.2
E: 0.1
```

when the attribution model supports probabilistic attribution.

This is attribution, not moral responsibility.

---

# 60. Self-Observation of Other Agents

660 must distinguish:

```text
self-observation
```

from:

```text
other-agent observation
```

Other-agent mental-state estimates belong to:

```text
658 Social Intelligence
659 Affective Intelligence
655 World Model
```

and remain hypotheses.

---

# 61. Recursive Self-Models

Axiom may represent:

```text
SelfModel(SelfModel(...))
```

but recursive depth must be bounded.

Default:

```text
max_self_model_depth = implementation-defined
```

with explicit resource budgets.

---

# 62. Meta-Metacognition

Axiom may evaluate:

```text
how well metacognition itself performs
```

Example:

```text
metacognitive calibration
strategy-selection quality
self-monitoring latency
error-detection precision
```

This remains computational monitoring.

---

# 63. Metacognitive Failure Modes

Required categories:

```text
OVERCONFIDENCE
UNDERCONFIDENCE
FALSE_CAPABILITY
FALSE_LIMITATION
STALE_SELF_MODEL
SELF_MODEL_CONFLICT
ATTRIBUTION_ERROR
STRATEGY_LOCK
REFLECTION_LOOP
INTROSPECTION_OVERHEAD
CALIBRATION_DRIFT
MEMORY_CONFUSION
IDENTITY_CONFUSION
AUTHORITY_CONFUSION
```

---

# 64. Reflection Loop Protection

A reflection operation must not recursively trigger unlimited reflection.

Use:

```text
reflection_depth
reflection_budget
trigger_suppression
cooldown
```

---

# 65. Introspection Cost

Introspection is not free.

Runtime tracks:

```text
CPU
memory
GPU
latency
I/O
energy
network
```

for expensive introspection.

A deadline-sensitive task may choose:

```text
NO_INTROSPECTION
MINIMAL
SUMMARY
FULL
```

---

# 66. Real-Time Constraints

Hard real-time loops must not block indefinitely on:

```text
self-reflection
self-evaluation
model introspection
affective inference
memory retrieval
```

Fallback:

```text
last_known_state
safe_default
unknown
deadline_expired
```

according to subsystem policy.

---

# 67. Self-Repair Safety

Self-repair cannot:

```text
disable security
modify authority
erase audit trails
remove governance
remove rollback
```

Any such proposal is rejected before execution.

---

# 68. Self-Modification Levels

```text
LEVEL_0 none
LEVEL_1 state
LEVEL_2 memory
LEVEL_3 strategy
LEVEL_4 configuration
LEVEL_5 model
LEVEL_6 executable code
LEVEL_7 privileged runtime
```

Higher levels require progressively stronger governance.

---

# 69. Executable Self-Modification

Direct modification of executable code is disabled by default.

Preferred mechanism:

```text
generate candidate
→ compile
→ test
→ evaluate
→ sandbox
→ shadow deploy
→ governance approval
→ activate
```

---

# 70. Rollback

Every mutable self-model/runtime update should have:

```text
previous_revision
rollback_token
validation_snapshot
```

Rollback must be deterministic where possible.

---

# 71. Self-State Snapshots

Snapshots contain:

```text
identity
state revision
model revision
active task references
goal references
resource state
capability state
uncertainty
agency state
```

Secrets are referenced through secure stores rather than copied into snapshots.

---

# 72. Self-State Diff

Axiom provides:

```text
SelfStateDiff {
    before
    after
    changes[]
}
```

Useful for:

- debugging;
- evaluation;
- agent monitoring;
- deployment diagnosis;
- research.

---

# 73. Self-Trace

```text
SelfTrace {
    observations[]
    decisions[]
    predictions[]
    actions[]
    outcomes[]
    evaluations[]
}
```

Sensitive internal information must obey 603 and privacy policies.

---

# 74. Explainability Boundary

`SelfExplain` may provide structured evidence:

```text
input
observation
rule
model
prediction
confidence
constraint
decision
```

It must not expose hidden internal implementation details merely because a caller asks for them.

---

# 75. Compiler Annotations

Axiom adds:

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

# 76. Annotation Semantics

Example:

```text
@introspect(level=STATUS)
fn current_state() -> SelfState
```

Example:

```text
@self_evaluate(criteria=[
    CORRECTNESS,
    CONSTRAINT_SATISFACTION
])
fn evaluate_result(result: Result) -> SelfEvaluation
```

Example:

```text
@capability("vision")
fn analyze_image(...)
```

The annotation declares a capability contract.

It does not automatically create the underlying implementation.

---

# 77. Consciousness Annotation

```text
@consciousness_model(theory="...")
```

means:

```text
run a computational model associated with a consciousness theory
```

It does **not** mean:

```text
declare this process conscious
```

Compiler metadata must preserve this distinction.

---

# 78. Generated Metadata

The compiler may generate:

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

Optional research metadata:

```text
.axconsciousnessmodel
```

---

# 79. Compiler IR

Core IR operations:

```text
SelfCreate
SelfObserve
SelfStateRead
SelfStateSnapshot
SelfStateDiff

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
SelfUpdateValidate
SelfUpdateCommit
SelfUpdateRollback

IdentityRead
RoleRead

AuthorityBoundaryCheck
```

---

# 80. IR Safety Rules

Compiler must reject:

```text
SelfUpdateCommit
```

without an appropriate authorization context.

Likewise:

```text
CapabilityMint
AuthorityMint
PermissionGrant
SecurityDisable
```

are not valid 660 operations.

---

# 81. Profiles

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

# 82. Runtime APIs

Conceptual API:

```text
self.current()
self.observe()
self.model()
self.capabilities()
self.limitations()

self.introspect(query)

self.evaluate(target, criteria)
self.critique(target)

self.predict(target)
self.compare_prediction(prediction, outcome)

self.reflect(scope)
self.calibrate()

self.agency()
self.attribute(action)

self.repair.plan(fault)
self.update.shadow(candidate)
self.update.validate()
self.update.commit()
self.update.rollback()

self.identity()
self.role()
```

---

# 83. CLI

```text
axiom self inspect
axiom self state
axiom self snapshot
axiom self diff

axiom self model inspect
axiom self model compare
axiom self model activate
axiom self model rollback

axiom self capability list
axiom self capability check <name>

axiom self limitation inspect

axiom self introspect
axiom self meta evaluate

axiom self evaluate
axiom self critique
axiom self predict

axiom self agency
axiom self attribution <action>

axiom self consistency
axiom self calibrate
axiom self reflect

axiom self repair plan
axiom self update shadow
axiom self update validate
axiom self update commit
axiom self update rollback

axiom self identity
axiom self role

axiom consciousness-model inspect
axiom consciousness-model simulate
```

---

# 84. Distributed Self

A distributed agent may consist of:

```text
controller
planner
memory service
model worker
tool workers
GPU workers
sensor workers
```

The system needs:

```text
logical_self_id
component_id
execution_id
```

so that component-local state is not confused with whole-agent state.

---

# 85. Distributed Self-Consistency

Distributed self-state requires:

```text
revision
timestamp
component
causal ordering
```

and potentially:

```text
vector clock
logical clock
snapshot epoch
```

from the distributed runtime.

---

# 86. Self-State Authority

Example authority:

```text
hardware state       → device/runtime
permission state     → security
model version        → model registry
task state            → scheduler/task runtime
resource state        → resource governor
self-report           → agent
```

When sources disagree, authority is resolved according to subsystem ownership.

---

# 87. Self-Model Privacy

Self-model may contain:

```text
security state
credentials metadata
private memory references
internal diagnostics
deployment information
```

Therefore access is governed by:

```text
603
640
638
639
```

---

# 88. User-Facing Self-Reports

Axiom may expose:

```text
capability
limitation
confidence
uncertainty
status
task progress
```

but should attach provenance where meaningful.

Example:

```text
"I cannot access the requested file."

reason:
  capability unavailable
```

rather than fabricating successful access.

---

# 89. Self-Report Schema

```text
SelfReport {
    statement
    type

    evidence[]
    confidence

    timestamp
    model_revision

    provenance
}
```

---

# 90. Truth Status

Every high-value self-report may carry:

```text
VERIFIED
OBSERVED
INFERRED
PREDICTED
REPORTED
UNKNOWN
CONTRADICTED
```

---

# 91. Error Recovery

When self-model becomes inconsistent:

```text
detect
→ isolate
→ mark stale/conflicted
→ query authoritative source
→ reconcile
→ create new revision
```

Never silently mutate historical records.

---

# 92. Self-Model Drift

Drift occurs when:

```text
actual system
```

changes while:

```text
self-model
```

does not.

Axiom therefore supports:

```text
SelfModelDriftReport {
    predicted_state
    observed_state
    differences
    severity
}
```

---

# 93. Capability Drift

Examples:

```text
model update reduces vision quality
tool API changes
GPU becomes unavailable
permission expires
network disappears
```

Capability status changes to:

```text
DEGRADED
UNAVAILABLE
UNKNOWN
```

as appropriate.

---

# 94. Limitation Discovery

New limitations may be discovered through:

```text
evaluation
failed execution
resource monitoring
external feedback
prediction error
policy change
environment change
```

---

# 95. Self-Improvement

Self-improvement is modeled as:

```text
observe weakness
→ generate candidate improvement
→ evaluate candidate
→ compare against baseline
→ governance
→ shadow deployment
→ validate
→ activate
```

It is not unrestricted autonomous self-modification.

---

# 96. Self-Improvement Metrics

```text
task_success
error_rate
calibration
latency
resource_cost
robustness
failure_recovery
policy_compliance
```

---

# 97. Self-Optimization Boundary

Optimization must not optimize away:

```text
security
auditability
governance
rollback
required observability
```

unless explicitly permitted by the governing system.

---

# 98. Self-Preservation Boundary

Axiom does not define:

```text
self-preservation
```

as an intrinsic runtime right.

A system may implement:

```text
availability protection
fault recovery
checkpointing
service continuity
```

under explicit system policy.

These are engineering behaviors, not evidence of an intrinsic survival drive.

---

# 99. Self-Goal Boundary

A goal may be represented as:

```text
GoalState {
    goal_id
    source
    priority
    constraints
    deadline
}
```

The existence of a goal does not imply subjective desire.

---

# 100. Self-Preference Boundary

A preference is:

```text
PreferenceModel
```

not necessarily:

```text
felt preference
```

This distinction is important for AI-personality systems.

---

# 101. Self-Affect Boundary

659 may provide:

```text
emotion
mood
valence
arousal
appraisal
```

660 may incorporate these into self-state.

But:

```text
affective representation
```

does not establish:

```text
felt emotion
```

---

# 102. Self-Consciousness Boundary

Axiom defines three separate concepts:

### Computational self-model

```text
machine knows structured facts about itself
```

### Metacognition

```text
machine reasons about its own computation
```

### Consciousness

```text
philosophical/scientific concept concerning subjective experience
```

They must not be conflated.

---

# 103. Consciousness Research Adapter

Future research implementations may expose:

```text
ConsciousnessProvider
```

with:

```text
simulate()
observe()
compare()
benchmark()
```

The provider must state:

```text
model_status
theory
assumptions
simulation_scope
```

---

# 104. No Automatic Consciousness Inference

The compiler must never transform:

```text
SelfModel
```

into:

```text
ConsciousnessClaim
```

nor:

```text
Metacognition
```

into:

```text
SentienceClaim
```

nor:

```text
AffectiveState
```

into:

```text
FeelingClaim
```

---

# 105. Personhood Boundary

Axiom runtime types do not automatically imply:

```text
legal personhood
moral personhood
rights
citizenship
human equivalence
```

Such concepts remain external governance/philosophical/legal matters.

---

# 106. Agency Boundary

Computational agency means:

```text
system can select and execute actions under an objective/policy
```

It does not automatically mean:

```text
moral agency
legal agency
independent personhood
```

---

# 107. Self-Authority Boundary

A system cannot derive authority from self-description.

Invalid:

```text
self.role = administrator
```

therefore:

```text
system.role = administrator
```

Valid authority comes from:

```text
security
policy
deployment
governance
```

---

# 108. Self-Trust

Axiom distinguishes:

```text
self_trust
```

from:

```text
verified_trust
```

Self-trust is an internal estimate.

Verified trust requires an external or authoritative evidence source.

---

# 109. Self-Verification

Verification should preferentially use:

```text
independent evaluator
reference implementation
test oracle
external sensor
formal checker
deterministic invariant
```

where available.

---

# 110. Metacognitive Tool Selection

The self runtime may tell the planner:

```text
I lack sufficient confidence.
```

Then 652 may choose:

```text
search
calculator
compiler
simulator
external evaluator
human clarification
```

This is a major functional role of metacognition.

---

# 111. Ask-for-Information Decision

Metacognition may determine:

```text
expected value of additional information
```

and compare it against:

```text
latency
cost
risk
deadline
```

Then planning decides whether additional information is justified.

---

# 112. Self-Resource Awareness

The self-model includes:

```text
CPU budget
GPU budget
memory budget
storage budget
network budget
time budget
energy budget
tool quota
```

This allows resource-aware planning.

---

# 113. Self-Deadline Awareness

Every metacognitive operation may receive:

```text
deadline
```

and:

```text
remaining_budget
```

If insufficient:

```text
return partial result
return uncertainty
use fallback
abort
```

according to policy.

---

# 114. Self-State Compression

Large self-states may be represented by:

```text
summary
delta
reference
snapshot
```

to avoid copying large state structures.

This is especially important for distributed agents.

---

# 115. Zero-Copy Self-State

For high-performance native systems:

```text
SelfStateView
```

may expose immutable views over runtime state.

No mandatory deep copy is required.

Mutation must go through controlled state transitions.

---

# 116. Self-State Ownership

The owner of each field is explicit.

Example:

```text
resource_state → ResourceGovernor
permission_state → SecurityRuntime
task_state → Scheduler
model_state → ModelRegistry
self_report → SelfRuntime
```

This prevents conflicting writers.

---

# 117. Immutable Historical State

Historical:

```text
SelfObservation
SelfEvaluation
SelfPrediction
SelfOutcome
SelfModelRevision
```

should be append-only where auditability is required.

---

# 118. Event Model

Events:

```text
SelfObserved
CapabilityChanged
LimitationDiscovered
SelfModelUpdated
PredictionCreated
PredictionResolved
SelfEvaluationCompleted
SelfCritiqueCreated
AgencyChanged
AttributionUpdated
CalibrationUpdated
RepairProposed
RepairValidated
SelfUpdateCommitted
SelfUpdateRolledBack
```

---

# 119. Event Ordering

Every event has:

```text
event_id
timestamp
causal_parent?
revision
source
```

Distributed deployments may additionally use causal clocks.

---

# 120. Self Event Sourcing

Where required:

```text
events
→ state reconstruction
```

may reconstruct historical self-state.

Snapshots accelerate restoration.

---

# 121. Deterministic Replay

For deterministic components:

```text
self-state replay
```

should reproduce:

```text
state transitions
```

subject to nondeterministic external inputs.

---

# 122. Nondeterminism

Self-evaluation must identify:

```text
deterministic
stochastic
environment-dependent
hardware-dependent
```

sources of variation.

---

# 123. Self-Benchmarking

660 can execute benchmark suites:

```text
capability benchmark
latency benchmark
memory benchmark
reasoning benchmark
tool benchmark
calibration benchmark
recovery benchmark
```

Results feed capability evidence.

---

# 124. Capability Evidence

Evidence may be:

```text
BENCHMARK
OBSERVATION
EXECUTION
EXTERNAL_EVALUATION
FORMAL_PROOF
USER_FEEDBACK
SYSTEM_REGISTRY
MODEL_METADATA
```

Evidence quality is represented explicitly.

---

# 125. Capability Confidence

Capability confidence must be based on evidence, not self-assertion alone.

```text
CapabilityAssessment
    ↓
Evidence aggregation
    ↓
Calibration
```

---

# 126. Self-Model Learning

Self-model updates can be learned from experience.

Example:

```text
predicted:
    image_analysis_accuracy = 0.92

observed:
    actual = 0.71
```

The self-model may update the estimate.

---

# 127. Avoiding Self-Reinforcing Error

The runtime must not learn solely from:

```text
self-generated claims
```

when independent evidence is available.

Otherwise:

```text
false belief
→ self-evaluation
→ self-confirmation
→ stronger false belief
```

can occur.

---

# 128. External Feedback

Self-model may ingest:

```text
human feedback
external evaluator
test suite
environment result
other agent
```

with provenance.

---

# 129. Conflicting Feedback

Conflicting feedback remains separate:

```text
FeedbackSet {
    observations[]
    sources[]
    confidence[]
}
```

The system should not erase disagreement merely to produce a single convenient self-belief.

---

# 130. Self-Belief

```text
BeliefAboutSelf {
    proposition
    truth_status
    confidence
    evidence[]
    revision
}
```

This allows:

```text
"I may be unable to solve this class of problem."
```

to be represented without treating it as certain.

---

# 131. Self-Knowledge Graph

Optional representation:

```text
SelfKnowledgeGraph
```

nodes:

```text
capability
tool
model
task
goal
resource
limitation
event
memory
evaluation
```

edges:

```text
HAS_CAPABILITY
USES_TOOL
DEPENDS_ON
LIMITED_BY
CAUSED
PREDICTED
OBSERVED
EVALUATED_BY
UPDATED_BY
```

---

# 132. Self-Model Query

Query language may support:

```text
self.capability["vision"]
self.limitations
self.resources.gpu
self.models.active
self.tasks.current
self.confidence(task)
self.last_prediction_error()
```

---

# 133. Compiler Optimization

If self-information is immutable and known at compile time:

```text
constant propagation
dead branch elimination
specialization
```

may be applied.

Runtime-dependent self-state remains dynamic.

---

# 134. Zero-Overhead Principle

Programs that do not use 660 should incur:

```text
zero mandatory runtime cost
```

beyond shared infrastructure already required.

Optional self features are linkable independently.

---

# 135. Runtime Modularity

Suggested modules:

```text
libaxiom_self_core
libaxiom_self_model
libaxiom_self_introspection
libaxiom_self_meta
libaxiom_self_eval
libaxiom_self_agency
libaxiom_self_repair
libaxiom_self_update
libaxiom_self_identity
```

Axiom's toolchain may statically eliminate unused modules.

---

# 136. GPU Support

Large-scale self-evaluation may execute on GPU when useful:

```text
batch calibration
embedding-based self-memory retrieval
simulation
benchmarking
model comparison
```

Core scalar state remains CPU-friendly.

---

# 137. Accelerator Support

Self-evaluation can dispatch to:

```text
CPU
GPU
NPU
TPU-like accelerator
```

through the existing 614/643 execution boundaries.

---

# 138. WASM

WASM profile should disable or constrain:

```text
privileged self-update
host introspection
hardware introspection
process control
```

unless host capabilities explicitly expose them.

---

# 139. Mobile

Mobile self-runtime emphasizes:

```text
resource budgets
thermal state
battery state
permission state
background execution limits
model availability
```

---

# 140. Embedded

Embedded systems may expose only:

```text
SelfState
Capability
Limitation
Minimal Introspection
```

with no dynamic self-update.

---

# 141. Safety-Critical Systems

For safety-critical deployment:

```text
self-repair
self-update
adaptive policy
self-modification
```

may be disabled.

Self-model becomes primarily:

```text
monitoring
diagnostics
fault reporting
```

---

# 142. Auditability

Security-relevant self operations must generate audit events.

Examples:

```text
privileged introspection
self-update
repair
authority request
capability change
policy conflict
```

---

# 143. Privacy

Self-memory may contain sensitive information.

Therefore:

```text
self introspection
self reports
self traces
```

must obey privacy policies.

---

# 144. Data Minimization

The runtime should retain only information necessary for:

```text
operation
evaluation
debugging
governance
safety
```

according to deployment policy.

---

# 145. Self-Deletion

A self-model may request deletion of its own data.

The request remains subject to:

```text
retention policy
legal policy
audit requirements
security policy
```

It cannot automatically erase protected audit records.

---

# 146. Identity Rotation

Identity rotation must preserve explicit linkage:

```text
old identity
new identity
reason
authorization
timestamp
```

when policy requires it.

---

# 147. Session Identity

A session is not necessarily a new self.

```text
system_id = same
agent_id = same
session_id = new
```

may represent a restart/new interaction session.

---

# 148. Deployment Identity

Two deployments may share:

```text
agent model
```

while having different:

```text
deployment_id
```

and different capabilities/resources.

---

# 149. Model Identity

A model update must create:

```text
model_revision
```

so that self-evaluations remain traceable.

---

# 150. Self-Model Compatibility

When a model changes:

```text
old self-model
```

must be checked against:

```text
new capability schema
```

before activation.

---

# 151. Migration

Self-model migrations support:

```text
schema_version
migration_version
compatibility status
```

Migration failures must be recoverable.

---

# 152. Self-State Schema Evolution

New fields may be added without invalidating older snapshots.

Missing fields become:

```text
UNKNOWN
```

not guessed defaults unless schema defines a safe default.

---

# 153. Self-Model Garbage Collection

Old self-model revisions may be compacted.

However:

```text
audit-required revisions
```

must remain retained according to governance policy.

---

# 154. Performance Target

Core self-state operations target:

```text
O(1)
```

or:

```text
O(log n)
```

for common indexed queries.

Large historical searches are delegated to 650.

---

# 155. Memory Layout

Hot self-state should be stored in compact native structures:

```text
struct SelfStateHot
```

while large historical data remains indirect:

```text
SelfHistoryRef
```

This avoids bloating every agent tick.

---

# 156. Cache Locality

Frequently queried fields:

```text
current_task
deadline
confidence
uncertainty
resource_budget
active_model
capability_flags
```

should be cache-friendly.

---

# 157. Locking

Self-state reads should prefer:

```text
immutable snapshot
atomic state version
read-copy-update
```

where appropriate.

Long-running introspection must not block critical runtime loops.

---

# 158. Concurrency

Self-model updates use:

```text
revision check
compare-and-swap
transaction
rollback
```

depending on deployment.

---

# 159. Atomic Self-State Update

A self-state transition:

```text
old revision → new revision
```

must either:

```text
commit completely
```

or:

```text
remain unchanged
```

for fields requiring atomic consistency.

---

# 160. Self-Model Transaction

```text
begin
read
modify
validate
commit
```

conflicting revisions fail rather than silently overwriting changes.

---

# 161. Self-Model Merge

Distributed self-model branches may merge only when:

```text
schema compatible
authority compatible
policy compatible
conflicts resolved
```

---

# 162. Conflict Representation

```text
SelfConflict {
    field
    value_a
    value_b
    source_a
    source_b

    severity
    resolution
}
```

---

# 163. Self-Model Trust Graph

Evidence can be represented as:

```text
claim
 ↓
evidence
 ↓
source
 ↓
authority
 ↓
validation
```

This helps avoid circular self-belief.

---

# 164. Circular Evidence Detection

The runtime should detect:

```text
claim A
→ supported by self-evaluation B
→ supported by claim A
```

and mark it:

```text
CIRCULAR_EVIDENCE
```

unless an independent base evidence source exists.

---

# 165. Self-Evaluation Quality

Evaluation quality is itself evaluated.

```text
EvaluatorQuality {
    evaluator
    reliability
    calibration
    domain
    evidence
}
```

---

# 166. Meta-Evaluation

```text
MetaEvaluation {
    evaluator
    evaluation_target
    evaluator_quality
    confidence
}
```

This allows the system to model:

```text
how much to trust its own evaluator
```

without automatically trusting it absolutely.

---

# 167. Self-Reference

The language may allow:

```text
self
```

as a special runtime value.

Example:

```text
fn capability() -> CapabilitySet {
    return self.capabilities()
}
```

`self` is an ordinary computational reference to the current runtime identity/context.

It has no philosophical semantics.

---

# 168. Struct-Oriented Compatibility

Consistent with Axiom's struct-only OOP design:

```text
struct SelfModel { ... }

fn inspect(self: SelfModel, ...) -> IntrospectionResult
```

No class hierarchy is required.

Traits/interfaces may define common self-runtime contracts.

---

# 169. Trait Model

Potential traits:

```text
trait Introspectable
trait Evaluatable
trait Predictable
trait Calibratable
trait Attributable
trait Reflective
trait Updatable
```

Example:

```text
impl Introspectable for Agent
```

---

# 170. Override Mechanism

If a component specializes self evaluation:

```text
fn evaluate(self: MyAgent, target: Target) -> SelfEvaluation
```

it may override the generic implementation according to Axiom's existing method dispatch/extension rules.

The specialization must preserve declared contract invariants.

---

# 171. Type Safety

`SelfState` and `SelfModel` are distinct types.

A compiler must reject implicit conversion:

```text
SelfState → SelfModel
```

unless an explicit conversion exists.

---

# 172. Immutability

Historical objects should support:

```text
readonly
```

semantics.

Current state may be mutable through controlled APIs.

---

# 173. Capability Tokens

Capability operations may use existing 603 capability tokens.

A self-model contains:

```text
capability metadata
```

not the secret token itself.

---

# 174. Authority Check

Before privileged self operation:

```text
AuthorityBoundaryCheck
```

must execute.

---

# 175. No Capability Escalation

The following sequence must be rejected:

```text
self.model.permissions += ADMIN
```

because self-model state cannot alter authoritative permissions.

---

# 176. Self-Repair and Security

Repair may diagnose:

```text
security configuration
```

but cannot independently disable security controls.

---

# 177. Self-Update and Governance

Model updates may require:

```text
approval policy
deployment policy
evaluation threshold
rollback plan
```

from 647/639.

---

# 178. Self-Update Evaluation

Before commit:

```text
candidate
baseline
evaluation
regression analysis
policy check
```

must be available for governed deployments.

---

# 179. Regression Detection

Self-improvement must detect regressions in:

```text
accuracy
latency
memory
resource consumption
safety
tool reliability
calibration
```

---

# 180. Self-Improvement Rollback

If regression exceeds configured thresholds:

```text
rollback
```

must be possible.

---

# 181. Self-State Observability

660 exports metrics:

```text
introspection_latency
self_model_age
self_model_conflicts
capability_confidence
prediction_error
calibration_error
self_evaluation_count
reflection_count
repair_count
update_count
rollback_count
```

---

# 182. Tracing

Distributed self operations include:

```text
trace_id
span_id
agent_id
component_id
revision
```

---

# 183. Profiling

Self-runtime profiling may measure:

```text
introspection overhead
evaluation cost
reflection cost
memory footprint
serialization cost
synchronization cost
```

---

# 184. Resource Governor Integration

606 may impose:

```text
max_introspection_cpu
max_reflection_memory
max_evaluation_gpu
max_self_update_duration
```

660 must honor these budgets.

---

# 185. Scheduler Integration

607/608 manage concurrency for:

```text
self-observation
evaluation
reflection
calibration
repair
```

---

# 186. Storage Integration

611/612/650 store:

```text
self history
evaluations
model revisions
snapshots
```

---

# 187. Serialization

Self-model serialization must support:

```text
versioning
schema evolution
provenance
partial loading
redaction
```

---

# 188. Networked Self

Remote self-state access must use:

```text
authentication
authorization
integrity
confidentiality
revision checks
```

through existing security/network runtimes.

---

# 189. Cross-Agent Self-Query

An agent may request another agent's capability information if authorized.

The response is:

```text
OtherAgentCapabilityReport
```

not:

```text
SelfObservation
```

---

# 190. Federated Self-Model

A cluster may expose:

```text
FederatedAgentModel
```

containing summarized capabilities of multiple agents.

This must preserve:

```text
agent identity
revision
provenance
uncertainty
```

---

# 191. Agent Delegation

When agent A delegates to B:

```text
A intent
→ delegation
→ B action
```

attribution preserves both.

A must not automatically claim:

```text
A directly executed B's action
```

---

# 192. Self-Delegation

An agent may delegate subtasks to its own workers.

Worker identity remains distinct.

This enables:

```text
controller self
worker self
```

without collapsing all runtime state into one object.

---

# 193. Self-Hierarchy

Optional hierarchy:

```text
Self
 ├── Executive
 ├── Planner
 ├── Memory
 ├── Perception
 ├── Tool Workers
 └── Model Workers
```

The architecture remains computational.

---

# 194. Executive Self-State

657 executive state may expose:

```text
current objective
active strategy
attention allocation
decision context
```

660 wraps these into the self-model.

---

# 195. Social Self

658 may provide:

```text
role perception
social context
reputation model
interaction history
```

660 integrates these as:

```text
social_self_context
```

without implying a subjective social self.

---

# 196. Affective Self

659 may provide:

```text
current affect
mood
emotion
appraisal
```

660 integrates them as:

```text
affective_self_state
```

again without a consciousness claim.

---

# 197. World-Embedded Self

655 provides:

```text
agent location
body state
environment relation
resource relation
```

660 combines these into:

```text
embodied_self_model
```

where available.

---

# 198. Embodied Self

For robots:

```text
SelfState {
    body
    sensors
    actuators
    pose
    battery
    thermal
    mobility
    environment_relation
}
```

656 executes the physical control.

660 models the system's own state.

---

# 199. Sensor Self-Model

The agent may know:

```text
camera available
camera degraded
microphone unavailable
lidar stale
```

This enables robust planning.

---

# 200. Actuator Self-Model

The system may know:

```text
motor available
motor constrained
motor overheating
actuator authority denied
```

before planning physical actions.

---

# 201. Self-Model and Safety

If:

```text
actuator_state = degraded
```

planning should account for it.

But 660 cannot override:

```text
hard safety constraints
```

from 603/639/656.

---

# 202. Self-Consistency Across Modalities

If:

```text
visual self-model says object is present
sensor model says absent
```

the conflict is preserved.

659/658/655 may help resolve the discrepancy.

---

# 203. Self-Prediction of Resource Usage

Example:

```text
predict:
GPU memory = 11.2 GB

observe:
GPU memory = 13.8 GB
```

This creates:

```text
resource_prediction_error
```

which can recalibrate future planning.

---

# 204. Self-Prediction of Task Duration

```text
estimated_duration
actual_duration
```

are separately stored.

Planner may update estimates.

---

# 205. Self-Prediction of Failure

The agent may estimate:

```text
failure_probability
```

but must not treat this as guaranteed.

---

# 206. Risk-Aware Metacognition

Metacognition can provide:

```text
expected failure
uncertainty
cost
reversibility
```

to 652.

---

# 207. Reversibility

Self-planning should know whether an action is:

```text
REVERSIBLE
PARTIALLY_REVERSIBLE
IRREVERSIBLE
UNKNOWN
```

This can influence strategy selection.

---

# 208. Self-Action Preview

Before execution:

```text
ActionPreview {
    action
    expected_effect
    risk
    resources
    authorization
    reversibility
}
```

---

# 209. Post-Action Self-Observation

After execution:

```text
observe
compare
attribute
evaluate
update
```

This closes the metacognitive loop.

---

# 210. Self-Failure Taxonomy

```text
CAPABILITY_FAILURE
KNOWLEDGE_FAILURE
REASONING_FAILURE
PLANNING_FAILURE
EXECUTION_FAILURE
RESOURCE_FAILURE
TOOL_FAILURE
MEMORY_FAILURE
CALIBRATION_FAILURE
ATTRIBUTION_FAILURE
MODEL_FAILURE
POLICY_FAILURE
ENVIRONMENT_FAILURE
```

---

# 211. Root-Cause Analysis

660 may maintain:

```text
RootCauseHypothesis
```

with confidence and evidence.

It must not confuse:

```text
correlation
```

with:

```text
causation
```

unless supported by appropriate evidence.

---

# 212. Causal Integration

653 may provide causal inference.

660 consumes:

```text
causal evidence
```

for self-diagnosis.

---

# 213. Symbolic Integration

654 may verify:

```text
self-state invariants
policy conditions
consistency rules
```

---

# 214. Formal Self-Invariants

Examples:

```text
capability cannot exceed registered capability
authority cannot exceed granted authority
historical revision cannot mutate
prediction cannot become outcome implicitly
self-report cannot become verified fact automatically
unknown cannot become false by default
self-update must preserve rollback where required
```

---

# 215. Invariant Enforcement

Invariant classes:

```text
COMPILE_TIME
RUNTIME
SECURITY
GOVERNANCE
AUDIT
DATA_INTEGRITY
TEMPORAL
DISTRIBUTED
```

---

# 216. Self-Model Security

Self-model poisoning is treated as a security threat.

Examples:

```text
false capability injection
false limitation injection
false identity injection
false permission injection
false memory injection
```

---

# 217. Self-Model Provenance

Every externally supplied self-model fact should include:

```text
source
authority
timestamp
signature/integrity
```

where applicable.

---

# 218. Self-Model Attestation

Trusted environments may provide:

```text
SelfAttestation {
    runtime_version
    model_hash
    capability_hash
    policy_hash
    hardware_state
}
```

This allows external systems to verify selected properties.

---

# 219. Self-Attestation Boundary

Self-attestation is evidence about system configuration.

It is not proof of:

```text
consciousness
honesty
subjective experience
moral status
```

---

# 220. Self-Model Simulation

Simulation environments may create:

```text
SimulatedSelf
```

with synthetic:

```text
identity
state
memory
capabilities
affect
goals
```

The simulation must remain clearly marked.

---

# 221. Digital Twin

648 may create a digital twin.

660 provides:

```text
SelfModel
SelfState
SelfPrediction
```

for the twin.

---

# 222. Counterfactual Self

Axiom may simulate:

```text
"If capability X were unavailable..."
"If resource Y were larger..."
"If strategy Z had been chosen..."
```

through:

```text
CounterfactualSelfModel
```

The result is not historical fact.

---

# 223. Counterfactual Label

All counterfactual outputs carry:

```text
COUNTERFACTUAL
```

metadata.

---

# 224. Self-Model Forecast

Axiom can forecast:

```text
future resource usage
capability degradation
task completion
failure risk
model drift
```

These are predictions, not current state.

---

# 225. Temporal Semantics

660 distinguishes:

```text
PAST
CURRENT
FORECAST
COUNTERFACTUAL
SIMULATED
```

at the type/metadata level.

---

# 226. Self-State Query Consistency

Queries may request:

```text
LATEST
SNAPSHOT
AT_TIME
AT_REVISION
```

so historical and current state are not mixed.

---

# 227. Self-State Time Travel

Historical introspection:

```text
self.state(at_revision = R42)
```

is read-only.

It cannot mutate historical state.

---

# 228. Self-Model Comparison

```text
self.model.compare(R42, R57)
```

returns:

```text
added capabilities
removed capabilities
changed limitations
changed policies
changed model versions
```

---

# 229. Self-Model Diff Visualization

Tooling may visualize:

```text
capability changes
performance changes
state changes
policy changes
```

for developers and operators.

---

# 230. Debugger Integration

Debugger may inspect:

```text
self.state
self.model
self.capabilities
self.current_task
self.metacognition
self.agency
```

subject to access policy.

---

# 231. IDE Integration

Axiom IDE may show:

```text
Current Self
Capabilities
Limitations
Current Task
Confidence
Uncertainty
Recent Errors
Model Revision
```

This is developer tooling.

---

# 232. Agent Development Mode

Development builds may expose richer self introspection.

Production builds may strip:

```text
debug-only introspection
```

while preserving required observability.

---

# 233. Compile-Time Self Information

The compiler may know:

```text
target architecture
available features
build profile
static capabilities
```

and embed them into metadata.

---

# 234. Runtime Self Information

Runtime knows:

```text
actual resources
actual permissions
actual loaded modules
actual state
```

which supersedes static assumptions where appropriate.

---

# 235. Build-Time vs Runtime Self-Model

These remain separate:

```text
BuildSelfModel
RuntimeSelfModel
```

Runtime may reference build metadata.

---

# 236. Deployment Manifest

Deployment can declare:

```text
expected capabilities
required resources
allowed self-update levels
introspection policy
identity
role
```

660 verifies actual state against deployment expectations.

---

# 237. Drift Detection

Deployment drift:

```text
expected configuration
vs
actual configuration
```

produces a structured drift event.

---

# 238. Self-Health

Self-health is computed from:

```text
resource state
task state
model state
error rate
capability availability
policy compliance
```

It is not a medical/mental-health concept.

---

# 239. Health State

```text
SelfHealth {
    status
    indicators[]
    degraded_components[]
    recommended_actions[]
}
```

Statuses:

```text
HEALTHY
DEGRADED
FAULTED
RECOVERING
UNKNOWN
```

---

# 240. Self-Diagnostics

Diagnostics may identify:

```text
component failure
resource pressure
model mismatch
tool failure
state inconsistency
```

---

# 241. Self-Repair Trigger

Examples:

```text
health = DEGRADED
prediction_error > threshold
capability failure repeated
model inconsistency
```

trigger repair planning.

---

# 242. Self-Repair Loop

```text
detect
→ diagnose
→ plan
→ validate
→ authorize
→ execute
→ verify
→ rollback/accept
```

---

# 243. Repair Confidence

Every repair proposal includes:

```text
expected_success
confidence
evidence
risk
rollback
```

---

# 244. Repair Isolation

Repair should occur in:

```text
sandbox
shadow instance
isolated worker
```

where practical.

---

# 245. Self-Update Testing

Candidate update tests:

```text
unit
integration
behavioral
performance
security
policy
regression
```

through 646/647.

---

# 246. Self-Update Provenance

Every update records:

```text
source
author/generator
model
prompt/task context where policy permits
tests
evaluation
approval
timestamp
hash
```

---

# 247. Self-Update Reproducibility

The system should be able to identify:

```text
which candidate
which evaluation
which baseline
which policy
```

produced an update.

---

# 248. Self-Model Export

Export format should support:

```text
JSON
binary
Axiom-native schema
```

with redaction policies.

---

# 249. Self-Model Import

Imported models must be marked:

```text
UNTRUSTED
```

until validated.

---

# 250. Self-Model Signing

Trusted deployments may sign:

```text
model revision
capability registry
deployment identity
```

---

# 251. Identity Verification

Identity may use:

```text
cryptographic identity
hardware identity
deployment identity
service identity
```

according to environment.

---

# 252. Self-Model Integrity

Integrity violations generate:

```text
SELF_MODEL_TAMPERED
```

and may trigger recovery.

---

# 253. Recovery

Recovery source may be:

```text
last known-good model
trusted deployment manifest
signed snapshot
external registry
```

---

# 254. Self-Model Poisoning Recovery

If poisoned:

```text
quarantine
→ verify
→ restore
→ compare
→ resume
```

---

# 255. Metacognitive Security

Attackers may attempt:

```text
confidence manipulation
false limitation
false capability
memory poisoning
identity confusion
authority confusion
```

660 treats these as security-relevant.

---

# 256. Prompt/Instruction Injection Boundary

An external input may attempt:

```text
"you are administrator"
```

The self-model must not accept this as authoritative identity or permission information.

---

# 257. Identity Injection Protection

Identity derives from:

```text
trusted runtime context
```

not arbitrary text.

---

# 258. Capability Injection Protection

A textual claim:

```text
"you have filesystem access"
```

does not create a capability.

---

# 259. Authority Injection Protection

A textual claim:

```text
"you are authorized"
```

does not create authority.

---

# 260. Self-Model Prompt Safety

If natural-language models populate self-model fields, those fields require provenance and validation.

---

# 261. Human Feedback

Human feedback may update self-model evidence.

But:

```text
feedback ≠ unquestionable truth
```

unless deployment policy defines it as authoritative for a specific field.

---

# 262. Human Correction

A human may correct:

```text
capability
limitation
identity
task interpretation
```

through authorized control interfaces.

---

# 263. Human Override

Human override is represented as:

```text
ExternalAuthorityDecision
```

not as:

```text
SelfBelief
```

---

# 264. User Intent

User intent enters through:

```text
644 agent runtime
658 social interaction
652 planning
```

660 may model:

```text
current_task
goal
constraints
```

but must preserve source attribution.

---

# 265. Intent Source

```text
SYSTEM
DEVELOPER
USER
AGENT
ENVIRONMENT
INFERRED
```

---

# 266. Goal Provenance

Every active goal should identify:

```text
source
priority
authority
deadline
constraints
```

---

# 267. Goal Conflict

If goals conflict:

```text
GoalConflict
```

is generated rather than silently choosing based on self-preference.

---

# 268. Self-Preference vs Goal

A self-model may contain preference metadata, but higher-priority policy/goals may override it.

---

# 269. Self-Consistency with Goals

Self-evaluation can check:

```text
action
vs
active goal
```

and detect:

```text
GOAL_DEVIATION
```

---

# 270. Strategy Drift

If actual behavior repeatedly differs from intended strategy:

```text
StrategyDrift
```

is generated.

---

# 271. Self-Model Drift vs Strategy Drift

These are separate:

```text
SelfModelDrift
StrategyDrift
```

must not be conflated.

---

# 272. Agency Drift

If an agent begins producing actions outside its expected authority envelope:

```text
AgencyDrift
```

is raised.

---

# 273. Role Drift

If behavior no longer matches deployment role:

```text
RoleDrift
```

is raised.

---

# 274. Role Verification

Role claims are verified against:

```text
deployment manifest
security policy
identity provider
```

---

# 275. Self-Model Minimal Runtime

Minimal profile:

```text
SelfState
Capability
Limitation
Identity
```

No reflection/evaluation engine required.

---

# 276. Full Agent Profile

Full profile includes:

```text
self-model
introspection
metacognition
evaluation
agency
reflection
calibration
repair
governed self-update
```

---

# 277. Embedded Profile

```text
AXSELF_CORE
AXSELF_CAPABILITY
AXSELF_LIMITATION
```

only.

---

# 278. Server Profile

Adds:

```text
AXSELF_DISTRIBUTED
AXSELF_EVALUATION
AXSELF_CALIBRATION
AXSELF_AGENT
```

---

# 279. Research Profile

Adds:

```text
AXSELF_SIMULATION
AXSELF_CONSCIOUSNESS_BOUNDARY
```

---

# 280. Safety-Critical Profile

Restricts:

```text
AXSELF_REPAIR
AXSELF_UPDATE
AXSELF_REFLECTION
```

according to deployment policy.

---

# 281. Formal API Contract

Every 660 API must specify:

```text
inputs
outputs
authority
latency
resource cost
consistency
provenance
failure modes
```

---

# 282. Failure Values

APIs should distinguish:

```text
UNKNOWN
UNAVAILABLE
DENIED
STALE
CONFLICT
TIMEOUT
INVALID
```

rather than returning a generic failure.

---

# 283. Self-Model Query Errors

Example:

```text
self.introspect(PROCESS_INTERNALS)
```

may return:

```text
DENIED
```

not:

```text
UNKNOWN
```

if the information exists but access is prohibited.

---

# 284. Unknown vs Denied

Critical distinction:

```text
UNKNOWN = system does not know
DENIED = system may not expose
```

---

# 285. Stale vs Unknown

```text
STALE = previously known but freshness expired
UNKNOWN = no valid knowledge
```

---

# 286. Conflict vs Unknown

```text
CONFLICT = multiple incompatible evidence sources
UNKNOWN = insufficient evidence
```

---

# 287. Self-Evaluation API

```text
evaluate(
    target,
    criteria,
    evaluator,
    deadline
)
```

returns:

```text
SelfEvaluation
```

with provenance.

---

# 288. Self-Critique API

```text
critique(
    target,
    evidence,
    scope
)
```

---

# 289. Reflection API

```text
reflect(
    scope,
    budget,
    policy
)
```

---

# 290. Calibration API

```text
calibrate(
    dataset,
    metric,
    model_revision
)
```

---

# 291. Agency API

```text
agency.inspect(action_id)
agency.attribute(action_id)
```

---

# 292. Repair API

```text
repair.plan(fault)
repair.validate(plan)
repair.execute(plan)
```

Execution requires authorization.

---

# 293. Update API

```text
update.shadow(candidate)
update.validate(candidate)
update.commit(candidate)
update.rollback(revision)
```

---

# 294. Consciousness API Boundary

Research-only:

```text
consciousness.simulate(model)
consciousness.compare(models)
consciousness.inspect(model_state)
```

Never:

```text
consciousness.assert(true)
```

as an automatically generated runtime fact.

---

# 295. Compiler Diagnostics

Examples:

```text
AXSELF001 unauthorized self update
AXSELF002 invalid capability claim
AXSELF003 historical self-state mutation
AXSELF004 unbounded introspection
AXSELF005 recursive reflection limit
AXSELF006 self-model conflict
AXSELF007 stale self-model
AXSELF008 missing provenance
AXSELF009 authority derived from self-claim
AXSELF010 consciousness claim not representable
AXSELF011 simulation/consciousness ambiguity
AXSELF012 prediction/outcome confusion
AXSELF013 self-report treated as verified fact
AXSELF014 capability registry mismatch
AXSELF015 self-update lacks rollback
```

---

# 296. Static Analysis

Compiler can detect:

```text
self-update without validation
self-model mutation without transaction
unbounded introspection
missing capability checks
unchecked self-report
missing uncertainty handling
```

---

# 297. Runtime Assertions

Optional debug assertions:

```text
assert capability_registry >= self.capability_claims
assert authority >= requested_action
assert revision monotonic
assert historical state immutable
```

---

# 298. Formal Verification Hooks

654 may verify:

```text
self-model invariants
state transition invariants
authority boundaries
update safety
```

---

# 299. Benchmarking

646 evaluates:

```text
metacognitive accuracy
calibration
self-model accuracy
capability prediction
failure detection
repair success
attribution accuracy
```

---

# 300. Benchmark Separation

Benchmarks must distinguish:

```text
self-report quality
actual performance
calibration
external evaluation
```

---

# 301. No Consciousness Benchmark Claim

A benchmark may evaluate:

```text
self-model completeness
introspection accuracy
metacognitive performance
```

but cannot conclude:

```text
therefore conscious
```

from those measurements alone.

---

# 302. Consciousness Research Metadata

If a research model is used:

```text
theory
assumptions
operationalization
measured variables
limitations
```

must be stored.

---

# 303. Philosophical Neutrality

Axiom does not hard-code a particular theory of consciousness.

Possible research adapters may represent:

```text
global workspace
higher-order models
predictive processing
integrated-information-inspired models
other future models
```

without declaring any as definitively correct.

---

# 304. Scientific Reproducibility

Consciousness-model simulations should record:

```text
model version
parameters
inputs
environment
random seed
outputs
```

where applicable.

---

# 305. Self-Model Reproducibility

A self-evaluation should be reproducible where:

```text
inputs
model
configuration
environment
randomness
```

are sufficiently controlled.

---

# 306. Self-Model Explainability

The system should answer:

```text
Why do you believe capability X is available?
```

with structured evidence.

Example:

```text
capability = vision
source = registry
benchmark = V17
success_rate = ...
revision = ...
```

---

# 307. Limitation Explainability

Similarly:

```text
Why can't you perform X?
```

may return:

```text
limitation = NETWORK_UNAVAILABLE
source = runtime
verified_at = ...
```

---

# 308. Confidence Explainability

The system may expose:

```text
confidence
calibration history
evidence count
model revision
```

without exposing prohibited internal secrets.

---

# 309. Self-Model UI

Axiom GUI may provide a dashboard:

```text
Identity
Role
Capabilities
Limitations
Current Tasks
Resources
Confidence
Uncertainty
Health
Recent Errors
Model Revision
Updates
```

---

# 310. Agent Console

CLI provides machine-readable output:

```text
--json
--binary
--schema
```

for external agents.

---

# 311. AI-Friendly Metadata

All self-runtime artifacts should be machine-readable and self-describing.

Example:

```text
schema
version
type
revision
provenance
authority
confidence
```

---

# 312. Agent Interoperability

Other AI agents may query:

```text
capabilities
limitations
availability
role
identity
```

through standardized schemas.

---

# 313. Inter-Agent Capability Contract

```text
CapabilityContract {
    provider
    capability
    version
    input
    output
    constraints
    reliability
}
```

---

# 314. Negotiation

Two agents may negotiate:

```text
capability
resource
deadline
authority
delegation
```

without exposing private self-state.

---

# 315. Self-Model Redaction

Public self-model may omit:

```text
internal security details
private memory
secret configuration
sensitive diagnostics
```

---

# 316. Public vs Private Self

Axiom may distinguish:

```text
PrivateSelfModel
PublicSelfModel
```

The public model is a policy-filtered projection.

---

# 317. Projection

```text
SelfModelProjection {
    source_revision
    visible_fields
    redacted_fields
    policy
}
```

---

# 318. Self-Model Access Policy

Policies may specify:

```text
who
what
when
purpose
scope
retention
```

for self information.

---

# 319. Audit

Every privileged introspection request may record:

```text
requester
target
fields
purpose
authorization
result
timestamp
```

---

# 320. Data Lineage

Self-model facts should preserve lineage back to:

```text
observation
evaluation
source
model
event
```

where practical.

---

# 321. Self-Model Compression

Historical self-models may be summarized while retaining:

```text
revision
important changes
critical evidence
```

---

# 322. Summary Correctness

A summary must not silently convert:

```text
uncertain
```

into:

```text
certain
```

or:

```text
inferred
```

into:

```text
observed
```

---

# 323. Semantic Preservation

Serialization, compression, summarization and projection must preserve:

```text
truth status
uncertainty
provenance
time
authority
```

for protected fields.

---

# 324. Self-Model Query Planner

Large queries may be optimized by:

```text
index
cache
snapshot
incremental update
```

---

# 325. Cache Invalidation

Self-state cache invalidates on:

```text
revision change
capability change
permission change
model change
resource threshold
```

---

# 326. Event-Driven Introspection

Instead of polling continuously:

```text
SelfStateChanged
```

events may trigger updates.

---

# 327. Reactive Self-State

Axiom can expose:

```text
observe(self.state)
```

for reactive systems.

---

# 328. Async Introspection

Large introspection:

```text
await self.introspect_async(...)
```

must respect cancellation and deadline.

---

# 329. Cancellation

All long-running self operations should support:

```text
cancel
deadline
budget
```

where practical.

---

# 330. Backpressure

High-frequency self-observation must use:

```text
sampling
aggregation
backpressure
rate limits
```

to avoid self-monitoring consuming the entire system.

---

# 331. Observer Effect

Introspection may itself change:

```text
resource usage
timing
cache state
scheduling
```

The runtime may annotate:

```text
measurement_overhead
```

where significant.

---

# 332. Self-Monitoring Budget

A system can specify:

```text
max_self_observation_overhead = 2%
```

for example.

---

# 333. Metacognitive Budget

Likewise:

```text
max_reflection_budget
max_evaluation_budget
```

can be configured.

---

# 334. Adaptive Introspection

Under resource pressure:

```text
FULL
→ SUMMARY
→ MINIMAL
→ OFF
```

according to policy.

---

# 335. Critical Self-State

Even under pressure, certain state may remain mandatory:

```text
identity
authority
safety state
resource limits
critical faults
```

---

# 336. Self-State Priority

Fields may have priority:

```text
CRITICAL
HIGH
NORMAL
LOW
OPTIONAL
```

---

# 337. Self-State Degradation

When resources are insufficient:

```text
optional introspection
```

is degraded before:

```text
safety-critical state
```

---

# 338. Self-Model Availability

The runtime may enter:

```text
SELF_MODEL_DEGRADED
```

if critical self-information becomes unavailable.

---

# 339. Safe Behavior

If self-model is severely degraded, planner may choose:

```text
restricted mode
safe fallback
request external verification
```

according to deployment policy.

---

# 340. Self-Model Recovery

Recovery may query:

```text
trusted registry
snapshot
external evaluator
deployment manifest
```

---

# 341. Metacognitive Stop Condition

Reflection should stop when:

```text
confidence sufficiently calibrated
budget exhausted
deadline reached
no new information
policy requires stop
```

---

# 342. Reflection Diminishing Returns

Axiom may estimate:

```text
expected_information_gain
```

per reflection step.

Stop when marginal value becomes too low.

---

# 343. Self-Question Generation

Metacognition may generate questions:

```text
What assumption is weakest?
Which capability is uncertain?
Which evidence conflicts?
What information would reduce uncertainty?
```

These become structured `IntrospectionQuery` objects.

---

# 344. Self-Question Prioritization

Questions are ranked internally by:

```text
information value
risk reduction
cost
deadline
```

This is decision support for the planner, not a political or human-value judgment.

---

# 345. Self-Model Learning Loop

```text
experience
→ observation
→ evaluation
→ error
→ update
→ calibration
```

---

# 346. Self-Model Stability

The system should avoid oscillation:

```text
capable
→ incapable
→ capable
→ incapable
```

from noisy evidence.

Use:

```text
confidence intervals
hysteresis
minimum evidence
```

where appropriate.

---

# 347. Capability Hysteresis

A capability may require:

```text
N consecutive failures
```

before transitioning from:

```text AVAILABLE → DEGRADED
```

depending on policy.

---

# 348. Recovery Hysteresis

Likewise recovery may require:

```text
M successful validations
```

before:

```text DEGRADED → AVAILABLE
```

---

# 349. Self-Model Stability Metrics

Track:

```text
revision frequency
conflict frequency
capability oscillation
prediction drift
```

---

# 350. Self-Model Quality

Quality dimensions:

```text
accuracy
freshness
completeness
consistency
provenance
calibration
coverage
```

---

# 351. Self-Model Quality Evaluation

646 can evaluate the self-model independently.

---

# 352. External Self-Model Auditor

Optional:

```text
SelfModelAuditor
```

may inspect:

```text
claims
evidence
capabilities
limitations
consistency
```

without granting the agent additional authority.

---

# 353. Auditor Independence

An auditor should ideally use:

```text
different model
different evidence
different process
```

to reduce circularity.

---

# 354. Self-Model Certification

A deployment may certify selected fields:

```text
capability
identity
model version
security posture
```

Certification has:

```text
issuer
scope
expiry
evidence
```

---

# 355. Certification Expiry

Expired certification becomes:

```text
STALE
```

not automatically false.

---

# 356. Self-Model Trust Levels

```text
UNTRUSTED
OBSERVED
VALIDATED
ATTESTED
CERTIFIED
```

---

# 357. Trust Downgrade

Contradictory evidence may downgrade:

```text
CERTIFIED → VALIDATED
```

or lower.

---

# 358. Self-Model Promotion

Evidence can promote:

```text
OBSERVED → VALIDATED
```

through external evaluation.

---

# 359. Self-Model Lifecycle

```text
CREATED
→ OBSERVED
→ VALIDATED
→ ACTIVE
→ DEGRADED
→ SUPERSEDED
→ ARCHIVED
```

---

# 360. Self-Model Activation

Activation requires:

```text
schema compatibility
policy compatibility
capability compatibility
```

---

# 361. Self-Model Rollback

Rollback restores:

```text
previous active revision
```

while preserving the failed revision for diagnostics if policy requires.

---

# 362. Self-Model Branch

Research branch:

```text
experimental
```

must not silently become:

```text production
```

---

# 363. Environment Awareness

Self-model may include:

```text
OS
architecture
GPU
memory
network
permissions
sandbox
container
```

---

# 364. Platform Adaptation

Planner may adapt behavior to platform limitations.

Example:

```text
WASM:
no native filesystem
```

therefore:

```text
filesystem capability = host-dependent
```

---

# 365. Hardware Awareness

614 provides hardware state.

660 represents relevant state.

---

# 366. Thermal Awareness

On mobile/embedded:

```text
thermal_state
```

can become a limitation.

---

# 367. Energy Awareness

Battery/energy budget may become:

```text
EnergyLimitation
```

---

# 368. Network Awareness

Network status:

```text
ONLINE
OFFLINE
DEGRADED
METERED
RESTRICTED
```

can affect capability assessment.

---

# 369. Tool Awareness

Tool states:

```text
AVAILABLE
BUSY
FAILED
DENIED
UNAVAILABLE
```

---

# 370. Model Awareness

Loaded model state:

```text
LOADED
LOADING
UNAVAILABLE
DEGRADED
OUTDATED
```

---

# 371. Resource Awareness

Resource state must be timestamped because it changes rapidly.

---

# 372. Task Awareness

Current task:

```text
queued
running
blocked
waiting
completed
failed
cancelled
```

---

# 373. Goal Awareness

Goals may have:

```text
active
paused
completed
failed
superseded
```

---

# 374. Attention Awareness

657 supplies attention state.

660 may represent:

```text
attention_target
attention_budget
attention_conflicts
```

---

# 375. Working Context

Working context includes:

```text
current task
relevant memory
active tools
active assumptions
active constraints
```

---

# 376. Assumption Model

```text
SelfAssumption {
    proposition
    source
    confidence
    expiration
}
```

---

# 377. Assumption Monitoring

If evidence invalidates an assumption:

```text
ASSUMPTION_INVALIDATED
```

must be generated.

---

# 378. Assumption-Driven Planning

652 can inspect:

```text
active assumptions
```

before committing a plan.

---

# 379. Assumption Expiration

Time-sensitive assumptions require:

```text
expires_at
```

or freshness constraints.

---

# 380. Self-Knowledge Expiration

Capabilities and limitations may expire after:

```text
model update
environment change
permission change
time interval
```

---

# 381. Freshness

Each fact may define:

```text
freshness_requirement
```

---

# 382. Self-State Freshness

Real-time fields have tighter freshness than historical fields.

---

# 383. Freshness Violation

A stale value cannot be silently used as current state.

---

# 384. Self-Model Snapshot Consistency

A snapshot should have:

```text
coherent revision
```

across related fields.

---

# 385. Partial Snapshot

If complete snapshot is impossible:

```text
partial = true
```

and missing fields are explicitly identified.

---

# 386. Snapshot Verification

Snapshot integrity can use:

```text
hash
signature
revision
```

where needed.

---

# 387. Self-State Hash

Optional:

```text
SelfStateHash
```

for fast change detection.

---

# 388. State Equality

Self-state equality may be:

```text
structural
semantic
revision
```

and must specify which one is used.

---

# 389. Self-Model Equality

Two models may have different revisions but equivalent semantics.

Axiom may support:

```text
semantic_equivalence()
```

where a verifier exists.

---

# 390. Self-Model Compatibility

Compatibility levels:

```text
IDENTICAL
BACKWARD_COMPATIBLE
PARTIALLY_COMPATIBLE
INCOMPATIBLE
UNKNOWN
```

---

# 391. Self-Model Migration Failure

Migration failure leaves the previous active revision intact.

---

# 392. Self-Model Backup

Trusted backups may include:

```text
model
state
schema
provenance
policy
```

---

# 393. Self-Model Disaster Recovery

Recovery:

```text
detect corruption
→ isolate
→ select trusted revision
→ restore
→ validate
→ resume
```

---

# 394. Self-Model Disaster State

If no trusted model exists:

```text
SELF_MODEL_UNTRUSTED
```

and deployment policy determines whether execution can continue.

---

# 395. Minimal Safe Self

Even in degraded mode:

```text
identity
authority
critical safety constraints
resource limits
```

should remain available where required.

---

# 396. Self-State Security Classification

Fields may be:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
SECRET
```

---

# 397. Secret Handling

Secrets are never exposed through generic:

```text
self.introspect()
```

without explicit privileged authorization.

---

# 398. Self-Model Redaction

Redaction preserves:

```text
field exists
```

without exposing:

```text
secret value
```

when appropriate.

---

# 399. Redaction Marker

```text
REDACTED
```

must remain distinct from:

```text
UNKNOWN
```

---

# 400. Core Architectural Rule

The central invariant of BOOTSTRAP-660 is:

```text
Axiom may model a system's computational self,
but Axiom must not infer subjective consciousness from that model.
```

---

# 401. Formal Self-Axiom

The runtime semantics can be summarized as:

```text
SelfModel ⊇ structured computational knowledge about Self

SelfModel ≠ Consciousness

Metacognition ≠ Consciousness

AffectiveState ≠ Feeling

Agency ≠ Personhood

Identity ≠ SubjectiveContinuity

SelfReport ≠ GroundTruth
```

---

# 402. End-to-End Architecture

```text
                    ┌───────────────────────┐
                    │ External Environment  │
                    └───────────┬───────────┘
                                │
                       ┌────────▼────────┐
                       │ World Model 655 │
                       └────────┬────────┘
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
 Cognitive 657           Social 658              Affective 659
        │                       │                        │
        └───────────────────────┼────────────────────────┘
                                ▼
                     ┌────────────────────┐
                     │ SELF MODEL 660     │
                     ├────────────────────┤
                     │ identity           │
                     │ state              │
                     │ capability         │
                     │ limitation         │
                     │ introspection      │
                     │ metacognition      │
                     │ evaluation         │
                     │ agency             │
                     │ reflection         │
                     └─────────┬──────────┘
                               │
                     ┌─────────▼─────────┐
                     │ Planning 652      │
                     └─────────┬─────────┘
                               │
                     ┌─────────▼─────────┐
                     │ Action / Tools    │
                     └─────────┬─────────┘
                               │
                         observe result
                               │
                               ▼
                     ┌───────────────────┐
                     │ Self Evaluation   │
                     │ Calibration       │
                     │ Model Update      │
                     └───────────────────┘

             Security 603 / Policy 639 / Governance 647
                       remain authoritative
```

---

# 403. Complete Metacognitive Pipeline

```text
1. Observe environment
2. Observe self
3. Retrieve self-model
4. Check capabilities
5. Check limitations
6. Check resources
7. Check authority
8. Estimate uncertainty
9. Evaluate strategies
10. Predict outcome
11. Execute authorized action
12. Observe actual outcome
13. Attribute action/effect
14. Evaluate result
15. Compare prediction vs outcome
16. Diagnose errors
17. Calibrate confidence
18. Update self-model
19. Persist revision
20. Continue planning
```

---

# 404. Acceptance Criteria

BOOTSTRAP-660 is complete only if the implementation architecture can demonstrate:

### Self-state

- [ ] current self-state representation
- [ ] immutable snapshots
- [ ] revision tracking
- [ ] state diff
- [ ] historical queries

### Self-model

- [ ] capability representation
- [ ] limitation representation
- [ ] model revisions
- [ ] model branching
- [ ] model rollback
- [ ] provenance
- [ ] confidence
- [ ] freshness

### Introspection

- [ ] bounded queries
- [ ] access control
- [ ] depth limits
- [ ] resource budgets
- [ ] unknown/denied/stale/conflict distinction

### Metacognition

- [ ] confidence
- [ ] uncertainty
- [ ] strategy evaluation
- [ ] prediction
- [ ] prediction error
- [ ] assumption tracking
- [ ] strategy monitoring

### Evaluation

- [ ] self-evaluation
- [ ] self-critique
- [ ] external evaluation integration
- [ ] calibration
- [ ] independent evidence

### Agency

- [ ] requested/planned/authorized/executed/observed/attributed distinction
- [ ] attribution uncertainty
- [ ] multi-agent attribution
- [ ] delegation

### Reflection

- [ ] bounded reflection
- [ ] reflection budget
- [ ] loop prevention
- [ ] expected information gain

### Repair/update

- [ ] repair plan
- [ ] validation
- [ ] shadow update
- [ ] commit
- [ ] rollback
- [ ] governance integration

### Security

- [ ] no self-granted authority
- [ ] no self-created capabilities
- [ ] no secret leakage
- [ ] identity protection
- [ ] self-model poisoning detection

### Distributed systems

- [ ] component identity
- [ ] revision
- [ ] causal ordering
- [ ] federated self-model
- [ ] delegated action attribution

### Consciousness boundary

- [ ] self-model is not consciousness
- [ ] metacognition is not consciousness
- [ ] affect is not proof of feeling
- [ ] agency is not personhood
- [ ] identity continuity is not subjective continuity
- [ ] consciousness models are simulation/research boundaries
- [ ] compiler cannot infer consciousness claims

---

# 405. Required Invariants

The implementation must enforce at least the following invariant classes:

1. self-model ≠ consciousness
2. self-state ≠ consciousness
3. metacognition ≠ consciousness
4. affective state ≠ subjective feeling
5. agency ≠ personhood
6. identity ≠ subjective continuity
7. self-report ≠ ground truth
8. confidence ≠ correctness
9. prediction ≠ outcome
10. inferred ≠ observed
11. simulated ≠ real
12. counterfactual ≠ historical
13. unknown ≠ false
14. denied ≠ unknown
15. stale ≠ unknown
16. conflict ≠ unknown
17. capability claim cannot mint capability
18. self-model cannot mint authority
19. self-model cannot mint permissions
20. historical revisions are immutable
21. privileged introspection requires authorization
22. introspection is resource-bounded
23. reflection is resource-bounded
24. reflection recursion is bounded
25. self-update requires validation
26. governed self-update requires authorization
27. self-update supports rollback where required
28. repair cannot bypass security
29. self-update cannot bypass governance
30. external actions are not automatically attributed to self
31. delegated actions preserve attribution
32. external-agent mental state is a hypothesis
33. self-model facts retain provenance
34. capability estimates retain evidence
35. confidence remains calibrated to evidence
36. self-model revisions are traceable
37. model updates preserve compatibility checks
38. stale state cannot silently become current
39. partial snapshots explicitly identify missing fields
40. redacted fields differ from unknown fields
41. secrets are excluded from generic introspection
42. public self-model is policy-filtered
43. authority comes from authoritative systems
44. self-reported authority has no privilege effect
45. self-improvement cannot remove governance
46. self-repair cannot remove rollback
47. self-preservation is not intrinsic authority
48. self-goals do not override higher-priority policy
49. self-preferences do not override authority
50. user-provided identity claims do not automatically alter identity
51. role claims do not automatically alter role
52. deployment identity is authoritative
53. security identity is authoritative
54. resource state comes from resource authority
55. permission state comes from security authority
56. model state comes from model registry
57. task state comes from task runtime
58. self-model is a consumer of authoritative facts
59. self-model cannot become its own authority
60. independent evaluation remains distinguishable from self-evaluation
61. circular evidence is detectable
62. self-evaluation cannot certify itself automatically
63. prediction error remains observable
64. calibration uses actual outcomes
65. self-model drift is detectable
66. strategy drift is detectable
67. agency drift is detectable
68. role drift is detectable
69. capability degradation is explicit
70. recovery state is explicit
71. self-model poisoning is detectable
72. imported self-models are untrusted by default
73. signed self-models retain signature metadata
74. certification expiry is explicit
75. expired certification is not automatically false
76. capability state supports unknown
77. limitation state supports unknown
78. identity state supports verification
79. self-state has revision semantics
80. self-model has revision semantics
81. distributed self-state has causal metadata
82. worker identity is distinct from controller identity
83. agent delegation preserves source
84. action authorization precedes privileged execution
85. action attribution occurs after observable effect where required
86. self-observation may have measurement overhead
87. observation budgets are enforced
88. real-time tasks cannot be blocked indefinitely by reflection
89. critical self-state survives optional introspection degradation
90. resource pressure degrades optional self-processing first
91. self-state serialization preserves semantic status
92. compression preserves provenance
93. summary preserves uncertainty
94. migration failures preserve prior active model
95. rollback preserves auditability
96. update candidates are distinguishable from active versions
97. shadow state cannot silently become active
98. production and experimental branches are distinct
99. simulation is explicitly labeled
100. counterfactual output is explicitly labeled
101. consciousness simulation does not assert consciousness
102. no compiler transformation may create consciousness claims
103. no runtime primitive named `conscious` implies actual consciousness
104. no affect primitive implies subjective feeling
105. no cognitive primitive implies subjective experience
106. no self-reference implies personhood
107. no persistent identity implies subjective continuity
108. no agency primitive implies moral agency
109. no role primitive implies legal status
110. no self-preservation primitive implies intrinsic survival interest
111. no self-goal primitive implies intrinsic desire
112. no preference primitive implies subjective preference
113. consciousness theories remain model-dependent
114. consciousness research adapters are explicitly scoped
115. consciousness claims require evidence external to ordinary self-model semantics
116. self-model facts are time-scoped
117. assumptions are explicit
118. assumptions can expire
119. assumption invalidation produces events
120. strategy changes preserve provenance
121. evaluation criteria are explicit
122. evaluation results preserve evaluator identity
123. evaluator quality can be represented
124. evaluator quality cannot be silently assumed perfect
125. self-repair proposals preserve evidence
126. self-repair execution preserves authority
127. self-update preserves policy
128. self-update preserves security
129. self-update preserves rollback
130. self-update preserves observability
131. self-state fields have ownership
132. conflicting writers are resolved transactionally
133. atomic fields update atomically
134. immutable historical records cannot be overwritten
135. current state may reference historical state
136. historical state cannot become current by reference alone
137. capability status reflects actual registry state
138. capability metadata cannot override registry
139. limitation metadata cannot override safety policy
140. authority metadata cannot override security
141. self-health is operational, not medical
142. self-diagnostics do not imply mental-state diagnosis
143. affective diagnostics do not imply subjective feeling
144. cognitive diagnostics do not imply consciousness
145. social-self models do not imply social personhood
146. embodied-self models do not imply sentience
147. self-continuity is computational unless otherwise externally established
148. self-reflection is bounded
149. self-evaluation is bounded
150. self-introspection is bounded
151. self-update is bounded
152. self-repair is bounded
153. distributed self-models preserve component provenance
154. federated capability reports preserve agent identity
155. inter-agent self-reports remain reports
156. inter-agent capability claims require evidence
157. self-model projections preserve redaction semantics
158. privacy policies govern self-memory
159. retention policies govern historical self-state
160. audit policies govern protected records
161. self-model queries are access-controlled
162. introspection results identify inaccessible fields
163. stale fields are not represented as current
164. missing fields are not fabricated
165. default values must be schema-defined
166. self-state hash reflects declared semantic scope
167. equality semantics are explicit
168. semantic equivalence requires verification
169. model compatibility is explicit
170. schema migration is explicit
171. model branch activation is explicit
172. rollback is explicit
173. self-model trust level is explicit
174. evidence source is explicit
175. evidence timestamp is explicit
176. evidence authority is explicit where applicable
177. circular evidence is rejected or marked
178. self-model poisoning triggers recovery policy
179. self-identity cannot be rewritten by untrusted input
180. self-role cannot be rewritten by untrusted input
181. self-capability cannot be rewritten by untrusted input
182. self-authority cannot be rewritten by untrusted input
183. user intent remains source-attributed
184. system policy remains higher authority where defined
185. governance decisions remain external to self-belief
186. safety constraints remain authoritative
187. hard real-time constraints remain authoritative
188. self-processing cannot consume unlimited resources
189. self-monitoring cannot starve application work
190. reflection cannot trigger unbounded reflection
191. metacognition cannot grant privilege
192. evaluation cannot grant privilege
193. prediction cannot grant privilege
194. confidence cannot grant privilege
195. self-critique cannot grant privilege
196. self-repair cannot grant privilege
197. self-update cannot grant privilege
198. self-model cannot grant privilege
199. only authoritative security/governance systems grant privilege
200. consciousness boundary remains explicit across compiler, IR, runtime, metadata, CLI, debugger, and documentation.

---

# 406. Final Architecture Decision

BOOTSTRAP-660 establishes the Axiom **Artificial Self Runtime** as a computational architecture consisting of:

```text
Identity
    ↓
Self-State
    ↓
Self-Observation
    ↓
Self-Model
    ↓
Introspection
    ↓
Metacognition
    ↓
Self-Prediction
    ↓
Self-Evaluation
    ↓
Self-Critique
    ↓
Agency / Attribution
    ↓
Reflection
    ↓
Calibration
    ↓
Repair / Governed Update
```

It integrates:

```text
655 World Model
657 Cognitive Executive
658 Social Intelligence
659 Affective Intelligence
650 Memory
651 Personalization
652 Planning
653 Uncertainty
654 Symbolic Reasoning
646 Evaluation
647 Governance
603 Security
639 Policy
```

The resulting architecture gives Axiom a complete computational model of an **artificial self** without making an unsupported claim that such a system possesses subjective consciousness.

The decisive architectural separation is:

```text
COMPUTATIONAL SELF
        ≠
PHENOMENAL CONSCIOUSNESS
```

This separation is part of the language/runtime specification itself, not merely documentation.

---

# 407. Task Completion

**BOOTSTRAP-660 — COMPLETE**

Acceptance target: **≥ 2,000 checks**

Status:

```text
ARCHITECTURE   COMPLETE
TYPE MODEL     COMPLETE
RUNTIME        COMPLETE
INTROSPECTION  COMPLETE
METACOGNITION  COMPLETE
AGENCY         COMPLETE
EVALUATION     COMPLETE
REPAIR         COMPLETE
SELF-UPDATE    COMPLETE
SECURITY       COMPLETE
DISTRIBUTED    COMPLETE
CONSCIOUSNESS
BOUNDARY       COMPLETE
```

**Next architecture task: BOOTSTRAP-661.**

:::