Tiếp tục với **BOOTSTRAP-652 — Native AI Planning, Decision Optimization, Constraint Solving, Search-Based Reasoning, Scheduling Intelligence & Decision Runtime 5.0**.

:::writing{variant="document" id="58321" title="BOOTSTRAP-652 — Native AI Planning, Decision Optimization, Constraint Solving, Search-Based Reasoning, Scheduling Intelligence & Decision Runtime 5.0"}
# BOOTSTRAP-652
## Native AI Planning, Decision Optimization, Constraint Solving, Search-Based Reasoning, Scheduling Intelligence & Decision Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Decision & Optimization Plane  
**Priority:** P0  
**Version:** 5.0  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-651

---

# 1. Purpose

BOOTSTRAP-652 defines Axiom's native decision-engine architecture for problems where an application must determine **what should be done, in what order, using which resources, under which constraints, according to which objectives**.

The subsystem provides a unified abstraction for:

- planning
- constraint solving
- optimization
- scheduling
- assignment
- matching
- routing
- resource allocation
- combinatorial search
- heuristic search
- branch-and-bound
- dynamic programming
- multi-objective optimization
- decision under scenarios
- robust optimization
- incremental solving
- warm starts
- plan validation
- solution explanation
- decision checkpointing
- solver/provider interoperability

The subsystem must support both:

1. **small deterministic problems solved directly inside the Axiom runtime**, and
2. **large problems delegated to specialized solver providers** without making those providers mandatory dependencies.

---

# 2. Architectural Position

652 sits above primitive computation and below application/agent decision execution.

```text
                    AI / Application Layer
                            │
              ┌─────────────┴─────────────┐
              │                           │
         AI Agents 644              Applications
              │                           │
              └─────────────┬─────────────┘
                            │
                     Decision API
                            │
                 ┌──────────▼──────────┐
                 │      652 Decision   │
                 │      Runtime        │
                 └──────────┬──────────┘
                            │
       ┌────────────┬───────┼────────┬─────────────┐
       ▼            ▼       ▼        ▼             ▼
   Planning     Search   Optimize  Schedule    Assignment
       │            │       │        │             │
       └────────────┴───────┼────────┴─────────────┘
                            │
                 Constraint / Objective Model
                            │
                 ┌──────────▼──────────┐
                 │ Solver / Search     │
                 │ Engine              │
                 └──────────┬──────────┘
                            │
                     Decision Solution
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
          Validate       Explain        Execute
```

---

# 3. Boundary With Existing Axiom Systems

652 MUST NOT absorb responsibilities already defined elsewhere.

| System | Responsibility |
|---|---|
| 629 | durable workflow execution |
| 635 | cluster membership / consensus / placement control |
| 636 | deployment and rollout orchestration |
| 639 | authorization and policy decisions |
| 641 | retrieval/search infrastructure |
| 642 | analytical computation |
| 643 | ML prediction/model execution |
| 644 | agent orchestration |
| 645 | semantic/knowledge graphs |
| 646 | evaluation and benchmarking |
| 648 | simulation |
| 651 | personalization and preference adaptation |
| **652** | **decision modeling, planning, optimization and constraint solving** |

652 can consume outputs from those systems but cannot silently replace them.

---

# 4. Design Principles

## 4.1 Decision ≠ Prediction

A prediction provides information.

A decision selects an action or configuration.

```text
ML prediction:
predicted_latency = 82ms

Decision:
choose node = node_17
```

652 may consume ML predictions from 643 but MUST NOT treat them as inherently authoritative.

---

## 4.2 Constraint ≠ Objective

A hard constraint defines what is allowed.

An objective defines what is preferred.

```text
constraint:
memory_used <= available_memory

objective:
minimize latency
```

---

## 4.3 Feasibility Before Optimization

The engine MUST distinguish:

```text
infeasible
feasible
optimal
suboptimal
unknown
timeout
partial
cancelled
```

A solution that violates a hard constraint MUST NOT be reported as feasible.

---

# 5. Core Types

```text
ProblemId
ProblemRevision
DecisionProblem

DecisionVariable
VariableId
VariableDomain

Constraint
ConstraintId
ConstraintSet
ConstraintViolation

Objective
ObjectiveId
ObjectiveTerm
ObjectiveSet

DecisionModel
DecisionContext

DecisionAssignment
DecisionSolution
SolutionStatus

DecisionPlan
PlanId
PlanRevision

Planner
Solver
Optimizer
SearchEngine

SearchState
SearchNode
SearchFrontier
SearchPolicy

Schedule
ScheduleTask
Resource
ResourceCalendar
TimeWindow

Assignment
Matching
Route
RoutingProblem

SolveLimits
OptimizationBudget
WarmStart
SolutionCheckpoint

DecisionExplanation
DecisionSnapshot
InfeasibilityCertificate
```

---

# 6. DecisionProblem

```text
decision Problem {
    variable x: int in 0..100
    variable y: int in 0..100

    constraint x + y <= 100

    objective maximize x + 2*y
}
```

A problem consists of:

```text
Problem
├── variables
├── domains
├── constraints
├── objectives
├── parameters
├── assumptions
├── decision context
├── solver configuration
└── metadata
```

---

# 7. Variable Domains

Native domains:

```text
Bool
Int
UInt
Real
Enum
Set
Sequence
Interval
Graph
Path
Vector
Tensor
```

The implementation MUST support specialized compact representations.

Examples:

```text
x: Int[0..100]
color: Enum{red, green, blue}
machines: Set<Machine>
route: Path<CityGraph>
window: Interval
```

---

# 8. Constraint Model

## 8.1 Equality

```text
x == y
```

## 8.2 Inequality

```text
x <= y
x >= y
x != y
```

## 8.3 Bounds

```text
0 <= x <= 100
```

## 8.4 All-Different

```text
constraint all_different(tasks.machine)
```

## 8.5 Cardinality

```text
count(selected) <= 10
```

## 8.6 Implication

```text
A -> B
```

## 8.7 Logical

```text
A && B
A || B
!A
```

## 8.8 Precedence

```text
A.end <= B.start
```

## 8.9 Resource Capacity

```text
resource.cpu_usage <= resource.cpu_capacity
```

## 8.10 Assignment

```text
each job assigned exactly one machine
```

## 8.11 Temporal

```text
task.start >= release_time
task.end <= deadline
```

## 8.12 Spatial

```text
distance(A, B) <= maximum_distance
```

## 8.13 Custom Constraint

Custom constraints MUST execute through an explicit provider/capability boundary.

Arbitrary code execution MUST NOT be implicitly introduced into a solver.

---

# 9. Hard and Soft Constraints

Every constraint has:

```text
kind = Hard | Soft
priority
weight
penalty
```

Hard:

```text
@hard
constraint memory <= capacity
```

Soft:

```text
@soft(weight=10)
constraint prefer_same_region
```

Hard constraints define feasibility.

Soft constraints contribute to optimization.

---

# 10. Objective Model

Supported objective modes:

```text
Minimize
Maximize
Satisfy
WeightedSum
Lexicographic
Pareto
Hierarchical
```

Example:

```text
objective minimize:
    0.6 * latency
  + 0.3 * cost
  + 0.1 * energy
```

Lexicographic:

```text
objective lexicographic:
    minimize violations
    minimize latency
    minimize cost
```

The engine MUST preserve objective ordering exactly.

---

# 11. Multi-Objective Optimization

Axiom MUST support Pareto solutions.

```text
ParetoFrontier<Solution>
```

A solution dominates another if it is no worse in every objective and strictly better in at least one.

The runtime MUST NOT arbitrarily collapse a Pareto frontier into one "best" result without an explicit policy.

---

# 12. Solver Architecture

```text
SolverProvider
├── NativeConstraintSolver
├── NativeSearchSolver
├── NativeOptimizer
├── DynamicProgrammingSolver
├── BranchBoundSolver
├── ExternalSolverProvider
└── SpecializedDomainSolver
```

External providers may wrap:

- MILP
- CP-SAT
- SMT
- SAT
- nonlinear solvers
- evolutionary optimizers
- domain-specific solvers

No external solver is required for the Axiom language/runtime baseline.

---

# 13. Native Solver Set

Axiom baseline SHOULD provide:

```text
Enumeration
ConstraintPropagation
Backtracking
BranchAndBound
DynamicProgramming
GreedySearch
AStar
BestFirstSearch
BeamSearch
LocalSearch
```

Optional advanced native implementations:

```text
SimulatedAnnealing
TabuSearch
IteratedLocalSearch
```

---

# 14. Search Engine

Core search abstraction:

```text
SearchState
SearchNode
SearchAction
SearchTransition
SearchGoal
SearchHeuristic
SearchFrontier
```

Conceptually:

```text
state
  │
  ├── action A ──> state'
  ├── action B ──> state''
  └── action C ──> state'''
```

---

# 15. Search Algorithms

Native algorithms:

```text
DFS
BFS
UniformCost
BestFirst
AStar
BeamSearch
BranchAndBound
IDAStar
```

Each algorithm MUST expose:

```text
expanded_nodes
generated_nodes
pruned_nodes
frontier_size
elapsed_time
solution_depth
cost
```

---

# 16. Heuristics

```text
heuristic h(state) -> score
```

Metadata:

```text
admissible
consistent
deterministic
estimated_cost
```

The engine MUST NOT assume admissibility merely because a heuristic is registered.

---

# 17. Transposition Tables

Search engines SHOULD support:

```text
StateHash -> BestKnownCost
```

This avoids repeated exploration of equivalent states.

The state hash MUST be deterministic for deterministic execution.

---

# 18. Branch-and-Bound

Each branch maintains:

```text
lower_bound
upper_bound
incumbent
```

A branch can be pruned when:

```text
bound >= incumbent
```

for minimization, or the equivalent condition for maximization.

---

# 19. Constraint Propagation

Propagation SHOULD occur before expensive search.

Examples:

```text
domain reduction
bound propagation
arc consistency
all-different propagation
precedence propagation
capacity propagation
```

Pipeline:

```text
Model
 → Normalize
 → Propagate
 → Detect contradiction
 → Reduce domains
 → Search
```

---

# 20. Infeasibility

The solver MUST distinguish:

```text
proven infeasible
not yet proven
timeout
unknown
```

When supported, it may emit:

```text
InfeasibilityCertificate
```

containing:

```text
conflicting constraints
conflicting domains
unsatisfied assumptions
solver/provider evidence
```

---

# 21. DecisionSolution

```text
DecisionSolution {
    status
    assignments
    objective_values
    constraint_status
    runtime
    solver
    solver_version
    optimality
    optimality_gap
    proof_status
}
```

Possible statuses:

```text
Optimal
Feasible
Suboptimal
Partial
Infeasible
Unknown
Timeout
Cancelled
```

A timeout MUST NOT automatically become `Optimal`.

---

# 22. Optimality Metadata

```text
Optimality {
    proven: bool
    gap: optional<Real>
    bound: optional<Real>
    incumbent: optional<Real>
}
```

Examples:

```text
proven = true
gap = 0
```

or:

```text
proven = false
gap = 0.017
```

---

# 23. Scheduling Model

652 provides generic scheduling primitives.

```text
Schedule {
    tasks
    resources
    calendars
    dependencies
}
```

Task:

```text
ScheduleTask {
    id
    duration
    release_time
    deadline
    dependencies
    eligible_resources
    preemptible
    setup_time
}
```

---

# 24. Resource Model

```text
Resource {
    id
    capacity
    availability
    cost
    location
    attributes
}
```

Resources may represent:

```text
CPU
GPU
RAM
storage
network
worker
machine
vehicle
human role
service instance
cluster node
```

Existing 606 resource accounting remains authoritative for runtime resource consumption.

---

# 25. Resource Calendars

```text
ResourceCalendar {
    working_windows
    maintenance_windows
    blackout_windows
    capacity_changes
}
```

The scheduler MUST treat unavailable intervals as hard constraints unless explicitly modeled otherwise.

---

# 26. Preemption

Tasks may declare:

```text
preemptible = true
```

The scheduler MUST NOT preempt a non-preemptible task.

---

# 27. Critical Path

For DAG scheduling:

```text
critical_path()
earliest_start()
latest_start()
slack()
```

These are deterministic analytical operations and need not invoke a general optimizer.

---

# 28. Assignment

Axiom provides:

```text
AssignmentProblem
```

Example:

```text
assign jobs -> machines
```

Constraints:

