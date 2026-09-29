Tiếp tục với **BOOTSTRAP-640 — Native Distributed Data Governance, Data Classification, Data Lineage, Residency, Retention, Privacy, Transformation Policy & Data Lifecycle Runtime 5.0**.

:::writing{variant="document" id="74126" title="BOOTSTRAP-640 — Native Distributed Data Governance, Data Classification, Data Lineage, Residency, Retention, Privacy, Transformation Policy & Data Lifecycle Runtime 5.0"}
# BOOTSTRAP-640
## Native Distributed Data Governance, Data Classification, Data Lineage, Residency, Retention, Privacy, Transformation Policy & Data Lifecycle Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Data Governance & Lifecycle Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-639

---

# 1. Mục tiêu

BOOTSTRAP-640 xây dựng lớp **Data Governance Plane** native của Axiom.

Nó quản lý vòng đời và governance của dữ liệu:

- classification;
- ownership;
- sensitivity;
- data domains;
- data lineage;
- provenance;
- residency;
- geographic restrictions;
- retention;
- deletion;
- archival;
- legal/organizational hold metadata;
- privacy constraints;
- data access governance;
- transformation requirements;
- masking/redaction;
- tokenization boundary;
- export restrictions;
- replication restrictions;
- cross-region movement;
- dataset lifecycle;
- schema/data contract governance;
- evidence và audit.

Mục tiêu:

> Axiom phải có khả năng biết **dữ liệu là gì, thuộc ai, đến từ đâu, được phép đi đâu, được giữ bao lâu, được biến đổi thế nào và khi nào phải loại bỏ** mà không biến core runtime thành một hệ thống quản trị doanh nghiệp khổng lồ.

---

# 2. Ranh giới kiến trúc

| Hệ thống | Trách nhiệm |
|---|---|
| 611 | filesystem/storage |
| 612 | serialization/schema |
| 628 | distributed data/replication |
| 637 | dynamic configuration |
| 638 | credentials/trust |
| 639 | policy decision |
| **640** | data governance/lifecycle |
| 633 | telemetry |
| 634 | events |
| 636 | deployment |
| 603 | capability enforcement |

Điểm quan trọng:

```text
628 = data distribution
639 = policy decision
640 = data governance
```

640 **không thay thế** 639.

Ví dụ:

```text
640:
dataset classification = Confidential
residency = VN
retention = 365 days

639:
may service A read dataset X?

603:
does service A possess required capability?

628:
where/how is dataset replicated?
```

---

# 3. Nguyên tắc nền tảng

1. Data governance metadata không phải data payload.
2. Classification phải explicit.
3. Không tự suy đoán sensitivity trong core.
4. Ownership phải explicit.
5. Lineage phải provenance-aware.
6. Residency phải enforceable qua policy/placement layers.
7. Retention phải deterministic.
8. Deletion phải distinguish logical/physical deletion.
9. Replication không được tự động phá residency policy.
10. Governance không tự cấp capability.
11. 640 không đọc dữ liệu tùy ý để phân loại.
12. Privacy transformation phải explicit.
13. Raw sensitive data không xuất hiện trong metadata nếu không cần.
14. Lineage metadata phải bounded.
15. Governance history phải immutable/auditable.
16. Data lifecycle state phải observable.
17. Policy revisions phải xác định.
18. Cross-tenant data movement phải explicit.
19. Governance failure phải có semantics rõ ràng.
20. Core không tuyên bố compliance certification.

---

# 4. Data Governance Model

Core object:

```text
DataAsset {
    asset_id
    asset_type
    owner
    steward
    classification
    schema
    lineage
    residency
    retention
    lifecycle
    access_policy
    transformation_policy
}
```

---

# 5. DataAsset

Các loại:

```text
Dataset
Table
Collection
Stream
Event
File
Object
Blob
Document
Model
FeatureSet
Cache
Index
Snapshot
Backup
Log
Telemetry
```

---

# 6. Asset identity

```text
DataAssetId
DataAssetGeneration
DataAssetVersion
DataAssetRevision
```

Không tái sử dụng identity sau destructive replacement nếu semantics yêu cầu audit continuity.

---

# 7. Dataset identity

```text
DatasetId {
    namespace
    name
    generation
}
```

---

# 8. Ownership

```text
DataOwner
DataSteward
DataCustodian
```

Phân biệt:

```text
Owner
```

= chịu trách nhiệm governance.

```text
Custodian
```

= hệ thống đang lưu trữ/điều khiển vật lý.

---

# 9. Data domain

```text
DataDomain {
    domain_id
    name
    owner
    classification_defaults
}
```

Ví dụ:

```text
customer
billing
telemetry
operations
model-training
```

---

# 10. Classification

Core classification phải extensible.

Built-in baseline:

```text
Public
Internal
Confidential
Restricted
Secret
```

Nhưng đây là **metadata semantics**, không phải capability.

---

# 11. Classification hierarchy

Có thể:

```text
Public
  ↓
Internal
  ↓
Confidential
  ↓
Restricted
  ↓
Secret
```

Nhưng domain có thể định nghĩa classification khác.

---

# 12. Classification level

```text
Classification {
    namespace
    level
    labels
    handling_requirements
}
```

---

# 13. Labels

Ví dụ:

```text
PII
Financial
Credential
Health
Location
Biometric
SourceCode
TradeSecret
Telemetry
```

Axiom chỉ cung cấp metadata mechanism.

Không tự xác nhận payload thực sự thuộc label đó.

---

# 14. Classification confidence

Nếu classification được tạo từ external analyzer:

```text
Declared
Imported
Derived
Inferred
```

Core không tự biến `Inferred` thành authoritative classification.

---

# 15. Classification authority

Mỗi classification có:

```text
authority_id
revision
timestamp
```

---

# 16. Classification change

Thay đổi:

```text
Confidential → Restricted
```

phải tạo revision mới.

Không mutate historical record.

---

# 17. Classification inheritance

Dataset có thể đặt default:

```text
Dataset = Confidential
```

Field có thể override:

```text
field.email = Restricted
```

Child không được tự hạ classification nếu parent policy cấm.

---

# 18. Field-level classification

Schema metadata có thể:

