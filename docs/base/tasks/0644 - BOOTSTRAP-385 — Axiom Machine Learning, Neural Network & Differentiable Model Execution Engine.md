# BOOTSTRAP-385 — Axiom Machine Learning, Neural Network & Differentiable Model Execution Engine

Sau **384 — Computer Vision, Image Processing & Geometric Perception**, bước tiếp theo là xây tầng **Machine Learning / Neural Network**.

Điểm quan trọng: **Axiom không biến ML thành một hệ thống runtime riêng**. ML phải được xây trên những gì Axiom đã có:

```text
Tensor
Linear Algebra
AD
Probability
Optimization
GPU
SIMD
Parallelism
Comptime
Expression Graph
```

Mục tiêu là để một model ML có thể đi từ:

```text
high-level model definition
        ↓
typed tensor graph
        ↓
shape/type inference
        ↓
AD
        ↓
graph optimization
        ↓
kernel fusion
        ↓
SIMD / CPU / GPU
        ↓
native machine code
```

mà không cần một `TensorFlow Runtime`, `PyTorch Runtime` hay object-heavy framework bắt buộc.

---

## 1. Neural Network là generic computation

Không tạo Core type:

```text
NeuralNetwork
Layer
Module
```

theo kiểu class hierarchy.

Thay vào đó:

```text
struct Linear
struct Conv2D
struct Attention
```

và ordinary functions:

```text
fn forward(layer: Linear, x: Tensor<...>) -> Tensor<...>
```

Compiler chỉ nhìn thấy typed computation.

---

## 2. Model là giá trị

Model có thể là:

```text
struct MLP {
    layers: ...
}
```

hoặc một composition generic.

Không cần:

```text
virtual forward()
object header
runtime dispatch
```

trừ khi programmer **explicitly** yêu cầu dynamic dispatch.

---

## 3. Parameters

Phân biệt:

```text
Parameter
Buffer
Input
Output
Temporary
```

Parameter là state được tối ưu trong training.

Ví dụ:

```text
struct Linear {
    weight: Parameter<Tensor<...>>,
    bias: Parameter<Tensor<...>>,
}
```

`Parameter` là library semantic abstraction.

---

## 4. Parameter không phải Tensor đặc biệt về machine representation

Về runtime, parameter thường vẫn chỉ là:

```text
Tensor<f32>
```

hoặc:

```text
Tensor<bf16>
Tensor<f16>
```

Metadata training có thể bị compiler erase khỏi inference binary.

---

## 5. Model State

Một model có thể có:

```text
Parameters
Buffers
Constants
Temporary State
Optimizer State
```

Phải phân biệt rõ.

Ví dụ BatchNorm:

```text
running_mean
running_variance
```

không phải trainable parameter.

---

## 6. Training vs Inference

Đây là semantic distinction quan trọng.

```text
training(model, batch)
```

có:

```text
gradient
parameter mutation
optimizer state
```

Trong khi inference:

```text
infer(model, input)
```

thường:

```text
read-only parameters
no gradient
```

Compiler có thể loại bỏ toàn bộ AD machinery trong inference build.

---

## 7. `requires_grad`

Không nên tạo dynamic runtime flag giống một số framework.

Thay vào đó, compiler biết graph nào cần differentiation.

Ví dụ:

```text
loss = model(x).loss(target)
grad = differentiate(loss, model.parameters)
```

Gradient graph được tạo tại compile time.

---

## 8. Gradient Type

Conceptual:

```text
Gradient<T>
```

nhưng có thể compile away thành:

```text
Tensor<f32>
```

khi representation tương thích.

---

## 9. Gradient Accumulation

Compiler/library phải xác định:

```text
overwrite
accumulate
reduce
atomic_accumulate
```

Không được implicit tạo race.

---

## 10. Layer

Layer chỉ là một abstraction thông thường.

Ví dụ:

```text
fn forward(layer: Linear, x: Tensor) -> Tensor
```

không cần interface:

```text
Layer::forward()
```

Dynamic layer collections nếu cần có thể dùng explicit:

```text
dyn Layer
```

nhưng static composition là default.

---

## 11. Static Model Composition

Ví dụ:

```text
model =
    Linear<784, 256>
    → ReLU
    → Linear<256, 10>
```

Compiler có thể biết toàn bộ graph.

Có thể:

- inline;
- fuse;
- specialize;
- constant-fold;
- eliminate intermediate tensors.

