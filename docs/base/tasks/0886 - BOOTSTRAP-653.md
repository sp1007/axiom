Tiếp tục với **BOOTSTRAP-653 — Native AI Probabilistic Reasoning, Bayesian Inference, Causal Modeling, Uncertainty Quantification, Risk Analysis & Decision-under-Uncertainty Runtime 5.0**.

:::writing{variant="document" id="74106" title="BOOTSTRAP-653 — Native AI Probabilistic Reasoning, Bayesian Inference, Causal Modeling, Uncertainty Quantification, Risk Analysis & Decision-under-Uncertainty Runtime 5.0"}
# BOOTSTRAP-653
## Native AI Probabilistic Reasoning, Bayesian Inference, Causal Modeling, Uncertainty Quantification, Risk Analysis & Decision-under-Uncertainty Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Probabilistic & Causal Reasoning Plane  
**Priority:** P0  
**Version:** 5.0  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-652

---

# 1. Purpose

BOOTSTRAP-653 defines Axiom's native substrate for reasoning when information is incomplete, noisy, uncertain, probabilistic, observational, experimental, or causally structured.

It provides:

- probability distributions
- random variables
- Bayesian inference
- likelihood models
- posterior inference
- conditional probability
- probabilistic graphical models
- Bayesian networks
- factor graphs
- Markov models
- hidden-state models
- probabilistic programs
- Monte Carlo inference
- importance sampling
- sequential Monte Carlo
- MCMC provider boundary
- variational inference provider boundary
- approximate inference
- uncertainty propagation
- confidence/credible intervals
- prediction intervals
- calibration
- causal graphs
- structural causal models
- interventions
- counterfactual reasoning
- treatment effects
- mediation
- confounding analysis
- causal discovery provider boundary
- risk modeling
- expected utility
- decision under uncertainty
- robust decision support
- probabilistic constraints
- scenario generation
- uncertainty-aware planning integration with 652
- simulation integration with 648
- ML integration with 643
- knowledge integration with 645
- agent integration with 644
- evaluation/calibration integration with 646.

The subsystem MUST distinguish mathematical probability from heuristic confidence, model assumptions from observed facts, and causal claims from correlations.

---

# 2. Architectural Position

```text id="qv3n5r"
                  Data / Sensors / Events
                           │
                           ▼
                   Evidence / Observations
                           │
            ┌──────────────▼──────────────┐
            │       653 Reasoning         │
            │ Probability / Causality     │
            └──────────────┬──────────────┘
                           │
       ┌───────────────────┼────────────────────┐
       ▼                   ▼                    ▼
   Bayesian            Causal              Uncertainty
   Inference           Models              Propagation
       │                   │                    │
       └───────────────────┼────────────────────┘
                           ▼
                      Risk Analysis
                           │
                           ▼
                 Decision-under-Uncertainty
                           │
                           ▼
                         652
                           │
                           ▼
                 Plan / Decision / Action
```

---

# 3. Boundary With Existing Systems

| System | Primary responsibility |
|---|---|
| 643 | ML models and prediction |
| 645 | knowledge graphs and semantic relationships |
| 648 | simulation and synthetic environments |
| 650 | memory/context |
| 651 | personalization/preferences |
| 652 | optimization/planning/constraint solving |
| **653** | **probability, causal inference, uncertainty and risk reasoning** |
| 646 | evaluation/calibration/testing |
| 639 | policy/authorization |
| 640 | governance |
| 644 | agent orchestration |

653 may consume predictions from 643, but it provides the semantics needed to represent uncertainty around those predictions.

---

# 4. Core Principle

Axiom MUST distinguish:

```text id="j75j9y"
observed fact
model assumption
probabilistic estimate
causal claim
heuristic confidence
simulation estimate
decision preference
```

These are not interchangeable.

---

# 5. Probability Model

The fundamental probability type:

```text id="5ozc7x"
Probability
```

with semantic range:

```text
0 <= p <= 1
```

Invalid values MUST fail validation.

---

# 6. Random Variable

```text id="5l8g8j"
RandomVariable<T> {
    domain
    distribution
    provenance
}
```

Example:

```text id="9s8qz5"
temperature ~ Normal(25, 3)
```

---

# 7. Distribution

```text id="6u5v6y"
Distribution<T> {
    sample()
    density(x)
    log_density(x)
    probability(event)
    expectation()
    variance()
}
```

---

# 8. Distribution Families

Native baseline:

```text id="f3s3gs"
Bernoulli
Categorical
Uniform
DiscreteUniform
Binomial
Poisson
Geometric
Normal
LogNormal
Exponential
Gamma
Beta
StudentT
Laplace
Logistic
```

Advanced distributions may be providers.

---

# 9. Distribution Composition

Distributions may be transformed:

```text id="xqjv0o"
X ~ Normal(...)
Y = f(X)
```

653 tracks transformation metadata.

---

# 10. Joint Distribution

```text id="l2x1i9"
JointDistribution<X,Y>
```

supports:

```text id="r2f8xw"
P(X,Y)
```

and marginals:

```text id="z7h7gt"
P(X)
P(Y)
```

---

# 11. Conditional Distribution

```text id="xj7c8r"
P(X | Y)
```

is a first-class representation.

---

# 12. Conditional Independence

The model may declare:

```text id="n6g48g"
X ⟂ Y | Z
```

The compiler/runtime may exploit such structure for efficient inference.

---

# 13. Bayes Rule

653 provides:

```text id="2l5y2f"
P(A|B) =
    P(B|A) * P(A)
    / P(B)
```

The runtime SHOULD provide numerically stable implementations.

---

# 14. Evidence

```text id="0d9qf2"
Evidence {
    variable
    observed_value
    timestamp
    source
    confidence?
    provenance
}
```

Evidence is distinct from model assumptions.

---

# 15. Observation

An observation is a value actually observed from a source.

It MUST retain:

```text id="w7m9k4"
source
time
revision
measurement metadata
```

---

# 16. Likelihood

```text id="5h2c1d"
Likelihood(parameters | observations)
```

is represented separately from posterior distributions.

---

# 17. Prior

```text id="1x3qbt"
Prior<T>
```

may originate from:

```text id="u7z7jx"
domain knowledge
historical data
previous posterior
hierarchical model
default model
```

Its provenance MUST be preserved.

---

# 18. Posterior

```text id="5m4h4s"
Posterior<T>
```

is derived from:

```text id="j0i2sp"
prior + likelihood + evidence
```

The system MUST retain references to the contributing model and evidence.

---

# 19. Bayesian Update

Conceptual API:

```text id="d8t2eq"
posterior = bayes.update(
    prior,
    likelihood,
    evidence
)
```

---

# 20. Sequential Bayesian Update

A posterior may become a new prior:

```text id="w8l6d0"
prior_1
   ↓ evidence_1
posterior_1
   ↓ evidence_2
posterior_2
```

Each update creates a new revision.

---

# 21. Immutable Inference

Inference inputs SHOULD remain immutable.

Output is a new inference artifact.

---

# 22. Probabilistic Model

```text id="9y8c0h"
ProbabilisticModel {
    variables
    distributions
    dependencies
    observations
    assumptions
}
```

---

# 23. Graphical Models

Supported abstractions:

```text id="6o5b4n"
BayesianNetwork
MarkovRandomField
FactorGraph
ConditionalRandomField
HiddenMarkovModel
DynamicBayesianNetwork
```

---

# 24. Bayesian Network

Directed acyclic graph:

```text id="7v7b2y"
A → B → C
```

with conditional probability distributions attached to nodes.

---

# 25. DAG Requirement

A Bayesian network MUST be acyclic.

Cycles require a different model class.

---

# 26. Factor Graph

```text id="g2g1mw"
Variable nodes
      │
      ▼
Factor nodes
```

A factor defines a local contribution to the joint distribution.

---

# 27. Factor

```text id="b6x0h4"
Factor {
    variables
    function
    normalization
}
```

---

# 28. Markov Random Field

Undirected probabilistic dependencies are represented separately from causal DAGs.

---

# 29. Hidden Markov Model

```text id="q4z5kv"
hidden_state_t
      ↓
observation_t
```

with:

```text id="3k8v2h"
initial distribution
transition distribution
emission distribution
```

---

# 30. Dynamic Bayesian Network

Time-indexed probabilistic dependencies:

```text id="6m9t6a"
X_t → X_t+1
X_t → Y_t
```

---

# 31. Inference Queries

Native query forms:

```text id="1u6c0q"
marginal(X)
conditional(X | evidence)
joint(X,Y)
expectation(f(X))
variance(X)
probability(event)
most_likely(X)
```

---

# 32. Exact Inference

For tractable models:

```text id="u4h3r1"
variable elimination
belief propagation
junction tree
enumeration
```

may be implemented natively.

---

# 33. Approximate Inference

Provider/runtime boundary:

```text id="v9e2cc"
MonteCarlo
ImportanceSampling
RejectionSampling
MCMC
VariationalInference
SequentialMonteCarlo
```

---

# 34. Monte Carlo

```text id="g4j2z4"
samples = sample(model, N)
```

Outputs MUST include:

```text id="b4b3l2"
sample_count
seed
estimator
standard_error?
```

---

# 35. Importance Sampling

```text id="j7d0p1"
weight_i =
    target(x_i) / proposal(x_i)
```

The runtime MUST track effective sample size where applicable.

---

# 36. Sequential Monte Carlo

Supports evolving systems:

```text id="h7w4ax"
predict
weight
resample
propagate
```

---

# 37. MCMC Provider

Provider interface:

```text id="s7f0m1"
MCMCProvider
```

Metadata:

```text id="h1k7qq"
chain_count
warmup
samples
seed
diagnostics
```

---

# 38. MCMC Diagnostics

Where supported:

```text id="d0t4nx"
R-hat
effective_sample_size
autocorrelation
divergence_count
```

---

# 39. Variational Inference

Provider boundary:

```text id="m8k4s6"
VariationalFamily
ELBO
optimizer
convergence
```

---

# 40. Inference Status

```text id="w9t8u2"
Exact
Approximate
Converged
NotConverged
Timeout
Cancelled
Unknown
```

---

# 41. Approximation Metadata

Every approximate inference result MUST record:

```text id="r6v5hp"
method
seed
sample_count
tolerance
convergence
error_estimate?
```

---

# 42. No False Precision

The runtime MUST NOT expose excessive numerical precision beyond the method's justified accuracy.

---

# 43. Uncertainty Representation

Supported forms:

```text id="z5f0ym"
Probability
Variance
StandardDeviation
Interval
CredibleInterval
PredictionInterval
Quantile
Distribution
Covariance
Correlation
```

---