```text
each_job_exactly_one
machine_capacity
machine_eligibility
```

Objectives:

```text
minimize_cost
minimize_latency
maximize_utilization
```

---

# 29. Matching

Native primitives:

```text
BipartiteMatching
MaximumMatching
MinimumCostMatching
StableMatchingProvider
```

Stable matching is a provider boundary because different applications may require different stability definitions.

---

# 30. Routing

```text
RoutingProblem {
    graph
    source
    destination
    constraints
    objective
}
```

Supports:

```text
shortest_path
least_cost_path
time_constrained_route
capacity_constrained_route
multi_stop_route
```

Graph data may originate from 645.

---

# 31. Min-Cost Flow

A native flow abstraction SHOULD support:

```text
nodes
edges
capacity
cost
supply
demand
```

Useful for:

- assignment
- transportation
- scheduling
- network allocation
- workload distribution.

---

# 32. Planning

Planning differs from optimization by explicitly modeling state transitions.

```text
PlanningState
ActionSchema
Precondition
Effect
Goal
Plan
```

Example:

```text
action move(robot, A, B)

precondition:
    robot_at(robot, A)

effect:
    robot_at(robot, B)
```

---

# 33. Plan Validation

Every generated plan SHOULD be independently validated.

```text
validate(plan, initial_state, goal)
```

Validation checks:

```text
preconditions
effects
resource usage
temporal constraints
goal satisfaction
policy constraints
```

---

# 34. Hierarchical Planning Boundary

652 MAY expose a provider interface for:

```text
HTN planning
temporal planning
partial-order planning
```

but these MUST NOT become mandatory compiler/runtime dependencies.

---

# 35. Scenario-Based Decisions

A problem may contain multiple scenarios:

```text
ScenarioSet {
    scenario_1
    scenario_2
    scenario_3
}
```

Each scenario can provide different parameters.

Example:

```text
fuel_price
demand
network_latency
machine_failure
```

---

# 36. Robust Optimization

Robust optimization may optimize against uncertainty sets rather than one expected value.

```text
robust objective
```

Example:

```text
minimize worst_case_latency
```

---

# 37. Stochastic Optimization

652 may expose:

```text
ScenarioSampling
MonteCarloEvaluation
ExpectedObjective
RiskAdjustedObjective
```

Randomness MUST be explicit and seedable.

---

# 38. Chance Constraints

Provider boundary:

```text
Pr(constraint) >= 0.99
```

The runtime MUST preserve the distinction between:

```text
exact probability
estimated probability
simulation estimate
model assumption
```

---

# 39. Decision Under Uncertainty

Decision context may include:

```text
known_parameters
estimated_parameters
uncertain_parameters
scenario_distribution
confidence_metadata
```

The engine MUST NOT silently convert uncertain inputs into guaranteed facts.

---

# 40. Personalization Integration

651 preferences may become decision objectives or constraints.

Example:

```text
preference:
    prefer_low_latency

decision:
    minimize latency
```

But personalization MUST NOT override hard security or governance constraints.

Ordering:

```text
Security
  ↓
Policy
  ↓
Governance
  ↓
Feasibility
  ↓
Personalization
  ↓
Optimization
```

---

# 41. Policy Integration

639 may provide:

```text
allowed
denied
conditional
```

A denied action MUST NOT be selected merely because it optimizes an objective.

---

# 42. Resource Integration

606 provides runtime resource budgets.

652 consumes:

```text
cpu_budget
memory_budget
gpu_budget
time_budget
```

A solver MUST operate inside its declared budget.

---

# 43. Agent Integration

644 agents may invoke:

```text
planner.solve()
optimizer.solve()
scheduler.solve()
router.solve()
assignment.solve()
```

Agents receive structured solutions rather than hidden solver reasoning.

---

# 44. Explanation

652 MUST provide structured decision explanations.

```text
DecisionExplanation {
    selected_assignments
    objective_values
    active_constraints
    binding_constraints
    rejected_candidates
    solver_statistics
    optimality_status
    assumptions
}
```

The explanation is a structured audit artifact.

It MUST NOT claim to expose hidden chain-of-thought.

---

# 45. Binding Constraints

A binding constraint is one whose relaxation could affect the current solution.

Example:

```text
memory <= 64GB
```

with:

```text
memory_used = 64GB
```

may be marked:

```text
binding = true
```

---

# 46. Warm Starts

```text
WarmStart {
    assignments
    objective
    source_solution
    source_revision
}
```

Warm starts can dramatically reduce repeated solve cost.

They MUST be validated against the new problem revision.

---

# 47. Incremental Solving

Problems may be modified:

```text
ProblemRevision 1
        ↓
ProblemRevision 2
        ↓
ProblemRevision 3
```

The engine SHOULD reuse:

```text
domains
propagation state
learned constraints
search information
warm starts
previous solutions
```

when valid.

---

# 48. Checkpointing

Long-running solves support:

```text
SolutionCheckpoint
```

containing:

```text
problem_revision
solver
solver_version
search_state
incumbent
bounds
random_seed
statistics
```

A checkpoint MUST NOT be resumed against an incompatible problem revision.

---

# 49. Deterministic Mode

Deterministic mode requires:

```text
stable variable ordering
stable constraint ordering
stable seed
stable tie-breaking
stable serialization
```

Parallel execution may be restricted when strict reproducibility is requested.

---

# 50. Parallel Search

Search may use:

```text
worker pools
parallel branches
distributed search providers
```

Results MUST preserve correctness regardless of completion order.

---

# 51. Distributed Optimization

Large problems may be delegated to 630/635 infrastructure.

Architecture:

```text
652 Problem
   ↓
Partition
   ↓
Distributed Solver
   ↓
Partial Solutions
   ↓
Global Reduction
   ↓
Final Solution
```

Distributed execution MUST preserve solver semantics.

---

# 52. Solver Budget

```text
SolveLimits {
    max_time
    max_memory
    max_cpu
    max_nodes
    max_iterations
    max_objective_evaluations
    max_solutions
    max_workers
}
```

The runtime MUST stop or degrade gracefully when a budget is exhausted.

---

# 53. Cancellation

Every solve MUST support cancellation.

```text
cancel(token)
```

Cancellation should preserve the best known valid solution where available.

---

# 54. Partial Solutions

If execution stops before optimality is proven:

```text
status = Partial
```

if a valid feasible solution exists.

The result MUST include:

```text
best_known_solution
best_known_bound
gap
termination_reason
```

---

# 55. Solver Selection

Axiom may choose a solver automatically.

Selection considers:

```text
problem type
variable domains
constraint structure
objective structure
size
deadline
available providers
resource budget
determinism requirement
```

Automatic selection MUST remain observable.

---

# 56. Solver Registry

```text
SolverRegistry {
    register(provider)
    unregister(id)
    find(capabilities)
    inspect(id)
}
```

Provider metadata:

```text
supported_domains
supported_constraints
supported_objectives
exactness
parallelism
determinism
external_dependencies
```

---

# 57. Provider Boundary

External solver providers MUST expose:

```text
compile_problem()
solve()
cancel()
checkpoint()
restore()
explain()
validate()
```

The provider MUST NOT gain unrestricted runtime authority.

---

# 58. Security

Decision models are potentially untrusted inputs.

The runtime MUST prevent:

- arbitrary native code execution
- uncontrolled filesystem access
- unrestricted network access
- unauthorized resource consumption
- privilege escalation through custom constraints

Custom execution requires explicit capabilities.

---

# 59. Governance

All decision inputs inherit governance metadata from 640.

Examples:

```text
data classification
retention
residency
privacy
lineage
allowed transformation
```

A solver MUST NOT silently discard governance metadata.

---

# 60. Audit

A decision snapshot SHOULD contain:

```text
problem_revision
input_snapshot
constraints
objectives
solver
solver_version
configuration
seed
resource_budget
solution
optimality_status
timestamp
```

This supports reproducibility and forensic analysis.

---

# 61. Compiler Annotations

Axiom introduces:

```text
@decision
@variable
@domain
@constraint
@objective
@optimize
@plan
@schedule
@resource
@assignment
@route
@search
@heuristic
@solver
@hard
@soft
@priority
@lexicographic
@pareto
@stochastic
@robust
@checkpoint
@warm_start
```

Example:

```text
@decision
problem AllocateGPU {
    @variable gpu: GPU
    @variable worker: Worker

    @constraint @hard
        worker.memory <= gpu.memory

    @objective @minimize
        latency(worker, gpu)
}
```

---

# 62. Runtime API

Conceptual API:

```text
decision.create(problem)
decision.validate(problem)
decision.solve(problem)
decision.cancel(handle)
decision.checkpoint(handle)
decision.restore(checkpoint)
decision.explain(solution)
decision.compare(solution_a, solution_b)
decision.benchmark(problem)
```

---

# 63. Specialized APIs

```text
planner.solve()
optimizer.solve()
scheduler.solve()
assignment.solve()
matching.solve()
router.solve()
search.solve()
```

All return the common `DecisionSolution` family.

---

# 64. Native DSL

Axiom may provide a compact decision DSL:

```text
decision schedule_jobs {
    variable start[job] : time
    variable machine[job] : Machine

    constraint precedence(job_a, job_b)
    constraint capacity(machine)

    objective minimize makespan
}
```

The DSL compiles into the common decision IR.

---

# 65. Decision IR

Compiler intermediate representation:

```text
DecisionIR
├── Variables
├── Domains
├── Constraints
├── Objectives
├── StateTransitions
├── Resources
├── SearchHints
├── SolverHints
└── Metadata
```

The IR MUST be deterministic and serializable.

---

# 66. Optimization Normalization

The compiler SHOULD normalize:

```text
x <= y
```

into a canonical constraint representation.

Likewise:

```text
maximize f(x)
```

may normalize into:

```text
minimize -f(x)
```

internally while retaining original semantic metadata.

---

# 67. Constant Folding

Decision expressions SHOULD support compile-time simplification.

Example:

```text
constraint x + 0 <= 100
```

becomes:

```text
constraint x <= 100
```

---

# 68. Domain Reduction

Static domain reduction should occur before runtime.

Example:

```text
x: 0..100
constraint x >= 40
constraint x <= 70
```

becomes:

```text
x: 40..70
```

---

# 69. Memory Representation

Small integer domains SHOULD use compact bitsets.

Enumerated domains SHOULD use:

```text
dense IDs
bitsets
compressed sparse sets
```

depending on cardinality.

---

# 70. Zero-Copy Integration

Decision inputs SHOULD support views into existing Axiom data structures.

Example:

```text
@borrowed
dataset.features
```

No mandatory heap duplication.

This does not introduce a language-level borrow checker; it is a runtime/compiler optimization boundary.

---

# 71. SIMD / Vectorization

Constraint and objective evaluation SHOULD support:

```text
SIMD
vectorized arithmetic
batch evaluation
```

where mathematically safe.

---

# 72. GPU Evaluation

Large independent objective evaluations MAY execute on GPU through 614/643 infrastructure.

Examples:

```text
population scoring
Monte Carlo
large vector objectives
simulation batches
```

The decision semantics remain defined by 652.

---

# 73. Simulation Integration

648 may evaluate candidate decisions:

```text
candidate plan
   ↓
simulation
   ↓
metrics
   ↓
objective evaluation
   ↓
decision engine
```

Simulation results MUST be marked as simulated/estimated.

---

# 74. Machine Learning Integration

643 predictions may enter:

```text
objective terms
constraint parameters
heuristics
candidate scoring
scenario generation
```

Example:

```text
predicted_cost(job, machine)
```

The prediction remains a model output, not a fact.

---

# 75. Knowledge Graph Integration

645 can provide:

```text
relationships
topology
dependencies
eligibility
graph paths
resource relationships
```

652 consumes these as decision inputs.

---

# 76. Search Integration

641 may provide candidate retrieval.

Pipeline:

```text
retrieve candidates
       ↓
filter constraints
       ↓
optimize/rank
       ↓
decision
```

---

# 77. Recommendation Integration

651 can formulate preference-weighted objectives.

Example:

```text
prefer:
    low_latency
    nearby_resource
    low_cost
```

652 solves the resulting decision problem subject to higher-priority constraints.

---

# 78. Workflow Integration

629 may invoke 652 for:

```text
task ordering
worker assignment
resource allocation
retry strategy
deadline planning
```

652 returns the plan.

629 remains responsible for durable execution.

---

# 79. Cluster Integration

635 may consume:

```text
placement recommendations
capacity allocation
leader placement alternatives
```

but consensus remains outside 652.

---

# 80. Deployment Integration

636 may use 652 for:

```text
rollout sequencing
instance allocation
canary selection
capacity planning
```

Deployment policy remains owned by 636/639.

---

# 81. API Gateway Integration

632 may use 652 for:

```text
traffic allocation
backend selection
capacity-aware routing
```

---

# 82. Service Runtime Integration

631 may use optimization for:

```text
load distribution
routing
capacity allocation
placement
```

---

# 83. Multi-Objective Tradeoffs

Axiom MUST preserve objective values independently.

Example:

```text
latency = 30ms
cost = $0.20
energy = 4.2J
```

The runtime MUST NOT expose only a single opaque score when component objectives are available.

---

# 84. Penalty Functions

Soft constraints may produce:

```text
penalty(constraint)
```

Penalty semantics MUST be explicit.

The solver MUST distinguish:

```text
actual objective
penalty objective
combined objective
```

---

# 85. Priority Levels

Constraints/objectives may define:

```text
priority = 0..N
```

Higher-priority constraints MUST dominate lower-priority preferences when configured as hierarchical optimization.

---

# 86. Solution Comparison

API:

```text
compare(a, b)
```

returns structured relations:

```text
dominates
dominated_by
equivalent
incomparable
```

This is preferable to an arbitrary numeric ranking for Pareto solutions.

---

# 87. Plan Execution Boundary

652 generates plans.

Execution belongs to:

```text
629
607
605
631
636
```

depending on context.

This prevents the solver from becoming an uncontrolled execution engine.

---

# 88. Plan Safety

Before execution:

```text
validate
policy-check
resource-check
governance-check
```

must succeed according to the consuming subsystem's contract.

---

# 89. State Freshness

A solution MUST record the revision of input state.

Example:

```text
solution.state_revision = 182
```

Consumers MUST detect stale plans when required.

---

# 90. Replanning

Runtime SHOULD support:

```text
replan(problem_delta)
```

without reconstructing the entire problem.

Useful for:

```text
machine failure
new request
resource loss
deadline change
network change
```

---

# 91. Receding-Horizon Planning

Provider:

```text
solve horizon H
execute first action/window
observe new state
replan
```

This supports MPC-style systems without requiring MPC as part of the language core.

---

# 92. Decision Cache

Cache key SHOULD include:

```text
problem_hash
problem_revision
solver
solver_version
configuration_hash
```

For personalized decisions, include 651 profile/context revision.

---

# 93. Cache Correctness

A cached solution MUST NOT be reused when:

```text
problem semantics changed
hard constraints changed
policy changed
required state revision changed
solver semantics changed
```

unless explicitly marked safe.

---

# 94. Serialization

Decision artifacts:

```text
.axdecision
.axconstraint
.axobjective
.axplan
.axschedule
.axsolver
.axsolution
```

must be machine-readable.

Recommended representation:

```text
binary canonical form
+
optional human-readable JSON/text projection
```

---

# 95. AI-Readable Metadata

Artifacts SHOULD include:

```text
problem_summary
variables
domains
constraints
objectives
solver
assumptions
solution_status
optimality
```

This allows AI agents to consume decisions without parsing opaque binary structures.

---

# 96. CLI

Recommended commands:

```text
axiom decision validate
axiom decision solve
axiom decision explain
axiom decision benchmark
axiom decision compare
axiom decision checkpoint
axiom decision restore

axiom plan solve
axiom plan validate

axiom schedule solve
axiom route solve
axiom assignment solve

axiom solver list
axiom solver inspect
```

---

# 97. Benchmarking

Benchmark results:

```text
problem_size
variables
constraints
objective_count
solver
runtime
memory
nodes
iterations
solutions
optimality
gap
```

Benchmark results MUST preserve the exact configuration.

---

# 98. Solver Diagnostics

Diagnostics SHOULD expose:

```text
propagation_ratio
pruning_ratio
branching_factor
cache_hit_ratio
nodes_per_second
objective_evaluations
constraint_evaluations
memory_peak
```

---

# 99. Failure Model

Expected failures:

```text
InvalidModel
InvalidDomain
UnsupportedConstraint
UnsupportedObjective
Infeasible
Timeout
MemoryLimit
Cancelled
ProviderUnavailable
CheckpointMismatch
InvalidWarmStart
StateStale
PolicyDenied
GovernanceDenied
```

---

# 100. Error Semantics

Errors MUST be structured.

Example:

```text
DecisionError {
    code
    message
    problem_id
    revision
    constraint_id?
    variable_id?
    provider?
    recoverable
}
```

---

# 101. Observability

Integrates with 602/633:

```text
decision.solve.started
decision.solve.completed
decision.solve.timeout
decision.solve.cancelled
decision.solve.infeasible
decision.solve.provider_error
```

Metrics:

```text
solve_latency
solve_memory
nodes
optimality_gap
timeout_rate
cache_hit_rate
```

---

# 102. Security Telemetry

Security-relevant decision events SHOULD record:

```text
policy revision
authorization context
decision actor
provider identity
execution boundary
```

without leaking protected data unnecessarily.

---

# 103. Privacy

Decision models may process sensitive data.

652 MUST support:

```text
data classification
field redaction
minimal snapshots
retention policy
access-controlled explanations
```

from 640/603.

---

# 104. Reproducibility

A reproducible decision requires:

```text
problem revision
input snapshot
solver version
configuration
seed
provider version
```

If any required component is unavailable, reproducibility status MUST be marked accordingly.

---

# 105. Numerical Semantics

Axiom MUST define numerical behavior for:

```text
NaN
Infinity
overflow
underflow
epsilon
tolerance
floating-point comparison
```

Constraint comparisons SHOULD allow explicit tolerances where appropriate.

---

# 106. Exact Arithmetic

For selected problems, the engine SHOULD support:

```text
integer exact arithmetic
rational arithmetic
decimal arithmetic
```

to avoid numerical ambiguity.

---

# 107. Floating-Point Tolerance

Example:

```text
constraint abs(x - y) <= 1e-9
```

Tolerance MUST be explicit rather than globally implicit.

---

# 108. Integer Optimization

Integer variables MUST preserve exact integer semantics.

No silent conversion to floating point.

---

# 109. Solver Correctness Contract

Every solver declares:

```text
exact
heuristic
approximate
stochastic
simulation_based
```

The runtime MUST propagate this metadata to the result.

---

# 110. Heuristic Result Semantics

A heuristic solver returning the current best solution MUST report:

```text
status = Feasible | Suboptimal | Partial
```

unless optimality is independently proven.

---

# 111. Approximate Solver Semantics

Approximate solvers may provide:

```text
estimated_quality
error_bound
confidence
```

when mathematically justified.

These fields MUST NOT be fabricated.

---

# 112. Randomized Solvers

Randomized algorithms MUST expose:

```text
seed
random_source
iterations
```

for reproducibility.

---

# 113. Search Limits

Search can stop because:

```text
time
memory
nodes
depth
iterations
objective evaluations
```

Each termination reason MUST be explicit.

---

# 114. Memory Safety

The decision runtime MUST use Axiom's native memory model.

It MUST NOT require:

```text
garbage collection
hidden tracing
mandatory reference counting
```

for correctness.

Temporary solver allocations should use:

```text
arena
region
stack
pool
explicit ownership
```

as appropriate.

---

# 115. Allocation Strategy

Recommended:

```text
Problem arena
Search arena
Solution arena
Checkpoint arena
```

Bulk deallocation should be O(1) where possible.

---

# 116. Zero-Copy Domains

Large domains SHOULD support immutable views instead of copies.

---

# 117. Threading

Solver parallelism uses 607/608.

No solver may invent a separate threading runtime.

---

# 118. GPU

GPU execution uses 614/643.

No solver may directly bypass Axiom's device abstraction.

---

# 119. Distributed Execution

Distributed solvers use 630/635.

652 defines semantics; infrastructure handles transport/execution.

---

# 120. AI Agent Tool Contract

Agent tool schema:

```text
decision.solve {
    problem
    limits
    objective_mode
    solver?
}
```

Result:

```text
{
    status,
    solution,
    objectives,
    constraints,
    optimality,
    explanation,
    provenance
}
```

---

# 121. Agent Safety

An agent may request a decision.

It cannot use 652 to bypass:

```text
639 authorization
603 capabilities
640 governance
```

---

# 122. Decision Provenance

Every production decision SHOULD identify:

```text
input source
problem revision
solver
solver version
objective revision
constraint revision
policy revision
model revision
```

---

# 123. Experiment Integration

646 may compare:

```text
solver A
solver B
heuristic A
heuristic B
```

using controlled benchmark datasets.

---

# 124. Simulation Evaluation

648 can test candidate policies across many scenarios.

652 receives:

```text
simulation score
risk
constraint failures
resource usage
```

---

# 125. Personalization Evaluation

651 can evaluate whether a decision respects:

```text
user preference
agent preference
context preference
```

without overriding hard constraints.

---

# 126. Model-Driven Optimization

643 predictions can become objective coefficients:

```text
cost(machine) = predicted_cost(machine)
```

The coefficient MUST carry model provenance.

---

# 127. Data Freshness

Decision inputs MUST expose:

```text
observed_at
available_at
expires_at
revision
```

to prevent stale-state decisions.

---

# 128. Temporal Validity

A solution with expired input data MAY be rejected before execution.

---

# 129. Constraint Versioning

Constraints are versioned independently.

```text
ConstraintRevision
```

Changing a constraint invalidates dependent cached solutions where necessary.

---

# 130. Objective Versioning

Likewise:

```text
ObjectiveRevision
```

must be tracked.

---

# 131. Model Fingerprint

Canonical decision model:

```text
model_hash = hash(
    variables +
    domains +
    constraints +
    objectives +
    semantics
)
```

This supports caching and reproducibility.

---

# 132. Search Fingerprint

Search configuration:

```text
algorithm
heuristic
seed
limits
provider
```

should also be fingerprinted.

---

# 133. Decision Snapshot

```text
DecisionSnapshot {
    problem
    context
    constraints
    objectives
    solution
    provenance
}
```

Snapshots are immutable.

---

# 134. Snapshot Storage

Uses 611/612/613 for:

```text
serialization
durability
compression
content addressing
```

---

# 135. Content Addressing

Large immutable decision artifacts SHOULD use content hashes.

---

# 136. Plan Diff

Plans support:

```text
plan.diff(a, b)
```

Output:

```text
added_actions
removed_actions
changed_actions
changed_assignments
objective_delta
constraint_delta
```

---

# 137. Schedule Diff

Schedules expose:

```text
task moved
resource changed
duration changed
dependency changed
```

---

# 138. Decision Comparison

Two solutions can be compared on:

```text
feasibility
objective vectors
resource usage
risk
latency
cost
```

No universal ranking is implied.

---

# 139. Pareto Archive

Runtime SHOULD support bounded Pareto archives.

```text
ParetoArchive {
    add(solution)
    remove_dominated()
    query()
}
```

---

# 140. Diversity Preservation

Optimization MAY preserve solution diversity.

Useful for:

```text
planning alternatives
routing alternatives
deployment alternatives
agent alternatives
```

---

# 141. Alternative Plans

Planner SHOULD be able to return:

```text
top_k_feasible
top_k_diverse
pareto_frontier
```

rather than one solution only.

---

# 142. Decision Policy

A decision policy describes how results are selected from alternatives.

```text
DecisionPolicy {
    feasibility_rule
    objective_rule
    tie_breaker
    risk_rule
}
```

The policy must be explicit.

---

# 143. Tie Breaking

Tie-breaking must be deterministic when deterministic mode is enabled.

Example:

```text
lowest_id
earliest_time
lexicographic
stable_hash
```

---

# 144. Scheduling Objectives

Common objectives:

```text
minimize_makespan
minimize_tardiness
minimize_idle_time
maximize_utilization
minimize_energy
minimize_cost
maximize_throughput
```

---

# 145. Scheduling Constraints

Common constraints:

```text
precedence
capacity
release_time
deadline
machine_eligibility
maintenance
setup
changeover
calendar
non_overlap
```

---

# 146. Packing

Generic packing primitives:

```text
bin
item
capacity
dimensions
compatibility
```

Useful for:

```text
memory allocation
container packing
storage
GPU placement
deployment
```

---

# 147. Knapsack

Native solver SHOULD recognize:

```text
0/1 knapsack
bounded knapsack
unbounded knapsack
multi-dimensional knapsack
```

and select optimized algorithms.

---

# 148. SAT-Like Constraints

Boolean decision problems may compile to compact bit-level representations.

---

# 149. Constraint Learning Boundary

A provider may expose:

```text
learned_clause
nogood
conflict
```

but the common API need only preserve semantically valid learned constraints.

---

# 150. Solver Portfolio

The runtime MAY run several solvers:

```text
solver A
solver B
solver C
```

and return according to an explicit portfolio policy.

---

# 151. Portfolio Determinism

A deterministic portfolio requires deterministic:

```text
solver order
timeouts
tie-breaking
aggregation
```

---

# 152. Early Termination

Search may stop once:

```text
objective <= target
```

or:

```text
gap <= tolerance
```

The termination reason MUST be recorded.

---

# 153. Quality Targets

Users may specify:

```text
target_objective
maximum_gap
minimum_quality
```

The engine may terminate once the target is proven satisfied.

---

# 154. SLA-Aware Solving

Applications may specify:

```text
deadline
```

The solver should return the best valid solution available before the deadline.

---

# 155. Anytime Algorithms

Supported algorithms may improve a solution continuously:

```text
solution_1
solution_2
solution_3
...
```

with monotonically improving objective where the algorithm guarantees it.

---

# 156. Streaming Solutions

Long solves MAY emit:

```text
on_solution(solution)
on_bound_update(bound)
on_progress(stats)
```

---

# 157. Backpressure

Streaming callbacks integrate with 608/607 backpressure semantics.

---

# 158. Cancellation Safety

Cancellation MUST leave the solver state valid.

No partially written checkpoint may be treated as valid.

---

# 159. Crash Recovery

Long-running solvers may recover from checkpoint via 600/611.

---

# 160. Failure Recovery

If provider failure occurs:

```text
retry
fallback solver
resume checkpoint
return partial solution
```

according to explicit policy.

---

# 161. Fallback

Fallback solver selection MUST preserve semantic correctness.

It MUST NOT silently relax hard constraints.

---

# 162. Constraint Relaxation

If the application explicitly permits relaxation:

```text
relaxation_policy
```

the engine may identify which soft/hard constraints could be relaxed.

Hard constraint relaxation MUST be explicit and auditable.

---

# 163. Minimal Relaxation

For infeasible problems, the engine MAY search for:

```text
minimum relaxation
```

or:

```text
minimum violation set
```

---

# 164. Unsat Explanation

Where supported:

```text
conflict_set
minimal_conflict_set
```

may identify conflicting constraints.

These are evidence artifacts, not hidden reasoning.

---

# 165. Human Review

High-impact decisions MAY require:

```text
review_required = true
```

before execution.

---

# 166. Approval Boundary

Approval remains outside the solver.

Possible integration:

```text
652 solution
    ↓
639 policy
    ↓
human approval
    ↓
629/636 execution
```

---

# 167. Dry Run

All major decision APIs SHOULD support:

```text
dry_run = true
```

to produce plans without executing them.

---

# 168. Explainable Plan

Example:

```text
plan:
    task A -> machine 2
    task B -> machine 1

reason:
    machine 2 satisfies memory constraint
    machine 1 minimizes remaining latency
```

This is structured justification based on recorded facts, not generated hidden reasoning.

---

# 169. AI-Friendly Syntax

Axiom permits:

```text
decision allocate {
    goal maximize throughput

    constraints {
        cpu <= capacity
        memory <= capacity
    }

    optimize {
        throughput
        cost
    }
}
```

---

# 170. Compiler Diagnostics

Example:

```text
error AX652001:
constraint references unknown variable 'gpu_mem'
```

or:

```text
warning AX652017:
objective contains stochastic value without declared seed
```

---

# 171. Static Analysis

Compiler SHOULD detect:

```text
unused variables
duplicate constraints
contradictory constant constraints
unbounded objectives
unsupported domains
objective/constraint type errors
```

---

# 172. Contradiction Detection

Example:

```text
x >= 10
x <= 5
```

should be diagnosed statically when possible.

---

# 173. Unbounded Optimization

If:

```text
maximize x
```

and `x` has no upper bound, the compiler/runtime SHOULD report:

```text
UnboundedObjective
```

when it can prove this.

---

# 174. Type System Integration

Decision expressions use normal Axiom typing.

Example:

```text
duration + duration -> duration
cost + cost -> cost
```

Invalid dimensional operations should fail compilation.

---

# 175. Units

Decision variables may use units:

```text
time
bytes
joules
meters
currency
```

Unit-safe constraints reduce modeling errors.

---

# 176. Domain-Specific Types

Examples:

```text
Duration
Capacity
Probability
Cost
Distance
Timestamp
ResourceId
MachineId
```

---

# 177. Probability Semantics

`Probability` MUST represent values in:

```text
[0,1]
```

unless explicitly using another statistical representation.

---

# 178. Cost Semantics

Costs SHOULD carry currency/unit metadata when applicable.

---

# 179. Temporal Semantics

Time expressions must identify:

```text
absolute time
duration
interval
deadline
period
```

---

# 180. Graph Semantics

Routing variables should preserve graph identity and revision.

---

# 181. Solver Capability Negotiation

Before execution:

```text
provider.supports(model)
```

returns capability information.

Unsupported features MUST fail clearly or trigger explicit fallback.

---

# 182. Compilation Pipeline

```text
Axiom Source
    ↓
Parser
    ↓
Semantic Analysis
    ↓
Decision IR
    ↓
Normalization
    ↓
Static Simplification
    ↓
Solver Lowering
    ↓
Native / Provider Backend
    ↓
Decision Runtime
```

---

# 183. Native Backend

The native backend targets:

```text
x86-64
ARM64
WASM
```

through existing Axiom compiler infrastructure.

---

# 184. No Mandatory Third-Party Solver

The Axiom SDK MUST remain usable with:

```text
no external optimizer
no external SAT solver
no external SMT solver
```

for baseline supported problem classes.

---

# 185. External Solver Adapters

Optional adapters may be distributed separately.

They MUST NOT contaminate core ABI requirements.

---

# 186. ABI Stability

Provider ABI SHOULD use a stable C-compatible/native Axiom boundary.

---

# 187. Version Compatibility

A solver provider declares:

```text
api_version
model_ir_version
capability_version
```

---

# 188. Provider Isolation

External providers SHOULD run under explicit isolation where required.

---

# 189. Runtime Profiles

Define:

```text
AXDECISION_NONE
AXDECISION_CORE
AXDECISION_CONSTRAINT
AXDECISION_SEARCH
AXDECISION_OPTIMIZE
AXDECISION_SCHEDULE
AXDECISION_ASSIGN
AXDECISION_ROUTE
AXDECISION_PLAN
AXDECISION_STOCHASTIC
AXDECISION_DISTRIBUTED
AXDECISION_AGENT
AXDECISION_SIMULATION
AXDECISION_FULL
```

---

# 190. Profile Semantics

`AXDECISION_CORE`:

```text
problem
variable
domain
constraint
objective
solution
```

`AXDECISION_SEARCH` adds search.

`AXDECISION_SCHEDULE` adds scheduling.

`AXDECISION_PLAN` adds state/action planning.

`AXDECISION_FULL` enables the complete feature surface.

---

# 191. Build-Time Stripping

Unused decision features MUST be removable.

A simple application using only:

```text
minimize(x)
```

must not link the entire solver ecosystem.

---

# 192. Dead-Code Elimination

Solver algorithms not referenced by the selected profile SHOULD be eliminated.

---

# 193. Embedded Targets

Minimal profiles should be viable on:

```text
embedded
mobile
WASM
desktop
server
```

subject to available resources.

---

# 194. WASM

WASM decision runtime MUST support deterministic execution.

External native solver providers are optional.

---

# 195. Mobile

Mobile applications may use:

```text
small native solver
incremental solving
bounded search
```

without requiring a server.

---

# 196. Server

Server deployments may use:

```text
distributed solver
provider portfolio
GPU evaluation
large memory
checkpointing
```

---

# 197. Edge

Edge deployments should favor:

```text
compact model
deterministic search
bounded memory
short deadlines
```

---

# 198. Observability Integration

All solves emit standard 602/633 telemetry.

---

# 199. Trace Context

Distributed solving propagates trace context.

---

# 200. Metrics Cardinality

Problem IDs, user IDs and model IDs MUST NOT automatically become unrestricted metric labels.

---

# 201. Logging

Logs SHOULD include:

```text
problem_id
revision
solver
status
duration
gap
```

Sensitive decision data remains governed.

---

# 202. Benchmark Corpus

Axiom SHOULD maintain canonical test classes:

```text
SAT
graph search
knapsack
assignment
scheduling
routing
packing
planning
multi-objective
stochastic
```

---

# 203. Correctness Tests

Every solver requires:

```text
known optimum
known infeasible
known unbounded
timeout
cancellation
determinism
serialization
checkpoint
```

tests.

---

# 204. Differential Testing

Multiple solver implementations may solve the same model.

Results can be compared for semantic consistency.

---

# 205. Fuzzing

Decision parser and model compiler SHOULD support fuzzing.

---

# 206. Property Testing

Examples:

```text
all returned solutions satisfy hard constraints
```

and:

```text
proven optimal solution cannot be improved
```

---

# 207. Metamorphic Testing

Transformations such as:

```text
variable renaming
constraint reordering
objective term reordering
```

must preserve semantics where mathematically equivalent.

---

# 208. Numerical Testing

Test:

```text
large values
small values
near-boundary values
NaN
Infinity
overflow
tolerance
```

---

# 209. Performance Tests

Measure:

```text
compile time
solve time
memory
nodes/sec
constraint evaluations/sec
parallel scaling
```

---

# 210. Regression Database

Solved models SHOULD be stored as content-addressed regression fixtures.

---

# 211. AI Agent Benchmark

644 integration tests should measure:

```text
plan validity
constraint compliance
decision latency
replanning success
tool-call correctness
```

---

# 212. Simulation Benchmark

648 integration should test decisions across generated environments.

---

# 213. Personalization Benchmark

651 integration should test:

```text
preference application
hard-constraint preservation
context adaptation
```

---

# 214. Security Benchmark

Test:

```text
malicious model
resource exhaustion
provider isolation
capability escalation
invalid custom constraints
```

---

# 215. Governance Benchmark

Verify that:

```text
restricted data
residency constraints
retention rules
privacy labels
```

survive model transformations.

---

# 216. Serialization Compatibility

Older `.axdecision` artifacts SHOULD be readable where schema compatibility permits.

---

# 217. Schema Evolution

Unknown optional fields must be safely ignored.

Unknown mandatory semantic versions must fail clearly.

---

# 218. Backward Compatibility

Axiom MUST preserve semantic compatibility for:

```text
DecisionIR
provider ABI
artifact metadata
```

within a major version.

---

# 219. Forward Compatibility

Consumers should preserve unknown metadata where possible.

---

# 220. Resource Quotas

602/606 quotas apply to solver execution.

---

# 221. Multi-Tenant Isolation

Distributed decision services MUST isolate:

```text
memory
CPU
GPU
filesystem
network
provider credentials
```

---

# 222. Tenant Fairness

Cluster-level scheduling remains under 635/606.

652 only produces decision requests and optimization workloads.

---

# 223. Priority

Solve requests may specify:

```text
priority
deadline
budget
```

Actual execution scheduling remains under 607/606/635.

---

# 224. Admission Control

639/606 may reject a solve before execution.

---

# 225. Rate Limiting

Repeated solve requests may be rate-limited.

---

# 226. Decision Reuse

Equivalent decision problems SHOULD reuse previous solutions when safe.

---

# 227. Similarity Reuse

Approximate reuse may be offered separately and MUST be marked approximate.

---

# 228. Learning Search Heuristics

643/651 may provide learned heuristics.

Learned heuristics MUST NOT alter hard constraint semantics.

---

# 229. Learned Solver Policy

A learned solver selector may choose among algorithms.

Its decision MUST remain observable.

---

# 230. Meta-Optimization

652 MAY optimize solver configuration:

```text
heuristic
branch ordering
parameters
```

through bounded search.

---

# 231. Auto-Tuning

Auto-tuning MUST respect the user-specified solve budget.

---

# 232. Explainability of Auto-Tuning

Record:

```text
selected solver
selected configuration
selection evidence
benchmark context
```

---

# 233. Safety-Critical Mode

Applications may request:

```text
safety_mode = strict
```

which may require:

```text
exact solver
proven feasibility
explicit validation
deterministic execution
```

according to application policy.

---

# 234. High-Assurance Mode

Provider MAY support formal certificates.

```text
SolutionCertificate
```

Examples:

```text
proof of optimality
proof of infeasibility
proof of constraint satisfaction
```

---

# 235. Certificate Verification

Certificates SHOULD be independently verifiable.

---

# 236. Decision Contract

A decision contract contains:

```text
inputs
constraints
objectives
acceptable statuses
required proof level
execution deadline
```

---

# 237. Contract Validation

The runtime checks the solution against the contract before returning it as accepted.

---

# 238. Plan Preconditions

A plan may require:

```text
state predicates
resource availability
authorization
```

before execution.

---

# 239. Plan Postconditions

Plans may declare:

```text
expected state
goal achieved
resource state
```

---

# 240. Execution Handoff

The consumer owns actual side effects.

652 returns an immutable plan/result.

---

# 241. Idempotency

Plan execution systems remain responsible for idempotency.

652 may provide stable plan IDs.

---

# 242. Decision Identity

```text
DecisionId
ProblemId
SolutionId
PlanId
```

must be independently addressable.

---

# 243. Version Graph

Decision artifacts form:

```text
ProblemRevision
   ↓
Solve
   ↓
SolutionRevision
   ↓
PlanRevision
```

---

# 244. Provenance Graph

Artifacts may reference:

```text
model
data
policy
solver
simulation
ML model
profile
```

---

# 245. Data Lineage

Lineage integrates with 640.

---

# 246. ML Model Lineage

Prediction inputs from 643 include:

```text
model_id
model_version
feature_revision
```

---

# 247. Recommendation Lineage

651-derived preferences include:

```text
profile_revision
preference_revision
context_revision
```

---

# 248. Scenario Lineage

648 scenarios include:

```text
scenario_id
simulation_version
seed
environment_revision
```

---

# 249. Decision Provenance Export

```text
axiom decision explain --provenance
```

should emit machine-readable provenance.

---

# 250. Minimal Example

```text
decision allocate_gpu {
    variable gpu : GPU

    constraint gpu.memory >= 24GB

    objective minimize gpu.cost
}
```

---

# 251. Scheduling Example

```text
decision schedule {
    variable start[A] : time
    variable start[B] : time

    constraint A.end <= B.start

    objective minimize B.end
}
```

---

# 252. Routing Example

```text
decision route {
    route vehicle from Hanoi to HaiPhong

    constraint fuel <= 20L

    objective minimize travel_time
}
```

---

# 253. Multi-Objective Example

```text
objective pareto {
    minimize latency
    minimize cost
    minimize energy
}
```

Returns a frontier rather than silently selecting one point.

---

# 254. Planning Example

```text
plan deliver_package {
    initial:
        package_at(A)

    actions:
        move(A,B)
        move(B,C)

    goal:
        package_at(C)
}
```

---

# 255. Infeasible Example

```text
constraint x >= 10
constraint x <= 5
```

Result:

```text
status = Infeasible
```

---

# 256. Timeout Example

```text
limits.max_time = 100ms
```

If no proof completes:

```text
status = Timeout
```

with best feasible solution if available.

---

# 257. Partial Example

```text
status = Partial
optimality.proven = false
gap = 0.023
```

---

# 258. Warm Start Example

```text
solve(problem_v2,
      warm_start = solution_v1)
```

---

# 259. Replanning Example

```text
replan(
    previous_plan,
    changed_resource = GPU7
)
```

---

# 260. Agent Example

```text
agent.plan {
    use planner
    respect policy
    return validated_plan
}
```

---

# 261. Compiler Output

Compiler emits:

```text
program.ax
program.axdecision
program.axsolver
program.axsolution-schema
```

only when required by the build.

---

# 262. Link-Time Optimization

Solver components SHOULD support:

```text
LTO
function elimination
specialization
constant propagation
```

---

# 263. Solver Specialization

A model known at compile time may generate specialized solver code.

Example:

```text
fixed 8-variable assignment
```

can compile to specialized machine code.

---

# 264. Partial Evaluation

Static constraints should be evaluated at compile time where possible.

---

# 265. JIT Boundary

Optional JIT can specialize:

```text
objective evaluation
constraint evaluation
heuristic evaluation
```

but native AOT remains primary.

---

# 266. ABI Minimalism

The core decision ABI SHOULD contain only:

```text
model
solve
cancel
result
```

Advanced features remain optional extensions.

---

# 267. Plugin ABI

Provider plugins expose:

```text
ax_decision_provider_init
ax_decision_provider_capabilities
ax_decision_provider_solve
ax_decision_provider_shutdown
```

or equivalent stable Axiom ABI.

---

# 268. Native Provider

Axiom itself provides at least one native provider.

---

# 269. Provider Health

Provider registry tracks:

```text
available
healthy
degraded
unavailable
```

---

# 270. Provider Failover

Failover must preserve model semantics.

---

# 271. Solver Telemetry

Provider performance is observable through 633.

---

# 272. Cost Accounting

Solver resource usage can be charged to:

```text
tenant
application
agent
workflow
decision
```

---

# 273. Budget Propagation

Parent budget:

```text
agent budget
```

is subdivided into:

```text
planning budget
solver budget
simulation budget
```

---

# 274. Budget Exhaustion

Child execution cannot exceed parent budget.

---

# 275. Agent Loop Protection

Repeated replanning must have explicit:

```text
max_replans
max_total_time
max_cost
```

---

# 276. Oscillation Detection

Replanning engines SHOULD detect:

```text
plan A
plan B
plan A
plan B
```

oscillation.

---

# 277. Hysteresis

Decision policies may require a minimum improvement before replacing an existing plan.

---

# 278. Stability

Stable decisions reduce unnecessary system churn.

---

# 279. Change Cost

Optimization may include:

```text
change_cost(current, candidate)
```

to discourage needless reconfiguration.

---

# 280. Incremental Objective

Example:

```text
minimize:
    latency
  + migration_cost
```

---

# 281. Existing-State Awareness

Replanning SHOULD treat current state as an explicit baseline.

---

# 282. Constraint Scope

Constraints may be:

```text
global
tenant
application
workflow
task
resource
scenario
```

---

# 283. Constraint Composition

Constraint sets support:

```text
union
intersection
difference
override
```

with explicit precedence.

---

# 284. Policy vs Constraint

Policy is authoritative governance.

Constraint is a mathematical/modeling condition.

A policy denial cannot be weakened by assigning it a low optimization weight.

---

# 285. Objective vs Preference

Preference from 651 becomes an objective only through explicit mapping.

---

# 286. Risk Objective

Risk may be modeled as:

```text
expected_loss
variance
worst_case
CVaR
```

where supported.

---

# 287. Risk Semantics

Risk metrics MUST preserve whether they are:

```text
exact
estimated
simulated
model-based
```

---

# 288. Scenario Weights

Scenario probabilities must be explicit.

---

# 289. Robust Set

Robust optimization may define:

```text
uncertainty_set
```

without assuming a probability distribution.

---

# 290. Decision Confidence

Confidence may be reported only when justified by the underlying method.

---

# 291. No Fabricated Certainty

The engine MUST NOT convert:

```text
heuristic result
```

into:

```text
guaranteed optimal result
```

---

# 292. Search Trace

Optional search trace:

```text
expanded
pruned
accepted
rejected
```

must be bounded/configurable.

---

# 293. Privacy-Preserving Explanation

Explanation output may redact:

```text
sensitive inputs
private features
protected attributes
```

while preserving decision validity metadata.

---

# 294. Explanation Access Control

Different users may receive different explanation detail.

---

# 295. Audit Immutability

Production decision snapshots SHOULD be append-only.

---

# 296. Decision Retention

Retention integrates with 640.

---

# 297. Deletion

Deletion requests must propagate to decision artifacts where legally/applicably required.

---

# 298. Cache Deletion

Cached decisions containing deleted data must be invalidated.

---

# 299. Security Boundary

A decision result does not grant authority.

```text
solution != permission
```

---

# 300. Final Security Rule

No solver output can bypass:

```text
603 Capability
639 Policy
640 Governance
```

---

# 301. Performance Target

For simple models:

```text
low allocation
low startup latency
native machine code
```

---

# 302. Scaling Target

For large models:

```text
incremental solving
parallel search
distributed provider
checkpointing
```

---

# 303. Compilation Target

Decision DSL compilation should add minimal overhead to normal application builds.

---

# 304. Runtime Target

Unused optimization features MUST NOT impose mandatory runtime overhead.

---

# 305. Embedded Target

Core constraint solving SHOULD remain usable without heap-heavy infrastructure.

---

# 306. Memory Target

Solver memory should be bounded by declared budgets whenever possible.

---

# 307. Failure Target

Resource exhaustion should produce structured failure, not process-wide corruption.

---

# 308. Determinism Target

A deterministic problem + deterministic solver + deterministic configuration must yield semantically identical results.

---

# 309. Numerical Reproducibility

Cross-platform floating-point reproducibility is guaranteed only when the selected numerical profile supports it.

---

# 310. Cross-Platform

Decision IR remains platform-neutral.

---

# 311. Native Optimization

Backend may specialize for:

```text
x86 AVX
ARM NEON
GPU
```

without changing semantics.

---

# 312. Compilation Cache

Compiled decision models may use Axiom's global compiler cache.

Cache invalidation includes:

```text
source hash
DecisionIR version
compiler version
solver backend version
```

---

# 313. Precompiled Models

A compiled decision model can be reused if all semantic fingerprints match.

---

# 314. AI Artifact Reuse

AI agents may inspect `.axdecision` metadata before reconstructing the problem.

---

# 315. Human-Readable Export

```text
axiom decision explain model.axdecision
```

may produce:

```text
variables
constraints
objectives
solution
optimality
provenance
```

---

# 316. Model Validation CLI

```text
axiom decision validate model.axdecision
```

---

# 317. Benchmark CLI

```text
axiom decision benchmark model.axdecision
```

---

# 318. Solver Inspection

```text
axiom solver inspect native
```

shows:

```text
algorithms
domains
constraints
exactness
parallelism
```

---

# 319. Plan Visualization

GUI tools may visualize:

```text
DAG
schedule
resource timeline
route
search tree
Pareto frontier
```

---

# 320. GUI Integration

GUI is not required by the decision runtime.

It consumes standardized artifacts.

---

# 321. AI GUI Integration

AI tools may render:

```text
decision graph
constraint graph
schedule
plan
```

from metadata.

---

# 322. Decision Graph

Problem dependencies can be represented as:

```text
variables
  ↓
constraints
  ↓
objectives
  ↓
solution
```

---

# 323. Constraint Graph

Useful for debugging and propagation analysis.

---

# 324. Resource Timeline

Scheduling UI can show:

```text
resource
task
start
end
capacity
```

---

# 325. Route Visualization

Route solutions expose graph paths for rendering.

---

# 326. Search Visualization

Search statistics may be visualized without exposing hidden reasoning.

---

# 327. Optimization Visualization

Objective values and Pareto fronts may be rendered.

---

# 328. Solver Recommendation

Axiom may recommend a solver based on declared capabilities, but the chosen solver remains inspectable.

---

# 329. Automatic Solver Selection Metadata

```text
selection_reason
candidate_solvers
selected_solver
```

---

# 330. User Override

Users can explicitly select:

```text
solver = native_cp
solver = astar
solver = external_provider
```

---

# 331. Provider Preference

Applications can define:

```text
prefer_native
prefer_exact
prefer_fast
prefer_deterministic
```

---

# 332. Tradeoff Configuration

Tradeoffs MUST be explicit.

---

# 333. No Hidden Optimization

The compiler/runtime MUST NOT silently alter declared objective semantics for convenience.

---

# 334. Approximation Opt-In

Approximation requires explicit configuration.

---

# 335. Constraint Approximation

Approximating a hard constraint requires explicit policy and audit metadata.

---

# 336. Model Simplification

Compiler optimizations are permitted only when semantics are preserved.

---

# 337. Semantic Equivalence

Decision IR transformations require semantic equivalence.

---

# 338. Solver Correctness

A solver is correct if every returned accepted solution satisfies all hard constraints and reported proof claims are valid.

---

# 339. Acceptance Criterion A

All hard constraints are checked independently before solution acceptance.

---

# 340. Acceptance Criterion B