---

## 12. Dynamic Model Composition

Vẫn phải hỗ trợ model loaded runtime.

Ví dụ:

```text
Vec<dyn Layer>
```

khi thực sự cần plugin/model loading.

Dynamic dispatch là explicit cost.

---

## 13. Shape Inference

Model:

```text
Linear<784,256>
```

nhận:

```text
Tensor<f32,[B,784]>
```

trả:

```text
Tensor<f32,[B,256]>
```

Compiler phải propagate shape.

---

## 14. Shape Error

Nếu:

```text
Linear<784,256>
```

nhận:

```text
Tensor<f32,[B,512]>
```

thì đây là compile-time error nếu shape static.

---

## 15. Symbolic Batch Dimension

Cho phép:

```text
Tensor<f32,[B,784]>
```

với:

```text
B
```

symbolic.

Compiler vẫn kiểm tra:

```text
784
```

mà không cần biết `B`.

---

## 16. Dynamic Shape

Runtime shape vẫn hỗ trợ:

```text
Tensor<f32, DynamicShape>
```

nhưng compiler chèn runtime checks khi cần.

---

## 17. Broadcasting

ML thường dùng broadcasting:

```text
x + bias
```

Shape solver phải kiểm tra broadcasting legality.

Không materialize broadcast tensor.

---

## 18. Activation Functions

Library primitives:

```text
ReLU
GELU
SiLU
Sigmoid
Tanh
Softmax
LogSoftmax
```

nhưng semantic implementation là ordinary numeric functions.

---

## 19. Activation Fusion

Ví dụ:

```text
matmul
→ bias
→ GELU
```

có thể fuse thành một kernel.

Không cần materialize:

```text
Y = matmul(...)
Z = Y + bias
W = gelu(Z)
```

nếu intermediate không observable.

---

## 20. Dense Layer

Linear layer:

```text
Y = XWᵀ + b
```

phải lower xuống Linear Algebra:

```text
GEMM
+
broadcast
+
elementwise
```

Không viết implementation GEMM riêng cho ML.

---

## 21. Convolution

Conv2D phải reuse tensor/image semantics.

Có thể lower xuống:

```text
direct convolution
im2col + GEMM
Winograd
FFT
implicit GEMM
GPU kernel
```

Cost model quyết định.

---

## 22. No Mandatory im2col

Compiler không được mặc định tạo huge temporary:

```text
im2col(X)
```

nếu direct convolution hoặc implicit GEMM tốt hơn.

---

## 23. Pooling

Hỗ trợ:

```text
MaxPool
AvgPool
AdaptivePool
GlobalPool
```

với shape inference.

---

## 24. Normalization

```text
BatchNorm
LayerNorm
RMSNorm
GroupNorm
InstanceNorm
```

có thể reuse reduction + tensor primitives.

---

## 25. Attention

Attention nên là semantic operation có khả năng được compiler recognize:

```text
Q K V
```

và:

```text
softmax(QKᵀ / sqrt(d))V
```

---

## 26. Attention Fusion

Compiler có thể lower thành:

```text
fused attention kernel
```

thay vì:

```text
QK
materialize
scale
materialize
softmax
materialize
V multiply
```

---

## 27. Memory-efficient Attention

Nếu intermediate không cần observable, compiler có thể chọn tiled/streaming attention.

Mục tiêu:

```text
O(N²)
```

về computation vẫn giữ semantics nhưng giảm memory materialization.

---

## 28. Transformer Blocks

Transformer không cần Core primitive.

Có thể composition:

```text
Embedding
→ Attention
→ Residual
→ Norm
→ MLP
→ Residual
```

Compiler nhận biết các patterns phổ biến.

---

## 29. Embedding

Embedding:

```text
Embedding<Vocab,Dim>
```

về machine level thường là gather.

Có thể lower xuống:

```text
TENSOR_GATHER
```

---

## 30. Sparse Embedding

Large vocabulary có thể dùng sparse access.

Compiler không nên biến embedding lookup thành dense matrix multiplication nếu semantics/cost không phù hợp.

---

## 31. Loss Functions

Library:

```text
MSE
MAE
CrossEntropy
BinaryCrossEntropy
KL
ContrastiveLoss
TripletLoss
```

Loss là ordinary pure computation.

---

## 32. Numerical Stability

Cross entropy nên được biểu diễn bằng stable primitive:

```text
log_softmax
```

thay vì:

```text
softmax
→ log
```

nếu numerical contract cho phép stable rewrite.

---

## 33. Optimizer

Optimizer là stateful algorithm:

```text
SGD
Momentum
Adam
AdamW
RMSProp
Adagrad
```

Không cần runtime base class.

---

## 34. Optimizer State

Ví dụ Adam:

```text
m
v
step
```

là explicit state.

Không hidden global state.

---

## 35. Optimizer Fusion

Có thể fuse:

```text
gradient
→ optimizer update
```

để tránh intermediate traffic.

Ví dụ:

```text
weight
gradient
momentum
```

được xử lý trong một kernel.

---

## 36. Mixed Precision

Model có thể sử dụng:

```text
f32
f16
bf16
```

và:

```text
master parameters
```

nếu training cần precision cao hơn.

---

## 37. Automatic Mixed Precision

Compiler/runtime policy có thể chọn precision cho operations.

Nhưng phải có contract:

```text
Strict
MixedPrecision
Approximate
```

Không được âm thầm thay precision trong Strict mode.

---

## 38. Loss Scaling

Có thể support:

```text
dynamic loss scaling
```

nhưng đây là training library.

---

## 39. Quantization

Distinguish:

```text
f32
bf16
f16
i8
u8
int4
```

với quantization semantics:

```text
scale
zero_point
range
rounding
```

Không coi quantized tensor là ordinary integer tensor.

---

## 40. Quantized Matmul

Compiler có thể lower:

```text
QMatMul
```

xuống:

```text
int8 dot-product
```

hoặc target-specific instructions.

---

## 41. Weight-only Quantization

Ví dụ:

```text
W : int4
X : bf16
```

có thể có specialized kernel.

---

## 42. Quantization Error

Quantization transformation cần numerical proof.

Compiler không được coi:

```text
f32 → int8
```

là semantics-preserving trong Strict mode.

---

## 43. Distributed Training

Không đưa distributed runtime vào Core.

Semantic primitives:

```text
AllReduce
AllGather
ReduceScatter
Broadcast
Send
Receive
```

có thể là library/runtime capabilities.

---

## 44. Distributed Gradient

Data parallel:

```text
worker 1 gradient
worker 2 gradient
worker 3 gradient
       ↓
    AllReduce
```

phải có explicit synchronization semantics.

---

## 45. Communication/Computation Overlap

Compiler/runtime có thể overlap:

```text
compute gradient layer N
+
communicate gradient layer N-1
```

nếu ownership/synchronization proofs cho phép.

---

## 46. Pipeline Parallelism

Model partition:

```text
GPU0 → GPU1 → GPU2 → GPU3
```

là execution graph.

Không phải một ngôn ngữ parallelism mới.

---

## 47. Model Parallelism

Tensor partition:

```text
W = [W0 W1 W2]
```

và collective communication.

Tensor layout metadata phải biểu diễn partition.

---

## 48. Sharded Tensor

Có thể có:

```text
ShardedTensor<T, Partition>
```

nhưng semantics vẫn dựa trên Tensor + Storage + Device.

---

## 49. Distributed Ownership

Một tensor shard thuộc worker/device cụ thể.

Không được implicit đọc shard ở device khác.

Transfer/communication explicit.

---

## 50. Data Loader

Training input pipeline:

```text
Dataset
→ Shuffle
→ Batch
→ Prefetch
→ Device Transfer
```

là streaming/async pipeline.

Có thể dùng:

```text
Async
Channel
Ownership
```

đã được định nghĩa.

---

## 51. DataLoader Zero-copy

Nếu decoder tạo buffer phù hợp:

```text
Disk
→ pinned memory
→ GPU
```

có thể tránh copy trung gian.

---

## 52. Random Augmentation

Augmentation stochastic phải sử dụng explicit RNG.

Ví dụ:

```text
random_crop
random_flip
color_jitter
```

Không dùng hidden global RNG.

---

## 53. Deterministic Training

Có thể yêu cầu:

```text
@deterministic
```

hoặc numerical/execution contract tương đương.

Compiler/runtime phải giữ:

- RNG sequence;
- reduction order;
- synchronization order;
- algorithm choice trong contract.

---

## 54. Checkpoint

Model checkpoint phải phân biệt:

```text
Parameters
OptimizerState
RngState
TrainingStep
ModelMetadata
```