# 44. Credible Interval

A Bayesian interval:

```text id="y4y4r2"
P(theta ∈ interval | evidence) = 0.95
```

must not be mislabeled as a frequentist confidence interval.

---

# 45. Confidence Interval

Frequentist confidence intervals are represented separately:

```text id="7f1r0w"
ConfidenceInterval
```

with method metadata.

---

# 46. Prediction Interval

Prediction uncertainty for future observations:

```text id="4g3l9s"
PredictionInterval
```

is distinct from parameter uncertainty.

---

# 47. Quantiles

```text id="d5f7e8"
quantile(distribution, q)
```

requires:

```text id="x4r2u9"
0 <= q <= 1
```

---

# 48. Expectation

```text id="3f9s5g"
E[X]
```

may be computed exactly or approximately.

---

# 49. Variance

```text id="0p9j5x"
Var(X)
```

must preserve numerical method metadata when estimated.

---

# 50. Covariance

```text id="y8m6i2"
Cov(X,Y)
```

supports uncertainty propagation.

---

# 51. Correlation

Correlation MUST be distinguished from causation.

---

# 52. Causal Model

```text id="7b8j1w"
CausalModel {
    variables
    causal_graph
    structural_equations
    exogenous_variables
    assumptions
}
```

---

# 53. Causal DAG

A causal graph:

```text id="w0r8c3"
Treatment → Outcome
      ↓
   Mediator
```

is explicitly distinct from a correlation graph.

---

# 54. Causal Claim

A causal relationship MUST carry:

```text id="3g2k8n"
claim
assumptions
identification_method
evidence
model_revision
```

---

# 55. Observational vs Interventional

653 distinguishes:

```text id="3s7f2j"
P(Y | X)
```

from:

```text id="8c5x6a"
P(Y | do(X=x))
```

The former is observational conditioning.

The latter represents intervention.

---

# 56. Intervention

```text id="m8s7a0"
intervene(model, X = x)
```

returns an interventional model.

---

# 57. Structural Causal Model

```text id="q5v8z2"
X = f_X(U_X)
Y = f_Y(X, U_Y)
```

where `U` represents exogenous variables.

---

# 58. Counterfactual

```text id="4p3v1y"
counterfactual(
    factual_state,
    intervention,
    query
)
```

requires a causal model.

---

# 59. Counterfactual Separation

Counterfactual results MUST NOT be produced from a correlation model unless a valid causal identification bridge is explicitly provided.

---

# 60. Potential Outcomes

Provider/model abstraction:

```text id="v5t9n3"
Y(0)
Y(1)
```

with treatment-effect estimands.

---

# 61. Average Treatment Effect

```text id="c9p2g1"
ATE = E[Y(1) - Y(0)]
```

must retain identification assumptions.

---

# 62. Conditional Treatment Effect

```text id="m2f4k8"
CATE(X)
```

supports heterogeneous effects.

---

# 63. Average Treatment Effect on Treated

```text id="k4r7s2"
ATT
```

is represented distinctly from ATE.

---

# 64. Confounding

A confounder may affect both treatment and outcome:

```text id="t6y9q3"
Z → X
Z → Y
```

653 models confounding explicitly.

---

# 65. Adjustment Set

A causal query may specify:

```text id="x4j7h9"
adjust_for = {Z1, Z2}
```

The engine MUST validate adjustment assumptions.

---

# 66. Backdoor Criterion

Causal identification providers MAY expose:

```text id="d8v3r1"
find_adjustment_set(graph, treatment, outcome)
```

---

# 67. Frontdoor Identification

Provider MAY support frontdoor identification.

---

# 68. Instrumental Variables

Provider boundary:

```text id="p6w2z8"
InstrumentalVariable
```

with explicit assumptions.

---

# 69. Mediation

Model:

```text id="v2h6m9"
X → M → Y
```

can estimate direct/indirect effects when identification assumptions permit.

---

# 70. Causal Discovery

Causal discovery is an inference task, not a guaranteed fact.

Provider output:

```text id="s1k4d7"
CandidateCausalGraph
```

MUST include uncertainty/assumption metadata.

---

# 71. Discovery Methods

Provider boundary may support:

```text id="n3b5k7"
constraint_based
score_based
functional_causal
time_series
```

---

# 72. Discovery Output

A discovered graph MUST be distinguishable from a graph supplied as established domain knowledge.

---

# 73. Causal Graph Provenance

```text id="a7d2f5"
source
dataset
method
assumptions
score
uncertainty
revision
```

---

# 74. Temporal Causality

Time ordering may provide constraints but does not automatically prove causality.

---

# 75. Intervention Data

Experimental observations SHOULD be marked:

```text id="j8s6n4"
interventional = true
```

with intervention description.

---

# 76. Randomized Experiments

Experiment metadata:

```text id="r2f7m9"
treatment_assignment
randomization_scheme
population
outcome
```

---

# 77. Causal Effect Uncertainty

Treatment-effect estimates MUST expose:

```text id="c4v8k1"
estimate
uncertainty
method
sample_size
assumptions
```

---

# 78. Missing Data

653 MUST explicitly model missingness.

Categories:

```text id="w6p1x3"
MCAR
MAR
MNAR
unknown
```

---

# 79. Missingness Model

A missing value MUST NOT automatically be interpreted as zero, false, or negative evidence.

---

# 80. Measurement Error

Observation models can represent:

```text id="q8m3y5"
true_value
measurement
noise
```

---

# 81. Sensor Fusion

Multiple observations may be combined probabilistically.

```text id="g2k7m4"
sensor_A
sensor_B
sensor_C
       ↓
posterior_state
```

---

# 82. Evidence Weight

Evidence reliability can be modeled explicitly.

It MUST NOT be silently converted into arbitrary probability values.

---

# 83. Calibration

653 integrates with 646 to measure:

```text id="e6t3p2"
calibration
Brier score
log loss
ECE
reliability
coverage
```

---

# 84. Calibration ≠ Accuracy

A probabilistic model may be calibrated even when its point predictions are imperfect.

---

# 85. Probability Calibration

Providers may implement:

```text id="u4r7x1"
PlattScaling
IsotonicRegression
TemperatureScaling
BetaCalibration
```

---

# 86. Proper Scoring Rules

Supported:

```text id="n5h2z8"
LogLoss
BrierScore
CRPS
```

---

# 87. Risk Model

```text id="m9f4s2"
RiskModel {
    hazards
    probabilities
    impacts
    correlations
    time_horizon
}
```

---

# 88. Risk Event

```text id="k7d3x1"
RiskEvent {
    probability
    impact
    timing
    dependencies
}
```

---

# 89. Expected Loss

```text id="r8p6v4"
E[Loss] = Σ P(event) * impact(event)
```

For continuous distributions, integration is used.

---

# 90. Tail Risk

Supported metrics:

```text id="q3m8y5"
VaR
CVaR
ExpectedShortfall
quantile_loss
```

where mathematically applicable.

---

# 91. Risk Aggregation

Correlated risks MUST NOT automatically be summed as independent.

---

# 92. Dependency-Aware Risk

Risk models can represent:

```text id="z4v7k2"
event_A → event_B
```

or shared latent causes.

---

# 93. Fault Trees

Provider/native representation:

```text id="p2k5m8"
AND gate
OR gate
XOR gate
basic event
```

---

# 94. Event Trees

Event sequences may represent branching outcomes.

---

# 95. Reliability

Native concepts:

```text id="t8q3y7"
failure_probability
survival_probability
hazard_rate
reliability
```

---

# 96. Markov Reliability Models

State transitions may model system reliability over time.

---

# 97. Availability

```text id="s7n4k2"
availability = uptime / total_time
```

may be modeled probabilistically.

---

# 98. Bayesian Updating of Reliability

Observed failures can update prior reliability distributions.

---

# 99. Decision Utility

```text id="x6f2m8"
Utility(action, outcome)
```

maps outcomes to explicit utility values.

---

# 100. Expected Utility

```text id="c3y7v5"
EU(action) = Σ P(outcome | action) * U(outcome)
```

---

# 101. Decision Under Uncertainty

653 can produce:

```text id="h8m4z2"
ExpectedUtility
RiskAdjustedUtility
RobustUtility
UtilityDistribution
```

for consumption by 652.

---

# 102. Separation From 652

653 estimates uncertainty and utility under uncertainty.

652 selects feasible actions according to explicit decision objectives/constraints.

```text id="w5n9k1"
653 → uncertain outcome model
       ↓
652 → constrained action selection
```

---

# 103. Chance Constraints

```text id="j4s8m6"
P(constraint(x, uncertainty)) >= threshold
```

requires an explicit probability model.

---

# 104. Probabilistic Constraint Evaluation

The runtime may calculate:

```text id="r6y2p8"
probability_of_violation
```

instead of treating an uncertain constraint as deterministic.

---

# 105. Robust Constraint

Alternative:

```text id="k7x4m2"
constraint must hold for all values in uncertainty_set
```

---

# 106. Risk Constraint

Example:

```text id="v5c9n3"
CVaR(loss) <= threshold
```

---

# 107. Scenario Interface to 652

```text id="m8q3z6"
DecisionScenario {
    parameters
    probability?
    uncertainty_set?
}
```

652 may optimize across scenarios generated by 653.

---

# 108. Scenario Generation

653 may generate:

```text id="t2y7p4"
MonteCarloScenario
QuasiRandomScenario
PosteriorScenario
StressScenario
AdversarialScenario
```

Stress/adversarial scenarios MUST be labeled appropriately.

---

# 109. Scenario Provenance

Every generated scenario records:

```text id="g4k9m2"
generator
seed
model
revision
parameters
```

---

# 110. Stress Testing

Stress tests intentionally explore adverse conditions.

They MUST NOT be interpreted as probability-weighted forecasts unless explicitly modeled.

---

# 111. Sensitivity Analysis

```text id="z7m3q8"
sensitivity(parameter, outcome)
```

can determine which assumptions most affect results.

---

# 112. Local Sensitivity

Derivative-based sensitivity where differentiability exists.

---

# 113. Global Sensitivity

Provider methods:

```text id="p4n8y6"
Sobol
Morris
variance_based
```

---

# 114. Uncertainty Decomposition

Total uncertainty may be separated into:

```text id="j6r2x9"
aleatoric
epistemic
measurement
model
parameter
sampling
```

Definitions MUST remain explicit.

---

# 115. Aleatoric Uncertainty

Irreducible variability in the modeled process.

---

# 116. Epistemic Uncertainty

Uncertainty arising from incomplete knowledge/model parameters.

---

# 117. Model Uncertainty

Alternative model structures may be represented explicitly.

---

