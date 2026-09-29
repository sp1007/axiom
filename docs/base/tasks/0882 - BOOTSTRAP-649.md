Tiếp tục với **BOOTSTRAP-649 — Native AI Multimodal Foundation, Unified Representation, Cross-Modal Embedding, Vision-Language-Audio-Speech Processing, Multimodal Fusion & Generative Media Runtime 5.0**.

:::writing{variant="document" id="38427" title="BOOTSTRAP-649 — Native AI Multimodal Foundation, Unified Representation, Cross-Modal Embedding, Vision-Language-Audio-Speech Processing, Multimodal Fusion & Generative Media Runtime 5.0"}
# BOOTSTRAP-649
## Native AI Multimodal Foundation, Unified Representation, Cross-Modal Embedding, Vision-Language-Audio-Speech Processing, Multimodal Fusion & Generative Media Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native Multimodal AI Representation & Generation Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-648

---

# 1. Mục tiêu

BOOTSTRAP-649 bổ sung native multimodal AI runtime cho Axiom.

Mục tiêu:

- text understanding;
- image understanding;
- audio understanding;
- speech understanding;
- video understanding;
- vision-language;
- audio-language;
- speech-language;
- cross-modal embeddings;
- multimodal tokenization;
- modality alignment;
- multimodal fusion;
- multimodal generation;
- unified context;
- multimodal retrieval;
- multimodal RAG;
- multimodal agent perception;
- multimodal tool interaction;
- media-conditioned generation;
- streaming multimodal inference.

Kiến trúc không biến Axiom thành một framework chỉ dành cho LLM.

Thay vào đó:

```text
Text
Image
Audio
Speech
Video
Sensor
Graph
Structured Data
       │
       ▼
Unified Multimodal Representation
       │
       ▼
Multimodal Model
       │
 ┌─────┼─────┐
 ▼     ▼     ▼
Text  Image  Audio
       │
       ▼
Agent / Search / Knowledge / Generation
```

---

# 2. Boundary

Các layer liên quan:

```text
617  Text / Unicode
616  Audio / Video / Media
615  Graphics
614  Device / Camera / GPU
641  Search / Vector Retrieval
642  Analytics
643  Tensor / ML
644  Agent
645  Knowledge Graph
646  Evaluation
647  Model Lifecycle
648  Simulation
649  Multimodal AI
```

649 **không thay thế** 616.

616 quản lý media.

649 hiểu media dưới góc độ AI representation/model execution.

---

# 3. Nguyên tắc kiến trúc

1. Modality là explicit.
2. Representation có type.
3. Shape có metadata.
4. Sampling rate phải được ghi rõ.
5. Timestamp phải được bảo toàn.
6. Audio/video không được mất temporal metadata.
7. Image giữ color-space metadata.
8. Text giữ Unicode semantics.
9. Speech giữ language metadata khi biết.
10. Cross-modal alignment phải explicit.
11. Embedding model identity phải được lưu.
12. Embedding dimension phải được lưu.
13. Không giả định mọi embedding cùng không gian.
14. Projection giữa modality là explicit.
15. Fusion strategy phải explicit.
16. Generation modality phải explicit.
17. Streaming phải bounded.
18. Context phải có budget.
19. Model artifact phải versioned.
20. Preprocessing phải versioned.
21. Tokenizer phải versioned.
22. Feature extractor phải versioned.
23. No mandatory Python runtime.
24. No mandatory PyTorch/TensorFlow/JAX.
25. External model providers là adapter.
26. No arbitrary code execution khi load model.
27. Model-generated metadata không mặc định là ground truth.
28. Provenance phải được bảo toàn.
29. Governance từ 640 áp dụng cho multimodal data.
30. Capability từ 603 kiểm soát camera/microphone/file/network.
31. Resource từ 606 kiểm soát VRAM/RAM/CPU.
32. Evaluation từ 646 kiểm tra chất lượng.
33. Model lifecycle từ 647 quản lý artifact.
34. Agent từ 644 tiêu thụ multimodal context.
35. Search từ 641 quản lý multimodal retrieval.
36. Knowledge graph từ 645 lưu semantic relationships.
37. Simulation từ 648 tạo synthetic multimodal data.
38. Không có universal multimodal quality score.
39. No mandatory hidden global context.
40. Struct-only public API.

---

# 4. Core types

```text
Modality
ModalityKind

MultimodalValue
MultimodalSample
MultimodalBatch

TextInput
ImageInput
AudioInput
SpeechInput
VideoInput
SensorInput
GraphInput
StructuredInput

TextRepresentation
ImageRepresentation
AudioRepresentation
SpeechRepresentation
VideoRepresentation
SensorRepresentation
GraphRepresentation

Token
TokenSequence
ModalityToken

Embedding
EmbeddingSpace
EmbeddingProjection

Encoder
Decoder
Projector
FusionModule
AlignmentModule

MultimodalGraph
MultimodalNode
MultimodalEdge

MultimodalContext
ContextItem
ContextBudget

GenerationRequest
GenerationResponse
GenerationStream

MediaCondition
GenerationCondition

MultimodalModel
MultimodalModelVersion
```

---

# 5. ModalityKind

```text
Text
Image
Audio
Speech
Video
Sensor
Graph
Structured
Embedding
Latent
```

---

# 6. Text representation

649 sử dụng 617 làm canonical text representation.

Không tạo một string runtime thứ hai.

---

# 7. Image representation

```text
ImageTensor {
    width
    height
    channels
    dtype
    color_space
    layout
}
```

---

# 8. Audio representation

```text
AudioTensor {
    samples
    channels
    sample_rate
    dtype
    layout
}
```

---

# 9. Speech representation

Speech bổ sung:

```text
language
speaker
timestamps
phonetic_metadata
transcript
```

nếu dữ liệu có.

---

# 10. Video representation

```text
VideoTensor {
    frames
    width
    height
    fps
    pixel_format
    color_space
}
```

---

# 11. Temporal metadata

Mọi temporal modality có:

