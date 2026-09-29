# BOOTSTRAP-376 — Axiom Probabilistic Computing, Statistics & Stochastic Numerical Engine

Sau **Graph Computing**, Axiom đã có gần đủ nền tảng cho numerical/AI/scientific computing cấp thấp. Bước tiếp theo nên bổ sung **probabilistic và statistical computing**.

Mục tiêu không phải tạo một `Probability` hay `Distribution` runtime primitive trong Core. Thay vào đó, xây một semantic layer generic có thể tận dụng:

- Numeric;
- Tensor;
- Sparse;
- Graph;
- AD;
- Expression Graph;
- Parallel;
- SIMD;
- GPU;
- Comptime.

Điểm quan trọng là **randomness phải có semantics rõ ràng**, không để `random()` trở thành một global mutable state khiến compiler không thể tối ưu.

---

## 1. Ba khái niệm phải tách biệt

Axiom phân biệt:

```text
Randomness
Probability
Statistics
```

### Randomness

Nguồn sinh mẫu:

```text
RNG
```

### Probability

Mô hình phân phối:

```text
Distribution<T>
```

### Statistics

Phép tính trên dữ liệu:

```text
mean
variance
covariance
quantile
histogram
...
```

Ba lớp này không được nhập làm một.

---

# 2. RNG không phải global state

Không nên có semantics kiểu:

```text
random()
random()
random()
```

dựa trên một global hidden RNG.

Thay vào đó:

```text
rng.next()
```

RNG là một value/state có ownership rõ ràng.

Ví dụ:

```text
let rng = Rng(seed)

let a = rng.next()
let b = rng.next()
```

Compiler biết state dependency.

---

# 3. Random state là resource

RNG state:

```text
Rng<S>
```

là stateful value.

Có thể:

```text
move
copy
split
clone
```

nhưng semantics phải explicit.

Đặc biệt:

```text
Copy<Rng>
```

không được vô tình tạo hai RNG có cùng state nếu programmer không muốn.

---

# 4. RNG splitting

Parallel computation cần:

```text
rng.split()
```

Ví dụ:

```text
let (r1, r2) = rng.split()
```

Mỗi RNG có stream riêng.

Điều này tốt hơn việc các worker cùng truy cập:

```text
global_rng
```

vì global RNG tạo contention và phá deterministic parallelism.

---

# 5. Deterministic randomness

Cùng:

```text
seed
algorithm
stream
configuration
```

phải có khả năng tạo cùng sequence trong deterministic mode.

Nhưng không nên yêu cầu mọi hardware backend phải cho cùng bit pattern nếu algorithm/backend contract không đảm bảo điều đó.

Phải phân biệt:

```text
DeterministicRng
PortableRng
FastRng
HardwareRng
```

---

# 6. Cryptographic RNG

Cryptographic randomness không được đồng nhất với simulation RNG.

Tách:

```text
SimulationRng
SecureRng
EntropySource
```

`SecureRng` có thể phụ thuộc OS/hardware entropy.

Không được để compiler thay:

```text
SecureRng
```

bằng PRNG thông thường.

---

# 7. Distribution là generic abstraction

Không cần hierarchy runtime:

```text
class Distribution
```

Thay vào đó:

```text
trait Distribution {
    type Sample
    fn sample(...)
    fn pdf(...)
    fn cdf(...)
}
```

Các distribution:

```text
Normal
Uniform
Bernoulli
Binomial
Poisson
Exponential
Gamma
Beta
Categorical
MultivariateNormal
...
```

đều là library types.

---

# 8. Distribution không nhất thiết là object

Ví dụ:

```text
let d = Normal::new(mu, sigma)
```

Compiler có thể biết toàn bộ type:

```text
Normal<f32>
```

và inline:

```text
sample(d, rng)
```

thành native arithmetic.

Không cần:

```text
heap allocation
vtable
object header
```

---

# 9. Distribution properties

Compiler có thể hiểu metadata:

```text
mean
variance
support
continuous/discrete
parameter_count
reparameterizable
differentiable
```

Những metadata này phục vụ optimization và AD.

---

# 10. Sampling semantics

Sampling:

```text
sample(distribution, rng)
```

là effectful operation vì nó tiêu thụ RNG state.

Compiler không được CSE:

```text
sample(d, rng)
```

thành một giá trị duy nhất nếu điều đó thay đổi RNG semantics.

---

# 11. Pure distribution functions

Ngược lại:

```text
pdf(d, x)
cdf(d, x)
log_pdf(d, x)
```

có thể là pure nếu distribution không chứa external state.

Do đó compiler được phép:

- CSE;
- inline;
- vectorize;
- fuse;
- GPU lower.

---

# 12. Log probability

Machine learning thường cần:

```text
log_prob
```

