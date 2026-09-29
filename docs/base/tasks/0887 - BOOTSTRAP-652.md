Tiếp tục với **BOOTSTRAP-652** — lớp quyết định/ tối ưu hóa tổng quát của Axiom, làm cầu nối giữa AI Agent, Workflow, Scheduler, Distributed Runtime và các hệ thống ML/Knowledge/Simulation.

:::writing{variant="document" id="58321" title="BOOTSTRAP-652 — Native AI Planning, Decision Optimization, Constraint Solving, Search-Based Reasoning, Scheduling Intelligence & Decision Runtime 5.0"}
# BOOTSTRAP-652
## Native AI Planning, Decision Optimization, Constraint Solving, Search-Based Reasoning, Scheduling Intelligence & Decision Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Decision & Optimization Plane  
**Priority:** Core AI Runtime / High-Level Native Runtime  
**Depends on:** BOOTSTRAP-600..651  
**Primary dependencies:** 629, 635, 636, 639, 641, 642, 643, 644, 645, 646, 648, 651

---

# 1. Purpose

BOOTSTRAP-652 defines Axiom's native decision intelligence runtime.

It provides a unified abstraction for:

- planning;
- constraint solving;
- combinatorial optimization;
- mathematical optimization;
- search;
- scheduling;
- resource allocation;
- assignment;
- matching;
- routing;
- sequencing;
- packing;
- multi-objective optimization;
- decision-making under uncertainty;
- heuristic optimization;
- exact optimization;
- incremental decision solving;
- replanning;
- plan validation;
- decision explanation.

The runtime must allow Axiom programs and AI agents to express:

```text
What can I do?
What must be true?
What should I optimize?
What resources are available?
What actions are possible?
What sequence should be executed?
What constraints must never be violated?
What is the best feasible solution under the declared objective?
```

without requiring a specific third-party solver.

---

# 2. Architectural Position

652 sits between high-level AI/application systems and execution runtimes.

```text
                         AI / APPLICATION
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
          Agent              Workflow          Distributed
           644                 629               Runtime
            │                   │                   │
            └───────────────────┼───────────────────┘
                                │
                         DECISION REQUEST
                                │
                         ┌──────▼──────┐
                         │    652     │
                         │  Decision  │
                         │   Engine   │
                         └──────┬──────┘
                                │
          ┌─────────────┬───────┼────────┬─────────────┐
          │             │       │        │             │
      Planning      Constraints Search Optimization Scheduling
          │             │       │        │             │
          └─────────────┴───────┼────────┴─────────────┘
                                │
                         SOLUTION / PLAN
                                │
                  ┌─────────────┼─────────────┐
                  │             │             │
               Validate      Explain       Execute
                  │             │             │
                  └─────────────┼─────────────┘
                                │
                         Native Runtime
```

652 does **not** execute arbitrary authority.

It produces decisions.

Existing runtimes remain responsible for execution.

---

# 3. Non-Goals

652 MUST NOT become:

1. the workflow runtime;
2. the cluster scheduler itself;
3. the authorization engine;
4. the policy engine;
5. the ML training runtime;
6. the database;
7. the knowledge graph;
8. the agent runtime;
9. the simulation runtime.

Instead:

```text
629 = workflow execution
635 = distributed coordination
639 = policy
643 = ML
644 = agents
645 = knowledge graph
648 = simulation
651 = personalization
652 = decision computation
```

---

# 4. Core Design Principles

## 4.1 Declarative first

A decision problem should describe:

```text
variables
domains
constraints
objectives
resources
actions
goals
```

rather than prescribing the algorithm.

Example:

```axiom
@decision ProductionPlan {
    variable units: Int[0..10000]

    constraint units <= capacity

    objective maximize profit
}
```

---

## 4.2 Solver independence

Application code MUST NOT depend directly on:

- Gurobi;
- CPLEX;
- OR-Tools;
- Z3;
- MiniZinc;
- SAT libraries;
- external optimization libraries.

Those may be provider implementations.

---

## 4.3 Exactness must be explicit

The runtime distinguishes:

```text
Optimal
Feasible
Suboptimal
Heuristic
Partial
Unknown
Timeout
Infeasible
Cancelled
```

A heuristic solution MUST NOT be reported as proven optimal.

---

## 4.4 Constraints are first-class

Constraints are represented explicitly and inspectably.

```text
Constraint
 ├── identity
 ├── expression
 ├── hardness
 ├── priority
 ├── scope
 ├── provenance
 └── evaluation state
```

---

# 5. Core Data Model

## 5.1 DecisionProblem

```axiom
struct DecisionProblem {
    id: ProblemId
    revision: u64
    variables: VariableSet
    constraints: ConstraintSet
    objectives: ObjectiveSet
    context: DecisionContext
}
```

---

# 6. Decision Variables

```axiom
struct DecisionVariable {
    id: VariableId
    name: String
    domain: VariableDomain
    default: Optional<Value>
}
```

Supported domains:

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
Tensor
Vector
```

The implementation may lower complex domains into primitive variables.

---

# 7. Variable Domains

## 7.1 Numeric

```axiom
Int[0..100]
Real[0.0..1.0]
```

## 7.2 Enumeration

```axiom
enum Machine {
    A
    B
    C
}
```

## 7.3 Set

```axiom
Set<Product>
```

## 7.4 Sequence

```axiom
Sequence<Job>
```

## 7.5 Interval

```axiom
Interval {
    start: Time
    end: Time
}
```

---

# 8. Expressions

The decision engine defines a typed expression IR.

```text
Constant
Variable
Parameter
Add
Sub
Mul
Div
Mod
Min
Max
Abs
Neg
And
Or
Not
Eq
Ne
Lt
Le
Gt
Ge
If
Sum
Product
Count
All
Any
SetContains
Element
Lookup
```

Expressions MUST be side-effect free.

---

# 9. Constraints

```axiom
struct Constraint {
    id: ConstraintId
    expression: BoolExpression
    hardness: ConstraintHardness
    priority: i32
    weight: Real
}
```

Constraint hardness:

```axiom
enum ConstraintHardness {
    Hard
    Soft
}
```

---

# 10. Constraint Categories

652 supports:

```text
Equality
Inequality
Bounds
AllDifferent
Cardinality
Membership
Implication
Logical
Precedence
Temporal
Capacity
Assignment
Flow
Routing
Spatial
Resource
Sequence
Set
Conditional
Nonlinear
CustomProvider
```

---

# 11. Hard Constraints

A hard constraint MUST be satisfied for a solution to be feasible.

```axiom
@hard
constraint cpu <= 64
```

The engine MUST reject a solution violating any hard constraint.

---

# 12. Soft Constraints

Soft constraints represent preferences.

```axiom
@soft(weight = 10)
constraint preferred_machine == machine
```

Soft violations become objective penalties.

A solution may therefore be:

```text
feasible
but imperfect
```

without being incorrectly classified as infeasible.

---

# 13. Constraint Priority

Optional priority levels:

```text
critical
high
normal
low
```

Priority MUST NOT silently override hard/soft semantics.

---

# 14. Objectives

```axiom
struct Objective {
    id: ObjectiveId
    direction: ObjectiveDirection
    expression: NumericExpression
    priority: i32
}
```

Directions:

```axiom
enum ObjectiveDirection {
    Minimize
    Maximize
}
```

---

# 15. Objective Strategies

Supported strategies:

```text
Single
WeightedSum
Lexicographic
Hierarchical
Pareto
EpsilonConstraint
GoalProgramming
```

---

# 16. Weighted Optimization

Example:

```axiom
objective maximize
    profit * 0.7
    - latency * 0.2
    - cost * 0.1
```

Weights MUST be explicitly represented.

The runtime MUST NOT infer semantic importance from arbitrary numeric magnitude.

---

# 17. Lexicographic Optimization

Example:

```axiom
@lexicographic
objective minimize cost priority 1
objective minimize latency priority 2
objective maximize quality priority 3
```

The engine first optimizes priority 1, then preserves its optimum while optimizing priority 2.

---

# 18. Pareto Optimization

The runtime may return:

```text
ParetoFrontier<Solution>
```

A Pareto solution MUST NOT be converted automatically into a single "best" solution without a declared selection rule.

---

# 19. DecisionSolution

```axiom
struct DecisionSolution {
    status: SolutionStatus
    assignments: AssignmentSet
    objective_values: ObjectiveValueSet
    constraint_state: ConstraintState
    statistics: SolveStatistics
}
```

---

# 20. Solution Status

```axiom
enum SolutionStatus {
    Optimal
    Feasible
    Suboptimal
    Heuristic
    Partial
    Infeasible
    Unknown
    Timeout
    Cancelled
    Error
}
```

---

# 21. Optimality Metadata

```axiom
struct Optimality {
    proven: bool
    gap: Optional<Real>
    bound: Optional<Real>
    certificate: Optional<OptimalityCertificate>
}
```

The runtime MUST distinguish:

```text
proven optimal
```

from:

```text
best solution found so far
```

---

# 22. Solver Architecture

```text
DecisionProblem
      │
      ▼
Canonical IR
      │
      ├── Propagation Solver
      ├── SAT/SMT Provider
      ├── MILP Provider
      ├── CP Provider
      ├── Dynamic Programming
      ├── Branch & Bound
      ├── Search Engine
      ├── Local Search
      ├── Heuristic Engine
      └── External Solver Provider
```

---

# 23. Native Solver

Axiom SHOULD ship with a compact native solver covering:

```text
constraint propagation
branch-and-bound
enumeration
dynamic programming
best-first search
A*
greedy search
local search
basic scheduling
basic assignment
basic matching
```

This establishes a dependency-free baseline.

---

# 24. External Solver Boundary

External providers may implement:

```axiom
trait DecisionSolverProvider {
    solve(problem: DecisionProblem,
          options: SolveOptions)
        -> DecisionSolution
}
```

Providers MUST NOT become mandatory runtime dependencies.

---

# 25. Search Engine

Core search abstraction:

```axiom
struct SearchState {
    state: State
    cost: Real
    depth: u32
}
```

```axiom
trait SearchProblem {
    initial() -> SearchState
    expand(state: SearchState) -> Sequence<SearchState>
    goal(state: SearchState) -> bool
}
```

---

# 26. Search Strategies

Supported:

```text
DepthFirst
BreadthFirst
UniformCost
BestFirst
A*
IDA*
BeamSearch
Bidirectional
BranchAndBound
IterativeDeepening
```

---

# 27. Heuristics

```axiom
trait Heuristic {
    estimate(state: SearchState) -> Real
}
```

Metadata:

```axiom
struct HeuristicInfo {
    admissible: bool
    consistent: bool
    deterministic: bool
}
```

The engine MUST NOT assume admissibility unless declared or proven.

---

# 28. Search Frontier

```axiom
struct SearchFrontier {
    open: FrontierCollection
    closed: Optional<VisitedSet>
}
```

Implementations may use:

```text
binary heap
indexed heap
bucket queue
radix queue
hash table
specialized priority queue
```

according to problem characteristics.

---

# 29. Transposition Tables

Search engines SHOULD support state deduplication.

```axiom
struct StateKey {
    hash: u128
    revision: u64
}
```

Hash collisions MUST NOT silently imply state equality unless the selected mode explicitly permits probabilistic hashing.

---

# 30. Constraint Propagation

The native solver SHOULD implement propagation for:

```text
bounds
equality
inequality
all-different
cardinality
linear relations
precedence
capacity
boolean implications
```

Propagation should occur before expensive branching whenever possible.

---

# 31. Branch and Bound

```text
Node
 ├── partial assignment
 ├── lower bound
 ├── upper bound
 └── feasibility state