```text
@classification("Restricted")
email: String
```

---

# 19. Record-level classification

Optional:

```text
record.classification
```

nhưng metadata overhead phải được kiểm soát.

---

# 20. Runtime vs compile-time classification

Compile-time:

```text
schema metadata
```

Runtime:

```text
record metadata
```

Ứng dụng chọn profile.

---

# 21. Data handling policy

```text
HandlingPolicy {
    allowed_operations
    allowed_destinations
    allowed_processors
    transformation_requirements
    export_rules
}
```

---

# 22. Data operations

```text
Read
Write
Create
Update
Delete
Export
Import
Replicate
Transform
Aggregate
Join
Train
Cache
Backup
Restore
Archive
```

---

# 23. Data destination

Destination có thể là:

```text
Region
Cluster
Service
Tenant
Device
StorageClass
ExternalEndpoint
```

---

# 24. Residency

```text
ResidencyPolicy {
    allowed_regions
    forbidden_regions
    allowed_clusters
    movement_rules
}
```

---

# 25. Residency semantics

Ví dụ:

```text
allowed_regions = [VN]
```

nghĩa là authoritative data không được đặt ở region ngoài VN.

Không tự động suy luận rằng:

```text
user is Vietnamese
```

hoặc các thuộc tính cá nhân khác.

---

# 26. Residency vs routing

Residency:

```text
where data may persist
```

Routing:

```text
where request may execute
```

Hai khái niệm phải độc lập.

---

# 27. Data movement

Movement:

```text
source
→ destination
```

phải evaluate:

```text
classification
residency
purpose
actor
policy
```

---

# 28. Replication integration

628 phải query 640 trước khi tạo replica nếu residency policy yêu cầu.

---

# 29. Replica metadata

```text
DataReplica {
    asset_id
    replica_id
    region
    cluster
    generation
    classification
    residency_status
}
```

---

# 30. Residency violation

State:

```text
Compliant
Pending
Violating
Unknown
```

---

# 31. Residency remediation

640 có thể emit:

```text
DataResidencyViolation
```

636/628/635 xử lý remediation.

640 không tự kill process hoặc migrate data nếu không có executor.

---

# 32. Data sovereignty boundary

Metadata có thể chỉ ra:

```text
jurisdiction_scope
```

nhưng core không đưa ra kết luận pháp lý.

---

# 33. Retention policy

```text
RetentionPolicy {
    minimum_duration
    maximum_duration
    deletion_mode
    archive_policy
}
```

---

# 34. Retention anchor

Retention có thể tính từ:

```text
Creation
LastWrite
Ingestion
Completion
Classification
BusinessEvent
ExplicitTimestamp
```

---

# 35. Retention timestamp

Phải explicit.

Không cho:

```text
"keep for 1 year"
```

mà không biết tính từ thời điểm nào.

---

# 36. Retention state

```text
Active
RetainUntil
EligibleForDeletion
DeletionPending
Deleted
Archived
Held
```

---

# 37. Legal/organizational hold abstraction

```text
DataHold {
    hold_id
    asset_scope
    reason_code
    issuer
    created_at
    expires_at?
}
```

640 chỉ quản lý metadata hold.

Không tự định nghĩa pháp luật.

---

# 38. Hold precedence

Nếu:

```text
retention expired
```

nhưng:

```text
hold active
```

thì:

```text
retain
```

---

# 39. Hold removal

Hold removal tạo audit event.

---

# 40. Deletion eligibility

Một asset chỉ eligible nếu:

```text
retention expired
AND
no active hold
AND
no required legal/operational dependency
```

---

# 41. Deletion semantics

Phân biệt:

```text
LogicalDelete
PhysicalDelete
CryptographicErase
ReplicaDelete
CacheDelete
BackupExpiry
```

---

# 42. Logical deletion

Asset không còn visible bình thường.

Payload có thể vẫn tồn tại cho đến physical reclamation.

---

# 43. Physical deletion

Storage layer 611/628 thực hiện.

---

# 44. Cryptographic erase

Nếu data encrypted bằng dedicated key:

```text
destroy key
```

có thể render data unreadable.

Không được tuyên bố rằng cryptographic erase luôn đảm bảo physical destruction.

---

# 45. Replica deletion

628 phải propagate deletion intent.

---

# 46. Backup deletion

Backup có lifecycle riêng.

640 phải track:

```text
backup_retention
```

---

# 47. Cache deletion

Distributed cache 628 phải invalidate data khi required.

---

# 48. Tombstone

Deletion có thể tạo:

```text
DataDeletionTombstone
```

để prevent stale replica resurrection.

---

# 49. Resurrection prevention

Replica nhận old data sau deletion phải reject nếu tombstone/revision mới hơn.

---

# 50. Data generation

Mỗi destructive lifecycle transition có generation/epoch.

---

# 51. Data lineage

640 xây dựng lineage graph.

```text
Source
 ↓
Transform
 ↓
Dataset
 ↓
Service
 ↓
Output
```

---

# 52. Lineage node

```text
LineageNode {
    node_id
    asset_id
    operation
    revision
}
```

---

# 53. Lineage edge

```text
LineageEdge {
    source
    destination
    operation
    timestamp
    actor
    execution_id
}
```

---

# 54. Lineage operations

```text
Read
Copy
Transform
Join
Aggregate
Filter
Export
Import
Train
Generate
Derive
```

---

# 55. Lineage granularity

Profiles:

```text
Dataset
Table
Column
Record
Field
```

Record/field-level lineage có thể rất lớn nên không mặc định bật.

---

# 56. Bounded lineage

Lineage phải có:

```text
max_nodes
max_edges
max_history
retention
sampling
```

---

# 57. Lineage compression

Có thể aggregate:

```text
1M records
```

thành:

```text
batch lineage
```

khi exact lineage không cần thiết.

---

# 58. Provenance

Lineage phải distinguish:

```text
Source
Transformation
Actor
Execution
Tool
Version
```

---

# 59. Transformation identity

```text
TransformationId
TransformationVersion
CodeFingerprint
```

---

# 60. Code fingerprint

Transformation lineage có thể lưu:

```text
build_id
package_hash
module_hash
```