# 118. Ensemble Uncertainty

Multiple models can produce:

```text id="s5k8m3"
model_distribution
```

rather than an unsupported single certainty estimate.

---

# 119. Bayesian Model Averaging

Provider:

```text id="u2n6x7"
model_posterior
```

with explicit model weights.

---

# 120. Hierarchical Bayesian Models

Support:

```text id="r4y8p1"
population
group
individual
```

levels.

---

# 121. Partial Pooling

Hierarchical models SHOULD preserve group-level and global uncertainty.

---

# 122. Prior Predictive Check

```text id="b7m3q9"
sample(prior)
compare_with_observed()
```

---

# 123. Posterior Predictive Check

```text id="n6x4r8"
sample(posterior_predictive)
compare()
```

---

# 124. Model Checking

Model diagnostics integrate with 646.

---

# 125. Bayesian Evidence

Where supported:

```text id="k3p8v6"
marginal_likelihood
BayesFactor
```

must identify numerical method.

---

# 126. Bayes Factor

A Bayes factor MUST preserve model pair identity.

---

# 127. Likelihood Ratio

Likelihood ratios are distinct from posterior odds.

---

# 128. Odds

```text id="f8m2z5"
odds(p) = p / (1-p)
```

---

# 129. Log Odds

Numerically stable log-odds representation is recommended.

---

# 130. Numerical Stability

Probability computations SHOULD use:

```text id="v3n7k4"
log-space
log-sum-exp
stable normalization
```

where appropriate.

---

# 131. Underflow Prevention

Tiny probabilities SHOULD remain representable through log probability.

---

# 132. Log Probability

```text id="y6p4r2"
LogProbability
```

is a first-class numerical representation.

---

# 133. Probability Semantics

`Probability` and `LogProbability` MUST NOT be interchangeable without explicit conversion.

---

# 134. Random Seed

All stochastic algorithms support explicit:

```text id="h2m7x9"
Seed
RandomStream
```

---

# 135. Independent Random Streams

Parallel sampling requires independent deterministic substreams.

---

# 136. Reproducible Sampling

Same:

```text id="q8v3m5"
model
seed
algorithm
version
```

must produce reproducible samples within the declared reproducibility profile.

---

# 137. Sampling Budget

```text id="c5y7n2"
max_samples
max_time
max_memory
max_chains
```

---

# 138. Adaptive Sampling

Sampling may continue until:

```text id="j4p8x6"
error <= tolerance
```

or budget exhaustion.

---

# 139. Monte Carlo Error

Estimated quantities SHOULD expose standard error or confidence/credible uncertainty when mathematically justified.

---

# 140. Effective Sample Size

Sampling methods SHOULD expose ESS where applicable.

---

# 141. Convergence

Convergence criteria MUST be explicit.

---

# 142. Non-Convergence

Non-converged inference MUST NOT be presented as converged.

---

# 143. Approximate Posterior

Approximate posterior artifacts carry:

```text id="r7k3m8"
method
approximation_family
convergence
diagnostics
```

---

# 144. Causal Identification Status

Causal query results:

```text id="y5p2n7"
Identified
PartiallyIdentified
NotIdentified
AssumptionDependent
```

---

# 145. Partial Identification

If data/assumptions identify only bounds:

```text id="z8m4q6"
EffectInterval
```

must be returned instead of a fabricated point estimate.

---

# 146. Causal Bounds

Provider may return:

```text id="c2x7p9"
lower_bound
upper_bound
assumptions
```

---

# 147. Causal Assumption Registry

```text id="h6n3v8"
CausalAssumption {
    id
    description
    formal_condition
    evidence
}
```

---

# 148. Assumption Validation

A causal result must expose its assumptions.

---

# 149. Do-Calculus Provider

Advanced provider may expose:

```text id="m7r2y5"
identify(query, graph)
```

---

# 150. Causal Query Language

Example:

```text id="p8k4n6"
causal {
    effect of treatment on outcome
    adjust_for { age, baseline }
}
```

---

# 151. Counterfactual Query Language

```text id="x4m7q2"
counterfactual {
    if treatment = 1
    what is outcome?
}
```

requires a causal model.

---

# 152. Causal Transportability

Provider may support:

```text id="v6p3y8"
transport_effect(source_population, target_population)
```

with explicit assumptions.

---

# 153. Domain Shift

Distribution changes between training and deployment can be represented as:

```text id="k2r8m5"
distribution_shift
```

---

# 154. Covariate Shift

Explicitly modeled separately from concept drift.

---

# 155. Concept Drift

Outcome mechanism changes are represented explicitly.

---

# 156. Drift Detection

646/643 may provide:

```text id="n4y7p2"
drift_score
detected_at
method
```

653 can update uncertainty models accordingly.

---

# 157. Temporal Probability

Time-dependent distributions:

```text id="z6m3x8"
P(X_t | history)
```

---

# 158. Survival Analysis

Provider/native concepts:

```text id="s4p8n2"
survival_function
hazard_function
cumulative_hazard
```

---

# 159. Competing Risks

Multiple failure causes can be represented.

---

# 160. Time-to-Event

```text id="y7r2m6"
TimeToEventDistribution
```

---

# 161. Bayesian Filtering

For dynamic state estimation:

```text id="q5n8x3"
predict
update
normalize
```

---

# 162. Kalman Filter Boundary

Native/provider support:

```text id="k8m4p7"
Kalman
ExtendedKalman
UnscentedKalman
```

where model assumptions apply.

---

# 163. Particle Filter

```text id="v3x7n9"
ParticleFilter
```

for nonlinear/non-Gaussian state estimation.

---

# 164. State Estimation

653 may provide posterior state estimates to:

```text id="p6m2y8"
648 simulation
652 planning
644 agents
```

---

# 165. Sensor Uncertainty

Sensor observations include:

```text id="g8r4n5"
noise_model
calibration
timestamp
quality
```

---

# 166. Sensor Fusion

Fusion must preserve source identity.

---

# 167. Evidence Conflict

If sensors disagree:

```text id="n2x7m5"
conflict_score
source_reliability
posterior_uncertainty
```

may be exposed.

---

# 168. Outlier Handling

Outlier treatment must be explicit.

The runtime MUST NOT silently discard observations.

---

# 169. Robust Statistics

Provider/native methods:

```text id="y4p8m2"
Huber
Tukey
median_based
trimmed
```

---

# 170. Probability Forecasting

Forecasts include:

```text id="r6m3x9"
forecast_distribution
forecast_horizon
calibration_metadata
```

---

# 171. Forecast Evaluation

646 can evaluate:

```text id="k7n4p2"
coverage
sharpness
calibration
log_score
CRPS
```

---

# 172. Uncertainty-Aware ML

643 model outputs may include:

```text id="x8m5r3"
point_estimate
predictive_distribution
uncertainty
```

653 standardizes the latter.

---

# 173. Probabilistic Model Registry

647 manages:

```text id="n3y7p8"
model identity
version
approval
deployment
rollback
```

---

# 174. Model Lifecycle

653 inference artifacts reference 647 model versions.

---

# 175. Model Governance

640 applies to probabilistic models and causal models.

---

# 176. Causal Model Governance

Causal assumptions are governance metadata.

---

# 177. Sensitive Variables

Protected/sensitive variables may require special policy controls.

---

# 178. Fairness Analysis

653 may provide statistical quantities for 646 fairness evaluation.

It MUST NOT independently declare a policy conclusion.

---

# 179. Group Conditional Distributions

```text id="p4m8x2"
P(Y | group)
```

may be computed with governance controls.

---

# 180. Distribution Comparison

Support:

```text id="r7n3y6"
KL
JS
Wasserstein
KS
```

where applicable.

---

# 181. Divergence Semantics

Divergence metrics MUST identify directionality where relevant.

---

# 182. Entropy

```text id="x5m8q2"
H(X)
```

---

# 183. Conditional Entropy

```text id="g3p7n9"
H(X|Y)
```

---

# 184. Mutual Information

```text id="v8r4m2"
I(X;Y)
```

Mutual information is statistical dependence, not causal influence.

---

# 185. Information Gain

Used for:

```text id="j6n3x7"
active learning
experiment selection
sensor selection
```

---

# 186. Value of Information

Decision analysis may compute:

```text id="q4m8p2"
EVPI
EVSI
```

where assumptions permit.

---

# 187. Experiment Design

653 may model:

```text id="z7n3r5"
candidate experiment
expected information gain
expected utility
cost
risk
```

---

# 188. Active Learning Integration

643 may use 653 uncertainty to select data acquisition targets.

---

# 189. Agent Integration

644 agents may ask:

```text id="m5x8q3"
what is uncertain?
what evidence would reduce uncertainty?
what is the expected risk?
what intervention changes the outcome?
```

---

# 190. Agent Evidence Contract

Agents receive:

```text id="p7n4y2"
beliefs
uncertainty
provenance
assumptions
```

not fabricated certainty.

---

# 191. Memory Integration

650 may store:

```text id="x3m8r6"
posterior revisions
evidence
causal assumptions
risk assessments
```

with appropriate lifecycle metadata.

---

# 192. Personalization Integration

651 may provide user-specific priors only when explicitly configured.

Personalization MUST NOT silently alter factual causal claims.

---

# 193. Knowledge Integration

645 may provide prior structural knowledge:

```text id="n8p3y5"
known relationships
ontology
domain constraints
```

653 distinguishes these from empirically inferred relationships.

---

# 194. Simulation Integration

648 can generate:

```text id="r5m7x2"
posterior predictive scenarios
stress scenarios
counterfactual environments
```

---

# 195. Decision Integration

652 receives:

```text id="v6n3p8"
expected outcomes
risk
probabilistic constraints
scenario distributions
utility
```

---

# 196. Risk-Aware Optimization

652 may optimize:

```text id="k4m8y3"
expected_cost
worst_case_cost
CVaR
probability_of_violation
```

provided 653 supplies the corresponding uncertainty model.

---

# 197. Chance-Constrained Optimization

Pipeline:

```text id="q7n3r6"
653:
    uncertainty model
       ↓
probability constraint
       ↓
652:
    optimization
```

---

# 198. Robust Optimization

Pipeline:

```text id="m5x8p2"
653:
    uncertainty set
       ↓
652:
    robust constraints/objectives
```

---

# 199. Decision Risk Report

```text id="z4r7n3"
RiskReport {
    expected_loss
    quantiles
    tail_risk
    probability_of_failure
    scenarios
    assumptions
}
```

---

# 200. Decision Utility Report

```text id="x8m3q6"
UtilityReport {
    expected_utility
    utility_distribution
    risk_adjusted_utility
}
```

---

# 201. Uncertainty Budget