```

Branches whose bound cannot improve the incumbent MAY be pruned.

---

# 32. Dynamic Programming

652 supports reusable subproblem states.

```axiom
@dynamic
problem Knapsack { ... }
```

The runtime may automatically detect repeated states when safe.

---

# 33. Local Search

Supported primitives:

```text
Neighborhood
Move
Evaluate
Apply
Undo
```

Strategies:

```text
HillClimbing
SimulatedAnnealing
TabuSearch
RandomRestart
VariableNeighborhood
```

---

# 34. Genetic / Evolutionary Boundary

Evolutionary algorithms are provider-level capabilities.

```axiom
trait EvolutionSolverProvider {
    optimize(...)
}
```

They MUST NOT be required by the core runtime.

---

# 35. Scheduling Model

```axiom
struct ScheduleTask {
    id: TaskId
    duration: Duration
    release: Optional<Time>
    deadline: Optional<Time>
    resource_requirements: ResourceRequirementSet
}
```

---

# 36. Scheduling Constraints

Supported:

```text
precedence
release time
deadline
capacity
machine eligibility
non-overlap
setup time
changeover
maintenance window
calendar
shift
resource availability
preemption
non-preemption
```

---

# 37. Resource Model

```axiom
struct DecisionResource {
    id: ResourceId
    capacity: Quantity
    calendar: ResourceCalendar
    attributes: AttributeSet
}
```

Resources may represent:

```text
CPU
GPU
RAM
storage
network bandwidth
worker
machine
vehicle
human operator
service instance
cluster node
budget
time
```

---

# 38. Resource Allocation

652 may optimize allocation across resources from:

- 606 Resource Governor;
- 629 workflow workers;
- 630 distributed compute;
- 635 cluster scheduler;
- 631 services;
- 636 deployment;
- 651 personalization.

652 produces an allocation proposal.

The consuming runtime remains responsible for enforcing actual resource limits.

---

# 39. Assignment

Generic assignment:

```axiom
@assignment
assign Worker -> Job
```

Supported objectives:

```text
minimize cost
minimize distance
maximize utilization
maximize compatibility
balance workload
minimize lateness
```

---

# 40. Matching

Native primitives:

```text
BipartiteMatching
WeightedMatching
MaximumMatching
MinimumCostMatching
```

Stable matching may be exposed through a specialized provider.

---

# 41. Flow Optimization

The runtime supports graph flow abstractions:

```text
MaxFlow
MinCostFlow
CapacityFlow
MultiCommodityFlow
```

The latter may use an external provider.

---

# 42. Routing

```axiom
struct RoutingProblem {
    graph: Graph
    origin: Node
    destinations: Sequence<Node>
    constraints: RoutingConstraintSet
}
```

Supported:

```text
shortest path
multi-destination routing
vehicle routing boundary
time-window routing
capacity routing
multi-route optimization
```

---

# 43. Graph Integration

645 provides graph data.

652 provides decision computation.

```text
645 Graph
   ↓
652 Route Optimization
   ↓
DecisionSolution
```

---

# 44. Planning

Planning models a transition from an initial state toward a goal.

```axiom
struct PlanningProblem {
    initial: State
    goal: GoalExpression
    actions: ActionSchemaSet
}
```

---

# 45. Action Schema

```axiom
struct ActionSchema {
    id: ActionId
    parameters: ParameterSet
    preconditions: ExpressionSet
    effects: EffectSet
    cost: Optional<Expression>
}
```

---

# 46. Plan

```axiom
struct Plan {
    actions: Sequence<PlanStep>
    cost: NumericValue
    validity: PlanValidity
}
```

---

# 47. Plan Validation

A plan MUST be independently replayable.

Validation checks:

```text
initial state
preconditions
effects
resource constraints
temporal constraints
goal satisfaction
authorization boundary
```

---

# 48. Temporal Planning

The runtime supports:

```text
before
after
during
overlap
starts
finishes
deadline
duration
```

Temporal planning MAY use interval variables internally.

---

# 49. HTN Boundary

Hierarchical Task Networks may be implemented as an optional planning provider.

The core representation remains compatible with hierarchical task decomposition without requiring HTN algorithms.

---

# 50. Uncertainty

Decision inputs may contain uncertain values.

```axiom
struct UncertainValue<T> {
    nominal: T
    distribution: Optional<Distribution>
    scenarios: Optional<ScenarioSet>
}
```

652 MUST preserve the distinction between:

```text
known value
estimated value
predicted value
uncertain value
unknown value
```

---

# 51. Stochastic Optimization

Optional capabilities:

```text
scenario optimization
Monte Carlo evaluation
stochastic programming
robust optimization
chance constraints
```

Simulation execution is delegated to 648.

---

# 52. Robust Optimization

A robust decision may optimize against a declared uncertainty set.

```axiom
@robust
objective minimize worst_case_cost
```

The uncertainty model MUST be explicit.

---

# 53. Chance Constraints

```axiom
@chance(probability >= 0.99)
constraint latency <= deadline
```

The runtime MUST record:

```text
assumption
probability model
sample count / analytical method
confidence metadata
```

---

# 54. Receding-Horizon Decision

652 supports incremental replanning.

```text
observe
   ↓
solve horizon
   ↓
execute first portion
   ↓
observe again
   ↓
re-solve
```

This is useful for:

```text
robotics
dynamic scheduling
resource allocation
network routing
autonomous agents
```

---

# 55. Warm Start

```axiom
struct WarmStart {
    solution: DecisionSolution
    source_revision: u64
}
```

A previous solution MAY seed a new solve.

Warm starts MUST NOT bypass validation.

---

# 56. Incremental Solving

A problem may be modified by delta.

```axiom
struct ProblemDelta {
    added_variables
    removed_variables
    changed_domains
    added_constraints
    removed_constraints
    changed_objectives
}
```

The solver may reuse prior internal state.

---

# 57. Checkpointing

Long-running optimization supports:

```axiom
struct SolveCheckpoint {
    problem_revision: u64
    solver_revision: u64
    incumbent: Optional<DecisionSolution>
    search_state: Optional<OpaqueSolverState>
}
```

Checkpoint contents must be versioned.

---

# 58. Solve Budget

```axiom
struct SolveBudget {
    max_time: Optional<Duration>
    max_cpu: Optional<Quantity>
    max_memory: Optional<Quantity>
    max_nodes: Optional<u64>
    max_iterations: Optional<u64>
    max_solutions: Optional<u64>
    max_objective_evaluations: Optional<u64>
}
```

---

# 59. Cancellation

Every solve operation must support cancellation.

```axiom
solve(problem, token)
```

Cancellation must produce:

```text
Cancelled
```

rather than silently returning an apparently complete result.

---

# 60. Parallel Search

652 may parallelize:

```text
branch exploration
population evaluation
candidate evaluation
scenario evaluation
objective evaluation
```

Parallelism MUST respect deterministic mode when requested.

---

# 61. Deterministic Mode

```axiom
SolveOptions {
    deterministic: true
    seed: 42
}
```

Deterministic mode requires:

- stable variable ordering;
- stable constraint ordering;
- deterministic tie-breaking;
- explicit random seed;
- deterministic reduction where supported.

---

# 62. Decision Context

```axiom
struct DecisionContext {
    timestamp: Time
    identity: Optional<Identity>
    policy_revision: Optional<u64>
    profile_revision: Optional<u64>
    model_revision: Optional<u64>
    data_revision: Optional<u64>
}
```

The context makes the decision reproducible.

---

# 63. Integration with 651

Personalization may contribute:

```text
preferences
weights
candidate scores
constraints
context
utility functions
```

But:

```text
preference != authorization
```

and:

```text
personalization != policy
```

---

# 64. Integration with 639

639 evaluates policy.

652 solves decisions subject to policy constraints.

```text
Decision
   ↓
639 Policy
   ↓
allowed problem
   ↓
652 Solve
```

652 MUST NOT manufacture permissions.

---

# 65. Integration with 643

ML predictions may be used as decision inputs.

Example:

```text
predicted demand
predicted latency
predicted failure probability
predicted cost
```

The prediction MUST remain identifiable as a prediction.

The optimizer MUST NOT silently convert it into ground truth.

---

# 66. Integration with 646

646 evaluates:

```text
solver quality
planner quality
decision stability
constraint correctness
regression
fairness-related metrics where applicable
robustness
```

---

# 67. Integration with 648

648 can generate scenarios:

```text
scenario → solve → simulate → evaluate → revise
```

This enables closed-loop decision testing.

---

# 68. Decision Explanation

652 exposes structured explanation, not hidden reasoning traces.

```axiom
struct DecisionExplanation {
    selected_assignments
    objective_values
    satisfied_constraints
    violated_soft_constraints
    binding_constraints
    solver
    solver_version
    optimality
    search_statistics
}
```

---

# 69. Binding Constraints

The runtime SHOULD identify constraints that materially limit the solution.

Example:

```text
capacity constraint:
GPU <= 8
```

may be marked:

```text
binding = true
```

This is useful for debugging and planning.

---

# 70. Infeasibility Analysis

If no feasible solution exists, the runtime SHOULD expose:

```text
conflicting constraints
relaxed constraints
unsatisfied goals
```

where the solver supports such analysis.

---

# 71. Infeasibility Certificate

```axiom
struct InfeasibilityCertificate {
    proof_type: String
    constraints: ConstraintIdSet
    provider: SolverProviderId
}
```

A certificate MUST identify its provenance.

---

# 72. Soft-Constraint Relaxation

The engine may calculate:

```text
minimum relaxation
```

for infeasible models.

Example:

```text
capacity <= 100
required >= 120
```

Possible diagnostic:

```text
capacity must increase by at least 20
```

Such diagnostics must be marked as solver-derived.

---

# 73. Decision Provenance

Every solution records:

```text
problem identity
problem revision
input revisions
constraint revision
objective revision
solver/provider
solver version
configuration
seed
start/end time
status
```

---

# 74. Audit Record

```axiom
struct DecisionAudit {
    request_id
    problem_id
    problem_revision
    context
    solver
    result
    provenance
}
```

Integrates with 602 and 640.

---

# 75. Security

Decision models are untrusted input.

The runtime MUST prevent:

```text
arbitrary native code execution
unsafe provider loading
unauthorized data access
unbounded resource consumption
```

Custom solver providers require explicit capability authorization.

---

# 76. Resource Governance

All solves are subject to 606.

```text
memory quota
CPU quota
GPU quota
time quota
parallelism quota
```

A solver MUST NOT bypass the resource governor.

---

# 77. Distributed Solving

Large problems may be distributed.

```text
Coordinator
    │
 ┌──┼────┬────┐
 │  │    │    │
 W1 W2   W3   W4
 │  │    │    │
