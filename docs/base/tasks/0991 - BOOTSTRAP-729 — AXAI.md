# BOOTSTRAP-729 — AXAI

**Namespace:** `AXAI`  
**Phase:** Axiom Civilization Runtime / Native Artificial Intelligence Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXCOMPUTE`, `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXSECURITY`, `AXIDENTITY`, `AXGEOSPATIAL`, `AXASSET`

> `AXAI` là runtime AI native của Axiom, không phải một chatbot framework. Mục tiêu là biến CPU/GPU/NPU, tensor, model, training, inference, agent và AI workload thành các primitive native của hệ sinh thái Axiom.

---

# 729.0 — Mục tiêu

AXAI phải hỗ trợ cùng một execution model cho:

```text
classical ML
deep learning
LLM
vision
audio
speech
multimodal
reinforcement learning
scientific AI
generative AI
AI agents
on-device AI
distributed AI
```

Kiến trúc tổng quát:

```text
                    AXAI
                      │
       ┌──────────────┼───────────────┐
       ↓              ↓               ↓
    Tensor          Model          Dataset
       │              │               │
       └──────────────┼───────────────┘
                      ↓
                Compute Graph
                      ↓
             AXCOMPUTE Runtime
                      ↓
             CPU / GPU / NPU
```

---

# 729.1 — AI Boundary

`AXAI` sở hữu:

```text
tensor semantics
tensor memory/layout
model representation
model execution
training
automatic differentiation
optimization
datasets
embeddings
vector representation
model registry
model versioning
evaluation
AI agents
tool orchestration
AI provenance
AI simulation
```

Không sở hữu:

```text
CPU/GPU physical resources → AXCOMPUTE
persistent storage         → AXSTORAGE
database                   → AXDATABASE
network transport          → AXNETWORK
cryptography               → AXSECURITY
human identity             → AXIDENTITY
physical assets            → AXASSET
```

---

# 729.2 — Tensor

Primitive trung tâm:

```axiom
tensor<T, shape, layout, device>
```

Ví dụ:

```axiom
tensor<f32, [1024, 1024]>
tensor<f16, [8, 4096, 4096], gpu>
tensor<i8, [4096, 4096]>
```

Tensor phải là first-class native type.

---

# 729.3 — Tensor Dimensions

Hỗ trợ:

```text
static dimensions
dynamic dimensions
symbolic dimensions
bounded dynamic dimensions
unknown dimensions
```

Ví dụ:

```axiom
tensor<f32, [batch, sequence, hidden]>
```

---

# 729.4 — Tensor Rank

```text
scalar → rank 0
vector → rank 1
matrix → rank 2
tensor → rank N
```

Không cần tạo các class riêng cho từng rank.

---

# 729.5 — Tensor Element Types

Native:

```text
bool
i8 i16 i32 i64
u8 u16 u32 u64
f16
bf16
f32
f64
```

AI extensions:

```text
fp8
int4
int2
quantized
complex64
complex128
```

Compiler phải biết semantic precision.

---

# 729.6 — Tensor Layout

```axiom
layout {
    shape
    strides
    offset
    contiguous
}
```

Layouts:

```text
row_major
column_major
strided
blocked
tiled
packed
channel_first
channel_last
```

Không ép mọi tensor thành contiguous.

---

# 729.7 — Tensor Device

```text
CPU
GPU
NPU
ACCELERATOR
UNIFIED_MEMORY
REMOTE
```

Device ownership → `AXCOMPUTE`.

---

# 729.8 — Tensor Memory

Tensor có thể nằm trong:

```text
host memory
device memory
unified memory
mapped memory
shared memory
remote memory
```

Copy chỉ thực hiện khi semantic yêu cầu.

---

# 729.9 — Zero-Copy Tensor

Nếu hai operation compatible:

```text
tensor A
   ↓
view
   ↓