thay vì:

```text
log(pdf(x))
```

Axiom nên coi đây là semantic operation riêng khi distribution cung cấp nó.

Điều này tránh:

```text
underflow
overflow
```

do `pdf` quá nhỏ.

---

# 13. Numerical stability

Compiler không được tự động thay:

```text
log(pdf(x))
```

bằng:

```text
log_pdf(x)
```

nếu numerical semantics không chứng minh tương đương.

Nhưng library/compiler có thể cung cấp rewrite:

```text
NumericallyEquivalent
```

khi numerical contract cho phép.

Điều này dùng lại framework từ task 372.

---

# 14. Statistics primitives

Library cung cấp:

```text
mean
weighted_mean
variance
stddev
covariance
correlation
median
quantile
percentile
min
max
argmin
argmax
histogram
```

Những operation này phải có numerical contract.

---

# 15. Variance algorithm

Không nên định nghĩa variance bằng:

```text
sum(x*x)/n - mean*mean
```

như semantics duy nhất.

Library có thể dùng:

```text
Welford
pairwise reduction
online variance
```

Compiler có thể chọn implementation dựa trên:

```text
NumericalContract
```

---

# 16. Streaming statistics

Dữ liệu lớn:

```text
stream → statistics
```

không cần materialize toàn bộ tensor.

Có thể có:

```text
OnlineMean
OnlineVariance
OnlineCovariance
```

là stateful value types.

Ownership semantics bình thường.

---

# 17. Weighted statistics

Weight:

```text
w_i
```

phải có semantics explicit:

```text
weighted_mean(x, w)
```

Không được compiler giả định weight normalization nếu API không yêu cầu.

---

# 18. Sampling Tensor

Có thể:

```text
sample(d, rng, shape)
```

tạo:

```text
Tensor<T, Shape>
```

Compiler có thể lower thành:

```text
parallel RNG
vectorized distribution sampling
GPU kernel
```

nếu RNG semantics cho phép.

---

# 19. Parallel random generation

Đây là vấn đề rất quan trọng.

Không được:

```text
parallel_for {
    global_rng.next()
}
```

một cách ngầm định.

Thay vào đó:

```text
parallel_sample(rng, distribution, shape)
```

có semantic contract về stream partition.

---

# 20. Counter-based RNG

Một backend rất phù hợp GPU là:

```text
counter + key → random value
```

Mỗi element có thể tạo random độc lập mà không cần shared mutable state.

Compiler có thể map:

```text
sample_at(seed, index)
```

thành counter-based RNG.

---

# 21. Reproducible parallel sampling

Axiom nên hỗ trợ:

```text
DeterministicSamplingPolicy
```

để:

```text
sample(shape, workers=1)
sample(shape, workers=16)
```

có thể tạo cùng sequence **nếu API đã yêu cầu parallel reproducibility**.

Nếu không yêu cầu, compiler được tự do tối ưu.

---

# 22. Monte Carlo

Một primitive/library abstraction:

```text
monte_carlo(f, samples)
```

có thể lower thành:

```text
parallel
SIMD
GPU
```

với:

```text
random sampling
reduction
confidence estimate
```

---

# 23. Reduction numerical semantics

Monte Carlo:

```text
sum(samples)
```

phải tuân:

```text
Strict
Deterministic
Fast
```

đã định nghĩa ở Numeric/Parallel engine.

---

# 24. Probability distributions + AD

Một số distribution có thể differentiable theo parameter.

Ví dụ:

```text
Normal(mu, sigma)
```

có derivative theo:

```text
mu
sigma
```

Axiom AD engine có thể sử dụng derivative rules.

Nhưng:

```text
sample()
```

không mặc định differentiable.

---

# 25. Reparameterization

Để AD qua sampling:

```text
z = mu + sigma * epsilon
```

với:

```text
epsilon ~ Normal(0,1)
```

distribution có thể cung cấp:

```text
reparameterize()
```

Compiler/AD engine có thể sử dụng semantic rule này.

---

# 26. Score-function estimator

Một distribution không reparameterizable có thể sử dụng:

```text
score_function
```

hoặc:

```text
REINFORCE
```

nhưng đây là statistical estimator semantics, không phải derivative thông thường.

AD engine phải phân biệt:

```text
ExactDerivative
ReparameterizedGradient
Estimator
Subgradient
```

---

# 27. Random variables vs samples

Không nên tạo runtime symbolic object bắt buộc:

```text
RandomVariableNode
```

Chỉ khi symbolic/probabilistic computation được yêu cầu mới tạo expression graph.

Thông thường:

```text
sample
```

chỉ là giá trị runtime.

---

# 28. Bayesian primitives

Library có thể cung cấp:

```text
prior
likelihood
posterior
log_joint
```