search branches
```

630/635 provide worker and cluster execution.

652 defines the decision semantics.

---

# 78. Distributed Determinism

Distributed solving may produce different search orders.

If deterministic mode is required, the provider must expose an appropriate deterministic strategy.

---

# 79. Solution Cache

Solutions may be cached using:

```text
problem revision
context revision
solver revision
objective revision
constraint revision
configuration
```

A stale solution MUST NOT be treated as current.

---

# 80. Decision Snapshot

```axiom
struct DecisionSnapshot {
    problem
    context
    solution
    provenance
}
```

Snapshots integrate with 600.

---

# 81. Compiler Representation

The compiler lowers decision declarations into an intermediate representation:

```text
AX-DIR
 ├── variables
 ├── domains
 ├── expressions
 ├── constraints
 ├── objectives
 ├── actions
 ├── resources
 ├── search hints
 └── solver requirements
```

---

# 82. Decision IR

Example:

```text
DECISION_BEGIN
VARIABLE x INT 0 100
CONSTRAINT x <= capacity
OBJECTIVE MAX profit(x)
DECISION_END
```

The exact binary encoding is compiler-defined.

---

# 83. Compiler Optimization

The compiler may:

- constant-fold expressions;
- remove unreachable constraints;
- simplify redundant bounds;
- detect fixed variables;
- precompute domains;
- specialize expressions;
- flatten small models;
- select specialized solvers.

---

# 84. Static Decision Analysis

The compiler SHOULD detect:

```text
contradictory constant constraints
empty domains
unused variables
duplicate constraints
dominated objectives
impossible bounds
```

---

# 85. Compile-Time Solving

Small static problems MAY be solved during compilation.

Example:

```axiom
const optimal = decision.solve(...)
```

The compiler may materialize the result as a constant if:

```text
problem is deterministic
inputs are compile-time known
solver result is proven valid
```

---

# 86. Runtime Solving

Dynamic inputs produce runtime decision requests.

```axiom
result = Decision.solve(problem, context)
```

---

# 87. Native Syntax

Suggested syntax:

```axiom
@decision Production {
    variable workers: Int[1..100]
    variable units: Int[0..10000]

    constraint units <= workers * 100
    constraint workers <= available_workers

    objective maximize profit(units, workers)
}
```

---

# 88. Scheduling Syntax

```axiom
@schedule FactoryPlan {
    task A duration 10m
    task B duration 20m
    task C duration 15m

    constraint B after A
    constraint C after A

    resource machine: capacity 1

    objective minimize makespan
}
```

---

# 89. Planning Syntax

```axiom
@plan Delivery {
    initial warehouse.state

    goal delivered(order)

    action Move(from, to) {
        requires vehicle_at(from)
        effects vehicle_at(to)
    }
}
```

---

# 90. Route Syntax

```axiom
@route DeliveryRoute {
    graph road_network
    start warehouse
    destinations customers

    constraint vehicle_capacity <= capacity

    objective minimize distance
}
```

---

# 91. Assignment Syntax

```axiom
@assignment Staff {
    assign employee -> task

    constraint employee.available(task)
    constraint task.requires(employee.skills)

    objective minimize total_cost
}
```

---

# 92. Search Syntax

```axiom
@search Path {
    initial start

    expand(state) {
        state.neighbors()
    }

    goal(state) {
        state.node == destination
    }

    heuristic(state) {
        distance(state.node, destination)
    }
}
```

---

# 93. Solver Selection

The runtime may automatically choose:

```text
Constraint Solver
Search Solver
MILP
CP
Dynamic Programming
Branch-and-Bound
Heuristic
```

based on model characteristics.

Selection must be inspectable.

---

# 94. Explicit Solver Selection

```axiom
@solver("native.branch_bound")
```

or:

```axiom
@solver(auto)
```

---

# 95. Solver Capability Negotiation

Each solver advertises:

```text
integer variables
real variables
nonlinear expressions
boolean constraints
temporal constraints
multi-objective
incremental solving
warm starts
parallel solving
proof certificates
```

The engine validates compatibility before execution.

---

# 96. Unsupported Model Handling

If no solver supports the model:

```text
Unsupported
```

must be returned explicitly.

The engine MUST NOT silently approximate unless approximation is explicitly permitted.

---

# 97. Approximation Mode

```axiom
SolveOptions {
    allow_approximation: true
}
```

Approximate solutions must report:

```text
approximate = true
```

and their provenance.

---

# 98. Search Budget

Search statistics:

```axiom
struct SearchStatistics {
    nodes_expanded
    nodes_pruned
    states_generated
    states_revisited
    frontier_peak
    elapsed
}
```

---

# 99. Optimization Statistics

```axiom
struct OptimizationStatistics {
    incumbent
    bound
    gap
    objective_evaluations
    iterations
    improvements
}
```

---

# 100. Scheduling Statistics

```axiom
struct ScheduleStatistics {
    makespan
    utilization
    lateness
    idle_time
    resource_conflicts
}
```

---

# 101. Decision Metrics

652 supports domain-neutral metrics:

```text
cost
utility
latency
distance
throughput
quality
risk
resource utilization
constraint violation
regret
stability
```

Applications may define custom metrics.

---

# 102. Decision Stability

A decision system may compare solutions across revisions.

```text
solution_delta
assignment_delta
objective_delta
constraint_delta
```

This allows detection of unstable plans.

---

# 103. Hysteresis

For dynamic systems, optional hysteresis prevents unnecessary replanning.

```axiom
@hysteresis(threshold = 0.05)
```

A new solution may only replace the current one if improvement exceeds the declared threshold.

---

# 104. Decision Churn

The runtime SHOULD expose:

```text
changed assignments
changed resources
changed schedule slots
changed routes
```

This is especially important for distributed and production systems.

---

# 105. Multi-Agent Decisions

644 may submit shared decision problems.

```text
Agent A
Agent B
Agent C
    ↓
Shared Decision Problem
    ↓
652
```

Agent identity remains governed by 627/603.

---

# 106. Negotiated Objectives

Multiple agents may contribute objectives.

The aggregation rule MUST be explicit:

```text
weighted
lexicographic
Pareto
negotiated
constraint-based
```

652 MUST NOT silently decide whose objective has greater authority.

---

# 107. Personalization-Aware Planning

651 may provide preferences:

```text
preferred time
preferred resource
preferred route
preferred workload
```

These become:

```text
soft constraints
objective terms
tie-breakers
```

unless explicitly declared hard constraints.

---

# 108. Policy-Aware Planning

639 constraints may become hard constraints.

Example:

```text
security policy
↓
hard constraint
↓
652
```

Policy semantics remain owned by 639.

---

# 109. AI Agent Tool Interface

644 exposes:

```axiom
decision.solve()
decision.plan()
decision.optimize()
decision.schedule()
decision.assign()
decision.route()
decision.validate()
decision.explain()
```

Agent-generated models must still pass security and resource checks.

---

# 110. Agent Safety Boundary

An agent may request:

```text
"find a plan"
```

but cannot automatically turn the resulting plan into privileged execution.

Execution remains separately authorized.

---

# 111. Simulation Loop

652 + 648:

```text
Generate Scenario
       ↓
Solve
       ↓
Simulate
       ↓
Measure
       ↓
Modify Model
       ↓
Solve Again
```

This supports decision robustness testing.

---

# 112. ML + Optimization Loop

643 can provide predictions:

```text
demand_model
failure_model
latency_model
```

652 consumes them:

```text
prediction
   ↓
optimization
   ↓
decision
```

The provenance of predictions must remain attached.

---

# 113. Search + Knowledge Graph

645 provides:

```text
graph topology
relationships
candidate paths
semantic constraints
```

652 performs:

```text
path selection
assignment
planning
optimization
```

---

# 114. Analytics Integration

642 may provide:

```text
aggregates
historical statistics
cost distributions
capacity measurements
```

652 uses them as decision inputs.

Point-in-time correctness from 642 remains mandatory.

---

# 115. Decision Evaluation

646 can evaluate:

```text
objective quality
constraint correctness
robustness
runtime cost
solution reproducibility
regression
```

---

# 116. Benchmarking

CLI:

```text
axiom decision benchmark
```

Measures:

```text
solve time
memory
nodes
iterations
objective quality
gap
throughput
```

---

# 117. Validation CLI

```text
axiom decision validate model.axdecision
```

Checks:

```text
syntax
domains
constraints
objectives
solver compatibility
security metadata
```

---

# 118. Solve CLI

```text
axiom decision solve model.axdecision
```

---

# 119. Explain CLI

```text
axiom decision explain solution.axsolution
```

---

# 120. Schedule CLI

```text
axiom decision schedule factory.axschedule
```

---

# 121. Route CLI

```text
axiom decision route delivery.axroute
```

---

# 122. Solver Inspection

```text
axiom decision solver list
axiom decision solver inspect native.branch_bound
```

---

# 123. Generated Metadata

Compiler/runtime may emit:

```text
.axdecision
.axconstraint
.axobjective
.axplan
.axschedule
.axassignment
.axroute
.axsearch
.axsolver
.axsolution
.axdecisionlog
.axdecisionmeta
```

These files are designed to be machine-readable by AI agents.

---

# 124. AI Metadata

Generated metadata should contain:

```text
problem schema
variable descriptions
constraint descriptions
objective descriptions
solver capabilities
solution semantics
provenance
dependencies
validation state
```

---

# 125. Memory Layout

The native runtime should use compact structures.

Hot solver data should favor:

```text
contiguous arrays
index-based references
compact IDs
struct-of-arrays where beneficial
arena allocation
reusable buffers
```

This aligns with Axiom's high-performance memory architecture.

---

# 126. Pointer Policy

The public decision API SHOULD avoid exposing raw pointers.

Internally, solver implementations may use:

```text
indices
handles
offsets
arena references
```

instead of pervasive pointer ownership semantics.

---

# 127. Allocation Policy

Solver allocations should support:

```text
arena
scratch
persistent model storage
checkpoint storage
result storage
```

Short-lived search nodes SHOULD use specialized allocators.

---

# 128. Zero-Copy Inputs

Where possible:

```text
tensor
vector
graph
dataset
feature
```

inputs should be referenced without copying.

Ownership/lifetime remains governed by the existing Axiom runtime model.

---

# 129. SIMD

Expression evaluation SHOULD support SIMD where profitable.

Candidates include:

```text
vector objective evaluation
batch constraints
population evaluation
scenario evaluation
heuristic evaluation
```

---

# 130. GPU Acceleration

GPU acceleration is optional.

Good candidates:

```text
population evaluation
Monte Carlo
large tensor objectives
parallel candidate scoring
scenario evaluation
```

Irregular branch-and-bound/search should remain CPU-capable.

---

# 131. CPU/GPU Scheduling

The engine may choose:

```text
CPU
GPU
hybrid
```

based on solver/provider capabilities and 606 resource budgets.

---

# 132. Numerical Semantics

Floating-point optimization must expose numerical policy.

```axiom
NumericalPolicy {
    tolerance
    feasibility_tolerance
    integrality_tolerance
    comparison_mode
}
```

---

# 133. Numerical Reproducibility

Solutions using floating-point arithmetic MUST record:

```text
numeric mode
precision
tolerances
hardware/provider
```

where reproducibility matters.

---

# 134. Constraint Tolerance

For real-valued constraints:

```text
x <= y + epsilon
```

the epsilon MUST be part of solver configuration or model semantics.

It must not be hidden.

---

# 135. Integer Safety

Integer overflow in model expressions MUST be detected or handled according to Axiom's integer semantics.

Silent wraparound inside an optimization model is prohibited unless explicitly requested by the language semantics.

---

# 136. Model Versioning

```axiom
ProblemRevision
ConstraintRevision
ObjectiveRevision
SolverRevision
```

must be independently trackable.

---

# 137. Reproducible Decision

A solution can be reproduced only if the necessary inputs are retained:

```text
model
data
context
solver
configuration
seed
provider version
```

The runtime SHOULD provide:

```axiom
decision.replay(snapshot)
```

---

# 138. Decision Replay

Replay compares:

```text
status
assignments
objective values
constraint state
solver statistics
```

and reports differences.

---

# 139. Failure Recovery

A long-running solve may recover from:

```text
process restart
worker failure
network interruption
resource preemption
```

using 600 checkpoints and 630 distributed execution.

---

# 140. Partial Solutions

When allowed, timeout may return the best validated solution found.

Example:

```text
status = Partial
optimality.proven = false
```

The solution MUST clearly indicate its non-optimal status.

---

# 141. Anytime Algorithms

652 SHOULD support anytime optimization.

```text
start
 ↓