Không serialize compiler objects.

---

## 55. Model Serialization

Static model có thể có compile-time known schema.

Runtime model có thể dùng explicit serialization format.

Không yêu cầu reflection runtime.

---

## 56. Model Compilation

Một model inference có thể compile thành:

```text
model.exe
```

với chỉ:

```text
weights
kernels
required runtime components
```

Không kéo theo training engine.

---

## 57. Weight Embedding

Nếu weights là immutable build input:

```text
comptime
```

có thể embed trực tiếp vào binary hoặc external resource.

---

## 58. Weight Memory Mapping

Weights lớn có thể sử dụng:

```text
mapped file
```

với explicit storage contract.

Compiler không giả định tất cả weights phải copy vào heap.

---

## 59. Graph Optimization

Model graph reuse Expression Graph:

```text
Constant Folding
CSE
Dead Tensor Elimination
Operator Fusion
Layout Propagation
Transpose Elimination
Constant Propagation
```

---

## 60. CompilerDB

Task 385 bổ sung:

```text id="mllm8u"
MlDB
ModelDB
ModelTypeDB
ModelGraphDB
ModelNodeDB
ModelEdgeDB
ModelParameterDB
ModelBufferDB
ModelInputDB
ModelOutputDB
ModelStateDB

LayerDB
LinearLayerDB
ConvLayerDB
ActivationLayerDB
NormalizationLayerDB
PoolingDB
EmbeddingDB
AttentionDB
TransformerDB

TrainingDB
TrainingGraphDB
TrainingStepDB
TrainingStateDB
GradientDB
GradientAccumulationDB
LossDB
OptimizerDB
OptimizerStateDB

InferenceDB
InferenceGraphDB
InferenceSpecializationDB
InferenceOptimizationDB

PrecisionDB
MixedPrecisionDB
LossScalingDB
QuantizationDB
QuantizationSchemeDB
QuantizationCalibrationDB
QuantizedKernelDB

DistributedMlDB
DistributedTensorDB
ShardingDB
PartitionDB
AllReduceDB
AllGatherDB
ReduceScatterDB
PipelineParallelDB
TensorParallelDB
DataParallelDB

DataPipelineDB
DatasetDB
DataLoaderDB
BatchDB
PrefetchDB
AugmentationDB

CheckpointDB
ModelSerializationDB
ModelArtifactDB
WeightStorageDB
WeightMappingDB

MlGraphOptimizationDB
OperatorFusionDB
KernelSelectionDB
MlCostModelDB
MlNumericalDB
MlDeterminismDB
MlGpuDB
MlSimdDB
MlParallelDB
MlAdDB
MlProofDB
MlVerificationDB
```

---

# 61. MIR additions

```text id="0r9x1k"
MODEL_BEGIN
MODEL_END

PARAMETER_CREATE
PARAMETER_LOAD
PARAMETER_STORE

LAYER_FORWARD
MODEL_FORWARD
MODEL_INFERENCE

LINEAR
CONV
POOL
NORMALIZE
ACTIVATE
EMBED
ATTENTION

LOSS
GRADIENT
GRADIENT_ACCUMULATE

OPTIMIZER_STEP
OPTIMIZER_UPDATE

QUANTIZE
DEQUANTIZE
QUANTIZED_MATMUL

MIXED_PRECISION
LOSS_SCALE

OP_FUSE
MODEL_FUSE
MODEL_LAYOUT_PROPAGATE
MODEL_CONSTANT_FOLD

SHARD
RESHARD
ALL_REDUCE
ALL_GATHER
REDUCE_SCATTER
BROADCAST

DATASET_NEXT
BATCH_CREATE
PREFETCH
AUGMENT

CHECKPOINT_SAVE
CHECKPOINT_LOAD

MODEL_COMPILE
MODEL_SPECIALIZE
```

---

# 62. ML Proofs

