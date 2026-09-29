Tiếp tục với **BOOTSTRAP-647 — Native AI Model Registry, Artifact Lineage, Model Lifecycle, Model Packaging, Versioning, Promotion, Serving Catalog & Model Supply-Chain Runtime 5.0**.

:::writing{variant="document" id="58421" title="BOOTSTRAP-647 — Native AI Model Registry, Artifact Lineage, Model Lifecycle, Model Packaging, Versioning, Promotion, Serving Catalog & Model Supply-Chain Runtime 5.0"}
# BOOTSTRAP-647
## Native AI Model Registry, Artifact Lineage, Model Lifecycle, Model Packaging, Versioning, Promotion, Serving Catalog & Model Supply-Chain Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Model Lifecycle & Supply-Chain Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-646

---

# 1. Mục tiêu

BOOTSTRAP-647 xây dựng **model lifecycle infrastructure native của Axiom**.

Nó quản lý toàn bộ vòng đời artifact AI:

```text
Dataset
   ↓
Training
   ↓
Model Artifact
   ↓
Validation
   ↓
Registration
   ↓
Version
   ↓
Promotion
   ↓
Packaging
   ↓
Deployment
   ↓
Serving
   ↓
Monitoring
   ↓
Retirement
```

647 tập trung vào **identity, artifact, lineage, versioning, registry, promotion và lifecycle**.

Nó không thay thế:

- 643 — model execution/training/inference;
- 646 — evaluation;
- 636 — deployment;
- 638 — credentials/trust;
- 639 — policy;
- 625 — package repository/distribution.

---

# 2. Boundary

| Layer | Responsibility |
|---|---|
| 613 | package/CAS |
| 625 | package registry/distribution |
| 636 | deployment orchestration |
| 638 | credential/trust lifecycle |
| 639 | policy |
| 640 | data governance |
| 643 | ML/model execution |
| 646 | evaluation |
| **647** | model identity/lifecycle/supply chain |

Điểm quan trọng:

```text
Model Registry != Package Registry
Model Artifact != Deployment
Model Version != Deployment Revision
Evaluation Result != Promotion
```

---

# 3. Nguyên tắc

1. Model identity immutable.
2. Model version immutable.
3. Artifact hash immutable.
4. Model metadata không chứa secret material.
5. Model artifact không được tự động thực thi code.
6. Model format phải có declared schema.
7. Provider phải được xác định.
8. Target phải được xác định.
9. Architecture phải được xác định.
10. Dtype phải được xác định.
11. Input/output schema phải versioned.
12. Model lineage phải first-class.
13. Dataset lineage phải preserved.
14. Training lineage phải preserved.
15. Evaluation lineage phải preserved.
16. Promotion là state transition có audit.
17. Promotion không đồng nghĩa deployment.
18. Deployment cần 636.
19. Policy cần 639.
20. Trust cần 638.
21. Package storage dùng 613/625.
22. Registry không cần internet.
23. Local registry là valid deployment.
24. Registry có thể distributed.
25. Model artifact có thể lớn.
26. Artifact không nên bị copy không cần thiết.
27. CAS được ưu tiên.
28. Model versions không bị overwrite.
29. Rollback dùng version cũ.
30. Retirement không đồng nghĩa deletion.
31. Deletion phải theo 640.
32. Model metadata phải AI-readable.
33. Registry API phải struct-only.
34. Không bắt buộc MLflow/W&B/Hugging Face.
35. External model registries là provider.
36. Native registry là canonical representation.
37. Registry không cấp capability.
38. Untrusted metadata không được trở thành code.
39. External providers không được mở rộng authority.
40. Model provenance phải survive transformation.

---

# 4. Core objects

```text
ModelRegistry
Model
ModelId
ModelGeneration
ModelVersion
ModelRevision

ModelArtifact
ArtifactId
ArtifactManifest
ArtifactChunk
ArtifactHash

ModelSchema
InputSchema
OutputSchema
ModelSignature

ModelProvider
ModelFormat
ModelTarget
ModelArchitecture

ModelLineage
TrainingRunRef
DatasetRef
EvaluationRef

ModelStage
ModelPromotion
PromotionPolicy
PromotionRecord

ModelRelease
ReleaseId
ReleaseRevision

ServingModel
ServingVersion
ServingProfile
ServingEndpointRef

ModelCompatibility
CompatibilityMatrix

ModelDependency
ModelRuntime
ModelProviderRef

ModelAttestation
ModelIntegrity
ModelTrust

ModelDeprecation
ModelRetirement

ModelAlias
ModelChannel

ModelCatalog
ModelSearchQuery
ModelQueryResult
```

---

# 5. Model identity

Canonical identity:

```text
ModelId
```

Không thay đổi trong toàn bộ vòng đời model.

---

# 6. Model generation

Model bị thay thế về mặt identity chỉ khi đó là model khác.

```text
ModelId + Generation
```

giúp tránh stale reference.

---

# 7. Model version

Mỗi version có:

```text
ModelVersion {
    id
    semantic_version
    artifact_hash
    schema_fingerprint
    build_id
}
```

---

# 8. Immutable version

Sau khi published:

```text
artifact
schema
lineage
integrity
```

không được mutate.

Thay đổi tạo version mới.

---

# 9. Model revision

Metadata mutable có thể được revision:

```text
description
tags
documentation
catalog metadata
```

nhưng không được thay đổi identity của artifact.

---

# 10. Artifact identity

Artifact được xác định bởi cryptographic hash.

```text
ArtifactHash
```

---

# 11. Artifact manifest

Manifest:

```text
ArtifactManifest {
    artifact_id
    hash
    format
    size
    chunks
    compression
    encryption
    target
    architecture
}
```

---

# 12. Chunked artifact

Model lớn được chia:

```text
chunk_0
chunk_1
chunk_2
...
```

---

# 13. Content-addressed storage

647 sử dụng CAS của 613.

```text
Model
 ↓
ArtifactManifest
 ↓
CAS
```

---

# 14. Deduplication

Hai model có chunk giống nhau không cần lưu duplicate.

---

# 15. Partial download

Model có thể tải từng chunk.

---

# 16. Resumable transfer

Transfer state:

```text
missing_chunks
received_chunks
verified_chunks
```

---

# 17. Integrity

Mỗi chunk được verify trước activation.

---

# 18. Merkle integrity

Large models có thể sử dụng Merkle tree.

---

# 19. Model formats

Native:

```text
.axmodel
```

External compatibility:

```text
ONNX
SafeTensors
GGUF
vendor-specific
```

---

# 20. Safe loading

External model format:

```text
parse
→ validate
→ inspect
→ verify
→ instantiate
```

không được:

```text
deserialize
→ execute arbitrary code
```

---

# 21. Model format provider

```text
NativeModelProvider
OnnxProvider
SafeTensorProvider
GgufProvider
ExternalModelProvider
TestModelProvider
```