feasible solution
 ↓
better solution
 ↓
better solution
 ↓
timeout
 ↓
return best validated solution
```

---

# 142. Objective Monotonicity

Where mathematically applicable, the solver records whether the incumbent objective improves monotonically.

---

# 143. Search Restart

Providers may restart search when beneficial.

Restart policy must be recorded for reproducibility.

---

# 144. Randomized Algorithms

Randomized solvers require:

```text
seed
random provider
algorithm version
```

in provenance.

---

# 145. Decision Policy vs Decision Optimization

A policy:

```text
if condition then action
```

belongs primarily to 639.

An optimization model:

```text
choose x maximizing objective subject to constraints
```

belongs to 652.

Both may be combined.

---

# 146. Planning vs Workflow

Workflow:

```text
execute predefined process
```

Planning:

```text
compute process dynamically
```

629 executes the resulting workflow.

652 generates the plan.

---

# 147. Scheduling vs Distributed Scheduler

652:

```text
computes candidate schedule
```

635:

```text
maintains cluster-wide scheduling/coordination
```

A 635 implementation may use 652 internally.

---

# 148. Recommendation vs Optimization

651 may rank recommendations.

652 may optimize a global allocation.

Example:

```text
651:
rank products for user

652:
allocate inventory among regions
```

---

# 149. Decision Composition

Solutions may become inputs to another decision problem.

```text
Decision A
   ↓
Decision B
   ↓
Decision C
```

Composition must preserve provenance.

---

# 150. Nested Optimization

Nested solves are allowed only when resource budgets permit.

The runtime SHOULD detect excessive recursion.

---

# 151. Decision Graph

Complex decision pipelines can be represented as:

```text
DecisionGraph {
    nodes
    edges
    dependencies
}
```

This integrates with 624 automation and 629 workflows.

---

# 152. Constraint Templates

Reusable constraints:

```axiom
constraint capacity_limit(resource, demand)
constraint no_overlap(tasks)
constraint precedence(a, b)
constraint assignment_valid(worker, task)
```

Templates must expand into explicit constraints.

---

# 153. Objective Templates

Reusable objectives:

```axiom
objective minimize_cost(...)
objective minimize_latency(...)
objective maximize_utilization(...)
objective minimize_makespan(...)
```

---

# 154. Domain Libraries

652 SHOULD provide reusable native domain models:

```text
Scheduling
Routing
Assignment
Packing
ResourceAllocation
Matching
Planning
Portfolio
Flow
```

These are model-building libraries, not separate runtimes.

---

# 155. Packing

Support:

```text
bin packing
knapsack
multi-dimensional packing
container loading
resource packing
```

---

# 156. Sequencing

Support:

```text
job sequencing
machine sequencing
batch ordering
priority ordering
setup minimization
```

---

# 157. Calendar Intelligence

Scheduling integrates:

```text
working hours
holidays
maintenance
time zones
availability windows
resource calendars
```

617 provides time/calendar semantics.

---

# 158. Multi-Time-Zone Decisions

All internal scheduling timestamps MUST use canonical time representation.

Display timezone is presentation metadata.

---

# 159. Fairness Constraints

Where an application requires fairness, it is modeled explicitly.

Examples:

```text
maximum workload disparity
minimum allocation
group constraints
rotation constraints
```

652 does not infer fairness criteria automatically.

---

# 160. Governance

Data classification and privacy rules from 640 propagate into:

```text
decision inputs
decision logs
solver traces
snapshots
explanations
```

Sensitive inputs MUST NOT leak through unrestricted diagnostics.

---

# 161. Explainability Boundary

The runtime exposes:

```text
what constraints were active
what objective values resulted
what assignments were selected
what solver was used
```

It does not expose hidden chain-of-thought.

---

# 162. Decision Confidence

The runtime MUST NOT invent confidence for deterministic optimization.

If uncertainty is meaningful, it should expose:

```text
objective gap
scenario robustness
probabilistic estimate
simulation statistics
```

with explicit provenance.

---

# 163. Regret

Optional evaluation metric:

```text
regret = selected_cost - reference_best_cost
```

The reference must be explicitly identified.

---

# 164. Counterfactual Analysis

The runtime may solve modified models:

```text
What if capacity increases?
What if resource disappears?
What if deadline changes?
```

Each counterfactual is a separate problem revision.

---

# 165. Sensitivity Analysis

Supported metadata:

```text
objective sensitivity
constraint sensitivity
resource shadow value
parameter impact
```

Provider-dependent features must be marked accordingly.

---

# 166. Shadow Prices

For supported mathematical solvers:

```axiom
struct ShadowValue {
    constraint: ConstraintId
    value: Real
}
```

Useful for resource planning.

---

# 167. What-If API

```axiom
decision.what_if(
    base_problem,
    modifications
)
```

returns comparable solutions.

---

# 168. Decision Comparison

```axiom
decision.compare(solution_a, solution_b)
```

produces:

```text
objective delta
assignment delta
constraint delta
resource delta
```

without declaring an overall winner.

---

# 169. Stability Testing

The runtime can perturb inputs:

```text
±1%
±5%
±10%
```

and measure solution changes.

---

# 170. Robustness Report

```axiom
struct RobustnessReport {
    scenarios
    feasible_ratio
    objective_distribution
    constraint_failures
    sensitivity
}
```

---

# 171. Scenario Management

648 owns scenario generation.

652 owns solving against scenarios.

---

# 172. Batch Solving

```axiom
decision.solve_many(problems)
```

may share:

```text
compiled model
solver state
memory
GPU buffers
```

where safe.

---

# 173. Vectorized Decision Evaluation

Multiple scenarios may be evaluated simultaneously.

This is especially useful for:

```text
Monte Carlo
forecast scenarios
simulation loops
hyperparameter search
```

---

# 174. Model Compilation

Large recurring decision models SHOULD be compiled once:

```text
source
 ↓
decision IR
 ↓
compiled model
 ↓
many solve requests
```

---

# 175. Solver Warm Cache

Compiled solver structures may be cached by:

```text
model hash
solver configuration
provider version
```

---

# 176. Content Addressing

Decision artifacts SHOULD support content-addressed identity.

This integrates with 613.

---

# 177. Artifact Signing

Production decision models and solver providers may be signed using 610.

---

# 178. Provider Trust

Solver providers declare:

```text
capabilities
version
permissions
resource requirements
trust level
```

---

# 179. Provider Isolation

Third-party providers SHOULD run behind an explicit provider boundary.

A malicious or faulty provider must not compromise the core runtime.

---

# 180. ABI

The native provider ABI should use stable handles rather than exposing compiler-private structures.

Example:

```text
AXDecisionProblemHandle
AXDecisionSolutionHandle
AXSolverHandle
```

---

# 181. FFI

External native solvers may be integrated through the existing Axiom FFI boundary.

The application still depends only on the abstract 652 API.

---

# 182. WASM

WASM profile supports:

```text
small native solver
constraint evaluation
search
planning
heuristics
```

Heavy external solvers remain optional.

---

# 183. Mobile

Mobile profiles prioritize:

```text
compact model
bounded search
low memory
incremental solving
deterministic execution
```

---

# 184. Embedded

Embedded profile excludes:

```text
distributed solver
large optimization providers
GPU provider
```

unless explicitly enabled.

---

# 185. Server

Server profile enables:

```text
parallel solving
distributed solving
large model caching
checkpointing
provider integration
```

---

# 186. AI Agent Profile

```text
AXDECISION_AGENT
```

enables:

```text
planning
search
constraint solving
tool-compatible decisions
explanation
replanning
```

---

# 187. Core Profiles

Recommended compiler profiles:

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

# 188. Compiler Annotations

Required annotations:

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
@chance
@hysteresis
@deterministic
```

---

# 189. Runtime API

Minimum API:

```axiom
Decision.solve()
Decision.validate()
Decision.explain()
Decision.compare()
Decision.replay()
Decision.what_if()

Planner.plan()
Planner.validate()

Scheduler.schedule()
Scheduler.validate()

Search.run()

Optimizer.optimize()
Optimizer.resume()
Optimizer.cancel()
```

---

# 190. Native Error Model

Errors include:

```text
InvalidModel
InvalidDomain
InvalidConstraint
InvalidObjective
UnsupportedModel
InfeasibleModel
ResourceLimit
Timeout
Cancelled
ProviderUnavailable
ProviderFailure
NumericalFailure
CheckpointFailure
SecurityViolation
```

---

# 191. Error Safety

Errors MUST NOT return partially initialized solutions as valid solutions.

---

# 192. Thread Safety

Decision models may be immutable and shared between concurrent solves.

Mutable solver state must be isolated per solve unless explicitly designed for shared use.

---

# 193. Reentrancy

A solver provider must document whether it supports:

```text
concurrent solve
nested solve
resume
cancel
checkpoint
```

---

# 194. Memory Safety

Solver implementations MUST obey Axiom's native memory model.

Temporary search state should have deterministic lifecycle.

---

# 195. No Mandatory GC

652 does not require garbage collection.

Large search structures should use:

```text
arena
pool
slab
reusable vector
```

allocation strategies.

---

# 196. No Mandatory Borrow Checker

The decision runtime must not require borrow-checker semantics.

Ownership is handled through Axiom's established runtime model.

---

# 197. Performance Goal

Native 652 should target:

```text
low allocation overhead
compact model representation
cache-friendly evaluation
specialized solver kernels
parallel evaluation
incremental reuse
```