tensor B
```

không copy dữ liệu.

---

# 729.10 — Tensor View

```axiom
view(tensor)
slice(tensor)
reshape(tensor)
transpose(tensor)
permute(tensor)
broadcast(tensor)
```

View phải có ownership/lifetime semantics rõ ràng theo memory model Axiom.

---

# 729.11 — Tensor Operations

Core:

```text
add
sub
mul
div
matmul
dot
reduce
sum
mean
max
min
argmax
reshape
transpose
concat
stack
split
slice
gather
scatter
pad
interpolate
```

---

# 729.12 — Neural Operations

```text
conv1d
conv2d
conv3d
pool
normalization
activation
attention
embedding
linear
dropout
softmax
layer_norm
rms_norm
```

---

# 729.13 — Operator Registry

```axiom
operator {
    name
    inputs
    outputs
    attributes
    constraints
    kernels
}
```

Operators phải có typed signatures.

---

# 729.14 — Broadcasting

Broadcasting phải được xác định compile-time khi shape static.

Dynamic shape → runtime validation.

Không được silently reshape tensor.

---

# 729.15 — Shape Checking

```text
compile-time:
    tensor<f32,[32,64]>
    × tensor<f32,[64,128]>
        ↓
    tensor<f32,[32,128]>
```

Shape mismatch phải là compile error nếu compiler biết được.

---

# 729.16 — Compute Graph

```axiom
graph {
    inputs
    nodes
    edges
    outputs
}
```

Ví dụ:

```text
input
 ↓
embedding
 ↓
attention
 ↓
normalization
 ↓
linear
 ↓
output
```

---

# 729.17 — Graph Compilation

Graph có thể được:

```text
validated
optimized
fused
scheduled
partitioned
compiled
cached
```

---

# 729.18 — Operator Fusion

Compiler/runtime có thể biến:

```text
A → matmul → bias → activation
```

thành:

```text
fused_kernel
```

nhằm giảm:

```text
memory traffic
kernel launches
temporary tensors
```

---

# 729.19 — Constant Folding

Model constants phải được fold khi có thể:

```text
constant
 +
constant
 →
constant
```

---

# 729.20 — Dead Tensor Elimination

Tensor intermediate không còn được sử dụng phải được loại khỏi graph.

---

# 729.21 — Memory Planning

Graph compiler xây:

```text
tensor lifetime graph
```

sau đó reuse buffer:

```text
Tensor A ──────┐
               ├── Buffer 1
Tensor B ──────┘
```

khi lifetime không overlap.

---

# 729.22 — Training Graph

Training graph:

```text
forward
   ↓
loss
   ↓
backward
   ↓
gradient
   ↓
optimizer
```

---

# 729.23 — Automatic Differentiation

```axiom
grad(f, x)
jacobian(f, x)
hessian(f, x)
```

Hỗ trợ:

```text
reverse mode
forward mode
mixed mode
```

---

# 729.24 — Gradient Tape

```axiom
tape {
    operations
    dependencies
    saved_tensors
}
```

Có thể:

```text
record
backward
release
checkpoint
```

---

# 729.25 — Gradient Memory Optimization

Hỗ trợ:

```text
activation checkpointing
recomputation
gradient accumulation
memory offload
```

---

# 729.26 — Optimizers

Native primitives:

```text
SGD
Momentum
Adam
AdamW
RMSProp
Adagrad
Lion-like extensible optimizer
```

Optimizer không phải language primitive; là AXAI library/runtime module built trên native tensor operations.

---

# 729.27 — Parameter

```axiom
parameter<T> {
    value
    gradient
    requires_grad
}
```

---

# 729.28 — Model

```axiom
model {
    parameters
    buffers
    graph
    metadata
}
```

Model phải có deterministic identity/version.

---

# 729.29 — Model Composition

```axiom
model Encoder {
    ...
}

model Decoder {
    ...
}

model AutoEncoder {
    encoder: Encoder
    decoder: Decoder
}
```

Compiler có thể inline/fuse graph khi phù hợp.

---

# 729.30 — Model State

Tách:

```text
architecture
parameters
buffers
optimizer state
metadata
```

Không trộn tất cả thành một opaque blob.

---

# 729.31 — Model Serialization

Native model artifact phải hỗ trợ:

```text
schema
weights
graph
dtype
layout
device-neutral representation
metadata
provenance
checksum
```

---

# 729.32 — Model Artifact

```axiom
model_artifact {
    model_id
    version
    architecture
    weights
    metadata
    provenance
    integrity
}
```

---

# 729.33 — Model Versioning

Version immutable:

```text
Model v1
Model v2
Model v3
```

Không mutate artifact đã published.

---

# 729.34 — Model Registry

```axiom
model_registry {
    models
    versions
    aliases
    deployments
}
```

Aliases:

```text
stable
latest
production
experimental
```

Alias không thay đổi immutable model version.

---

# 729.35 — Dataset

```axiom
dataset {
    dataset_id
    schema
    source
    partitions
    versions
}
```

Dataset có version.

---

# 729.36 — Dataset Sample

```axiom
sample {
    features
    labels
    metadata
    provenance
}
```

---

# 729.37 — Dataset Pipeline

```text
source
 ↓
