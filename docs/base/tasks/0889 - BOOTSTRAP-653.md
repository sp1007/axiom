Tiếp tục với task kế tiếp của chuỗi Axiom: **BOOTSTRAP-653**.

:::writing{variant="document" id="58321" title="BOOTSTRAP-653 — Native AI Probabilistic, Causal & Uncertainty Runtime 5.0"}

# BOOTSTRAP-653
## Native AI Probabilistic Reasoning, Bayesian Modeling, Causal Inference, Uncertainty & Decision-under-Uncertainty Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Reasoning / Statistical Intelligence  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-652  
**Primary dependencies:** 642, 643, 644, 645, 646, 648, 651, 652  
**Security dependencies:** 603, 610  
**Governance dependencies:** 639, 640, 647  
**Target:** Compiler-implementable, native, deterministic-capable, CPU/GPU-capable, provider-extensible.

---

# 1. Mục tiêu

BOOTSTRAP-653 bổ sung cho Axiom một runtime native dành cho:

- xác suất;
- phân phối xác suất;
- Bayesian inference;
- probabilistic programming;
- Bayesian networks;
- factor graphs;
- graphical models;
- uncertainty quantification;
- uncertainty propagation;
- causal graphs;
- causal inference;
- intervention;
- counterfactual reasoning;
- treatment-effect estimation;
- experimental reasoning;
- sensitivity analysis;
- probabilistic time-series;
- decision-making under uncertainty.

Mục tiêu không phải biến Axiom thành một ngôn ngữ thống kê riêng.

Thay vào đó, Axiom cung cấp **native mathematical substrate** để compiler/runtime có thể biểu diễn và thực thi các mô hình xác suất và nhân quả mà không bắt buộc phụ thuộc vào một thư viện bên thứ ba.

---

# 2. Phân biệt các tầng AI

Axiom phải giữ rõ ranh giới:

```text
642 Analytics
    ↓
643 Machine Learning
    ↓
653 Probability / Causality / Uncertainty
    ↓
652 Decision Optimization
    ↓
644 Agent Execution
```

Trong đó:

### 643 — Machine Learning

Trả lời:

> "Mô hình dự đoán điều gì?"

Ví dụ:

```text
P(y | x)
```

### 653 — Probabilistic/Causal

Trả lời:

> "Mức độ không chắc chắn là bao nhiêu?"

và:

> "Điều gì xảy ra nếu ta can thiệp vào X?"

Ví dụ:

```text
P(Y | X)
P(Y | do(X))
P(Y_x | X')
```

### 652 — Decision Optimization

Trả lời:

> "Với các khả năng và ràng buộc đó, nên chọn action nào theo objective đã khai báo?"

653 **không tự chọn hành động**.

652 **không tự suy diễn quan hệ nhân quả**.

---

# 3. Nguyên tắc thiết kế

## 3.1 Correlation != Causation

Axiom tuyệt đối không được tự động biến:

```text
P(Y | X)
```

thành:

```text
P(Y | do(X))
```

hoặc tuyên bố:

```text
X causes Y
```

nếu causal model chưa được khai báo hoặc xác định.

---

## 3.2 Conditioning != Intervention

Hai phép toán:

```text
observe(X = x)
```

và:

```text
intervene(X = x)
```

là hai semantic operation khác nhau.

Compiler phải giữ khác biệt này trong IR.

---

## 3.3 Uncertainty là first-class metadata

Một giá trị có thể là:

```text
value = 10.2
```

nhưng cũng có thể:

```text
value = 10.2 ± uncertainty
```

hoặc:

```text
distribution ~ Normal(...)
```

Axiom không được ép mọi uncertainty thành một scalar duy nhất.

---

# 4. Core Types

## 4.1 Probability

```axiom
probability p = 0.72
```

Invariant:

```text
0 <= p <= 1
```

---

## 4.2 LogProbability

```axiom
log_probability lp = -2.31
```

Cho phép:

- tránh underflow;
- tính likelihood;
- Bayesian inference;
- stable normalization.

---

## 4.3 RandomVariable

```axiom
random X: Real
```

Random variable phải có:

- type;
- domain;
- distribution/model;
- provenance;
- revision.

---

# 5. Distribution Model

Core abstraction:

```axiom
distribution Normal(mean, std)
distribution Bernoulli(p)
distribution Categorical(probabilities)
distribution Poisson(lambda)
distribution Gamma(shape, rate)
distribution Beta(alpha, beta)
```

---

# 6. Required Distributions

Runtime core phải hỗ trợ:

### Discrete

- Bernoulli
- Binomial
- Categorical
- Multinomial
- Poisson
- Geometric

### Continuous

- Uniform
- Normal
- LogNormal
- Exponential
- Gamma
- Beta
- Dirichlet

### Multivariate

- MultivariateNormal
- Mixture
- Empirical

### Structural

- TransformedDistribution
- TruncatedDistribution
- ConditionalDistribution
- JointDistribution

### Extension

Custom distribution phải đi qua provider boundary.

---

# 7. Distribution Interface

Conceptual API:

```axiom
distribution D:
    sample(rng)
    log_pdf(x)
    pdf(x)
    cdf(x)
    quantile(p)
    mean()
    variance()
    entropy()
```

Không phải mọi distribution bắt buộc implement mọi operation.

Compiler phải biết capability:

```text
supports_pdf
supports_cdf
supports_sampling
supports_quantile
supports_entropy
```

---