---

# 198. Solver Selection Cost

Automatic solver selection itself must remain cheap relative to solving.

For recurring models, selection should be cached.

---

# 199. Model Complexity Estimation

The runtime SHOULD estimate:

```text
variable count
constraint count
domain size
graph size
search branching factor
estimated complexity
```

This helps select an appropriate solver.

---

# 200. Complexity Metadata

```axiom
struct ModelComplexity {
    variables
    constraints
    domain_cardinality
    estimated_branching
    nonlinear_terms
}
```

---

# 201. Constraint Graph

The compiler/runtime SHOULD construct a constraint dependency graph.

This enables:

```text
propagation
decomposition
parallel evaluation
diagnostics
solver selection
```

---

# 202. Decomposition

Independent components may be solved separately.

```text
Problem
 ├── Component A
 ├── Component B
 └── Component C
```

The runtime may combine independent solutions.

---

# 203. Connected Components

Variables connected only through independent constraints SHOULD be detected automatically.

---

# 204. Symmetry Breaking

Providers may add mathematically valid symmetry-breaking constraints.

Such generated constraints must be marked:

```text
generated = true
```

---

# 205. Redundant Constraints

Redundant constraints may improve propagation.

The solver must distinguish:

```text
user constraint
generated constraint
provider constraint
```

---

# 206. Constraint Provenance

```axiom
ConstraintOrigin {
    User
    Compiler
    Policy
    Template
    Provider
}
```

---

# 207. Objective Provenance

Likewise:

```axiom
ObjectiveOrigin {
    User
    Personalization
    Policy
    Template
    Provider
}
```

---

# 208. No Silent Objective Injection

651 or another subsystem MUST NOT silently inject an objective into a 652 model.

Injected objectives require explicit metadata.

---

# 209. No Silent Constraint Injection

Security/policy constraints may be mandatory, but they must remain inspectable in the effective model.

---

# 210. Effective Model

Before solving:

```axiom
effective_problem = compile(
    user_problem,
    policy_constraints,
    resource_constraints,
    context
)
```

The resulting effective model is auditable.

---

# 211. Decision Lifecycle

```text
CREATE
  ↓
COMPILE
  ↓
VALIDATE
  ↓
ENRICH
  ↓
SOLVE
  ↓
VALIDATE SOLUTION
  ↓
EXPLAIN
  ↓
SNAPSHOT
  ↓
EXECUTE
  ↓
OBSERVE
  ↓
REPLAN
```

---

# 212. Execution Boundary

652 ends at:

```text
validated decision
```

Execution belongs to the consuming runtime.

---

# 213. Feedback Loop

Execution results can return to:

```text
642 analytics
643 ML
646 evaluation
648 simulation
651 adaptation
```

and trigger another solve.

---

# 214. Autonomous Replanning

644 agents may request:

```text
observe → plan → execute → observe → replan
```

but execution permissions remain external.

---

# 215. Decision Ledger

Production deployments SHOULD retain:

```text
decision request
effective model hash
solution hash
execution result
```

for audit.

---

# 216. Decision Hash

```axiom
DecisionHash = hash(
    problem,
    context,
    constraints,
    objectives,
    solver_config
)
```

---

# 217. Solution Hash

```axiom
SolutionHash = hash(
    DecisionHash,
    assignments,
    objective_values
)
```

---

# 218. Integrity

Decision artifacts may be signed.

This allows downstream systems to verify:

```text
who produced the decision
which model produced it
whether it was modified
```

---

# 219. Governance Integration

640 may enforce:

```text
retention
residency
privacy
data classification
decision audit requirements
```

---

# 220. Observability Integration

602 records:

```text
solve latency
solver failures
timeouts
resource consumption
solution status
model sizes
```

---

# 221. Metrics

Recommended metrics:

```text
decision.solve.count
decision.solve.latency
decision.solve.timeout
decision.solve.infeasible
decision.solve.optimal
decision.solve.partial
decision.model.variables
decision.model.constraints
decision.search.nodes
decision.optimization.gap
```

---

# 222. Tracing

A decision trace:

```text
request
 → model compile
 → policy enrichment
 → solver selection
 → solve
 → validation
 → result
```

---

# 223. Logging

Decision logs MUST avoid dumping large models by default.

Use:

```text
model hash
summary
artifact reference
```

instead.

---

# 224. Diagnostics

Compiler diagnostics:

```text
AXD001 Empty domain
AXD002 Contradictory constraint
AXD003 Unsupported expression
AXD004 No compatible solver
AXD005 Invalid objective
AXD006 Numerical instability
AXD007 Unbounded objective
AXD008 Infeasible model
AXD009 Missing capability
AXD010 Resource budget exceeded
```

---

# 225. Unbounded Models

If the objective is unbounded:

```text
status = Unknown
reason = Unbounded
```

unless the solver has a stronger formal status.

---

# 226. Incomplete Models

Missing required declarations must fail validation.

---

# 227. Objective Direction

The compiler must never infer whether a numeric expression should be maximized or minimized.

Direction is mandatory.

---

# 228. Constraint Semantics

Boolean constraints evaluate to:

```text
true
false
unknown
```

where uncertainty is supported.

Unknown must not silently become true.

---

# 229. Three-Valued Diagnostics

For uncertain inputs:

```text
Satisfied
Violated
Undetermined
```

may be used during analysis.

Final feasibility depends on the declared uncertainty semantics.

---

# 230. Decision Contract

Every decision model defines:

```text
Inputs
Variables
Constraints
Objectives
Solver requirements
Output schema
Validation rules
```

---

# 231. Output Schema

Solutions must have a statically describable shape.

Example:

```axiom
DecisionResult<ProductionPlan>
```

---

# 232. Typed Decisions

Decision variables use Axiom types.

This enables compiler checks before the solver sees the model.

---

# 233. Units

Scheduling/resource models SHOULD support units:

```text
ms
s
kg
m
GB
GB/s
USD
```

Unit mismatches should be compiler errors where the type system can prove them.

---

# 234. Resource Quantities

Resource capacities should be represented with typed quantities rather than raw numbers.

---

# 235. Time Representation

Time values use the common Axiom time model from 617/611.

---

# 236. Graph Representation

Graph references use 645 graph primitives when available.

---

# 237. Tensor Objectives

643 tensor operations may appear inside provider-supported objective functions.

---

# 238. Automatic Differentiation Boundary

Gradient-based optimization may use 643 differentiation facilities.

652 owns the optimization problem semantics.

---

# 239. Differentiable Optimization

Optional provider:

```text
GradientDescent
Adam
L-BFGS
SQP
```

These are not mandatory for the core solver.

---

# 240. Mixed Optimization

A model may combine:

```text
discrete variables
continuous variables
neural predictions
logical constraints
```

through provider capabilities.

---

# 241. Black-Box Optimization

Optional provider boundary:

```text
BayesianOptimization
EvolutionaryOptimization
DerivativeFreeOptimization
```

---

# 242. Objective Evaluation API

```axiom
trait ObjectiveEvaluator {
    evaluate(solution) -> ObjectiveValueSet
}
```

---

# 243. Constraint Evaluator

```axiom
trait ConstraintEvaluator {
    evaluate(solution) -> ConstraintState
}
```

---

# 244. Independent Validation

The final solution SHOULD be validated by a separate validation path when feasible.

This protects against solver/provider bugs.

---

# 245. Solver Result Trust

A provider result is not automatically trusted.

652 verifies:

```text
assignments
domain validity
constraint validity
objective consistency
```

before returning a valid solution.

---

# 246. Provider Failure Isolation

A failed solver provider must not corrupt:

```text
model
cache
other solves
runtime
```

---

# 247. Solver Fallback

If configured:

```axiom
fallback = native
```

the runtime may fall back to the native solver when a provider fails.

Fallback must be recorded.

---

# 248. No Silent Fallback

Fallback cannot occur silently when result semantics may differ.

---

# 249. Result Equivalence

When multiple solvers produce solutions, the runtime can compare:

```text
feasibility
objective
assignments
```

but should not assume identical assignments when multiple optima exist.

---

# 250. Multiple Optima

A model may have many equally optimal solutions.

The runtime may expose:

```text
solution_count
alternative_solutions
```

where supported.

---

# 251. Tie-Breaking

Tie-breaking must be explicit.

Examples:

```text
minimize cost
then minimize latency
then stable ID
```

---

# 252. Stable Tie-Breaking

Stable IDs can provide reproducible selection among equivalent solutions.

---

# 253. Decision Diversity

For recommendation-like planning problems, multiple valid solutions can be requested.

```axiom
solve(k = 10)
```

---

# 254. Solution Pool

```axiom
struct SolutionPool {
    solutions
    diversity_metric
}
```

---

# 255. Alternative Plans

Agents can request several plans and evaluate them separately.

---

# 256. Plan Ranking

652 may rank plans according to explicitly declared objectives.

651 may consume resulting candidate plans for personalization.

---

# 257. Planning Heuristics

Built-in planning heuristics may include:

```text
goal distance
resource cost
action cost
critical path
relaxed planning graph
```

---

# 258. Planning Dead-End Detection

The planner SHOULD detect states where:

```text
goal impossible
required resource unavailable
precondition permanently violated
```

when computationally possible.

---

# 259. Action Cost

Actions may have:

```text
time
energy
money
risk
resource
```

costs.

---

# 260. Composite Cost

```axiom
cost =
    time * 0.5 +
    money * 0.3 +
    energy * 0.2
```

The aggregation must be explicit.

---

# 261. Goal Priority

Goals may be:

```text
required
preferred
optional
```

This maps naturally to hard/soft constraints.

---

# 262. Planning Under Resource Constraints

Actions may reserve resources.

---

# 263. Temporal Resource Planning

A resource can be occupied during an interval.

---

# 264. Plan Parallelism

Independent actions may execute concurrently if resources and constraints permit.

---

# 265. Plan Serialization

The runtime can convert a partially ordered plan into a concrete sequence where required.

---

# 266. Plan DAG

Plans SHOULD internally support dependency DAGs.

---

# 267. Cycle Detection

Cyclic precedence constraints must be detected before scheduling.

---

# 268. Critical Path

Scheduling analysis should expose:

```text
critical path
critical tasks
slack
```

---

# 269. Slack

```text
slack = latest_start - earliest_start
```

---

# 270. Bottleneck Detection

The scheduler SHOULD identify:

```text
resource bottlenecks
critical constraints
capacity bottlenecks
```

---

# 271. Capacity Planning

652 can solve:

```text
required capacity
resource allocation
future demand
```

using 642/643 forecasts.

---

# 272. Autoscaling Integration

636 may use 652 to compute:

```text
desired capacity
placement
rollout schedule
```

but 636 remains responsible for actual deployment.

---

# 273. Load Balancing

631/632 may use 652 for:

```text
optimal routing
weighted placement
capacity allocation
```

---

# 274. Cost Optimization

652 can optimize declared cost models.

Cost sources may come from:

```text
642 analytics
606 resource accounting
external pricing
```

---

# 275. Budget Constraint