decode
 ↓
validate
 ↓
transform
 ↓
augment
 ↓
batch
 ↓
prefetch
 ↓
device
```

Pipeline phải streaming-capable.

---

# 729.38 — DataLoader

```axiom
loader {
    dataset
    batch_size
    workers
    prefetch
    shuffle
    sampler
}
```

Không yêu cầu load toàn bộ dataset vào RAM.

---

# 729.39 — Dataset Sharding

```text
dataset
 ├── shard 0
 ├── shard 1
 ├── shard 2
 └── ...
```

Hỗ trợ:

```text
node sharding
worker sharding
epoch sharding
```

---

# 729.40 — Deterministic Dataset

Dataset pipeline có thể yêu cầu:

```axiom
deterministic = true
seed = ...
```

để reproducibility.

---

# 729.41 — Data Provenance

Mỗi training artifact có thể trace:

```text
model
 ↓
training run
 ↓
dataset version
 ↓
preprocessing version
 ↓
code version
 ↓
hyperparameters
 ↓
hardware
```

---

# 729.42 — Training Run

```axiom
training_run {
    run_id
    model
    dataset
    configuration
    hardware
    seed
    checkpoints
    metrics
}
```

---

# 729.43 — Training Lifecycle

```text
CREATED
 ↓
VALIDATING
 ↓
QUEUED
 ↓
ALLOCATING
 ↓
INITIALIZING
 ↓
RUNNING
 ↓
CHECKPOINTING
 ↓
COMPLETED
```

Alternative:

```text
PAUSED
CANCELLED
FAILED
RECOVERING
```

---

# 729.44 — Checkpoint

```axiom
checkpoint {
    model_state
    optimizer_state
    scheduler_state
    epoch
    step
    RNG_state
    metadata
}
```

Checkpoint phải đủ để resume khi configuration tương thích.

---

# 729.45 — Fault Recovery

Training runtime hỗ trợ:

```text
node failure
GPU failure
process failure
network interruption
storage interruption
```

Recovery:

```text
last valid checkpoint
 ↓
resource reallocation
 ↓
resume
```

---

# 729.46 — Distributed Training

Primitive:

```text
worker
rank
world
group
collective
```

Operations:

```text
all_reduce
all_gather
broadcast
reduce_scatter
barrier
send
receive
```

---

# 729.47 — Distributed Model Parallelism

Hỗ trợ:

```text
data parallel
tensor parallel
pipeline parallel
sequence parallel
expert parallel
hybrid parallel
```

---

# 729.48 — Distributed Dataset

Dataset và model partition phải tách semantic:

```text
data sharding
    ≠
model sharding
```

---

# 729.49 — Mixed Precision

Graph có thể chỉ định:

```axiom
precision {
    compute = fp16
    accumulation = fp32
    parameters = bf16
}
```

Precision conversion phải explicit hoặc compiler-approved theo policy.

---

# 729.50 — Quantization

Hỗ trợ:

```text
dynamic quantization
static quantization
weight-only
activation quantization
mixed precision
```

Metadata:

```text
scale
zero_point
axis
scheme
calibration
```

---

# 729.51 — Sparse Tensor

```axiom
sparse_tensor {
    values
    indices
    shape
    format
}
```

Formats:

```text
COO
CSR
CSC
blocked
structured_sparse
```

---

# 729.52 — Embedding

```axiom
embedding<T> {
    dimension
    metric
}
```

Embeddings là numerical representation, không phải semantic truth.

---

# 729.53 — Vector Search

AXAI có thể tạo vector representation.

Actual vector database/search infrastructure:

→ `AXDATABASE`.

Flow:

```text
document
 ↓
AXAI embedding
 ↓
AXDATABASE vector index
 ↓