nhưng không tạo một Bayesian runtime hierarchy.

Các framework MCMC/VI có thể xây bên trên:

```text
AD
Tensor
Graph
Randomness
```

---

# 29. MCMC

Các algorithms:

```text
MetropolisHastings
HamiltonianMonteCarlo
NUTS
Gibbs
```

là library abstractions.

Compiler có thể tối ưu:

```text
gradient
random generation
state transitions
```

nhưng không cần hiểu toàn bộ statistical theory trong Core.

---

# 30. Optimization boundary

Một statistical computation có thể trở thành:

```text
ExpressionGraph
        ↓
AD
        ↓
Tensor
        ↓
Parallel
        ↓
SIMD/GPU
```

Ví dụ:

```text
log_likelihood(parameters, data)
```

có thể được:

```text
differentiate
fuse
vectorize
parallelize
GPU lower
```

mà không cần runtime reflection.

---

# 31. CompilerDB

Bổ sung:

```text
ProbabilityDB
DistributionDB
DistributionTypeDB
DistributionParameterDB
DistributionSupportDB
DistributionMomentDB
DistributionPdfDB
DistributionCdfDB
DistributionLogPdfDB
DistributionSampleDB
DistributionDerivativeDB
DistributionReparameterizationDB

RngDB
RngTypeDB
RngStateDB
RngSeedDB
RngStreamDB
RngSplitDB
RngDeterminismDB
RngParallelDB
RngCounterDB
RngEntropyDB
SecureRngDB

StatisticsDB
MeanDB
VarianceDB
CovarianceDB
CorrelationDB
QuantileDB
HistogramDB
OnlineStatisticsDB
WeightedStatisticsDB
StatisticsReductionDB

MonteCarloDB
SamplingDB
SamplingPlanDB
SamplingParallelDB
SamplingGpuDB
SamplingNumericalDB

BayesianDB
PriorDB
LikelihoodDB
PosteriorDB
McmcDB
McmcKernelDB
VariationalInferenceDB

ProbabilisticExpressionDB
ProbabilisticGraphDB
ProbabilisticADDB
ProbabilisticProofDB
ProbabilisticCostModelDB
ProbabilisticVerificationDB
```

---

# 32. MIR additions

Semantic MIR:

```text
RNG_CREATE
RNG_SEED
RNG_NEXT
RNG_SPLIT
RNG_SAMPLE_AT
RNG_ENTROPY

DIST_CREATE
DIST_PDF
DIST_LOG_PDF
DIST_CDF
DIST_SAMPLE
DIST_MOMENT

STAT_MEAN
STAT_VARIANCE
STAT_COVARIANCE
STAT_CORRELATION
STAT_QUANTILE
STAT_HISTOGRAM

STAT_ONLINE_UPDATE
STAT_REDUCE

MONTE_CARLO_BEGIN
MONTE_CARLO_SAMPLE
MONTE_CARLO_REDUCE
MONTE_CARLO_END

PROB_LOG_JOINT
PROB_REPARAMETERIZE
PROB_SCORE_ESTIMATE
```

Sau semantic optimization, các operation này có thể biến thành arithmetic/vector/parallel/GPU instructions.

---

# 33. Proof system

Cần:

```text
RngStateProof
RngDeterminismProof
RngParallelProof
RngStreamProof
DistributionParameterProof
DistributionSupportProof
DistributionNumericalProof
DistributionDerivativeProof
ReparameterizationProof
StatisticsNumericalProof
StatisticsReductionProof
SamplingShapeProof
SamplingAliasProof
SamplingParallelProof
SamplingGpuProof
MonteCarloProof
ProbabilisticADProof
ProbabilisticDeterminismProof
ProbabilisticVerificationProof
```

---

# 34. Compiler optimization

Compiler có thể thực hiện:

```text
sample generation fusion
RNG stream fusion
distribution specialization
constant parameter specialization
vectorized sampling
parallel sampling
GPU sampling
log-pdf fusion
statistical reduction fusion
Monte-Carlo fusion
```

Ví dụ:

```text
sample Normal(0, 1)
```

không cần instantiate runtime object.

Có thể trở thành trực tiếp:

```text
RNG instructions
+
normal transform
```

---

# 35. Quan trọng: randomness là effect

Trong Effect System của Axiom:

```text
pdf(d,x)
```

có thể:

```text
Pure
```

nhưng:

```text
sample(d,rng)
```

có:

```text
RandomEffect
```

hoặc effect tương đương.

Điều này ngăn compiler thực hiện các transformation sai.

Ví dụ:

```text
let a = sample(d, rng)
let b = sample(d, rng)
```

không được CSE thành:

```text
let a = sample(d, rng)
let b = a
```

---

# 36. Nhưng random state vẫn phải tối ưu được

