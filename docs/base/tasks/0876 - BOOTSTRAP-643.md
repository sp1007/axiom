Tiếp tục với **BOOTSTRAP-643 — Native Distributed Machine Learning, Tensor, Dataset, Feature Store, Model Execution, Training/Inference & AI Compute Runtime 5.0**.

:::writing{variant="document" id="58317" title="BOOTSTRAP-643 — Native Distributed Machine Learning, Tensor, Dataset, Feature Store, Model Execution, Training/Inference & AI Compute Runtime 5.0"}
# BOOTSTRAP-643
## Native Distributed Machine Learning, Tensor, Dataset, Feature Store, Model Execution, Training/Inference & AI Compute Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI / Machine Learning / Tensor / Model Execution Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-642

---

# 1. Mục tiêu

BOOTSTRAP-643 bổ sung nền tảng AI/ML native cho Axiom.

Mục tiêu:

- tensor;
- multidimensional arrays;
- automatic differentiation;
- neural-network primitives;
- CPU/GPU execution;
- accelerator execution;
- model representation;
- model serialization;
- training;
- inference;
- dataset pipeline;
- feature store;
- distributed training;
- distributed inference;
- checkpoint;
- optimizer;
- mixed precision;
- quantization;
- graph compilation;
- kernel fusion;
- memory planning;
- model serving;
- batching;
- streaming inference;
- model versioning;
- experiment metadata;
- reproducibility;
- integration với 630 distributed compute;
- integration với 642 analytical runtime;
- integration với 614 GPU/accelerator;
- integration với 640 data governance.

Axiom phải có khả năng xây dựng AI/ML application mà không bắt buộc:

- Python;
- PyTorch;
- TensorFlow;
- JAX;
- CUDA;
- third-party inference runtime.

Các hệ thống trên có thể được hỗ trợ bằng provider/adaptor.

---

# 2. Architectural boundary

| Layer | Responsibility |
|---|---|
| 614 | GPU/accelerator/device |
| 615 | graphics/compute command infrastructure |
| 606 | resource governance |
| 607 | execution |
| 608 | synchronization |
| 612 | serialization |
| 628 | distributed data |
| 630 | distributed compute |
| 634 | streaming |
| 638 | credential lifecycle |
| 640 | data governance |
| 642 | analytics/data processing |
| **643** | ML/AI computation |

643 không thay thế:

- 614 GPU abstraction;
- 630 distributed worker placement;
- 642 analytical engine.

Nó sử dụng chúng.

---

# 3. Core design

Axiom ML stack:

```text
                    Axiom AI
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      Tensor         Dataset        Model
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 Compute Graph
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
            CPU       GPU     Accelerator
             │         │         │
             └─────────┼─────────┘
                       ▼
               Execution Runtime
                       │
              ┌────────┴────────┐
              ▼                 ▼
           Training          Inference
```

---

# 4. Design principles

1. Tensor là primitive typed.
2. Shape được kiểm tra càng sớm càng tốt.
3. Dtype là explicit.
4. Device placement là explicit.
5. Host/device transfer là visible.
6. Không có implicit GPU synchronization trong hot path.
7. Không bắt buộc CUDA.
8. CPU luôn là fallback.
9. Memory ownership rõ ràng.
10. Không yêu cầu GC.
11. Graph execution có thể compile.
12. Eager execution vẫn được hỗ trợ.
13. Training và inference dùng chung tensor core.
14. Model graph không phụ thuộc Python object graph.
15. Serialization deterministic.
16. Checkpoint có version.
17. Distributed training không giả định exactly-once.
18. Randomness phải có seed/stream rõ ràng.
19. Data lineage tích hợp 640.
20. Resource usage tích hợp 606.
21. Security không bị bypass bởi GPU kernels.
22. External ML runtimes là provider.

---

# 5. Core objects

```text
Tensor
TensorView
TensorShape
TensorStride
TensorLayout
TensorDType
TensorDevice
TensorBuffer
TensorStorage
TensorIndex
TensorSlice
TensorMask

ComputeGraph
GraphNode
GraphValue
GraphInput
GraphOutput

Operator
Kernel
KernelProvider

Gradient
AutogradGraph
GradientTape

Parameter
ParameterSet
Module
Model

Dataset
DatasetSchema
DatasetShard
DatasetIterator
DataLoader
Batch
Sampler

Feature
FeatureSet
FeatureStore

Optimizer
LearningRateSchedule
LossFunction
Metric

TrainingJob
TrainingStep
TrainingState
Checkpoint

InferenceSession
InferenceRequest
InferenceResponse
BatchRequest

ModelArtifact
ModelVersion
ModelSignature
ModelRegistry
```

---

# 6. Tensor

Tensor là multidimensional typed value.

```text
Tensor<T, Shape>
```

Ví dụ:

```text
Tensor<f32, [32, 224, 224, 3]>
```

---

# 7. Dynamic shape

Runtime shape được hỗ trợ:

```text
Tensor<f32, [?, 224, 224, 3]>
```

---

# 8. Symbolic shape

Có thể khai báo:

```text
batch = N
Tensor<f32, [N, 768]>
```

---

# 9. Shape checking

Compiler có thể phát hiện:

```text
[N, 768] × [512, 512]
```

là không tương thích.

---

# 10. Runtime shape errors

Nếu shape chỉ biết runtime:

```text
ShapeMismatch
```

được phát sinh trước kernel execution.

---

# 11. Tensor rank

Rank là số dimensions.

---

# 12. Dimension

Dimension có thể:

- constant;
- symbolic;
- dynamic.

---

# 13. Dtype

Core:

```text
bool
i8/i16/i32/i64
u8/u16/u32/u64
f16
bf16
f32
f64
complex64
complex128
```

---

# 14. Quantized dtype

Optional:

```text
qint8
quint8
qint4
```

với scale/zero-point metadata.

---

# 15. Tensor device

```text
CPU
GPU
NPU
TPU-like Accelerator
DSP
CustomAccelerator
```

---

# 16. Device identity

Device dùng generation-safe handle từ 614.