# 8. Sampling

API:

```axiom
sample(D, rng)
```

Vectorized:

```axiom
sample(D, rng, count=10000)
```

GPU:

```axiom
sample_gpu(D, rng, count=1000000)
```

---

# 9. Random Number Generation

RNG là first-class runtime object.

```axiom
rng = Random(seed=42)
```

Yêu cầu:

- deterministic seed;
- reproducibility;
- stream splitting;
- parallel-safe streams;
- CPU/GPU-compatible sequence semantics khi provider hỗ trợ;
- explicit RNG ownership.

Không được dùng implicit global RNG trong deterministic build nếu không được khai báo.

---

# 10. Numerical Stability

Runtime phải hỗ trợ native:

```text
log_sum_exp()
log_normalize()
stable_softmax()
stable_log_softmax()
```

Inference engine phải ưu tiên log-domain khi cần.

Không được để:

```text
exp(-1000)
```

vô tình trở thành nguồn numerical failure không được phát hiện.

---

# 11. Bayesian Model

Model:

```axiom
model DiseaseModel:
    prior p_disease ~ Bernoulli(0.1)

    likelihood:
        test_positive ~ Bernoulli(sensitivity(p_disease))
```

Core semantic components:

```text
Prior
Likelihood
Posterior
Evidence
PosteriorPredictive
```

---

# 12. Bayesian Identity

Runtime phải bảo toàn:

```text
Posterior ∝ Prior × Likelihood
```

và:

```text
P(θ | D) =
P(D | θ) P(θ)
----------------
P(D)
```

Evidence/marginal likelihood phải được lưu nếu được tính.

---

# 13. Bayesian Hierarchical Models

Hỗ trợ:

```text
population parameter
    ↓
group parameter
    ↓
individual parameter
```

Ví dụ:

```axiom
population_mu ~ Normal(0, 10)

for group in groups:
    group_mu[group] ~ Normal(population_mu, 1)
```

---

# 14. Inference Engines

Axiom phải có provider-independent interface:

```axiom
infer(model, query, engine)
```

Core engine families:

### Exact

- enumeration;
- variable elimination;
- dynamic programming;
- exact discrete inference.

### Approximate

- Monte Carlo;
- importance sampling;
- MCMC;
- Sequential Monte Carlo;
- variational inference;
- Laplace approximation.

---

# 15. MCMC

Provider/core interface:

```text
MCMC
 ├── MetropolisHastings
 ├── Gibbs
 ├── HamiltonianMonteCarlo
 └── NUTS
```

HMC/NUTS có thể nằm trong optimized provider nếu implementation phụ thuộc autodiff/GPU.

Metadata:

```text
chain_count
sample_count
warmup
step_size
acceptance_rate
effective_sample_size
R_hat
seed
```

---

# 16. Sequential Monte Carlo

Hỗ trợ:

```text
particles
weights
resampling
transition
observation
```

Đây là nền tảng cho:

- state estimation;
- tracking;
- dynamic Bayesian models;
- probabilistic robotics;
- time-series inference.

---

# 17. Variational Inference

Interface:

```axiom
posterior = variational_infer(model)
```

Metadata:

```text
variational_family
objective
iterations
convergence
elbo
```

Không được ghi kết quả variational approximation là exact posterior.

---

# 18. Factor Graph

Core objects:

```text
Variable
Factor
FactorGraph
Message
Belief
```

Ví dụ:

```text
X ─ Factor1 ─ Y ─ Factor2 ─ Z
```

Hỗ trợ:

- belief propagation;
- factor elimination;
- message passing;
- approximate inference.

---

# 19. Bayesian Network

```axiom
bayesian_network Weather:
    Cloudy -> Rain
    Cloudy -> Traffic
    Rain -> Traffic
```

Invariant:

```text
DAG
```

Một Bayesian Network core không được chứa cycle.

---

# 20. Conditional Independence

Axiom phải biểu diễn explicit:

```text
X ⟂ Y | Z
```

Graph engine phải hỗ trợ:

- d-separation;
- conditional independence queries.

---

# 21. Causal Model

Core:

```axiom
causal_model Economy:
    InterestRate -> Investment
    Investment -> Growth
    Inflation -> InterestRate
    Inflation -> Growth
```

Model phải phân biệt:

```text
observed variable
latent variable
treatment
outcome
confounder
mediator
collider
instrument
```

---

# 22. Causal Graph

Objects:

```text
CausalGraph
CausalNode
CausalEdge
VariableRole
GraphRevision
```

Edges phải mang provenance.

Ví dụ:

```text
source = domain_expert
source = experiment
source = causal_discovery
source = imported_model
```

---

# 23. DAG Requirement

Structural causal model mặc định yêu cầu:

```text
acyclic directed graph
```

Nếu hệ thống cần feedback loop:

```text
dynamic_causal_model
```

phải được khai báo riêng.

Không được âm thầm cho phép cycle trong DAG.

---

# 24. Structural Causal Model

Core abstraction:

```text
X = fX(Ux)
Y = fY(X, Uy)
Z = fZ(X, Y, Uz)
```

Axiom không yêu cầu mọi SCM phải symbolic.

Có thể sử dụng:

- native functions;
- learned models;
- neural functions;
- external provider.

---

# 25. Intervention

Intervention:

```axiom
do(X = 10)
```

khác với:

```axiom
observe(X = 10)
```

Semantic:

```text
observe:
    condition on X

do:
    replace generating mechanism of X
```

