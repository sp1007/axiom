Tiếp tục với **BOOTSTRAP-653** — lớp suy luận nhân quả, xác suất và bất định, bổ sung phần còn thiếu giữa **quan sát → suy luận → quyết định** của Axiom.

:::writing{variant="document" id="74163" title="BOOTSTRAP-653 — Native AI Causal Inference, Probabilistic Reasoning, Bayesian Modeling, Uncertainty, Evidence Propagation & Decision-under-Uncertainty Runtime 5.0"}
# BOOTSTRAP-653
## Native AI Causal Inference, Probabilistic Reasoning, Bayesian Modeling, Uncertainty, Evidence Propagation & Decision-under-Uncertainty Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Inference & Uncertainty Plane  
**Priority:** Core AI Runtime / High-Level Native Runtime  
**Depends on:** BOOTSTRAP-600..652  
**Primary dependencies:** 639, 641, 642, 643, 645, 646, 648, 650, 651, 652

---

# 1. Purpose

BOOTSTRAP-653 defines Axiom's native runtime for reasoning when information is:

- incomplete;
- uncertain;
- probabilistic;
- noisy;
- conflicting;
- partially observed;
- causally dependent;
- temporally evolving.

It provides primitives for:

```text
probability
distributions
random variables
conditional probability
Bayesian inference
Bayesian networks
factor graphs
probabilistic graphical models
evidence propagation
belief updating
uncertainty propagation
causal graphs
causal interventions
counterfactual reasoning
effect estimation
confounding analysis
scenario inference
hypothesis comparison
belief revision
decision under uncertainty
```

The runtime bridges:

```text
OBSERVE
   ↓
EVIDENCE
   ↓
INFER
   ↓
BELIEF
   ↓
PREDICT
   ↓
DECIDE
```

---

# 2. Architectural Position

```text
                    WORLD / DATA
                         │
                         ▼
                  ┌──────────────┐
                  │ Observation  │
                  └──────┬───────┘
                         │
                    642 / 643
                         │
                         ▼
                  ┌──────────────┐
                  │    653       │
                  │ Inference &  │
                  │ Uncertainty  │
                  └──────┬───────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Bayesian       Causal        Probabilistic
       Inference      Reasoning       Prediction
          │              │              │
          └──────────────┼──────────────┘
                         │
                  ┌──────▼──────┐
                  │   Belief    │
                  │   State     │
                  └──────┬──────┘
                         │
                       652
                         │
                  ┌──────▼──────┐
                  │   Decision  │
                  └─────────────┘
```

---

# 3. Non-Goals

653 MUST NOT become:

1. a general ML training framework;
2. a database;
3. a knowledge graph database;
4. a deterministic optimizer;
5. a workflow engine;
6. an agent runtime;
7. a simulation engine;
8. a replacement for 643 tensor/ML primitives.

Instead:

```text
643 = learn models
645 = represent knowledge/relationships
648 = simulate worlds/scenarios
652 = optimize decisions
653 = reason under uncertainty and causality
```

---

# 4. Core Principles

## 4.1 Uncertainty is first-class

Axiom MUST distinguish:

```text
known
unknown
uncertain
estimated
predicted
observed
inferred
assumed
counterfactual
```

---

## 4.2 Probability is not certainty

A probability value MUST NOT be represented as a Boolean truth value.

---

## 4.3 Correlation is not causation

The runtime MUST preserve the distinction between:

```text
association
prediction
causal effect
```

---

## 4.4 Causal claims require a causal model

653 MUST NOT infer causal direction merely because two variables correlate.

---

# 5. Core Types

```axiom
struct Probability {
    value: Real
}

struct ProbabilityInterval {
    lower: Real
    upper: Real
}

struct RandomVariable<T> {
    domain: Domain<T>
    distribution: Distribution<T>
}

struct Evidence {
    variable: VariableId
    value: Value
    reliability: Optional<Probability>
}

struct Belief<T> {
    distribution: Distribution<T>
    provenance: EvidenceSet
}
```

---

# 6. Probability Invariants

For ordinary probability:

```text
0 <= P <= 1
```

The compiler/runtime MUST reject invalid probability values.

---

# 7. Probability Representation

Axiom SHOULD provide:

```text
f32 probability
f64 probability
fixed-point probability
log-probability
```

according to profile.

---

# 8. Log Probability

For numerical stability:

```axiom
LogProbability
```

may represent:

```text
log(P)
```

Internally.

Conversion must preserve semantic meaning.

---

# 9. Probability Distribution

```axiom
trait Distribution<T> {
    probability(value: T) -> Probability
    sample(rng: Random) -> T
    log_probability(value: T) -> Real
}
```

---

# 10. Required Distributions

Native runtime SHOULD support:

```text
Bernoulli
Categorical
Uniform
Normal
LogNormal
Exponential
Poisson
Binomial
Geometric
Beta
Gamma
Dirichlet
MultivariateNormal
Mixture
Empirical
Discrete
```

---

# 11. Distribution Metadata

```axiom
struct DistributionInfo {
    family: DistributionFamily
    parameters: ParameterSet
    support: Domain
}
```

---

# 12. Discrete Distribution

```axiom
struct DiscreteDistribution<T> {
    outcomes: Sequence<T>
    probabilities: Sequence<Probability>
}
```

Probabilities must sum to 1 within declared numerical tolerance.

---

# 13. Continuous Distribution

Continuous distributions expose density rather than point probability.

```axiom
pdf(x)
cdf(x)
quantile(p)
```

---

# 14. Sampling

```axiom
sample(distribution, rng)
```

must use explicit randomness.

---

# 15. Randomness

```axiom
struct Random {
    algorithm: RandomAlgorithm
    seed: u64
}
```

Reproducible inference requires explicit seed/state when sampling is involved.

---

# 16. Random Algorithms

Native options:

```text
PCG
Xoshiro
Philox
ChaCha-based secure RNG boundary
```

Cryptographic randomness belongs to 610.

---

# 17. Expectation

```axiom
expectation(X)
```

represents:

```text
E[X]
```

---

# 18. Variance

```axiom
variance(X)
```

---

# 19. Covariance

```axiom
covariance(X, Y)
```

---

# 20. Correlation

```axiom
correlation(X, Y)
```

Correlation MUST be clearly distinguished from causal effect.

---

# 21. Conditional Probability

```axiom
P(A | B)
```

is represented as:

```axiom
conditional_probability(A, B)
```

---

# 22. Bayes Rule

The semantic identity:

```text
P(A|B) = P(B|A) P(A) / P(B)
```

is available to the inference engine.

---

# 23. Prior

```axiom
struct Prior<T> {
    distribution: Distribution<T>
}
```

---

# 24. Likelihood

```axiom
trait Likelihood<Model, Data> {
    evaluate(model: Model, data: Data) -> LogProbability
}
```

---

# 25. Posterior

```axiom
struct Posterior<T> {
    distribution: Distribution<T>
    evidence: EvidenceSet
}
```

---

# 26. Bayesian Update

```axiom
posterior = bayes(prior, likelihood, evidence)
```

---

# 27. Evidence

Evidence must carry provenance.

```axiom
struct Evidence {
    source: EvidenceSource
    timestamp: Time
    observation: Observation
    reliability: Optional<Probability>
}
```

---

# 28. Evidence Sources

Sources may be:

```text
sensor
database
user
model
agent
external service
simulation
memory
knowledge graph
derived computation
```

---

# 29. Evidence Reliability

Reliability is metadata about evidence quality.

It MUST NOT automatically become the probability of the hypothesis.

---

# 30. Conflicting Evidence

The runtime supports multiple observations that disagree.

```text
Evidence A → P(H)
Evidence B → P(H)
Evidence C → P(H)
```

The inference model decides how they combine.

---

# 31. Evidence Provenance

Every posterior SHOULD retain:

```text
source evidence
model version
inference method
timestamp
```

---

# 32. Belief State

```axiom
struct BeliefState {
    variables: BeliefVariableSet
    evidence: EvidenceSet
    revision: u64
}
```

---

# 33. Belief Revision

New evidence creates a new belief revision.

Historical beliefs MUST remain recoverable where retention policy requires.

---

# 34. Bayesian Network

```axiom
struct BayesianNetwork {
    variables: VariableSet
    edges: DirectedEdgeSet
    conditional_distributions: CPDSet
}
```

---

# 35. DAG Requirement

A Bayesian network's dependency graph MUST be acyclic.

Cycles require another model class.

---

# 36. Conditional Probability Table

For discrete variables:

```axiom
struct CPT {
    variable: VariableId
    parents: VariableIdSet
    probabilities: Tensor
}
```

---

# 37. Factor Graph

```axiom
struct FactorGraph {
    variables: VariableNodeSet
    factors: FactorSet
}
```

---

# 38. Factor

```axiom
trait Factor {
    variables() -> VariableIdSet
    log_value(assignment) -> Real
}
```

---