---

# 17. Tensor storage

```text
Owned
Borrowed
Mapped
Unified
DeviceLocal
Shared
```

---

# 18. Tensor lifetime

Tensor không yêu cầu garbage collector.

---

# 19. Tensor buffer

Buffer được quản lý bằng deterministic ownership.

---

# 20. Tensor view

View không copy dữ liệu.

---

# 21. Slice

```text
tensor[:, 10:20]
```

tạo view nếu layout cho phép.

---

# 22. Stride

Tensor lưu:

```text
shape
stride
offset
```

---

# 23. Contiguous

API:

```text
tensor.is_contiguous()
tensor.contiguous()
```

---

# 24. Layout

Core layouts:

```text
RowMajor
ColumnMajor
Strided
Blocked
ChannelsFirst
ChannelsLast
```

---

# 25. Layout conversion

Compiler/runtime có thể chèn conversion.

---

# 26. Broadcasting

Axiom hỗ trợ broadcasting theo quy tắc deterministic.

---

# 27. Elementwise operators

```text
+
-
*
/
%
pow
exp
log
sqrt
abs
min
max
```

---

# 28. Comparison

```text
==
!=
<
<=
>
>=
```

trả boolean tensor.

---

# 29. Logical operators

```text
and
or
xor
not
```

---

# 30. Reduction

```text
sum
mean
min
max
prod
argmin
argmax
```

---

# 31. Axis semantics

Reduction có thể chỉ định:

```text
axis
keepdim
```

---

# 32. Matrix operations

```text
matmul
dot
outer
```

---

# 33. Batched matrix multiplication

```text
batch_matmul
```

---

# 34. Linear algebra

```text
transpose
inverse
solve
det
norm
svd
qr
eigh
```

Một số operations có thể là provider-dependent.

---

# 35. Convolution

Core conceptual operator:

```text
conv1d
conv2d
conv3d
```

---

# 36. Pooling

```text
max_pool
avg_pool
adaptive_pool
```

---

# 37. Activation

```text
relu
gelu
silu
sigmoid
tanh
softmax
log_softmax
```

---

# 38. Normalization

```text
batch_norm
layer_norm
group_norm
rms_norm
```

---

# 39. Attention

Native primitive:

```text
scaled_dot_product_attention
```

---

# 40. Embedding

```text
embedding_lookup
```

---

# 41. Scatter/gather

```text
gather
scatter
index_select
index_put
```

---

# 42. Masking

Boolean tensor can select values.

---

# 43. Padding

Explicit padding operator.

---

# 44. Reshape

Reshape không copy nếu stride-compatible.

---

# 45. Flatten

View where possible.

---

# 46. Concatenate

```text
concat
stack
split
chunk
```

---

# 47. Copy semantics

Copy chỉ xảy ra khi required.

---

# 48. Device transfer

```text
tensor.to(device)
```

---

# 49. Transfer semantics

Transfer trả về tensor mới trên device đích.

---

# 50. Explicit synchronization

```text
device.wait()
stream.wait()
```

---

# 51. Async tensor operation

Operations có thể trả future/event-backed result.

---

# 52. Compute stream

```text
ComputeStream
```

từ 614/615.

---

# 53. Stream semantics

Tensor operations trên cùng stream giữ ordering.

---

# 54. Cross-stream dependency

Dùng event/fence từ 608/614.

---

# 55. CPU fallback

Mọi mandatory operator phải có CPU implementation hoặc explicit unsupported state.

---

# 56. Kernel provider

```text
NativeCPUProvider
NativeGPUProvider
PlatformGPUProvider
ExternalProvider
TestProvider
```

---

# 57. CPU SIMD

Kernels sử dụng:

```text
SSE
AVX2
AVX-512
NEON
SVE
```

khi target hỗ trợ.

---

# 58. GPU provider

Có thể map sang:

```text
Vulkan
DirectML
Metal
WebGPU
CUDA provider
ROCm provider
```

nhưng không dependency core.

---

# 59. Accelerator provider

Provider có:

```text
capabilities
supported_dtypes
supported_ops
memory_model
```

---

# 60. Kernel dispatch

Dispatch dựa trên:

```text
operator
dtype
shape
layout
device
capability
```

---

# 61. Kernel cache

Compiled kernel cache key:

```text
operator
dtype
shape class
device
compiler version
provider version
```

---

# 62. Kernel specialization

Static shapes có thể generate specialized kernels.

---

# 63. Fusion

Ví dụ:

```text
matmul
→
bias
→
gelu
```

có thể fuse.

---

# 64. Fusion correctness

Fusion không được thay đổi floating-point semantics ngoài mode được khai báo.

---

# 65. Precision modes

```text
Strict
FastMath
MixedPrecision
```

---

# 66. FastMath

FastMath phải explicit.

---

# 67. Mixed precision

Training có thể sử dụng:

```text
f16
bf16
```

với master parameters ở f32 khi cần.

---

# 68. Loss scaling

Optional dynamic/static loss scaling.

---

# 69. Automatic differentiation

Axiom hỗ trợ reverse-mode autodiff.

---

# 70. Gradient tape

```text
GradientTape
```

ghi lại differentiable operations.

---

# 71. Gradient

```text
Gradient<T>
```

có shape/dtype tương ứng.

---

# 72. Gradient rules

Mỗi differentiable operator có derivative rule.

---

# 73. Non-differentiable operators

Compiler/runtime đánh dấu explicit.

---

# 74. Higher-order differentiation

Optional:

```text
grad(grad(f))
```

---

# 75. Forward-mode autodiff

Optional provider.

---

# 76. Gradient checkpointing

Cho phép trade:

```text
memory ↔ compute
```

---

# 77. Graph representation

```text
ComputeGraph {
    nodes
    inputs
    outputs
}
```

---

# 78. Graph node

```text
GraphNode {
    op
    inputs
    attributes
    outputs
}
```

---

# 79. Graph validation

Checks:

- topological ordering;
- shape;
- dtype;
- device;
- operator attributes;
- cycle.