Applications may specify:

```text id="n6p4y8"
max_allowed_uncertainty
```

for a decision.

---

# 202. Evidence Threshold

Applications may require:

```text id="r3m7x5"
minimum_evidence_quality
```

before accepting a decision.

This is an explicit policy, not a mathematical default.

---

# 203. Confidence Threshold

A system may require:

```text id="v8q2n6"
credible_interval_width <= threshold
```

before execution.

---

# 204. Model Comparison

Two probabilistic models may be compared by:

```text id="k5m8r3"
predictive score
calibration
likelihood
posterior predictive checks
complexity
```

No universal metric is implied.

---

# 205. Causal Model Comparison

Causal models may be compared by:

```text id="y3p7n8"
fit
identification
assumption set
predictive validity
interventional validity
```

---

# 206. Causal vs Predictive Performance

A model can predict well without identifying causal effects.

The runtime MUST preserve this distinction.

---

# 207. Bayesian Model Revision

Model revision changes produce new artifacts rather than mutating historical inference.

---

# 208. Evidence Revision

New evidence creates a new posterior revision.

---

# 209. Evidence Retraction

If evidence is retracted:

```text id="m8x3p5"
posterior revision
```

must be recomputed or invalidated.

---

# 210. Provenance Graph

Inference lineage:

```text id="q4n7y2"
Evidence
   ↓
Likelihood
   ↓
Prior
   ↓
Inference
   ↓
Posterior
   ↓
Decision
```

---

# 211. Causal Provenance

```text id="r6m3x8"
Data
 ↓
Causal Model
 ↓
Identification
 ↓
Effect Estimate
 ↓
Decision
```

---

# 212. Inference Cache

Cache key includes:

```text id="v7p4n2"
model_hash
evidence_hash
algorithm
algorithm_version
configuration
seed
```

---

# 213. Cache Correctness

A cached posterior MUST NOT survive incompatible changes in:

```text id="k3m8y5"
model
evidence
algorithm semantics
prior
```

---

# 214. Incremental Inference

Where supported:

```text id="x5r7p3"
update(previous_posterior, new_evidence)
```

---

# 215. Streaming Inference

Sequential models may emit:

```text id="n8m4q6"
posterior_update
uncertainty_update
change_point
```

---

# 216. Change-Point Detection

Provider/native support:

```text id="q2y7m5"
BayesianChangePoint
CUSUM
PageHinkley
```

where applicable.

---

# 217. Anomaly Probability

Anomaly detection may output:

```text id="v6p3r8"
P(anomaly | observation)
```

and retain model provenance.

---

# 218. Out-of-Distribution Probability

Where supported:

```text id="m4x8n2"
P(in_distribution | x)
```

must be identified as a model estimate, not a ground truth.

---

# 219. Uncertainty-Aware Anomaly Detection

Results include:

```text id="k7r3y5"
anomaly_score
uncertainty
threshold
calibration
```

---

# 220. Probabilistic Rules

Axiom may define:

```text id="p8m4x6"
rule:
    if P(failure | evidence) > 0.8
    then raise_alert
```

The threshold is application logic.

---

# 221. Probabilistic Logic Boundary

Advanced probabilistic logic can be exposed through a provider.

---

# 222. Bayesian Decision Rule

```text id="y5n8r3"
choose action maximizing expected utility
```

subject to explicit constraints from 652.

---

# 223. Minimax Decision

```text id="m7x4p2"
choose action minimizing worst-case loss
```

---

# 224. Minimax Regret

```text id="q3n8y5"
minimize maximum regret
```

---

# 225. Risk-Sensitive Decision

```text id="v6m2r8"
expected_loss
+
lambda * risk
```

The risk coefficient MUST be explicit.

---

# 226. Utility Scaling

Utility transformations must preserve declared semantics.

---

# 227. Utility Uncertainty

If utility itself is uncertain, represent:

```text id="k4p8x3"
UtilityDistribution
```

rather than a false scalar certainty.

---

# 228. Preference Integration

651 preferences may define utility parameters.

---

# 229. Policy Integration

639 can prohibit actions regardless of expected utility.

---

# 230. Governance Integration

640 governs data used in probabilistic inference.

---

# 231. Security Integration

603 governs access to:

```text id="n7m3x8"
private evidence
sensitive distributions
causal models
risk reports
```

---

# 232. Cryptographic Provenance

610 may sign:

```text id="p4r8y2"
model artifact
evidence snapshot
inference result
risk report
```

---

# 233. Audit

653 events:

```text id="x6m3q7"
inference.started
inference.completed
inference.failed
posterior.updated
causal.query.completed
risk.computed
scenario.generated
```

---

# 234. Observability

Metrics:

```text id="v8n4p2"
inference_latency
sample_count
ESS
convergence
calibration
posterior_entropy
risk_tail
```

---

# 235. Privacy

Inference outputs can leak information about evidence.

Explanation APIs must respect 603/640.

---

# 236. Differential Privacy Boundary

Provider may support:

```text id="k3m7x5"
DP mechanism
epsilon
delta
privacy_accountant
```

---

# 237. Privacy Budget

Privacy budgets are explicit.

---

# 238. Differential Privacy Semantics

Noise added for privacy must be distinguished from model uncertainty.

---

# 239. Federated Probabilistic Inference

Provider may support distributed evidence aggregation.

---

# 240. Secure Aggregation

610 may provide cryptographic aggregation.

---

# 241. Federated Causal Analysis

Provider boundary only; assumptions must remain explicit.

---

# 242. Distributed Inference

630 may execute:

```text id="p7m4x8"
parallel chains
parallel samples
distributed particle filters
```

---

# 243. Deterministic Distributed Sampling

Requires deterministic stream partitioning.

---

# 244. GPU Sampling

614/643 may accelerate:

```text id="n6x3r7"
Monte Carlo
likelihood evaluation
particle propagation
```

---

# 245. Tensor Integration

653 distributions may operate over 643 tensors where supported.

---

# 246. Automatic Differentiation

Provider/runtime may expose gradients for differentiable probabilistic models.

---

# 247. Reparameterization

Variational models may use explicit reparameterization metadata.

---

# 248. Gradient Semantics

Gradients are model derivatives, not probabilities.

---

# 249. Probabilistic Programming

Axiom MAY expose:

```text id="x4m8p3"
sample
observe
condition
infer
```

as language/runtime primitives.

---

# 250. Example Probabilistic Program

```text id="q7n3y6"
model coin {
    p ~ Beta(1, 1)

    observe heads ~ Bernoulli(p)
    observe heads ~ Bernoulli(p)
    observe tails ~ Bernoulli(p)

    infer p
}
```

---

# 251. `sample`

`sample` creates a stochastic value from a declared distribution.

---

# 252. `observe`

`observe` conditions the model on evidence.

---

# 253. `infer`

`infer` executes an inference algorithm.

---

# 254. Randomness Boundary

Randomness must be represented by explicit `RandomStream` where reproducibility matters.

---

# 255. Side Effects

Probabilistic model evaluation should be side-effect free.

---

# 256. Inference Context

```text id="m6r3y8"
InferenceContext {
    seed
    limits
    numerical_profile
    algorithm
}
```

---

# 257. Inference Limits

```text id="p4n7x2"
max_time
max_memory
max_samples
max_iterations
max_chains
max_error
```

---

# 258. Adaptive Termination

Inference can terminate on:

```text id="k8m3r5"
error target
convergence target
budget exhaustion
deadline
```

---

# 259. Inference Checkpoint

```text id="v7x4n6"
InferenceCheckpoint {
    model_revision
    evidence_revision
    algorithm
    sampler_state
    random_state
    diagnostics
}
```

---

# 260. Checkpoint Compatibility

Restore requires matching semantic revisions.

---

# 261. Posterior Serialization

Artifacts:

```text id="q5m8y3"
.axprob
.axposterior
.axcausal
.axrisk
.axscenario
.axinference
```

---

# 262. Canonical Serialization

Inference artifacts use canonical serialization.

---

# 263. AI-Readable Metadata

Metadata includes:

```text id="m3r7x8"
variables
distributions
evidence
assumptions
algorithm
uncertainty
provenance
```

---

# 264. CLI

```text id="k6p4n2"
axiom probability infer
axiom probability sample
axiom probability update
axiom probability diagnose

axiom causal identify
axiom causal effect
axiom causal intervene
axiom causal counterfactual

axiom risk analyze
axiom risk stress

axiom uncertainty propagate
axiom uncertainty calibrate
```

---

# 265. Compiler Annotations

```text id="x8m3q5"
@probability
@random
@distribution
@prior
@likelihood
@posterior
@evidence
@observe
@sample
@infer
@causal
@intervention
@counterfactual
@effect
@confounder
@adjust
@risk
@utility
@uncertainty
@scenario
@stochastic
@robust
@chance_constraint
@calibration
@model_assumption
```

---

# 266. Profiles

```text id="r7n4x2"
AXPROB_NONE
AXPROB_CORE
AXPROB_DISTRIBUTION
AXPROB_BAYES
AXPROB_GRAPH
AXPROB_MONTECARLO
AXPROB_MCMC
AXPROB_CAUSAL
AXPROB_RISK
AXPROB_UNCERTAINTY
AXPROB_DECISION
AXPROB_STREAMING
AXPROB_DISTRIBUTED
AXPROB_GPU
AXPROB_PRIVACY
AXPROB_AGENT
AXPROB_FULL
```

---

# 267. Build Stripping

Unused distributions and inference algorithms MUST be removable.

---

# 268. Dependency-Free Baseline

Core probability operations require no external statistical package.

---

# 269. External Provider Boundary

Advanced methods can be loaded through providers.

No external framework becomes mandatory for the core runtime.

---

# 270. Numerical Backend

Probability computations may use Axiom numeric primitives.

---

# 271. High Precision

Optional high-precision arithmetic may be used for sensitive calculations.

---

# 272. SIMD

Independent probability evaluations SHOULD support vectorization.

---

# 273. GPU

Large Monte Carlo workloads MAY use GPU.

---

# 274. CPU Fallback

Every GPU-enabled probabilistic operation MUST have a supported CPU semantic path where practical.

---

# 275. WASM

Deterministic probability functions should be available in WASM profiles.

---

# 276. Mobile

Compact distributions and bounded inference should be available on mobile.

---

# 277. Embedded

Simple probability distributions and filtering may be usable on embedded targets.

---

# 278. Server

Server profiles support distributed inference and provider execution.

---

# 279. Edge

Edge profiles emphasize bounded memory and deterministic sampling.

---

# 280. Performance

Native probability operations should minimize allocations.

---

# 281. Memory Model