nearest-neighbor query
```

---

# 729.54 — Multimodal Tensor

AXAI phải coi:

```text
text
image
audio
video
speech
3D
sensor
geospatial
```

là data sources có thể chuyển thành tensor representations.

---

# 729.55 — Tokenization Boundary

Tokenizer có thể là AI preprocessing component:

```axiom
tokenizer {
    encode()
    decode()
    vocabulary
}
```

Nhưng text encoding không được hard-code vào tensor runtime.

---

# 729.56 — Sequence Model

Primitive graph phải hỗ trợ:

```text
sequence length
attention mask
causal mask
position representation
KV cache
```

---

# 729.57 — KV Cache

```axiom
kv_cache {
    keys
    values
    position
    layer
}
```

Có thể reside:

```text
CPU
GPU
unified
paged device memory
```

---

# 729.58 — Inference Session

```axiom
inference_session {
    model
    device
    execution_plan
    memory_plan
}
```

Session có thể reuse compiled execution plan.

---

# 729.59 — Inference Request

```axiom
inference_request {
    inputs
    parameters
    deadline
    priority
}
```

---

# 729.60 — Batched Inference

Runtime hỗ trợ:

```text
static batching
dynamic batching
continuous batching
micro batching
```

Scheduler thuộc integration với `AXCOMPUTE`.

---

# 729.61 — Streaming Inference

AI output có thể stream:

```text
input
 ↓
partial computation
 ↓
output chunk
 ↓
output chunk
 ↓
...
```

Không yêu cầu toàn bộ result nằm trong memory.

---

# 729.62 — Model Compilation Cache

```text
model
+
hardware
+
driver/backend
+
precision
+
shape
+
compiler version
```

→ deterministic execution artifact cache.

Source/model không thay đổi → có thể reuse compiled artifact.

---

# 729.63 — Backend Abstraction

```axiom
ai_backend {
    compile()
    allocate()
    execute()
    synchronize()
}
```

Backend:

```text
CPU
GPU
NPU
custom accelerator
```

---

# 729.64 — CPU Backend

Không yêu cầu external AI framework.

Compiler/runtime có thể generate:

```text
SIMD
vector operations
threaded kernels
cache-aware kernels
```

---

# 729.65 — GPU Backend

AXAI mô tả GPU execution abstractly:

```text
kernel
grid
block
thread
shared_memory
device_memory
synchronization
```

Actual physical backend → `AXCOMPUTE`.

---

# 729.66 — NPU Backend

NPU có thể impose:

```text
supported dtypes
static shape constraints
operator limitations
memory limits
```

Compiler phải validate trước deployment.

---

# 729.67 — Graph Partitioning

Một model có thể chạy:

```text
CPU
 ↓
GPU
 ↓
NPU
 ↓
CPU
```

Compiler tối ưu transfer boundaries.

---

# 729.68 — Data Locality

Execution planner tối ưu:

```text
compute locality
memory locality
NUMA locality
device locality
network locality
```

Không tự động copy tensor qua network nếu không cần.

---

# 729.69 — AI Scheduler

Scheduler nhận:

```text
workload
deadline
priority
device requirements
memory requirements
energy constraints
```

và gửi resource request tới:

→ `AXCOMPUTE`.

---

# 729.70 — AI Agent

AI agent là first-class runtime abstraction:

```axiom
agent {
    model
    memory
    tools
    policy
    state
}
```

Agent không phải một model.

---

# 729.71 — Agent Loop

```text
observe
 ↓
reason
 ↓
plan
 ↓
tool call
 ↓
observe result
 ↓
update state
 ↓
continue
```

---

# 729.72 — Agent State

```axiom
agent_state {
    conversation
    working_memory
    task_state
    tool_state
    checkpoints
}
```

Persistent memory:

→ `AXSTORAGE` / `AXDATABASE`.

---

# 729.73 — Tool

```axiom
ai_tool {
    name
    input_schema
    output_schema
    capability
    execution_policy
}
```

Tool phải typed.

---

# 729.74 — Tool Invocation

```text
agent
 ↓
tool selection
 ↓
capability validation
 ↓
AXSECURITY
 ↓
tool execution
 ↓
result
 ↓
agent
```

AI không bypass capability system.

---

# 729.75 — Agent Permissions

Agent phải có:

```text
identity
capabilities
resource limits
time limits
tool scope
data scope
```

Agent không mặc định có toàn quyền.

---

# 729.76 — AI Memory

Phân biệt:

```text
working memory
episodic memory
semantic memory
persistent application data
```

AXAI định nghĩa semantic interface.

Persistence:

→ AXSTORAGE / AXDATABASE.

---

# 729.77 — Retrieval-Augmented Generation

Native pipeline:

```text
query
 ↓
embedding
 ↓
AXDATABASE vector search
 ↓
candidate retrieval
 ↓
ranking
 ↓
context construction
 ↓