---

# 80. Graph cycles

Training control flow không được encode bằng cycle tùy tiện trong static graph.

---

# 81. Control flow

Graph có thể hỗ trợ:

```text
If
While
For
```

với bounded/dynamic execution.

---

# 82. Graph optimization

Rules:

```text
constant_fold
dead_node_elimination
common_subexpression
operator_fusion
layout_propagation
dtype_propagation
device_propagation
```

---

# 83. Graph compiler

Pipeline:

```text
Graph
→
Canonical IR
→
Shape inference
→
Optimization
→
Device partition
→
Kernel selection
→
Executable graph
```

---

# 84. Model module

```text
Module {
    parameters
    buffers
    submodules
    forward
}
```

---

# 85. Struct-only design

Module không phải class.

Method:

```text
fn forward(self: Model, input: Tensor) -> Tensor
```

---

# 86. Parameter

Parameter là tensor có gradient.

---

# 87. Buffer

Non-gradient model state.

Ví dụ:

```text
running_mean
running_variance
```

---

# 88. Parameter registry

Generated metadata thay vì reflection.

---

# 89. Model composition

```text
Sequential
Residual
Parallel
```

có thể là struct combinators.

---

# 90. Override mechanism

Axiom trait/dispatch mechanism từ core cho phép provider thay implementation.

---

# 91. Training mode

Module có explicit:

```text
Training
Inference
```

---

# 92. Dropout

Training-only randomness.

---

# 93. Randomness

Random state phải explicit.

---

# 94. RNG

```text
Rng
RngKey
RandomStream
```

---

# 95. Deterministic RNG

Same seed + same algorithm + same execution mode produces reproducible sequence.

---

# 96. Non-deterministic mode

Allowed for performance.

---

# 97. Dataset

```text
Dataset<T>
```

là typed source of samples.

---

# 98. Dataset source

```text
File
Table
Stream
ObjectStore
Generated
Remote
```

---

# 99. Dataset transformation

```text
map
filter
shuffle
batch
repeat
take
cache
prefetch
```

---

# 100. Lazy dataset

Pipeline evaluated during iteration.

---

# 101. Data loader

```text
DataLoader<T>
```

có:

```text
workers
prefetch
batch_size
shuffle
drop_last
```

---

# 102. Backpressure

DataLoader tích hợp 607.

---

# 103. Dataset sharding

Dataset có thể shard:

```text
by_index
by_hash
by_range
by_partition
```

---

# 104. Distributed sampler

Mỗi worker nhận non-overlapping samples khi required.

---

# 105. Epoch

Epoch semantics explicit.

---

# 106. Data ordering

Có thể:

```text
Deterministic
BestEffort
Randomized
```

---

# 107. Dataset checkpoint

Lưu:

```text
dataset revision
shard
offset
shuffle seed
epoch
```

---

# 108. Data augmentation

Augmentation là pure transform nếu có thể.

---

# 109. Image augmentation

Provider module có thể cung cấp:

```text
resize
crop
flip
rotate
normalize
color_transform
```

---

# 110. Audio augmentation

Có thể tích hợp 616.

---

# 111. Text preprocessing

617 là authoritative text/Unicode layer.

---

# 112. Tokenization

Tokenizer là provider/module.

---

# 113. No mandatory NLP tokenizer

Core tensor runtime không phụ thuộc tokenizer.

---

# 114. Feature

```text
Feature<T>
```

có:

```text
name
dtype
shape
version
source
```

---

# 115. FeatureSet

Collection typed features.

---

# 116. FeatureStore

```text
FeatureStore {
    definitions
    offline_source
    online_source
}
```

---

# 117. Offline features

642 có thể tính feature batches.

---

# 118. Online features

628/611 can provide low-latency lookup.

---

# 119. Feature freshness

Feature metadata:

```text
computed_at
source_revision
expires_at
```

---

# 120. Feature lineage

640 records source and transformation.

---

# 121. Feature governance

Classification/residency/retention apply.

---

# 122. Training dataset

Training data references:

```text
dataset_revision
feature_revision
governance_revision
```

---

# 123. Training job

```text
TrainingJob {
    model
    dataset
    optimizer
    schedule
    resources
    checkpoint_policy
}
```

---

# 124. Training state

```text
epoch
step
parameters
optimizer_state
scheduler_state
rng_state
dataset_position
```

---

# 125. Optimizer

Core algorithms:

```text
SGD
Momentum
Adam
AdamW
RMSProp
```

---

# 126. Optimizer state

State stored separately from parameters.

---

# 127. Learning rate schedule

```text
Constant
Step
Cosine
Linear
Exponential
Warmup
```

---

# 128. Custom schedule

Pure function over step/epoch.

---

# 129. Loss

```text
LossFunction
```

---

# 130. Standard losses

```text
MSE
MAE
Huber
CrossEntropy
BinaryCrossEntropy
KLDiv
NLL
Contrastive
Triplet
```

---

# 131. Metrics

```text
Accuracy
Precision
Recall
F1
MAE
MSE
RMSE
AUC
```

---

# 132. Metric semantics

Metrics do not alter model state.

---

# 133. Training loop

Canonical:

```text
load batch
→
forward
→
loss
→
backward
→
optimizer
→
metrics
→
checkpoint
```

---

# 134. Training API

```text
trainer.fit(model, dataset)
```

---

# 135. Training callbacks

Callbacks are explicit hooks.

---

# 136. Callback security

Callbacks cannot automatically obtain capabilities.

---

# 137. Evaluation

Evaluation runs without gradient by default.

---

# 138. Validation split

Explicit dataset partition.

---

# 139. Early stopping

Optional declarative training policy.

---

# 140. Gradient clipping

```text
clip_norm
clip_value
```

---

# 141. Gradient accumulation

Supports large effective batch sizes.

---

# 142. Distributed data parallel

Workers maintain model replicas and synchronize gradients.

---

# 143. Data parallelism

```text
batch
→
workers
→
local gradients
→
all_reduce
```

---

# 144. All-reduce

Provider abstraction.