Large sample sets should support:

```text id="n6m4r8"
arena
streaming
chunked storage
memory mapping
```

---

# 282. Streaming Samples

Samples need not all reside in memory simultaneously.

---

# 283. Online Statistics

Support:

```text id="x3p7m5"
online_mean
online_variance
online_covariance
quantile_sketch
```

---

# 284. Numerical Stability

Online statistics must use stable algorithms.

---

# 285. Distribution Sampling API

```text id="k8r4n2"
sample(dist, n, stream)
```

---

# 286. Vectorized Sampling

```text id="m7x3p6"
sample_batch(dist, shape, stream)
```

---

# 287. Distribution Algebra

Support:

```text id="v4n8y2"
sum
product
transform
mixture
condition
truncate
```

where mathematically valid.

---

# 288. Mixture Distribution

```text id="q6m3r8"
Mixture {
    components
    weights
}
```

---

# 289. Mixture Weights

Weights MUST be nonnegative and sum to one after normalization.

---

# 290. Truncated Distribution

Explicit bounds:

```text id="p4x7n5"
truncate(dist, lower, upper)
```

---

# 291. Conditional Distribution Object

Conditional distributions remain first-class artifacts.

---

# 292. Copula Boundary

Advanced dependence modeling may expose:

```text id="k3m8r6"
Copula
```

provider.

---

# 293. Correlation Matrix

Must be validated as a valid covariance/correlation structure where required.

---

# 294. Positive Semidefinite Check

Covariance matrices used by supported algorithms MUST satisfy required numerical conditions.

---

# 295. Matrix Decomposition

Probability backend may use:

```text id="v7n2p4"
Cholesky
QR
SVD
eigendecomposition
```

from Axiom numerical infrastructure.

---

# 296. Sparse Probability Graphs

Large graphical models SHOULD use sparse representations.

---

# 297. Factor Sparsity

Factor graphs should avoid dense allocation when factors are sparse.

---

# 298. Graph Compilation

Probabilistic graphs may be compiled into optimized inference plans.

---

# 299. Graph Optimization

Compiler may reorder elimination variables when semantics remain unchanged.

---

# 300. Elimination Heuristic

Variable elimination order is a performance choice and MUST remain observable.

---

# 301. Junction Tree

Provider/native implementation may construct a junction tree for exact inference.

---

# 302. Treewidth

Inference planning SHOULD expose estimated treewidth or equivalent complexity information.

---

# 303. Complexity Awareness

Compiler diagnostics may warn about potentially exponential inference.

---

# 304. Exact vs Approximate Choice

Automatic inference selection must identify:

```text id="m8r3y5"
exact
approximate
```

---

# 305. Approximation Opt-In

Applications may require exact inference.

If exact inference is unavailable within budget, return failure/timeout rather than silently approximate.

---

# 306. Approximation Policy

Applications may explicitly permit approximate inference.

---

# 307. Error Bounds

When available, approximate inference should report mathematically justified error bounds.

---

# 308. Heuristic Error

Heuristic uncertainty estimates must be labeled heuristic.

---

# 309. Calibration

Inference probabilities should be evaluated for calibration when used for decisions.

---

# 310. Decision Calibration

A probability threshold should correspond to observed frequencies under the declared evaluation population when calibrated.

---

# 311. Population Scope

Calibration metadata MUST include:

```text id="p5n8x2"
population
time period
dataset
sampling method
```

---

# 312. Dataset Shift

Calibration can degrade under distribution shift.

The runtime should preserve deployment population metadata.

---

# 313. Causal Population Scope

Causal estimates must identify the target population.

---

# 314. Transportability

Effects transported across populations must preserve assumptions.

---

# 315. External Validity

External validity is metadata, not automatic truth.

---

# 316. Selection Bias

653 may represent selection mechanisms explicitly.

---

# 317. Collider

Causal graph tooling may identify collider structures.

---

# 318. Conditioning Safety

Conditioning on a collider can alter associations.

The runtime should expose graph diagnostics where supported.

---

# 319. Confounding Diagnostics

The causal subsystem may identify potential confounders.

---

# 320. Unmeasured Confounding

If an effect depends on an unmeasured-confounding assumption, this must be recorded.

---

# 321. Sensitivity to Unmeasured Confounding

Provider may compute sensitivity bounds.

---

# 322. Causal Sensitivity Analysis

Outputs:

```text id="k4m7x3"
assumption_strength
effect_range
robustness_threshold
```

---

# 323. Causal Effect Bounds

If point identification fails, return bounds.

---

# 324. Intervention Cost

Decision models may associate interventions with:

```text id="p8n3y6"
cost
risk
resource_usage
```

---

# 325. Experiment Selection

653 can calculate expected information value for candidate experiments.

---

# 326. Active Experiment Design

Pipeline:

```text id="m5r8x2"
candidate experiment
   ↓
expected information
   ↓
expected utility
   ↓
cost/risk
   ↓
652 selection
```

---

# 327. Sequential Decision Under Uncertainty

Repeated cycle:

```text id="v7n4p3"
observe
infer
plan
act
observe
```

uses:

```text id="x5m8q7"
653 inference
652 planning
```

---

# 328. Belief State

The current posterior can be represented as:

```text id="q3r7n5"
BeliefState
```

---

# 329. Belief-State Planning

Provider boundary for POMDP-like systems:

```text id="k6m3x8"
BeliefState
Action
Observation
Transition
Reward
```

---

# 330. POMDP Boundary

Partially observable planning may combine:

```text id="p8y4n2"
653 belief updates
652 planning
```

without making a POMDP solver mandatory.

---

# 331. Markov Decision Process Boundary

MDP state/action/reward abstractions may be consumed by 652.

---

# 332. Policy

A policy maps state/belief to actions.

```text id="m7x4r8"
Policy(state) -> action
```

---

# 333. Policy Uncertainty

A learned or inferred policy may expose confidence/uncertainty metadata.

---

# 334. Risk-Constrained Policy

652 can constrain policies using 653 risk estimates.

---

# 335. Offline Evaluation

Policies may be evaluated using historical data with explicit assumptions.

---

# 336. Counterfactual Policy Evaluation

Requires causal assumptions and is distinct from ordinary prediction.

---

# 337. Off-Policy Evaluation

Provider boundary may support:

```text id="v3n8m6"
IPS
SNIPS
DoublyRobust
```

with support/overlap diagnostics.

---

# 338. Positivity

Causal/off-policy estimators should expose violations of treatment/action support assumptions.

---

# 339. Overlap Diagnostics

```text id="q7m4x2"
propensity_overlap
effective_support
```

---

# 340. Propensity

```text id="k5r8n3"
P(action | context)
```

must preserve estimation provenance.

---

# 341. Causal Bandit Boundary

653 can provide uncertainty estimates for bandit models; 651 remains responsible for personalization/exploration policy.

---

# 342. Bayesian Bandit Boundary

Posterior beliefs may feed 651/652.

---

# 343. Risk-Aware Exploration

Exploration constraints can consume 653 risk estimates.

---

# 344. Safety Constraints

Exploration cannot bypass 639/603.

---

# 345. Model Risk

653 may represent uncertainty in the model itself.

---

# 346. Scenario Risk

Scenarios can represent rare but important conditions.

---

# 347. Tail Scenario Generation

Tail sampling methods may include:

```text id="m4x8p7"
importance sampling
stratified sampling
extreme-value methods
```

provider boundary.

---

# 348. Extreme Value Theory

Provider may support:

```text id="q5n3y8"
GEV
GPD
tail_index
```

---

# 349. Reliability Block Diagrams

Provider may represent:

```text id="v8m4r2"
series
parallel
k-out-of-n
```

---

# 350. Fault Propagation

Fault-tree events may feed risk models.

---

# 351. Bayesian Fault Diagnosis

Observed symptoms can update fault probabilities.

---

# 352. Root Cause Analysis

Probabilistic root-cause outputs MUST be labeled hypotheses unless causally identified.

---

# 353. Incident Integration

602/633 incidents may provide evidence to 653.

---

# 354. Observability Integration

Telemetry may become evidence:

```text id="k7p3x5"
metric
trace
log
event
```

with timestamp/provenance.

---

# 355. Online Bayesian Updating

Streaming telemetry may update:

```text id="m6r8n2"
failure probability
latency distribution
capacity model
```

---

# 356. Change Detection

Posterior updates can identify regime changes.

---

# 357. Forecasting

Future distributions can feed:

```text id="q4n7m3"
652 schedules
capacity planning
deployment planning
```

---

# 358. Capacity Uncertainty

Resource capacity from 606 may become:

```text id="x8m2r5"
CapacityDistribution
```

when uncertain.

---

# 359. Reliability-Aware Scheduling

652 may constrain:

```text id="v5n8p3"
P(task_failure) <= threshold
```

---

# 360. Deadline Risk

Schedule analysis may produce:

```text id="m7r3x8"
P(deadline_miss)
```

---

# 361. Service Risk

631 can consume:

```text id="q6n4p2"
failure_probability
latency_distribution
```

for routing decisions.

---

# 362. Deployment Risk

636 can consume:

```text id="k8m5r3"
rollout_failure_distribution
```

---

# 363. Workflow Risk

629 can consume:

```text id="v3x7n6"
task_failure_probability
completion_time_distribution
```

---

# 364. Distributed System Risk

635 can consume:

```text id="p5n8m2"
node_failure_distribution
network_partition_scenarios
```

---

# 365. Risk Aggregation

Correlations across components must be represented where known.

---

# 366. Independence Assumption

Assuming independence MUST be explicit.

---

# 367. Dependency Graph

Risk dependencies can use 645 graph structures.

---

# 368. Bayesian Network Compilation

Risk graphs may compile into 653 probabilistic graphs.

---

# 369. Causal Risk

Where causal models exist, risk interventions can be evaluated through `do()` semantics.

---

# 370. Intervention Risk

```text id="m4r8x3"
P(failure | do(action))
```

may differ from:

```text id="k7n3p5"
P(failure | action observed)
```

---

# 371. Decision Audit

Decision outputs should distinguish observational and interventional quantities.

---

# 372. Model Assumption Report

```text id="v6m2y8"
AssumptionReport {
    assumptions
    sensitivity
    unsupported_assumptions
}
```

---

# 373. Assumption Sensitivity

Users can determine whether decisions change under alternative assumptions.

---

# 374. Robust Decision

A robust decision may remain valid across an uncertainty set.

---

# 375. Ambiguity Sets

Distributional ambiguity can be represented:

```text id="p8x4n2"
DistributionSet
```

---

# 376. Distributionally Robust Optimization

Provider boundary:

```text id="m5r7y3"
DRO
```