```axiom
constraint total_cost <= budget
```

---

# 276. Risk Constraint

Risk can be modeled explicitly.

```axiom
constraint expected_risk <= threshold
```

---

# 277. Risk Provenance

Risk estimates must identify their model/data source.

---

# 278. No Hidden Risk Model

The engine must not invent risk assumptions.

---

# 279. Robust Decision

Robust decisions should report:

```text
uncertainty set
worst-case objective
scenario failures
```

---

# 280. Decision Sensitivity

Parameter changes should be measurable.

---

# 281. API Extensibility

New optimization methods should be added as providers rather than changing the core ABI.

---

# 282. Versioning

The 652 API uses semantic versioning:

```text
Decision API 5.x
```

Breaking changes require major version changes.

---

# 283. Compatibility

Decision artifacts should declare:

```text
minimum runtime version
required capabilities
solver requirements
```

---

# 284. Serialization

Decision models must serialize into:

```text
binary
JSON-compatible diagnostic form
human-readable text
```

---

# 285. Compact Binary Form

Production artifacts SHOULD use compact binary encoding.

---

# 286. Human-Readable Form

The source representation remains canonical for developers.

---

# 287. AI-Readable Form

Metadata should expose semantic labels and relationships.

Example:

```text
variable: workers
type: integer
domain: 1..100
meaning: available production workers
```

---

# 288. Documentation Generation

Compiler can generate decision documentation:

```text
axiom decision doc
```

---

# 289. Schema Extraction

Compiler can emit:

```text
decision schema
constraint schema
objective schema
solution schema
```

---

# 290. Test Generation

The compiler/test runtime SHOULD generate:

```text
boundary cases
constraint violation cases
empty domains
resource saturation
deadline cases
```

---

# 291. Property Testing

Decision models may define properties:

```axiom
property solution_respects_constraints
property objective_is_consistent
```

---

# 292. Fuzzing

Decision models should be fuzzable through 646.

---

# 293. Differential Testing

A native solver can be compared with external providers.

---

# 294. Solver Conformance

Every provider must pass:

```text
model parsing
domain correctness
constraint correctness
objective correctness
cancellation
timeout
error handling
result validation
```

tests.

---

# 295. Benchmark Suite

Axiom should maintain benchmark classes:

```text
SAT-like
scheduling
routing
assignment
packing
planning
continuous optimization
mixed integer
search
```

---

# 296. Performance Targets

Targets should measure:

```text
model construction overhead
solve latency
memory
throughput
scaling
```

rather than claiming a universal solver speed.

---

# 297. Small Problem Optimization

Small models should avoid heavyweight solver initialization.

---

# 298. Large Problem Optimization

Large models should support:

```text
streaming construction
incremental solving
parallelism
checkpointing
distributed execution
```

---

# 299. Streaming Constraints

Very large generated constraint sets may be constructed incrementally.

---

# 300. Streaming Solutions

The solver may emit improving solutions:

```text
on_solution(solution)
```

---

# 301. Solution Callback

Callbacks must execute under the declared runtime execution model.

---

# 302. Callback Safety

Solver callbacks must not mutate solver internals unless explicitly supported.

---

# 303. Backpressure

Streaming solutions use 607/608 mechanisms for backpressure.

---

# 304. Event Integration

Decision events:

```text
SolveStarted
SolutionFound
IncumbentImproved
BoundImproved
ConstraintViolation
SolveCompleted
SolveCancelled
```

---

# 305. Event Persistence

Important decision events may be persisted through 600/602.

---

# 306. Decision Trigger

Other runtimes may trigger solves on:

```text
data update
resource change
policy change
forecast change
failure
schedule disruption
user request
agent request
```

---

# 307. Replanning Trigger Policy

Trigger conditions must be explicit.

---

# 308. Debouncing

Rapid changes may be coalesced to avoid unnecessary solving.

---

# 309. Solve Queue

Large systems may queue decision requests.

629/607 handle execution scheduling.

---

# 310. Priority

Decision requests may have:

```text
critical
high
normal
low
```

priority.

---

# 311. Fairness of Solver Scheduling

The runtime SHOULD prevent low-priority requests from permanently starving other requests unless explicitly configured.

---

# 312. Multi-Tenant Isolation

Decision solving must respect 603/606 tenant boundaries.

---

# 313. Tenant Resource Limits

Each tenant may receive separate:

```text
CPU
memory
GPU
time
solver concurrency
```

budgets.

---

# 314. Model Ownership

Decision artifacts have ownership metadata.

---

# 315. Authorization

Operations:

```text
read model
solve model
modify model
register provider
inspect solution
export decision
```

may require different capabilities.

---

# 316. Decision Data Privacy

Private user preferences from 651 must not appear in public decision artifacts without authorization.

---

# 317. Federated Decision Inputs

Federated systems may contribute aggregate statistics without exposing raw data.

---

# 318. Privacy-Preserving Optimization Boundary

Optional providers may support:

```text
secure aggregation
differential privacy
encrypted computation
```

These are provider capabilities, not mandatory core features.

---

# 319. Decision Governance

Organizations can declare:

```text
approved solvers
approved model versions
maximum decision risk
required audit
```

through 639/640.

---

# 320. Model Approval

Production models may require approval before use.

647 manages lifecycle.

---

# 321. Solver Approval

External solver providers can be registered and approved through 647/603.

---

# 322. Decision Deployment

Decision models can be packaged through 613/625.

---

# 323. Version Rollback

A failed model can roll back through 600/625/647.

---

# 324. Canary Decision Model

636 may deploy a new decision model to a subset of requests.

---

# 325. Shadow Decisions

A new solver/model can run without affecting execution.

```text
production decision
       │
       ├── execute
       │
       └── shadow decision
```

Results are compared through 646.

---

# 326. Decision A/B Evaluation

637 may assign experiment cohorts.

652 records experiment identity.

---

# 327. Experiment Isolation

Experiment-specific objectives or constraints must be explicit.

---

# 328. Agent Planning Experiments

644 may compare planning strategies using 646/648.

---

# 329. Decision Model Registry

647 stores:

```text
model versions
solver requirements
approval state
deployment state
```

---

# 330. Decision Runtime Registry

A runtime can discover installed:

```text
solver providers
heuristics
model templates
domain libraries
```

---

# 331. Package Isolation

Providers are isolated through 623/603.

---

# 332. Offline Mode

Core solver must work without network access.

---

# 333. Reproducible Offline Decisions

Offline mode should support:

```text
model artifact
data snapshot
solver
configuration
seed
```

as a complete decision package.

---

# 334. Embedded Decision Engine

Applications may statically link a subset of 652.

---

# 335. Dead-Code Elimination

Unused solver families should be removable by the linker.

---

# 336. Minimal Binary

A simple application using only constraint solving should not include:

```text
distributed runtime
GPU provider
ML provider
```

unless required.

---

# 337. Static Linking

652 components should support static linking.

---

# 338. Dynamic Linking

Optional providers may be dynamically loaded.

---

# 339. ABI Stability

Provider ABI must remain independent from compiler internal IR versions.

---

# 340. Native Code Generation

Hot objective/constraint expressions may compile to native machine code.

---

# 341. JIT Boundary

Optional JIT can specialize:

```text
constraint evaluator
objective evaluator
heuristic
transition function
```

---

# 342. AOT Specialization

AOT compilation is preferred where model structure is static.

---

# 343. Expression Compilation

Repeated expressions should be compiled once and reused.

---

# 344. Constant Propagation

Constant parameters should be folded.

---

# 345. Branch Elimination

Conditional constraints with compile-time conditions may be simplified.

---

# 346. Sparse Models

Large sparse constraint matrices should use sparse representations.

---

# 347. Dense Models

Small dense models may use dense arrays for cache efficiency.

---

# 348. Adaptive Representation

The runtime may select sparse/dense layout based on model statistics.

---

# 349. Matrix Integration

643 numerical primitives may provide matrix operations.

---

# 350. Linear Model

652 defines semantic linear expressions while 643 may provide optimized numeric kernels.

---

# 351. Nonlinear Model

Nonlinear providers must explicitly advertise supported operations.

---

# 352. Nonlinear Safety

Unsupported nonlinear expressions must fail clearly.

---

# 353. Discrete Model

Integer/Boolean domains should use compact bit/integer representations.

---

# 354. Boolean Propagation

Native propagation should simplify logical constraints aggressively.

---

# 355. SAT Boundary

SAT solving is optional provider capability.

---

# 356. SMT Boundary

SMT solving is optional provider capability.

---

# 357. MILP Boundary

MILP solving is optional provider capability.

---

# 358. CP Boundary

Constraint programming is supported through native/provider architecture.

---

# 359. Solver Portfolio

The runtime may run several solvers and select the best valid result.

This mode must record all participating providers.

---

# 360. Portfolio Budget

A portfolio solver receives a shared resource budget.

---

# 361. Solver Racing

Independent solvers may race.

The first valid solution is not automatically globally optimal unless optimality is proven.

---

# 362. Portfolio Result

The final result records:

```text
providers attempted
providers completed
best solution
proof status
```

---

# 363. Decision Quality

Quality is represented through declared metrics rather than a universal score.

---

# 364. No Universal "Best"

652 MUST NOT impose a universal notion of best decision.

The model declares:

```text
objectives
constraints
tradeoffs
```

---

# 365. Decision Tradeoffs

The runtime may expose:

```text
Pareto frontier
objective deltas
constraint costs
```

to let applications select according to explicit criteria.

---

# 366. Decision Selection

When multiple solutions exist, the caller can specify:

```axiom
select(solution where ...)
```

---

# 367. Human-in-the-Loop

Applications may pause after optimization for human approval.

---

# 368. Approval Record

```axiom
DecisionApproval {
    decision_hash
    approver
    timestamp
    policy_revision
}
```

---

# 369. Agent-in-the-Loop

644 can inspect several candidate plans and request another solve.

---

# 370. Decision Escalation

If constraints conflict or uncertainty is high, the system may return:

```text
NeedsReview
```

rather than fabricating certainty.

---

# 371. Review Reasons

```text
infeasible
high uncertainty
large objective tradeoff
policy conflict
insufficient data
solver timeout
```

---

# 372. Human Override

An application may explicitly override a decision.

The override must be recorded as:

```text
human override
```

and must not modify the original solver result.

---

# 373. Override Provenance

```text
original decision
override actor
override reason
new decision
```

---

# 374. Decision Lifecycle State

```axiom
enum DecisionLifecycle {
    Draft
    Validated
    Solving
    Solved
    Approved
    Executing
    Completed
    Superseded
    Rejected
}
```

---

# 375. Supersession

A new decision may supersede an older decision without deleting history.

---

# 376. Decision Lineage

The runtime tracks:

```text
decision A
   ↓ modified
decision B
   ↓ modified
decision C
```

---

# 377. Temporal Validity

Decisions can have:

```text
valid_from
valid_until
```

---

# 378. Expired Decisions

An expired decision must not automatically be treated as current.

---

# 379. Decision Refresh

Dynamic decisions may specify:

```text
refresh interval
refresh triggers
```

---

# 380. Solver Service Mode