---

# 26. Causal Query

```axiom
query P(Y | do(X = x))
```

Runtime phải giữ query type:

```text
Observational
Interventional
Counterfactual
```

---

# 27. Counterfactual

```axiom
counterfactual:
    Y
    under X = 10
    given observed X = 5
```

Counterfactual yêu cầu model có semantics đủ mạnh.

Không được tạo counterfactual từ correlation-only model.

---

# 28. Potential Outcomes

Axiom hỗ trợ:

```text
Y(0)
Y(1)
```

và:

```text
ATE = E[Y(1) - Y(0)]
```

Metadata phải ghi assumptions:

```text
consistency
SUTVA
positivity
exchangeability
```

Không được coi các assumptions này là mặc định invisible.

---

# 29. Treatment Effect

Core objects:

```text
Treatment
Outcome
Estimand
EffectEstimate
TreatmentEffect
```

Các estimand:

```text
ATE
ATT
ATC
CATE
ITE
```

---

# 30. Adjustment

```axiom
adjust_for {Age, Income, Region}
```

Runtime phải lưu:

```text
adjustment_set
reason
graph_revision
identification_method
```

---

# 31. Backdoor Criterion

Engine phải hỗ trợ kiểm tra backdoor adjustment.

Ví dụ:

```text
X <- Z -> Y
```

có thể yêu cầu:

```text
adjust(Z)
```

Nhưng engine không được tự động điều chỉnh nếu graph chưa được xác nhận.

---

# 32. Frontdoor

Provider/core identification layer hỗ trợ frontdoor identification khi điều kiện thỏa mãn.

Result:

```text
Identified
PartiallyIdentified
NotIdentified
Unknown
```

---

# 33. Do-Calculus

Do-calculus là provider-capable advanced inference.

Không bắt buộc implementation đầy đủ trong smallest runtime profile.

Compiler phải nhận biết:

```text
requires_causal_identification
```

---

# 34. Partial Identification

Nếu dữ liệu/assumptions không đủ để xác định một causal effect:

Không được ép ra một số duy nhất.

Có thể trả:

```text
lower_bound
upper_bound
```

hoặc:

```text
IdentificationStatus.Partial
```

---

# 35. Causal Discovery

Discovery algorithms đi qua provider boundary.

Có thể hỗ trợ:

```text
PC
FCI
GES
NOTEARS
LiNGAM
```

nhưng output phải mang:

```text
DiscoveryGraph
confidence
assumptions
algorithm
dataset
hyperparameters
```

Graph discovered **không mặc nhiên trở thành causal truth**.

---

# 36. Uncertainty

Core type:

```axiom
uncertain<T>
```

Conceptually:

```text
value
distribution
uncertainty
provenance
```

---

# 37. Aleatoric vs Epistemic

Axiom phải giữ metadata:

```text
Aleatoric
Epistemic
Mixed
Unknown
```

Ví dụ:

```text
sensor noise → Aleatoric
unknown parameter → Epistemic
```

Không được tự động gộp hai loại thành một scalar.

---

# 38. Credible Interval

```axiom
credible_interval(posterior, 0.95)
```

Result:

```text
lower
upper
mass
distribution
```

---

# 39. Prediction Interval

Phân biệt:

```text
parameter uncertainty
```

với:

```text
future observation uncertainty
```

Do đó:

```text
credible_interval
```

không được tự động gọi là:

```text
prediction_interval
```

---

# 40. Uncertainty Propagation

Ví dụ:

```text
X ~ Normal(...)
Y = f(X)
```

Runtime hỗ trợ:

```axiom
propagate_uncertainty(Y)
```

Methods:

- analytical;
- linearization;
- Monte Carlo;
- unscented transform;
- sampling-based;
- provider-specific.

---

# 41. Covariance

Core:

```text
Variance
Covariance
Correlation
CovarianceMatrix
PrecisionMatrix
```

Phải hỗ trợ vectorized/GPU representations.

---

# 42. Information Theory

Native primitives:

```text
entropy()
cross_entropy()
kl_divergence()
js_divergence()
mutual_information()
conditional_mutual_information()
```

---

# 43. Calibration

Model calibration metrics:

```text
BrierScore
LogLoss
ECE
Coverage
CalibrationCurve
```

Calibration results phải lưu:

```text
dataset
population
time_range
model_revision
metric_definition
```

---

# 44. Missing Data

Missingness types:

```text
MCAR
MAR
MNAR
```

phải là explicit model assumptions.

Runtime hỗ trợ:

```text
missingness_indicator
imputation_model
joint_model
sensitivity_analysis
```

Không được giả định MAR một cách silent.

---

# 45. Sensitivity Analysis

Core:

```axiom
sensitivity(model, parameter_range)
```

Phân tích:

```text
parameter sensitivity
confounding sensitivity
prior sensitivity
model sensitivity
missing-data sensitivity
```

---

# 46. Time-Series Probability

Native abstractions:

```text
StateSpaceModel
HiddenMarkovModel
DynamicBayesianNetwork
KalmanFilter
ParticleFilter
```

---

# 47. Temporal Causality

Axiom có thể cung cấp:

```text
GrangerCausality
```

nhưng semantic phải ghi rõ:

```text
temporal_predictive causality
```

Không được đồng nhất Granger causality với structural causality.

---

# 48. Experimental Design

Core:

```text
Experiment
TreatmentArm
ControlArm
Randomization
Blocking
Assignment
Outcome
```