Không cần lưu toàn bộ executable.

---

# 61. Model lineage

ML/model workloads có:

```text
ModelId
TrainingRunId
DatasetRevision
FeatureSetRevision
CodeFingerprint
```

---

# 62. Training data lineage

630/629 có thể publish:

```text
TrainingRun
```

đến 640.

640 chỉ lưu provenance metadata.

---

# 63. Derived data

Dataset Y derived từ X:

```text
Y
  derived_from X
```

Không copy toàn bộ X metadata nếu không cần.

---

# 64. Classification propagation

Transformation có policy:

```text
propagate classification
```

Ví dụ:

```text
Restricted + Restricted
→ Restricted
```

Semantics phải explicit.

---

# 65. Classification join rule

Nếu join hai datasets:

```text
A classification = X
B classification = Y
```

result classification có thể được policy xác định:

```text
max(X,Y)
```

hoặc custom lattice.

---

# 66. Classification lattice

640 hỗ trợ partial ordering:

```text
Public < Internal < Confidential < Restricted
```

nhưng domain có thể định nghĩa lattice riêng.

---

# 67. Incomparable classifications

Nếu:

```text
Financial
Health
```

không có thứ tự trực tiếp.

Policy có thể require union:

```text
Financial + Health
```

---

# 68. Data purpose

Data operation có:

```text
Purpose {
    purpose_id
    description
}
```

Ví dụ:

```text
service_delivery
analytics
debugging
training
billing
security
```

---

# 69. Purpose binding

Policy có thể yêu cầu:

```text
data may be used only for purpose X
```

---

# 70. Purpose propagation

Purpose metadata có thể travel cùng data contract.

---

# 71. Purpose violation

Ví dụ:

```text
billing data
→
model training
```

nếu policy cấm:

```text
deny
```

---

# 72. Data minimization

Transformation policy có thể yêu cầu:

```text
only fields required
```

---

# 73. Field projection

```text
ProjectionPolicy {
    allowed_fields
    denied_fields
}
```

---

# 74. Masking

640 cung cấp metadata/contract cho:

```text
Mask
Redact
Hash
Tokenize
Generalize
Remove
```

Transformation thực thi bởi 640 provider hoặc data-processing layer.

---

# 75. Masking semantics

Ví dụ:

```text
email
→
e***@example.com
```

Masking algorithm phải được explicit.

---

# 76. Redaction

```text
Redact(field)
```

nghĩa là field bị loại khỏi output.

---

# 77. Tokenization boundary

Tokenization:

```text
original
→
token
```

provider giữ mapping nếu cần.

640 không giữ secret token vault mặc định.

---

# 78. Hashing

Hashing sensitive fields phải chỉ định:

```text
algorithm
salt policy
version
```

---

# 79. Reversible transformation

Nếu transform reversible:

```text
encrypt
tokenize
```

phải khai báo.

---

# 80. Irreversible transformation

Ví dụ:

```text
redact
one-way hash
aggregation
```

phải đánh dấu irreversible.

---

# 81. Transformation provenance

Mỗi transform có:

```text
input revision
output revision
transform version
actor
timestamp
```

---

# 82. Data export

Export request:

```text
DataExportRequest {
    asset
    destination
    purpose
    fields
    format
}
```

---

# 83. Export admission

640 + 639 evaluate:

```text
classification
destination
purpose
policy
```

---

# 84. Data import

Import phải validate:

```text
schema
classification
provenance
source
destination
```

---

# 85. External destination

External export phải explicit capability:

```text
603 network/external capability
```

và policy:

```text
639 allow
```

---

# 86. Data boundary

Cross-boundary transfer:

```text
internal
→
external
```

được coi là governance event.

---

# 87. Data transfer receipt

```text
DataTransferReceipt {
    transfer_id
    source
    destination
    asset_revision
    classification
    policy_revision
}
```

---

# 88. Transfer integrity

Payload integrity thuộc 610.

Governance metadata thuộc 640.

---

# 89. Encryption requirement

640 có thể yêu cầu:

```text
at_rest = encrypted
in_transit = encrypted
```

610/611/609 thực hiện.

---

# 90. Key binding

Dataset có thể reference:

```text
CredentialId
KeyGeneration
```

không chứa key material.

---

# 91. Rotation impact

638 key rotation không được làm mất governance metadata.

---

# 92. Data lifecycle

Canonical state machine:

```text
Declared
→ Active
→ Restricted
→ Archived
→ RetentionExpired
→ DeletionPending
→ Deleted
```

Có thể có:

```text
Held
Derived
Quarantined
```

---

# 93. Quarantine

Data có thể bị:

```text
Quarantined
```

do integrity/governance violation.

640 phát state.

Executor xử lý.

---

# 94. Lifecycle transitions

Mọi transition phải:

```text
authorized
audited
versioned
```

---

# 95. Lifecycle controller

```text
DataLifecycleController
```

đọc:

```text
retention
holds
residency
dependencies
```

và tạo actions.

---

# 96. Lifecycle action

```text
Retain
Archive
Delete
Move
Replicate
Restrict
Quarantine
Transform
```

---

# 97. No direct unsafe deletion

640 không trực tiếp free arbitrary storage blocks.

611/628 thực hiện physical operations.

---

# 98. Data dependency

Asset A có thể depend:

```text
A → B
```

Không xóa B nếu A yêu cầu B và policy cấm orphaning.

---

# 99. Dependency graph

```text
DataDependencyGraph {
    nodes
    edges
    revisions
}
```

---

# 100. Dependency types

```text
DerivedFrom
References
MaterializedFrom
Indexes
SnapshotOf
BackupOf
ReplicaOf
```

---

# 101. Data contract

```text
DataContract {
    schema_fingerprint
    classification
    lineage_requirements
    residency
    retention
    access
}
```

---

# 102. Schema integration

612 cung cấp:

```text
schema fingerprint
version
migration
```

640 attaches governance metadata.

---

# 103. Schema evolution

Nếu field nhạy cảm mới được thêm:

```text
governance validation
```

có thể yêu cầu policy review.

---

# 104. Schema admission

Data schema activation có thể hỏi 639:

```text
admit schema revision?
```

---