---

# 22. Model architecture

Model metadata có thể mô tả:

```text
Transformer
CNN
RNN
Diffusion
AudioModel
VisionModel
MultimodalModel
GraphModel
CustomGraph
```

---

# 23. Architecture identity

Architecture metadata không tự động quyết định semantics.

Actual executable graph đến từ 643.

---

# 24. Model signature

Model phải khai báo:

```text
inputs
outputs
shapes
dtypes
layouts
constraints
```

---

# 25. Dynamic shapes

Cho phép:

```text
batch = dynamic
sequence = dynamic
height = dynamic
width = dynamic
```

nhưng constraint phải rõ.

---

# 26. Input contract

Ví dụ:

```text
input_tokens: i32[N, T]
attention_mask: bool[N, T]
```

---

# 27. Output contract

Ví dụ:

```text
logits: f16[N, T, V]
```

---

# 28. Model target

```text
CPU
GPU
NPU
DSP
Accelerator
WASM
MultiDevice
```

---

# 29. Architecture target

```text
x86_64
arm64
riscv64
wasm32
...
```

---

# 30. Device constraints

Model có thể yêu cầu:

```text
min_memory
required_features
required_instruction_set
required_gpu_features
```

---

# 31. Provider constraints

Model có thể yêu cầu provider capabilities.

---

# 32. Compatibility

Compatibility gồm:

```text
SchemaCompatible
RuntimeCompatible
DeviceCompatible
ProviderCompatible
PolicyCompatible
```

---

# 33. Compatibility matrix

```text
Model
 ×
Provider
 ×
Target
 ×
Device
 ×
Runtime
```

---

# 34. Compatibility result

```text
Compatible
Incompatible
Unknown
```

Không được coi `Unknown` là `Compatible`.

---

# 35. Model dependency

Model có thể phụ thuộc:

- tokenizer;
- vocabulary;
- preprocessor;
- postprocessor;
- feature schema;
- embedding model;
- auxiliary model.

---

# 36. Dependency identity

Mỗi dependency có:

```text
id
version
hash
compatibility
```

---

# 37. Model bundle

Bundle có thể chứa:

```text
weights
graph
tokenizer
config
preprocessor
postprocessor
metadata
```

---

# 38. Separation

Model bundle không được chứa:

- runtime credentials;
- private keys;
- production secrets.

---

# 39. Model configuration

Configuration có thể thuộc 601/637.

Artifact immutable không nên phụ thuộc implicit remote configuration.

---

# 40. Model runtime profile

```text
ModelRuntimeProfile {
    execution_mode
    precision
    batch_policy
    memory_policy
    device_policy
}
```

---

# 41. Serving profile

Serving configuration tách khỏi model identity.

---

# 42. Model alias

Alias:

```text
latest
stable
candidate
production
```

chỉ là mutable pointer.

---

# 43. Alias safety

Alias thay đổi phải atomic.

---

# 44. Alias revision

Mỗi alias mutation có revision.

---

# 45. Alias rollback

Có thể chuyển alias về version trước.

---

# 46. Alias is not version

Một alias không được dùng làm immutable artifact reference.

---

# 47. Model channel

Channels:

```text
Development
Validation
Staging
Production
Archived
```

là lifecycle metadata.

---

# 48. Model stages

Canonical lifecycle:

```text
Draft
Registered
Validated
Candidate
Staged
Promoted
Serving
Deprecated
Retired
Revoked
```

---

# 49. Stage transitions

Không được tự ý chuyển stage.

Transition phải qua policy.

---

# 50. Promotion

Promotion:

```text
Candidate
→ Staged
→ Promoted
```

---

# 51. Promotion evidence

Promotion record phải reference:

```text
evaluation
policy
actor
timestamp
artifact
schema
```

---

# 52. Promotion policy

639 quyết định điều kiện.

---

# 53. Evaluation gate

646 cung cấp evidence.

---

# 54. Promotion does not deploy

Promotion chỉ thay đổi lifecycle state.

---

# 55. Deployment

636 nhận promoted release.

---

# 56. Rollback

Rollback:

```text
current version
→ previous known version
```

---

# 57. Rollback identity

Rollback không tạo artifact mới.

---

# 58. Emergency revoke

638/639 có thể mark model:

```text
Revoked
```

---

# 59. Revoked model

Không được activate mới.

Existing deployment handling thuộc 636/639.

---

# 60. Retirement

Retired model không còn candidate cho deployment mới trừ khi explicitly restored.

---

# 61. Restore

Restore là explicit policy-controlled operation.

---

# 62. Deletion

Deletion chỉ xảy ra sau retention policy.

---

# 63. Model retention

640 quản lý:

- model;
- evaluation;
- lineage;
- artifact;
- logs.

---

# 64. Model lineage

Canonical chain:

```text
Dataset
 ↓
Preprocessing
 ↓
Training
 ↓
Checkpoint
 ↓
Model
 ↓
Evaluation
 ↓
Promotion
 ↓
Deployment
```

---

# 65. Dataset lineage

Reference:

```text
DatasetId
DatasetRevision
GovernanceRevision
```

---

# 66. Training lineage

Reference:

```text
TrainingJobId
TrainingRunId
CodeFingerprint
ConfigFingerprint
```

---

# 67. Code lineage

Ghi compiler/source/build fingerprint.

---

# 68. Dependency lineage

Record:

```text
runtime
operator library
provider
tokenizer
preprocessor
```

---

# 69. Evaluation lineage

646 result:

```text
EvaluationId
EvaluationRevision
GateResult
```

---

# 70. Deployment lineage

636:

```text
DeploymentId
ReleaseId
Cluster
Revision
```

---

# 71. Serving lineage

631:

```text
ServiceId
ServiceInstance
ModelVersion
ServingProfile
```

---

# 72. Full provenance

```text
Data
 ↓
Training
 ↓
Model
 ↓
Evaluation
 ↓
Promotion
 ↓
Release
 ↓
Deployment
 ↓
Serving
```

---

# 73. Model release

Release là immutable deployment candidate.

```text
ModelRelease {
    release_id
    model_version
    package_hash
    schema_fingerprint
    evaluation_refs
    policy_refs
}
```

---

# 74. Release != package

Package chứa artifact.

Release mô tả **được phép đưa artifact nào vào lifecycle nào**.

---

# 75. Model supply chain

Supply chain:

```text
source
→ training
→ artifact
→ packaging
→ validation
→ registry
→ promotion
→ deployment
```

---

# 76. Supply-chain fingerprint

Release có fingerprint toàn chuỗi.

---

# 77. Attestation

Model có thể có:

```text
ModelAttestation {
    producer
    build
    source
    artifact
    environment
    signature
}
```

---

# 78. Signature

638/610 xử lý cryptographic verification.

---

# 79. Trust