---

# 145. Collective operations

```text
Broadcast
AllReduce
AllGather
ReduceScatter
Reduce
Barrier
```

---

# 146. Collective backend

May use:

```text
shared memory
IPC
network
GPU collective provider
```

---

# 147. Collective security

Capability required for cross-process/network collective.

---

# 148. Parameter server

Optional architecture.

---

# 149. Model parallelism

Tensor/model layers may be distributed across devices.

---

# 150. Pipeline parallelism

Stages can execute on different workers/devices.

---

# 151. Hybrid parallelism

Data + tensor + pipeline parallelism.

---

# 152. Distributed training topology

635 supplies placement.

---

# 153. Distributed training job

630 launches workers.

---

# 154. Worker identity

Uses 630 worker identity/generation.

---

# 155. Training rendezvous

Uses 635 coordination.

---

# 156. Failure handling

Worker failure:

```text
retry
replace
restore checkpoint
```

---

# 157. Elastic training

Optional worker count changes.

---

# 158. Elastic semantics

Optimizer/state consistency must be preserved.

---

# 159. Checkpoint

Checkpoint includes:

```text
model
optimizer
scheduler
rng
dataset
training metadata
```

---

# 160. Checkpoint format

Native:

```text
AXCKPT
```

---

# 161. Checkpoint metadata

```text
model_id
model_version
schema
source_revision
training_step
build_id
```

---

# 162. Atomic checkpoint

Write generation then activate.

---

# 163. Incremental checkpoint

Optional delta checkpoint.

---

# 164. Checkpoint encryption

610/638.

---

# 165. Checkpoint governance

640.

---

# 166. Checkpoint retention

640 retention policies.

---

# 167. Model artifact

```text
ModelArtifact {
    graph
    weights
    signature
    metadata
}
```

---

# 168. Model version

Immutable.

---

# 169. Model signature

Defines:

```text
inputs
outputs
dtypes
shapes
optional fields
```

---

# 170. Model compatibility

Inference rejects incompatible input.

---

# 171. Model format

Native:

```text
AXMODEL
```

---

# 172. AXMODEL

```text
Header
ModelSchema
Graph
Weights
Constants
Metadata
Checksums
```

---

# 173. Weight storage

Can be chunked.

---

# 174. Weight compression

613.

---

# 175. Weight encryption

610/638.

---

# 176. Weight quantization

Supported metadata:

```text
scale
zero_point
axis
scheme
```

---

# 177. Quantization

Modes:

```text
FP16
BF16
INT8
INT4
```

where provider supports.

---

# 178. Calibration

Calibration dataset explicitly specified.

---

# 179. Quantization correctness

Quantized model records quantization scheme.

---

# 180. Model conversion

External formats can be imported through provider boundary.

---

# 181. ONNX boundary

Optional provider.

---

# 182. TensorFlow boundary

Optional provider.

---

# 183. PyTorch boundary

Optional provider.

---

# 184. SafeTensors boundary

Optional weight import/export provider.

---

# 185. External model runtime

Optional provider:

```text
ONNX Runtime
TensorRT
CoreML
DirectML
```

No mandatory dependency.

---

# 186. Model compiler

```text
AXMODEL
→
shape inference
→
constant folding
→
operator fusion
→
quantization
→
device partition
→
kernel selection
→
ExecutableModel
```

---

# 187. Executable model

```text
ExecutableModel {
    graph
    kernels
    memory_plan
    device_plan
}
```

---

# 188. Memory planning

Compiler computes tensor lifetimes.

---

# 189. Buffer reuse

Non-overlapping tensors can reuse memory.

---

# 190. Static memory plan

Static-shape model can have near-static activation allocation.

---

# 191. Dynamic memory

Dynamic shape uses bounded allocator.

---

# 192. Inference arena

Inference request can use per-request arena.

---

# 193. Batch inference

Requests can be batched.

---

# 194. Dynamic batching

Optional scheduler groups compatible requests.

---

# 195. Batch compatibility

Must match:

```text
model
version
shape
dtype
device
```

---

# 196. Inference queue

607 manages scheduling.

---

# 197. Inference deadline

Request deadline propagates to kernels.

---

# 198. Cancellation

Cancelled inference releases request resources.

---

# 199. Streaming inference

Model can expose:

```text
stream(input_chunk)
```

for supported architectures.

---

# 200. Stateful inference

State is explicit.

---

# 201. KV cache

Transformer-style inference can use:

```text
KVCache
```

---

# 202. KV cache ownership

Per-session or shared according to explicit policy.

---

# 203. KV cache limits

606 enforces memory limits.

---

# 204. Paged KV cache

Optional provider.

---

# 205. Prefix cache

Optional.

---

# 206. Cache correctness

Cache key includes:

```text
model_version
tokenizer_version
input_prefix
generation_policy
```

---

# 207. Model serving

```text
ModelServer
ModelEndpoint
InferenceSession
```

---

# 208. Model endpoint

631 exposes network/service contract.

---

# 209. Authentication

627/638.

---

# 210. Authorization

603/639.

---

# 211. Data governance

640 applies to inference inputs/outputs.

---

# 212. Streaming model endpoint

634/626 can transport streaming inference.

---

# 213. Batch endpoint

Analytics workloads can use 642.

---

# 214. Model registry

```text
ModelRegistry {
    ModelId
    versions
    artifacts
    signatures
    metadata
}
```

---

# 215. Registry storage

625 may distribute model packages.

---

# 216. Model package

613/625 package:

```text
weights
graph
tokenizer
runtime metadata
```

---

# 217. Model deployment

636 orchestrates rollout.

---

# 218. Model canary

636 + 632 traffic routing.

---

# 219. Model rollback

Rollback to immutable previous model generation.

---

# 220. Model health

633 metrics:

```text
latency
error_rate
throughput
memory
GPU_utilization
```

---

# 221. Model quality metrics

643 can expose application-defined metrics.

No automatic quality winner selection is required.

---

# 222. Drift detection

Optional descriptive statistics.

---

# 223. Data drift