# 105. Data contract compatibility

Compatibility phải kiểm tra:

```text
schema
classification
residency
retention
```

---

# 106. Data governance fingerprint

```text
GovernanceFingerprint =
hash(
    schema_fingerprint,
    classification,
    residency,
    retention,
    handling_policy
)
```

---

# 107. Governance revision

```text
GovernanceRevision
```

khác:

```text
DataRevision
```

---

# 108. Why separate revisions?

Data:

```text
record changed
```

Governance:

```text
retention changed
```

Không nhất thiết cùng revision.

---

# 109. Governance snapshot

```text
GovernanceSnapshot {
    asset
    governance_revision
    schema_fingerprint
    policies
    classification
    residency
    retention
}
```

Immutable.

---

# 110. Governance consistency

Critical governance changes có thể yêu cầu:

```text
linearizable
```

Operational metadata có thể eventual.

---

# 111. Governance registry

```text
DataGovernanceRegistry
```

Storage có thể dùng 628.

---

# 112. Registry operations

```text
register_asset
update_governance
get_asset
get_snapshot
watch_asset
query_lineage
query_residency
query_retention
```

---

# 113. Query model

Queries phải bounded:

```text
scope
asset_type
classification
owner
region
lifecycle
```

---

# 114. No arbitrary graph traversal

Lineage query phải có:

```text
max_depth
max_nodes
max_edges
timeout
```

---

# 115. Lineage traversal

Directions:

```text
Upstream
Downstream
Both
```

---

# 116. Lineage time range

Query có:

```text
from_revision
to_revision
```

hoặc timestamp range.

---

# 117. Lineage deletion

Lineage metadata có lifecycle riêng.

Không được tự giữ indefinitely.

---

# 118. Provenance retention

Có thể giữ lineage lâu hơn payload nếu governance yêu cầu.

---

# 119. Audit vs lineage

Audit:

```text
who did what
```

Lineage:

```text
data came from where/how
```

Không trộn hai hệ thống.

---

# 120. Telemetry relation

633 có telemetry.

640 có data governance.

Telemetry chỉ trở thành lineage source nếu explicit integration.

---

# 121. Event integration

634 phát:

```text
DataAssetCreated
DataAssetUpdated
DataClassified
DataMoved
DataExported
DataArchived
DataDeletionRequested
DataDeleted
DataGovernanceViolation
```

---

# 122. Event privacy

Events không chứa payload nhạy cảm mặc định.

---

# 123. Event references

Thay payload bằng:

```text
asset_id
revision
fingerprint
```

---

# 124. Data access

639 quyết định:

```text
may_read?
may_export?
may_transform?
```

640 cung cấp governance context.

---

# 125. Effective access

```text
Capability
AND
Identity
AND
Policy
AND
DataGovernance
```

---

# 126. Data governance cannot grant access

640 không cấp:

```text
read capability
```

603 vẫn authoritative.

---

# 127. Data policy evaluation

639 nhận:

```text
classification
purpose
residency
asset_id
```

từ 640.

---

# 128. Dynamic governance

637 có thể tune:

```text
retention
limits
rollout
```

nhưng không được bypass immutable security constraints.

---

# 129. Governance rollout

Policy changes:

```text
prepare
→ validate
→ simulate
→ canary
→ activate
```

---

# 130. Governance impact simulation

Có thể hỏi:

```text
What assets would become non-compliant?
```

Result phải là inventory/evidence, không tự remediate.

---

# 131. Residency impact

Trước thay đổi:

```text
allowed_regions = VN
```

sang:

```text
VN + SG
```

simulation tìm replicas affected.

---

# 132. Retention impact

Thay:

```text
365d
→
90d
```

simulation:

```text
assets newly eligible for deletion
```

---

# 133. Classification impact

Thay:

```text
Internal
→
Restricted
```

simulation:

```text
access paths
replicas
exports
caches
```

---

# 134. Governance drift

Expected:

```text
Restricted
```

Observed:

```text
Internal
```

state:

```text
GovernanceDrift
```

---

# 135. Drift remediation

640 emits:

```text
GovernanceDriftDetected
```

Executor có thể:

```text
reclassify
restrict
move
delete
```

theo explicit policy.

---

# 136. Residency remediation

Possible actions:

```text
StopReplication
MoveReplica
DeleteReplica
Quarantine
```

---

# 137. Retention remediation

```text
Archive
Delete
ExtendByHold
```

---

# 138. Deletion workflow

Deletion nên đi qua 629 nếu:

```text
multi-stage
approval
large dataset
```

---

# 139. Simple deletion

Small local asset:

```text
640
→
611
```

có thể trực tiếp invoke lifecycle adapter.

---

# 140. Large deletion

Distributed:

```text
640
→
629 workflow
→
628 replicas
→
611 storage
```

---

# 141. Deletion verification

Result:

```text
Requested
InProgress
PartiallyDeleted
Deleted
Failed
```

---

# 142. Partial deletion

Không báo:

```text
Deleted
```

nếu replica vẫn tồn tại khi policy yêu cầu complete deletion.

---

# 143. Best-effort deletion

Policy có thể cho phép:

```text
BestEffort
```

nhưng phải report incomplete state.

---

# 144. Backup retention

Backup system phải publish:

```text
backup_revision
expiry
location
```

---

# 145. Snapshot retention

628 snapshots có:

```text
snapshot_retention
```

640 có thể govern.

---

# 146. Archive

Archive state:

```text
Archived
```

không đồng nghĩa:

```text
Deleted
```

---

# 147. Cold storage

Storage class:

```text
Hot
Warm
Cold
Archive
```

Governance có thể constrain transitions.

---

# 148. Data residency and archive

Archive location cũng phải satisfy residency.

---

# 149. Cross-region backup

Backup không được bypass residency.

---

# 150. Data movement planning

Before movement:

```text
source governance
+
destination governance
```

phải compatible.

---

# 151. Movement compatibility

Destination phải support:

```text
classification
encryption
retention
residency
```

---

# 152. Data handling capabilities

Platform capabilities:

```text
CanEncrypt
CanMask
CanTokenize
CanDelete
CanRegionLock
CanAudit
```

---

# 153. Processor capability