```text
start_time
duration
timebase
```

---

# 12. Timestamp

Timestamp dùng integer ticks/timescale khi có thể.

---

# 13. Multimodal sample

```text
MultimodalSample {
    items[]
    sample_id
    source_revision
    timestamp
}
```

---

# 14. Multimodal item

Mỗi item:

```text
modality
payload
metadata
provenance
```

---

# 15. Unified representation

Axiom hỗ trợ:

```text
Raw Modality
    ↓
Preprocessor
    ↓
Feature Representation
    ↓
Embedding / Tokens
    ↓
Unified Context
```

---

# 16. Representation levels

```text
Raw
Feature
Token
Embedding
Latent
Semantic
```

---

# 17. No forced universal token format

Axiom không ép image/audio phải biến thành text token.

Model có thể sử dụng:

- continuous features;
- discrete tokens;
- latent vectors;
- patches;
- frames;
- learned representations.

---

# 18. Token

```text
Token {
    id
    modality
    position
    timestamp
}
```

---

# 19. Continuous feature

```text
FeatureTensor
```

là tensor 643.

---

# 20. Embedding

```text
Embedding {
    values
    dimension
    dtype
    space_id
    model_id
    model_version
}
```

---

# 21. Embedding space

```text
EmbeddingSpace {
    space_id
    dimension
    metric
    model_fingerprint
}
```

---

# 22. Embedding compatibility

Hai embedding chỉ được trực tiếp so sánh nếu:

```text
space_id
dimension
metric
```

tương thích.

---

# 23. Cross-modal embedding

Ví dụ:

```text
Text → Space X
Image → Space X
Audio → Space X
```

cho phép semantic retrieval chung.

---

# 24. Projection

Nếu modality nằm ở space khác:

```text
Projection<A,B>
```

phải explicit.

---

# 25. Projection version

Projection có model/version riêng.

---

# 26. Alignment

Alignment mô tả quan hệ giữa:

```text
text ↔ image
text ↔ audio
text ↔ video
image ↔ audio
speech ↔ text
```

---

# 27. Alignment types

```text
Exact
Temporal
Spatial
Semantic
Weak
Approximate
```

---

# 28. Temporal alignment

Ví dụ:

```text
video frame 120
↔
speech segment 3.2s–3.7s
```

---

# 29. Spatial alignment

Image regions có thể liên kết với:

- objects;
- text;
- bounding boxes;
- masks.

---

# 30. Semantic alignment

Một concept có thể liên kết nhiều modalities.

---

# 31. Multimodal graph

```text
ImageRegion
   ↕
Object
   ↕
TextSpan
   ↕
AudioSegment
   ↕
VideoSegment
```

---

# 32. MultimodalNode

```text
MultimodalNode {
    id
    modality
    span
    embedding
    provenance
}
```

---

# 33. MultimodalEdge

```text
Temporal
Spatial
Semantic
Correspondence
DerivedFrom
Describes
Contains
```

---

# 34. Preprocessing

Preprocessor là first-class component.

```text
Preprocessor<TInput,TOutput>
```

---

# 35. Preprocessing examples

Text:

- normalization;
- segmentation;
- tokenizer.

Image:

- resize;
- crop;
- normalize;
- color conversion.

Audio:

- resampling;
- normalization;
- spectrogram.

Video:

- frame sampling;
- resizing;
- temporal sampling.

---

# 36. Preprocessing determinism

Preprocessor có determinism metadata.

---

# 37. Preprocessing fingerprint

Output ghi:

```text
preprocessor_id
version
configuration_hash
```

---

# 38. Tokenizer

Tokenizer thuộc model pipeline.

---

# 39. Tokenizer types

```text
BPE
Unigram
WordPiece
Character
Byte
Patch
DiscreteAudio
Learned
Custom
```

---

# 40. Multimodal tokenizer

Có thể map:

```text
text token
image patch token
audio token
video token
```

vào cùng sequence.

---

# 41. Token namespace

Token IDs phải có vocabulary/model identity.

Không được giả định token ID toàn cục.

---

# 42. Special modality markers

Model có thể khai báo:

```text
<text>
<image>
<audio>
<video>
<sensor>
```

nhưng đây là model-level convention.

---

# 43. Position encoding

Các loại:

```text
Absolute
Relative
Rotary
Temporal
Spatial
Factorized
Learned
```

---

# 44. Multidimensional positions

Video có thể cần:

```text
time
height
width
```

---

# 45. Audio positions

Có thể dùng:

```text
time
frequency
channel
```

---

# 46. Fusion

Fusion layer:

```text
FusionModule
```

---

# 47. Fusion strategies

```text
EarlyFusion
LateFusion
CrossAttention
Concatenation
Addition
GatedFusion
MixtureOfExperts
HierarchicalFusion
GraphFusion
```

---

# 48. Early fusion

Raw/feature-level combination.

---

# 49. Late fusion

Separate encoders → separate predictions → combine.

---

# 50. Cross-attention

Một modality query modality khác.

---

# 51. Gated fusion

Model học trọng số modality.

---

# 52. Missing modality

Multimodal model phải khai báo:

```text
Required
Optional
Substitutable
```

---

# 53. Missing modality behavior

```text
Error
Mask
Fallback
Impute
Degraded
```

---

# 54. No silent imputation

Nếu model tự impute phải metadata rõ.

---

# 55. Multimodal context

```text
MultimodalContext {
    items[]
    token_budget
    tensor_budget
    time_budget
}
```

---

# 56. Context item

```text
ContextItem {
    modality
    source
    representation
    provenance
    priority
}
```

---

# 57. Context budget

Có thể giới hạn:

- tokens;
- bytes;
- tensors;
- pixels;
- audio seconds;
- video frames;
- compute.

---

# 58. Context selection

Có thể dùng:

- recency;
- relevance;
- explicit priority;
- modality budget.

---

# 59. Retrieval

641 có thể retrieve:

```text
text
image
audio
video
multimodal
```

---

# 60. Multimodal RAG