Hỗ trợ:

- A/B testing;
- randomized experiments;
- factorial designs;
- sequential experiments;
- adaptive experiments.

---

# 49. Sample Size

Provider/core analytics có thể hỗ trợ:

```text
power()
sample_size()
minimum_detectable_effect()
```

Các assumptions phải được lưu cùng kết quả.

---

# 50. Bayesian Experimental Design

Hỗ trợ:

```text
expected_information_gain
expected_utility
posterior_uncertainty_reduction
```

Có thể tích hợp với 652 để tối ưu experiment selection.

---

# 51. Decision Under Uncertainty

653 cung cấp:

```text
ExpectedUtility
Risk
UtilityDistribution
ScenarioDistribution
```

652 tiêu thụ chúng.

Ví dụ:

```text
ExpectedUtility(action)
```

sau đó:

```text
652.optimize(...)
```

---

# 52. Risk Measures

Hỗ trợ:

```text
Variance
VaR
CVaR
ExpectedShortfall
WorstCase
```

Robust optimization có thể được kết hợp với 652.

---

# 53. Chance Constraints

Ví dụ:

```text
P(delay <= deadline) >= 0.95
```

653 tính probability.

652 dùng kết quả để tìm solution.

---

# 54. Bayesian Decision Theory

Core:

```text
Posterior
Utility
Action
ExpectedUtility
OptimalDecision
```

Nhưng 653 không sở hữu optimization authority.

---

# 55. Scenario Integration

648 tạo:

```text
synthetic scenarios
```

653 có thể phân tích chúng.

Mọi scenario phải giữ:

```text
synthetic = true
```

và:

```text
source_simulation_revision
```

Không được biến synthetic observation thành real-world observation.

---

# 56. ML Integration

643 có thể cung cấp:

```text
predictive_distribution
```

653 có thể chuyển thành:

```text
uncertainty model
```

Nhưng:

```text
prediction != causal effect
```

luôn phải được giữ trong type system/metadata.

---

# 57. Knowledge Graph Integration

645 cung cấp:

```text
semantic graph
```

653 bổ sung:

```text
probabilistic edge
causal edge
uncertainty
confidence
evidence
```

Không nên biến mọi graph edge của 645 thành causal edge.

---

# 58. Agent Integration

644 có thể gọi:

```text
infer()
estimate_effect()
simulate()
query_probability()
sensitivity()
```

Agent không được nhận authority chỉ vì có inference result.

---

# 59. Personalization Integration

651 có thể dùng:

```text
posterior preference
uncertainty
treatment effect
```

để cá nhân hóa.

Ví dụ:

```text
P(preference | behavior)
```

Nhưng personalization không được tự động tạo causal claim.

---

# 60. Evaluation Integration

646 phải có khả năng đánh giá:

- posterior calibration;
- predictive coverage;
- estimator bias;
- variance;
- causal estimator robustness;
- synthetic ground truth;
- simulation recovery;
- sensitivity.

---

# 61. Causal Simulation Validation

648 có thể tạo environment với known causal graph:

```text
ground_truth_graph
ground_truth_effect
```

653 estimator được benchmark against:

```text
estimated_effect
```

Đây là một phương pháp quan trọng để kiểm tra causal engine.

---

# 62. Provenance

Mỗi causal/probabilistic result production-grade phải chứa:

```text
dataset_id
dataset_revision
sample_definition
population
model_revision
graph_revision
assumptions
estimator
inference_engine
provider
provider_version
random_seed
code_hash
timestamp
```

---

# 63. Evidence Provenance

Evidence phải phân loại:

```text
observational
experimental
synthetic
simulated
expert
imported
derived
```

---

# 64. Causal Claim Object

```text
CausalClaim
```

gồm:

```text
cause
effect
estimand
estimate
uncertainty
assumptions
evidence
identification_method
model_revision
```

Không được lưu causal claim chỉ dưới dạng:

```text
"X causes Y"
```

---

# 65. Explainability

653 không expose hidden chain-of-thought.

Thay vào đó trả structured explanation:

```text
model
assumptions
query
identification
adjustment_set
estimator
estimate
uncertainty
diagnostics
sensitivity
provenance
```

---

# 66. Inference Status

Mọi inference result có:

```text
Exact
Approximate
Heuristic
MonteCarlo
Variational
Unknown
Failed
```

Không được gọi approximate result là exact.

---

# 67. Monte Carlo Error

Monte Carlo results phải có metadata về:

```text
sample_count
effective_sample_size
standard_error
MonteCarloError
seed
```

nếu engine có khả năng tính.

---

# 68. Reproducibility

Stochastic result phải hỗ trợ:

```text
seed
engine_revision
algorithm_revision
model_revision
```

Build reproducible phải pin toàn bộ các thành phần cần thiết.

---

# 69. GPU

Các operation có thể vectorize:

```text
sampling
log_pdf
likelihood
posterior evaluation
Monte Carlo
matrix operations
```

có thể chạy GPU.

Không được yêu cầu GPU cho core probability runtime.

---

# 70. Tensor Integration

653 sử dụng tensor primitive từ 643.

Ví dụ:

```text
distribution.parameters : Tensor
samples : Tensor
log_probability : Tensor
```

Không tạo một tensor system thứ hai.

---

# 71. Memory

Probability runtime phải tránh allocation không cần thiết trong:

- sampling;
- likelihood evaluation;
- MCMC;
- particle filtering;
- Monte Carlo.

Cho phép:

```text
arena
preallocated buffers
streaming samples
memory pools
```

---

# 72. Streaming Inference

Hỗ trợ:

```text
update(model, observation)
```

để Bayesian state có thể cập nhật incrementally.

Không bắt buộc load toàn bộ dataset vào RAM.

---

# 73. Online Bayesian Update

Concept:

```text
posterior_t
    +
new evidence
    ↓
posterior_t+1
```

Revision phải được lưu.

---

# 74. Distributed Inference

Provider boundary cho:

```text
distributed MCMC
distributed variational inference
distributed particle filtering
federated Bayesian inference
```

Aggregation phải giữ provenance.

---

# 75. Privacy

653 không tự phá vỡ privacy boundary.

Có thể tích hợp:

- secure aggregation;
- differential privacy provider;
- encrypted computation provider;
- federated inference.

Các capability này đi qua 603/610.

---

# 76. Governance

Production causal model phải chịu:

```text
640 Data Governance
639 Policy
647 Model Governance
```

Protected attributes không được tự động suy luận hoặc sử dụng vượt capability policy.

---

# 77. Compiler Annotations

Axiom compiler nhận diện:

```text
@probability
@random
@distribution
@prior
@likelihood
@posterior
@evidence
@sample
@infer
@factor
@bayesian

@causal
@causal_graph
@cause
@effect
@treatment
@outcome
@confounder
@mediator
@collider
@instrument
@intervention
@counterfactual
@estimand
@adjustment
@sensitivity

@uncertainty
@credible_interval
@prediction_interval
@risk
@utility
@scenario
@robust
```

---

# 78. Generated Metadata

Compiler có thể sinh:

```text
.axprob
.axdist
.axmodel
.axposterior
.axcausal
.axgraph
.axestimand
.axeffect
.axuncertainty
.axinference
```

Các file này phục vụ:

- compiler;
- debugger;
- IDE;
- AI coding agents;
- provenance;
- reproducibility;
- model inspection.

---

# 79. IR Representation

Compiler IR phải phân biệt:

```text
ProbabilityOp
DistributionOp
SampleOp
ObserveOp
InterveneOp
InferOp
ConditionOp
CounterfactualOp
ExpectationOp
VarianceOp
PropagateUncertaintyOp
CausalEffectOp
```

Đặc biệt:

```text
ObserveOp != InterveneOp
```

là invariant compiler-level.

---

# 80. Type-Level Semantic Distinction

Không nên cho phép:

```text
Probability<Observational>
```

được implicit cast thành:

```text
Probability<Interventional>
```

Tương tự:

```text
Prediction
```

không được implicit cast thành:

```text
CausalEffect
```

---

# 81. Causal Effect Type

Conceptual:

```axiom
causal_effect<Treatment, Outcome>
```

chứa:

```text
estimand
estimate
uncertainty
assumptions
```

---

# 82. Distribution Type

Conceptual:

```axiom
Distribution<T>
```

API:

```text
sample
log_prob
prob
mean
variance
entropy
quantile
```

Capability system xác định operation nào hợp lệ.

---

# 83. Query API

```axiom
probability.query(model, query)
causal.query(model, query)
uncertainty.propagate(model)
```

---

# 84. CLI

Axiom CLI bổ sung:

```text
axiom probability sample
axiom probability infer
axiom probability fit
axiom probability posterior
axiom probability predictive

axiom causal graph
axiom causal identify
axiom causal effect
axiom causal intervene
axiom causal counterfactual

axiom uncertainty propagate
axiom uncertainty sensitivity
axiom uncertainty calibrate

axiom model validate
axiom decision risk
```

---

# 85. Runtime Profiles

```text
AXPROB_NONE
AXPROB_CORE
AXPROB_DISTRIBUTION
AXPROB_SAMPLING
AXPROB_INFERENCE
AXPROB_BAYES
AXPROB_GRAPHICAL
AXPROB_CAUSAL
AXPROB_COUNTERFACTUAL
AXPROB_TIME
AXPROB_UNCERTAINTY
AXPROB_DECISION
AXPROB_DISCOVERY
AXPROB_EXPERIMENT
AXPROB_DISTRIBUTED
AXPROB_GPU
AXPROB_AGENT
AXPROB_SIMULATION
AXPROB_FULL
```

Linker chỉ đưa các subsystem được sử dụng vào binary.

---

# 86. Provider Boundary

External providers có thể cung cấp:

```text
advanced MCMC
SMT-based probabilistic inference
symbolic causal identification
GPU kernels
specialized distributions
causal discovery
probabilistic programming backend
```

Nhưng Axiom core không được phụ thuộc bắt buộc vào chúng.

---

# 87. Failure Model

Inference có thể trả:

```text
InvalidModel
InvalidDistribution
NotIdentified
PartiallyIdentified
NumericalFailure
NonConvergence
Divergence
InsufficientSamples
Timeout
Cancelled
ProviderUnavailable
```

---

# 88. Convergence

MCMC/VI/SMC engines phải có convergence metadata khi khả dụng.

Không được coi:

```text
finished_iterations
```

là:

```text
converged
```

---

# 89. Assumption Registry

Mỗi causal model có:

```text
AssumptionSet
```

Ví dụ:

```text
NoUnmeasuredConfounding
Positivity
Consistency
SUTVA
StableMeasurement
CorrectGraph
```