Model trust metadata:

```text
Publisher
Signer
TrustDomain
VerificationStatus
```

---

# 80. Trust state

```text
Unknown
Verified
Trusted
Quarantined
Revoked
```

---

# 81. Trust does not imply quality

Verified signature không đồng nghĩa model đã đạt evaluation gate.

---

# 82. Evaluation does not imply trust

Đạt metric không thay thế artifact integrity/trust.

---

# 83. Promotion requires both

Production promotion policy có thể yêu cầu:

```text
IntegrityVerified
AND
EvaluationPassed
AND
PolicyAllowed
```

---

# 84. Model quarantine

Model có thể bị quarantine nếu:

- signature invalid;
- artifact corrupted;
- provider incompatible;
- security policy violated.

---

# 85. Quarantine

Quarantine ngăn activation nhưng giữ artifact để điều tra.

---

# 86. Model catalog

Catalog index:

```text
name
description
tags
task
language
modality
architecture
version
stage
```

---

# 87. Catalog search

Có thể tìm:

```text
task = speech
language = vi
target = cpu
precision = f16
stage = production
```

---

# 88. Semantic catalog

641 có thể index metadata.

---

# 89. Vector catalog

645/641 có thể hỗ trợ semantic model discovery.

---

# 90. Catalog result

Catalog result phải reference immutable ModelVersion.

---

# 91. Model metadata

Metadata có thể chứa:

- task;
- modality;
- language;
- license;
- creator;
- description;
- capabilities;
- limitations.

---

# 92. Limitation metadata

Model producer có thể khai báo known limitations.

Registry không biến limitation thành guarantee.

---

# 93. Model card

Native metadata:

```text
.axmodelcard
```

---

# 94. Model card

Có thể chứa:

```text
intended_use
limitations
training_data_summary
evaluation_summary
risk_notes
license
provenance
```

---

# 95. Model card provenance

Mỗi claim có thể reference source/evidence.

---

# 96. Model documentation

Documentation không được thay đổi artifact hash.

---

# 97. Model schema evolution

Schema thay đổi lớn tạo version mới.

---

# 98. Compatible schema change

Minor compatible changes có thể dùng revision theo policy.

---

# 99. Breaking change

Breaking change phải tạo incompatible version.

---

# 100. Schema compatibility rules

Kiểm tra:

- input added required;
- input removed;
- dtype changed;
- shape changed;
- output removed;
- semantic field changed.

---

# 101. Compatibility analyzer

647 có static compatibility checker.

---

# 102. Serving compatibility

Before serving:

```text model
+ runtime
+ device
+ schema
+ provider
```

phải pass compatibility.

---

# 103. Model migration

Model migration không mutate artifact.

Tạo artifact/version mới.

---

# 104. Quantized variant

Quantized model có thể:

```text same logical model
different artifact/version
```

---

# 105. Variant identity

Variants reference:

```text parent_model
variant_type
artifact_hash
```

---

# 106. Model family

Model family groups variants:

```text
Base
Quantized
Distilled
Pruned
FineTuned
Specialized
```

---

# 107. Family identity

Family không thay thế model version identity.

---

# 108. Fine-tune lineage

Fine-tuned model references:

```text parent_model
fine_tuning_dataset
training_run
```

---

# 109. Distillation lineage

Student model references:

```text teacher_model
distillation_dataset
training_run
```

---

# 110. Ensemble model

Ensemble references multiple immutable models.

---

# 111. Ensemble artifact

Ensemble definition itself is versioned.

---

# 112. Model composition

Models may be composed into pipeline:

```text
preprocessor
→ encoder
→ model
→ postprocessor
```

---

# 113. Pipeline identity

Pipeline gets its own immutable revision.

---

# 114. Model graph

643 owns actual execution graph.

647 stores identity/reference.

---

# 115. Model cache

Serving systems may cache model artifacts.

---

# 116. Cache identity

Cache key:

```text
artifact_hash
provider
target
runtime_version
```

---

# 117. Cache invalidation

Artifact hash change automatically creates distinct cache entry.

---

# 118. Compiled model cache

643 can compile model into target-specific artifact.

---

# 119. Compiled artifact identity

```text
source_model_hash
compiler_hash
target
provider
optimization_profile
```

---

# 120. Compilation reproducibility

Same inputs should produce deterministic artifact when compiler profile permits.

---

# 121. Model compilation lineage

Compiled artifact references original model.

---

# 122. Model deployment package

625/613 may package:

```text
model
compiled kernels
metadata
schema
runtime requirements
```

---

# 123. Runtime dependencies

Dependencies are explicit.

---

# 124. No hidden downloads

Serving cannot silently download arbitrary model components.

---

# 125. Offline mode

Registry supports fully offline operation.

---

# 126. Air-gapped mode

No external network dependency.

---

# 127. Registry providers

```text
NativeRegistry
LocalRegistry
FileRegistry
RemoteRegistry
FederatedRegistry
ExternalRegistry
TestRegistry
```

---

# 128. External registries

Optional adapters:

```text
Hugging Face
MLflow
OCI-like registries
Object Storage
Cloud model registries
```

---

# 129. External provider authority

External registry cannot bypass:

- 603;
- 639;
- 638;
- 640.

---

# 130. Registry namespace

```text
tenant/project/model
```

---

# 131. Model name

Human-readable name is not identity.

---

# 132. Model lookup

Lookup by:

```text
ModelId
ModelVersion
ArtifactHash
Alias
Tag
```

---

# 133. Model query

Typed query preferred.

---

# 134. Model filters

```text
task
modality
language
target
architecture
stage
provider
license
```

---

# 135. Model tags

Tags are metadata, not lifecycle authority.

---

# 136. Alias mutation

Requires permission.

---

# 137. Promotion authorization

Requires 639 policy evaluation.

---

# 138. Approval

Promotion may require explicit approval token.

---

# 139. Approval binding

Approval token binds:

```text
model
version
artifact
environment
policy_revision
expiry
```

---

# 140. Approval replay

Approval token cannot be reused beyond its declared scope.

---

# 141. Model release candidate

Candidate state contains:

```text
model_version
evaluation_refs
compatibility_result
trust_result
policy_result
```

---

# 142. Release validation

Validation must complete before promotion.

---

# 143. Promotion transaction

Promotion atomically updates:

```text
stage
release
audit
alias
```

where declared by policy.

---

# 144. Partial promotion

If multi-region promotion is used:

```text
region status
cluster status
```

is explicit.

---

# 145. Federation

Each registry domain retains local authority.

---

# 146. Federated registry

Global catalog may aggregate metadata without becoming global authority.

---

# 147. Cross-region artifact

Artifact transfer follows 640 residency and 603 capabilities.

---

# 148. Cross-cluster promotion

636 controls rollout.

---

# 149. Registry replication

628 handles replication.

---

# 150. Registry consistency