model inference
```

Vector similarity không phải factual verification.

---

# 729.78 — AI Output

```axiom
ai_output {
    value
    model
    model_version
    input_reference
    timestamp
    provenance
    confidence
}
```

---

# 729.79 — AI Output Classification

```text
GENERATED
PREDICTED
CLASSIFIED
RECOMMENDED
EXTRACTED
SUMMARIZED
VERIFIED
AUTHORITATIVE
```

`AUTHORITATIVE` chỉ được cấp bởi domain workflow có authority phù hợp.

---

# 729.80 — AI ≠ Authority

AI prediction không tự động trở thành:

```text
legal fact
medical diagnosis
financial transaction
identity fact
academic grade
property ownership
government decision
```

Domain runtime quyết định authority.

---

# 729.81 — Human-in-the-Loop

Các operation nhạy cảm có thể yêu cầu:

```axiom
human_approval
multi_party_approval
review
```

AI chỉ tạo proposal.

---

# 729.82 — AI Evaluation

```axiom
evaluation {
    model
    dataset
    metrics
    configuration
    results
}
```

Metrics có thể:

```text
accuracy
precision
recall
F1
loss
latency
throughput
memory
energy
```

Không có một metric chung cho mọi model.

---

# 729.83 — Benchmark

```axiom
benchmark {
    workload
    hardware
    model
    dataset
    duration
    metrics
}
```

Kết quả phải ghi rõ hardware/software environment.

---

# 729.84 — Reproducibility

Training/inference có thể record:

```text
model version
dataset version
code version
compiler version
backend version
hardware
random seeds
configuration
```

---

# 729.85 — Randomness

AI runtime phải cung cấp explicit RNG:

```axiom
rng {
    seed
    algorithm
    state
}
```

Không phụ thuộc hidden global RNG cho deterministic workflows.

---

# 729.86 — Model Safety Metadata

```axiom
model_policy {
    allowed_use
    prohibited_use
    data_constraints
    deployment_constraints
}
```

Metadata không tự enforce security; policy enforcement thuộc runtime/security layer.

---

# 729.87 — Sensitive Data

AI pipeline phải propagate:

```text
privacy_classification
purpose
retention
access_policy
provenance
```

---

# 729.88 — Data Lineage

```text
input data
 ↓
preprocessing
 ↓
tensor
 ↓
model
 ↓
output
 ↓
application action
```

Có thể truy ngược lineage.

---

# 729.89 — Model Lineage

```text
base model
 ↓
fine-tuning
 ↓
quantization
 ↓
optimization
 ↓
deployment artifact
```

Không được mất parent lineage.

---

# 729.90 — Model Conversion

```axiom
convert_model(
    source,
    target_backend
)
```

Conversion phải preserve:

```text
semantics
weights
metadata
precision
provenance
```

nếu target backend có thể biểu diễn đầy đủ.

---

# 729.91 — Model Compatibility

```axiom
check_model_compatibility()
```

Result:

```text
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
```

Không silently approximate unsupported operators.

---

# 729.92 — AI Event Model

```axiom
ai_event {
    event_id
    type
    actor
    model
    input_reference
    output_reference
    timestamp
    provenance
}
```

Events:

```text
MODEL_REGISTERED
MODEL_VERSIONED
MODEL_COMPILED
MODEL_DEPLOYED

TRAINING_CREATED
TRAINING_STARTED
TRAINING_CHECKPOINTED
TRAINING_COMPLETED
TRAINING_FAILED

INFERENCE_STARTED
INFERENCE_COMPLETED

AGENT_CREATED
AGENT_TOOL_CALLED
AGENT_COMPLETED

EVALUATION_COMPLETED
MODEL_RETIRED
```

---

# 729.93 — AI Replay

```axiom
replay_ai_run(run_id)
```

Replay có thể:

```text
re-execute
inspect
compare
benchmark
```

Không tạo production side effects.

---

# 729.94 — AI Simulation

```axiom
simulate_ai_system()
```

Có thể mô phỏng:

```text
model deployment
resource allocation
agent behavior
latency
memory usage
failure recovery
distributed inference
```

---

# 729.95 — AI Digital Twin

```axiom
ai_digital_twin {
    models
    datasets
    hardware
    workloads
    agents
    dependencies
}
```

Dùng cho capacity planning và architecture testing.

---

# 729.96 — AI + AXCOMPUTE

```text
AXAI
 ↓