Assumptions có status:

```text
Declared
Verified
PartiallyVerified
Unverified
Violated
Unknown
```

---

# 90. Data Leakage Prevention

Inference pipeline phải biết:

```text
event_time
availability_time
observation_time
intervention_time
```

Không được sử dụng future information để tạo posterior/effect estimate mà không khai báo.

---

# 91. Temporal Provenance

Time-series result phải giữ:

```text
time_origin
window
sampling_frequency
timezone
lag_definition
```

---

# 92. Selection Bias

Causal/effect estimation phải có khả năng ghi:

```text
selection_mechanism
sampling_frame
exclusion_rules
missingness
```

---

# 93. Transportability

Advanced provider có thể hỗ trợ:

```text
transport_effect(source_population, target_population)
```

Nhưng assumptions về population shift phải explicit.

---

# 94. Domain Adaptation

643/651 có thể cung cấp learned representations.

653 có thể đánh giá:

```text
distribution_shift
covariate_shift
prior_shift
concept_shift
```

Không tự động coi distribution shift là causal effect.

---

# 95. Model Comparison

Bayesian model comparison có thể sử dụng:

```text
posterior_predictive
WAIC
LOO
marginal_likelihood
BayesFactor
```

Các metric có assumptions và limitations phải được lưu metadata.

---

# 96. Posterior Predictive Check

```axiom
posterior_predictive_check(model, observed_data)
```

phải có:

```text
observed_statistic
replicated_statistics
discrepancy
coverage
```

---

# 97. Synthetic Ground Truth

648 có thể cung cấp known ground truth:

```text
true_graph
true_distribution
true_effect
true_parameter
```

653 test suite phải sử dụng chúng để kiểm tra inference correctness.

---

# 98. Deterministic Small Models

Core test suite phải có những model nhỏ mà inference có thể tính exact.

Ví dụ:

```text
2-state Bayesian network
```

để kiểm tra:

```text
exact_probability
exact_marginal
exact_conditional
exact_intervention
```

---

# 99. Security

Input:

```text
model
distribution
query
dataset
provider
```

được xem là untrusted.

Không cho phép model metadata tự cấp:

```text
filesystem
network
process
GPU privileged access
```

---

# 100. Capability Isolation

Inference engine chỉ được truy cập capability được cấp.

Ví dụ:

```text
Capability.ProbabilityCompute
Capability.DatasetRead
Capability.GPUCompute
Capability.RandomSource
```

---

# 101. Audit

Production result phải audit được:

```text
who/what requested
model revision
data revision
graph revision
assumptions
engine
provider
seed
parameters
result
```

---

# 102. Performance Architecture

Hot path:

```text
Model
 ↓
Compiled Graph
 ↓
Specialized Kernel
 ↓
Vectorized CPU/GPU
```

Không chạy dynamic interpreter cho mỗi scalar operation nếu compiler có thể specialize.

---

# 103. Compile-Time Specialization

Ví dụ:

```axiom
Normal<f32>
```

có thể compile thành specialized implementation.

Distribution parameters có thể:

```text
compile-time constant
runtime variable
tensor
```

---

# 104. Autodiff Integration

643 cung cấp autodiff.

653 sử dụng nó cho:

- likelihood gradients;
- HMC;
- variational inference;
- Laplace approximation;
- differentiable probabilistic models.

Không xây một autodiff engine riêng.

---

# 105. Mixed Precision

Cho phép:

```text
f32
f64
bf16
fp16
```

nhưng inference engine phải chỉ rõ numerical requirements.

Một số statistical reductions mặc định có thể yêu cầu accumulator precision cao hơn input.

---

# 106. Sparse Models

Graphical models có thể sparse.

Runtime phải hỗ trợ:

```text
sparse factor graph
sparse covariance
sparse precision matrix
```

để tránh memory explosion.

---

# 107. Streaming Samples

Không bắt buộc giữ toàn bộ:

```text
10^9 samples
```

trong RAM.

Có thể sử dụng:

```text
online mean
online variance
quantile sketch
streaming diagnostics
```

---

# 108. Checkpoint

Inference engine hỗ trợ:

```text
save_checkpoint()
resume_checkpoint()
```

Checkpoint chứa:

```text
model_revision
engine_revision
RNG_state
chain_state
optimizer_state
iteration
diagnostics
```

---

# 109. Cancellation

Long-running inference phải hỗ trợ:

```text
cancel
timeout
budget
checkpoint
resume
```

---

# 110. Resource Budget

Có thể giới hạn:

```text
max_time
max_memory
max_samples
max_iterations
max_chains
max_particles
max_gpu_memory
```

Tích hợp 606.

---

# 111. Distributed Sampling

Nếu provider hỗ trợ:

```text
chain parallelism
particle parallelism
data parallel likelihood
```

phải giữ chain identity và provenance.

---

# 112. Federated Inference

Có thể tích hợp:

```text
federated posterior
federated causal estimation
```

nhưng:

- privacy policy;
- secure aggregation;
- participant identity;
- data provenance

phải được giữ.

---

# 113. No Silent Causal Claims

Đây là invariant đặc biệt quan trọng:

```text
predict(X,Y)
```

không bao giờ tự trở thành:

```text
cause(X,Y)
```

---

# 114. No Silent Synthetic Evidence

```text
simulation(data)
```

không được implicit cast thành:

```text
observational(data)
```

---

# 115. No Silent Intervention

```text
condition(X)
```