# 39. Factorization

A joint distribution may be represented as:

```text
P(X1...Xn) = product of factors
```

---

# 40. Graphical Model

653 supports a common abstraction:

```axiom
trait ProbabilisticModel {
    variables()
    factors()
    infer(query, evidence)
}
```

---

# 41. Inference Methods

Native/provider methods:

```text
ExactEnumeration
VariableElimination
BeliefPropagation
LoopyBeliefPropagation
Sampling
MCMC
ImportanceSampling
ParticleFiltering
VariationalInference
LaplaceApproximation
ExternalProvider
```

---

# 42. Exact Inference

For sufficiently small models, exact inference SHOULD be available.

---

# 43. Approximate Inference

Approximate inference MUST report:

```text
method
sample count / iteration count
approximation type
convergence metadata
```

where applicable.

---

# 44. Inference Status

```axiom
enum InferenceStatus {
    Exact
    Approximate
    Converged
    NotConverged
    Partial
    Timeout
    Failed
}
```

---

# 45. Approximation Warning

A non-converged approximate inference result MUST NOT be presented as an exact posterior.

---

# 46. Marginal Query

```axiom
infer P(A)
```

---

# 47. Conditional Query

```axiom
infer P(A | B)
```

---

# 48. Joint Query

```axiom
infer P(A, B, C)
```

---

# 49. MAP Inference

Maximum a posteriori:

```axiom
map(query, evidence)
```

returns the highest-posterior assignment.

MAP is distinct from posterior distribution.

---

# 50. MPE

Most probable explanation:

```axiom
mpe(evidence)
```

---

# 51. Top-K Hypotheses

```axiom
top_k_hypotheses(k)
```

returns multiple hypotheses and their probabilities.

---

# 52. Probability Calibration

643/646 may evaluate calibration.

653 stores calibrated probability metadata where available.

---

# 53. Calibration

A predicted probability of 0.8 means something different from a raw score.

653 MUST preserve:

```text
probability
score
logit
confidence heuristic
```

as distinct types.

---

# 54. Confidence

`Confidence` is not a universal probability.

```axiom
struct Confidence {
    value: Real
    interpretation: ConfidenceInterpretation
}
```

---

# 55. Confidence Interpretation

Possible meanings:

```text
posterior probability
interval coverage
model confidence
heuristic confidence
human confidence
```

---

# 56. Uncertainty Types

653 distinguishes:

```text
AleatoricUncertainty
EpistemicUncertainty
MeasurementUncertainty
ModelUncertainty
ParameterUncertainty
StructuralUncertainty
```

---

# 57. Uncertainty Representation

```axiom
struct Uncertainty<T> {
    value: T
    source: UncertaintySource
    magnitude: UncertaintyMeasure
}
```

---

# 58. Interval Uncertainty

```axiom
Interval<T> {
    lower
    upper
}
```

is useful when a probability distribution is unavailable.

---

# 59. Belief Interval

```axiom
BeliefInterval {
    lower_probability
    upper_probability
}
```

may represent bounded belief.

---

# 60. Set-Valued Uncertainty

The runtime may represent:

```text
possible values ∈ set
```

without inventing a probability distribution.

---

# 61. Missing Data

Missing data is not automatically interpreted as negative evidence.

---

# 62. Unknown State

```axiom
Unknown<T>
```

must remain distinguishable from:

```text
Null
False
Zero
Empty
```

---

# 63. Partial Observation

A model may observe only part of the state.

Inference may calculate a belief over hidden variables.

---

# 64. Hidden Variable

```axiom
@latent
variable Z
```

---

# 65. Latent Variables

Latent variables may appear in:

```text
Bayesian networks
factor graphs
mixture models
HMMs
state-space models
```

---

# 66. Hidden Markov Model

Native model boundary:

```axiom
struct HMM {
    states
    transition
    emission
    initial
}
```

---

# 67. HMM Operations

```text
forward
backward
viterbi
filter
smooth
```

---

# 68. State-Space Model

```axiom
struct StateSpaceModel {
    transition_model
    observation_model
    initial_distribution
}
```

---

# 69. Filtering

```axiom
filter(observation)
```

updates current belief.

---

# 70. Smoothing

```axiom
smooth(observations)
```

uses future evidence to infer previous hidden states.

---

# 71. Prediction

```axiom
predict(horizon)
```

projects belief forward.

---

# 72. Particle Filter

Optional native/provider implementation:

```text
particles
weights
resampling
propagation
```

---

# 73. Sequential Monte Carlo

Particle filtering uses explicit randomness and reports effective sample size where supported.

---

# 74. Bayesian Inference Engine

```axiom
trait BayesianEngine {
    update(prior, evidence) -> Posterior
    marginal(query) -> Distribution
    map(query) -> Assignment
}
```

---

# 75. MCMC

Optional provider:

```text
MetropolisHastings
Gibbs
HamiltonianMonteCarlo
NUTS
```

---

# 76. MCMC Diagnostics

Results should expose:

```text
iterations
burn_in
effective_sample_size
R_hat
acceptance_rate
```

where applicable.

---

# 77. Non-Convergence

Non-converged chains must be explicitly marked.

---

# 78. Sampling Budget

```axiom
InferenceBudget {
    max_time
    max_samples
    max_iterations
    max_memory
}
```

---

# 79. Variational Inference

Provider boundary:

```text
MeanField
StructuredVI
AmortizedInference
```

---

# 80. Evidence Propagation

Evidence can propagate through a graphical model.

```text
Observation
 ↓
Factor
 ↓
Belief
 ↓
Dependent variables
```

---

# 81. Message Passing

Factor graph engines may expose:

```axiom
Message {
    source
    target
    distribution
}
```

---

# 82. Message Scheduling

Supported:

```text
synchronous
asynchronous
residual
priority
```

---

# 83. Belief Propagation

Exact on trees.

For loopy graphs, convergence is not guaranteed and must be represented.

---

# 84. Causal Model

```axiom
struct CausalModel {
    variables: VariableSet
    graph: DirectedGraph
    structural_equations: EquationSet
    assumptions: CausalAssumptionSet
}
```

---

# 85. Causal Graph

A causal graph is a directed graph representing declared causal relationships.

---

# 86. Causal Direction

Edges:

```text
A → B
```

mean the model declares A as a direct causal parent of B.

The runtime does not infer this merely from correlation.

---

# 87. Structural Causal Model

```axiom
struct StructuralEquation {
    target: VariableId
    parents: VariableIdSet
    function: CausalFunction
}
```

---

# 88. Exogenous Variables

```axiom
@exogenous
variable U
```

represents external variation.

---

# 89. Endogenous Variables

Variables determined by structural equations are endogenous.

---

# 90. Causal Assumptions

```axiom
struct CausalAssumption {
    type
    description
    provenance
}
```

Possible assumptions:

```text
no hidden confounding
stable mechanism
acyclicity
consistency
positivity
```

---

# 91. Assumption Provenance

Every causal result must preserve which assumptions were used.

---

# 92. Intervention

```axiom
intervene(X = x)
```

represents an intervention rather than an observation.

---

# 93. do-Operator

Semantic form:

```text
P(Y | do(X=x))
```

must remain distinct from:

```text
P(Y | X=x)
```

---

# 94. Observation vs Intervention

This is a mandatory invariant.

Observing:

```text
X = 1
```

does not mean:

```text
do(X = 1)
```

---

# 95. Intervention Model

When an intervention occurs, incoming causal mechanisms for the intervened variable are replaced according to the causal model.

---

# 96. Average Treatment Effect

```axiom
ATE(X, Y)
```

may be represented as:

```text
E[Y | do(X=1)] - E[Y | do(X=0)]
```

for binary treatment.

---

# 97. Conditional Treatment Effect

```axiom
CTE(X, Y | Z)
```

supports subgroup effects.

---

# 98. Individual Treatment Effect

ITE may be represented where assumptions and data support it.

The runtime must not imply identification merely because the API can express the query.

---

# 99. Identification

```axiom
identify(effect)
```

determines whether the causal quantity is identifiable under the model and assumptions.

---

# 100. Identification Status

```axiom
enum IdentificationStatus {
    Identified
    NotIdentified
    AssumptionDependent
    Unknown
}
```

---

# 101. Backdoor Criterion

The causal engine SHOULD support graph-based backdoor analysis.

---

# 102. Frontdoor Criterion

The causal engine MAY support frontdoor identification.

---

# 103. Adjustment Set

```axiom
AdjustmentSet {
    variables
    justification
}
```

---

# 104. Confounder

A confounder is a variable affecting both treatment and outcome in the causal model.

The runtime must not label a variable a confounder merely from correlation.

---

# 105. Collider

The causal graph may identify collider structures.

---

# 106. Collider Warning

Conditioning on a collider can create spurious association.

The runtime SHOULD diagnose this when graph semantics make it identifiable.

---

# 107. Mediation