Supports:

```text
Local
Session
Causal
Quorum
Linearizable
```

where backend supports.

---

# 151. Version visibility

A model may be:

```text
Registered locally
Replicated
Globally visible
```

independently.

---

# 152. Stale registry

Stale catalog result must expose revision/freshness.

---

# 153. No stale activation

Activation requires current enough metadata according to policy.

---

# 154. Model lease

Serving can hold:

```text
ModelLease
```

to prevent premature reclamation.

---

# 155. Lease

Lease identifies:

```text
model_version
serving_instance
generation
expiry
```

---

# 156. Retirement safety

Model cannot be physically deleted while active leases exist.

---

# 157. Force retirement

Requires explicit privileged policy.

---

# 158. Model garbage collection

Artifact reclamation is separate from language GC.

---

# 159. Reclamation

Possible only when:

```text no active lease
AND
retention expired
AND
policy allows
```

---

# 160. Model storage accounting

606 tracks:

- artifact bytes;
- chunks;
- cache;
- compiled artifacts.

---

# 161. Model download budget

Network quota applies.

---

# 162. Model load budget

Memory/VRAM quota applies.

---

# 163. Model concurrency

Serving profile defines maximum concurrency.

---

# 164. Model warmup

Serving may require explicit warmup evaluation.

---

# 165. Warmup result

Recorded as part of deployment/serving validation.

---

# 166. Serving catalog

631 can query:

```text
ModelId
Version
Endpoint
Provider
Device
Health
```

---

# 167. Serving alias

Serving alias resolves to immutable version before request execution.

---

# 168. Request consistency

A request may pin:

```text ModelVersion
```

to avoid alias race.

---

# 169. Model rollout

636 decides traffic rollout.

---

# 170. Model traffic variants

Canary variants reference immutable versions.

---

# 171. Shadow model

Shadow model receives copies but production side effects remain prohibited unless explicitly authorized.

---

# 172. A/B model variant

637/636 may control allocation.

647 records model identity.

---

# 173. Model health

Health data comes from 633/631.

647 stores lifecycle evidence.

---

# 174. Model quality

Quality evidence comes from 646.

647 stores references.

---

# 175. Model security

Security evidence comes from 603/638/639.

---

# 176. Model governance

640 provides:

- data lineage;
- residency;
- retention;
- classification.

---

# 177. Model audit

Every lifecycle mutation creates audit event.

---

# 178. Audit events

```text
ModelRegistered
VersionCreated
ArtifactVerified
ValidationCompleted
Promoted
Demoted
AliasChanged
ServingStarted
Deprecated
Revoked
Retired
Deleted
```

---

# 179. Event integration

634 distributes lifecycle events.

---

# 180. Event schema

Events use 612 schema.

---

# 181. Event ordering

Within one model identity, lifecycle revisions are monotonic.

---

# 182. Model state machine

```text
Draft
 ↓
Registered
 ↓
Validated
 ↓
Candidate
 ↓
Staged
 ↓
Promoted
 ↓
Serving
 ↓
Deprecated
 ↓
Retired
```

Exceptional:

```text
Quarantined
Revoked
Failed
```

---

# 183. State transition validation

Invalid transition rejected.

---

# 184. Generation safety

Concurrent lifecycle mutations use expected generation/revision.

---

# 185. CAS mutation

Registry updates use:

```text
expected_revision
```

---

# 186. Transaction

Related metadata updates can be atomic.

---

# 187. Crash recovery

600/628 recover registry transactions.

---

# 188. Registry snapshot

Snapshots are immutable.

---

# 189. Backup

Registry metadata can be backed up through 611/613.

---

# 190. Artifact recovery

CAS integrity can reconstruct missing metadata references where manifest remains valid.

---

# 191. Orphan detection

Registry scans for:

```text artifact without model
model without artifact
broken dependency
expired lease
```

---

# 192. Repair

Repair must be explicit and auditable.

---

# 193. No silent repair

Corrupted model metadata is not silently recreated.

---

# 194. Model dependency graph

Registry maintains dependency DAG.

---

# 195. Dependency cycle

Model dependency cycles are rejected unless provider explicitly supports recursive runtime semantics.

---

# 196. Version constraints

Dependencies can specify:

```text exact
compatible range
minimum
maximum
hash pinned
```

---

# 197. Reproducible bundle

Bundle identity includes every dependency hash.

---

# 198. Supply-chain lock

Native lockfile:

```text
.axmodellock
```

---

# 199. Lockfile

Contains:

```text
model
artifact
dependencies
provider
target
hashes
```

---

# 200. Lock validation

Serving/deployment can require lockfile consistency.

---

# 201. Model SBOM

Native metadata may describe:

- components;
- libraries;
- providers;
- licenses;
- build inputs.

---

# 202. SBOM

Model supply-chain components can be exported.

---

# 203. License metadata

License information is descriptive metadata.

Policy 639 may impose deployment restrictions.

---

# 204. Model publisher

Publisher identity references 638 trust system.

---

# 205. Publisher verification

Signature verification does not imply safety or performance.

---

# 206. Model trust domains

Models can belong to:

```text
internal
partner
public
experimental
```

---

# 207. Trust domain policy

639 determines allowed usage.

---

# 208. Model provenance

Provenance can include:

```text producer
source
training run
dataset
compiler
artifact
evaluation
publisher
```

---

# 209. Provenance immutability

Core provenance records cannot be rewritten.

---

# 210. Provenance correction

Corrections append a new revision.

---

# 211. Model card version

Model card has independent revision.

---

# 212. Model metadata schema

`.axmodelmeta`

---

# 213. Model registry schema

`.axmodelregistry`

---

# 214. Release schema

`.axmodelrelease`

---

# 215. Supply-chain schema

`.axmodelsupply`

---

# 216. Lifecycle schema

`.axmodellifecycle`

---

# 217. Model lock schema

`.axmodellock`

---

# 218. Compiler annotations

```text
@model
@model_version
@artifact
@model_schema
@model_input
@model_output
@model_dependency
@model_family
@model_variant
@model_release
@model_stage
@model_alias
@model_promotion
@model_evaluation
@model_serving
@model_target
@model_provider
@model_trust
@model_attestation
@model_lineage
@model_retention
@model_revoke
@model_retire
```

---

# 219. Generated metadata

```text
.axmodel
.axmodelmeta
.axmodelcard
.axmodelregistry
.axmodelrelease
.axmodelsupply
.axmodellifecycle
.axmodellock
```

---

# 220. Struct-only API

```text
ModelRegistry
Model
ModelVersion
ModelArtifact
ModelManifest
ModelSchema
ModelRelease
ModelPromotion
ModelLineage
ModelCompatibility
ModelCatalog
ModelLease
```

---

# 221. Example registration

```text
registry.register(
    model,
    artifact,
    schema,
    lineage
)
```