Service có thể declare:

```text
ProcessorContract {
    supported_classifications
    supported_transformations
    supported_regions
}
```

---

# 154. Data processor admission

639 kiểm tra:

```text
asset
+
processor
+
purpose
+
policy
```

---

# 155. Processor trust

638/627 supply:

```text
identity
trust
credential state
```

---

# 156. Processor lineage

Transformation records:

```text
processor_id
processor_version
build_id
```

---

# 157. Data export format

Export metadata:

```text
format
schema_fingerprint
governance_fingerprint
```

---

# 158. Import verification

Receiver kiểm tra:

```text
schema
governance
provenance
signature
```

nếu required.

---

# 159. Signed data manifest

Có thể có:

```text
DataManifest {
    asset_id
    revision
    schema
    governance
    content_hash
    signature
}
```

---

# 160. Content hash

Hash từ 610.

Không chứa payload trong manifest.

---

# 161. Content-addressed data

613 CAS có thể lưu payload.

640 lưu governance metadata reference.

---

# 162. CAS lifecycle

CAS object không được reclaim nếu governance references còn active.

---

# 163. Reference tracking

```text
GovernanceReference
```

có thể protect CAS objects.

---

# 164. Data garbage collection

640 không phải language GC.

Nó là:

```text
data lifecycle reclamation
```

---

# 165. Reclamation

Object eligible:

```text
no active references
AND
retention expired
AND
no hold
```

---

# 166. Distributed reclamation

628/613 thực hiện.

640 quyết định eligibility.

---

# 167. Stale replica

Nếu replica stale vượt governance limit:

```text
Stale
```

có thể:

```text
quarantine
resync
delete
```

---

# 168. Data freshness

Optional:

```text
FreshnessPolicy {
    max_age
}
```

---

# 169. Freshness vs retention

Freshness:

```text
how old may data be?
```

Retention:

```text
how long may data exist?
```

---

# 170. Data quality metadata

Optional:

```text
QualityMetadata {
    completeness
    validity
    freshness
    confidence
}
```

640 chỉ stores declared/derived evidence.

Không tự certify quality.

---

# 171. Data contract validation

On ingest:

```text
schema
classification
provenance
required metadata
```

---

# 172. Missing governance metadata

States:

```text
Unknown
Incomplete
Unclassified
```

Security-sensitive flows có thể deny unknown.

---

# 173. Default classification

Assets phải có:

```text
explicit classification
```

hoặc domain default.

---

# 174. Unknown classification

Không mặc định thành:

```text
Public
```

---

# 175. Safe default

Default thường:

```text
Unknown
```

và policy quyết định handling.

---

# 176. Data catalog

640 có lightweight catalog:

```text
DataCatalog
```

Metadata only.

Không phải BI platform.

---

# 177. Catalog search

```text
find assets
by owner
by classification
by domain
by region
by lifecycle
```

---

# 178. Catalog indexing

Indexes:

```text
owner
classification
region
type
lifecycle
schema
```

---

# 179. Catalog scalability

Metadata store có thể partition theo:

```text
tenant
domain
asset_id
```

---

# 180. Multi-tenant governance

Tenant metadata isolated.

Global platform authority có cross-tenant read capability.

---

# 181. Tenant ownership

Tenant có thể own:

```text
dataset
stream
model
```

nhưng platform controls global governance constraints.

---

# 182. Data sharing

Sharing contract:

```text
DataShare {
    source
    consumer
    purpose
    fields
    expiry
    policy_revision
}
```

---

# 183. Share expiration

Expired share:

```text
inactive
```

---

# 184. Share revocation

Revocation tạo revision.

Existing cached data phải follow policy.

---

# 185. Data access grant

640 does not grant capability.

Share is governance metadata.

---

# 186. Cross-tenant share

Explicit:

```text
source_tenant
destination_tenant
approval
policy
```

---

# 187. Data usage evidence

Consumer can emit:

```text
DataUseEvent {
    asset
    purpose
    consumer
    revision
}
```

---

# 188. Usage retention

Usage evidence có lifecycle riêng.

---

# 189. Privacy boundary

640 cung cấp metadata primitives:

```text
purpose
classification
minimization
masking
retention
sharing
residency
```

Không tuyên bố compliance với luật cụ thể.

---

# 190. Privacy policy

```text
PrivacyPolicy {
    purposes
    allowed_processing
    retention
    sharing
    residency
}
```

---

# 191. Data subject reference

Nếu ứng dụng cần user/data-subject mapping:

```text
DataSubjectRef
```

opaque ID.

640 không cần biết danh tính thật.

---

# 192. Subject deletion request

Có thể model:

```text
DataErasureRequest {
    subject_ref
    scope
    requested_at
}
```

---

# 193. Erasure scope

Có thể gồm:

```text
primary
replicas
cache
derived
indexes
backups
```

---

# 194. Derived data

Erasure propagation policy phải explicit.

Không phải mọi aggregate đều có thể reverse-delete.

---

# 195. Erasure workflow

Complex erasure:

```text
640
→
639 authorization
→
629 workflow
→
628/611/613
```

---

# 196. Erasure evidence

Evidence:

```text
requested
processed
partially_processed
completed
```

Không chứa deleted payload.

---

# 197. Data lineage after deletion

Lineage metadata có thể retain:

```text
asset tombstone
```

để tránh mất provenance.

---

# 198. Tombstone privacy

Tombstone không chứa:

```text
raw payload
```

và sensitive identifiers phải redacted nếu policy yêu cầu.

---

# 199. Governance audit

Audit events:

```text
AssetRegistered
ClassificationChanged
ResidencyChanged
RetentionChanged
HoldCreated
HoldReleased
DataExported
DataMoved
DataDeleted
DataArchived
PolicyViolation
GovernanceDrift
```

---

# 200. Audit integration

602/633 lưu telemetry/audit.

640 không trở thành independent logging system.

---

# 201. Metrics

```text
governance_assets
classification_changes
residency_violations
retention_expired
deletion_pending
deletion_failed
lineage_edges
governance_drift
data_exports
cross_region_transfers
```

---

# 202. Cardinality control

Không dùng:

```text
raw record IDs
```