A timeout cannot produce `Optimal` without an independent proof.

---

# 341. Acceptance Criterion C

A heuristic solver identifies itself as heuristic.

---

# 342. Acceptance Criterion D

Problem revisions invalidate incompatible cached solutions.

---

# 343. Acceptance Criterion E

Solver checkpoints identify the exact model revision.

---

# 344. Acceptance Criterion F

Provider failure does not corrupt the host application.

---

# 345. Acceptance Criterion G

Custom constraints cannot bypass capability/security boundaries.

---

# 346. Acceptance Criterion H

Policy denial cannot be converted into a soft optimization penalty.

---

# 347. Acceptance Criterion I

Decision artifacts are deterministic under deterministic configuration.

---

# 348. Acceptance Criterion J

All solution statuses are machine-readable.

---

# 349. Acceptance Criterion K

All objectives are preserved independently.

---

# 350. Acceptance Criterion L

Pareto solutions can be represented without forced scalarization.

---

# 351. Acceptance Criterion M

Schedules reject overlapping non-shareable tasks.

---

# 352. Acceptance Criterion N

Plans can be independently validated.

---

# 353. Acceptance Criterion O

Routes preserve graph revision.

---

# 354. Acceptance Criterion P

Warm starts are validated before reuse.

---

# 355. Acceptance Criterion Q

Incremental solving preserves semantic equivalence.

---

# 356. Acceptance Criterion R

Resource budgets are enforced.

---

# 357. Acceptance Criterion S

Cancellation is safe.

---

# 358. Acceptance Criterion T

Replanning detects stale state.

---

# 359. Acceptance Criterion U

AI model provenance is preserved.

---

# 360. Acceptance Criterion V

Personalization provenance is preserved.

---

# 361. Acceptance Criterion W

Simulation-derived metrics are marked as simulated.

---

# 362. Acceptance Criterion X

Decision provenance can be exported.

---

# 363. Acceptance Criterion Y

Decision artifacts support schema evolution.

---

# 364. Acceptance Criterion Z

Unused solver components can be stripped from builds.

---

# 365. Acceptance Criterion AA

Core decision runtime requires no third-party solver.

---

# 366. Acceptance Criterion AB

Native solver can solve baseline constraint/search classes.

---

# 367. Acceptance Criterion AC

Search algorithms expose bounded resource usage.

---

# 368. Acceptance Criterion AD

Search results expose termination reason.

---

# 369. Acceptance Criterion AE

Optimization results expose objective vector.

---

# 370. Acceptance Criterion AF

Optimization results expose optimality gap when available.

---

# 371. Acceptance Criterion AG

Infeasibility can be represented independently from timeout.

---

# 372. Acceptance Criterion AH

Unbounded objectives are detected where provable.

---

# 373. Acceptance Criterion AI

Numerical tolerance is explicit.

---

# 374. Acceptance Criterion AJ

Integer semantics remain exact.

---

# 375. Acceptance Criterion AK

Unit-aware decision expressions compile correctly.

---

# 376. Acceptance Criterion AL

Distributed solving preserves solution semantics.

---

# 377. Acceptance Criterion AM

Parallel execution preserves correctness.

---

# 378. Acceptance Criterion AN

Provider ABI version is validated.

---

# 379. Acceptance Criterion AO

External providers cannot silently gain unrestricted authority.

---

# 380. Acceptance Criterion AP

Decision execution remains separate from plan generation.

---

# 381. Acceptance Criterion AQ

Dry-run mode produces no side effects.

---

# 382. Acceptance Criterion AR

Decision snapshots are immutable.

---

# 383. Acceptance Criterion AS

Audit metadata records model and solver versions.

---

# 384. Acceptance Criterion AT

Sensitive explanation fields can be redacted.

---

# 385. Acceptance Criterion AU

Decision cache keys contain all semantic dependencies.

---

# 386. Acceptance Criterion AV

Cache invalidation occurs on policy revision when required.

---

# 387. Acceptance Criterion AW

Cache invalidation occurs on model revision.

---

# 388. Acceptance Criterion AX

Cache invalidation occurs on required state revision.

---

# 389. Acceptance Criterion AY

Solver selection is observable.

---

# 390. Acceptance Criterion AZ

Solver fallback cannot weaken hard constraints.

---

# 391. Acceptance Criterion BA

Constraint relaxation is explicit.

---

# 392. Acceptance Criterion BB

Plan alternatives can be represented.

---

# 393. Acceptance Criterion BC

Pareto archives remove dominated solutions correctly.

---

# 394. Acceptance Criterion BD

Tie-breaking is deterministic when requested.

---

# 395. Acceptance Criterion BE

Randomized solvers record seeds.

---

# 396. Acceptance Criterion BF

Scenario probabilities are explicit.

---

# 397. Acceptance Criterion BG

Estimated probabilities are labeled estimates.

---

# 398. Acceptance Criterion BH

Robust optimization can operate without probability distributions.

---

# 399. Acceptance Criterion BI

Risk metrics preserve their estimation method.

---

# 400. Acceptance Criterion BJ

Decision confidence cannot be fabricated.

---

# 401. Acceptance Criterion BK

Decision explanations use structured facts.

---

# 402. Acceptance Criterion BL

Hidden chain-of-thought is never required by the API.

---

# 403. Acceptance Criterion BM

Constraint violations identify responsible constraint IDs.

---

# 404. Acceptance Criterion BN

Solution provenance survives serialization.

---

# 405. Acceptance Criterion BO

Decision IR is serializable.

---

# 406. Acceptance Criterion BP

Decision IR has a version number.

---

# 407. Acceptance Criterion BQ

Provider capability negotiation occurs before solve.

---

# 408. Acceptance Criterion BR

Unsupported models fail clearly.

---

# 409. Acceptance Criterion BS

Fallback is explicit.

---

# 410. Acceptance Criterion BT

Long-running solves support checkpoints.

---

# 411. Acceptance Criterion BU

Checkpoint restoration verifies compatibility.

---

# 412. Acceptance Criterion BV

Partial solutions preserve best-known bounds where available.

---

# 413. Acceptance Criterion BW

Streaming solutions obey backpressure.

---

# 414. Acceptance Criterion BX

Solver metrics integrate with observability.

---

# 415. Acceptance Criterion BY

Tenant quotas are enforced.

---

# 416. Acceptance Criterion BZ

Agent loops have explicit budgets.

---

# 417. Acceptance Criterion CA

Oscillation can be detected.

---

# 418. Acceptance Criterion CB

Change cost can be modeled.

---

# 419. Acceptance Criterion CC

State freshness is explicit.

---

# 420. Acceptance Criterion CD

Stale decisions can be rejected.

---

# 421. Acceptance Criterion CE

Plan validation checks preconditions.

---

# 422. Acceptance Criterion CF

Plan validation checks postconditions.

---

# 423. Acceptance Criterion CG

Plan validation checks resource constraints.

---

# 424. Acceptance Criterion CH

Plan validation checks policy requirements.

---

# 425. Acceptance Criterion CI

Plan execution remains outside 652.

---

# 426. Acceptance Criterion CJ

Resource accounting remains authoritative in 606.

---

# 427. Acceptance Criterion CK

Cluster coordination remains authoritative in 635.

---

# 428. Acceptance Criterion CL

Workflow execution remains authoritative in 629.

---

# 429. Acceptance Criterion CM

Deployment execution remains authoritative in 636.

---

# 430. Acceptance Criterion CN

Authorization remains authoritative in 639.

---

# 431. Acceptance Criterion CO

Governance remains authoritative in 640.

---

# 432. Acceptance Criterion CP

ML prediction remains authoritative only within 643's model contract.

---

# 433. Acceptance Criterion CQ

Simulation outputs remain marked as simulation outputs.

---

# 434. Acceptance Criterion CR

Personalization remains subordinate to hard constraints.

---

# 435. Acceptance Criterion CS

Knowledge graph revisions are preserved.

---

# 436. Acceptance Criterion CT

Search candidate provenance is preserved.

---

# 437. Acceptance Criterion CU

Decision model fingerprints are stable.

---

# 438. Acceptance Criterion CV

Equivalent models produce equivalent fingerprints.

---

# 439. Acceptance Criterion CW

Compiler cache invalidates on semantic changes.

---

# 440. Acceptance Criterion CX

Link-time elimination removes unused solver modules.

---

# 441. Acceptance Criterion CY

Native backend remains dependency-free.

---

# 442. Acceptance Criterion CZ

WASM profile can execute supported native solvers.

---

# 443. Acceptance Criterion DA

Mobile profile can execute bounded decision problems.

---

# 444. Acceptance Criterion DB

Embedded profile can operate under bounded memory.

---

# 445. Acceptance Criterion DC

Server profile supports distributed providers.

---

# 446. Acceptance Criterion DD

Edge profile supports deterministic bounded solving.

---

# 447. Acceptance Criterion DE

GUI consumes decision artifacts without coupling to solver internals.

---

# 448. Acceptance Criterion DF

AI agents can consume structured results.

---

# 449. Acceptance Criterion DG

Decision metadata is AI-readable.

---

# 450. Acceptance Criterion DH

Human-readable explanations can be generated from structured facts.

---

# 451. Acceptance Criterion DI

Decision comparison does not require arbitrary global ranking.

---

# 452. Acceptance Criterion DJ

Incomparable Pareto solutions remain distinguishable.

---

# 453. Acceptance Criterion DK

Alternative plans remain independently validatable.

---

# 454. Acceptance Criterion DL

High-impact decisions can require human approval.

---

# 455. Acceptance Criterion DM

Approval cannot be silently bypassed by the solver.

---

# 456. Acceptance Criterion DN

Dry-run guarantees no side effects.

---

# 457. Acceptance Criterion DO

Audit records can identify the decision actor.

---

# 458. Acceptance Criterion DP

Privacy policies apply to decision snapshots.

---

# 459. Acceptance Criterion DQ

Deletion policies invalidate affected caches.

---

# 460. Acceptance Criterion DR

Decision retention follows governance policy.

---

# 461. Acceptance Criterion DS

Numerical edge cases are tested.

---

# 462. Acceptance Criterion DT

Solver correctness is independently tested.

---

# 463. Acceptance Criterion DU

Differential solver testing is supported.

---

# 464. Acceptance Criterion DV

Fuzz testing is supported.

---

# 465. Acceptance Criterion DW

Property testing is supported.

---

# 466. Acceptance Criterion DX

Metamorphic testing is supported.

---

# 467. Acceptance Criterion DY

Regression fixtures are content-addressed.

---

# 468. Acceptance Criterion DZ

Benchmark configurations are reproducible.

---

# 469. Acceptance Criterion EA

Solver diagnostics expose performance counters.

---

# 470. Acceptance Criterion EB

Resource usage is observable.

---

# 471. Acceptance Criterion EC

Cost accounting can attribute solver usage.

---

# 472. Acceptance Criterion ED

Parent budgets propagate to child solves.

---

# 473. Acceptance Criterion EE

Automatic solver selection can be overridden.

---

# 474. Acceptance Criterion EF

Provider health is observable.

---

# 475. Acceptance Criterion EG

Provider failover is controlled.

---

# 476. Acceptance Criterion EH

External solver adapters are optional.

---

# 477. Acceptance Criterion EI

Provider ABI is versioned.

---

# 478. Acceptance Criterion EJ

Decision artifacts preserve schema compatibility.

---

# 479. Acceptance Criterion EK

Unknown optional fields can survive round-trip serialization.

---

# 480. Acceptance Criterion EL

Unknown mandatory semantic versions fail safely.

---

# 481. Acceptance Criterion EM

Decision APIs expose cancellation.

---

# 482. Acceptance Criterion EN

Cancellation preserves valid best-known state.

---

# 483. Acceptance Criterion EO

Solver crash cannot corrupt application state.

---

# 484. Acceptance Criterion EP

Checkpoint files are atomic.

---

# 485. Acceptance Criterion EQ

Checkpoint recovery verifies integrity.

---

# 486. Acceptance Criterion ER

Model serialization is canonical.

---

# 487. Acceptance Criterion ES

Constraint serialization is canonical.

---

# 488. Acceptance Criterion ET

Objective serialization is canonical.

---

# 489. Acceptance Criterion EU

Problem hashes include semantic metadata.

---

# 490. Acceptance Criterion EV

Provider versions participate in reproducibility.

---

# 491. Acceptance Criterion EW

Random seeds participate in reproducibility.

---

# 492. Acceptance Criterion EX