Axiom can expose a persistent solver service:

```text
DecisionService
```

which keeps compiled models warm.

---

# 381. Service API

```text
create_problem
update_problem
solve
cancel
checkpoint
resume
explain
close
```

---

# 382. Service Isolation

Each tenant/request receives isolated solver state.

---

# 383. Connection Failure

Persistent solve services must recover through 600/605.

---

# 384. Distributed Solver Service

630 may distribute solver workers.

---

# 385. Cluster Solver

635 may allocate solver workers based on resource availability.

---

# 386. Network Transport

609/626 provide transport.

652 defines only decision protocol semantics.

---

# 387. Decision RPC

A serialized decision request contains:

```text
model
context
budget
solver requirements
```

---

# 388. Remote Solver Security

Remote solver calls must use 603/610/627 boundaries.

---

# 389. Remote Result Verification

Remote solutions should be independently validated when feasible.

---

# 390. Model Integrity

The receiver verifies model hash before solving.

---

# 391. Result Integrity

The receiver verifies solution hash before accepting the result.

---

# 392. Replay Protection

Requests may include:

```text
request_id
nonce
timestamp
```

where required by the transport/security layer.

---

# 393. Decision Quotas

Per-application quotas:

```text
solves/sec
concurrent solves
CPU
memory
model size
```

---

# 394. Rate Limiting

632/606 may enforce limits.

---

# 395. Backpressure

607/608 mechanisms handle queued solves.

---

# 396. Scheduling Solves

Decision requests themselves can be scheduled by 607.

---

# 397. Priority Inversion

Solver scheduling must account for resource priorities.

---

# 398. Starvation Prevention

Long-running low-priority solves may be preemptible.

---

# 399. Preemption

A solver may checkpoint before yielding resources.

---

# 400. Resume

```axiom
Decision.resume(checkpoint)
```

continues from a compatible checkpoint.

---

# 401. Checkpoint Compatibility

Checkpoint requires matching:

```text
model
solver
provider
architecture compatibility
```

---

# 402. Migration

Portable checkpoints are preferred.

Provider-specific checkpoints may remain non-portable.

---

# 403. Crash Recovery

Interrupted solves may resume from last durable checkpoint.

---

# 404. Checkpoint Frequency

Checkpoint frequency is configurable.

---

# 405. Storage

Checkpoint artifacts use 611/600.

---

# 406. Compression

613 may compress large solver checkpoints.

---

# 407. Content Addressing

Checkpoint identity may use 613 content hashes.

---

# 408. Garbage Collection of Checkpoints

Retention policy belongs to 600/640.

652 only exposes lifecycle metadata.

---

# 409. Decision Artifact Cleanup

Unused decision artifacts can be removed according to lifecycle policy.

---

# 410. API Stability

The semantic model must remain stable even when solver implementations change.

---

# 411. Language-Level Integration

Decision declarations are ordinary Axiom declarations.

They can be:

```text
generic
composed
parameterized
embedded
tested
compiled
serialized
```

---

# 412. Generic Problems

```axiom
decision Assignment<TResource, TTask> { ... }
```

---

# 413. Reusable Solver Components

Heuristics and constraints may be generic functions.

---

# 414. Struct-Only OOP Compatibility

No classes are required.

Example:

```axiom
struct Solver {}

fn Solver.solve(self, problem: DecisionProblem)
    -> DecisionSolution
```

---

# 415. Override Mechanism

Solver behavior can be customized through explicit provider/trait implementation rather than class inheritance.

Example:

```axiom
trait Solver {
    fn solve(self, problem) -> DecisionSolution
}

struct NativeSolver {}
struct MySolver {}

impl Solver for NativeSolver { ... }
impl Solver for MySolver { ... }
```

---

# 416. Method Dispatch

Static dispatch is preferred.

Dynamic dispatch is optional where runtime-selected providers are needed.

---

# 417. Zero-Cost Abstractions

Static solver strategies SHOULD compile away abstraction overhead when concrete types are known.

---

# 418. Runtime Dispatch

Provider registries may use explicit handles/function tables.

---

# 419. Trait Boundary

Traits should define solver/provider contracts without requiring inheritance.

---

# 420. Decision DSL

Axiom may expose specialized syntax while lowering everything to the common 652 IR.

---

# 421. DSL Example

```axiom
decision {
    variables ...
    constraints ...
    objectives ...
}
```

---

# 422. Unified Semantics

Regardless of syntax, all models compile to the same semantic decision representation.

---

# 423. Static Type Checking

Invalid variable/domain combinations are compiler errors.

---

# 424. Example Error

```text
cannot apply temporal precedence to scalar Bool variable
```

---

# 425. Model Linting

The compiler should warn about:

```text
dominated objectives
unused constraints
unreachable actions
excessively loose domains
likely unbounded objectives
```

---

# 426. Performance Hints

Optional annotations:

```text
@branch
@priority
@propagate
@memoize
@parallel
@cache
```

These are hints, not semantic requirements.

---

# 427. Semantic vs Performance Metadata

The compiler must distinguish:

```text
semantic declaration
```

from:

```text
optimization hint
```

---

# 428. Incorrect Hints

An invalid optimization hint must never change program correctness.

---

# 429. Constraint Compilation

Constraints compile into normalized form:

```text
LHS
operator
RHS
```

where possible.

---

# 430. Objective Normalization

Maximize/minimize expressions are normalized into canonical representation.

---

# 431. Canonical Model

Equivalent models SHOULD produce equivalent canonical hashes when normalization is deterministic.

---

# 432. Model Hashing

Canonical model hashing enables cache reuse.

---

# 433. Cache Safety

Cache hits require matching semantic inputs.

---

# 434. Cache Invalidation

Changes to:

```text
constraint
objective
domain
data
policy
solver
```

invalidate affected cache entries.

---

# 435. Data Dependency

Dynamic external data must carry revision/version identity.

---

# 436. Point-in-Time Decision

Historical decisions must use the data snapshot available at decision time.

---

# 437. Temporal Data Correctness

643/642 data lineage propagates into 652 provenance.

---

# 438. Decision Dataset

Repeated decisions may be collected into a dataset for 643/646 analysis.

---

# 439. Decision Learning

Historical decisions can train models, but 652 does not automatically assume historical decisions were optimal.

---

# 440. Imitation Boundary

Learning from previous decisions is a 643 capability.

652 can serve as the optimization target.

---

# 441. Reinforcement Learning Boundary

RL policy training belongs to 643.

652 can provide environment/action constraints and optimization objectives.

---

# 442. Agent Planning Boundary

644 decides when to invoke planning.

652 computes the plan.

---

# 443. Knowledge Boundary

645 stores semantic knowledge.

652 consumes graph/model information.

---

# 444. Simulation Boundary

648 simulates outcomes.

652 chooses decisions.

---

# 445. Governance Boundary

639/640 define what is allowed.

652 optimizes within those boundaries.

---

# 446. Personalization Boundary

651 defines user/context preference signals.

652 can use them as declared decision terms.

---

# 447. Final Decision Pipeline

```text
Context
   ↓
Identity / Security
   ↓
Policy
   ↓
Data / Knowledge / Prediction
   ↓
Personalization
   ↓
652 Decision Model
   ↓
Constraint Compilation
   ↓
Objective Compilation
   ↓
Solver Selection
   ↓
Search / Optimization
   ↓
Independent Validation
   ↓
Explanation / Provenance
   ↓
Approval if required
   ↓
Execution
   ↓
Observation
   ↓
Replanning
```

---

# 448. Core Invariants

The following invariants are mandatory.

1. Hard constraints cannot be silently violated.
2. Soft constraints must remain distinguishable from hard constraints.
3. Objective direction must be explicit.
4. A heuristic result cannot be labeled proven optimal.
5. Timeout cannot imply optimality.
6. Solver failure cannot imply infeasibility.
7. Unknown cannot imply feasible.
8. Policy authority remains outside 652.
9. Personalization cannot grant authority.
10. Predictions remain identifiable as predictions.
11. Uncertainty must remain explicit.
12. Solver provenance must be retained.
13. Problem revision must be identifiable.
14. Solution revision must be identifiable.
15. Stale solutions cannot silently become current.
16. Randomized solves must record seeds when reproducibility is requested.
17. Deterministic mode must use stable ordering.
18. Provider failures cannot corrupt other solver instances.
19. Cancellation must be observable.
20. Resource budgets must be enforced.
21. Solver providers cannot bypass security boundaries.
22. Arbitrary native code cannot execute through model expressions.
23. Model expressions must be side-effect free.
24. Objective evaluation must be deterministic when deterministic mode is enabled.
25. Constraint validation must occur before accepting a solution.
26. Invalid domains must fail validation.
27. Empty domains must fail validation.
28. Contradictory constant constraints must be detectable.
29. Unbounded objectives must be reported.
30. Unsupported models must be reported explicitly.
31. Approximation must be explicitly enabled.
32. Approximate results must be marked.
33. Partial results must be marked.
34. Infeasibility certificates must carry provenance.
35. Solver-specific diagnostics must remain identifiable.
36. Generated constraints must be distinguishable from user constraints.
37. Generated objectives must be distinguishable from user objectives.
38. Effective policy constraints must be inspectable.
39. Decision provenance must survive serialization.
40. Decision provenance must survive distributed execution.
41. Solution hashes must correspond to actual solutions.
42. Checkpoints must identify their source model.
43. Checkpoints must identify their solver.
44. Incompatible checkpoints cannot be resumed.
45. Decision cache keys must include all semantic dependencies.
46. Dynamic data must carry revision identity.
47. Historical replay must use historical inputs.
48. Solver selection must be inspectable.
49. Solver fallback must be recorded.
50. Portfolio execution must record participating providers.
51. Multiple optima must remain distinguishable.
52. Tie-breaking must be explicit.
53. Pareto results must not silently become scalar rankings.
54. Human overrides must not erase original decisions.
55. Superseded decisions must remain auditable where retention requires.
56. Execution is outside the semantic authority of 652.
57. Resource allocation decisions cannot bypass 606.
58. Cluster decisions cannot bypass 635.
59. Workflow decisions cannot bypass 629 execution.
60. Deployment decisions cannot bypass 636 authorization/execution.
61. Agent decisions cannot bypass 603/627 security.
62. Decision data must obey 640 governance.
63. Solver artifacts must obey 613/625 packaging rules.
64. Decision logs must obey 602 observability rules.
65. Decision state must obey 600 lifecycle rules.
66. Decision concurrency must obey 607/608.
67. Distributed decisions must obey 630/635.
68. Remote decisions must obey 609/610/627.
69. GPU decisions must obey 614/606.
70. Tensor decisions must obey 643 numerical semantics.
71. Graph decisions must preserve 645 graph identity.
72. Simulation decisions must preserve 648 scenario provenance.
73. Personalization decisions must preserve 651 profile revision.
74. Model compilation must not change semantic meaning.
75. Optimization hints cannot change correctness.
76. Numeric tolerance must be explicit.
77. Floating-point comparisons must follow declared tolerance.
78. Integer overflow must not silently corrupt a decision model.
79. Unit mismatches must be rejected where statically provable.
80. Temporal values must use canonical time semantics.
81. Calendar semantics must remain explicit.
82. Constraint expressions must be side-effect free.
83. Objective expressions must be side-effect free.
84. Search state must be safely isolated.
85. Concurrent solves must not share mutable state accidentally.
86. Provider ABI must remain stable independently of compiler internals.
87. Third-party solver libraries are optional.
88. The native solver must provide a dependency-free baseline.
89. Small models should not require heavyweight runtime initialization.
90. Unused solver features should be removable from final binaries.
91. Decision artifacts must be AI-readable.
92. Decision artifacts must be machine-verifiable.
93. Decision explanations must not claim information unavailable from the solver.
94. Confidence must not be fabricated.
95. Risk assumptions must be explicit.
96. Counterfactual decisions must be separate revisions.
97. What-if analysis must preserve base-model provenance.
98. Replanning must not silently mutate historical decisions.
99. Decision quality must be defined by explicit objectives/constraints.
100. 652 must remain a decision-computation layer rather than becoming an execution authority.