```text
Query
 ↓
Multimodal Embedding
 ↓
641 Retrieval
 ↓
Evidence
 ↓
Multimodal Context
 ↓
643 Model
 ↓
Response
```

---

# 61. Evidence

Evidence giữ:

```text
source_id
revision
span
modality
retrieval_score
```

---

# 62. Evidence provenance

Không được mất provenance khi chuyển thành embedding.

---

# 63. Knowledge graph integration

645 có thể map:

```text
Image
→ Entity
→ Relation
→ Text
→ Audio
```

---

# 64. Multimodal entity

Một entity có thể có:

```text
text description
image
audio
video
embedding
```

---

# 65. Cross-modal entity retrieval

Ví dụ:

```text
text query → image
image query → text
audio query → video
```

---

# 66. Retrieval compatibility

641 owns index semantics.

649 owns representation.

---

# 67. Speech

649 integrates 616 + 617 + 643.

---

# 68. Speech pipeline

```text
Audio
 ↓
Voice Activity
 ↓
Acoustic Features
 ↓
Speech Encoder
 ↓
Speech Representation
 ↓
Text / Semantic Representation
```

---

# 69. Speech-to-text

Model provider boundary.

---

# 70. Text-to-speech

Model provider boundary.

---

# 71. Speech-to-speech

Có thể:

```text
Speech
→ semantic representation
→ target speech
```

---

# 72. Speaker representation

Có thể chứa:

```text
speaker_id
speaker_embedding
speaker_revision
```

---

# 73. Speaker privacy

Speaker embedding được governance như sensitive derived data khi policy yêu cầu.

---

# 74. Voice conversion

Provider boundary.

---

# 75. Prosody

Speech representation có thể chứa:

```text
pitch
energy
duration
prosody_embedding
```

---

# 76. Audio understanding

Audio model có thể xử lý:

- speech;
- music;
- environmental sound;
- events.

---

# 77. Audio event

```text
AudioEvent {
    start
    end
    label
    confidence
}
```

---

# 78. Vision

Image model có thể xử lý:

- classification;
- detection;
- segmentation;
- depth;
- OCR;
- captioning;
- visual question answering.

---

# 79. Region

```text
ImageRegion {
    box
    polygon
    mask
    embedding
}
```

---

# 80. OCR

617 text + 643 model.

---

# 81. OCR provenance

Text extracted from image được đánh dấu:

```text
source_modality = Image
```

---

# 82. Visual grounding

Text span ↔ image region.

---

# 83. Video

Video pipeline:

```text
Video
 ↓
Frame Sampling
 ↓
Temporal Encoder
 ↓
Spatial Encoder
 ↓
Video Representation
```

---

# 84. Temporal sampling

Policies:

```text
Uniform
Keyframe
EventBased
Adaptive
FixedRate
```

---

# 85. Frame budget

Context có max frames.

---

# 86. Long video

Không bắt buộc load toàn bộ video vào RAM.

---

# 87. Streaming video

616 cung cấp media stream.

649 xử lý chunks.

---

# 88. Audio streaming

Chunked processing.

---

# 89. Streaming inference

```text
InputChunk
→ EncoderState
→ OutputChunk
```

---

# 90. Stateful encoder

State có generation/version.

---

# 91. Streaming reset

Explicit.

---

# 92. Backpressure

Streaming pipeline tích hợp 607/606.

---

# 93. Multimodal streaming

Ví dụ:

```text
camera frame
+
microphone chunk
+
text event
```

được aligned theo simulation/media clock.

---

# 94. Cross-modal clock

Sử dụng 616 media timeline hoặc simulation timeline.

---

# 95. Clock distinction

Không trộn:

```text
wall clock
media clock
simulation clock
```

---

# 96. Multimodal generation

Model có thể generate:

```text
Text
Image
Audio
Speech
Video
Structured
```

---

# 97. GenerationRequest

```text
GenerationRequest {
    model
    inputs
    conditions
    output_modality
    constraints
    seed
    budget
}
```

---

# 98. GenerationResponse

```text
GenerationResponse {
    outputs[]
    model_version
    seed
    provenance
    usage
}
```

---

# 99. GenerationStream

Streaming outputs.

---

# 100. Seed

Generative models có optional explicit seed.

---

# 101. Sampling

```text
Greedy
Temperature
TopK
TopP
Typical
Beam
Custom
```

Provider-specific.

---

# 102. Sampling metadata

Output records sampling parameters.

---

# 103. Generation constraints

Có thể giới hạn:

- schema;
- output size;
- token count;
- duration;
- resolution;
- sampling rate.

---

# 104. Structured generation

Model có thể output 612-compatible schema.

---

# 105. JSON is not canonical

Axiom uses typed schema rather than string JSON as semantic foundation.

---

# 106. Image generation

649 defines representation and pipeline.

Actual kernels/model execution remain 643/provider.

---

# 107. Audio generation

616 handles media output representation.

643/649 handles model execution.

---

# 108. Video generation

Frame generation + media assembly.

---

# 109. Multimodal conditioning

Generation can accept:

```text
text
image
audio
video
reference embedding
structured control
```

---

# 110. Condition identity

Every condition has provenance.

---

# 111. Reference image

```text
ImageCondition
```

can be bound to a specific image revision.

---

# 112. Region condition

Generation can target specific spatial region.

---

# 113. Temporal condition

Video/audio generation can bind to temporal segment.

---

# 114. Negative condition

Model provider may support explicit negative conditioning.

---

# 115. Provider capability

Not all models support all conditions.

Capability discovery is required.

---

# 116. Model capability descriptor

```text
ModelCapabilities {
    input_modalities[]
    output_modalities[]
    max_context
    max_resolution
    max_duration
    streaming
    batching
}
```

---

# 117. Model compatibility

Request is validated before execution.

---

# 118. Model loading

647 manages model artifact lifecycle.

---

# 119. Model execution

643 executes tensor/model graph.

---

# 120. Multimodal model