làm unbounded metric labels.

---

# 203. Governance explain

CLI:

```text
axiom data explain dataset-X
```

show:

```text
classification
owner
residency
retention
lineage
effective policies
```

---

# 204. Why blocked?

```text
axiom data why-blocked export-X
```

có thể combine 640 + 639 explain data.

---

# 205. Governance impact

```text
axiom data impact classification-change
```

show affected:

```text
replicas
services
exports
policies
```

---

# 206. Lineage query

```text
axiom data lineage asset-X --upstream --depth 5
```

---

# 207. Residency query

```text
axiom data residency asset-X
```

---

# 208. Retention query

```text
axiom data retention asset-X
```

---

# 209. Deletion query

```text
axiom data deletion-status asset-X
```

---

# 210. Governance snapshot export

```text
.axdata-governance
```

có thể chứa metadata snapshot.

---

# 211. AI-readable metadata

Generated:

```text
.axdata
.axlineage
.axclassification
.axresidency
.axretention
.axlifecycle
.axdatacontract
```

---

# 212. Compiler annotations

```text
@data
@dataset
@classification
@owner
@steward
@residency
@retention
@lineage
@purpose
@share
@transform
@mask
@tokenize
@governance
@hold
```

---

# 213. Struct-only API

Ví dụ:

```text
DataRegistry.register(self, asset)
DataRegistry.classify(self, asset, classification)
DataRegistry.get_governance(self, asset)
DataRegistry.record_lineage(self, edge)
DataRegistry.check_residency(self, movement)
DataLifecycle.evaluate(self, asset)
DataLifecycle.delete(self, asset)
```

---

# 214. Error model

```text
DataGovernanceError
UnknownAsset
ClassificationError
ResidencyViolation
RetentionConflict
ActiveHold
LineageLimitExceeded
GovernanceConflict
SchemaMismatch
DataContractViolation
DeletionIncomplete
UnauthorizedDataMovement
StaleGovernance
```

---

# 215. Concurrency

Governance snapshot immutable.

Readers concurrent.

Writers produce revisions.

---

# 216. Registry update

```text
read revision
→
modify
→
CAS expected_revision
→
publish
```

---

# 217. Governance transactions

Một transaction có thể update:

```text
classification
residency
retention
```

atomically cho cùng asset.

---

# 218. Cross-asset transactions

Không mặc định atomic.

629/628 orchestration nếu cần.

---

# 219. Governance watch

```text
watch(asset)
watch(namespace)
watch(classification)
watch(region)
```

---

# 220. Watch semantics

Initial snapshot:

```text
revision N
```

sau đó:

```text
N+1
N+2
...
```

---

# 221. Watch backpressure

Bounded queue + snapshot replacement.

---

# 222. Federation watch

Regional registry có thể subscribe global governance changes.

---

# 223. Edge governance

Edge bundle có:

```text
scope
expiry
issuer_epoch
```

---

# 224. Offline governance

Nếu control plane unavailable:

```text
last valid snapshot
```

theo max offline duration.

---

# 225. Edge data movement

Edge không được tự export restricted data khi governance snapshot stale nếu policy fail-closed.

---

# 226. Device governance

614 devices có thể mang:

```text
data residency
classification
trust zone
```

---

# 227. GPU data governance

GPU buffers không cần per-buffer metadata mặc định.

Higher profile có thể attach:

```text
DataGovernanceRef
```

---

# 228. Media governance

616 media assets có thể dùng:

```text
classification
retention
residency
```

---

# 229. UI governance

619/621 document data có thể attach:

```text
DataAssetRef
```

---

# 230. Document export

622/621 export action phải query governance nếu document classified.

---

# 231. Package governance

613/625 package assets có:

```text
origin
license_metadata
classification
```

---

# 232. Model governance

630 model artifacts có:

```text
training_data_refs
model_revision
governance_fingerprint
```

---

# 233. Model training policy

639 quyết định whether training operation allowed.

640 supplies:

```text
training dataset classification
purpose
lineage
residency
```

---

# 234. Feature store

628 distributed data + 640 governance:

```text
FeatureSet
Feature
SourceLineage
Retention
Classification
```

---

# 235. Stream governance

634 event stream can have:

```text
topic classification
retention
residency
consumer restrictions
```

---

# 236. Event payload governance

Event schema may declare:

```text
@classification
@retention
@residency
```

---

# 237. Event retention

634 enforces storage retention.

640 defines governance requirement.

---

# 238. Log governance

602 logs may have:

```text
classification
retention
redaction
```

640 can provide metadata contracts.

---

# 239. Telemetry governance

633 telemetry may have:

```text
sensitivity
retention
aggregation
```

---

# 240. Secret governance

638 secret material is outside ordinary data governance.

640 may track:

```text
SecretRef
classification
retention metadata
```

but never secret plaintext.

---

# 241. Credential separation

Credential lifecycle remains 638.

Data governance does not own keys.

---

# 242. Encryption separation

610 owns cryptographic implementation.

640 declares requirements.

---

# 243. Storage separation

611 owns physical storage.

640 declares lifecycle.

---

# 244. Replication separation

628 owns replica mechanics.

640 constrains where/why replication may occur.

---

# 245. Deployment separation

636 owns rollout.

640 may block deployment if data governance requirements fail.

---

# 246. Policy separation

639 decides policy.

640 provides domain-specific governance facts and constraints.

---

# 247. Data governance decision

Conceptually:

```text
GovernanceContext
        ↓
639 Policy
        ↓
Decision
```

640 itself is not a second authorization engine.

---

# 248. Governance compiler

Compiler can validate:

```text
schema
classification
residency
retention
lineage declarations
```

---

# 249. Compile-time errors

Examples:

```text
unknown classification
invalid retention
invalid region
cyclic lineage declaration
unsupported transformation
```

---

# 250. Runtime validation

Dynamic assets still require runtime validation.

---

# 251. Static governance

For immutable assets:

```text
compile-time governance
```

may be enough.

---

# 252. Dynamic governance

For runtime-created datasets:

```text
runtime registration
```

required.

---

# 253. Default lifecycle

New asset:

```text
Declared
```

must transition:

```text
Active
```