---

# 222. Example validation

```text
registry.validate(
    model_version,
    evaluation_ref
)
```

---

# 223. Example promotion

```text
registry.promote(
    model_version,
    target_stage
)
```

---

# 224. Example alias

```text
registry.assign_alias(
    "production",
    model_version
)
```

---

# 225. Example serving resolution

```text
registry.resolve(
    model_id,
    alias = "production"
)
```

---

# 226. Example artifact

```text
artifact = registry.artifact(
    model_version
)
```

---

# 227. Example lineage

```text
registry.lineage(
    model_version
)
```

---

# 228. Example compatibility

```text
registry.check_compatibility(
    model_version,
    device,
    runtime
)
```

---

# 229. CLI

```text
axiom model list
axiom model inspect
axiom model versions
axiom model register
axiom model validate
axiom model promote
axiom model demote
axiom model alias
axiom model lineage
axiom model dependencies
axiom model compatibility
axiom model verify
axiom model quarantine
axiom model revoke
axiom model retire
axiom model restore
axiom model delete
```

---

# 230. Supply-chain CLI

```text
axiom model supply-chain inspect MODEL
axiom model supply-chain verify MODEL
axiom model supply-chain export MODEL
```

---

# 231. Reproducibility CLI

```text
axiom model reproduce MODEL_VERSION
```

---

# 232. Catalog query

```text
axiom model search \
    --task speech \
    --language vi \
    --target cpu
```

---

# 233. Serving lookup

```text
axiom model resolve production/my-model
```

---

# 234. Security verification

```text
axiom model verify MODEL_VERSION
```

---

# 235. Registry diagnostics

```text
axiom model doctor
```

Kiểm tra:

- broken artifacts;
- orphan chunks;
- invalid dependencies;
- stale aliases;
- missing evaluation;
- expired leases.

---

# 236. Registry health

633 metrics:

```text
registry_lookup_latency
artifact_fetch_latency
verification_failures
orphan_artifacts
active_models
retired_models
cache_hit_rate
```

---

# 237. Model metrics

Serving metrics remain owned by 633/631.

647 only references lifecycle state.

---

# 238. Model quality metrics

646 owns metrics.

647 references immutable results.

---

# 239. No duplicated ownership

Một metric chỉ có một canonical owner.

---

# 240. Model lineage query

Can answer:

```text
Which dataset produced this model?
Which evaluation validated it?
Which deployment uses it?
Which service serves it?
Which dependencies does it contain?
```

---

# 241. Reverse lineage

Can answer:

```text
Which models depend on dataset X?
Which deployments use model Y?
Which services use version Z?
```

---

# 242. Impact analysis

640/641/642 may analyze downstream impact.

---

# 243. Model dependency impact

Before retirement:

```text
registry
→ dependency graph
→ active serving
→ deployments
```

must be checked.

---

# 244. Retirement gate

Model with active production references cannot normally retire without explicit policy.

---

# 245. Emergency revoke

Revocation can override normal lifecycle.

---

# 246. Revocation propagation

634 distributes revocation events.

636/631 enforce activation/serving response.

---

# 247. Registry federation

Federated registry uses:

```text
RegistryId
RegistryGeneration
TrustDomain
```

---

# 248. Registry authority

Each registry controls its own namespace.

---

# 249. Imported model

Imported model enters:

```text
Imported
→ Verified
→ Validated
→ Candidate
```

rather than automatically Production.

---

# 250. External model import

Import requires:

- artifact integrity;
- schema validation;
- provider compatibility;
- trust policy;
- optional evaluation.

---

# 251. Model conversion

ONNX → Axiom model:

```text
external artifact
→ conversion
→ new artifact
```

---

# 252. Conversion lineage

Converted model records source format/hash.

---

# 253. Conversion validation

646 should validate semantic equivalence where possible.

---

# 254. Compiler integration

643 can compile registered model into target executable representation.

---

# 255. Compiled model registration

Compiled artifacts may be registered as derived artifacts.

---

# 256. Derived artifact

```text
source_model_hash
compiler_hash
target
provider
```

---

# 257. Artifact promotion

Only canonical model version is promoted; compiled variants follow it.

---

# 258. Runtime selection

Serving chooses compiled artifact compatible with device.

---

# 259. Fallback

Fallback provider must be explicitly configured.

---

# 260. No semantic fallback

A lower-precision or different provider cannot silently replace requested model semantics when policy disallows it.

---

# 261. Model warm cache

Cache can preload promoted model versions.

---

# 262. Model prefetch

636/631 can prefetch artifacts before rollout.

---

# 263. Prefetch failure

Does not alter model identity.

---

# 264. Large model streaming

Model can load chunks progressively if 643 supports it.

---

# 265. Lazy loading

Weights may be lazily loaded.

---

# 266. Memory mapping

Native artifacts can use mmap where compatible.

---

# 267. Device memory

614/643 manage actual device memory.

---

# 268. Registry ownership

647 owns metadata, not live GPU memory.

---

# 269. Model unload

631/643 release runtime resources.

---

# 270. Model lease release

Serving instance releases lease after unload.

---

# 271. Model lifecycle event

Every important state transition can emit event 634.

---

# 272. Event replay

Registry state can be reconstructed from snapshots + lifecycle events where configured.

---

# 273. Registry snapshot

Snapshot includes:

```text
model identities
versions
aliases
stages
dependencies
metadata
```

---

# 274. Artifact snapshot

CAS snapshot includes referenced artifact hashes.

---

# 275. Snapshot consistency

Registry metadata and artifact manifest references must agree.

---

# 276. Backup validation

Restore test validates:

```text registry
+
artifact manifest
+
CAS
```

---

# 277. Disaster recovery

628/636 may replicate registry metadata.

---

# 278. Cross-region recovery

Artifact residency remains governed by 640.

---

# 279. Registry disaster mode

Read-only mode can preserve model resolution during control-plane failure.

---

# 280. Serving during registry outage

Existing pinned model versions may continue according to policy.

---

# 281. Alias during registry outage

Cached alias resolution may be allowed only within explicit freshness policy.

---

# 282. Security during outage

Cached trust state cannot extend beyond allowed expiry.

---

# 283. Offline serving

Pinned model artifact can serve without registry connectivity when policy permits.

---

# 284. Offline model package

Package contains:

```text
model
manifest
schema
integrity
required runtime
```

---

# 285. Model air-gap transfer

Transfer package can be verified offline.

---

# 286. Import/export

```text
axiom model export
axiom model import
```

---

# 287. Export manifest

Includes hashes and provenance references.

---

# 288. No secret export

Credentials and private keys are excluded.

---

# 289. Model replication

Registry metadata replication via 628.

---

# 290. Artifact replication

CAS replication via 613/628.

---

# 291. Artifact replication policy

May specify:

```text
regions
clusters
replicas
priority
```