```text id="l2db6f"
ModelShapeProof
ModelTypeProof
ModelGraphProof
ModelParameterProof

LayerShapeProof
LinearShapeProof
ConvolutionShapeProof
AttentionShapeProof
NormalizationShapeProof

BroadcastProof
GradientShapeProof
DifferentiabilityProof
GradientAccumulationProof

LossNumericalProof
OptimizerStateProof
OptimizerUpdateProof

MixedPrecisionProof
QuantizationProof
QuantizationErrorProof

TensorShardProof
DistributedOwnershipProof
CollectiveOrderingProof
DistributedSynchronizationProof

DataPipelineProof
RandomAugmentationProof
DeterministicTrainingProof

ModelFusionProof
OperatorFusionProof
LayoutPropagationProof
TransposeEliminationProof

InferenceSpecializationProof
WeightStorageProof
CheckpointProof

MlAliasProof
MlStorageProof
MlDeviceProof
MlParallelProof
MlSimdProof
MlGpuProof
MlAdProof
MlNumericalProof
MlDeterminismProof
```

---

# 63. Invariants

### `AML-01`
Model phải có typed input/output semantics.

### `AML-02`
Static tensor shape mismatch phải được phát hiện compile-time.

### `AML-03`
Dynamic shape phải có runtime validation khi cần.

### `AML-04`
Layer abstraction không được yêu cầu runtime object hierarchy.

### `AML-05`
Static model composition phải có thể được monomorphize và inline.

### `AML-06`
Dynamic dispatch chỉ xuất hiện khi programmer/model representation yêu cầu.

### `AML-07`
Parameters phải được phân biệt khỏi ordinary temporary tensors về semantic state.

### `AML-08`
Inference không được giữ AD/training machinery nếu không observable.

### `AML-09`
Gradient generation phải reuse AD engine.

### `AML-10`
Gradient accumulation phải preserve ownership và race semantics.

### `AML-11`
Broadcasting phải được shape solver kiểm chứng.

### `AML-12`
Linear/Conv phải reuse Linear Algebra/Tensor infrastructure.

### `AML-13`
Attention fusion chỉ được thực hiện khi numerical/effect semantics cho phép.

### `AML-14`
Operator fusion không được thay đổi observable tensor semantics.

### `AML-15`
Quantization phải có numerical contract rõ ràng.

### `AML-16`
Mixed precision không được implicit phá vỡ Strict numerical contract.

### `AML-17`
Optimizer state phải có ownership rõ ràng.

### `AML-18`
Optimizer update phải preserve parameter aliasing rules.

### `AML-19`
Random augmentation phải dùng explicit RNG semantics.

### `AML-20`
Deterministic training phải preserve declared RNG/reduction/synchronization semantics.

### `AML-21`
Distributed tensors phải có storage/device ownership rõ ràng.

### `AML-22`
Collective communication phải có synchronization semantics rõ ràng.

### `AML-23`
Implicit cross-device tensor access không được tồn tại trong safe semantics.

### `AML-24`
Sharding/resharding phải preserve logical tensor semantics.

### `AML-25`
Data pipeline phải preserve ownership khi transfer giữa stages.

### `AML-26`
Inference artifact không được kéo theo training runtime nếu không cần.

### `AML-27`
Static weights có thể được embedded/mapped mà không thay đổi model semantics.

### `AML-28`
ML kernels phải có thể lower xuống SIMD/parallel/GPU.

### `AML-29`
ML abstraction phải compile away khi representation không observable.

### `AML-30`
Không sử dụng ML thì chương trình Axiom không được phát sinh ML runtime dependency.

---

# 64. Vị trí của ML trong Axiom

Sau 385, kiến trúc trở thành:

```text
                         AI / AUTONOMOUS SYSTEM
                                  │
             ┌────────────────────┼───────────────────┐
             │                    │                   │
       Machine Learning       Robotics            Vision
             │                    │                   │
       Neural Networks        Planning             Image
             │                    │                   │
             └──────────────┬─────┴───────────────────┘
                            │
                   Tensor / Linear Algebra
                            │
                 AD / Probability / Solver
                            │
                    Numeric / Units
                            │
             Geometry / Physics / Signals
                            │
                SIMD / Parallel / GPU
                            │
                         MIR
                            │
                     Native Machine
```

Điểm quan trọng nhất của **385** là Axiom **không cần trở thành “một PyTorch viết bằng Axiom”**.

Thay vào đó, compiler hiểu đủ semantic để:

```text
Model source
    ↓
Typed tensor graph
    ↓
AD
    ↓
Shape/layout analysis
    ↓
Fusion
    ↓
Memory planning
    ↓
Kernel selection
    ↓
SIMD/GPU
    ↓
Native executable
```

Một model inference cuối cùng có thể chỉ còn **weights + machine kernels + đúng những runtime capabilities mà nó thực sự sử dụng**.