execution graph
 ↓
resource requirements
 ↓
AXCOMPUTE
 ↓
CPU/GPU/NPU allocation
```

AXAI không tự sở hữu physical scheduler.

---

# 729.97 — AI + AXSTORAGE

Model/dataset/checkpoint:

```text
AXAI semantic object
        ↓
AXSTORAGE artifact
```

Storage engine không hiểu model semantics.

---

# 729.98 — AI + AXDATABASE

```text
metadata
training records
experiments
embeddings
vector indexes
evaluation results
```

→ AXDATABASE.

---

# 729.99 — AI + AXNETWORK

Distributed AI dùng:

```text
collectives
RPC
streaming
parameter transfer
checkpoint transfer
model serving
```

→ AXNETWORK.

---

# 729.100 — AI + AXSECURITY

Mọi agent/tool/model deployment phải có:

```text
identity
capability
policy
audit
isolation
```

---

# 729.101 — AI + AXIDENTITY

Model/service/agent có identity:

```text
agent_identity
model_publisher_identity
training_operator_identity
deployment_identity
```

Không dùng model ID thay identity.

---

# 729.102 — AI + AXGEOSPATIAL

Spatial AI có thể consume:

```text
geometry
raster
terrain
remote sensing
sensor data
```

nhưng authoritative spatial state vẫn thuộc `AXGEOSPATIAL`.

---

# 729.103 — Native APIs

Core API:

```axiom
tensor()
tensor_view()
reshape()
transpose()
matmul()
reduce()

compile_graph()
optimize_graph()
execute_graph()

grad()
backward()

create_model()
load_model()
save_model()
compile_model()

create_dataset()
create_loader()
train()
evaluate()

create_checkpoint()
restore_checkpoint()

create_embedding()
vectorize()

create_inference_session()
infer()
stream_infer()

register_model()
publish_model()
deploy_model()
retire_model()

create_agent()
run_agent()
pause_agent()
resume_agent()
checkpoint_agent()

register_tool()
invoke_tool()

trace_ai_run()
replay_ai_run()
simulate_ai_system()
```

---

# 729.104 — Formal Invariants

```text
AI-INV-01   Tensor shape is explicit.
AI-INV-02   Tensor dtype is explicit.
AI-INV-03   Tensor layout is explicit.
AI-INV-04   Tensor device is explicit when non-default.
AI-INV-05   Shape-incompatible static operations fail at compile time.
AI-INV-06   Runtime shape validation is mandatory for dynamic shapes.
AI-INV-07   Views do not silently copy data.
AI-INV-08   Copies are explicit or compiler-proven necessary.
AI-INV-09   Tensor memory ownership is defined.
AI-INV-10   Tensor operations are type-safe.

AI-INV-11   Compute graphs have explicit inputs and outputs.
AI-INV-12   Graph optimization preserves declared semantics.
AI-INV-13   Unsupported operators cannot be silently replaced.
AI-INV-14   Fused kernels preserve observable semantics.
AI-INV-15   Temporary tensor lifetime is analyzable.
AI-INV-16   Memory reuse cannot overlap live tensor lifetimes.
AI-INV-17   Device transfers are explicit in execution planning.
AI-INV-18   Backend capabilities are discoverable.
AI-INV-19   Compilation artifacts identify their target environment.
AI-INV-20   Cached compiled artifacts are invalidated when compatibility changes.

AI-INV-21   Model architecture and model parameters are distinct.
AI-INV-22   Published model versions are immutable.
AI-INV-23   Model lineage is preserved.
AI-INV-24   Dataset versions are identifiable.
AI-INV-25   Training runs identify model and dataset versions.
AI-INV-26   Checkpoints identify compatible training state.
AI-INV-27   Resume cannot silently mix incompatible states.
AI-INV-28   Deterministic runs record RNG state/configuration.
AI-INV-29   Distributed ranks have explicit identity.
AI-INV-30   Collective operations have defined synchronization semantics.