```text
MultimodalModel {
    encoders[]
    decoders[]
    projectors[]
    fusion
    tokenizer
    generation_policy
}
```

---

# 121. Model graph

Can be represented using 643 ComputeGraph.

---

# 122. Graph compilation

643 optimizes:

- fusion;
- memory;
- kernel selection;
- device placement.

---

# 123. Modality pipeline graph

649 adds semantic modality graph around 643 tensor graph.

---

# 124. Device placement

Components can execute on:

```text
CPU
GPU
NPU
DSP
ExternalProvider
```

---

# 125. Placement

606/614/630 govern resources and placement.

---

# 126. CPU fallback

Optional provider can execute without GPU.

---

# 127. Quantization

643 quantization applies to multimodal models.

---

# 128. Image quantization

Provider-specific.

---

# 129. Audio quantization

Provider-specific.

---

# 130. Mixed precision

Each tensor carries dtype.

---

# 131. Precision metadata

Outputs can record:

```text
dtype
accumulation_dtype
quantization
```

---

# 132. Batch

```text
MultimodalBatch
```

supports padded/ragged inputs.

---

# 133. Ragged modality

Examples:

- different image sizes;
- different audio lengths;
- different frame counts.

---

# 134. Padding

Padding semantics explicit.

---

# 135. Mask

Masks identify valid elements.

---

# 136. Packed representation

Optional for efficient inference.

---

# 137. Dynamic shapes

643 supports dynamic shapes.

649 declares modality constraints.

---

# 138. Memory

Large images/video/audio use streaming/chunking.

---

# 139. Zero-copy

When representations are compatible, 614/616 buffers may be reused.

---

# 140. GPU zero-copy

Use shared/device memory where supported.

---

# 141. CPU/GPU synchronization

608/614 primitives.

---

# 142. Async preprocessing

607.

---

# 143. Async inference

643.

---

# 144. Async generation

649 stream API.

---

# 145. Cancellation

Cancellation propagates through:

```text
preprocessing
encoder
fusion
decoder
media output
```

---

# 146. Timeout

Generation timeout is resource policy, not model semantics.

---

# 147. Model warmup

647/643.

---

# 148. Multimodal cache

Cache keys include:

```text
model_version
preprocessor_version
input_revision
configuration_hash
```

---

# 149. Embedding cache

641-compatible.

---

# 150. Feature cache

643/642.

---

# 151. Media cache

616.

---

# 152. Context cache

649 can cache encoded representations.

---

# 153. KV cache

Transformer providers can expose KV cache.

---

# 154. KV cache identity

Bound to:

```text
model
context
generation
```

---

# 155. KV cache security

Cannot cross tenants unless explicitly allowed.

---

# 156. Model batching

Dynamic batching optional.

---

# 157. Batch scheduler

607/643.

---

# 158. Multimodal batching

Batch compatible modalities together.

---

# 159. Heterogeneous batch

Can batch multiple input shapes using masks/packing.

---

# 160. Scheduling policy

Interactive vs batch workloads can use different resource policies.

---

# 161. Streaming priority

Interactive streams may receive bounded priority.

---

# 162. Admission control

639 controls expensive multimodal requests.

---

# 163. Resource limits

606:

```text
max_pixels
max_audio_seconds
max_video_frames
max_tokens
max_memory
max_compute
```

---

# 164. Security capabilities

603:

```text
ReadCamera
ReadMicrophone
ReadMedia
GenerateMedia
AccessModel
AccessEmbedding
ExportMedia
```

---

# 165. Camera

649 cannot directly open camera.

614 owns device capability.

---

# 166. Microphone

616/614 own device access.

---

# 167. File input

611 owns file capability.

---

# 168. Network media

609/626 own network access.

---

# 169. External model provider

Provider receives only approved data.

---

# 170. External API privacy

Sensitive data export must pass policy.

---

# 171. Model provider isolation

Provider cannot grant itself capability.

---

# 172. Model output trust

Generated output is untrusted data.

---

# 173. Generated code

If output is code, it remains data until separately validated/compiled.

---

# 174. Generated commands

Cannot directly execute without 603/639 authorization.

---

# 175. Multimodal prompt injection

Image/audio/video may contain adversarial instructions.

Model runtime must treat content as data.

---

# 176. Agent boundary

644 decides whether content is trusted instruction.

---

# 177. Tool boundary

Multimodal model cannot invoke tools implicitly.

---

# 178. Evidence

Extracted claims can be linked to source regions.

---

# 179. Citation span

```text
image region
audio timestamp
video interval
text span
```

---

# 180. Grounding

Multimodal response may reference evidence.

---

# 181. Evaluation

646 evaluates:

- OCR;
- caption;
- grounding;
- speech recognition;
- image understanding;
- video understanding;
- cross-modal retrieval;
- generation;
- alignment.

---

# 182. Simulation

648 can generate multimodal synthetic datasets.

---

# 183. Knowledge graph

645 stores multimodal entity relationships.

---

# 184. Search

641 stores multimodal embeddings.

---

# 185. Analytics

642 analyzes multimodal metadata.

---

# 186. Dataset

640 governs source and derived data.

---

# 187. Lineage

Each representation transformation has lineage:

```text
raw
→ preprocessed
→ encoded
→ embedded
→ generated
```

---

# 188. Transformation identity

```text
TransformId
TransformVersion
ConfigurationFingerprint
```

---

# 189. Derived data

Embeddings and latents are derived assets.

---

# 190. Retention

Derived representations may need deletion when source is deleted according to 640 policy.

---

# 191. Residency

Model inference may be constrained to permitted region.

---

# 192. Privacy

Multimodal data may include biometric/sensitive information.

Governance metadata must remain attached.

---

# 193. Secret handling

Secrets are never included in multimodal context by default.

---

# 194. Redaction

649 can request governance-controlled redaction before inference/export.

---

# 195. Watermark metadata

Generated media may optionally carry provenance metadata.

---

# 196. Authenticity metadata

Model output can record:

```text
generated
model
version
timestamp
```

---