subject to governance.

---

# 292. Model residency

Model artifact can carry residency classification.

---

# 293. Training-data residency

Model lineage references training data governance.

---

# 294. Derived model governance

640 may propagate relevant restrictions from training data.

---

# 295. Model deletion

Deletion must consider:

```text
serving
deployment
lineage
evaluation
cache
backup
replica
```

---

# 296. Tombstone

Deleted model identity remains tombstoned long enough to prevent accidental resurrection.

---

# 297. Resurrection prevention

Old artifact cannot recreate deleted model without explicit restore workflow.

---

# 298. Model restore

Restore creates a new lifecycle revision and audit event.

---

# 299. Model audit trail

Audit trail is append-only.

---

# 300. Audit integrity

Audit records can be cryptographically chained.

---

# 301. Model catalog consistency

Search index 641 may lag registry.

Result must expose registry revision.

---

# 302. Search index rebuild

Registry remains authoritative.

---

# 303. AI-readable model registry

An AI agent can query:

```text
model
version
schema
evaluation
lineage
compatibility
trust
deployment
```

through structured API.

---

# 304. Agent model selection

644 may request candidates based on constraints.

647 returns evidence, not an implicit quality judgment.

---

# 305. Constraint query

Example:

```text
target = cpu
memory <= 2GB
language = vi
task = tts
license = allowed
evaluation = required
```

---

# 306. Candidate result

Every candidate contains:

```text
model_id
version
artifact_hash
compatibility
evaluation_refs
trust_status
```

---

# 307. Selection boundary

Agent/application/policy chooses the candidate.

---

# 308. Model policy

639 can express:

```text
production requires verified publisher
AND
evaluation gate passed
AND
artifact signed
```

---

# 309. Policy cannot modify artifact

Policy only allows or denies usage.

---

# 310. Model metadata security

Untrusted metadata cannot:

- execute code;
- alter policy;
- grant capability;
- modify registry state.

---

# 311. Model prompt/config security

Model-provided configuration is data, not executable policy.

---

# 312. Custom operator

Custom operator requires:

```text
provider
artifact
capability
trust
```

---

# 313. Operator supply chain

Custom kernels are included in supply-chain manifest.

---

# 314. Kernel compatibility

643 checks device/provider support.

---

# 315. Model runtime compatibility

647 records required runtime ABI.

---

# 316. ABI fingerprint

Model executable interface has ABI fingerprint.

---

# 317. Schema fingerprint

Input/output schema has fingerprint.

---

# 318. Artifact fingerprint

Artifact hash is canonical.

---

# 319. Build fingerprint

Compiler/build configuration has fingerprint.

---

# 320. Full model identity tuple

```text
ModelId
ModelVersion
ArtifactHash
SchemaFingerprint
BuildId
Target
Provider
```

---

# 321. Reproducible model build

Source + dependencies + config + compiler + dataset + seed should reconstruct training/build lineage where possible.

---

# 322. Reproducibility limitations

Hardware nondeterminism and external providers may prevent bit-identical reconstruction.

Such limitations must be recorded.

---

# 323. Model build status

```text
Reproducible
ConditionallyReproducible
NonReproducible
Unknown
```

---

# 324. Model lifecycle status

Separate from build reproducibility.

---

# 325. Model quality status

Separate from trust.

---

# 326. Trust/quality matrix

A model can independently be:

```text
trusted
validated
deployed
```

Each state has separate meaning.

---

# 327. No single "model status"

UI may display multiple dimensions rather than collapsing them.

---

# 328. Model registry API performance

Expected:

- O(1) lookup by immutable ID;
- bounded alias resolution;
- indexed metadata search;
- streaming artifact transfer.

---

# 329. Large registry

Registry metadata must support millions of versions without loading all metadata into memory.

---

# 330. Pagination

Catalog queries use cursor pagination.

---

# 331. Query cursor

Cursor is bound to:

```text query_fingerprint
registry_revision
expiration
```

---

# 332. Cache

647 can cache:

- metadata;
- compatibility;
- artifact manifests.

---

# 333. Cache invalidation

Revision-aware.

---

# 334. No stale promotion

Promotion uses current registry revision.

---

# 335. Concurrency

Concurrent registration uses optimistic concurrency.

---

# 336. Race protection

Alias/stage updates use CAS.

---

# 337. Multi-writer registry

Supports concurrent writers through transaction/version model.

---

# 338. Registry partitioning

Can partition by:

```text tenant
project
namespace
model_id
```

---

# 339. Cross-partition queries

Explicit and budgeted.

---

# 340. Model catalog federation

Federated search results identify source registry.

---

# 341. External registry synchronization

Sync records:

```text source_registry
source_revision
import_revision
```

---

# 342. Sync conflict

Local and external changes never silently overwrite each other.

---

# 343. Import conflict

Requires explicit resolution.

---

# 344. External deletion

Imported model remains locally versioned unless policy requests deletion.

---

# 345. Model package compatibility

625 handles distribution dependencies.

647 handles semantic model identity.

---

# 346. Model marketplace boundary

Marketplace, payment, ratings and commercial ranking are outside core.

---

# 347. Model licensing

License metadata can be enforced by 639.

---

# 348. Model provenance search

Can query all models derived from a dataset revision.

---

# 349. Dataset impact

640 can notify 647 when governed source changes.

---

# 350. Revalidation trigger

A material dataset governance change can trigger evaluation request.

---

# 351. Model invalidation

647 can mark:

```text
NeedsRevalidation
```

without automatically deleting model.

---

# 352. Evaluation freshness

Promotion policy may require evaluation not older than a configured revision/time.

---

# 353. Evaluation binding

A gate references exact:

```text model version
dataset revision
evaluation revision
```

---

# 354. No floating evaluation

`latest evaluation` is not sufficient for immutable promotion evidence.

---

# 355. Promotion record

Promotion stores exact evaluation references.

---

# 356. Deployment release

636 stores exact model release.

---

# 357. Serving resolution

631 stores exact model version/generation.

---

# 358. Full chain consistency

```text
Promotion
→ Release
→ Deployment
→ Service
```

must preserve exact model identity.

---

# 359. Model downgrade

Downgrade is explicit and policy-controlled.

---

# 360. Roll-forward

A fixed model can be replaced with a new version without mutating history.

---

# 361. Emergency fallback

636 may select an explicitly configured fallback version.

---

# 362. Fallback validation

Fallback must itself satisfy required compatibility/trust policy.

---

# 363. Model dependency fallback

Dependencies are resolved from immutable references.

---

# 364. No floating dependencies in production

Production release should pin dependencies.

---

# 365. Development mode

Floating dependency resolution may be allowed.

---

# 366. Lock promotion

Production promotion can require `.axmodellock`.

---

# 367. Model supply-chain verification command

```text
axiom model supply-chain verify MODEL
```