AI-INV-31   AI output carries provenance when configured as auditable.
AI-INV-32   AI prediction is not automatically authoritative domain state.
AI-INV-33   AI agents cannot bypass AXSECURITY capabilities.
AI-INV-34   Tool invocation is policy-controlled.
AI-INV-35   Agent identity is distinct from model identity.
AI-INV-36   AI replay cannot mutate production state.
AI-INV-37   AI simulation cannot mutate production state.
AI-INV-38   Sensitive data policies propagate through AI pipelines.
AI-INV-39   Vector similarity is not equivalent to semantic truth.
AI-INV-40   AI-derived state is distinguishable from authoritative state.
```

---

# 729.105 — Performance Architecture

AXAI phải ưu tiên:

```text
zero-copy
memory reuse
operator fusion
compile-time shape analysis
static graph optimization
SIMD/vectorization
GPU kernel fusion
NPU specialization
mixed precision
quantization
persistent execution plans
KV-cache reuse
streaming
NUMA awareness
device locality
asynchronous execution
```

Không xây architecture kiểu:

```text
Axiom tensor
 → generic object
 → serialization
 → RPC
 → external framework
 → device
```

cho hot path.

---

# 729.106 — Axiom Compiler Integration

Compiler có thể nhìn thấy:

```text
tensor type
shape
dtype
layout
device
operator graph
```

Do đó có thể optimize ở compile time.

Ví dụ:

```axiom
fn inference(
    x: tensor<f16, [1, 1024], gpu>
) -> tensor<f16, [1, 4096], gpu>
```

Compiler có thể biết:

```text
shape
dtype
device
```

trước runtime.

---

# 729.107 — AI Native Syntax Direction

Axiom không nên biến thành DSL chỉ dành cho AI.

Mục tiêu:

```text
ordinary Axiom
       +
tensor types
       +
graph semantics
       +
accelerator execution
```

Ví dụ:

```axiom
fn linear(
    x: tensor<f16, [N, 1024]>,
    w: tensor<f16, [1024, 4096]>
) -> tensor<f16, [N, 4096]>
{
    return x @ w
}
```

AI code vẫn là Axiom code.

---

# 729.108 — Không phụ thuộc Framework

`AXAI` architecture không yêu cầu:

```text
PyTorch
TensorFlow
JAX
ONNX Runtime
CUDA framework
```

làm semantic dependency.

External model formats/backends có thể được viết dưới dạng adapters.

---

# 729.109 — External Model Import

Có thể hỗ trợ adapters:

```text
ONNX
SafeTensors
GGUF
custom Axiom model
```

nhưng:

```text
external format
    ≠
AXAI native semantic model
```

---

# 729.110 — Native Model Format

Axiom nên có format:

```text
.axmodel
```

với:

```text
header
schema
graph
weights
tensor metadata
quantization metadata
provenance
integrity
```

Có thể mmap weights trực tiếp khi layout tương thích.

---

# 729.111 — Native Dataset Format

Có thể có:

```text
.axdata
```

nhưng dataset semantic không nên bị khóa vào một physical format.

AXSTORAGE cung cấp underlying storage.

---

# 729.112 — Agent Runtime Isolation

Agent execution nên hỗ trợ:

```text
sandbox
resource quota
memory limit
CPU/GPU quota
network capability
storage capability
tool capability
execution timeout
```

Integration:

```text
AXAI
 ↓
AXSECURITY
 ↓
AXCOMPUTE
 ↓
AXNETWORK / AXSTORAGE
```

---

# 729.113 — AI Failure Model

Các failure phải phân biệt:

```text
MODEL_ERROR
DATA_ERROR
SHAPE_ERROR
DEVICE_ERROR
MEMORY_ERROR
NETWORK_ERROR
CHECKPOINT_ERROR
RESOURCE_DENIED
POLICY_DENIED
TIMEOUT
NON_DETERMINISTIC
UNSUPPORTED_OPERATOR
```

Không trả về một generic `AI_ERROR`.

---

# 729.114 — AI Observability

Telemetry:

```text
latency
throughput
memory
VRAM
kernel time
transfer time
queue time
tokens/sec
samples/sec
energy reference
error rate
```

Tracing:

```text
request
 ↓
graph
 ↓
operator
 ↓
kernel
 ↓
device
```

---

# 729.115 — AI Cost Accounting

`AXAI` tạo resource usage:

```text
compute time
memory
GPU time
storage
network
```

Actual monetary accounting:

→ `AXFINANCE`.

---

# 729.116 — AI Deployment

```text
model
 ↓
validate
 ↓
compile
 ↓
package
 ↓
register
 ↓
deploy
 ↓
health check
 ↓