# 197. Content provenance

C2PA-like external interoperability may be supported as provider boundary.

---

# 198. No authenticity guarantee

Metadata alone does not prove physical origin.

---

# 199. Model fingerprint

Every generated artifact references model fingerprint.

---

# 200. Preprocessor fingerprint

Also recorded.

---

# 201. Prompt/condition fingerprint

Inputs can be hashed while sensitive raw values remain protected.

---

# 202. Reproducibility manifest

```text
model
preprocessors
tokenizer
inputs
conditions
seed
sampling
hardware
provider
compiler
```

---

# 203. Determinism

Model provider declares:

```text
BitExact
NumericallyDeterministic
SeedDeterministic
BestEffort
NonDeterministic
```

---

# 204. Multimodal alignment evaluation

646 compares temporal/spatial/semantic alignment.

---

# 205. Cross-modal retrieval evaluation

Metrics include:

```text
Recall@K
Precision@K
MRR
nDCG
CrossModalRecall
```

---

# 206. Generation evaluation

Possible metrics:

- exact schema validity;
- semantic similarity;
- perceptual similarity;
- audio quality;
- temporal consistency;
- grounding.

---

# 207. No universal quality score

Every metric must identify:

```text
task
dataset
metric
version
```

---

# 208. Multimodal benchmark

```text
Benchmark {
    modalities
    dataset_revision
    model_revision
    evaluator_revision
}
```

---

# 209. Agent benchmark

644 + 646 + 649 can test multimodal agent trajectories.

---

# 210. Visual agent

```text
Image
→ Agent
→ Action
```

---

# 211. Audio agent

```text
Audio
→ Agent
→ Action
```

---

# 212. Video agent

```text
Video
→ Agent
→ Action
```

---

# 213. Multimodal agent

```text
Image + Audio + Text
→ Agent
→ Tool
→ Environment
```

---

# 214. Simulation integration

648 provides environment observations.

---

# 215. Robotics boundary

649 may provide perception.

614 owns actual device I/O.

648 owns simulation.

---

# 216. Sensor fusion

```text
Camera
+
LiDAR
+
IMU
+
GPS
→
Unified Representation
```

---

# 217. Sensor fusion strategy

```text
Early
Feature
Late
KalmanProvider
Learned
Graph
```

---

# 218. External sensor fusion

Provider boundary.

---

# 219. Temporal fusion

Observations can be aligned over sliding windows.

---

# 220. Missing sensor

Sensor availability metadata is explicit.

---

# 221. Sensor uncertainty

Optional covariance/uncertainty metadata.

---

# 222. Uncertainty propagation

Providers may propagate uncertainty through representation graph.

---

# 223. No universal uncertainty semantics

Each provider declares semantics.

---

# 224. Multimodal memory

644 memory can store:

```text
text
image reference
audio reference
video reference
embedding
knowledge entity
```

---

# 225. Memory payload policy

Large media normally stored by reference, not duplicated into agent memory.

---

# 226. Media reference

```text
MediaRef {
    asset_id
    revision
    span
}
```

---

# 227. Context reconstruction

Agent context resolves references under current authorization.

---

# 228. Authorization-aware retrieval

641 checks policy before returning media.

---

# 229. Multimodal RAG context

Context contains:

```text
Evidence
MediaRef
Text
Embedding
GraphFact
```

---

# 230. Context ordering

Ordering is explicit.

---

# 231. Context truncation

Must preserve evidence boundaries where possible.

---

# 232. Truncation metadata

Dropped items are recorded in diagnostic mode.

---

# 233. Token budget

643 provides model token constraints.

---

# 234. Pixel budget

649 adds pixel limits.

---

# 235. Audio budget

Duration/sample budget.

---

# 236. Video budget

Frame/duration budget.

---

# 237. Graph budget

645 query budget.

---

# 238. Unified budget

```text
MultimodalBudget {
    tokens
    bytes
    pixels
    frames
    audio_seconds
    graph_nodes
    compute
}
```

---

# 239. Budget enforcement

606 remains authoritative.

---

# 240. Multimodal scheduler

Requests can be split into:

```text
preprocess
encode
fuse
decode
postprocess
```

---

# 241. Pipeline parallelism

643/607.

---

# 242. Device pipeline

```text
CPU preprocess
→ GPU encode
→ GPU fusion
→ CPU postprocess
```

---

# 243. Memory transfer

614 manages device memory.

---

# 244. Pinned buffers

616/614.

---

# 245. Zero-copy media tensor

If media buffer layout matches model tensor requirements.

---

# 246. Format conversion

Explicit transformation.

---

# 247. Color conversion

617/615/616 boundaries.

---

# 248. Audio resampling

616.

---

# 249. Video decode

616.

---

# 250. Image decode

616/media provider or 615 provider.

---

# 251. Text decode

617.

---

# 252. Speech segmentation

Provider boundary.

---

# 253. OCR segmentation

Provider boundary.

---

# 254. Multimodal preprocessing graph

```text
Input
→ Decode
→ Normalize
→ FeatureExtract
→ Align
→ Encode
```

---

# 255. Preprocessing graph fingerprint

Used for caching/reproducibility.

---

# 256. Compile preprocessing graph

643 may fuse tensor operations.

---

# 257. Runtime graph

```text
MediaGraph
+
TensorGraph
```

---

# 258. Graph execution

No hidden interpreter required for compiled production paths.

---

# 259. Kernel provider

Native CPU/GPU kernels.

---

# 260. External kernel provider

Optional CUDA/ROCm/Metal/Vulkan/etc.

---

# 261. Hardware acceleration

Capability discovery.

---

# 262. Unsupported modality

Returns explicit `UnsupportedModality`.

---

# 263. Unsupported shape

Returns explicit `ShapeMismatch`.

---

# 264. Unsupported model

`ModelCapabilityMismatch`.

---

# 265. Context overflow

`ContextBudgetExceeded`.

---

# 266. Media overflow

`MediaBudgetExceeded`.

---

# 267. Model load error