```axiom
MediationModel {
    treatment
    mediator
    outcome
}
```

---

# 108. Direct Effect

```axiom
NaturalDirectEffect
```

is supported only under required assumptions.

---

# 109. Indirect Effect

Likewise:

```axiom
NaturalIndirectEffect
```

requires explicit assumptions.

---

# 110. Counterfactual

```axiom
counterfactual(
    observed_state,
    intervention,
    query
)
```

---

# 111. Counterfactual Semantics

Counterfactuals must be tied to a causal model.

The runtime must not fabricate counterfactual outcomes from ordinary correlation alone.

---

# 112. Potential Outcomes

Optional representation:

```axiom
PotentialOutcome {
    treatment
    outcome
}
```

---

# 113. Treatment Assignment

The model can represent:

```text
treated
control
```

and assignment mechanisms.

---

# 114. Randomized Experiment

Experimental data can be represented explicitly.

```axiom
Experiment {
    treatment
    control
    assignment_mechanism
}
```

---

# 115. Observational Data

Observational data must be marked as observational.

---

# 116. Data Source Type

```axiom
enum EvidenceStudyType {
    Observational
    RandomizedExperiment
    QuasiExperimental
    Synthetic
    Simulation
}
```

---

# 117. Synthetic Causal Data

648-generated data must remain marked synthetic.

---

# 118. Causal Effect Provenance

Every causal estimate records:

```text
data source
causal graph
assumptions
adjustment
estimator
model version
```

---

# 119. Causal Estimators

Provider boundary:

```text
InverseProbabilityWeighting
Matching
RegressionAdjustment
DoublyRobust
GFormula
SyntheticControl
DifferenceInDifferences
RegressionDiscontinuity
InstrumentalVariable
```

---

# 120. Estimator Status

```axiom
enum EstimateStatus {
    Estimated
    Identified
    NotIdentified
    Unstable
    InsufficientData
    Failed
}
```

---

# 121. Confidence / Credible Intervals

653 supports:

```text
ConfidenceInterval
CredibleInterval
PredictionInterval
ToleranceInterval
```

as distinct types.

---

# 122. Interval Semantics

The runtime must not conflate frequentist confidence intervals with Bayesian credible intervals.

---

# 123. Posterior Predictive

```axiom
posterior_predictive(query)
```

returns a predictive distribution integrating parameter uncertainty.

---

# 124. Predictive Distribution

Predictions are distributions when uncertainty matters.

---

# 125. Quantile

```axiom
quantile(distribution, p)
```

---

# 126. Credible Region

For Bayesian models:

```axiom
credible_region(level)
```

---

# 127. Highest Posterior Density

Optional provider operation:

```axiom
hpd(level)
```

---

# 128. Entropy

```axiom
entropy(X)
```

---

# 129. Information Gain

```axiom
information_gain(prior, posterior)
```

---

# 130. KL Divergence

```axiom
kl_divergence(P, Q)
```

---

# 131. Jensen-Shannon Divergence

```axiom
js_divergence(P, Q)
```

---

# 132. Mutual Information

```axiom
mutual_information(X, Y)
```

---

# 133. Conditional Mutual Information

```axiom
conditional_mutual_information(X, Y | Z)
```

---

# 134. Information-Theoretic Reasoning

Information metrics may be used by:

```text
active learning
experiment design
feature selection
belief updating
planning
```

---

# 135. Active Information Gathering

653 can represent:

```text
"What observation should I obtain next?"
```

but selection optimization belongs to 652.

---

# 136. Value of Information

```axiom
value_of_information(action, decision_model)
```

can be computed by combining 653 with 652.

---

# 137. Expected Value of Perfect Information

```axiom
EVPI
```

---

# 138. Expected Value of Sample Information

```axiom
EVSI
```

---

# 139. Decision Under Uncertainty

653 produces distributions/beliefs.

652 consumes them:

```text
653
belief / scenarios
   ↓
652
decision optimization
```

---

# 140. Expected Utility

```axiom
expected_utility(decision, belief)
```

---

# 141. Risk-Sensitive Decision

652 may optimize:

```text
expected cost
variance
CVaR
worst case
```

using uncertainty information from 653.

---

# 142. Value-at-Risk

Optional risk metric:

```axiom
VaR(distribution, confidence)
```

---

# 143. Conditional Value-at-Risk

```axiom
CVaR(distribution, confidence)
```

---

# 144. Utility Function

```axiom
trait Utility {
    evaluate(outcome) -> Real
}
```

---

# 145. Expected Utility

```text
EU = Σ P(outcome) * U(outcome)
```

or its continuous equivalent.

---

# 146. Utility vs Probability

Probability describes uncertainty.

Utility describes preference.

They MUST remain separate.

---

# 147. Decision Semantics

```text
653 = uncertainty
651 = preference
652 = optimization
```

---

# 148. Belief + Preference + Decision

```text
Belief
  ↓
Expected outcomes
  ↓
Utility / objectives
  ↓
652
```

---

# 149. Causal Decision

A causal model may feed intervention outcomes into 652.

```text
CausalModel
   ↓
do(X)
   ↓
OutcomeDistribution
   ↓
ExpectedUtility
   ↓
652
```

---

# 150. Policy Evaluation

639 policies may constrain interventions.

---

# 151. Causal Policy

A policy may be represented as:

```axiom
policy:
    if state then intervention
```

653 can estimate outcomes.

652 can optimize among allowed policies.

---

# 152. Policy Value

```axiom
evaluate_policy(policy, causal_model)
```

returns outcome distributions.

---

# 153. Counterfactual Policy Analysis

Different policy alternatives may be evaluated under the same causal model.

---

# 154. No Political/Normative Inference

The runtime does not decide what objectives humans should value.

Objectives remain explicit inputs.

---

# 155. Temporal Causality

Causal models may contain temporal variables.

Edges violating declared temporal order should fail validation.

---

# 156. Dynamic Bayesian Network

```axiom
struct DynamicBayesianNetwork {
    state_variables
    transition_model
    observation_model
}
```

---

# 157. Time-Indexed Belief

```axiom
BeliefState[t]
```

---

# 158. Belief Update

```text
prior[t]
   ↓
transition
   ↓
prediction[t+1]
   ↓
observation[t+1]
   ↓
posterior[t+1]
```

---

# 159. Online Inference

653 supports streaming evidence.

```axiom
belief.update(evidence)
```

---

# 160. Streaming Evidence

New observations should update the current belief without rebuilding the entire model when possible.

---

# 161. Incremental Inference

The runtime SHOULD reuse:

```text
factorization
messages
particles
sufficient statistics
```

when safe.

---

# 162. Sufficient Statistics

Distributions/models may expose sufficient statistics.

---

# 163. Bayesian Conjugacy

Native engine may optimize conjugate models:

```text
Beta-Bernoulli
Gamma-Poisson
Dirichlet-Categorical
Normal-Normal
```

---

# 164. Conjugate Update

Conjugate updates should avoid expensive general-purpose inference.

---

# 165. Approximate Posterior

If no closed form exists, provider inference is used.

---

# 166. Numerical Stability

Probability calculations SHOULD use:

```text
log-sum-exp
normalized weights
stable matrix decomposition
```

where appropriate.

---

# 167. Underflow Protection

Very small probabilities should not silently become zero when log-space computation can preserve information.

---

# 168. Overflow Protection

Large likelihood products must use numerically stable formulations.

---

# 169. Matrix Semantics

643 supplies:

```text
matrix
tensor
linear algebra
decomposition
```

for probabilistic inference.

---

# 170. GPU Inference

Large batched inference may use GPU acceleration through 614/643.

---

# 171. CPU Inference

Small/irregular models should remain efficient on CPU.

---

# 172. Sparse Graphical Models

Large sparse models should use compact adjacency/factor structures.

---

# 173. Dense Models

Small dense distributions may use contiguous tensor storage.

---

# 174. Adaptive Representation

The runtime may select representation based on graph/model size.

---

# 175. Model Compilation

Probabilistic models should compile into an intermediate representation.

```text
AX-PIR
```

---

# 176. Probabilistic IR

```text
variables
domains
factors
distributions
dependencies
evidence
inference operations
```

---

# 177. Causal IR

```text
variables
causal edges
structural equations
interventions
counterfactual queries
assumptions
```

---

# 178. Shared Inference IR

Causal and probabilistic models may lower to shared tensor/factor primitives where mathematically valid.

---

# 179. Compiler Annotations

Required annotations:

```text
@probability
@distribution
@random
@prior
@likelihood
@posterior
@evidence
@belief
@uncertain
@latent
@causal
@cause
@effect
@intervention
@counterfactual
@confounder
@mediator
@experiment
@observation
@stochastic
@sample
@infer
@bayesian
@factor
@factor_graph
@bayesian_network
@markov
@hidden
@prediction
@uncertainty
```

---

# 180. Native Syntax

Example:

```axiom
@probability
variable Rain: Bool

prior Rain {
    true: 0.3
    false: 0.7
}
```

---

# 181. Evidence Syntax

```axiom
observe Rain = true
```

---

# 182. Conditional Model

```axiom
P(WetGrass | Rain, Sprinkler)
```

---

# 183. Bayesian Model Syntax

```axiom
@bayesian
model Weather {
    variable Rain: Bool
    variable Sprinkler: Bool
    variable WetGrass: Bool

    Rain -> WetGrass
    Sprinkler -> WetGrass

    ...
}
```

---

# 184. Causal Syntax

```axiom
@causal
model Treatment {
    Treatment -> Recovery
    Age -> Treatment
    Age -> Recovery
}
```

---

# 185. Intervention Syntax

```axiom
intervene Treatment = true
```

---

# 186. Counterfactual Syntax

```axiom
counterfactual {
    intervene Treatment = false
    query Recovery
}
```

---

# 187. Distribution Syntax

```axiom
variable temperature:
    Normal(mean = 25.0, stddev = 2.0)
```

---

# 188. Uncertain Value Syntax

```axiom
uncertain temperature {
    range 20..30
}
```

---

# 189. Evidence Reliability

```axiom
observe sensor.temperature = 24.5
    @reliability(0.98)
```

Reliability modifies the evidence model only through declared semantics.

---

# 190. Sampling Syntax

```axiom
sample temperature
```

---

# 191. Inference Syntax

```axiom
belief = infer P(Rain | WetGrass = true)
```

---

# 192. MAP Syntax

```axiom
hypothesis = map Rain | evidence
```

---

# 193. Causal Effect Syntax

```axiom
effect = causal_effect(
    Treatment,
    Recovery
)
```

---

# 194. Identification Syntax

```axiom
identify causal_effect(Treatment, Recovery)
```

---

# 195. Posterior Predictive

```axiom
prediction = posterior_predictive(Y)
```

---

# 196. Belief Store

650 may store long-term beliefs.

653 owns inference semantics.

---

# 197. Memory Integration

A belief stored in 650 must retain:

```text
source
timestamp
model
revision
uncertainty
```

---

# 198. Memory Does Not Equal Truth

Retrieving a belief from 650 does not make it certain.

---

# 199. Evidence Weighting

Evidence may have different reliability.

The model determines how reliability enters inference.

---

# 200. Source Independence

Evidence sources may be correlated.

The runtime MUST NOT assume independence unless declared or established by the model.

---

# 201. Double Counting

The runtime SHOULD detect obvious duplicate evidence where provenance permits.

---

# 202. Correlated Evidence

If two observations originate from the same underlying source, they must not automatically be treated as independent evidence.

---

# 203. Evidence Identity

```axiom
EvidenceId
```

uniquely identifies an observation.

---

# 204. Evidence Revision

Corrections create new revisions rather than silently rewriting historical evidence.

---

# 205. Evidence Retraction

```axiom
retract(evidence_id)
```

creates a new belief revision.

---

# 206. Belief Revision

The engine may recompute affected beliefs incrementally.

---

# 207. Contradiction

A belief system may contain contradictory evidence.

653 must represent this explicitly.

---

# 208. Contradiction Resolution

Methods may include:

```text
Bayesian weighting
source reliability
explicit conflict model
belief revision
paraconsistent provider
human review
```

No universal resolution policy is assumed.

---

# 209. Paraconsistent Boundary

Optional reasoning provider can reason with inconsistent knowledge without deriving arbitrary conclusions.

---

# 210. Closed-World vs Open-World

The inference engine MUST distinguish:

```text
not observed
observed false
unknown
```

---

# 211. Open-World Default

Unless a model declares otherwise, missing evidence is unknown.

---

# 212. Closed-World Models

Applications may explicitly declare closed-world semantics.

---

# 213. Temporal Evidence

Evidence has:

```text
observation_time
availability_time
ingestion_time
```

where needed.

---

# 214. Point-in-Time Correctness

Historical inference must use evidence available at the relevant time.

---

# 215. Leakage Prevention

Future evidence must not silently influence historical inference.

---

# 216. Model Versioning

Every inference result records:

```text
model revision
inference algorithm
provider version
parameters
```

---

# 217. Inference Cache

Cache keys include:

```text
model hash
evidence revision
query
algorithm
configuration
```

---

# 218. Cache Safety

A cached posterior must not be reused after relevant evidence changes.

---

# 219. Belief Snapshot

```axiom
struct BeliefSnapshot {
    model
    evidence
    beliefs
    provenance
}
```

Integrates with 600.

---

# 220. Checkpoint

Long inference jobs support checkpoints.

---

# 221. Sampling Checkpoint

MCMC/particle inference checkpoints retain:

```text
random state
samples/particles
weights
iteration
model revision
```

---

# 222. Deterministic Inference

Exact inference must be deterministic under identical inputs.

---

# 223. Reproducible Sampling

Sampling-based inference requires:

```text
seed
RNG algorithm
RNG state
```

for exact replay.

---

# 224. Parallel Sampling

Independent chains may execute in parallel.

---

# 225. Chain Independence

Parallel chains should use independent RNG streams.

---

# 226. Distributed Inference

630 can distribute:

```text
chains
particles
scenarios
factor computations
```

---

# 227. Aggregation

Distributed posterior aggregation must use mathematically valid aggregation rules.

---

# 228. Numerical Precision

Inference may use:

```text
f32
f64
extended precision
log-space
```

depending on model requirements.

---

# 229. Precision Metadata

Result records numerical precision.

---

# 230. Automatic Precision Selection

The runtime MAY increase precision when numerical diagnostics detect instability.

Such behavior must be observable.

---

# 231. Matrix Conditioning

Inference providers should expose conditioning diagnostics where relevant.

---

# 232. Singular Models

Degenerate covariance/matrix structures must be reported explicitly.

---

# 233. Positive Semidefinite Covariance

Covariance matrices must satisfy required numerical validity conditions.

---

# 234. Distribution Validation

Each distribution validates parameter constraints.

Examples:

```text
stddev > 0
probability ∈ [0,1]
shape > 0
```

---

# 235. Invalid Distribution

Invalid parameters produce compile-time or runtime errors depending on whether values are static.

---

# 236. Sampling Validation

Samples must belong to the declared support.

---

# 237. Probability Normalization

Discrete distributions must normalize according to numerical tolerance.

---

# 238. Mixture Model

```axiom
Mixture {
    components
    weights
}
```

Weights must form a valid mixture.

---

# 239. Gaussian Mixture

Optional optimized representation:

```text
GaussianMixture
```

---

# 240. Bayesian Mixture

Component uncertainty remains represented.

---

# 241. Hierarchical Bayesian Model

653 may support:

```text
global parameter
    ↓
group parameter
    ↓
observation
```

---

# 242. Hierarchical Priors

Hierarchical parameters must retain their dependency structure.

---

# 243. Empirical Distribution

Observed samples can define:

```axiom
EmpiricalDistribution(samples)
```

---

# 244. Bootstrap

Optional inference utility:

```axiom
bootstrap(dataset, statistic, B)
```

---

# 245. Resampling

Bootstrap randomness must be reproducible when seeded.

---

# 246. Monte Carlo

```axiom
monte_carlo(model, N)
```

---

# 247. Monte Carlo Error

The runtime SHOULD estimate sampling error.

---

# 248. Confidence in Simulation

Monte Carlo uncertainty is distinct from model uncertainty.

---

# 249. Scenario Propagation

648 scenarios can become evidence/uncertainty inputs.

---

# 250. Scenario Distribution

Scenario weights must be explicit.

---

# 251. Importance Sampling

Optional provider:

```axiom
importance_sample(...)
```

---

# 252. Sequential Decision

653 can provide predictive distributions to 652 for multi-step decisions.

---

# 253. POMDP Boundary

Partially Observable Markov Decision Processes may be represented through:

```text
belief state = 653
action selection = 652
transition/simulation = 648
```

---

# 254. Belief-State Planning

```text
belief
 ↓
possible action
 ↓
predicted belief
 ↓
utility
 ↓
652
```

---

# 255. Model Predictive Control Boundary

MPC may combine:

```text
653 state estimation
652 optimization
648 simulation
```

---

# 256. Causal Planning

652 plans interventions using causal outcomes supplied by 653.

---

# 257. Causal Optimization

A decision objective may depend on:

```text
P(outcome | do(action))
```

---

# 258. Expected Causal Utility

```axiom
maximize E[U(Y) | do(X=x)]
```

---

# 259. Policy Optimization

652 can optimize intervention policies using causal outcome models.

---

# 260. Robust Causal Decision

653 may return uncertainty intervals for causal effects.

652 may optimize against declared risk criteria.

---

# 261. Sensitivity to Causal Assumptions

Causal estimates SHOULD support sensitivity analysis.

---

# 262. Unmeasured Confounding

Where supported:

```axiom
sensitivity_to_unmeasured_confounding(...)
```

---

# 263. Causal Bounds

When point identification fails, the engine may return:

```text
lower bound
upper bound
```

rather than inventing a point estimate.

---

# 264. Partial Identification

```axiom
struct IdentifiedSet<T> {
    lower
    upper
    assumptions
}
```

---

# 265. Assumption Sensitivity

Results should identify assumptions whose removal changes identification.

---

# 266. Causal Graph Validation

Checks:

```text
cycles
invalid variables
missing equations
temporal violations
```

---

# 267. Structural Equation Validation

Every endogenous variable must have an appropriate mechanism where required.

---

# 268. Intervention Validation

Interventions must target declared variables.

---

# 269. Counterfactual Validation

Counterfactual queries require a compatible causal model.

---

# 270. Causal Effect Units

Effects should retain units.

Example:

```text
kg
ms
USD
probability
```

---

# 271. Effect Type

```axiom
struct CausalEffect<T> {
    estimate: T
    uncertainty: Uncertainty<T>
    assumptions: CausalAssumptionSet
}
```

---

# 272. Effect Provenance

Includes:

```text
data
model
estimator
adjustment
assumptions
```

---

# 273. Causal Discovery Boundary

Automatic causal discovery may be provided by 643/optional provider.

653 consumes a causal graph.

---

# 274. Causal Discovery Warning

A discovered graph is a model hypothesis, not automatically ground truth.

---

# 275. Graph Confidence

Discovery algorithms may provide edge scores, but those scores must not be represented as established causal certainty.

---

# 276. Knowledge Graph Integration

645 relationships may provide candidate causal structures.

653 requires explicit causal semantics before using them causally.

---

# 277. Semantic Relationship

```text
645:
"smoking associated_with disease"

653:
requires:
"smoking causes disease"
```

if a causal inference is requested.

---

# 278. Ontology Integration

Variable types and meanings may come from 645.

---

# 279. Unit Semantics

617/642/643 may provide semantic units.

---

# 280. Multimodal Evidence

649 can provide evidence from:

```text
text
image
audio
video
sensor
```

653 treats extracted signals according to declared uncertainty.

---

# 281. Speech Evidence

Speech recognition confidence is not automatically causal or probabilistic evidence of the underlying event.

---

# 282. Vision Evidence

Object detection probability remains model output metadata.

---

# 283. Evidence Fusion

Multiple modalities may be combined through:

```text
factor model
Bayesian model
ensemble
provider
```

---

# 284. Evidence Fusion Provenance

Each modality remains traceable.

---

# 285. Sensor Fusion

Native use cases:

```text
GPS
IMU
camera
radar
temperature
```

through probabilistic state estimation.

---

# 286. Kalman Filter Boundary

Optional native/provider implementation:

```text
KalmanFilter
ExtendedKalmanFilter
UnscentedKalmanFilter
```

---

# 287. State Estimation

State estimation outputs:

```text
mean
covariance
timestamp
model revision
```

---

# 288. Sensor Reliability

Sensor reliability is model metadata, not an absolute truth.

---

# 289. Outlier Handling

Inference providers may support robust likelihoods.

---

# 290. Missing Sensor

Missing observations must not automatically mean zero.

---

# 291. Fault Diagnosis

653 may infer hypotheses:

```text
sensor fault
component fault
network fault
```

with explicit posterior probabilities.

---

# 292. Diagnosis

```axiom
diagnose(evidence)
```

returns ranked hypotheses with probabilities.

---

# 293. Diagnosis + Planning

```text
653 diagnosis
      ↓
652 repair plan
```

---

# 294. Anomaly Detection Boundary

643 may provide anomaly models.

653 can represent uncertainty around anomaly hypotheses.

---

# 295. Hypothesis Set

```axiom
struct Hypothesis<T> {
    state: T
    posterior: Probability
    provenance: EvidenceSet
}
```

---

# 296. Hypothesis Ranking

Ranking is by explicit posterior or utility.

---

# 297. No Hidden Ranking Criterion

The engine must not silently combine probability and utility.

---

# 298. Belief Decision Interface

```axiom
belief.select_by_probability()
belief.select_by_expected_utility()
```

These remain distinct operations.

---

# 299. Decision Interface

652 receives either:

```text
distribution
expected value
scenario set
risk measure
```

according to the decision model.

---

# 300. Distribution-to-Decision Conversion

The conversion must be explicit.

---

# 301. Expected Value

Replacing an uncertain variable with its mean is an approximation unless the decision model explicitly permits it.

---

# 302. Jensen Effect

Nonlinear objectives SHOULD preserve full distributions when expectation-of-function differs from function-of-expectation.

---

# 303. Risk Neutrality

Expected-value optimization assumes risk-neutral semantics.

Risk preferences must be explicit.

---

# 304. Risk Aversion

Use utility/risk functions rather than hidden transformations.

---

# 305. Robustness

Robust decisions can use uncertainty sets rather than probabilities.

---

# 306. Ambiguity

Distinguish:

```text
risk:
known probability model

ambiguity:
uncertain probability model
```

---

# 307. Distributional Uncertainty

Optional representation:

```axiom
DistributionSet
```

---

# 308. Distributionally Robust Optimization Boundary

653 provides distribution uncertainty.

652/provider performs optimization.

---

# 309. Evidence Acquisition

653 can identify uncertainty that could be reduced by additional evidence.

---

# 310. Active Learning Boundary

643 may train/update models.

653 computes information gain.

652 selects acquisition action.

---

# 311. Experiment Design

```axiom
design_experiment(model, candidate_observations)
```

may return expected information gain.

---

# 312. Experiment Selection

Optimization of experiment design belongs to 652.

---

# 313. Causal Experiment Design

The causal graph may determine which intervention provides useful information.

---

# 314. Intervention Cost

Experiment actions can have:

```text
time
money
risk
resource
```

and 652 can optimize them.

---

# 315. Privacy

Evidence and posterior states obey 640.

---

# 316. Security

Inference models are untrusted inputs.

No arbitrary executable code may be embedded in probabilistic expressions.

---

# 317. Provider Security

External inference providers require 603 capability authorization.

---

# 318. Resource Limits

Inference is governed by 606:

```text
CPU
memory
GPU
time
samples
iterations
```

---

# 319. Distributed Inference

630 provides execution.

653 defines mathematical semantics.

---

# 320. Observability

602 records:

```text
inference latency
sample count
convergence
model size
evidence count
provider
```

---

# 321. Metrics

Recommended:

```text
inference.request.count
inference.latency
inference.timeout
inference.failure
inference.sample_count
inference.convergence
inference.posterior_entropy
causal.effect.count
causal.identification.failure
```

---

# 322. Trace

```text
evidence
 → model
 → inference
 → posterior
 → causal query
 → decision
```

---

# 323. Audit

Inference audit contains:

```text
model revision
evidence revision
query
algorithm
parameters
result
assumptions
```

---

# 324. Reproducibility

A result must be replayable when all required model/evidence/provider/randomness artifacts are available.

---

# 325. Inference Snapshot

```axiom
InferenceSnapshot {
    model
    evidence
    query
    result
    provenance
}
```

---

# 326. Serialization

Support:

```text
binary
human-readable
JSON-compatible diagnostics
```

---

# 327. Compact Representation

Production probabilistic models should use compact binary storage.

---

# 328. AI Metadata

Generated metadata should expose:

```text
variable meanings
causal edges
probability semantics
assumptions
evidence provenance
inference algorithm
uncertainty
```

---

# 329. Generated Files

Recommended artifacts:

```text
.axprobability
.axdistribution
.axbelief
.axevidence
.axfactor
.axbayes
.axcausal
.axintervention
.axcounterfactual
.axinference
.axposterior
.axuncertainty
.axcausaleffect
```

---

# 330. CLI

```text
axiom infer solve
axiom infer update
axiom infer query
axiom infer explain
axiom infer validate
axiom infer sample
axiom infer diagnose

axiom causal validate
axiom causal identify
axiom causal effect
axiom causal intervene
axiom causal counterfactual

axiom probability inspect
axiom probability sample
```

---

# 331. Inference Explanation

```axiom
struct InferenceExplanation {
    query
    evidence
    model
    method
    assumptions
    result
    uncertainty
    diagnostics
}
```

---

# 332. Causal Explanation

```axiom
struct CausalExplanation {
    query
    graph
    intervention
    adjustment
    assumptions
    identification
    estimate
    uncertainty
}
```

---

# 333. Explanation Boundary

Explanations describe the mathematical/model path.

They do not expose hidden internal chain-of-thought.

---

# 334. Model Comparison

653 can compare probabilistic models using explicit criteria:

```text
likelihood
AIC
BIC
WAIC
cross-validation
posterior predictive checks
```

Provider-dependent metrics must identify their semantics.

---

# 335. Model Selection

Model selection is distinct from causal truth.

---

# 336. Bayesian Model Comparison