checks:

```text
artifact
dependencies
signatures
schema
compiler
provider
evaluation
policy
```

---

# 368. Model attestation chain

```text
Source
 ↓
Build
 ↓
Artifact
 ↓
Package
 ↓
Registry
 ↓
Evaluation
 ↓
Promotion
```

---

# 369. Attestation storage

Attestation metadata is immutable.

---

# 370. Attestation verification

610/638 verify cryptographic portions.

---

# 371. Registry health state

```text
Healthy
Degraded
ReadOnly
Recovering
Unavailable
```

---

# 372. Read-only recovery

Model resolution can continue while writes are disabled.

---

# 373. Registry failover

635/628 may coordinate registry replicas.

---

# 374. Split-brain protection

Registry writes require valid epoch/fencing.

---

# 375. Registry leader

635 can elect registry control-plane leader where needed.

---

# 376. Local registry

Single-process/local registry needs no distributed control plane.

---

# 377. Minimal profile

Axiom application can use:

```text
ModelArtifact
ModelSchema
ModelVersion
```

without full registry.

---

# 378. Embedded registry

A small application can embed an in-process registry.

---

# 379. Server registry

Large deployment uses distributed registry.

---

# 380. WASM registry

Host-provided read-only registry is supported.

---

# 381. Mobile registry

Local catalog can operate under platform sandbox.

---

# 382. Edge registry

Edge nodes may maintain signed offline model catalogs.

---

# 383. Offline promotion

Promotion in offline mode requires delegated authority and expiry.

---

# 384. Federation

Offline edge state reconciles on reconnect.

---

# 385. Conflict

Conflicting promotions are resolved by authority/revision rules, not timestamps alone.

---

# 386. Clock independence

Model lifecycle correctness does not depend solely on wall-clock time.

---

# 387. Expiry

Time-based policies use trusted clock semantics from 637/638.

---

# 388. Model alias expiry

Alias may have explicit expiry.

---

# 389. Candidate expiry

Candidate releases may expire.

---

# 390. Retention

Expired candidate artifacts remain according to retention.

---

# 391. Model archival

Archived model may move to lower-cost storage.

---

# 392. Archive restore

Restore preserves artifact hash.

---

# 393. Cold storage

Provider may move CAS chunks to cold storage.

---

# 394. Serving cannot use cold artifact directly

Artifact must be restored before serving unless provider explicitly supports streaming cold storage.

---

# 395. Artifact compression

613 handles compression.

---

# 396. Artifact encryption

610 handles cryptography; 638 handles keys.

---

# 397. Encrypted model

Encryption metadata is separate from model identity.

---

# 398. Key rotation

Encrypted artifact may remain same logical model while encryption wrapper changes.

---

# 399. Wrapped artifact

If ciphertext changes, artifact hash changes but logical model version can reference immutable source plus new package wrapper according to packaging policy.

---

# 400. No private key in model

Absolute invariant.

---

# 401. Model secrets

Secrets must use 638 references, not embedded bytes.

---

# 402. Environment secrets

Serving obtains secrets at runtime.

---

# 403. Model config secret

Secret references are resolved by capability-controlled provider.

---

# 404. AI-generated model

Models produced by 643/644 must enter normal registry validation.

---

# 405. Agent-generated model metadata

Agent-generated metadata is marked as generated until verified.

---

# 406. Agent cannot promote without policy

644 cannot bypass 639.

---

# 407. Model provenance from agent

Agent-generated model records agent identity/version.

---

# 408. Model provenance from workflow

629 workflow ID is preserved.

---

# 409. Model provenance from compute

630 job ID is preserved.

---

# 410. Model provenance from cluster

635 placement information can be recorded.

---

# 411. Model provenance from compiler

Compiler build fingerprint is recorded.

---

# 412. Model provenance from hardware

Training hardware can be recorded.

---

# 413. Training environment

Environment fingerprint references 643/633.

---

# 414. Model metadata export

Can export machine-readable provenance.

---

# 415. Model metadata import

Imported metadata is untrusted until validated.

---

# 416. Schema validation

Import validates metadata schema before registration.

---

# 417. Namespace collision

Imported model IDs cannot silently overwrite local model IDs.

---

# 418. Import remapping

Explicit namespace remapping supported.

---

# 419. Registry permissions

Capabilities:

```text
ModelRead
ModelRegister
ModelUpdateMetadata
ModelPromote
ModelAlias
ModelRevoke
ModelRetire
ModelDelete
ArtifactRead
ArtifactWrite
```

---

# 420. Least privilege

Normal serving needs read-only model/artifact capabilities.

---

# 421. Promotion capability

Promotion is privileged.

---

# 422. Deletion capability

Deletion is separate from retirement.

---

# 423. Audit

All privileged actions audited.

---

# 424. Diagnostics

602 receives:

```text
registration failures
verification failures
promotion failures
artifact corruption
dependency failures
```

---

# 425. Observability

633 receives lifecycle metrics.

---

# 426. Event stream

634 receives model lifecycle events.

---

# 427. Search

641 indexes model metadata.

---

# 428. Analytics

642 analyzes:

- model adoption;
- version distribution;
- evaluation trends;
- artifact size;
- lifecycle durations.

---

# 429. Knowledge graph

645 may represent:

```text
Model
Dataset
Experiment
Evaluation
Deployment
Service
```

relationships.

---

# 430. Agent

644 can query registry as a tool.

---

# 431. Evaluation

646 is authoritative for evaluation results.

---

# 432. Policy

639 is authoritative for promotion authorization.

---

# 433. Governance

640 is authoritative for data lifecycle constraints.

---

# 434. Trust

638/610 are authoritative for cryptographic trust.

---

# 435. Deployment

636 is authoritative for deployment orchestration.

---

# 436. Serving

631 is authoritative for service execution.

---

# 437. Compiler

643 is authoritative for model compilation/execution representation.

---

# 438. Registry remains coordinator

647 links these domains without taking ownership from them.

---

# 439. Performance

Registry metadata operations should be:

- low allocation;
- indexed;
- bounded;
- asynchronous for large artifacts.

---

# 440. Artifact streaming

Large model transfers use streaming APIs.

---

# 441. Parallel chunk transfer

Provider may download chunks concurrently.

---

# 442. Backpressure

606/607 govern transfer resource usage.

---

# 443. Artifact verification pipeline

```text
Receive
→ Hash
→ Verify
→ Manifest Validate
→ Schema Validate
→ Dependency Validate
→ Trust Validate
→ Register
```

---

# 444. Registration failure

Invalid artifact never becomes active version.

---

# 445. Atomic registration

Model version and artifact manifest become visible atomically.

---

# 446. Crash safety

Interrupted registration leaves recoverable staging state.

---

# 447. Staging

Staging artifacts are not visible to serving.

---

# 448. Staging cleanup