không được compile thành:

```text
do(X)
```

---

# 116. No Silent Optimality

653 có thể cung cấp:

```text
expected utility
risk
posterior
effect
```

nhưng không tuyên bố:

```text
optimal action
```

trừ khi 652 thực hiện optimization tương ứng.

---

# 117. No Hidden Assumptions

Production causal result phải có:

```text
assumptions
```

metadata.

---

# 118. No Fake Precision

Nếu estimate:

```text
1.234567890
```

nhưng uncertainty lớn, runtime không được ngầm biểu diễn như một kết quả cực kỳ chính xác.

Uncertainty phải được giữ riêng.

---

# 119. Core Invariants

Axiom 653 phải đảm bảo ít nhất:

1. `0 <= probability <= 1`.
2. Distribution probability mass/measure hợp lệ.
3. Log probability có semantic nhất quán.
4. `Observe != Intervene`.
5. `P(Y|X) != P(Y|do(X))` về mặt type/semantic.
6. Causal effect yêu cầu causal model hoặc identification assumptions.
7. Counterfactual yêu cầu structural/potential-outcome semantics.
8. Synthetic evidence không trở thành observational evidence.
9. Approximate inference không được gắn nhãn exact.
10. Monte Carlo phải giữ sample/error metadata khi khả dụng.
11. Random seed được lưu cho reproducibility.
12. DAG causal không được chứa cycle.
13. Missing-data assumptions phải explicit.
14. Causal discovery output phải mang trạng thái discovery.
15. Uncertainty phải được propagate khi operation yêu cầu.
16. Posterior phải nhất quán với prior/likelihood semantics.
17. Production causal claim phải có provenance.
18. Causal claim phải có estimand.
19. Intervention phải được biểu diễn khác conditioning.
20. Inference engine không được tự cấp authority.
21. 653 không được tự biến inference thành policy.
22. 653 không được tự biến inference thành optimization.
23. 653 không được tự biến prediction thành causation.
24. Numerical failure phải detectable.
25. Non-convergence không được báo là convergence.
26. Timeout không được báo là completed exact result.
27. Provider approximation phải được metadata hóa.
28. Model revision phải được pin trong production result.
29. Dataset revision phải được pin trong production result.
30. Graph revision phải được pin trong causal result.
31. Assumptions phải có provenance.
32. Future information không được leak vào historical inference.
33. Time semantics phải explicit trong temporal models.
34. Protected data phải chịu governance.
35. Capability boundary không được bị inference model bypass.

Mục tiêu implementation: **≥70 invariants** và **≥600 acceptance criteria**.

---

# 120. Acceptance Criteria Groups

Test suite phải bao phủ ít nhất:

```text
Probability                 40+
Distribution               60+
Sampling                   40+
Numerical Stability        40+
Bayesian                  70+
Inference                 80+
Graphical Models          50+
Causal Graph               50+
Identification             60+
Counterfactual             40+
Uncertainty                50+
Time Series                40+
Experiments                30+
Simulation Integration     30+
ML Integration             30+
Decision Integration       30+
GPU                         20+
Distributed                20+
Security                   30+
Governance                 30+
Compiler/IR                50+
```

Tổng mục tiêu:

```text
>= 600 acceptance criteria
```

---

# 121. Integration Architecture

```text
                 ┌───────────────┐
                 │      642      │
                 │   Analytics   │
                 └───────┬───────┘
                         │
                 ┌───────▼───────┐
                 │      643      │
                 │      ML       │
                 └───────┬───────┘
                         │
645 Knowledge ────────────┼────────── 648 Simulation
                         │
                 ┌───────▼────────┐
                 │      653       │
                 │ Probability    │
                 │ Causality      │
                 │ Uncertainty    │
                 └───────┬────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
        ┌─────▼─────┐         ┌────▼─────┐
        │    652    │         │   644    │
        │ Decision  │         │  Agent   │
        └───────────┘         └──────────┘
              │
        ┌─────▼─────┐
        │ Execution │
        │  Runtime  │
        └───────────┘
```

---

# 122. Relationship With 651

651:

```text
What does this user/agent prefer?
```

653:

```text
How uncertain are we about that preference?
What causal effect might an intervention have?
```

Ví dụ:

```text
P(preference | behavior)
```

có thể thuộc 651 + 653.

Nhưng:

```text
effect(recommendation -> behavior)
```

là causal inference và thuộc 653.

---

# 123. Relationship With 652

653:

```text
P(outcome | action)
risk(outcome)
causal_effect(action)
```

652:

```text
choose action
subject to constraints
```

Do đó pipeline:

```text
653
  ↓
uncertain outcomes
  ↓
652
  ↓
optimized decision
```

---

# 124. Relationship With 648

648:

```text
generate scenarios
simulate world
```

653:

```text
infer uncertainty
estimate causal effect
analyze probability
```

Có thể:

```text
648 → 653 → 652
```

---

# 125. Relationship With 646

646 kiểm tra:

```text
calibration
coverage
bias
simulation recovery
causal estimator performance
```

653 cung cấp engine cần được đánh giá.

---

# 126. Relationship With 639

639 quyết định:

```text
is this action/query permitted?
```

653 quyết định:

```text
what does the probabilistic/causal model imply?
```

Không được trộn hai trách nhiệm.

---

# 127. Relationship With 640

640 quyết định:

```text
data classification
retention
residency
lineage
privacy
```

653 tiêu thụ data theo governance constraints.