integrates with 652.

---

# 377. Chance Constraint vs Robust Constraint

The two must remain semantically distinct.

---

# 378. Bayesian vs Frequentist

The runtime must preserve inferential framework metadata.

---

# 379. Statistical Test

Provider may expose:

```text id="q4n8x6"
hypothesis_test
p_value
effect_size
interval
```

---

# 380. P-Value Semantics

A p-value MUST NOT be represented as:

```text id="v7m3r5"
P(hypothesis is true)
```

---

# 381. Multiple Testing

Provider may support:

```text id="k2x8n4"
Bonferroni
Holm
BenjaminiHochberg
```

---

# 382. Effect Size

Effect size is distinct from statistical significance.

---

# 383. Bayesian Hypothesis Testing

Posterior probabilities/Bayes factors remain distinct from p-values.

---

# 384. Experimental Metadata

Statistical inference records:

```text id="m6r4p8"
sample_size
sampling_method
population
hypothesis
test_method
```

---

# 385. Power Analysis

Provider may support:

```text id="q7n3x5"
power
sample_size
effect_size
alpha
```

---

# 386. Sequential Testing

Stopping rules MUST be explicit.

---

# 387. Optional Frequentist Layer

Frequentist inference is supported as an optional statistical provider layer; the core probability model remains framework-neutral.

---

# 388. Uncertainty Visualization

GUI may display:

```text id="v4m8n2"
density
CDF
interval
posterior
risk curve
calibration
causal graph
```

---

# 389. AI Explanation

AI can summarize structured uncertainty metadata but MUST preserve:

```text id="k5r7x3"
method
assumptions
uncertainty
provenance
```

---

# 390. No Fabricated Explanation

Generated text cannot invent causal mechanisms absent from the model.

---

# 391. Structured Causal Explanation

```text id="m8p4n6"
effect
identification
assumptions
evidence
uncertainty
```

---

# 392. Structured Risk Explanation

```text id="q3x7m5"
event
probability
impact
risk_metric
uncertainty
```

---

# 393. Decision Explanation Integration

652 may combine these into a decision report.

---

# 394. Model Card Integration

647 can attach:

```text id="v6n2r8"
model assumptions
training population
limitations
calibration
```

---

# 395. Causal Model Card

Causal artifacts should include:

```text id="k4m8x3"
identification assumptions
target population
known limitations
```

---

# 396. Risk Model Card

Risk artifacts include:

```text id="p7n3y5"
risk horizon
data source
scenario assumptions
tail limitations
```

---

# 397. Artifact Signing

610 may sign model and inference artifacts.

---

# 398. Supply Chain

647 governs third-party probabilistic model providers.

---

# 399. Provider Isolation

External inference providers use explicit capabilities.

---

# 400. Plugin Security

Inference plugins cannot arbitrarily access private evidence.

---

# 401. Resource Limits

Sampling/inference is governed by 606.

---

# 402. CPU Scheduling

607/608 govern parallel inference.

---

# 403. Network

609 governs remote inference providers.

---

# 404. Storage

611/612 govern persisted posterior/checkpoint artifacts.

---

# 405. Compression

613 may compress large sample archives.

---

# 406. Serialization

612 defines canonical structured serialization.

---

# 407. IPC

604 supports isolated provider communication.

---

# 408. Distributed Compute

630 provides execution infrastructure.

---

# 409. Consensus

635 remains responsible for distributed coordination.

---

# 410. Event Bus

634 can publish posterior/risk updates.

---

# 411. Streaming

Streaming inference integrates with 634/607.

---

# 412. Configuration

601 configures:

```text id="m7r4x8"
default algorithm
precision
sampling limits
provider selection
```

---

# 413. Secrets

638/610 manage credentials for external data/model providers.

---

# 414. Identity

627 determines who may query sensitive inference artifacts.

---

# 415. Policy

639 determines whether an inference operation is permitted.

---

# 416. Governance

640 determines how evidence and inference artifacts are classified/retained.

---

# 417. Observability

602/633 monitor inference behavior.

---

# 418. Crash Recovery

600/605 handle long-running inference recovery.

---

# 419. Application State

Inference sessions may be checkpointed through 600.

---

# 420. Plugin Runtime

623 provides optional external inference plugins.

---

# 421. Scripting

624 can automate probabilistic analyses.

---

# 422. Package Distribution

625 distributes model/provider packages.

---

# 423. API Exposure

626 can expose probabilistic queries over HTTP/RPC.

---

# 424. API Security

627/639 protect remote inference APIs.

---

# 425. Rate Limits

606/632 can limit expensive inference requests.

---

# 426. Cost Controls

Decision services can charge for:

```text id="k8m3p6"
samples
GPU time
CPU time
provider usage
```

---

# 427. Multi-Tenant Probability Runtime

Tenant isolation applies to:

```text id="m4r7x2"
models
evidence
samples
posteriors
risk reports
```

---

# 428. Data Residency

Inference artifacts inherit 640 residency constraints.

---

# 429. Retention

Evidence and posterior retention follows governance policy.

---

# 430. Deletion

Deleting evidence may invalidate derived inference artifacts.

---

# 431. Derived Data

Posterior distributions derived from sensitive evidence remain potentially sensitive.

---

# 432. Derived Data Classification

640 metadata must propagate to derived artifacts.

---

# 433. Lineage

Derived artifacts reference source evidence.

---

# 434. Query Authorization

Access to posterior does not imply access to source evidence.

---

# 435. Redaction

Risk reports may redact sensitive factors while retaining aggregate metrics.

---

# 436. Differential Privacy

If applied, DP metadata must remain attached to outputs.

---

# 437. Reproducibility

Reproducible inference requires:

```text id="p6n3x8"
model revision
evidence revision
algorithm
algorithm version
configuration
seed
numerical profile
```

---

# 438. Reproducibility Class

```text id="m7r4y2"
Strict
Deterministic
Seeded
Approximate
NonReproducible
```

---

# 439. Numerical Profile

```text id="k5x8p3"
Fast
Accurate
Deterministic
HighPrecision
```

---

# 440. Cross-Platform Reproducibility

Exact reproducibility is guaranteed only under compatible numerical profiles.

---

# 441. Artifact Hash

Canonical inference artifact hash includes semantic metadata.

---

# 442. Posterior Hash

Posterior hash includes:

```text id="v8m2r6"
model
evidence
algorithm
configuration
```

---

# 443. Risk Hash

Risk report hash includes:

```text id="q4n7x3"
risk model
scenario set
metric
configuration
```

---

# 444. Causal Result Hash

Causal result hash includes:

```text id="m5r8p2"
causal model
query
identification
data
method
```

---

# 445. Cache Invalidation

Any semantic dependency change invalidates derived caches.

---

# 446. Online Learning Boundary

643/651 own model updating.

653 provides uncertainty/inference primitives.

---

# 447. Bayesian Online Learning

Can be implemented through explicit 643/651 model contracts using 653 inference.

---

# 448. Personalization Uncertainty

651 may store uncertain preferences as distributions.

---

# 449. Agent Beliefs

644 can maintain beliefs through 653 artifacts.

---

# 450. Memory Beliefs

650 may store beliefs with revision/provenance.

---

# 451. Knowledge Confidence

645 knowledge entries may carry confidence metadata but 653 remains responsible for formal probabilistic interpretation.

---

# 452. Knowledge vs Probability

A confidence score from 645 is not automatically a probability.

---

# 453. Probability Conversion

Any conversion from confidence score to probability must specify calibration/mapping.

---

# 454. Semantic Types

Axiom should distinguish:

```text id="k3m7x8"
Probability
ConfidenceScore
Likelihood
PosteriorProbability
CausalEffect
Risk
Utility
```

---

# 455. Unit Safety

Risk, cost, probability and utility must not be freely interchangeable.

---

# 456. Compiler Type Checking

Invalid combinations should produce compile-time errors where statically detectable.

---

# 457. Example Type Error

```text id="m4x8p2"
error AX653041:
cannot add Probability to Duration
```

---

# 458. Causal Type Error

A causal effect cannot be used as a probability without explicit transformation.

---

# 459. Distribution Type Safety

A distribution over `Duration` is not automatically a distribution over `Probability`.

---

# 460. Random Variable Type

```text id="p7n3r6"
RandomVariable<Duration>
```

---

# 461. Sampling Type

```text id="v5m8x2"
sample(RandomVariable<Duration>)
    -> Duration
```

---

# 462. Inference Type

```text id="k6r4p8"
infer(theta)
    -> Posterior<Theta>
```

---

# 463. Posterior Query

```text id="m3x7n5"
posterior.mean()
posterior.interval(0.95)
```

---

# 464. Causal Query Type

```text id="q8m4r2"
effect(Treatment, Outcome)
    -> CausalEffect
```

---

# 465. Risk Query Type

```text id="v7p3x8"
risk(event)
    -> RiskDistribution
```

---

# 466. Decision Query Type

```text id="k5m8n3"
expected_utility(action)
    -> Utility
```

---

# 467. Probabilistic Constraint Type

```text id="m4r7x2"
probability(constraint) >= 0.99
```

---

# 468. Compiler Lowering

Probability expressions lower into `ProbIR`.

---

# 469. ProbIR

```text id="q6n3p8"
ProbIR
├── Variables
├── Distributions
├── Factors
├── Evidence
├── Queries
├── CausalGraph
├── Interventions
├── InferencePlan
├── RiskModel
└── Provenance
```

---

# 470. CausalIR

```text id="x7m4r2"
CausalIR
├── Variables
├── DAG
├── StructuralFunctions
├── ExogenousVariables
├── Interventions
├── Counterfactuals
├── Assumptions
└── IdentificationPlan
```

---

# 471. RiskIR

```text id="p3n8y5"
RiskIR
├── Events
├── Probabilities
├── Impacts
├── Dependencies
├── Scenarios
├── RiskMetrics
└── Mitigations
```

---

# 472. Inference Plan

Compiler generates:

```text id="m6r4x8"
query
→ select algorithm
→ compile model
→ execute
→ validate
→ emit posterior
```

---

# 473. Algorithm Selection

Selection considers:

```text id="k7n3p5"
model structure
treewidth
sample size
accuracy
deadline
resources
exactness requirement
```

---

# 474. Exactness Requirement

User can require:

```text id="v8m4r2"
@exact
```

Approximation then becomes invalid.

---

# 475. Approximation Requirement

User may specify:

```text id="q5x7n3"
@approximate(error <= 0.01)
```

---

# 476. Solver Budget

Inference budgets integrate with 606.

---

# 477. Checkpoint

Inference checkpoints integrate with 600/611.

---

# 478. Provider Selection