Optional:

```text
BayesFactor
ModelPosterior
```

---

# 337. Posterior Predictive Check

```axiom
posterior_predictive_check(model, observed_data)
```

---

# 338. Calibration Check

```axiom
calibration_check(predictions, outcomes)
```

---

# 339. Distribution Check

```axiom
distribution_check(samples, model)
```

---

# 340. Statistical Tests

Statistical testing belongs primarily to 642/643 but 653 can consume test results as evidence metadata.

---

# 341. P-Value

If represented, p-values MUST remain distinct from posterior probabilities.

---

# 342. Statistical Significance

653 MUST NOT automatically convert statistical significance into causal significance.

---

# 343. Effect Size

Effect magnitude remains distinct from statistical significance.

---

# 344. Practical Significance

A domain can define explicit utility thresholds.

---

# 345. Model Assumptions

Every probabilistic/causal model may declare:

```axiom
assume ...
```

---

# 346. Assumption Validation

Some assumptions can be checked mechanically.

Others remain untestable modeling assumptions.

---

# 347. Assumption Status

```axiom
enum AssumptionStatus {
    Verified
    Supported
    Unverified
    Violated
    Unknown
}
```

---

# 348. Assumption Report

Results should include assumption status.

---

# 349. Causal Transportability

Optional provider can reason about transferring causal effects across populations.

---

# 350. Population Context

```axiom
PopulationContext {
    id
    characteristics
}
```

---

# 351. Domain Shift

643 detects/model domain shift.

653 may propagate uncertainty caused by distribution changes.

---

# 352. Covariate Shift

Model metadata may record covariate shift.

---

# 353. Causal Stability

Causal models may declare mechanisms expected to remain stable.

---

# 354. Environment

648 can test causal assumptions across simulated environments.

---

# 355. Invariance

Optional causal provider may test invariant relationships.

---

# 356. Intervention Registry

Interventions are versioned objects.

---

# 357. Intervention Safety

Actual intervention execution is outside 653 and remains subject to 603/639.

---

# 358. Intervention Planning

652 determines sequence/cost/resource allocation for interventions.

---

# 359. Causal + Agent

644 can ask:

```text
What caused this?
What would happen if X changed?
Which evidence would reduce uncertainty?
```

653 computes structured answers.

---

# 360. Agent Uncertainty

Agent memory from 650 can store beliefs with uncertainty.

---

# 361. Agent Belief Revision

New evidence should update or supersede beliefs rather than silently overwrite historical state.

---

# 362. Personalization

651 can provide prior preferences or context.

Preferences are not evidence of factual truth.

---

# 363. Personalization + Causal Model

User preferences may define utility, not causal relationships.

---

# 364. Knowledge Graph + Causal Model

A graph relation may be imported as a causal edge only through explicit declaration or validated model transformation.

---

# 365. Search + Inference

641 can retrieve evidence.

653 evaluates how evidence affects beliefs.

---

# 366. Retrieval Provenance

Retrieved documents remain evidence sources with provenance.

---

# 367. Evidence Freshness

Evidence should include freshness metadata.

---

# 368. Temporal Decay

Applications may explicitly define evidence decay.

653 must not automatically decay evidence without model semantics.

---

# 369. Confidence Decay

Likewise, confidence changes require an explicit model.

---

# 370. Streaming Sensor Inference

614 sensor streams can feed 653.

---

# 371. Event-Driven Belief Update

634 events may trigger inference updates.

---

# 372. Workflow Integration

629 can invoke inference tasks.

---

# 373. Distributed Workflow

630 can distribute expensive inference.

---

# 374. Scheduler Integration

635 may allocate inference resources.

---

# 375. Resource Governor

606 limits sampling and inference budgets.

---

# 376. Checkpointing

600 stores inference checkpoints.

---

# 377. Crash Recovery

605 restarts inference services and resumes checkpoints where possible.

---

# 378. Package Integration

625/613 distribute probabilistic models and inference providers.

---

# 379. Plugin Integration

623 allows optional inference algorithms.

---

# 380. No Mandatory Third-Party Dependency

Native core must support basic:

```text
probability
distributions
Bayesian update
sampling
basic Bayesian networks
basic filtering
```

without external libraries.

---

# 381. Optional Heavy Providers

Advanced:

```text
large MCMC
large probabilistic programming
advanced causal estimation
GPU probabilistic inference
```

may be external providers.

---

# 382. Native Runtime Profiles

```text
AXINFER_NONE
AXINFER_CORE
AXINFER_PROBABILITY
AXINFER_DISTRIBUTION
AXINFER_BAYES
AXINFER_FACTOR
AXINFER_CAUSAL
AXINFER_FILTER
AXINFER_MONTE_CARLO
AXINFER_UNCERTAINTY
AXINFER_DECISION
AXINFER_DISTRIBUTED
AXINFER_AGENT
AXINFER_MULTIMODAL
AXINFER_FULL
```

---

# 383. Compiler Lowering

Probabilistic expressions lower into:

```text
probability IR
factor IR
tensor IR
random IR
causal IR
```

---

# 384. Native Code Generation

Hot probability calculations may compile to native code.

---

# 385. Vectorization

Batch probability calculations should support SIMD.

---

# 386. GPU

Large tensorized factor evaluation can use GPU.

---

# 387. Memory Model

Inference state should favor:

```text
contiguous arrays
compact variable IDs
arena allocation
sparse factor storage
reusable buffers
```

---

# 388. No Mandatory GC

Inference runtime must not require garbage collection.

---

# 389. No Mandatory Borrow Checker

The API should work with Axiom's existing ownership/memory model without introducing a special borrow-checking requirement.

---

# 390. Struct-Only Architecture

Inference objects are ordinary structs.

Example:

```axiom
struct BayesianEngine {}

fn BayesianEngine.infer(
    self,
    model: BayesianNetwork,
    query: Query
) -> InferenceResult
```

---

# 391. Traits

Provider customization uses traits:

```axiom
trait InferenceEngine {
    fn infer(...)
}
```

---

# 392. Static Dispatch

Static dispatch is preferred for known inference engines.

---

# 393. Dynamic Provider Dispatch

Dynamic dispatch is used only when runtime-selected providers are required.

---

# 394. Zero-Cost Abstraction

Static probabilistic models should compile with minimal abstraction overhead.

---

# 395. Model Specialization

Known distributions and graph structures should enable specialization.

---

# 396. Constant Folding

Static probabilities should be folded by compiler.

---

# 397. Compile-Time Validation

Invalid probability constants should fail compilation.

Example:

```text
P = 1.2
```

must be rejected.

---

# 398. Compile-Time Distribution

Small static Bayesian models may be solved at compile time.

---

# 399. Runtime Distribution

Dynamic evidence creates runtime inference.

---

# 400. Decision Pipeline

```text
Observation
    ↓
Evidence
    ↓
653 Inference
    ↓
Belief / Distribution
    ↓
Causal Query
    ↓
Outcome Distribution
    ↓
652 Optimization
    ↓
Decision
```

---

# 401. Uncertainty Pipeline

```text
Input uncertainty
       ↓
Model uncertainty
       ↓
Inference uncertainty
       ↓
Prediction uncertainty
       ↓
Decision uncertainty
```

Each stage retains provenance.

---

# 402. Uncertainty Propagation

If:

```text
A uncertain
B = f(A)
```

the resulting uncertainty of B should be computed rather than discarded.

---

# 403. Monte Carlo Propagation

```axiom
propagate(samples, function)
```

---

# 404. Analytical Propagation

Where closed forms exist, the runtime may use analytical propagation.

---

# 405. Linear Gaussian Propagation

Native optimized path:

```text
mean
covariance
linear transform
```

---

# 406. Nonlinear Propagation

Provider methods:

```text
MonteCarlo
UnscentedTransform
Linearization
```

---

# 407. Error Propagation

Measurement uncertainties can propagate through mathematical functions.

---

# 408. Interval Propagation

Interval arithmetic is an optional exact-bounds mechanism.

---

# 409. Interval Arithmetic

Operations must preserve declared interval semantics.

---

# 410. Dependency Problem

Naive interval arithmetic may overestimate uncertainty when variables are correlated.

The runtime should preserve dependency metadata where possible.

---

# 411. Correlated Uncertainty

Covariance or joint distribution should be retained when available.

---

# 412. Independent Assumption

Independence is an explicit model property.

---

# 413. Conditional Independence

Graphical models can represent conditional independence.

---

# 414. Independence Testing

Statistical evidence may suggest independence but does not automatically establish causal independence.

---

# 415. Model Simplification

Compiler may remove conditionally independent factors where mathematically valid.

---

# 416. Factor Elimination

Variable elimination order affects computational complexity.

---

# 417. Elimination Heuristic

Native heuristics:

```text
MinFill
MinDegree
WeightedMinFill
```

---

# 418. Junction Tree Boundary

Optional exact inference provider.