ACTIVE
```

Deployment lifecycle:

```text
CREATED
VALIDATING
COMPILED
STAGED
DEPLOYED
ACTIVE
PAUSED
RETIRED
FAILED
```

---

# 729.117 — Model Rollback

```axiom
rollback_deployment(
    deployment,
    target_version
)
```

Target phải là immutable compatible version.

---

# 729.118 — Model A/B Execution

Runtime có thể chạy nhiều model versions:

```text
deployment A
deployment B
```

Nhưng routing policy phải explicit.

AXAI không tự kết luận model nào "tốt hơn".

---

# 729.119 — AI Policy

Policy có thể kiểm soát:

```text
allowed model
allowed dataset
allowed hardware
allowed user
allowed geographic region
allowed data class
allowed tools
allowed output class
```

Policy engine → `AXSECURITY` / domain-specific policy.

---

# 729.120 — Completion Criteria

`BOOTSTRAP-729` phải freeze:

1. Tensor type.
2. Shape system.
3. Dynamic dimensions.
4. Dtypes.
5. Layout.
6. Device.
7. Memory.
8. Views.
9. Zero-copy.
10. Core operators.
11. Neural operators.
12. Operator registry.
13. Broadcasting.
14. Shape checking.
15. Compute graph.
16. Graph compilation.
17. Operator fusion.
18. Constant folding.
19. Dead tensor elimination.
20. Memory planning.
21. Automatic differentiation.
22. Gradient tape.
23. Checkpointing.
24. Optimizers.
25. Parameters.
26. Model abstraction.
27. Model serialization.
28. Model artifact.
29. Model versioning.
30. Model registry.
31. Dataset.
32. Dataset pipeline.
33. DataLoader.
34. Dataset sharding.
35. Data provenance.
36. Training runs.
37. Distributed training.
38. Model parallelism.
39. Mixed precision.
40. Quantization.
41. Sparse tensors.
42. Embeddings.
43. Vector-search integration.
44. Multimodal tensors.
45. Tokenization interface.
46. Sequence models.
47. KV cache.
48. Inference sessions.
49. Batched inference.
50. Streaming inference.
51. Compilation cache.
52. Backend abstraction.
53. CPU backend.
54. GPU backend.
55. NPU backend.
56. Graph partitioning.
57. Data locality.
58. AI scheduling.
59. AI agents.
60. Agent state.
61. Tools.
62. Tool capability enforcement.
63. Agent memory.
64. RAG.
65. AI output provenance.
66. AI authority boundary.
67. Human approval.
68. Evaluation.
69. Benchmarking.
70. Reproducibility.
71. Model conversion.
72. Model compatibility.
73. AI events.
74. Replay.
75. Simulation.
76. Digital twin.
77. AXCOMPUTE integration.
78. AXSTORAGE integration.
79. AXDATABASE integration.
80. AXNETWORK integration.
81. AXSECURITY integration.
82. AXIDENTITY integration.
83. AXGEOSPATIAL integration.
84. Native model format.
85. External model adapters.
86. Agent sandbox.
87. Failure model.
88. Observability.
89. Resource accounting.
90. Deployment.
91. Rollback.
92. Multi-version deployment.
93. Policy integration.
94. Formal invariants.
95. Compiler integration.
96. Performance architecture.

---

# 729.121 — Definition of Done

```text
BOOTSTRAP-729
STATUS: COMPLETE / FROZEN

AXAI
 ├── Native Tensor Runtime
 ├── Shape & Type System
 ├── CPU/GPU/NPU Execution
 ├── Compute Graph
 ├── Autodiff
 ├── Training Runtime
 ├── Distributed Training
 ├── Inference Runtime
 ├── Quantization
 ├── Embeddings
 ├── Multimodal AI
 ├── Model Registry
 ├── Dataset Runtime
 ├── Checkpointing
 ├── AI Evaluation
 ├── AI Provenance
 ├── AI Agents
 ├── Tool Runtime
 ├── AI Memory
 ├── RAG
 ├── Model Deployment
 ├── AI Simulation
 ├── AI Digital Twin
 ├── Security Integration
 └── Native Compiler Integration
```

**BOOTSTRAP-729 / AXAI — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-730 — AXMEDIA

**Native Media & Multimedia Runtime — audio, video, image, codecs, containers, streams, frames, timelines, subtitles, metadata, capture, playback, transcoding, editing primitives, synchronization, spatial audio, speech interfaces, media pipelines, GPU acceleration, zero-copy media buffers, live streaming, recording, media indexing, content addressing, media AI integration, deterministic media processing, distributed media processing & Media Runtime 5.0.**