only after required governance metadata exists.

---

# 254. Incomplete asset

Missing mandatory metadata:

```text
Incomplete
```

---

# 255. Restricted asset

Restricted state may prohibit:

```text
export
replication
training
```

according to policy.

---

# 256. Quarantine

Integrity mismatch:

```text
content_hash != expected
```

can trigger quarantine.

---

# 257. Provenance mismatch

If import claims:

```text
source = X
```

but signature/provenance invalid:

```text
UnknownProvenance
```

---

# 258. Provenance trust

Source trust can come from:

```text
638
627
610
```

---

# 259. Data manifest verification

Manifest:

```text
content_hash
schema
governance
signature
```

validated before admission.

---

# 260. Governance bundle signing

`.axdata` governance metadata can be signed.

---

# 261. Policy + governance fingerprint

Effective execution context may contain:

```text
schema_fingerprint
governance_fingerprint
policy_revision
credential_generation
```

---

# 262. Reproducible data processing

Processing result metadata can record:

```text
input revisions
governance revisions
policy revision
processor build
```

---

# 263. Reproducibility

Replay can reconstruct governance context without exposing payload.

---

# 264. Data processing receipt

```text
DataProcessingReceipt {
    execution_id
    inputs
    outputs
    transformations
    policy_revision
    governance_revision
}
```

---

# 265. Processing failure

If governance validation fails:

```text
RejectedBeforeProcessing
```

preferred over processing then discovering violation.

---

# 266. Post-processing validation

Output governance must also be validated.

---

# 267. Output classification

Transformation can specify:

```text
output_classification
```

or propagation rule.

---

# 268. Aggregation privacy boundary

Aggregation may reduce sensitivity but must not automatically lower classification.

---

# 269. De-identification

De-identification can be declared:

```text
Transformation {
    reversible = false
    removes_direct_identifiers = true
}
```

No automatic claim that data is legally anonymous.

---

# 270. Privacy-preserving transform

Optional provider boundary:

```text
DifferentialPrivacyProvider
```

if future module supplies it.

Not core mandatory.

---

# 271. Transformation provider

```text
DataTransformProvider {
    inspect
    validate
    execute
}
```

Execution remains capability controlled.

---

# 272. No arbitrary transform execution

Governance policy cannot dynamically load unknown transformation code.

---

# 273. Provider trust

Transformation provider must satisfy:

```text
publisher
signature
ABI
capabilities
```

through 603/638/623.

---

# 274. Data processor contract

Provider declares:

```text
input classifications
output classifications
supported regions
supported transformations
```

---

# 275. Contract validation

Input/output mismatch:

```text
DataContractViolation
```

---

# 276. Residency-aware scheduling

635 can use:

```text
asset.allowed_regions
```

as placement constraints.

---

# 277. Compute placement

630 can use same metadata for data locality.

---

# 278. Workflow placement

629 can ensure activities execute in allowed regions.

---

# 279. Service routing

631 can route to service instances capable of handling data classification.

---

# 280. Gateway routing

632 can prevent requests from routing data to forbidden destinations.

---

# 281. Event routing

634 can prevent replication/publication to unauthorized regions.

---

# 282. Global governance graph

```text
Data
 ↓
Service
 ↓
Workflow
 ↓
Compute
 ↓
Region
 ↓
Storage
```

640 provides governance relationships.

---

# 283. Impact graph

If region becomes unavailable:

```text
640
→ affected datasets
→ replicas
→ services
→ workflows
→ deployments
```

This is analysis only.

---

# 284. No automatic disaster decision

636/635 decide actual deployment/failover strategy.

640 supplies constraints.

---

# 285. Governance health

States:

```text
Healthy
Degraded
Violating
Unknown
```

---

# 286. Governance health reasons

```text
metadata_missing
residency_violation
retention_expired
lineage_broken
classification_unknown
processor_untrusted
```

---

# 287. Health metrics

633 receives governance status.

---

# 288. Governance alert

602/633 can generate:

```text
DataGovernanceAlert
```

---

# 289. Alert suppression

Deduplicate by:

```text
asset
violation_type
governance_revision
```

---

# 290. Large-scale catalog

For millions of assets:

```text
partition
index
incremental reconciliation
```

---

# 291. Incremental lineage

Only changed edges need propagation.

---

# 292. Incremental classification

Classification update should not scan all payloads.

---

# 293. Governance cache

Cache:

```text
asset governance snapshot
```

keyed by:

```text
asset generation
governance revision
```

---

# 294. Cache invalidation

Revision change invalidates.

---

# 295. No stale destructive decisions

Deletion eligibility must verify current governance revision before destructive action.

---

# 296. Two-phase deletion

Recommended:

```text
Eligibility
→
Commit deletion
```

---

# 297. Deletion token

```text
DeletionToken {
    asset
    generation
    governance_revision
    expires_at
}
```

---

# 298. Deletion fencing

If asset changes after token issuance:

```text
token invalid
```

---

# 299. Movement token

Same pattern:

```text
DataMovementToken
```

binds:

```text
source
destination
asset_generation
governance_revision
policy_revision
```

---

# 300. Final architecture

```text
                         ┌───────────────────────┐
                         │      Axiom Data       │
                         │       Assets          │
                         └───────────┬───────────┘
                                     │
                          ┌──────────▼──────────┐
                          │       BOOTSTRAP-640 │
                          │   Data Governance   │
                          ├─────────────────────┤
                          │ Classification      │
                          │ Ownership            │
                          │ Residency            │
                          │ Retention            │
                          │ Lifecycle            │
                          │ Lineage              │
                          │ Provenance            │
                          │ Privacy Metadata      │
                          │ Data Contracts        │
                          │ Transformation Rules  │
                          │ Sharing               │
                          │ Governance Registry   │
                          │ Impact Analysis       │
                          │ Drift Detection       │
                          └──────────┬──────────┘
                                     │
              ┌──────────────────────┼────────────────────────┐
              │                      │                        │
              ▼                      ▼                        ▼
            639                    628                      611
         Policy                  Distributed              Storage
         Decision                   Data                  Filesystem
              │                      │                        │
              └──────────────┬───────┴──────────────┬─────────┘
                             ▼                      ▼
                           635                    636
                         Placement              Deployment
                             │                      │
                             ▼                      ▼
                           631                    632
                         Services               Gateway
```