`ModelLoadFailure`.

---

# 268. Provider error

`ProviderFailure`.

---

# 269. Generation cancellation

`GenerationCancelled`.

---

# 270. Security denial

`CapabilityDenied`.

---

# 271. Governance denial

`GovernanceViolation`.

---

# 272. Policy denial

`PolicyDenied`.

---

# 273. Diagnostics

633/602 records:

```text
modality
model
preprocessor
latency
device
memory
tokens
frames
audio_duration
```

---

# 274. Metrics

```text
encode_latency
fusion_latency
decode_latency
queue_latency
GPU_time
CPU_time
memory_peak
throughput
```

---

# 275. Streaming metrics

```text
time_to_first_output
chunk_latency
buffer_depth
dropped_chunks
```

---

# 276. Model usage

647 records model artifact usage.

---

# 277. Experiment

643/646 experiment metadata.

---

# 278. A/B infrastructure

637 can control variant assignment.

Evaluation remains 646.

---

# 279. Feature flags

637 can select model/provider.

---

# 280. Security boundary

Feature flags cannot grant camera/microphone capability.

---

# 281. Model routing

647/631 can route requests to compatible model versions.

---

# 282. Multimodal model routing

Routing criteria:

```text modality
resolution
language
latency
device
policy
```

---

# 283. Fallback

Fallback model must be capability-compatible.

---

# 284. Fallback provenance

Response records which model actually executed.

---

# 285. Model ensemble

Multiple models can produce representations/results.

---

# 286. Ensemble strategies

```text Average
Vote
Weighted
Cascade
Router
MixtureOfExperts
```

---

# 287. Ensemble weights

Explicit configuration.

---

# 288. No hidden ensemble

Model manifest must identify components.

---

# 289. Cascaded inference

Example:

```text
cheap model
→ confidence check
→ expensive model
```

---

# 290. Confidence

Provider-defined semantics.

---

# 291. Confidence cannot grant authority

Security remains 603/639.

---

# 292. Multimodal moderation

646 evaluation/safety providers may inspect outputs.

---

# 293. Moderation provider

External safety model can be adapter.

---

# 294. Safety pipeline

```text
Input
→ Policy
→ Model
→ Output
→ Safety Evaluation
→ Delivery
```

---

# 295. Policy

639 can require safety evaluator before external delivery.

---

# 296. No automatic safety guarantee

Evaluation evidence is versioned.

---

# 297. Output transformation

Can:

- redact;
- resize;
- transcode;
- filter metadata.

---

# 298. Output storage

611/613.

---

# 299. Output distribution

625/631/632.

---

# 300. Generated media package

613 can package generated assets.

---

# 301. Asset identity

Generated asset:

```text
AssetId
AssetRevision
ContentHash
```

---

# 302. Content addressing

613.

---

# 303. Deduplication

CAS can deduplicate identical generated assets.

---

# 304. Large artifact streaming

No full-memory requirement.

---

# 305. Video generation streaming

Output chunks can be written directly to 611.

---

# 306. Audio generation streaming

Same.

---

# 307. Image generation

May be tile/chunk based.

---

# 308. Latent artifact

Intermediate latents are optional artifacts.

---

# 309. Latent privacy

Latents may encode sensitive information and are governed as derived data.

---

# 310. Model inversion risk

646 can evaluate leakage.

---

# 311. Membership leakage

646 privacy tests.

---

# 312. Prompt leakage

649 must not expose protected context merely because model generated output.

---

# 313. Context isolation

Per-request context boundary.

---

# 314. Tenant isolation

Model KV/cache/context cannot cross tenants.

---

# 315. Batch isolation

Dynamic batching must preserve request boundaries.

---

# 316. Padding isolation

Padded values cannot become visible across requests.

---

# 317. Cache isolation

Cache keys include authorization-relevant identity when required.

---

# 318. External provider isolation

Provider requests are separately scoped.

---

# 319. Audit

Sensitive multimodal access is auditable.

---

# 320. Retention

Prompt/media retention configurable through 640.

---

# 321. Delete

Deleting source can invalidate:

- embeddings;
- cached representations;
- generated derivatives;

according to governance policy.

---

# 322. Derived dependency graph

640 lineage tracks:

```text
Source
 ↓
Preprocess
 ↓
Embedding
 ↓
Index
 ↓
Context
 ↓
Generation
```

---

# 323. Knowledge graph lineage

645 may store semantic provenance.

---

# 324. Search index invalidation

641 uses source revision.

---

# 325. Analytics invalidation

642 uses dataset revision.

---

# 326. Model cache invalidation

647 model revision.

---

# 327. Context cache invalidation

Input revision + model revision + preprocessor revision.

---

# 328. Compiler annotations

```text
@multimodal
@modality
@encoder
@decoder
@projector
@fusion
@alignment
@embedding
@tokenizer
@preprocess
@vision
@audio
@speech
@video
@cross_modal
@generation
@condition
@context
@streaming
@grounding
@media_model
```

---

# 329. Generated metadata

```text
.axmulti
.axmodality
.axencoder
.axdecoder
.axfusion
.axalignment
.axembedding
.axmultimodel
.axgeneration
.axcontext
```

---

# 330. CLI

```text
axiom multimodal inspect
axiom multimodal model
axiom multimodal capabilities
axiom multimodal encode
axiom multimodal embed
axiom multimodal align
axiom multimodal retrieve
axiom multimodal generate
axiom multimodal stream
axiom multimodal trace
axiom multimodal provenance
axiom multimodal benchmark
```

---

# 331. Provider architecture

```text
NativeMultimodalProvider
NativeVisionProvider
NativeAudioProvider
NativeSpeechProvider
NativeVideoProvider

HardwareMultimodalProvider
PlatformMultimodalProvider
ExternalModelProvider
RemoteModelProvider
TestMultimodalProvider
```

---

# 332. External interoperability

Optional adapters:

- ONNX;
- SafeTensors;
- GGUF;
- OpenAI-compatible APIs;
- generic HTTP model APIs;
- TensorRT-like providers;
- CUDA/ROCm;
- WebGPU.

Không provider nào là core dependency.

---

# 333. Model import

Import phải validate:

- schema;
- tensor shapes;
- dtype;
- operators;
- model fingerprint;
- security.

---

# 334. Custom operator

Requires explicit provider/capability.

---

# 335. Unsafe model

Model có unsupported/custom operations không được silently execute.

---

# 336. Model sandbox

Untrusted external model execution có thể chạy out-of-process.

---

# 337. Model package trust

647/638.

---

# 338. Signature

Model package can be signed.

---

# 339. Model artifact hash

Mandatory for reproducible model identity.

---

# 340. Versioning

Model version is immutable.

---

# 341. Tokenizer compatibility

Tokenizer mismatch must fail unless explicitly adapted.

---

# 342. Preprocessor compatibility

Mismatch must fail or require explicit migration.

---

# 343. Embedding compatibility

Dimension/space mismatch fails.

---

# 344. Cross-modal projection compatibility

Projection must declare source/target spaces.

---

# 345. Schema evolution

612 handles serialized multimodal schemas.

---

# 346. Media compatibility

616 handles codecs/containers.

---

# 347. UI integration

619 may display:

- multimodal input;
- generated output;
- regions;
- timestamps;
- embeddings;
- evidence.

---

# 348. Document integration

621 may attach multimodal assets to documents.

---

# 349. Navigation

622 can route to media/evidence/model inspection views.

---

# 350. Plugin

623 may add modality provider.

---

# 351. Scripting

624 may automate multimodal pipelines.

---

# 352. Package registry

625 distributes model/preprocessor packages.

---

# 353. Network

626/631/632 expose multimodal inference APIs.

---

# 354. Distributed serving

631 handles service execution.

---

# 355. Gateway

632 handles edge traffic.

---

# 356. Deployment

636 deploys model-serving components.

---

# 357. Cluster

635 places GPU/NPU workloads.

---

# 358. Compute

630 distributes batch inference.

---

# 359. Workflow

629 orchestrates long multimodal processing.

---

# 360. Event bus

634 streams media/model events.

---

# 361. Observability

633 traces end-to-end multimodal inference.

---

# 362. State

600 checkpoints streaming/model pipeline state.

---

# 363. Storage

611 persists media and intermediate artifacts.

---

# 364. Compression

613 compresses datasets/artifacts.

---

# 365. Crypto

610 protects encrypted model/data transport.

---

# 366. Credentials

638 protects external model API credentials.

---

# 367. Policy

639 governs model/provider usage.

---

# 368. Governance

640 governs media/data lifecycle.

---

# 369. Search

641 indexes embeddings.

---

# 370. Analytics

642 analyzes inference datasets.

---

# 371. ML

643 executes model.

---

# 372. Agent

644 consumes outputs.

---

# 373. Knowledge

645 provides semantic context.

---

# 374. Evaluation

646 validates outputs.

---

# 375. Simulation

648 generates controlled inputs.

---

# 376. Model lifecycle

647 owns model promotion.

---

# 377. End-to-end multimodal AI loop

```text
        ┌──────────────┐
        │ 616 / 617    │
        │ Media / Text │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │     649      │
        │ Preprocess   │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ 643 Tensor   │
        │ Model Engine │
        └──────┬───────┘
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
     641      645      644
   Search   Knowledge  Agent
       │       │        │
       └───────┼────────┘
               ▼
        Multimodal Context
               │
               ▼
           Generation
               │
        ┌──────┼──────┐
        ▼      ▼      ▼
      Text   Audio   Image/Video
        │      │      │
        └──────┼──────┘
               ▼
             646
           Evaluation
               │
               ▼
             647
       Model Lifecycle
```

---

# 378. Core invariants

1. Modality type is explicit.
2. Representation type is explicit.
3. Embedding space is explicit.
4. Embedding dimension is explicit.
5. Model version is explicit.
6. Preprocessor version is explicit.
7. Tokenizer version is explicit.
8. Media timestamps are preserved.
9. Color metadata is preserved.
10. Audio sample rate is preserved.
11. Video frame timing is preserved.
12. Cross-modal alignment is explicit.
13. Missing modality is explicit.
14. Imputation is explicit.
15. Fusion strategy is explicit.
16. Context budget is enforced.
17. Resource budget is enforced.
18. Streaming is bounded.
19. Cancellation propagates.
20. Model artifacts are immutable.
21. Model hashes are recorded.
22. Provider capabilities are checked.
23. Unsupported operations fail explicitly.
24. External provider cannot expand authority.
25. Camera access requires capability.
26. Microphone access requires capability.
27. Network model access requires capability.
28. Model output cannot grant capability.
29. Generated code is untrusted.
30. Generated commands are untrusted.
31. Prompt injection is treated as untrusted content.
32. Tenant context is isolated.
33. Batch requests remain isolated.
34. Cache boundaries preserve authorization.
35. Sensitive media is governed.
36. Derived embeddings preserve lineage.
37. Generated media preserves provenance.
38. Source deletion follows governance rules.
39. Residency applies to derived representations.
40. Model routing is explicit.
41. Fallback is explicit.
42. Ensemble composition is explicit.
43. Determinism level is declared.
44. Seed is recorded when used.
45. Sampling parameters are recorded.
46. Reproducibility manifest is available.
47. No universal quality score exists in core.
48. Evaluation belongs to 646.
49. Model lifecycle belongs to 647.
50. Simulation belongs to 648.
51. Media I/O belongs to 616.
52. Text semantics belong to 617.
53. Tensor execution belongs to 643.
54. Agent authority belongs to 644.
55. Search authority belongs to 641.
56. Knowledge authority belongs to 645.
57. Security belongs to 603.
58. Policy belongs to 639.
59. Governance belongs to 640.
60. Resource control belongs to 606.
61. Scheduling belongs to 607.
62. No mandatory Python runtime.
63. No mandatory ML framework.
64. No mandatory external model provider.
65. No mandatory external vector database.
66. No raw pointer public API.
67. No mandatory GC.
68. Struct-only API.
69. Untrusted model loading is isolated.
70. Custom operators require explicit trust.
71. Intermediate representations are versioned.
72. Streaming state is generation-safe.
73. KV cache is request-scoped.
74. Cross-request state leakage is prohibited.
75. Large media need not reside fully in memory.
76. Zero-copy is optional and validated.
77. Device synchronization is explicit.
78. Provider nondeterminism is declared.
79. Partial multimodal results are marked.
80. Provenance survives transformation.