Nếu compiler chứng minh:

```text
rng
```

chỉ được sử dụng một lần, state có thể scalarize.

Nếu parallel:

```text
rng.split()
```

có thể được compile thành independent streams.

Do đó randomness **không đồng nghĩa với chậm**.

---

# 37. GPU integration

Sampling:

```text
sample(d, rng, shape)
```

có thể:

```text
CPU scalar
CPU SIMD
CPU parallel
GPU
```

Compiler chọn backend dựa trên:

```text
shape
distribution
RNG
numerical contract
cost
target features
```

Không thay đổi semantics.

---

# 38. Graph integration

Graph Monte Carlo:

```text
random_walk(graph, rng, start)
```

có thể trở thành:

```text
Graph
+
RNG
+
Parallel
+
GPU
```

Ví dụ:

```text
N random walks
```

có thể partition thành N independent streams.

Đây là một trong những lý do Graph + Probability nên cùng sử dụng semantic RNG thay vì global random state.

---

# 39. Invariants

### `APROB-01`
Randomness phải có explicit state hoặc explicit entropy source.

### `APROB-02`
Không có hidden global RNG trong safe semantic model.

### `APROB-03`
RNG state phải tuân ownership semantics.

### `APROB-04`
RNG copying phải có semantics rõ ràng.

### `APROB-05`
RNG splitting phải tạo stream semantics rõ ràng.

### `APROB-06`
Deterministic RNG phải preserve declared reproducibility contract.

### `APROB-07`
Secure entropy không được thay bằng ordinary PRNG.

### `APROB-08`
Sampling là effectful operation.

### `APROB-09`
Pure distribution evaluation phải có thể được compiler optimize.

### `APROB-10`
Compiler không được CSE sampling nếu làm thay đổi RNG semantics.

### `APROB-11`
Distribution parameters phải được type-check.

### `APROB-12`
Distribution support phải được tôn trọng.

### `APROB-13`
Invalid distribution parameters phải được xử lý explicit.

### `APROB-14`
Numerical stability phải tuân NumericalContract.

### `APROB-15`
`log_pdf` có semantics riêng nếu distribution cung cấp implementation ổn định.

### `APROB-16`
Statistics reductions phải tuân reduction/numerical contract.

### `APROB-17`
Parallel sampling phải có explicit stream partition semantics.

### `APROB-18`
Parallel RNG không được phụ thuộc vào shared mutable global state.

### `APROB-19`
GPU RNG phải preserve declared RNG semantics.

### `APROB-20`
Counter-based sampling phải preserve index/stream identity contract.

### `APROB-21`
AD không được tự động differentiate sampling nếu chưa có valid estimator/rule.

### `APROB-22`
Reparameterization phải là explicit semantic capability.

### `APROB-23`
Score-function estimators phải phân biệt với exact derivatives.

### `APROB-24`
Monte Carlo reductions phải tuân numerical semantics.

### `APROB-25`
Bayesian abstractions không được yêu cầu runtime object hierarchy.

### `APROB-26`
Statistical state objects phải tuân ownership/drop semantics.

### `APROB-27`
Compiler được phép specialize distribution khi parameters compile-time known.

### `APROB-28`
Probabilistic abstractions có thể compile away hoàn toàn khi semantics cho phép.

### `APROB-29`
Optimization không được thay đổi random sequence khi reproducibility contract yêu cầu.

### `APROB-30`
Probability/statistics layer không được tạo mandatory runtime dependency cho chương trình không sử dụng nó.

---

## Vị trí của 376 trong Axiom

Sau task này, phần numerical/AI foundation sẽ có cấu trúc khá hoàn chỉnh:

```text
                    Axiom Numerical / AI Foundation
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
       Numeric              Tensor                Graph
          │                    │                    │
          ├───────┐       ┌────┼────┐          ┌────┼────┐
          │       │       │    │    │          │    │    │
       Linear   FFT      AD   Expr Sparse      BFS  GNN  Graph
       Algebra                 │              │
          │                    │              │
          └──────────────┬─────┴──────────────┘
                         │
                Parallel / SIMD / GPU
                         │
          ┌──────────────┴──────────────┐
          │                             │
      Scientific                   Probabilistic
      Computing                     Computing
          │                             │
      PDE/Solvers                  Statistics
      Simulation                   Monte Carlo
                                   Bayesian
```

Điểm quan trọng nhất của task 376 là **RNG được đưa vào semantic/effect model một cách nghiêm túc**. Điều này giúp Axiom vừa có khả năng viết ML/scientific software, vừa không phá những nguyên tắc cốt lõi đã xây dựng: **determinism khi cần, zero-cost abstraction, ownership rõ ràng, parallel/GPU friendly và compiler được quyền tối ưu mạnh**.