Compare current distribution against reference distribution.

---

# 224. Model drift

Compare monitored model metrics over time.

---

# 225. No autonomous retraining

Automatic retraining is a higher-level policy/workflow.

---

# 226. Experiment tracking

```text
Experiment
Run
ParameterSet
MetricRecord
Artifact
```

---

# 227. Experiment metadata

Stores:

```text
code_fingerprint
model_version
dataset_revision
feature_revision
seed
hardware
provider
```

---

# 228. Reproducibility

A run can declare:

```text
Strict
BestEffort
NonDeterministic
```

---

# 229. Strict reproducibility

Requires:

- fixed seed;
- deterministic kernels;
- fixed dataset ordering;
- fixed model version;
- fixed provider;
- compatible hardware.

---

# 230. Hardware differences

May prevent bit-identical floating point.

Metadata records hardware/provider.

---

# 231. Experiment storage

612/628.

---

# 232. Experiment lineage

640.

---

# 233. AI data lineage

Training run links:

```text
dataset
features
model
code
configuration
```

---

# 234. Training data privacy

Training dataset classification applies to derived model where policy requires propagation.

---

# 235. Model classification

Model artifact can have independent classification plus inherited constraints.

---

# 236. Model residency

Model can be restricted to specific regions.

---

# 237. Cross-region model distribution

Requires explicit 639/640 authorization.

---

# 238. Secret isolation

API keys/credentials never embedded into model artifact.

---

# 239. Secure model loading

Model package signature verified before activation.

---

# 240. Model integrity

Weights and graph checksums verified.

---

# 241. Trusted model provider

638 can bind signing identity.

---

# 242. Untrusted model

Can execute only inside permitted sandbox/capability scope.

---

# 243. Model operator security

Custom operators require signed/trusted plugin.

---

# 244. Arbitrary native code

Model file must never implicitly execute arbitrary native code.

---

# 245. Custom operator format

Explicit provider module.

---

# 246. Model graph safety

No hidden filesystem/network/process operations.

---

# 247. Resource limits

Model declares estimates:

```text
memory
compute
workspace
device
```

---

# 248. Admission

639 evaluates model execution request.

---

# 249. Scheduling

606/607/630 allocate resources.

---

# 250. GPU memory

614/606 manage VRAM budgets.

---

# 251. Multi-model serving

Server can host multiple models.

---

# 252. Model isolation

Each model has:

```text
ModelGeneration
ResourceGroup
CapabilitySet
```

---

# 253. Model unload

Unused model generations can be unloaded.

---

# 254. Warm model

Model can remain resident under resource budget.

---

# 255. Model cache

Cache key:

```text
model_hash
target
device
provider
precision
```

---

# 256. Model loading

Can be asynchronous.

---

# 257. Model loading cancellation

Supported before activation.

---

# 258. Atomic activation

Model generation becomes serving only after validation.

---

# 259. Device loss

Inference/training detects device loss.

---

# 260. Recovery

Recreate device resources and reload model/checkpoint.

---

# 261. GPU context

614 owns device context.

---

# 262. AI runtime owns

- model execution;
- tensor graphs;
- kernel dispatch;
- training state.

It does not own physical GPU lifecycle.

---

# 263. Distributed checkpoint

Large checkpoints can be sharded.

---

# 264. Checkpoint shard

```text
ModelShard
OptimizerShard
```

---

# 265. Parallel checkpoint

Workers write shards concurrently.

---

# 266. Checkpoint manifest

Lists:

```text
shard
hash
size
worker
revision
```

---

# 267. Checkpoint recovery

Missing shard causes recovery failure unless redundancy/provider exists.

---

# 268. Checkpoint redundancy

Optional replication through 628.

---

# 269. Object storage

613/611 provider.

---

# 270. Dataset caching

Dataset cache can use CAS from 613.

---

# 271. Cache identity

Hash of:

```text
source_revision
transform_graph
parameters
```

---

# 272. Cache invalidation

Source revision change invalidates derived cache.

---

# 273. Data loader cache

Local node cache optional.

---

# 274. Feature cache

628 distributed cache.

---

# 275. Training throughput

Metrics:

```text
samples/sec
tokens/sec
steps/sec
device_utilization
input_pipeline_wait
```

---

# 276. Input bottleneck

Telemetry distinguishes:

```text
compute_bound
input_bound
memory_bound
communication_bound
```

---

# 277. Distributed training metrics

```text
all_reduce_time
communication_bytes
stragglers
worker_utilization
```

---

# 278. Straggler detection

Descriptive telemetry only.

---

# 279. Elastic worker replacement

630/635.

---

# 280. Training failure classification

```text
DataError
ModelError
NumericalError
ResourceError
DeviceError
CommunicationError
CheckpointError
PolicyError
```

---

# 281. Numerical anomaly detection

Optional:

```text
NaN
Inf
overflow
underflow
```

detection.

---

# 282. NaN policy

```text
Ignore
Warn
Fail
```

---

# 283. Gradient anomaly

Optional detection.

---

# 284. Gradient clipping

Prevents exploding gradients where configured.

---

# 285. Loss scaling

Prevents underflow in mixed precision.

---

# 286. Automatic mixed precision

Optional planner feature.

---

# 287. AMP correctness

Unsafe casts require explicit policy.

---

# 288. Checkpoint frequency

By:

```text
steps
epochs
time
metric
```

---

# 289. Checkpoint trigger

Metric-triggered checkpoint must be deterministic based on observed metric.

---

# 290. Training resume

Restores exact training state when checkpoint contains required state.

---

# 291. Partial resume

Explicitly marked if optimizer/RNG/data state missing.

---

# 292. Transfer learning

Load model checkpoint then selectively freeze parameters.

---

# 293. Parameter freezing

```text
requires_grad = false
```

---

# 294. Parameter groups

Optimizer can assign different hyperparameters.

---

# 295. Gradient accumulation

State tracked across microbatches.

---

# 296. Gradient synchronization

Can occur every N steps.

---

# 297. Gradient compression

Optional distributed optimization.