---

# 128. AI-Friendly Metadata

Compiler phải tạo machine-readable description:

```text
model
variables
domains
distributions
dependencies
assumptions
inference_engine
estimand
uncertainty
provenance
limitations
```

Mục tiêu là AI agent có thể inspect model mà không cần đọc toàn bộ source.

---

# 129. Example

```axiom
@causal
model TreatmentEffect:

    @confounder age
    @confounder income

    @treatment treatment
    @outcome outcome

    age -> treatment
    age -> outcome

    income -> treatment
    income -> outcome

    treatment -> outcome

estimate = causal.effect(
    model = TreatmentEffect,
    treatment = treatment,
    outcome = outcome,
    adjustment = {age, income}
)
```

Result:

```text
estimand
estimate
standard_error
interval
assumptions
adjustment_set
identification_method
dataset_revision
model_revision
```

---

# 130. Example: Probabilistic Prediction

```axiom
model Demand:
    demand ~ Poisson(lambda)

posterior = infer(Demand)

future = posterior.predictive()
```

Không chỉ trả:

```text
42
```

mà có thể trả:

```text
distribution
mean
median
quantiles
variance
interval
```

---

# 131. Example: Decision Integration

```axiom
demand = probabilistic.predict(Demand)

decision = decision.optimize(
    objective = expected_profit(demand),
    constraints = inventory_limit
)
```

653 cung cấp distribution.

652 thực hiện optimization.

---

# 132. Example: Intervention

```axiom
observed = causal.query(
    P(outcome | treatment)
)

intervened = causal.query(
    P(outcome | do(treatment = 1))
)
```

Compiler giữ hai query là hai operation khác nhau.

---

# 133. Example: Counterfactual

```axiom
cf = causal.counterfactual(
    outcome,
    intervention = treatment = 1,
    observed = treatment = 0
)
```

Chỉ hợp lệ nếu model có đủ counterfactual semantics.

---

# 134. Example: Uncertainty Propagation

```axiom
temperature ~ Normal(25, 2)

energy = f(temperature)

result = uncertainty.propagate(energy)
```

Result giữ distribution/interval thay vì ép scalar.

---

# 135. Minimal Runtime

Một binary chỉ sử dụng deterministic distributions không nên kéo toàn bộ:

```text
MCMC
causal discovery
GPU provider
distributed runtime
```

Linker phải loại bỏ chúng.

---

# 136. Full AI Runtime

`AXPROB_FULL` có thể bao gồm:

```text
Probability
Distributions
Sampling
Bayesian
MCMC
VI
Graphical Models
Causal Inference
Counterfactuals
Time Series
Uncertainty
Experimental Design
GPU
Distributed
Simulation
Decision Integration
Agent Integration
```

---

# 137. Compiler Diagnostics

Compiler phải cảnh báo:

```text
CAUSAL001:
Observational probability used as causal effect.
```

```text
CAUSAL002:
Intervention requires an explicit causal model.
```

```text
PROB001:
Distribution normalization cannot be proven.
```

```text
PROB002:
Inference engine returned approximate posterior.
```

```text
CAUSAL003:
Causal identification assumptions are unverified.
```

```text
UNC001:
Uncertainty discarded by implicit scalar conversion.
```

---

# 138. Design Rule

Axiom 653 phải ưu tiên:

```text
explicit semantics
>
silent convenience
```

đặc biệt đối với:

- causality;
- uncertainty;
- interventions;
- assumptions;
- synthetic data;
- approximate inference.

---

# 139. Final Architecture

BOOTSTRAP-653 hoàn thiện tầng:

```text
             AI DATA
                │
        ┌───────▼────────┐
        │ ML / Analytics │
        │   642 / 643    │
        └───────┬────────┘
                │
        ┌───────▼────────────┐
        │       653          │
        │ Probability        │
        │ Bayesian           │
        │ Causal             │
        │ Counterfactual     │
        │ Uncertainty        │
        └───────┬────────────┘
                │
       ┌────────┴────────┐
       │                 │
 ┌─────▼─────┐     ┌────▼─────┐
 │    652    │     │    644   │
 │ Decision  │     │  Agent   │
 └─────┬─────┘     └────┬─────┘
       │                 │
       └────────┬────────┘
                ▼
          Native Execution
```

---

# 140. Completion Definition

BOOTSTRAP-653 được coi là hoàn thành khi:

- probability model được biểu diễn native;
- distribution system hoạt động;
- sampling deterministic-capable;
- Bayesian inference có provider boundary;
- causal graph native;
- intervention khác conditioning ở semantic/IR level;
- counterfactual có explicit requirements;
- uncertainty first-class;
- causal assumptions/provenance bắt buộc;
- synthetic/observational evidence được phân biệt;
- ML/analytics/simulation/decision/agent integration hoàn chỉnh;
- CPU/GPU execution path được xác định;
- distributed provider boundary được xác định;
- security/governance boundary được xác định;
- compiler IR và diagnostics được xác định;
- metadata/AI inspection artifacts được xác định;
- ≥70 invariants;
- ≥600 acceptance criteria;
- implementation không yêu cầu third-party library trong core runtime.

**BOOTSTRAP-653 — COMPLETE.**

**Next architecture task: BOOTSTRAP-654 — Native AI Symbolic Reasoning, Logic, Rules, Theorem Proving, Formal Knowledge & Neuro-Symbolic Runtime 5.0.**

:::