Numerical profile participates in reproducibility.

---

# 493. Acceptance Criterion EY

State revisions participate in reproducibility.

---

# 494. Acceptance Criterion EZ

Policy revisions participate in reproducibility.

---

# 495. Acceptance Criterion FA

Personalization revisions participate in reproducibility when used.

---

# 496. Acceptance Criterion FB

Simulation revisions participate in reproducibility when used.

---

# 497. Acceptance Criterion FC

ML model revisions participate in reproducibility when used.

---

# 498. Acceptance Criterion FD

Decision lineage can be traversed.

---

# 499. Acceptance Criterion FE

Decision artifacts can be independently verified.

---

# 500. Acceptance Criterion FF

High-assurance certificates can be verified independently.

---

# 501. Acceptance Criterion FG

Solver exactness metadata is preserved.

---

# 502. Acceptance Criterion FH

Approximate solver metadata is preserved.

---

# 503. Acceptance Criterion FI

Heuristic metadata is preserved.

---

# 504. Acceptance Criterion FJ

Stochastic metadata is preserved.

---

# 505. Acceptance Criterion FK

Simulation-based metadata is preserved.

---

# 506. Acceptance Criterion FL

Constraint relaxation metadata is preserved.

---

# 507. Acceptance Criterion FM

Objective scalarization metadata is preserved.

---

# 508. Acceptance Criterion FN

Pareto semantics are preserved.

---

# 509. Acceptance Criterion FO

Lexicographic semantics are preserved.

---

# 510. Acceptance Criterion FP

Hierarchical priority semantics are preserved.

---

# 511. Acceptance Criterion FQ

Soft constraint penalties remain explicit.

---

# 512. Acceptance Criterion FR

Hard constraints remain authoritative.

---

# 513. Acceptance Criterion FS

Solver optimization cannot override authorization.

---

# 514. Acceptance Criterion FT

Solver optimization cannot override governance.

---

# 515. Acceptance Criterion FU

Solver optimization cannot override resource admission.

---

# 516. Acceptance Criterion FV

Decision plans can be diffed.

---

# 517. Acceptance Criterion FW

Schedule plans can be diffed.

---

# 518. Acceptance Criterion FX

Decision alternatives can be archived.

---

# 519. Acceptance Criterion FY

Solution archives can be bounded.

---

# 520. Acceptance Criterion FZ

Dominated Pareto solutions can be removed.

---

# 521. Acceptance Criterion GA

Search frontier memory is bounded by budget.

---

# 522. Acceptance Criterion GB

Transposition tables can be bounded.

---

# 523. Acceptance Criterion GC

Search pruning statistics are available.

---

# 524. Acceptance Criterion GD

Heuristic properties are declared.

---

# 525. Acceptance Criterion GE

The runtime does not assume undeclared heuristic guarantees.

---

# 526. Acceptance Criterion GF

Branch-and-bound bounds are validated.

---

# 527. Acceptance Criterion GG

Dynamic programming state keys are deterministic.

---

# 528. Acceptance Criterion GH

A* can expose admissibility metadata.

---

# 529. Acceptance Criterion GI

Beam width is explicit.

---

# 530. Acceptance Criterion GJ

Search depth limits are explicit.

---

# 531. Acceptance Criterion GK

Enumeration limits are explicit.

---

# 532. Acceptance Criterion GL

Constraint propagation is observable.

---

# 533. Acceptance Criterion GM

Domain reductions preserve semantics.

---

# 534. Acceptance Criterion GN

Static contradiction detection is sound.

---

# 535. Acceptance Criterion GO

Unboundedness detection is sound.

---

# 536. Acceptance Criterion GP

Numerical tolerances are not silently global.

---

# 537. Acceptance Criterion GQ

Unit semantics are checked.

---

# 538. Acceptance Criterion GR

Time semantics are checked.

---

# 539. Acceptance Criterion GS

Graph revisions are checked.

---

# 540. Acceptance Criterion GT

Resource calendars are respected.

---

# 541. Acceptance Criterion GU

Non-preemptible tasks are never split.

---

# 542. Acceptance Criterion GV

Precedence constraints are validated.

---

# 543. Acceptance Criterion GW

Capacity constraints are validated.

---

# 544. Acceptance Criterion GX

Assignment cardinality is validated.

---

# 545. Acceptance Criterion GY

Route validity is validated.

---

# 546. Acceptance Criterion GZ

Plan goal satisfaction is validated.

---

# 547. Acceptance Criterion HA

Plan action preconditions are validated.

---

# 548. Acceptance Criterion HB

Plan effects are validated.

---

# 549. Acceptance Criterion HC

Scenario identities are preserved.

---

# 550. Acceptance Criterion HD

Scenario probabilities are preserved.

---

# 551. Acceptance Criterion HE

Robust uncertainty sets are preserved.

---

# 552. Acceptance Criterion HF

Risk calculations expose their method.

---

# 553. Acceptance Criterion HG

Monte Carlo seeds are preserved.

---

# 554. Acceptance Criterion HH

Simulation seeds are preserved.

---

# 555. Acceptance Criterion HI

ML feature revisions are preserved.

---

# 556. Acceptance Criterion HJ

ML prediction provenance is preserved.

---

# 557. Acceptance Criterion HK

Personalization provenance is preserved.

---

# 558. Acceptance Criterion HL

Knowledge graph provenance is preserved.

---

# 559. Acceptance Criterion HM

Search provenance is preserved.

---

# 560. Acceptance Criterion HN

Workflow provenance is preserved.

---

# 561. Acceptance Criterion HO

Cluster provenance is preserved.

---

# 562. Acceptance Criterion HP

Deployment provenance is preserved.

---

# 563. Acceptance Criterion HQ

Policy provenance is preserved.

---

# 564. Acceptance Criterion HR

Governance provenance is preserved.

---

# 565. Acceptance Criterion HS

Decision provenance is queryable.

---

# 566. Acceptance Criterion HT

Decision provenance is exportable.

---

# 567. Acceptance Criterion HU

Sensitive provenance fields are access-controlled.

---

# 568. Acceptance Criterion HV

Audit snapshots are immutable.

---

# 569. Acceptance Criterion HW

Decision retention is configurable.

---

# 570. Acceptance Criterion HX

Decision deletion propagates to caches.

---

# 571. Acceptance Criterion HY

Solver usage can be cost-accounted.

---

# 572. Acceptance Criterion HZ

Multi-tenant solve isolation is enforceable.

---

# 573. Acceptance Criterion IA

Provider capabilities are inspectable.

---

# 574. Acceptance Criterion IB

Provider health is inspectable.

---

# 575. Acceptance Criterion IC

Provider versions are inspectable.

---

# 576. Acceptance Criterion ID

Solver selection is inspectable.

---

# 577. Acceptance Criterion IE

Fallback is inspectable.

---

# 578. Acceptance Criterion IF

Auto-tuning is inspectable.

---

# 579. Acceptance Criterion IG

Anytime improvements are observable.

---

# 580. Acceptance Criterion IH

Streaming results are cancellable.

---

# 581. Acceptance Criterion II

Backpressure is enforced.

---

# 582. Acceptance Criterion IJ

Long-running decisions support checkpointing.

---

# 583. Acceptance Criterion IK

Checkpoint restore preserves semantics.

---

# 584. Acceptance Criterion IL

Checkpoint mismatch is detected.

---

# 585. Acceptance Criterion IM

Crash recovery is atomic.

---

# 586. Acceptance Criterion IN

Partial results are explicitly marked.

---

# 587. Acceptance Criterion IO

Timeout results are explicitly marked.

---

# 588. Acceptance Criterion IP

Cancelled results are explicitly marked.

---

# 589. Acceptance Criterion IQ

Unknown results are explicitly marked.

---

# 590. Acceptance Criterion IR

Optimal results are explicitly proven.

---

# 591. Acceptance Criterion IS

Suboptimal results identify their basis.

---

# 592. Acceptance Criterion IT

Feasible results identify feasibility.

---

# 593. Acceptance Criterion IU

Infeasible results identify infeasibility.

---

# 594. Acceptance Criterion IV

Decision execution remains separate.

---

# 595. Acceptance Criterion IW

Dry-run is side-effect free.

---

# 596. Acceptance Criterion IX

Human approval boundaries are enforceable.

---

# 597. Acceptance Criterion IY

Agent execution cannot bypass decision safety boundaries.

---

# 598. Acceptance Criterion IZ

Decision APIs remain usable without AI.

---

# 599. Acceptance Criterion JA

AI integration remains optional.

---

# 600. Acceptance Criterion JB

Decision runtime remains usable without distributed infrastructure.

---

# 601. Acceptance Criterion JC

Decision runtime remains usable without GPU.

---

# 602. Acceptance Criterion JD

Decision runtime remains usable without external solver providers.

---

# 603. Acceptance Criterion JE

Decision runtime remains usable without database infrastructure for in-memory problems.

---

# 604. Acceptance Criterion JF

Minimal profiles remain compact.

---

# 605. Acceptance Criterion JG

Unused algorithms can be removed at link time.

---

# 606. Acceptance Criterion JH

Native compilation produces efficient machine code.

---

# 607. Acceptance Criterion JI

Decision models can be precompiled.

---

# 608. Acceptance Criterion JJ

Compiled model caches are safely invalidated.

---

# 609. Acceptance Criterion JK

AI-readable artifacts are generated only when requested/required.

---

# 610. Acceptance Criterion JL

Human-readable artifacts remain optional.

---

# 611. Acceptance Criterion JM

Decision metadata is UTF-8 compatible.

---

# 612. Acceptance Criterion JN

Decision DSL supports normal Axiom UTF-8 identifiers where allowed.

---

# 613. Acceptance Criterion JO

Decision IR is platform independent.

---

# 614. Acceptance Criterion JP

Native backends can specialize without changing semantics.

---

# 615. Acceptance Criterion JQ

WASM execution preserves semantics.

---

# 616. Acceptance Criterion JR

Mobile execution preserves semantics.

---

# 617. Acceptance Criterion JS

Embedded execution preserves semantics within declared limits.

---

# 618. Acceptance Criterion JT

Server execution can scale through providers.

---

# 619. Acceptance Criterion JU

Edge execution can operate deterministically.

---

# 620. Acceptance Criterion JV

Decision GUI remains decoupled.

---

# 621. Acceptance Criterion JW

Decision CLI remains scriptable.

---

# 622. Acceptance Criterion JX

Decision artifacts are automatable by AI agents.

---

# 623. Acceptance Criterion JY

Compiler diagnostics identify precise model locations.

---

# 624. Acceptance Criterion JZ

Static errors are deterministic.

---

# 625. Acceptance Criterion KA

Runtime errors are structured.

---

# 626. Acceptance Criterion KB

Solver errors preserve provider identity.

---

# 627. Acceptance Criterion KC

Provider errors do not masquerade as model infeasibility.

---

# 628. Acceptance Criterion KD

Model infeasibility does not masquerade as provider failure.

---

# 629. Acceptance Criterion KE

Timeout does not masquerade as infeasibility.

---

# 630. Acceptance Criterion KF

Unknown does not masquerade as infeasibility.

---

# 631. Acceptance Criterion KG

Approximation does not masquerade as exactness.

---

# 632. Acceptance Criterion KH

Simulation does not masquerade as observed reality.

---

# 633. Acceptance Criterion KI

Predictions do not masquerade as facts.

---

# 634. Acceptance Criterion KJ

Preferences do not masquerade as mandatory policy.

---

# 635. Acceptance Criterion KK

Policy does not masquerade as optimization preference.

---

# 636. Acceptance Criterion KL

Governance does not become optional through optimization.

---

# 637. Acceptance Criterion KM

Security boundaries remain outside optimization semantics.

---

# 638. Acceptance Criterion KN

All critical decision dependencies are revisioned.

---

# 639. Acceptance Criterion KO

Decision snapshots preserve revision references.

---

# 640. Acceptance Criterion KP

Decision caches respect revisions.

---

# 641. Acceptance Criterion KQ

Decision provenance survives restart.

---

# 642. Acceptance Criterion KR

Decision provenance survives serialization.

---

# 643. Acceptance Criterion KS

Decision provenance survives provider execution.

---

# 644. Acceptance Criterion KT

Decision results can be independently validated.

---

# 645. Acceptance Criterion KU

Decision plans can be independently validated.

---

# 646. Acceptance Criterion KV

Schedules can be independently validated.

---