---

# 298. Gradient compression semantics

Approximation explicitly recorded.

---

# 299. Distributed optimizer

Optional sharded optimizer state.

---

# 300. Parameter sharding

Large model weights can be partitioned.

---

# 301. Tensor parallel

Operations split by tensor dimensions.

---

# 302. Pipeline scheduling

Microbatch execution across stages.

---

# 303. Communication overlap

Compute and communication can overlap where device supports.

---

# 304. Collective ordering

All distributed workers must use compatible collective order.

---

# 305. Deadlock prevention

Collective sequence validated where possible.

---

# 306. Collective timeout

Every collective has bounded timeout.

---

# 307. Worker failure

Collective aborts rather than hanging indefinitely.

---

# 308. Distributed rendezvous

635 provides membership/leader/lease coordination.

---

# 309. Training cluster identity

Training run binds to:

```text
ClusterId
TrainingJobId
Generation
```

---

# 310. Training lease

Worker membership is lease-based.

---

# 311. Stale worker

Fencing prevents stale worker from committing checkpoint.

---

# 312. Checkpoint fencing

Commit token bound to training generation.

---

# 313. Model promotion

636 can promote validated model artifact.

---

# 314. Model registry state

```text
Draft
Validated
Staged
Active
Deprecated
Retired
Revoked
```

---

# 315. Revoked model

Cannot be newly activated.

---

# 316. Model security event

638/602 records activation/revocation.

---

# 317. Model package signature

625/638.

---

# 318. Model deployment manifest

```text
.axmodeldeploy
```

contains:

- model ID;
- version;
- package hash;
- target;
- resource requirements;
- capabilities;
- governance metadata;
- rollout policy.

---

# 319. Compiler annotations

```text
@tensor
@device
@kernel
@gradient
@model
@parameter
@buffer
@dataset
@feature
@train
@infer
@checkpoint
@optimizer
@metric
@model_server
@quantized
@distributed
```

---

# 320. Generated metadata

```text
.axtensor
.axgraph
.axmodel
.axdataset
.axfeature
.axtraining
.axcheckpoint
.axinference
```

---

# 321. Compiler shape inference

Static shape information should propagate through graph.

---

# 322. Dtype inference

Operator output dtype determined statically where possible.

---

# 323. Device inference

Compiler can detect incompatible device operations.

---

# 324. Transfer insertion

Compiler may insert explicit transfer nodes.

---

# 325. Transfer visibility

Generated plan must show transfers.

---

# 326. Memory planning

Compiler computes liveness.

---

# 327. Alias analysis

Views and in-place operations require alias safety.

---

# 328. In-place operation

Allowed only when alias analysis proves safe.

---

# 329. Mutation

Tensor mutation is explicit.

---

# 330. Immutable tensor mode

Optional safety profile.

---

# 331. Training mutation

Optimizer updates parameters explicitly.

---

# 332. Model immutability

Inference model generation is immutable while serving.

---

# 333. Concurrent inference

Read-only model parameters can be shared.

---

# 334. Mutable model state

Requires synchronization or session-local state.

---

# 335. Thread safety

Tensor operations are thread-safe where documented; mutable buffers are not implicitly synchronized.

---

# 336. Async inference

Returns `InferenceFuture`.

---

# 337. Batch scheduler

Can combine compatible requests.

---

# 338. Priority

Requests may have explicit priority subject to 606/639.

---

# 339. Tenant quotas

Per-tenant:

```text
requests
tokens
GPU time
memory
```

---

# 340. Rate limits

631/632/606.

---

# 341. Inference admission

639 evaluates request policy.

---

# 342. Prompt/data governance

Inference input can carry classification/purpose metadata.

---

# 343. Output governance

Generated output may inherit or transform classification according to 640.

---

# 344. Model input residency

Inference request may be region restricted.

---

# 345. Model locality

635 places model execution according to residency/device requirements.

---

# 346. Edge inference

636 can deploy model to edge nodes.

---

# 347. Offline inference

Model package can run without network if all dependencies are embedded.

---

# 348. Model dependency closure

Model package declares:

```text
weights
tokenizer
operators
runtime requirements
```

---

# 349. Reproducible model package

613/625 provide deterministic package generation.

---

# 350. Model artifact hashing

Content hash identifies exact model.

---

# 351. Model graph hash

Separate graph fingerprint from weight fingerprint.

---

# 352. Weight hash

Each shard can have independent hash.

---

# 353. Model signature hash

Input/output contract fingerprint.

---

# 354. Full model fingerprint

Combination of:

```text
graph
weights
signature
provider requirements
```

---

# 355. Inference cache

Optional cache keyed by model/input policy fingerprint.

---

# 356. Cache privacy

Sensitive inputs must not be cached unless explicitly permitted.

---

# 357. Cache governance

640 controls retention/residency.

---

# 358. Embedding generation

643 can expose embedding model execution.

---

# 359. Search integration

641 can consume embeddings for vector search.

---

# 360. Hybrid retrieval

642/643 can create analytical features for 641 hybrid ranking.

---

# 361. RAG boundary

Axiom can compose:

```text
641 retrieval
→
643 embedding/model
→
application logic
```

without making RAG a core primitive.

---

# 362. Tokenizer boundary

Tokenizer is model/application-specific.

---

# 363. LLM model support

Transformer architecture is expressible through:

- embedding;
- attention;
- normalization;
- feed-forward;
- KV cache;
- tensor parallelism.

---

# 364. No mandatory LLM runtime

Transformer support comes from tensor/model primitives.

---

# 365. Sequence batching

Variable-length sequences supported using:

```text
padding
mask
packed representation
```

---

# 366. Ragged tensor

Optional:

```text
RaggedTensor
```

---

# 367. Packed sequences

Avoid unnecessary padding.

---

# 368. Attention mask

Explicit tensor.

---

# 369. Causal attention

Explicit mode.

---

# 370. KV cache memory

Governed by 606.

---

# 371. Quantized inference

INT8/INT4 provider kernels.

---

# 372. Quantization calibration