---

# 301. Architecture invariant

640 phải giữ nguyên chuỗi:

```text
Data Governance
      ↓
Policy Decision
      ↓
Capability Enforcement
      ↓
Execution
```

không được biến thành:

```text
Data Governance
      ↓
implicit authority
```

---

# 302. Acceptance target

Implementation target:

**≥420 acceptance criteria**

bao gồm:

- data asset identity;
- classification;
- field classification;
- ownership;
- stewardship;
- data contracts;
- residency;
- retention;
- deletion;
- archival;
- holds;
- lifecycle;
- lineage;
- provenance;
- transformation;
- masking;
- tokenization;
- purpose;
- sharing;
- export/import;
- cross-region movement;
- replication;
- backup;
- cache;
- distributed governance;
- federation;
- edge;
- offline governance;
- drift detection;
- impact analysis;
- schema integration;
- policy integration;
- capability integration;
- storage integration;
- distributed data integration;
- event integration;
- workflow integration;
- compute integration;
- audit;
- telemetry;
- security;
- fuzzing;
- failure recovery;
- scalability;
- deterministic behavior.

---

# 303. Profiles

```text
AXDATA_GOV_NONE
AXDATA_GOV_LOCAL
AXDATA_GOV_CLASSIFICATION
AXDATA_GOV_LINEAGE
AXDATA_GOV_RESIDENCY
AXDATA_GOV_RETENTION
AXDATA_GOV_PRIVACY
AXDATA_GOV_LIFECYCLE
AXDATA_GOV_DISTRIBUTED
AXDATA_GOV_FEDERATION
AXDATA_GOV_EDGE
AXDATA_GOV_FULL
```

---

# 304. Minimal profile

`AXDATA_GOV_NONE`:

Không link data governance runtime.

---

# 305. Embedded profile

```text
AXDATA_GOV_LOCAL
```

chỉ gồm:

```text
classification
retention
lifecycle
```

không cần distributed registry.

---

# 306. Distributed profile

`AXDATA_GOV_DISTRIBUTED` thêm:

```text
registry
lineage
replica governance
residency
watch
reconciliation
```

---

# 307. Full profile

`AXDATA_GOV_FULL`:

```text
classification
lineage
residency
retention
privacy
sharing
lifecycle
distributed registry
federation
edge
impact analysis
```

---

# 308. Runtime invariants

Các invariant quan trọng:

1. Asset ID không tự đổi khi governance metadata thay đổi.
2. Governance revision monotonic.
3. Governance snapshot immutable.
4. Unknown classification không tự biến thành Public.
5. Residency violation phải observable.
6. Retention không tự bỏ qua active hold.
7. Delete eligibility phải verify current revision.
8. Deletion token phải generation-bound.
9. Movement token phải destination-bound.
10. Replication phải kiểm tra residency.
11. Backup phải tuân residency.
12. Archive phải tuân residency.
13. Cache không được trở thành governance bypass.
14. Derived data phải có provenance.
15. Transformation phải versioned.
16. Lineage graph phải bounded.
17. Cross-tenant data movement phải explicit.
18. Data export phải governance-aware.
19. Classification không tự cấp capability.
20. 640 không override 603.
21. 640 không override 639.
22. 640 không trực tiếp điều khiển physical storage ngoài adapter.
23. 640 không chứa secret plaintext.
24. 640 không cần đọc payload để hoạt động.
25. Governance metadata phải auditable.
26. Historical governance revisions immutable.
27. Rollback tạo revision mới.
28. Stale governance không được dùng cho destructive operations.
29. Partial deletion phải observable.
30. Replica resurrection sau deletion phải bị chặn khi tombstone còn hiệu lực.
31. Lineage history có lifecycle.
32. Privacy metadata không tự tạo legal conclusion.
33. Classification inference không tự trở thành authoritative.
34. Data purpose phải explicit nếu policy yêu cầu.
35. Transformation provider phải trusted.
36. External export phải capability + policy controlled.
37. Governance failure semantics phải explicit.
38. Federation exceptions phải scoped.
39. Edge snapshots phải có expiry.
40. Offline governance phải có maximum validity.
41. Policy decisions vẫn thuộc 639.
42. Cryptographic operations vẫn thuộc 610.
43. Credential lifecycle vẫn thuộc 638.
44. Replica mechanics vẫn thuộc 628.
45. Deployment orchestration vẫn thuộc 636.
46. Placement vẫn thuộc 635.
47. Storage mechanics vẫn thuộc 611.
48. Audit không được chứa raw sensitive payload mặc định.
49. Metrics không được có unbounded sensitive cardinality.
50. Governance evaluator phải bounded.

---

# 309. Kết luận

BOOTSTRAP-640 hoàn thiện **Data Governance Plane** của Axiom.

Axiom giờ phân biệt rõ:

```text
611 = nơi lưu dữ liệu
612 = dữ liệu được encode thế nào
613 = dữ liệu/package được đóng gói thế nào
628 = dữ liệu được phân phối thế nào
634 = dữ liệu/event được truyền thế nào
639 = operation trên dữ liệu có được phép không
640 = dữ liệu phải được quản trị và tồn tại thế nào
```

Kiến trúc governance cuối cùng:

```text
                   DATA
                     │
             ┌───────▼────────┐
             │      640       │
             │   Governance   │
             └───────┬────────┘
                     │
      ┌──────────────┼─────────────────┐
      ▼              ▼                 ▼
 Classification   Lifecycle         Lineage
 Residency        Retention         Provenance
 Purpose          Deletion           Transform
 Sharing          Archive            Ownership
      │              │                 │
      └──────────────┼─────────────────┘
                     ▼
                    639
               Policy Decision
                     │
                    603
              Capability Boundary
                     │
                    EXECUTION
```

**BOOTSTRAP-640 = COMPLETE**

**Task tiếp theo: BOOTSTRAP-641 — Native Distributed Search, Indexing, Query Planning, Full-Text Search, Vector Search, Hybrid Retrieval & Query Execution Runtime 5.0.**
:::