---

# 449. Acceptance Criteria

BOOTSTRAP-652 is considered implementation-complete when the Axiom implementation satisfies at minimum:

## Core model

- [ ] DecisionProblem exists.
- [ ] DecisionVariable exists.
- [ ] VariableDomain exists.
- [ ] Constraint exists.
- [ ] Objective exists.
- [ ] DecisionSolution exists.
- [ ] SolveOptions exists.
- [ ] SolveStatus exists.
- [ ] DecisionContext exists.
- [ ] Decision provenance exists.

## Native solver

- [ ] Integer variables work.
- [ ] Boolean variables work.
- [ ] Enum variables work.
- [ ] Bounds work.
- [ ] Equality constraints work.
- [ ] Inequality constraints work.
- [ ] Boolean constraints work.
- [ ] Hard constraints work.
- [ ] Soft constraints work.
- [ ] Single-objective minimization works.
- [ ] Single-objective maximization works.
- [ ] Weighted objectives work.
- [ ] Lexicographic objectives work.
- [ ] Feasibility detection works.
- [ ] Infeasibility reporting works.
- [ ] Timeout works.
- [ ] Cancellation works.
- [ ] Solution validation works.

## Search

- [ ] DFS.
- [ ] BFS.
- [ ] Uniform Cost.
- [ ] Best First.
- [ ] A*.
- [ ] Branch and Bound.
- [ ] Beam Search.
- [ ] Heuristic interface.
- [ ] Search statistics.
- [ ] State deduplication.
- [ ] Search checkpointing.

## Optimization

- [ ] Native optimization path.
- [ ] Warm start.
- [ ] Incremental solve.
- [ ] Anytime solve.
- [ ] Objective gap where supported.
- [ ] Deterministic mode.
- [ ] Seeded randomized mode.
- [ ] Solution pool.
- [ ] Pareto provider boundary.

## Planning

- [ ] Initial state.
- [ ] Goal state.
- [ ] Action schema.
- [ ] Preconditions.
- [ ] Effects.
- [ ] Action cost.
- [ ] Plan generation.
- [ ] Plan validation.
- [ ] Temporal planning boundary.
- [ ] Resource-aware planning.

## Scheduling

- [ ] Tasks.
- [ ] Resources.
- [ ] Duration.
- [ ] Release time.
- [ ] Deadline.
- [ ] Precedence.
- [ ] Capacity.
- [ ] Non-overlap.
- [ ] Calendar.
- [ ] Machine eligibility.
- [ ] Makespan.
- [ ] Critical path.
- [ ] Slack.
- [ ] Bottleneck detection.

## Allocation

- [ ] Assignment.
- [ ] Matching.
- [ ] Min-cost assignment.
- [ ] Capacity allocation.
- [ ] Flow boundary.
- [ ] Routing boundary.
- [ ] Packing primitives.

## Distributed runtime

- [ ] Remote solver provider.
- [ ] Worker execution.
- [ ] Distributed budget.
- [ ] Checkpointing.
- [ ] Resume.
- [ ] Provider isolation.
- [ ] Result verification.

## AI integration

- [ ] Agent integration.
- [ ] ML prediction integration.
- [ ] Knowledge graph integration.
- [ ] Simulation integration.
- [ ] Personalization integration.
- [ ] Evaluation integration.
- [ ] Model registry integration.

## Governance/security

- [ ] Policy constraints.
- [ ] Resource quotas.
- [ ] Decision provenance.
- [ ] Audit record.
- [ ] Provider authorization.
- [ ] Artifact integrity.
- [ ] Historical replay.
- [ ] Human approval boundary.

## Compiler

- [ ] Decision syntax.
- [ ] Decision IR.
- [ ] Static validation.
- [ ] Model hashing.
- [ ] Generated metadata.
- [ ] AOT specialization.
- [ ] Dead-code elimination.
- [ ] AI-readable schema generation.

---

# 450. Required Test Families

The implementation must include:

```text
unit tests
property tests
solver conformance tests
compiler tests
serialization tests
determinism tests
numerical tests
concurrency tests
cancellation tests
checkpoint tests
distributed tests
security tests
resource-limit tests
regression benchmarks
```

---

# 451. Mandatory End-to-End Tests

### Test A — Simple optimization

```text
maximize x
subject to x <= 100
```

Expected:

```text
x = 100
status = Optimal
```

### Test B — Infeasible

```text
x <= 5
x >= 10
```

Expected:

```text
Infeasible
```

### Test C — Scheduling

Three tasks with precedence and one machine.

Expected:

```text
no overlap
precedence satisfied
```

### Test D — Routing

Graph with multiple paths.

Expected:

```text
selected route satisfies declared objective
```

### Test E — Timeout

Artificially bounded search.

Expected:

```text
Timeout or Partial
```

never falsely:

```text
Optimal
```

### Test F — Replanning

Change resource capacity.

Expected:

```text
new problem revision
new solution
old solution remains historical
```

### Test G — Agent

644 requests a plan.

Expected:

```text
plan returned
execution not automatically authorized
```

### Test H — Policy

639 introduces a hard constraint.

Expected:

```text
effective model includes constraint
```

### Test I — Personalization

651 provides a preference.

Expected:

```text
preference affects explicit objective/soft constraint
```

but does not create authority.

### Test J — Simulation

648 produces scenarios.

Expected:

```text
scenario provenance preserved
```

---

# 452. Performance Acceptance

The implementation should demonstrate:

```text
O(1) / near-O(1)
```

access for common variable/constraint handles.

Hot loops should avoid unnecessary heap allocation.

Repeated model solves should reuse compiled structures.

Large models should support sparse representation.

---

# 453. Binary Size Acceptance

Applications using only:

```text
constraints + native search
```

must not automatically include:

```text
distributed runtime
GPU runtime
ML runtime
external solver libraries
```

---

# 454. Dependency Acceptance

The native 652 baseline must compile and execute without:

```text
Gurobi
CPLEX
OR-Tools
Z3
MiniZinc
Python
JVM
.NET
Node.js
```

or equivalent external runtime dependencies.

External providers remain optional.

---

# 455. Final Architecture

```text
                    AXIOM APPLICATION
                           │
                  ┌────────▼────────┐
                  │ AI / Agent 644  │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │ Decision Request │
                  └────────┬────────┘
                           │
                 ┌─────────▼─────────┐
                 │      652         │
                 │ Decision Engine  │
                 └─────────┬─────────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
   Planning            Constraints        Objectives
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                  ┌────────▼────────┐
                  │ Canonical Model │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │ Solver Selector │
                  └────────┬────────┘
                           │
       ┌───────────────────┼────────────────────┐
       │                   │                    │
   Native Solver      Search Engine       Providers
       │                   │                    │
       └───────────────────┼────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Solution   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
          Validate      Explain      Snapshot
              │            │            │
              └────────────┼────────────┘
                           │
                    Execution Runtime
```

---

# 456. Relationship to Previous Architecture

```text
600 State
601 Configuration
602 Observability
603 Security
604 IPC
605 Supervision
606 Resources
607 Scheduling
608 Synchronization
609 Networking
610 Cryptography
611 Storage
612 Serialization
613 Packaging
614 Hardware/GPU
615 Graphics
616 Media
617 Text/Unicode
618 Input
619 GUI
620 Reactive UI
621 Documents
622 Navigation
623 Plugins
624 Scripting
625 Distribution
626 HTTP/RPC
627 Identity
628 Distributed Data
629 Workflow
630 Distributed Compute
631 Services
632 Edge
633 Distributed Observability
634 Event Bus
635 Cluster Coordination
636 Deployment
637 Feature/Experiment Control
638 Secrets Rotation
639 Policy
640 Data Governance
641 Search
642 Analytics
643 ML
644 Agents
645 Knowledge Graph
646 AI Evaluation
647 AI Governance
648 Simulation
649 Multimodal
650 Memory
651 Personalization
652 Decision / Optimization
```

The architecture now has a clear separation:

```text
KNOW
  641 / 645 / 650

PREDICT
  643

PERSONALIZE
  651

SIMULATE
  648

DECIDE
  652

EXECUTE
  629 / 630 / 631 / 635 / 636
```

---

# 457. Completion Criteria

BOOTSTRAP-652 is COMPLETE when:

1. the semantic decision model is frozen;
2. constraint semantics are frozen;
3. objective semantics are frozen;
4. solver/provider boundary is frozen;
5. planning model is frozen;
6. scheduling model is frozen;
7. search model is frozen;
8. provenance model is frozen;
9. checkpoint/replay semantics are frozen;
10. compiler IR requirements are frozen;
11. security/governance boundaries are frozen;
12. native solver requirements are frozen;
13. acceptance tests are defined;
14. dependency boundaries are defined;
15. Axiom struct-only/trait architecture is respected.

**Status: COMPLETE**

---

# 458. Next Architecture Task

## BOOTSTRAP-653

**Native AI Causal Inference, Probabilistic Reasoning, Bayesian Modeling, Uncertainty, Evidence Propagation & Decision-under-Uncertainty Runtime 5.0**

652 answers:

> "Given a model, constraints and objectives, what decision should be selected?"

653 will answer the complementary question:

> "Given incomplete, uncertain or probabilistic evidence, what should Axiom believe, infer, update and propagate before making a decision?"

It will integrate:

```text
643 ML
645 Knowledge Graph
646 Evaluation
648 Simulation
650 Memory
651 Personalization
652 Decision
```

while remaining distinct from ordinary deterministic optimization.

The resulting architecture will form:

```text
OBSERVE
   ↓
KNOW
   ↓
PREDICT
   ↓
INFER
   ↓
DECIDE
   ↓
PLAN
   ↓
EXECUTE
   ↓
OBSERVE AGAIN
```

**BOOTSTRAP-652 — COMPLETE.**
:::

BOOTSTRAP-652 đã khóa phần **planning + optimization + constraint/search + scheduling + decision runtime**. Task kế tiếp trong chuỗi là **BOOTSTRAP-653 — Causal/Probabilistic Reasoning & Uncertainty Runtime 5.0**.