Calibration data lineage recorded through 640.

---

# 373. Weight-only quantization

Supported.

---

# 374. Activation quantization

Supported where provider supports.

---

# 375. Mixed quantization

Per-layer/per-tensor policies.

---

# 376. Model compilation cache

Compiled executable keyed by model fingerprint + target.

---

# 377. Compilation reuse

Unchanged model/source reuses compiled artifact.

---

# 378. Compiler integration

643 integrates with Axiom compiler cache.

---

# 379. Native executable embedding

Small inference models may be embedded into native binaries.

---

# 380. Model resource packaging

613.

---

# 381. Single-file application

Model artifact can be embedded into AXPK/native application bundle.

---

# 382. Lazy model loading

Model weights can load on demand.

---

# 383. Memory-mapped weights

Possible when storage/provider permits.

---

# 384. Weight streaming

Large model weights can be streamed.

---

# 385. Page cache

611 handles file cache; 643 may add model-specific cache hints.

---

# 386. Model unloading

Explicit.

---

# 387. Training memory allocator

Separate pools:

```text
parameter
gradient
optimizer
activation
temporary
communication
```

---

# 388. Memory diagnostics

Report each pool separately.

---

# 389. GPU memory diagnostics

Report:

```text
allocated
reserved
free
fragmentation
peak
```

---

# 390. Fragmentation mitigation

Pool allocator + lifetime-aware reuse.

---

# 391. Activation checkpointing

Recompute selected graph segments.

---

# 392. Graph partitioning

Partition graph by device.

---

# 393. CPU/GPU hybrid execution

Allowed.

---

# 394. Accelerator fallback

Unsupported operator can run CPU if transfer policy permits.

---

# 395. Fallback cost

Planner accounts for transfer.

---

# 396. Unsupported operation

If fallback disabled, fail at plan validation rather than halfway through execution.

---

# 397. Graph validation

Executable graph must be fully validated before serving.

---

# 398. Runtime safety

No malformed model may cause arbitrary memory access outside runtime abstractions.

---

# 399. Model fuzzing

AXMODEL parser must be fuzz-tested.

---

# 400. Tensor fuzzing

Shape/dtype/operator combinations fuzz-tested.

---

# 401. Numerical tests

Compare kernels against reference implementation.

---

# 402. Differential testing

CPU and GPU implementations compared within declared tolerance.

---

# 403. Deterministic tests

Fixed seeds and deterministic kernels.

---

# 404. Distributed tests

Simulate:

- worker loss;
- network partition;
- stale worker;
- checkpoint corruption;
- device loss;
- coordinator failure.

---

# 405. Training recovery tests

Resume from checkpoint and verify state.

---

# 406. Inference failover

Serving model can migrate/restart.

---

# 407. Model rollout tests

Verify:

```text
stage
activate
observe
rollback
```

---

# 408. Governance tests

Verify:

- restricted data;
- residency;
- retention;
- lineage;
- model classification.

---

# 409. Security tests

Verify:

- unauthorized model load;
- unauthorized GPU;
- unauthorized dataset;
- cross-tenant access;
- capability attenuation.

---

# 410. Performance benchmarks

Benchmark:

```text
tensor ops
matmul
convolution
attention
training throughput
inference latency
memory usage
data loading
distributed communication
```

---

# 411. Binary size

Minimal tensor-only profile must not pull:

- distributed runtime;
- model registry;
- SQL;
- package registry;
- GUI;
- unnecessary GPU providers.

---

# 412. Dead stripping

Unused operators/providers are removable.

---

# 413. Static linking

Native AI application can statically link selected providers.

---

# 414. Dynamic provider

Large GPU backends may be dynamic modules.

---

# 415. ABI

Stable C-compatible provider ABI.

---

# 416. Provider capability query

Runtime can ask:

```text
supports(op)
supports(dtype)
supports(device)
```

---

# 417. Provider versioning

Provider ABI/version fingerprint.

---

# 418. Provider trust

External provider must satisfy 603/623 trust policy.

---

# 419. No implicit code download

Model execution cannot download arbitrary kernels/code.

---

# 420. Remote model provider

Network model execution is an explicit service boundary.

---

# 421. Remote inference

631/626 handles transport.

---

# 422. Remote inference security

610/627/638.

---

# 423. Remote model lineage

640 records provider/model identity.

---

# 424. Model observability

633 metrics/traces.

---

# 425. Model audit

602 security/audit events.

---

# 426. Training audit

Training run records:

```text
dataset
code
model
config
hardware
provider
checkpoint
```

---

# 427. Configuration

601/637 configure:

- default device;
- precision;
- worker count;
- batch sizes;
- cache;
- checkpoint policy.

---

# 428. Dynamic configuration safety

637 cannot change immutable model graph semantics without explicit new generation.

---

# 429. Policy

639 may require:

```text
approved model
approved dataset
approved region
approved device
```

---

# 430. Credentials

638 manages:

- dataset credentials;
- model repository credentials;
- external provider keys.

---

# 431. Data governance

640 controls:

- training data;
- model artifacts;
- feature data;
- inference inputs/outputs.

---

# 432. Event integration

634 emits:

```text
TrainingStarted
TrainingProgress
CheckpointCreated
ModelValidated
ModelActivated
InferenceStarted
InferenceCompleted
ModelRevoked
```

---

# 433. Workflow integration

629 can orchestrate:

```text
dataset preparation
→
training
→
evaluation
→
validation
→
deployment
```

---

# 434. Deployment integration

636 deploys validated model.

---

# 435. Cluster integration

635 determines placement.

---

# 436. Compute integration

630 executes workers.

---

# 437. Analytics integration

642 prepares datasets/features/evaluation.

---

# 438. Search integration

641 handles embeddings/vector retrieval.

---

# 439. Package integration

613/625 distribute model artifacts.

---

# 440. Final AI architecture