---

# 419. Treewidth

The compiler/runtime may estimate graph treewidth.

---

# 420. Complexity Diagnostics

Large treewidth should produce a diagnostic warning when relevant.

---

# 421. Approximation Selection

The runtime may recommend approximate inference when exact inference exceeds budget.

It must not silently switch unless approximation is enabled.

---

# 422. Anytime Inference

Sampling algorithms may return progressively improved estimates.

---

# 423. Partial Posterior

Partial inference results must indicate approximation state.

---

# 424. Streaming Posterior

Applications can subscribe to improving estimates.

---

# 425. Convergence

Providers should expose convergence diagnostics.

---

# 426. Stopping Criteria

```text
max iterations
time budget
error tolerance
effective sample size
posterior change
```

---

# 427. Error Estimate

Approximate inference should expose estimated numerical/statistical error when available.

---

# 428. Confidence vs Error

Estimated Monte Carlo error is not confidence in the underlying model.

---

# 429. Model Misspecification

653 may report diagnostics indicating model/data mismatch.

It must not claim the model is causally correct solely from fit.

---

# 430. Posterior Predictive Failure

Poor posterior predictive fit can be reported as a model diagnostic.

---

# 431. Causal Model Validation

Observed data can be compared against causal model predictions.

---

# 432. Interventional Data

If experimental intervention data exists, it may be used to validate causal assumptions.

---

# 433. Observational/Interventional Separation

Data provenance must preserve whether evidence came from observation or intervention.

---

# 434. Experimental Randomization

Random assignment metadata should be retained.

---

# 435. Instrumental Variables

Optional causal provider.

---

# 436. Difference-in-Differences

Optional provider with explicit assumptions:

```text parallel trends
```

---

# 437. Regression Discontinuity

Optional provider with design assumptions.

---

# 438. Synthetic Control

Optional provider.

---

# 439. Matching

Optional provider.

---

# 440. Propensity Score

```axiom
propensity(treatment | covariates)
```

may be represented.

---

# 441. Positivity

Causal estimators requiring positivity must report violations.

---

# 442. Consistency

Causal effect models must declare consistency assumptions where applicable.

---

# 443. SUTVA Boundary

Optional causal model metadata.

---

# 444. Interference

Models may explicitly declare whether units can affect one another.

---

# 445. Network Treatment Effects

If interference exists, causal models can reference 645 graph topology.

---

# 446. Spillover Effects

Provider-level causal models may represent spillovers.

---

# 447. Temporal Treatment

Treatments may occur over time.

---

# 448. Longitudinal Causal Model

```axiom
CausalTimeline {
    observations
    interventions
    confounders
}
```

---

# 449. Dynamic Treatment

Sequential treatments can feed into dynamic causal models.

---

# 450. Causal + Reinforcement Learning

643 RL models can use causal state representations.

653 remains responsible for explicit causal semantics.

---

# 451. Bayesian Decision Theory

653 supplies:

```text
belief
posterior
predictive distribution
```

652 supplies:

```text
decision
utility
constraints
```

---

# 452. Expected Loss

```axiom
expected_loss(decision, distribution)
```

---

# 453. Risk Measures

Supported interfaces:

```text
Expected
Variance
VaR
CVaR
WorstCase
Custom
```

---

# 454. Utility Distribution

The result can retain the full utility distribution.

---

# 455. Decision Robustness

652 can test decisions against 653's uncertainty.

---

# 456. Sensitivity

Decision sensitivity to belief changes should be measurable.

---

# 457. Belief Sensitivity

The runtime may perturb:

```text
priors
likelihood parameters
causal assumptions
```

and recompute outcomes.

---

# 458. Posterior Sensitivity

Results can include how much the posterior changes under alternative priors.

---

# 459. Prior Sensitivity

Bayesian conclusions should expose prior dependence when significant.

---

# 460. Causal Sensitivity

Causal estimates can expose sensitivity to unmeasured confounding where supported.

---

# 461. Uncertainty Report

```axiom
struct UncertaintyReport {
    source
    type
    magnitude
    propagation
    sensitivity
}
```

---

# 462. Belief Report

```axiom
struct BeliefReport {
    posterior
    evidence
    assumptions
    diagnostics
}
```

---

# 463. Causal Report

```axiom
struct CausalReport {
    effect
    identification
    assumptions
    uncertainty
    sensitivity
}
```

---

# 464. Decision Report

653 can provide the uncertainty inputs needed by 652.

---

# 465. Full AI Reasoning Loop

```text
645 Knowledge
      ↓
641 Retrieval
      ↓
650 Memory
      ↓
653 Evidence + Inference
      ↓
643 Prediction
      ↓
653 Uncertainty / Causality
      ↓
651 Preferences
      ↓
652 Decision
      ↓
644 Agent
      ↓
629/630/631 Execution
      ↓
648 Simulation / 642 Observation
      ↓
653 Update
```

---

# 466. Security Invariant

A probabilistic belief cannot grant authority.

---

# 467. Policy Invariant

A causal estimate cannot override 639.

---

# 468. Personalization Invariant

A user preference cannot become factual evidence.

---

# 469. Memory Invariant

A stored belief cannot become ground truth merely because it is persistent.

---

# 470. ML Invariant

A model prediction cannot automatically become causal evidence.

---

# 471. Simulation Invariant

Synthetic evidence must remain marked synthetic.

---

# 472. Retrieval Invariant

Retrieved text is evidence only under an explicit evidence interpretation.

---

# 473. Causal Invariant

Correlation does not imply causation.

---

# 474. Intervention Invariant

Observation and intervention remain distinct.

---

# 475. Probability Invariant

Probability and confidence remain distinct.

---

# 476. Uncertainty Invariant

Unknown must not silently become zero/false.

---

# 477. Approximation Invariant

Approximate inference must be marked approximate.

---

# 478. Convergence Invariant

Non-converged inference cannot be represented as converged.

---

# 479. Provenance Invariant

Every inference result must identify its evidence/model provenance.

---

# 480. Replay Invariant

Reproducible inference requires reproducible inputs and randomness.

---

# 481. Causal Identification Invariant

An unidentified causal effect cannot be returned as a uniquely identified effect.

---

# 482. Assumption Invariant

Causal conclusions must expose relevant assumptions.

---

# 483. Numerical Invariant

Numerical instability must be observable.

---

# 484. Security Invariant

Inference models cannot execute arbitrary code.

---

# 485. Resource Invariant

Inference must respect 606 quotas.

---

# 486. Execution Invariant

Inference cannot directly execute interventions.

---

# 487. Decision Invariant

653 computes uncertainty; 652 computes declared decisions.

---

# 488. Storage Invariant

Inference snapshots obey 600/611/613 lifecycle rules.

---

# 489. Distributed Invariant

Distributed inference preserves mathematical semantics.

---

# 490. Version Invariant

Model/evidence/provider revisions remain attached to results.

---

# 491. Acceptance Criteria — Probability

- [ ] Probability type.
- [ ] Probability validation.
- [ ] LogProbability.
- [ ] Discrete distributions.
- [ ] Continuous distributions.
- [ ] Sampling.
- [ ] CDF.
- [ ] PDF.
- [ ] Quantile.
- [ ] Expectation.
- [ ] Variance.
- [ ] Covariance.
- [ ] Correlation.
- [ ] Entropy.
- [ ] KL divergence.
- [ ] Mutual information.

---

# 492. Acceptance Criteria — Bayesian

- [ ] Prior.
- [ ] Likelihood.
- [ ] Posterior.
- [ ] Evidence.
- [ ] Bayesian update.
- [ ] Bayesian network.
- [ ] Factor graph.
- [ ] Conditional inference.
- [ ] Marginal inference.
- [ ] MAP.
- [ ] MPE.
- [ ] Top-K hypotheses.
- [ ] Exact inference.
- [ ] Approximate inference.
- [ ] Convergence metadata.

---

# 493. Acceptance Criteria — Sequential

- [ ] HMM.
- [ ] Forward.
- [ ] Backward.
- [ ] Viterbi.
- [ ] State-space model.
- [ ] Filtering.
- [ ] Smoothing.
- [ ] Prediction.
- [ ] Particle filter boundary.
- [ ] Incremental evidence.
- [ ] Streaming belief update.

---

# 494. Acceptance Criteria — Causal

- [ ] Causal graph.
- [ ] Structural equations.
- [ ] Exogenous variables.
- [ ] Endogenous variables.
- [ ] Intervention.
- [ ] do-operator.
- [ ] Identification.
- [ ] Adjustment set.
- [ ] ATE.
- [ ] CTE.
- [ ] ITE boundary.
- [ ] Counterfactual.
- [ ] Confounding metadata.
- [ ] Collider diagnostics.
- [ ] Mediation boundary.
- [ ] Causal assumptions.
- [ ] Sensitivity analysis.
- [ ] Partial identification.

---

# 495. Acceptance Criteria — Uncertainty