Provider selection is observable and overrideable.

---

# 479. Provider Failure

Provider failure is distinct from:

```text id="m3r8x5"
model invalid
data invalid
non-convergence
```

---

# 480. Fallback

Fallback may select another inference method only if the application's approximation policy allows it.

---

# 481. No Silent Downgrade

Exact → approximate fallback requires explicit permission.

---

# 482. Statistical Assumptions

Every statistical method SHOULD record:

```text id="k4m7x8"
distribution assumptions
sampling assumptions
independence assumptions
missing-data assumptions
```

---

# 483. Assumption Violation

Diagnostics may warn when data contradict model assumptions.

---

# 484. Model Misfit

Posterior predictive checks can identify misfit.

---

# 485. Causal Misfit

Observed/interventional discrepancies can reveal causal model problems.

---

# 486. Calibration Drift

Production systems can monitor probability calibration over time.

---

# 487. Risk Drift

Risk estimates can be monitored against observed outcomes.

---

# 488. Outcome Feedback

646/643 can feed observed outcomes back for evaluation.

---

# 489. Continuous Validation

Long-running systems SHOULD continuously evaluate calibration where appropriate.

---

# 490. Decision Feedback

652 decisions may be evaluated against realized outcomes.

---

# 491. Causal Feedback

Observed intervention outcomes can update causal evidence where valid.

---

# 492. No Automatic Causal Learning

Observed correlation after an intervention does not automatically rewrite the causal graph.

---

# 493. Human Review

High-impact causal/risk model changes may require approval through 647/639.

---

# 494. Model Promotion

647 owns promotion of probabilistic/causal models.

---

# 495. Model Rollback

647 handles rollback.

---

# 496. Version Pinning

Production inference can pin exact model versions.

---

# 497. Experimentation

637/646 manage experiments around probabilistic models.

---

# 498. A/B Testing

Experiment assignment remains outside 653.

653 analyzes outcomes/uncertainty.

---

# 499. Causal Experiment Analysis

653 may estimate treatment effects from experiment data.

---

# 500. Experimental Provenance

Treatment assignment metadata is preserved.

---

# 501. Risk Experimentation

Alternative risk models can be evaluated in controlled environments.

---

# 502. Simulation Experimentation

648 can generate synthetic stress tests.

---

# 503. Synthetic Data

Synthetic evidence MUST be marked synthetic.

---

# 504. Synthetic Causal Data

Synthetic causal relationships cannot be treated as real-world evidence.

---

# 505. Training Data

Model training remains 643/647 responsibility.

---

# 506. Inference Data

653 consumes data according to governance rules.

---

# 507. Data Contracts

Input datasets require:

```text id="m7r4x3"
schema
revision
population
timestamp
provenance
```

---

# 508. Population Metadata

Statistical results must identify the analyzed population.

---

# 509. Sampling Metadata

Sampling mechanism is preserved.

---

# 510. Weighting

Survey/importance weights must remain explicit.

---

# 511. Survey Inference

Provider may support weighted estimates.

---

# 512. Missing Population

Generalization beyond the observed population requires explicit assumptions.

---

# 513. Extrapolation

Extrapolated results must be labeled.

---

# 514. Forecast Horizon

Forecasts record:

```text id="k4x8n2"
horizon
frequency
cutoff_time
```

---

# 515. Backtesting

646 can evaluate forecasts using historical rolling windows.

---

# 516. Temporal Leakage

Inference/training pipelines MUST preserve temporal availability semantics.

---

# 517. Point-in-Time Correctness

Evidence available after the decision time cannot silently enter a historical inference.

---

# 518. Causal Leakage

Post-treatment variables must not be used as pre-treatment confounders without explicit causal semantics.

---

# 519. Decision Leakage

Future outcomes cannot become decision inputs in retrospective evaluation unless explicitly marked.

---

# 520. Evaluation Population

646 evaluation metadata is preserved.

---

# 521. Uncertainty Reporting

Default reporting should prefer:

```text id="m5r7x3"
estimate
interval/distribution
method
assumptions
```

rather than one bare number.

---

# 522. Probability Formatting

Probability output may be rendered:

```text id="k8n4p2"
0.73
73%
```

but internal representation remains numeric.

---

# 523. Risk Formatting

Risk may be rendered in application-specific units.

---

# 524. Utility Formatting

Utility must retain its semantic scale.

---

# 525. Causal Effect Units

Causal effects retain outcome units.

---

# 526. Treatment Effect Sign

Sign conventions must be explicit.

---

# 527. Intervention Semantics

`do(X=x)` is not syntactic sugar for ordinary assignment.

---

# 528. Counterfactual Semantics

Counterfactual queries operate on structural models.

---

# 529. Potential Outcome Consistency

Potential outcomes require explicit treatment/intervention definitions.

---

# 530. SUTVA Boundary

Provider may declare assumptions such as no interference.

---

# 531. Interference

Network/spillover effects require explicit models.

---

# 532. Time-Varying Treatment

Causal models may represent longitudinal interventions.

---

# 533. Dynamic Treatment

Provider may support sequential treatment policies.

---

# 534. Longitudinal Confounding

Time-varying confounding requires explicit methods.

---

# 535. Survival Causality

Treatment effects on time-to-event outcomes require survival-specific models.

---

# 536. Competing Outcomes

Multiple outcomes can be represented jointly.

---

# 537. Multi-Outcome Causality

Covariance among outcomes must be preserved.

---

# 538. Causal Mediation

Direct/indirect effects remain method-specific.

---

# 539. Heterogeneous Effects

CATE estimates include uncertainty and subgroup support.

---

# 540. Small Sample Warning

Inference should expose low effective sample sizes.

---

# 541. Rare Event Warning

Rare events require appropriate numerical/sampling diagnostics.

---

# 542. Tail Risk Warning

Tail estimates with insufficient samples must expose uncertainty.

---

# 543. Model Extrapolation Warning

Queries outside model-supported domains should be flagged.

---

# 544. OOD Warning

Out-of-distribution inference may be flagged.

---

# 545. Uncertainty Propagation

If:

```text id="k3m8x5"
Y = f(X,Z)
```

and X/Z are uncertain, output Y should preserve propagated uncertainty where supported.

---

# 546. Monte Carlo Propagation

```text id="m7r4p8"
sample X
sample Z
evaluate f
aggregate
```

---

# 547. Analytic Propagation

Where mathematically tractable:

```text id="v5n8x2"
mean
variance
covariance
```

may be propagated analytically.

---

# 548. Linear Approximation

Delta-method approximations may be provided explicitly.

---

# 549. Nonlinear Propagation

Nonlinear transformations should not assume linear uncertainty propagation without declaration.

---

# 550. Correlated Inputs

Covariance must be retained when known.

---

# 551. Independence

Independent sampling requires explicit independence assumptions.

---

# 552. Dependence

Copulas/factor models may represent dependence.

---

# 553. Risk Aggregation

Portfolio/system risk must account for dependence when modelled.

---

# 554. Stress Scenarios

Stress scenarios may violate normal probability assumptions deliberately.

---

# 555. Scenario Labels

Every scenario is:

```text id="k4m8r3"
probabilistic
stress
synthetic
historical
counterfactual
```

as appropriate.

---

# 556. Historical Scenario

Historical scenarios preserve actual observation provenance.

---

# 557. Counterfactual Scenario

Counterfactual scenarios require causal model provenance.

---

# 558. Synthetic Scenario

Synthetic scenarios must never silently enter historical datasets.

---

# 559. Decision Scenario

Decision scenarios are inputs to 652 optimization.

---

# 560. Scenario Reduction

Large scenario sets may be reduced.

Reduction method and distortion metrics must be recorded.

---

# 561. Scenario Clustering

Provider may cluster scenarios while preserving approximate distribution properties.

---

# 562. Importance Sampling

Tail-focused scenario generation may use importance sampling.

---

# 563. Risk Bounds

Risk calculations can provide upper/lower bounds when exact estimates are unavailable.

---

# 564. Conservative Mode

Applications may request conservative uncertainty handling.

---

# 565. Conservative Semantics

Conservative mode must define mathematically what is being bounded.

---

# 566. Safety Margin

A safety margin is a decision parameter, not automatically a probability.

---

# 567. Probability Threshold

Thresholds must be explicit.

---

# 568. Risk Threshold

Risk limits must be explicit.

---

# 569. Utility Threshold

Utility acceptance criteria must be explicit.

---

# 570. Evidence Threshold

Evidence requirements must be explicit.

---

# 571. Causal Evidence

Evidence supporting causal claims must remain distinguishable from observational evidence.

---

# 572. Model Assumption Review

Models should support assumption review before deployment.

---

# 573. Model Registry

647 stores approved versions.

---

# 574. Model Deployment

External deployment remains under 647/636.

---

# 575. Model Runtime

Inference execution occurs in 653.

---

# 576. Model Training

Training remains 643.

---

# 577. Model Evaluation

Evaluation remains 646.

---

# 578. Model Governance

Governance remains 640/647.

---

# 579. Model Security

Security remains 603/638/610.

---

# 580. Model Distribution

625 distributes models/providers.

---

# 581. API Service

626 exposes inference APIs.

---

# 582. Agent Service

644 exposes probabilistic tools.

---

# 583. Decision Service

652 consumes 653 results.

---

# 584. Workflow Service

629 can schedule inference tasks.

---

# 585. Scheduler Service

635 can allocate inference compute.

---

# 586. Resource Service

606 budgets inference.

---

# 587. Observability Service

633 observes inference.

---

# 588. Storage Service

611 stores inference artifacts.

---

# 589. Serialization Service

612 serializes inference artifacts.

---

# 590. Compression Service

613 compresses sample archives.

---

# 591. IPC Service

604 isolates external inference providers.

---

# 592. Networking Service

609 connects remote providers.

---

# 593. Configuration Service

601 controls inference defaults.

---

# 594. State Service

600 stores long-running inference state.

---

# 595. Supervision

605 supervises provider processes.

---

# 596. Package Service

623/625 distribute inference extensions.

---

# 597. Scripting

624 automates inference workflows.

---

# 598. GUI

619/620 can bind probabilistic state to UI.

---

# 599. Document Integration

621 can embed risk/probability reports.

---

# 600. Completion Invariants

Mandatory invariants:

```text id="g6m4x8"
I-001 probability is bounded [0,1]
I-002 probability is distinct from confidence score
I-003 correlation is distinct from causation
I-004 observation is distinct from assumption
I-005 prediction is distinct from intervention
I-006 P(Y|X) is distinct from P(Y|do(X))
I-007 causal claims preserve assumptions
I-008 causal discovery is not automatically established truth
I-009 approximate inference is marked approximate
I-010 non-converged inference is not marked converged
I-011 exact inference remains exact
I-012 exact-required mode cannot silently approximate
I-013 random seeds are preserved
I-014 stochastic algorithms expose method metadata
I-015 posterior preserves prior/evidence provenance
I-016 evidence revisions invalidate incompatible posteriors
I-017 model revisions invalidate incompatible inference
I-018 cache keys include semantic dependencies
I-019 numerical tolerance is explicit
I-020 uncertainty is not silently collapsed
I-021 simulation is not observation
I-022 synthetic data is labeled synthetic
I-023 stress scenarios are not probability forecasts
I-024 counterfactuals require causal semantics
I-025 interventions require intervention semantics
I-026 causal effects preserve target population
I-027 partial identification returns bounds
I-028 unmeasured confounding assumptions are explicit
I-029 missingness assumptions are explicit
I-030 independence assumptions are explicit
I-031 risk aggregation respects modeled dependence
I-032 expected loss is distinct from worst-case loss
I-033 VaR is distinct from CVaR
I-034 probability is distinct from risk
I-035 utility is distinct from probability
I-036 decision remains owned by 652
I-037 policy remains owned by 639
I-038 governance remains owned by 640
I-039 model training remains owned by 643
I-040 model lifecycle remains owned by 647
I-041 evaluation remains owned by 646
I-042 simulation remains owned by 648
I-043 personalization remains owned by 651
I-044 agent orchestration remains owned by 644
I-045 knowledge remains owned by 645
I-046 inference artifacts are versioned
I-047 inference artifacts are provenance-aware
I-048 inference artifacts are serializable
I-049 checkpoints are revision-bound
I-050 external providers are capability-bound
I-051 external providers cannot access unauthorized evidence
I-052 resource budgets are enforced
I-053 cancellation is safe
I-054 partial results are explicit
I-055 timeout is distinct from non-convergence
I-056 provider failure is distinct from model failure
I-057 model failure is distinct from data failure
I-058 approximate error metadata is preserved
I-059 calibration metadata is preserved
I-060 population metadata is preserved
I-061 temporal availability is preserved
I-062 causal leakage is prevented
I-063 point-in-time correctness is preserved
I-064 random streams are reproducible when requested
I-065 parallel streams are independently partitioned
I-066 probability estimates expose estimation method
I-067 risk estimates expose estimation method
I-068 causal estimates expose identification method
I-069 confidence intervals retain inferential framework
I-070 credible intervals retain Bayesian semantics
I-071 prediction intervals retain predictive semantics
I-072 model uncertainty is distinguishable from observation noise
I-073 aleatoric and epistemic uncertainty remain distinguishable
I-074 derived artifacts retain data classification
I-075 deletion propagates to derived artifacts where required
I-076 privacy noise is distinct from model uncertainty
I-077 differential privacy metadata is preserved
I-078 provenance survives serialization
I-079 provenance survives restart
I-080 artifacts can be independently validated
I-081 probability computations use stable numerical methods
I-082 log probability is distinct from probability
I-083 covariance validity is checked
I-084 distribution parameters are validated
I-085 scenario identity is preserved
I-086 scenario provenance is preserved
I-087 scenario probabilities are explicit
I-088 uncertainty sets are explicit
I-089 robust constraints are distinct from chance constraints
I-090 decision thresholds are explicit
I-091 assumptions are inspectable
I-092 assumption sensitivity is supported
I-093 model extrapolation is detectable where possible
I-094 OOD status is preserved where available
I-095 causal discovery output is labeled candidate/inferred
I-096 causal graph revisions are versioned
I-097 intervention queries preserve intervention identity
I-098 counterfactual queries preserve factual/interventional states
I-099 utility parameters are explicit
I-100 risk preferences are explicit
```

---

# 601. Acceptance Criteria

The implementation MUST additionally satisfy:

1. probability primitives compile natively;
2. distributions can be sampled;
3. distribution parameters are validated;
4. random streams are reproducible;
5. conditional probability is representable;
6. Bayesian updates are representable;
7. evidence is versioned;
8. posterior provenance is preserved;
9. exact inference has explicit status;
10. approximate inference has explicit status;
11. convergence is reported;
12. MCMC diagnostics are represented where supported;
13. Monte Carlo diagnostics are represented;
14. uncertainty intervals preserve semantic type;
15. covariance matrices are validated;
16. factor graphs are representable;
17. Bayesian networks are validated as DAGs;
18. HMMs are representable;
19. dynamic models are representable;
20. causal DAGs are representable;
21. interventions are first-class;
22. counterfactuals require causal models;
23. causal assumptions are preserved;
24. adjustment sets are inspectable;
25. causal bounds are representable;
26. treatment effects retain population scope;
27. missing-data assumptions are preserved;
28. measurement error can be modeled;
29. sensor fusion preserves source provenance;
30. risk events are representable;
31. expected loss is computable;
32. tail risk is representable;
33. CVaR is representable where supported;
34. risk dependencies are preserved;
35. fault trees are representable;
36. reliability models are representable;
37. Bayesian filtering is representable;
38. particle filtering has explicit sampling metadata;
39. uncertainty propagation is supported;
40. scenario generation is supported;
41. scenario provenance is preserved;
42. stress scenarios are distinguishable;
43. synthetic scenarios are distinguishable;
44. posterior predictive checks are supported;
45. prior predictive checks are supported;
46. calibration metrics are representable;
47. proper scoring rules are representable;
48. forecast distributions are versioned;
49. forecast horizons are explicit;
50. temporal leakage is prevented;
51. point-in-time semantics are enforced;
52. causal leakage is prevented;
53. model revisions invalidate incompatible caches;
54. evidence revisions invalidate incompatible caches;
55. inference checkpoints are revision-bound;
56. cancellation is safe;
57. inference budgets are enforceable;
58. exact-required mode rejects unsupported approximation;
59. provider fallback is explicit;
60. provider identity is preserved;
61. provider version is preserved;
62. external provider capabilities are inspectable;
63. privacy metadata is preserved;
64. derived-data classification is propagated;
65. retention policy applies to inference artifacts;
66. deletion invalidates affected derived artifacts;
67. differential privacy metadata is preserved;
68. model provenance is preserved;
69. causal provenance is preserved;
70. risk provenance is preserved;
71. AI agents can consume structured inference results;
72. AI agents receive uncertainty metadata;
73. AI explanations cannot fabricate causal claims;
74. 652 can consume probability distributions;
75. 652 can consume scenario sets;
76. 652 can consume risk metrics;
77. 652 can consume chance constraints;
78. 652 can consume robust uncertainty sets;
79. 648 can consume scenario models;
80. 643 can consume uncertainty primitives;
81. 645 can provide structural priors;
82. 650 can persist belief revisions;
83. 651 can consume uncertainty-aware preferences;
84. 646 can evaluate calibration;
85. 647 can govern model lifecycle;
86. 639 can gate inference operations;
87. 640 can govern inference data;
88. 603 can secure inference artifacts;
89. 606 can budget inference;
90. 607 can schedule inference;
91. 630 can distribute inference;
92. 614 can accelerate sampling;
93. 611 can persist checkpoints;
94. 612 can serialize inference;
95. 613 can compress samples;
96. 609 can connect providers;
97. 604 can isolate providers;
98. 633 can observe inference;
99. 600 can persist long-running inference state;
100. unused probabilistic components can be stripped.

---

# 602. Reference Architecture

```text
                     Evidence / Data
                           │
                           ▼
                  ┌─────────────────┐
                  │ 653 Probability │
                  │    Runtime      │
                  └────────┬────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
       Distribution     Bayesian       Causal
         Engine         Inference       Engine
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                    Uncertainty Engine
                           │
                           ▼
                      Risk Engine
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
          Scenario Engine       Utility Engine
                 │                   │
                 └─────────┬─────────┘
                           ▼
                     Decision Bridge
                           │
                           ▼
                         652
                           │
                           ▼
                  Plan / Decision / Action
```

---

# 603. Conceptual Separation

Axiom's AI reasoning stack now becomes:

```text
641 retrieves
642 analyzes
643 predicts
644 orchestrates agents
645 represents knowledge
646 evaluates
647 governs models
648 simulates
649 understands multimodal data
650 remembers
651 personalizes
652 optimizes/decides
653 reasons about uncertainty and causality
```

The resulting architecture avoids the common mistake of treating:

```text
prediction = probability
correlation = causation
confidence = probability
simulation = evidence
optimization = authorization
```

as equivalent concepts.

---

# 604. Implementation Priority

Implementation order:

```text
P0:
    Probability
    Distribution
    RandomStream
    Evidence
    Conditional Probability
    Bayesian Update
    Uncertainty Types

P1:
    Graphical Models
    Monte Carlo
    Risk
    Scenario Engine
    Calibration

P2:
    Causal DAG
    Intervention
    Counterfactual
    Treatment Effects

P3:
    MCMC
    Variational Inference
    Advanced Causal Identification
    Sequential Monte Carlo

P4:
    Distributed Inference
    GPU Sampling
    Privacy-Preserving Inference
    Advanced Risk Providers
```

---

# 605. Completion Criteria

BOOTSTRAP-653 is complete because:

- probabilistic primitives are defined;
- distribution model is defined;
- Bayesian inference architecture is defined;
- graphical models are defined;
- approximate inference boundary is defined;
- uncertainty representation is defined;
- calibration semantics are defined;
- causal model architecture is defined;
- intervention/counterfactual semantics are defined;
- causal identification boundaries are defined;
- risk architecture is defined;
- scenario generation is defined;
- decision-under-uncertainty integration with 652 is defined;
- simulation integration with 648 is defined;
- ML integration with 643 is defined;
- knowledge integration with 645 is defined;
- memory/personalization integration is defined;
- security/governance boundaries are defined;
- compiler/IR integration is defined;
- native/dependency-free baseline is defined;
- 100 invariants and 100+ acceptance criteria are defined;
- no unresolved architectural dependency blocks implementation.

**BOOTSTRAP-653: COMPLETE.**

---

# 606. Next Architecture Task

Proceed automatically to:

## BOOTSTRAP-654
### Native AI Reinforcement Learning, Markov Decision Processes, POMDP, Policy Learning, Planning Under Uncertainty, Bandits & Sequential Decision Runtime 5.0

652 provides deterministic optimization/planning.

653 provides probabilistic and causal reasoning.

654 will combine them into a dedicated native substrate for **learning and executing policies over sequential decisions and uncertain environments**, while preserving clear boundaries with 643 ML, 651 personalization/exploration, 648 simulation, 652 planning and 653 uncertainty.
:::