```text
                       Axiom AI
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
      Dataset           Tensor            Model
        │                 │                 │
        ▼                 ▼                 ▼
   DataLoader         ComputeGraph      AXMODEL
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                    AI Execution IR
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
            CPU          GPU       Accelerator
             │            │            │
             └────────────┼────────────┘
                          ▼
                  Training / Inference
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
           Local       Distributed    Serving
             │            │            │
             └────────────┼────────────┘
                          ▼
       630 Compute / 635 Cluster / 636 Deploy
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
      642                641                640
   Analytics           Search           Governance
```

---

# 441. Architecture invariants

1. Tensor dtype is explicit.
2. Tensor shape is explicit.
3. Device is explicit.
4. Device transfer is observable.
5. CPU fallback exists for mandatory primitives.
6. No mandatory CUDA.
7. No mandatory Python.
8. No mandatory third-party ML runtime.
9. No mandatory GC.
10. Tensor lifetime is deterministic.
11. Views do not silently copy.
12. Copies are explicit or compiler-visible.
13. In-place mutation requires alias safety.
14. Autodiff follows registered derivative rules.
15. Randomness is explicit.
16. Training state is checkpointable.
17. Checkpoints are versioned.
18. Model artifacts are immutable.
19. Model signatures are explicit.
20. Model execution cannot execute arbitrary code.
21. Custom operators require explicit provider/module.
22. Provider capabilities are declared.
23. Unsupported operators fail explicitly.
24. GPU fallback is explicit.
25. Memory budgets are enforced.
26. KV-cache memory is governed.
27. Distributed workers are generation-safe.
28. Stale workers cannot commit.
29. Collective operations have bounded waits.
30. Training retries cannot corrupt checkpoints.
31. Model activation is atomic.
32. Model rollback uses immutable generation.
33. Dataset revisions are recorded.
34. Feature lineage is recorded.
35. Training lineage is recorded.
36. Governance metadata follows data.
37. Residency restrictions apply to training and inference.
38. Classification restrictions apply to derived artifacts where required.
39. Secrets never enter model artifacts.
40. Credentials never enter graph plans.
41. Model packages are integrity checked.
42. Model deployment requires policy admission.
43. Resource scheduling remains owned by 606/630/635.
44. GPU lifecycle remains owned by 614.
45. Storage remains owned by 611.
46. Distributed state remains owned by 628.
47. Analytics remains owned by 642.
48. Search remains owned by 641.
49. Model serving remains compatible with 631.
50. No AI subsystem may silently bypass Axiom security/governance.

---

# 442. Acceptance criteria

Target: **≥500 acceptance criteria**, covering:

- tensor correctness;
- shape inference;
- dtype inference;
- broadcasting;
- layouts;
- views;
- slicing;
- indexing;
- device transfers;
- CPU kernels;
- SIMD;
- GPU;
- accelerator;
- autodiff;
- graph compilation;
- operator fusion;
- memory planning;
- quantization;
- mixed precision;
- model serialization;
- model loading;
- model validation;
- dataset pipelines;
- DataLoader;
- distributed sampling;
- feature store;
- training;
- optimizer;
- metrics;
- checkpoint;
- resume;
- distributed training;
- collectives;
- worker failure;
- elastic training;
- inference;
- batching;
- streaming inference;
- KV cache;
- model serving;
- model registry;
- model deployment;
- rollback;
- governance;
- lineage;
- residency;
- security;
- observability;
- resource governance;
- external providers;
- ABI;
- fuzzing;
- deterministic execution;
- numerical correctness;
- performance;
- binary-size minimization.

---

# 443. Profiles

```text
AXAI_NONE
AXAI_TENSOR
AXAI_AUTODIFF
AXAI_NN
AXAI_DATASET
AXAI_TRAINING
AXAI_INFERENCE
AXAI_QUANT
AXAI_GPU
AXAI_DISTRIBUTED
AXAI_SERVING
AXAI_FULL
```

### `AXAI_TENSOR`

Chỉ:

- Tensor;
- CPU kernels;
- SIMD;
- basic operators.

### `AXAI_AUTODIFF`

Thêm gradient/autodiff.

### `AXAI_GPU`

Thêm GPU provider.

### `AXAI_TRAINING`

Thêm training/optimizer/checkpoint.

### `AXAI_INFERENCE`

Thêm model compilation/inference.

### `AXAI_DISTRIBUTED`

Thêm distributed training.

### `AXAI_SERVING`

Thêm model serving/registry/deployment integration.

### `AXAI_FULL`

Toàn bộ AI runtime.

---

# 444. Quan hệ với Axiom compiler

643 tạo một cầu nối quan trọng giữa **ngôn ngữ hệ thống** và **AI compute**:

```text
Axiom source
      │
      ▼
Tensor / Model DSL
      │
      ▼
Axiom IR
      │
      ├── CPU native code
      ├── SIMD kernels
      ├── GPU kernels/provider
      └── Accelerator provider
```

Điều này cho phép Axiom không cần xây một "Python riêng cho AI".

Thay vào đó, AI trở thành một phần của hệ thống type + compiler + native runtime.

---

# 445. Ý nghĩa kiến trúc

Sau 643, Axiom có ba lớp dữ liệu/tính toán lớn:

```text
641 Search
    ↓
retrieval / full-text / vector / hybrid

642 Analytics
    ↓
OLAP / DataFrame / aggregation / joins

643 AI
    ↓
tensor / training / inference / model execution
```

Ba hệ thống dùng chung:

```text
611 Storage
612 Schema
613 Packaging
614 GPU/Device
606 Resources
607 Scheduling
628 Distributed Data
630 Distributed Compute
634 Events
639 Policy
640 Governance
```

Do đó Axiom có thể xây:

```text
database
search engine
analytics engine
ML pipeline
AI inference service
distributed AI system
```

mà không cần biến từng hệ thống thành một runtime độc lập.

---

# 446. Trạng thái

**BOOTSTRAP-643 — COMPLETE**

Task tiếp theo:

**BOOTSTRAP-644 — Native AI Agent, Tool Calling, Structured Generation, Context Runtime, Memory, Retrieval-Augmented Execution, Planning & Autonomous Task Runtime 5.0**
:::