Unreferenced staging artifacts are reclaimed after retention.

---

# 449. Model registry garbage collection

Separate from artifact CAS garbage collection.

---

# 450. Registry consistency invariant

Every active version must reference an existing verified artifact manifest.

---

# 451. Supply-chain invariant

Every production release must have an immutable artifact hash.

---

# 452. Promotion invariant

Promotion references exact evaluation evidence.

---

# 453. Deployment invariant

Deployment references exact release/model version.

---

# 454. Serving invariant

Serving resolves to immutable model version.

---

# 455. Alias invariant

Alias mutation is atomic and versioned.

---

# 456. Revocation invariant

Revoked model cannot become newly active without explicit restoration.

---

# 457. Deletion invariant

Referenced artifact cannot be physically deleted.

---

# 458. Dependency invariant

Production dependency versions are pinned.

---

# 459. Trust invariant

Signature verification cannot be bypassed by metadata.

---

# 460. Security invariant

Model artifact cannot grant capabilities.

---

# 461. Governance invariant

Artifact movement obeys residency policy.

---

# 462. Lineage invariant

Transformation cannot silently erase source lineage.

---

# 463. Evaluation invariant

Evaluation result is tied to exact model version.

---

# 464. Reproducibility invariant

Environment differences are recorded.

---

# 465. Compatibility invariant

Unknown compatibility cannot silently become compatible.

---

# 466. Cache invariant

Compiled cache is keyed by source artifact/compiler/target/provider identity.

---

# 467. Federation invariant

Federated catalog cannot become implicit global authority.

---

# 468. Offline invariant

Offline authority has explicit scope/expiry.

---

# 469. Recovery invariant

Registry recovery cannot resurrect tombstoned model without explicit restore.

---

# 470. Audit invariant

Privileged lifecycle mutations are auditable.

---

# 471. Acceptance criteria

**Target: ≥500 acceptance criteria**

Các nhóm bắt buộc:

- model registration;
- model identity;
- model version;
- artifact hashing;
- CAS;
- chunking;
- resumable transfer;
- integrity verification;
- model schema;
- input/output contract;
- dynamic shape;
- model format;
- external format import;
- safe loading;
- architecture metadata;
- target compatibility;
- provider compatibility;
- dependency resolution;
- model bundle;
- model family;
- fine-tuning lineage;
- distillation lineage;
- quantization variants;
- ensemble models;
- model pipelines;
- model aliases;
- lifecycle states;
- promotion;
- demotion;
- approval;
- evaluation binding;
- quality gate binding;
- trust;
- attestation;
- signature verification;
- quarantine;
- revoke;
- retire;
- restore;
- deletion;
- retention;
- model lineage;
- training lineage;
- dataset lineage;
- experiment lineage;
- evaluation lineage;
- deployment lineage;
- serving lineage;
- supply-chain fingerprint;
- lockfiles;
- SBOM;
- catalog;
- search;
- semantic discovery;
- compatibility matrix;
- model cache;
- compiled artifact;
- compiler lineage;
- runtime ABI;
- serving resolution;
- model lease;
- artifact reclamation;
- registry replication;
- registry federation;
- offline registry;
- edge registry;
- disaster recovery;
- snapshot;
- backup;
- restore;
- event emission;
- observability;
- diagnostics;
- governance;
- residency;
- security;
- credentials;
- capability enforcement;
- agent integration;
- AI-readable metadata;
- CLI;
- API;
- fuzzing;
- crash recovery;
- deterministic testing;
- performance;
- large-model streaming.

---

# 472. Profiles

```text
AXMODEL_NONE
AXMODEL_ARTIFACT
AXMODEL_SCHEMA
AXMODEL_REGISTRY
AXMODEL_LINEAGE
AXMODEL_CATALOG
AXMODEL_TRUST
AXMODEL_PROMOTION
AXMODEL_SERVING
AXMODEL_SUPPLYCHAIN
AXMODEL_FEDERATION
AXMODEL_EDGE
AXMODEL_FULL
```

---

# 473. Minimal profile

`AXMODEL_ARTIFACT` chỉ cần:

```text
ModelArtifact
ArtifactManifest
ModelSchema
ModelVersion
```

---

# 474. Local profile

`AXMODEL_REGISTRY` bổ sung:

```text
ModelRegistry
ModelCatalog
ModelLifecycle
ModelAlias
```

---

# 475. Production profile

`AXMODEL_FULL` có:

```text
registry
lineage
evaluation
trust
promotion
supply-chain
serving
federation
governance
```

---

# 476. Final architecture

```text
                         AXIOM AI MODEL PLANE

                              643 ML
                                │
                                ▼
                         Model Artifact
                                │
                         ┌──────┴──────┐
                         │     647     │
                         │Model Registry│
                         └──────┬──────┘
                                │
        ┌───────────────┬───────┼────────┬──────────────┐
        ▼               ▼       ▼        ▼              ▼
     Schema          Lineage   Trust   Catalog       Lifecycle
        │               │       │        │              │
        │               │       │        │              ▼
        │               │       │        │          Promotion
        │               │       │        │              │
        │               │       │        │              ▼
        │               │       │        │           Release
        │               │       │        │              │
        │               │       │        │              ▼
        │               │       │        │             636
        │               │       │        │          Deployment
        │               │       │        │              │
        │               │       │        │              ▼
        │               │       │        │             631
        │               │       │        │           Serving
        │               │       │        │
        │               │       │        └──────► 641 Search
        │               │       └───────────────► 638 Trust
        │               └───────────────────────► 640 Governance
        └───────────────────────────────────────► 646 Evaluation

                     613 CAS / 625 Distribution
```

---

# 477. Chuỗi AI lifecycle hoàn chỉnh

Sau 647, Axiom có một AI supply chain native:

```text
DATA
 ↓
640 Governance
 ↓
643 Training
 ↓
647 Model Artifact
 ↓
646 Evaluation
 ↓
639 Policy
 ↓
647 Promotion
 ↓
636 Deployment
 ↓
631 Serving
 ↓
633 Observability
 ↓
646 Continuous Evaluation
 ↓
647 Lifecycle
```

---

# 478. Ý nghĩa kiến trúc

Axiom hiện đã có sự phân tách rõ:

```text
643 = BUILD / RUN AI

646 = MEASURE AI

647 = IDENTIFY / GOVERN AI ARTIFACT LIFECYCLE

636 = DEPLOY AI

631 = SERVE AI
```

Điều này tránh việc một runtime khổng lồ biến thành một "AI framework" duy nhất.

---

# 479. Trạng thái

**BOOTSTRAP-647 — COMPLETE**

### Task kế tiếp

**BOOTSTRAP-648 — Native AI Simulation, Synthetic Data, Environment Modeling, Scenario Generation, Digital Twin, Agent Sandbox & Closed-Loop AI Testing Runtime 5.0**
:::