# 647. Acceptance Criterion KW

Routes can be independently validated.

---

# 648. Acceptance Criterion KX

Assignments can be independently validated.

---

# 649. Acceptance Criterion KY

Optimization objectives can be independently recomputed.

---

# 650. Acceptance Criterion KZ

Constraint satisfaction can be independently recomputed.

---

# 651. Acceptance Criterion LA

Decision engine integrates cleanly with 651 personalization.

---

# 652. Acceptance Criterion LB

Decision engine integrates cleanly with 650 memory/context.

---

# 653. Acceptance Criterion LC

Decision engine integrates cleanly with 649 multimodal inputs.

---

# 654. Acceptance Criterion LD

Decision engine integrates cleanly with 648 simulation.

---

# 655. Acceptance Criterion LE

Decision engine integrates cleanly with 647 AI governance.

---

# 656. Acceptance Criterion LF

Decision engine integrates cleanly with 646 evaluation.

---

# 657. Acceptance Criterion LG

Decision engine integrates cleanly with 645 knowledge graphs.

---

# 658. Acceptance Criterion LH

Decision engine integrates cleanly with 644 agents.

---

# 659. Acceptance Criterion LI

Decision engine integrates cleanly with 643 ML.

---

# 660. Acceptance Criterion LJ

Decision engine integrates cleanly with 642 analytics.

---

# 661. Acceptance Criterion LK

Decision engine integrates cleanly with 641 retrieval.

---

# 662. Acceptance Criterion LL

Decision engine integrates cleanly with 639 policy.

---

# 663. Acceptance Criterion LM

Decision engine integrates cleanly with 638 secrets where needed.

---

# 664. Acceptance Criterion LN

Decision engine integrates cleanly with 637 configuration.

---

# 665. Acceptance Criterion LO

Decision engine integrates cleanly with 636 deployment.

---

# 666. Acceptance Criterion LP

Decision engine integrates cleanly with 635 coordination.

---

# 667. Acceptance Criterion LQ

Decision engine integrates cleanly with 634 events.

---

# 668. Acceptance Criterion LR

Decision engine integrates cleanly with 633 observability.

---

# 669. Acceptance Criterion LS

Decision engine integrates cleanly with 632 edge.

---

# 670. Acceptance Criterion LT

Decision engine integrates cleanly with 631 service runtime.

---

# 671. Acceptance Criterion LU

Decision engine integrates cleanly with 630 distributed compute.

---

# 672. Acceptance Criterion LV

Decision engine integrates cleanly with 629 workflows.

---

# 673. Acceptance Criterion LW

Decision engine integrates cleanly with 628 distributed data.

---

# 674. Acceptance Criterion LX

Decision engine integrates cleanly with 627 identity.

---

# 675. Acceptance Criterion LY

Decision engine integrates cleanly with 626 HTTP/service interfaces.

---

# 676. Acceptance Criterion LZ

Decision engine integrates cleanly with 625 package/distribution.

---

# 677. Acceptance Criterion MA

Decision engine integrates cleanly with 624 scripting.

---

# 678. Acceptance Criterion MB

Decision engine integrates cleanly with 623 plugins.

---

# 679. Acceptance Criterion MC

Decision engine integrates cleanly with 622 navigation where scheduling/navigation decisions are exposed.

---

# 680. Acceptance Criterion MD

Decision engine integrates cleanly with 621 document workflows.

---

# 681. Acceptance Criterion ME

Decision engine integrates cleanly with 620 reactive state.

---

# 682. Acceptance Criterion MF

Decision engine integrates cleanly with 619 GUI.

---

# 683. Acceptance Criterion MG

Decision engine integrates cleanly with 618 input.

---

# 684. Acceptance Criterion MH

Decision engine integrates cleanly with 617 text/time metadata.

---

# 685. Acceptance Criterion MI

Decision engine integrates cleanly with 616 media pipelines when scheduling media processing.

---

# 686. Acceptance Criterion MJ

Decision engine integrates cleanly with 615 graphics scheduling where applicable.

---

# 687. Acceptance Criterion MK

Decision engine integrates cleanly with 614 devices/resources.

---

# 688. Acceptance Criterion ML

Decision engine integrates cleanly with 613 packaging.

---

# 689. Acceptance Criterion MM

Decision engine integrates cleanly with 612 serialization.

---

# 690. Acceptance Criterion MN

Decision engine integrates cleanly with 611 storage.

---

# 691. Acceptance Criterion MO

Decision engine integrates cleanly with 610 cryptography where secure provenance is required.

---

# 692. Acceptance Criterion MP

Decision engine integrates cleanly with 609 networking.

---

# 693. Acceptance Criterion MQ

Decision engine integrates cleanly with 608 synchronization.

---

# 694. Acceptance Criterion MR

Decision engine integrates cleanly with 607 async execution.

---

# 695. Acceptance Criterion MS

Decision engine integrates cleanly with 606 resource governance.

---

# 696. Acceptance Criterion MT

Decision engine integrates cleanly with 605 supervision.

---

# 697. Acceptance Criterion MU

Decision engine integrates cleanly with 604 IPC.

---

# 698. Acceptance Criterion MV

Decision engine integrates cleanly with 603 capability security.

---

# 699. Acceptance Criterion MW

Decision engine integrates cleanly with 602 observability.

---

# 700. Acceptance Criterion MX

Decision engine integrates cleanly with 601 configuration.

---

# 701. Acceptance Criterion MY

Decision engine integrates cleanly with 600 state persistence.

---

# 702. Core Invariants

The following invariants are mandatory:

```text
I-001 hard constraints define feasibility
I-002 policy denial cannot be optimized away
I-003 governance restrictions cannot be optimized away
I-004 solver output does not grant authority
I-005 timeout is not optimality
I-006 heuristic is not proof
I-007 simulation is not observation
I-008 prediction is not fact
I-009 preference is not policy
I-010 soft constraint is not hard constraint
I-011 stale state is detectable
I-012 model revisions are immutable
I-013 solution provenance is preserved
I-014 solver identity is preserved
I-015 solver version is preserved
I-016 random seed is preserved when relevant
I-017 exactness status is preserved
I-018 numerical tolerance is explicit
I-019 deterministic mode is reproducible
I-020 checkpoint revision must match
I-021 warm start must be validated
I-022 cached solution must match semantic dependencies
I-023 plan execution is external to 652
I-024 cancellation cannot corrupt state
I-025 partial solutions are explicitly marked
I-026 infeasibility differs from timeout
I-027 unknown differs from infeasibility
I-028 unboundedness differs from infeasibility
I-029 Pareto solutions need not be scalarized
I-030 objective vectors remain inspectable
I-031 alternative plans remain independently validatable
I-032 custom code requires capability
I-033 provider failure is distinguishable from model failure
I-034 fallback cannot weaken semantics
I-035 distributed execution preserves model semantics
I-036 solver selection is observable
I-037 resource budgets are enforceable
I-038 parent budgets constrain child solves
I-039 execution side effects are outside solver core
I-040 dry-run produces no side effects
I-041 audit snapshots are immutable
I-042 governance metadata follows data
I-043 sensitive explanations are access-controlled
I-044 deletion invalidates affected caches
I-045 provider ABI is versioned
I-046 DecisionIR is versioned
I-047 DecisionIR is deterministic
I-048 native solver remains dependency-free
I-049 unused solver modules can be stripped
I-050 decision runtime can operate without AI
I-051 AI integration is optional
I-052 GPU integration is optional
I-053 distributed infrastructure is optional
I-054 external solvers are optional
I-055 numerical semantics are explicit
I-056 integer semantics remain exact
I-057 units remain type-safe
I-058 time semantics remain explicit
I-059 graph revisions remain explicit
I-060 scenario identity remains explicit
I-061 scenario probability remains explicit
I-062 uncertainty remains distinguishable from certainty
I-063 risk methodology remains explicit
I-064 learned heuristics cannot alter hard constraints
I-065 agent cannot bypass decision security
I-066 personalization cannot override policy
I-067 workflow remains execution owner
I-068 cluster remains coordination owner
I-069 deployment remains rollout owner
I-070 policy remains authorization owner
I-071 governance remains data-policy owner
I-072 ML remains model-prediction owner
I-073 simulation remains environment-model owner
I-074 decision remains optimization/planning owner
I-075 solutions can be independently validated
I-076 plans can be independently validated
I-077 schedules can be independently validated
I-078 routes can be independently validated
I-079 assignments can be independently validated
I-080 objectives can be independently recomputed
I-081 constraints can be independently recomputed
I-082 provenance survives serialization
I-083 provenance survives restart
I-084 checkpoints are atomic
I-085 cancellation is safe
I-086 resource exhaustion is structured
I-087 solver crash cannot corrupt application state
I-088 cache invalidation is semantic
I-089 compiler optimization preserves decision semantics
I-090 solver approximation is explicit
I-091 randomized behavior is seedable
I-092 tie-breaking can be deterministic
I-093 search limits are explicit
I-094 search statistics are observable
I-095 optimization gap is explicit when available
I-096 proof status is explicit
I-097 human approval boundaries are enforceable
I-098 decision identity is stable
I-099 decision artifacts are AI-readable
I-100 decision artifacts are machine-verifiable
```

---

# 703. Reference Architecture

```text
                   ┌──────────────────────────────┐
                   │  User / Application / Agent  │
                   └──────────────┬───────────────┘
                                  │
                         Decision Request
                                  │
                   ┌──────────────▼───────────────┐
                   │        652 Decision API      │
                   └──────────────┬───────────────┘
                                  │
                  ┌───────────────▼────────────────┐
                  │        Decision Model          │
                  │ variables / domains / context  │
                  └───────────────┬────────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
        Constraints           Objectives          State/Actions
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  ▼
                         Normalization / IR
                                  │
                                  ▼
                       Solver Selection Layer
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
         Constraint           Search              Optimize
          Solver              Engine               Engine
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  ▼
                           Decision Solution
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                Validate       Explain       Compare
                    │
                    ▼
             Policy/Governance
                    │
                    ▼
              Plan / Schedule
                    │
                    ▼
       629 / 631 / 635 / 636 / Runtime
```

---

# 704. Why 652 Exists as a Separate Layer

Axiom now has many AI subsystems capable of producing information:

```text
641 retrieval
642 analytics
643 ML
645 knowledge
648 simulation
649 multimodal
650 memory
651 personalization
```

But information alone does not answer:

```text
Which action should be taken?
Which resource should be assigned?
Which sequence should execute?
Which schedule satisfies all constraints?
Which route minimizes cost?
Which plan remains feasible?
```

652 provides that missing deterministic decision substrate.

---

# 705. Core Architectural Principle

The final separation is:

```text
643 predicts
645 represents knowledge
648 simulates
650 remembers
651 personalizes
652 decides
```

while:

```text
639 authorizes
640 governs
629 executes workflows
635 coordinates clusters
636 deploys
```

This separation prevents the AI layer from becoming an opaque monolithic runtime.

---

# 706. Completion Criteria

BOOTSTRAP-652 is considered complete when:

- DecisionProblem is defined.
- Variables/domains are defined.
- Constraint system is defined.
- Objective system is defined.
- Search architecture is defined.
- Optimization architecture is defined.
- Planning architecture is defined.
- Scheduling architecture is defined.
- Assignment/matching/routing are defined.
- Solver/provider boundary is defined.
- Deterministic and stochastic execution are defined.
- Warm starts and incremental solving are defined.
- Checkpointing is defined.
- Distributed solving boundary is defined.
- Security and governance boundaries are defined.
- AI/ML/simulation/personalization integration is defined.
- Decision provenance is defined.
- Decision artifacts are defined.
- Compiler integration is defined.
- Runtime profiles are defined.
- Native dependency-free baseline is defined.
- 700+ acceptance criteria/invariants are defined.
- No unresolved architectural dependency blocks implementation.

**BOOTSTRAP-652: COMPLETE.**

---

# 707. Next Architecture Task

Proceed automatically to:

## BOOTSTRAP-653
### Native AI Probabilistic Reasoning, Bayesian Inference, Causal Modeling, Uncertainty Quantification, Risk Analysis & Decision-under-Uncertainty Runtime 5.0

652 answers:

> **What action/plan is optimal or feasible under a defined model?**

653 will define the complementary probabilistic/causal substrate:

> **What can be inferred from uncertain evidence, what may cause what, how uncertainty propagates, and how decisions should consume explicit uncertainty/risk information?**
:::