---

# 379. Acceptance target

**≥600 acceptance criteria**, covering:

- modality types;
- raw representations;
- tensors;
- text;
- image;
- audio;
- speech;
- video;
- sensor;
- graph;
- structured data;
- preprocessing;
- tokenization;
- multimodal tokens;
- embeddings;
- embedding spaces;
- projections;
- alignment;
- fusion;
- missing modalities;
- multimodal context;
- context budgeting;
- multimodal RAG;
- vision;
- OCR;
- speech;
- audio;
- video;
- multimodal streaming;
- generation;
- structured generation;
- image generation;
- audio generation;
- video generation;
- cross-modal generation;
- model loading;
- model routing;
- batching;
- dynamic batching;
- device placement;
- GPU;
- NPU;
- quantization;
- mixed precision;
- caching;
- KV cache;
- security;
- privacy;
- provenance;
- governance;
- lineage;
- retrieval;
- knowledge graph;
- agent;
- evaluation;
- simulation;
- digital twin;
- deployment;
- distributed inference;
- model serving;
- external providers;
- ABI;
- FFI;
- plugin;
- package;
- diagnostics;
- telemetry;
- testing;
- fuzzing;
- determinism;
- reproducibility;
- performance;
- scalability.

---

# 380. Profiles

```text
AXMULTI_NONE

AXMULTI_CORE
AXMULTI_TEXT
AXMULTI_VISION
AXMULTI_AUDIO
AXMULTI_SPEECH
AXMULTI_VIDEO
AXMULTI_SENSOR

AXMULTI_EMBEDDING
AXMULTI_ALIGNMENT
AXMULTI_FUSION
AXMULTI_RAG

AXMULTI_GENERATION
AXMULTI_STREAMING
AXMULTI_AGENT

AXMULTI_MULTIMODEL
AXMULTI_DISTRIBUTED
AXMULTI_SERVE

AXMULTI_FULL
```

---

# 381. Minimal profile

```text
AXMULTI_CORE
```

chỉ yêu cầu:

```text
Modality
MultimodalValue
MultimodalSample
Representation
Embedding
Context
```

---

# 382. Edge profile

```text
AXMULTI_CORE
+
AXMULTI_EMBEDDING
+
AXMULTI_VISION
+
AXMULTI_AUDIO
```

có thể chạy trên CPU/NPU/GPU nhỏ.

---

# 383. Server profile

```text
AXMULTI_MULTIMODEL
+
AXMULTI_STREAMING
+
AXMULTI_DISTRIBUTED
+
AXMULTI_SERVE
```

---

# 384. Generative media profile

```text
AXMULTI_GENERATION
+
AXMULTI_VIDEO
+
AXMULTI_AUDIO
+
AXMULTI_VISION
```

---

# 385. AI agent profile

```text
AXMULTI_RAG
+
AXMULTI_AGENT
+
AXMULTI_STREAMING
```

---

# 386. Final architecture

```text
                         AXIOM MULTIMODAL AI

 ┌────────────────────────────────────────────────────────────┐
 │                         Applications                        │
 └─────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │       644          │
                    │       Agent        │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │       649          │
                    │   Multimodal       │
                    │   Context/Fusion   │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                    ▼
      ┌────────┐         ┌─────────┐         ┌──────────┐
      │ Vision │         │  Audio  │         │  Text    │
      └────┬───┘         └────┬────┘         └────┬─────┘
           │                  │                   │
           └──────────────────┼───────────────────┘
                              ▼
                    ┌────────────────────┐
                    │       643          │
                    │ Tensor / ML Engine │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼─────────────────┐
             ▼                ▼                 ▼
          ┌──────┐        ┌────────┐        ┌────────┐
          │ 641  │        │  645   │        │  648   │
          │Search│        │Knowledge│       │Simulation│
          └──────┘        └────────┘        └────────┘
                              │
                              ▼
                         ┌──────────┐
                         │   646    │
                         │Evaluation│
                         └────┬─────┘
                              ▼
                         ┌──────────┐
                         │   647    │
                         │ Lifecycle│
                         └──────────┘
```

---

# 387. Kết quả

BOOTSTRAP-649 hoàn thiện **multimodal semantic layer** của Axiom.

Axiom hiện có thể biểu diễn và xử lý thống nhất:

```text
Text
Image
Audio
Speech
Video
Sensor
Graph
Structured Data
Embeddings
Latents
```

đồng thời giữ đúng boundary:

```text
616 = Media
617 = Text
643 = Tensor/ML
649 = Multimodal AI
641 = Retrieval
645 = Knowledge
644 = Agent
646 = Evaluation
647 = Model Lifecycle
648 = Simulation
```

Điều này cho phép xây dựng các pipeline như:

```text
Camera
   +
Microphone
   +
Text
   ↓
Multimodal Encoder
   ↓
Unified Representation
   ↓
Knowledge/Search
   ↓
Agent
   ↓
Tool / Environment
   ↓
Multimodal Generation
```

mà không cần biến Axiom thành wrapper quanh một framework AI bên ngoài.

---

# 388. Trạng thái

**BOOTSTRAP-649 — COMPLETE**

### Task kế tiếp

**BOOTSTRAP-650 — Native AI Memory, Context Engineering, Episodic/Semantic/Procedural Memory, Long-Context Runtime, Retrieval Memory, Forgetting, Consolidation & Persistent Cognitive State 5.0**
:::