- [ ] Aleatoric uncertainty.
- [ ] Epistemic uncertainty.
- [ ] Measurement uncertainty.
- [ ] Parameter uncertainty.
- [ ] Interval uncertainty.
- [ ] Distribution uncertainty.
- [ ] Uncertainty propagation.
- [ ] Monte Carlo propagation.
- [ ] Analytical propagation.
- [ ] Risk measures.
- [ ] VaR.
- [ ] CVaR.

---

# 496. Acceptance Criteria — Decision Integration

- [ ] Expected utility.
- [ ] Expected loss.
- [ ] Risk-sensitive decision.
- [ ] Causal decision.
- [ ] Value of information.
- [ ] Experiment design boundary.
- [ ] POMDP boundary.
- [ ] MPC boundary.
- [ ] Belief-state planning.
- [ ] Robust decision.
- [ ] Distributionally robust boundary.

---

# 497. Acceptance Criteria — Compiler

- [ ] Probability syntax.
- [ ] Distribution syntax.
- [ ] Evidence syntax.
- [ ] Bayesian model syntax.
- [ ] Causal model syntax.
- [ ] Intervention syntax.
- [ ] Counterfactual syntax.
- [ ] Probabilistic IR.
- [ ] Causal IR.
- [ ] Static probability validation.
- [ ] Model hashing.
- [ ] AI metadata generation.
- [ ] Dead-code elimination.

---

# 498. Acceptance Criteria — Runtime

- [ ] CPU execution.
- [ ] Optional GPU execution.
- [ ] SIMD execution.
- [ ] Memory-efficient factors.
- [ ] Checkpointing.
- [ ] Replay.
- [ ] Cancellation.
- [ ] Resource budgets.
- [ ] Distributed inference.
- [ ] Provider isolation.
- [ ] Serialization.
- [ ] Observability.
- [ ] Audit.

---

# 499. Mandatory End-to-End Tests

## Test A — Bayes

Given prior and evidence, posterior must be correctly computed.

## Test B — Conflicting Evidence

Two conflicting observations must remain represented and combine according to declared model semantics.

## Test C — Unknown

Missing evidence must not become false.

## Test D — HMM

Forward/backward/Viterbi results must satisfy known reference cases.

## Test E — Intervention

`P(Y | X)` must remain distinct from `P(Y | do(X))`.

## Test F — Unidentified Causal Effect

The engine must return:

```text
NotIdentified
```

rather than fabricate an effect.

## Test G — Counterfactual

A valid causal model must produce a counterfactual result with provenance.

## Test H — Sampling

Seeded sampling must be reproducible.

## Test I — Non-Convergence

Inference exceeding convergence criteria must be marked accordingly.

## Test J — Decision Integration

653 must produce an outcome distribution that 652 can consume.

---

# 500. Performance Requirements

The native implementation SHOULD optimize for:

```text
compact factor storage
contiguous probability arrays
sparse graph traversal
log-space arithmetic
SIMD
batch inference
incremental updates
memory reuse
```

Small models should have extremely low setup overhead.

Large models may use provider implementations.

---

# 501. Dependency Requirements

The native 653 baseline MUST work without:

```text
PyTorch
TensorFlow
JAX
PyMC
Stan
NumPy
SciPy
external causal libraries
```

or other third-party runtimes.

External providers remain optional.

---

# 502. Binary Size

A program using only:

```text
probability
Normal distribution
Bayesian update
```

must not automatically include:

```text
MCMC
GPU runtime
causal estimator providers
distributed runtime
```

unless requested.

---

# 503. Native Profiles

Recommended:

```text
AXINFER_NONE
AXINFER_CORE
AXINFER_PROBABILITY
AXINFER_BAYES
AXINFER_GRAPH
AXINFER_CAUSAL
AXINFER_STATE
AXINFER_MONTE_CARLO
AXINFER_UNCERTAINTY
AXINFER_DECISION
AXINFER_DISTRIBUTED
AXINFER_AGENT
AXINFER_MULTIMODAL
AXINFER_FULL
```

---

# 504. Core Invariants

653 must guarantee at minimum:

1. probabilities are valid;
2. invalid distributions are rejected;
3. unknown differs from false;
4. observation differs from intervention;
5. correlation differs from causation;
6. probability differs from confidence;
7. evidence retains provenance;
8. synthetic evidence remains synthetic;
9. posterior retains model revision;
10. approximate inference is marked;
11. non-convergence is marked;
12. causal assumptions are retained;
13. unidentified effects are not fabricated;
14. counterfactuals require causal semantics;
15. causal estimates retain uncertainty;
16. numerical instability is observable;
17. random inference can be reproduced when seeded;
18. future data cannot silently leak into historical inference;
19. resource limits are enforced;
20. inference cannot grant authority;
21. inference cannot bypass policy;
22. inference cannot bypass security;
23. beliefs cannot become truth merely through persistence;
24. ML predictions remain predictions;
25. simulation data remains synthetic;
26. retrieval evidence remains provenance-tagged;
27. utility remains distinct from probability;
28. decision optimization remains 652's responsibility;
29. inference results remain versioned;
30. provider behavior remains auditable.

---

# 505. Final Architecture

```text
                         WORLD
                           │
                           ▼
                     OBSERVATIONS
                           │
             ┌─────────────┼─────────────┐
             │             │             │
           Sensors       Search        Memory
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │     653      │
                    │  INFERENCE   │
                    └──────┬───────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
      Probability       Bayesian          Causal
       Reasoning        Inference         Reasoning
          │                │                 │
          └────────────────┼─────────────────┘
                           │
                    ┌──────▼──────┐
                    │    Belief   │
                    │    State    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Prediction │
                    └──────┬──────┘
                           │
                     651 Preference
                           │
                    ┌──────▼──────┐
                    │     652     │
                    │   DECISION  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    PLAN     │
                    └──────┬──────┘
                           │
                    629 / 630 / 631
                           │
                       EXECUTION
                           │
                       OBSERVE
                           │
                           └──────────► 653
```

---

# 506. Axiom AI Architecture After 653

The major AI layers now have a clean division:

```text
641  = SEARCH / RETRIEVAL
642  = ANALYTICS
643  = LEARN / PREDICT
644  = AGENT
645  = KNOWLEDGE
646  = EVALUATE
647  = GOVERN
648  = SIMULATE
649  = MULTIMODAL
650  = REMEMBER
651  = PERSONALIZE
652  = DECIDE / OPTIMIZE
653  = INFER / CAUSE / UNCERTAINTY
```

The resulting reasoning pipeline is:

```text
OBSERVE
   ↓
RETRIEVE / REMEMBER
   ↓
KNOW
   ↓
PREDICT
   ↓
INFER
   ↓
UNDERSTAND CAUSAL EFFECTS
   ↓
PERSONALIZE
   ↓
DECIDE
   ↓
PLAN
   ↓
EXECUTE
   ↓
OBSERVE
```

This creates the foundation for a substantially more capable native AI stack without collapsing all AI functionality into a single opaque "AI runtime."

---

# 507. Completion Criteria

BOOTSTRAP-653 is COMPLETE when:

1. probability semantics are frozen;
2. distribution model is frozen;
3. evidence model is frozen;
4. Bayesian model is frozen;
5. factor model is frozen;
6. inference provider boundary is frozen;
7. uncertainty model is frozen;
8. causal graph semantics are frozen;
9. intervention semantics are frozen;
10. counterfactual semantics are frozen;
11. causal identification boundary is frozen;
12. assumption/provenance model is frozen;
13. decision-under-uncertainty boundary with 652 is frozen;
14. compiler IR requirements are frozen;
15. memory/performance architecture is frozen;
16. security/governance boundaries are frozen;
17. acceptance tests are defined;
18. native dependency-free baseline is defined;
19. Axiom struct/trait architecture is respected;
20. AI-readable metadata is defined.

**Status: COMPLETE**

---

# 508. Next Architecture Task

## BOOTSTRAP-654

**Native AI World Model, State Estimation, Predictive Environment Model, Temporal Reasoning, Dynamics, Belief-State Simulation & Model-Based Intelligence Runtime 5.0**

653 provides:

```text
belief
probability
causal inference
uncertainty
```

652 provides:

```text
decision
optimization
planning
```

The next layer should establish a persistent **world model** that represents how entities, environments and systems evolve over time:

```text
WORLD STATE
    ↓
OBSERVE
    ↓
ESTIMATE STATE
    ↓
PREDICT FUTURE STATE
    ↓
SIMULATE
    ↓
653 UNCERTAINTY / CAUSAL INFERENCE
    ↓
652 DECISION
    ↓
ACTION
    ↓
WORLD STATE UPDATE
```

This becomes the foundation for model-based agents, robotics, autonomous systems, digital twins, predictive control, long-horizon planning and increasingly capable Axiom-native AI.

**BOOTSTRAP-653 — COMPLETE.**
:::