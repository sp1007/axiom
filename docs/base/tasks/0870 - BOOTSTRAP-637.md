Tiếp tục với **BOOTSTRAP-637 — Native Distributed Configuration, Feature Flags, Dynamic Policy, Runtime Experimentation, Progressive Delivery Signals & Global Control Registry Runtime 5.0**.

:::writing{variant="document" id="58321" title="BOOTSTRAP-637 — Native Distributed Configuration, Feature Flags, Dynamic Policy, Runtime Experimentation, Progressive Delivery Signals & Global Control Registry Runtime 5.0"}
# BOOTSTRAP-637
## Native Distributed Configuration, Feature Flags, Dynamic Policy, Runtime Experimentation, Progressive Delivery Signals & Global Control Registry Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Dynamic Control Plane  
**Depends on:** BOOTSTRAP-600 through BOOTSTRAP-636  
**Primary dependencies:** 601, 603, 628, 631, 632, 633, 634, 635, 636

---

# 1. Mục tiêu

BOOTSTRAP-637 bổ sung một runtime native cho phép hệ thống Axiom thay đổi **behavior runtime** mà không cần rebuild hoặc redeploy binary.

Nó cung cấp:

- distributed configuration;
- runtime configuration;
- feature flags;
- kill switches;
- dynamic operational policies;
- experimentation;
- deterministic targeting;
- progressive-delivery signals;
- configuration rollout;
- configuration rollback;
- global control registry;
- federation-aware configuration;
- edge/offline configuration;
- configuration watches;
- configuration snapshots;
- revision history;
- drift detection;
- safe fallback.

637 **không** phải:

- local configuration system;
- secret manager;
- service discovery;
- deployment controller;
- security capability engine;
- arbitrary remote scripting engine.

Ranh giới:

```text
601  Local Application Configuration
       │
       ▼
637  Distributed Dynamic Control
       │
       ├── Configuration
       ├── Feature Flags
       ├── Runtime Policy
       ├── Experiments
       ├── Progressive Signals
       └── Global Control Registry
       │
       ├──────────────► 631 Service Runtime
       ├──────────────► 632 Gateway
       ├──────────────► 633 Telemetry
       ├──────────────► 634 Event Runtime
       └──────────────► 636 Deployment
```

---

# 2. Thiết kế nền tảng

637 sử dụng nguyên tắc:

> **Dynamic data, static code.**

Remote control có thể thay đổi dữ liệu điều khiển nhưng không được thay đổi executable semantics tùy ý.

Ví dụ hợp lệ:

```text
request_timeout = 3000ms
cache_ttl = 60s
feature_x = true
max_connections = 500
sampling_rate = 0.05
traffic_weight = 10%
```

Không hợp lệ:

```text
execute(remote_code)
load(remote_script)
eval(remote_expression_with_side_effects)
```

637 không tạo remote-code-execution primitive.

---

# 3. Phân biệt các hệ thống liên quan

| Hệ thống | Trách nhiệm |
|---|---|
| 601 | configuration local/bootstrap |
| 603 | security capability/policy |
| 628 | distributed replicated state |
| 631 | service discovery/routing |
| 633 | telemetry |
| 634 | event distribution |
| 635 | cluster control/consensus |
| 636 | deployment/rollout |
| 637 | runtime dynamic control |

Đặc biệt:

```text
601 = "ứng dụng được cấu hình như thế nào khi khởi động?"

637 = "ứng dụng đang được điều khiển như thế nào khi đang chạy?"
```

---

# 4. Architecture

637 gồm các tầng:

```text
                    ┌───────────────────────────────┐
                    │      Axiom Applications       │
                    └───────────────┬───────────────┘
                                    │
                          Typed Runtime API
                                    │
                    ┌───────────────▼───────────────┐
                    │       Config Runtime          │
                    ├───────────────────────────────┤
                    │ Feature Flag Runtime           │
                    │ Experiment Runtime             │
                    │ Dynamic Policy Runtime         │
                    │ Progressive Signal Runtime     │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │    Snapshot / Watch Layer      │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │   Distributed Control Store    │
                    └───────────────┬───────────────┘
                                    │
               ┌────────────────────┼───────────────────┐
               ▼                    ▼                   ▼
             628                  635                 Edge
        Replicated Data       Control Plane        Federation
```

---

# 5. Core identities

637 định nghĩa:

```text
ConfigKey
ConfigNamespace
ConfigValue
ConfigVersion
ConfigRevision
ConfigSnapshot
ConfigWatch
ConfigSource
ConfigTarget
ConfigSchema
ConfigPolicy
```

Feature:

```text
FeatureId
FeatureVersion
FeatureFlag<T>
FlagRule
FlagAssignment
FlagTarget
```

Experiment:

```text
ExperimentId
ExperimentVersion
VariantId
ExperimentAssignment
ExperimentExposure
ExperimentTarget
```

Registry:

```text
RegistryId
RegistryEntryId
RegistryRevision
RegistryNamespace
RegistryEntry
```

---

# 6. ConfigKey

```text
ConfigKey {
    namespace: ConfigNamespace
    name: String
}
```

Canonical key:

```text
global.database.timeout
cluster.eu-west.gateway.max_connections
service.orders.cache.ttl
tenant.example.feature.checkout
```

Key rules:

- UTF-8;
- case-sensitive;
- normalized;
- no ambiguous separators;
- maximum depth;
- bounded length;
- deterministic serialization.

---

# 7. Namespace hierarchy

637 hỗ trợ hierarchical scopes:

```text
global
federation
cluster
region
zone
service
service_instance
tenant
cohort
subject
```

Ví dụ:

```text
global
 └── region:europe
      └── cluster:prod-1
           └── service:orders
                └── instance:42
```

Không phải mọi loại configuration đều được phép ở mọi scope.

Mỗi schema khai báo:

```text
allowed_scopes
```

Ví dụ:

```text
database.pool_size
    global       ✓
    cluster      ✓
    service      ✓
    subject      ✗
```

---

# 8. Precedence

Precedence phải deterministic.

Mặc định:

```text
global
 < federation
 < region
 < cluster
 < zone
 < service
 < instance
 < tenant
 < cohort
 < subject
```

Nhưng schema có thể giới hạn scope.

Không được phép có hai giá trị cùng precedence mà không có conflict rule xác định.

---

# 9. Typed configuration

637 không sử dụng:

```text
get("timeout") -> String
```

làm API chính.

API chuẩn:

```text
get<T>(key: ConfigKey<T>) -> Result<T, ConfigError>
```

Ví dụ:

```text
let timeout: Duration =
    config.get(ConfigKeys.database_timeout)
```

Compiler biết kiểu:

```text
ConfigKey<Duration>
```

Do đó:

```text
config.get(ConfigKeys.database_timeout)
```

không cần runtime reflection.

---

# 10. ConfigSchema

Schema:

```text
ConfigSchema<T> {
    schema_id
    version
    fingerprint
    type
    default_value
    constraints
    allowed_scopes
    fallback_policy
    dynamic
}
```

Constraint có thể gồm:

```text
min
max
length
enum
pattern
required
nullable
```

Không cho phép constraint thực thi arbitrary code.

---

# 11. Validation

Mỗi thay đổi phải trải qua:

```text
Decode
   ↓
Schema validation
   ↓
Constraint validation
   ↓
Cross-field validation
   ↓
Policy validation
   ↓
Target validation
   ↓
Activation
```

Validation failure:

```text
new revision = rejected
active revision = unchanged
```

---

# 12. ConfigValue

ConfigValue có thể là:

```text
Bool
I8
I16
I32
I64
U8
U16
U32
U64
F32
F64
String
Bytes
Duration
Timestamp
Enum
Struct
Array
Map
SecretRef
```

Không lưu secret plaintext trong control-plane event history.

---

# 13. SecretRef

637 chỉ tham chiếu secret:

```text
SecretRef {
    secret_id
    version
}
```

Secret material được lấy qua 610/603.

Ví dụ:

```text
database.password = SecretRef("db/password", 17)
```

Không:

```text
database.password = "real-password"
```

trong distributed config store.

---

# 14. ConfigRevision

Mỗi thay đổi tạo revision mới:

```text
ConfigRevision {
    revision_id
    parent_revision
    author
    timestamp
    schema_fingerprint
    content_hash
    target
    reason
}
```

Revision immutable.

Không sửa revision cũ.

Rollback là:

```text
revision N
   ↓
new revision N+1
   ↓
content = revision N
```

Không rewrite lịch sử.

---

# 15. Compare-and-Swap

API:

```text
update(
    key,
    expected_revision,
    new_value
)
```

Nếu:

```text
expected_revision != current_revision
```

thì:

```text
Conflict
```

Không silently overwrite.

---

# 16. Atomic batch update

637 hỗ trợ:

```text
ConfigTransaction
```

Ví dụ:

```text
transaction {
    set(A, 10)
    set(B, 20)
    delete(C)
}
```

Activation:

```text
prepare
validate
commit
publish
```

Consumers chỉ nhìn thấy:

```text
revision N
```

hoặc:

```text
revision N+1
```

Không nhìn thấy trạng thái giữa transaction.

---

# 17. Snapshot

```text
ConfigSnapshot {
    generation
    revision
    created_at
    expires_at
    values
}
```

Application có thể giữ:

```text
snapshot = config.snapshot()
```

Sau đó đọc nhiều lần mà không cần lock/control-plane round trip.

---

# 18. Hot-path rule

Không khuyến khích:

```text
for item in items {
    if config.get(flag) {
        ...
    }
}
```

nếu `get()` tạo synchronization hoặc lookup control plane.

Thay vào đó:

```text
let snapshot = config.snapshot()

for item in items {
    if snapshot.feature_x {
        ...
    }
}
```

Hoặc:

```text
let flag = config.bind(FeatureFlags.feature_x)

for item in items {
    if flag.value() {
        ...
    }
}
```

Read path mục tiêu:

```text
O(1)
```

và không cần global mutex.

---

# 19. Watch

```text
ConfigWatch<T> {
    current()
    next()
    close()
}
```

Watch có thể theo:

```text
key
prefix
namespace
target
schema
```

Ví dụ:

```text
watch("service.orders.*")
```

---

# 20. Initial snapshot semantics

Watch luôn có:

```text
InitialSnapshot
```

sau đó:

```text
Change
Change
Change
...
```

Consumer không phải race giữa:

```text
read()
```

và:

```text
watch()
```

---

# 21. Revision monotonicity

Một watch stream phải đảm bảo:

```text
revision(n+1) > revision(n)
```

Nếu phát hiện gap:

```text
revision 100
revision 104
```

watcher phải:

```text
resync
```

trừ khi provider chứng minh được các revision bị bỏ qua không ảnh hưởng tới target.

---

# 22. Watch backpressure

Watch queue có giới hạn.

Khi overflow:

```text
GapDetected
```

thay vì vô hạn queue.

Consumer phải resync snapshot.

---

# 23. Change coalescing

Có thể coalesce:

```text
A=1
A=2
A=3
A=4
```

thành:

```text
A=4
```

chỉ khi semantics của watcher cho phép bỏ qua intermediate states.

Watcher yêu cầu every revision sẽ không được coalesce.

---

# 24. Stale configuration

Snapshot có:

```text
fresh
stale
expired
invalid
```

Một config schema khai báo:

```text
max_staleness
```

Ví dụ:

```text
max_staleness = 30s
```

---

# 25. Fallback policy

Mỗi dynamic configuration có thể khai báo:

```text
UseLastKnownGood
UseStaticDefault
FailOpen
FailClosed
RejectStartup
```

Ví dụ security-sensitive operational switch:

```text
FailClosed
```

Trong khi UI cosmetic feature:

```text
UseStaticDefault
```

---

# 26. Feature Flags

637 hỗ trợ:

```text
FeatureFlag<bool>
FeatureFlag<Enum>
FeatureFlag<String>
FeatureFlag<Struct>
FeatureFlag<Numeric>
```

Ví dụ:

```text
feature.new_renderer
feature.video_encoder
feature.experimental_pipeline
```

---

# 27. Flag states

Mỗi flag có:

```text
enabled
disabled
targeted
expired
blocked
```

`blocked` có priority cao hơn targeting.

---

# 28. Kill switch

Kill switch là flag đặc biệt:

```text
KillSwitch<T>
```

Properties:

```text
default_safe_value
activation_priority
scope
expiration
```

Mục tiêu:

```text
disable dangerous feature
```

mà không cần deployment.

---

# 29. Targeting

Targeting rule có thể kiểm tra:

```text
region
cluster
zone
service
service_version
release
instance
tenant
cohort
device_class
platform
architecture
declared_labels
```

Không tự động thu thập PII.

---

# 30. Declarative targeting language

Ví dụ:

```text
target {
    region == "asia"
    && service_version >= "5.2"
}
```

Nhưng expression chỉ là declarative AST.

Không được:

```text
target {
    execute(...)
}
```

Không có:

```text
network()
file()
spawn()
random()
clock()
```

trong targeting expression.

---

# 31. Expression complexity

Target expression phải có giới hạn:

```text
max_nodes
max_depth
max_string_length
max_collection_size
max_evaluation_steps
```

Nếu vượt:

```text
TargetEvaluationLimit
```

---

# 32. Percentage rollout

637 hỗ trợ:

```text
10%
25%
50%
100%
```

Assignment deterministic:

```text
bucket =
    hash(
        experiment_or_flag_id,
        subject_key,
        salt
    ) % 10000
```

Ví dụ:

```text
0..9999
```

với:

```text
10% = 0..999
```

---

# 33. Stable assignment

Nếu:

```text
experiment_id
subject_key
salt
```

không thay đổi thì assignment không thay đổi.

Điều này tránh:

```text
request 1 → variant A
request 2 → variant B
```

không chủ ý.

---

# 34. Allocation

Variant allocation:

```text
A = 5000
B = 3000
C = 2000
```

Tổng:

```text
10000
```

Nếu tổng không hợp lệ:

```text
InvalidAllocation
```

---

# 35. Experiment

```text
Experiment<T> {
    id
    version
    variants
    targeting
    allocation
    subject_key
    salt
    start
    end
}
```

Assignment:

```text
ExperimentAssignment {
    experiment_id
    experiment_version
    subject_key_hash
    variant_id
}
```

Không lưu raw subject identity nếu không cần.

---

# 36. Exposure event

Khi application thực sự sử dụng variant:

```text
ExperimentExposure {
    experiment_id
    variant_id
    assignment_revision
    timestamp
    context
}
```

Exposure gửi tới 633/634.

Assignment và exposure là hai sự kiện khác nhau.

---

# 37. Không tự động quyết định winner

Core 637 chỉ cung cấp:

```text
assignment
exposure
measurement hooks
```

Không tự động:

```text
declare_winner()
```

Không có built-in statistical decision engine.

Ứng dụng hoặc hệ thống phân tích bên ngoài có thể xử lý telemetry.

---

# 38. Mutually Exclusive Experiments

637 hỗ trợ:

```text
ExperimentGroup
```

Ví dụ:

```text
CheckoutExperiment
PaymentExperiment
```

Nếu cùng thuộc group:

```text
subject → chỉ nhận một experiment
```

Assignment deterministic.

---

# 39. Experiment lifecycle

```text
Draft
↓
Validated
↓
Scheduled
↓
Running
↓
Paused
↓
Completed
↓
Archived
```

Không xóa lịch sử assignment.

---

# 40. Dynamic Operational Policy

637 có thể điều khiển:

```text
timeouts
retry counts
retry backoff
circuit breaker thresholds
connection limits
cache TTL
worker counts
queue limits
sampling rates
log levels
compression level
batch size
event retention
scheduler tuning
```

Ví dụ:

```text
policy.orders.request_timeout = 2s
```

---

# 41. Security policy boundary

637 không tự cấp quyền.

Không hợp lệ:

```text
config.security.allow_filesystem = true
```

nếu việc đó tạo capability mới.

Authority vẫn thuộc:

```text
603 Security Runtime
```

637 chỉ có thể:

```text
reference_policy
request_policy_revision
```

và phải được 603 chấp thuận.

---

# 42. Dynamic policy precedence

Operational policy có precedence:

```text
platform
→ federation
→ cluster
→ region
→ service
→ instance
```

Nhưng schema có thể giới hạn.

Policy conflict phải được phát hiện trước activation.

---

# 43. PolicyRef

```text
PolicyRef<T> {
    policy_id
    revision
    schema_fingerprint
}
```

Runtime có thể bind:

```text
let timeout =
    policy.bind(Policies.http_timeout)
```

---

# 44. Progressive Delivery Signals

637 cung cấp signal engine để 636 sử dụng.

```text
ProgressiveSignal {
    signal_id
    source
    metric
    scope
    release_id
    revision
    variant
    window
    threshold
    state
}
```

States:

```text
Unknown
Healthy
Warning
Failing
Expired
Unavailable
```

---

# 45. Signal source

Nguồn có thể là:

```text
633 Metric
633 Trace-derived metric
634 Event count
631 Service health
632 Gateway health
636 deployment state
custom provider
```

---

# 46. Signal evaluation

Ví dụ:

```text
error_rate < 1%
p95_latency < 500ms
availability >= target
queue_lag < threshold
```

637 chỉ tính signal theo policy.

Nó không tự đưa ra deployment strategy.

---

# 47. Health gate integration

636 có thể khai báo:

```text
health_gate {
    signal = orders.error_rate
    condition = "< 0.01"
    consecutive_windows = 3
}
```

637 trả:

```text
Pass
Fail
Unknown
```

636 quyết định:

```text
continue
pause
rollback
```

theo deployment policy.

---

# 48. Global Control Registry

637 cung cấp registry metadata.

Registry có thể chứa:

```text
config schemas
feature flags
experiments
runtime policies
deployment references
cluster metadata
control capabilities
schema fingerprints
policy revisions
release metadata
```

Không chứa toàn bộ service-routing state.

---

# 49. Registry ≠ Service Discovery

631:

```text
Where is service X?
```

637:

```text
What control metadata applies to service X?
```

Hai hệ thống có thể liên kết:

```text
637 RegistryEntry
        │
        └── references → 631 ServiceId
```

nhưng không thay thế nhau.

---

# 50. RegistryEntry

```text
RegistryEntry {
    entry_id
    namespace
    kind
    owner
    version
    schema_fingerprint
    content_hash
    metadata
    capabilities
    revision
}
```

---

# 51. Registry namespaces

Ví dụ:

```text
config/
feature/
experiment/
policy/
service-metadata/
deployment/
cluster/
release/
schema/
```

---

# 52. Registry consistency

Metadata quan trọng có thể yêu cầu:

```text
Linearizable
```

Metadata thông thường có thể dùng:

```text
Causal
Session
Eventual
```

637 không tự định nghĩa distributed consistency mới.

Nó sử dụng semantics từ 628/635.

---

# 53. Provider architecture

```text
ConfigProvider
RegistryProvider
FeatureProvider
ExperimentProvider
PolicyProvider
SignalProvider
```

Providers:

```text
LocalMemory
LocalFile
Embedded
DistributedStore
ClusterControlStore
EdgeReplica
RemoteRegistry
TestProvider
```

Không provider nào được phép bypass security 603.

---

# 54. Bootstrap

Startup:

```text
601 bootstrap
      ↓
637 provider discovery
      ↓
last-known-good snapshot
      ↓
distributed refresh
      ↓
validation
      ↓
atomic activation
```

Nếu control plane unavailable:

```text
last-known-good
```

được sử dụng theo fallback policy.

---

# 55. Persistent local cache

637 có thể lưu:

```text
snapshot
revision
schema
expiry
signature
provider identity
```

qua 611/612/613.

Cache phải atomic.

---

# 56. Signed snapshot

Edge/offline deployment có thể sử dụng:

```text
SignedConfigSnapshot
```

Signature verification qua 610.

Snapshot chứa:

```text
content_hash
schema_fingerprint
revision
issuer
expiry
signature
```

---

# 57. Edge mode

Edge node có thể hoạt động:

```text
online
degraded
offline
```

Offline:

```text
use signed snapshot
```

Không được nhận dynamic control không xác thực.

---

# 58. Delegated authority

Federated/edge control có:

```text
DelegatedControlScope {
    scope
    permissions
    issuer
    expiry
    fencing_epoch
}
```

Ví dụ:

```text
edge-cluster-17
    allowed:
        feature.read
        policy.read
        config.activate
    expires:
        T
```

---

# 59. Fencing

Nếu edge controller cũ vẫn hoạt động sau failover:

```text
old_epoch < current_epoch
```

thì write bị reject.

Điều này ngăn stale controller ghi đè control state.

---

# 60. Multi-cluster configuration

Federation có:

```text
global config
regional overrides
cluster overrides
edge overrides
```

Ví dụ:

```text
global.timeout = 5s

asia.timeout = 3s

cluster-a.timeout = 2s
```

Resolution deterministic.

---

# 61. Drift detection

637 so sánh:

```text
desired revision
observed revision
active revision
```

Trạng thái:

```text
Converged
Pending
Drifted
Rejected
Stale
Unavailable
```

---

# 62. Reconciliation

Controller:

```text
observe
compare
validate
apply
verify
```

Không loop vô hạn.

Nếu repeated failure:

```text
Backoff
```

và phát event.

---

# 63. Configuration rollout

Một config change có thể rollout:

```text
All
Cluster
Region
Percentage
Canary
Wave
Target
```

Ví dụ:

```text
region:asia → 10%
region:asia → 25%
region:asia → 50%
region:asia → 100%
```

---

# 64. Rollout revision

```text
ConfigRollout {
    rollout_id
    source_revision
    target_revision
    strategy
    targets
    health_gates
    pause_policy
    rollback_policy
}
```

637 thực thi control-plane rollout.

636 vẫn là authority cho deployment artifact rollout.

---

# 65. Rollback

Rollback phải tạo revision mới:

```text
R1
R2
R3
R4 = content(R2)
```

History:

```text
R1 → R2 → R3 → R4
```

Không:

```text
delete R3
```

---

# 66. Safe activation

Activation:

```text
prepare
↓
schema validation
↓
policy validation
↓
dependency validation
↓
target validation
↓
health precondition
↓
commit
↓
publish
```

---

# 67. Dependency graph

Config có thể khai báo:

```text
depends_on
```

Ví dụ:

```text
feature.new_api
    depends_on:
        policy.api_version
```

Dependency graph phải acyclic nếu schema yêu cầu ordering.

Cycle:

```text
ConfigDependencyCycle
```

---

# 68. Runtime compatibility

Mỗi dynamic value có:

```text
min_runtime_version
max_runtime_version
schema_fingerprint
```

Node không hiểu schema không được activate value.

---

# 69. Schema migration

Config schema migration:

```text
v1 → v2
```

phải là explicit migration.

Không tự động đoán:

```text
String → Duration
```

nếu conversion không được khai báo.

---

# 70. Config history

History API:

```text
list_revisions(key)
get_revision(key, revision)
diff(revision_a, revision_b)
```

Diff phải typed:

```text
added
removed
changed
unchanged
```

---

# 71. Audit

Mỗi mutation tạo audit event:

```text
ConfigChanged
ConfigRejected
ConfigActivated
ConfigRolledBack
FlagChanged
ExperimentStarted
ExperimentStopped
PolicyChanged
RegistryChanged
```

Audit tích hợp 602/633/634.

---

# 72. Author identity

Mutation metadata:

```text
actor_id
publisher_id
service_id
session_id
reason
source
```

Identity từ 627/603.

---

# 73. Authorization

Permissions:

```text
config.read
config.write
config.activate
config.rollback
config.admin

feature.read
feature.write
feature.admin

experiment.read
experiment.write
experiment.admin

policy.read
policy.write
policy.admin

registry.read
registry.write
registry.admin
```

Capability checks phải xảy ra trước mutation.

---

# 74. Tenant isolation

Tenant-scoped configuration không được đọc chéo tenant.

Registry key resolution phải kiểm tra:

```text
tenant_scope
capability
namespace
```

---

# 75. Privacy

Targeting metadata không mặc định thu thập:

```text
name
email
phone
address
raw identifiers
```

Subject key có thể là:

```text
opaque stable identifier
```

---

# 76. Data minimization

Experiment exposure chỉ ghi những field cần thiết.

Schema có:

```text
privacy_classification
```

Ví dụ:

```text
Public
Internal
Sensitive
SecretReference
```

---

# 77. Secret handling

Không được log:

```text
SecretRef resolved value
```

Không đưa secret vào:

```text
experiment exposure
config history
registry metadata
diagnostic event
```

---

# 78. Watch security

Watch permission được kiểm tra trước subscription.

Nếu quyền bị revoke:

```text
WatchRevoked
```

và stream đóng.

---

# 79. Capability attenuation

Một service có:

```text
config.read(service.orders)
```

không thể suy ra:

```text
config.write(global)
```

Authority không được nâng cấp qua 637.

---

# 80. Event integration

637 phát events:

```text
ConfigRevisionCreated
ConfigActivated
ConfigRollback
FlagChanged
ExperimentExposure
PolicyChanged
RegistryUpdated
SignalChanged
```

634 vận chuyển.

---

# 81. Telemetry integration

633 nhận:

```text
config_revision
flag_id
experiment_id
variant_id
policy_revision
signal_id
```

nhưng không raw secret.

---

# 82. Trace correlation

Runtime request có thể gắn:

```text
config_generation
flag_generation
policy_generation
```

để debug:

```text
request failed
    ↓
which runtime configuration was active?
```

---

# 83. Deterministic evaluation

Flag evaluation phải deterministic với cùng:

```text
snapshot
target attributes
subject key
```

Kết quả phải giống nhau.

---

# 84. No hidden randomness

Không sử dụng runtime RNG cho percentage assignment.

Sử dụng deterministic hash.

Điều này bảo đảm:

```text
restart
reconnect
different node
```

không thay đổi assignment ngoài ý muốn.

---

# 85. Time-dependent rules

Expiration sử dụng timestamp được cung cấp bởi runtime policy.

Targeting expression không được gọi arbitrary clock.

Compiler/runtime cung cấp:

```text
evaluation_time
```

một lần cho evaluation.

---

# 86. Atomic snapshot evaluation

Một request nên dùng cùng snapshot:

```text
snapshot_generation = 500
```

thay vì:

```text
flag A @ 500
flag B @ 501
policy C @ 502
```

nếu operation yêu cầu consistency.

API:

```text
ControlSnapshot
```

cho phép bind nhiều values.

---

# 87. ControlSnapshot

```text
ControlSnapshot {
    config_generation
    flag_generation
    policy_generation
    registry_generation
}
```

Application có thể tạo:

```text
let control = controls.snapshot()
```

và evaluate toàn bộ behavior trên cùng generation boundary.

---

# 88. Performance

Read path mục tiêu:

```text
O(1)
```

cho key lookup.

Không:

```text
network RPC
```

trong normal read.

Không:

```text
global mutex
```

trong normal read.

Update path có thể chậm hơn nhưng phải bounded.

---

# 89. Snapshot implementation

Native implementation ưu tiên:

```text
immutable snapshot
atomic pointer/reference swap
generation counter
```

Readers:

```text
lock-free
```

hoặc platform-equivalent.

Memory reclamation sử dụng lifetime strategy của Axiom runtime, không yêu cầu GC.

---

# 90. Memory reclamation

Snapshot cũ được giữ cho đến khi không còn reader.

Có thể dùng:

```text
epoch reclamation
hazard pointer
RCU-like provider
reference-counted immutable object
```

provider lựa chọn chiến lược.

---

# 91. No mandatory GC

637 không yêu cầu:

```text
garbage collector
```

Dynamic control runtime phải hoạt động với ownership/lifetime model của Axiom.

---

# 92. Failure modes

Provider failure:

```text
Unavailable
```

Schema failure:

```text
InvalidSchema
```

Signature failure:

```text
InvalidSignature
```

Revision conflict:

```text
Conflict
```

Target failure:

```text
TargetUnavailable
```

Watch overflow:

```text
ResyncRequired
```

---

# 93. Control-plane outage

Nếu distributed store unavailable:

```text
last-known-good
```

được dùng theo policy.

Không được mặc định:

```text
disable all application behavior
```

và cũng không được mặc định:

```text
accept arbitrary stale data forever
```

---

# 94. Expiration

Dynamic values có thể có:

```text
expires_at
```

Sau expiry:

```text
fallback_policy
```

được áp dụng.

Đặc biệt feature flag temporary phải có expiry để tránh flag tồn tại vô hạn.

---

# 95. Feature lifecycle

```text
Defined
↓
Disabled
↓
Canary
↓
Partial
↓
Enabled
↓
Deprecated
↓
Removed
```

Runtime không tự xóa flag.

Compiler/tooling có thể cảnh báo flag stale.

---

# 96. Flag debt detection

Compiler có thể phát hiện:

```text
flag declared
but no references
```

hoặc:

```text
flag expired
```

và sinh warning.

Không tự động xóa source code.

---

# 97. Registry garbage collection

Registry entry có lifecycle:

```text
Active
Deprecated
Archived
Deleted
```

Deletion chỉ khi retention policy cho phép.

---

# 98. Global control registry consistency

Control registry không trở thành universal database.

Mỗi entry có:

```text
owner
source_of_truth
```

637 chỉ lưu metadata/control state phù hợp.

---

# 99. Source-of-truth rule

Ví dụ:

```text
Service endpoint
    source = 631

Deployment release
    source = 636

Security capability
    source = 603

Metric definition
    source = 633

Dynamic config
    source = 637
```

Registry có thể tham chiếu nhưng không được âm thầm duplicate authoritative state.

---

# 100. Compiler annotations

637 hỗ trợ:

```text
@config
@config_schema
@dynamic
@feature
@flag
@experiment
@variant
@target
@runtime_policy
@watch
@signal
@registry
```

---

# 101. Example

```text
@config(
    key = "orders.request_timeout",
    default = 2s,
    dynamic = true
)
let request_timeout: Duration
```

Compiler sinh:

```text
ConfigKey<Duration>
```

---

# 102. Feature example

```text
@feature("new_checkout")
let new_checkout: FeatureFlag<bool>
```

Usage:

```text
if new_checkout.enabled() {
    checkout_v2()
} else {
    checkout_v1()
}
```

---

# 103. Experiment example

```text
@experiment("checkout_layout")
variants {
    control = 5000
    compact = 5000
}
```

Application:

```text
match experiment.assign(subject) {
    control => render_control(),
    compact => render_compact()
}
```

---

# 104. Policy example

```text
@runtime_policy("http.timeout")
let timeout: Duration
```

Usage:

```text
client.set_timeout(timeout.value())
```

---

# 105. Watch example

```text
let watch =
    config.watch(ConfigKeys.cache_ttl)

while let change = watch.next() {
    cache.update_ttl(change.value)
}
```

Watch processing chạy async.

---

# 106. Generated metadata

Compiler sinh:

```text
.axconfig
.axflag
.axexperiment
.axpolicy
.axsignal
.axregistry
```

Metadata gồm:

```text
schema
type
version
fingerprint
scope
fallback
capabilities
dependencies
```

---

# 107. CLI

Axiom toolchain hỗ trợ:

```text
axiom config get
axiom config set
axiom config diff
axiom config history
axiom config rollback

axiom flag list
axiom flag inspect
axiom flag enable
axiom flag disable

axiom experiment list
axiom experiment inspect
axiom experiment assign

axiom policy list
axiom policy inspect

axiom signal list
axiom signal inspect

axiom registry list
axiom registry inspect
```

Mutation command phải yêu cầu capability phù hợp.

---

# 108. Dry run

Trước activation:

```text
axiom config plan
```

trả:

```text
affected services
affected clusters
schema validation
dependency changes
policy changes
expected rollout
health gates
```

Không thay đổi runtime.

---

# 109. Diff

Diff hiển thị:

```text
old revision
new revision
added
removed
changed
scope
risk metadata
compatibility
```

Không hiển thị secret material.

---

# 110. Rollout simulator

637 cung cấp deterministic simulator:

```text
targets
revision
strategy
failure policy
health signals
```

Output:

```text
planned activations
dependencies
rollback path
```

---

# 111. Interaction with 636

636:

```text
deployment intent
```

637:

```text
runtime control
```

Ví dụ:

```text
636 deploy version 5
637 feature.new_engine = 5%
```

Sau khi health gate pass:

```text
637 = 25%
```

Sau đó:

```text
637 = 100%
```

636 có thể điều phối artifact rollout; 637 điều khiển runtime behavior.

---

# 112. Interaction with 632

Gateway có thể nhận:

```text
traffic policy
```

từ 637.

Ví dụ:

```text
feature.checkout_v2 = 10%
```

632 thực thi traffic routing.

637 không trực tiếp xử lý packet/request.

---

# 113. Interaction with 631

Service runtime nhận:

```text
timeout
retry policy
connection limit
feature flags
```

631 vẫn thực thi service calls.

---

# 114. Interaction with 635

635 cung cấp:

```text
cluster identity
leader epoch
control-plane consistency
fencing
```

637 không tự tạo consensus protocol mới.

---

# 115. Interaction with 628

628 cung cấp:

```text
replication
consistency
snapshot
version vectors
distributed state
```

637 sử dụng thay vì duplicate distributed storage engine.

---

# 116. Interaction with 634

634 cung cấp:

```text
change propagation
event delivery
exposure events
```

637 không cần tự xây broker thứ hai.

---

# 117. Federation

Federation hierarchy:

```text
Global Control
      │
      ├── Region Control
      │      ├── Cluster A
      │      └── Cluster B
      │
      └── Edge Control
```

Mỗi authority có:

```text
scope
epoch
expiry
```

---

# 118. Conflict resolution

Nếu local override conflict global:

```text
scope precedence
```

được áp dụng.

Nếu hai authority cùng precedence:

```text
Conflict
```

Không dùng:

```text
last writer wins
```

một cách mặc định cho policy-sensitive control.

---

# 119. Clock skew

Không dùng wall-clock timestamp làm sole ordering primitive.

Ordering dựa trên:

```text
revision
epoch
sequence
```

Timestamp chỉ là metadata.

---

# 120. Transaction boundary

637 không cung cấp universal distributed transaction.

Ví dụ:

```text
config update
+
service deployment
+
gateway traffic switch
```

không phải một atomic transaction toàn hệ thống.

Thay vào đó:

```text
636 orchestration
637 control revision
631 execution
632 traffic
633 observation
```

---

# 121. Progressive rollout state

637 có:

```text
Prepared
Canary
Partial
Expanded
Complete
Paused
Failed
RollbackRequested
```

636 vẫn quyết định deployment state cuối cùng.

---

# 122. Health evaluation

Signal evaluator phải phân biệt:

```text
Pass
Fail
InsufficientData
Stale
Unavailable
```

Không biến:

```text
missing telemetry
```

thành:

```text
healthy
```

một cách mặc định.

---

# 123. Threshold semantics

Threshold phải khai báo:

```text
operator
threshold
window
aggregation
minimum_samples
```

Ví dụ:

```text
p95_latency
<
500ms
over 5m
minimum_samples=1000
```

---

# 124. Aggregation

Supported:

```text
count
sum
average
min
max
rate
ratio
percentile
error_rate
```

Percentile phải chỉ rõ algorithm/accuracy boundary nếu approximate.

---

# 125. Signal freshness

Signal có:

```text
observed_at
expires_at
source_revision
```

Expired signal:

```text
Unknown
```

không tự động Pass.

---

# 126. Runtime policy safety

Operational policy phải khai báo:

```text
safe_min
safe_max
```

nếu applicable.

Ví dụ:

```text
worker_count:
    min = 1
    max = 1024
```

---

# 127. Dynamic resource controls

637 có thể thay đổi:

```text
worker target
queue capacity
connection limit
cache size
```

nhưng 606 vẫn là authority cuối cùng về resource quota.

637 không thể vượt:

```text
hard resource limit
```

---

# 128. Resource interaction

Nếu:

```text
config.worker_count = 1000
```

nhưng 606:

```text
max_threads = 100
```

runtime phải clamp/reject theo policy.

637 không bypass 606.

---

# 129. Configuration validation against runtime

Activation có thể kiểm tra:

```text
schema
security
resource limits
platform support
service version
deployment version
```

Nếu incompatible:

```text
Rejected
```

---

# 130. Platform compatibility

Dynamic config có thể target:

```text
Windows
Linux
macOS
Android
iOS
WASM
Embedded
```

Schema có thể khai báo:

```text
supported_platforms
```

---

# 131. WASM

WASM host có thể cung cấp:

```text
static snapshot
dynamic host callback
```

637 không giả định filesystem/network availability.

---

# 132. Mobile

Mobile phải hỗ trợ:

```text
offline snapshot
battery-aware refresh
background refresh restrictions
```

Không yêu cầu persistent network connection.

---

# 133. Embedded

Embedded profile ưu tiên:

```text
static config
signed snapshot
bounded memory
no distributed client
```

---

# 134. Security model

637 security layers:

```text
Authentication
Authorization
Capability
Namespace isolation
Schema restrictions
Audit
Signature verification
Fencing
Expiry
```

---

# 135. Threat model

637 phải chống:

```text
unauthorized mutation
stale writer
rollback abuse
configuration injection
schema confusion
targeting bypass
tenant leakage
secret leakage
watch amplification
control-plane DoS
unbounded expressions
```

---

# 136. Replay protection

Signed snapshots và mutations có:

```text
revision
epoch
expiry
issuer
```

Old revision không thể được replay nếu policy yêu cầu monotonic activation.

---

# 137. Emergency override

Có thể có:

```text
EmergencyControl
```

nhưng phải:

```text
authenticated
authorized
audited
scoped
time-bounded
```

Không có hidden backdoor.

---

# 138. Break-glass

Break-glass authority:

```text
explicit capability
short TTL
mandatory audit
optional dual authorization
```

---

# 139. Control-plane partition

Khi network partition:

```text
existing snapshot → continue
new control → unavailable
```

theo fallback policy.

Không tự tạo divergent authority nếu policy không cho phép.

---

# 140. Offline writes

Offline writes chỉ được phép nếu namespace hỗ trợ:

```text
offline_write = true
```

và phải có:

```text
delegated authority
expiry
fencing epoch
```

---

# 141. Reconnect

Khi reconnect:

```text
validate authority
compare revision
detect conflict
reconcile
activate
```

Không blind overwrite.

---

# 142. Configuration conflict

Conflict object:

```text
ConfigConflict {
    key
    local_revision
    remote_revision
    authority
    resolution_policy
}
```

Resolution:

```text
AcceptRemote
KeepLocal
Merge
Manual
Reject
```

Merge chỉ khi schema hỗ trợ deterministic merge.

---

# 143. Merge safety

Không merge arbitrary structured config.

Schema có thể khai báo:

```text
merge_strategy
```

Ví dụ:

```text
SetUnion
MapMerge
NumericMax
NumericMin
Reject
```

---

# 144. Deterministic map merge

Map merge phải có:

```text
stable key ordering
stable conflict rule
```

để tất cả replicas tạo cùng kết quả.

---

# 145. Config snapshots and checkpoints

600 checkpoint có thể tham chiếu:

```text
control_generation
config_revision
flag_revision
policy_revision
```

nhằm tái hiện runtime state.

---

# 146. Crash recovery

Sau crash:

```text
load last known good
verify schema
verify signature
restore snapshot
reconnect provider
resync
```

---

# 147. Diagnostics

602 ghi:

```text
config activation latency
watch lag
revision gap
provider errors
snapshot age
evaluation latency
flag evaluation count
experiment exposure count
policy rejection
```

---

# 148. Tracing

633 trace span:

```text
control.lookup
control.evaluate
config.activate
flag.evaluate
experiment.assign
policy.resolve
registry.lookup
```

---

# 149. Metrics

Core metrics:

```text
config_read_total
config_activation_total
config_rejection_total
config_revision_lag
watch_resync_total
watch_queue_depth
flag_evaluation_total
experiment_assignment_total
experiment_exposure_total
policy_resolution_total
registry_lookup_total
snapshot_age
```

---

# 150. Cardinality protection

Không tạo metric label trực tiếp từ arbitrary:

```text
subject_id
tenant_id
config_key
```

nếu schema không cho phép.

633 cardinality policy vẫn có authority.

---

# 151. Resource limits

637 phải giới hạn:

```text
keys
namespaces
snapshot_size
revision_size
watchers
watch_queue
target_expression_size
experiment_variants
registry_entries
history_retention
```

---

# 152. DoS protection

Một client không được tạo:

```text
1,000,000 watches
```

hoặc:

```text
unbounded config transactions
```

Quota tích hợp 606.

---

# 153. Watch multiplexing

Runtime có thể multiplex:

```text
many consumers
```

qua một provider stream.

Không yêu cầu một network connection cho mỗi watcher.

---

# 154. Local event dispatch

Nếu nhiều local subscribers:

```text
provider update
    ↓
snapshot swap
    ↓
local dispatcher
    ├── subscriber A
    ├── subscriber B
    └── subscriber C
```

Dispatcher phải bounded.

---

# 155. Backpressure

Slow subscriber:

```text
does not block snapshot activation
```

Subscriber bị:

```text
coalesced
```

hoặc:

```text
resync required
```

---

# 156. Read isolation

Config read không được block:

```text
deployment controller
registry write
watch delivery
```

---

# 157. Write isolation

Large transaction không được giữ global lock trong toàn bộ validation.

Pipeline:

```text
parse
validate
prepare
commit
publish
```

---

# 158. Compiler optimization

Compiler có thể constant-fold static configuration:

```text
@config(dynamic=false)
```

Dynamic config không được constant-fold.

---

# 159. Dead stripping

Nếu application không sử dụng:

```text
experiments
feature flags
registry
```

thì tương ứng runtime code phải được loại bỏ.

---

# 160. Minimal binary

Ví dụ:

```text
AXCONFIG_LOCAL
```

không kéo theo:

```text
AXEXPERIMENT
AXFEDERATION
AXREGISTRY
```

nếu không dùng.

---

# 161. Profiles

```text
AXCONFIG_NONE
AXCONFIG_LOCAL
AXCONFIG_DYNAMIC
AXCONFIG_FEATURE
AXCONFIG_EXPERIMENT
AXCONFIG_POLICY
AXCONFIG_FEDERATION
AXCONFIG_EDGE
AXCONFIG_FULL
```

---

# 162. AXCONFIG_NONE

Application không có dynamic control runtime.

Compiler không link 637 runtime.

---

# 163. AXCONFIG_LOCAL

Chỉ:

```text
local immutable snapshot
```

Không distributed provider.

---

# 164. AXCONFIG_DYNAMIC

Bao gồm:

```text
remote config
watch
revision
rollback
```

---

# 165. AXCONFIG_FEATURE

Thêm:

```text
feature flags
targeting
percentage rollout
kill switches
```

---

# 166. AXCONFIG_EXPERIMENT

Thêm:

```text
experiments
variants
assignment
exposure
```

---

# 167. AXCONFIG_POLICY

Thêm:

```text
dynamic operational policies
```

---

# 168. AXCONFIG_FEDERATION

Thêm:

```text
global
region
cluster
edge
```

---

# 169. AXCONFIG_EDGE

Thêm:

```text
signed snapshots
offline mode
delegated control
fencing
```

---

# 170. AXCONFIG_FULL

Toàn bộ 637.

---

# 171. Public API

Core:

```text
ConfigRegistry
ConfigNamespace
ConfigSnapshot
ConfigWatch<T>
ConfigSchema<T>
ConfigKey<T>
ConfigRevision
ConfigTransaction
ConfigTarget
ConfigProvider
```

Feature:

```text
FeatureFlag<T>
FeatureProvider
FlagRule
FlagAssignment
```

Experiment:

```text
Experiment
ExperimentGroup
Variant
ExperimentAssignment
ExperimentExposure
```

Policy:

```text
RuntimePolicy<T>
PolicyRef<T>
PolicyProvider
```

Signal:

```text
ProgressiveSignal
SignalEvaluator
SignalWindow
HealthGateInput
```

Registry:

```text
GlobalRegistry
RegistryEntry
RegistryNamespace
RegistryProvider
```

---

# 172. Struct-only API

Axiom không cần class hierarchy.

Ví dụ:

```text
struct ConfigRegistry {
    provider: ConfigProvider
}

fn ConfigRegistry.get<T>(
    self: &ConfigRegistry,
    key: ConfigKey<T>
) -> Result<T, ConfigError>
```

Các method đều là ordinary functions với receiver đầu tiên.

---

# 173. Override mechanism

Provider specialization dùng trait/implementation:

```text
trait ConfigProvider {
    fn snapshot(...)
    fn update(...)
    fn watch(...)
}
```

Backend:

```text
impl DistributedConfigProvider for ConfigProvider
impl EdgeConfigProvider for ConfigProvider
impl TestConfigProvider for ConfigProvider
```

Compiler dispatch có thể:

```text
static
devirtualized
monomorphized
```

khi biết implementation.

---

# 174. FFI boundary

Provider ABI phải stable.

External control systems có thể được adapter:

```text
ExternalConfigProvider
```

nhưng Axiom core không phụ thuộc chúng.

---

# 175. External systems

Optional adapters có thể kết nối:

```text
external configuration service
external feature flag system
external registry
external telemetry
```

Không phải dependency bắt buộc.

---

# 176. TestProvider

Test provider phải hỗ trợ:

```text
inject revision
inject conflict
inject stale snapshot
inject watch gap
inject provider failure
inject invalid schema
inject signature failure
```

---

# 177. Deterministic test clock

Testing có:

```text
FakeClock
```

cho:

```text
expiry
TTL
experiment schedule
signal windows
```

---

# 178. Deterministic hashing

Test có thể inject:

```text
HashProvider
```

để verify percentage allocation.

---

# 179. Property testing

Properties:

```text
same subject → same assignment
same snapshot → same evaluation
revision monotonicity
rollback preserves history
invalid config never activates
expired snapshot follows fallback
unauthorized write always fails
```

---

# 180. Fuzzing

Fuzz:

```text
config parser
schema parser
target AST
allocation parser
registry metadata
snapshot decoder
watch stream
transaction
signature envelope
```

---

# 181. Fault injection

Simulate:

```text
network partition
provider crash
leader change
stale replica
clock skew
watch overflow
partial rollout
signature failure
disk failure
process restart
```

---

# 182. Security testing

Tests:

```text
capability escalation
tenant isolation
scope escape
stale writer
replay
tampering
secret leakage
policy bypass
expression injection
```

---

# 183. Compatibility testing

Test:

```text
schema v1 ↔ v2
runtime old ↔ new
provider old ↔ new
federation old ↔ new
edge offline ↔ reconnect
```

---

# 184. Performance targets

Target:

```text
normal local config read = O(1)
```

Hot read:

```text
no network
no global lock
```

Snapshot activation:

```text
atomic
```

Watch delivery:

```text
bounded
```

Target evaluation:

```text
bounded
```

---

# 185. Binary-size target

Unused subsystems must dead-strip.

Application chỉ dùng:

```text
FeatureFlag<bool>
```

không kéo toàn bộ:

```text
Experiment
Federation
Registry
Edge
```

---

# 186. Availability model

Data plane không được phụ thuộc control plane cho mỗi request.

Nguyên tắc:

```text
control plane updates behavior
data plane executes behavior
```

---

# 187. Control-plane failure isolation

Control-plane failure không được làm application data plane crash chỉ vì:

```text
config provider unavailable
```

trừ khi schema explicit:

```text
fail_closed
```

---

# 188. Safe defaults

Mọi dynamic configuration quan trọng phải có:

```text
static default
```

hoặc:

```text
explicit startup failure policy
```

Không được implicit undefined behavior.

---

# 189. Runtime generation

Mỗi activation tăng:

```text
generation
```

Ví dụ:

```text
generation 101
generation 102
generation 103
```

Logs/traces có thể tham chiếu generation.

---

# 190. Reproducibility

Bug report có thể ghi:

```text
build_id
config_generation
config_revision
flag_generation
policy_generation
deployment_revision
cluster_generation
```

để tái hiện behavior.

---

# 191. Control bundle

637 hỗ trợ export:

```text
.axcontrol
```

chứa:

```text
schemas
snapshots
revisions
flags
policies
experiments
registry metadata
signatures
```

Secret material bị loại bỏ.

---

# 192. Replay

Developer có thể replay:

```text
ControlSnapshot
+
request inputs
```

để tái hiện flag/policy behavior.

---

# 193. AI-readable metadata

`.axconfig` phải chứa machine-readable:

```text
schema
scope
dependencies
fallback
security
revision
activation rules
```

AI tooling có thể hiểu:

```text
what controls this behavior?
```

---

# 194. Explain API

637 cung cấp:

```text
explain(key, context)
```

Output:

```text
source
scope
revision
precedence
target rule
selected value
fallback
```

Không expose secret.

---

# 195. Explain feature

```text
explain_flag(flag, subject)
```

Ví dụ:

```text
flag = new_checkout
snapshot = 102
target = region:asia
bucket = 731
allocation = 0..999
result = enabled
reason = percentage_rule
```

---

# 196. Explain policy

```text
explain_policy(timeout, service)
```

cho biết:

```text
global = 10s
cluster = 5s
service = 2s
effective = 2s
```

---

# 197. Explain registry

```text
registry.explain(entry)
```

cho biết:

```text
owner
source_of_truth
revision
scope
authority
```

---

# 198. Operational safety

637 phải ưu tiên:

```text
determinism
boundedness
auditability
rollback
least authority
safe defaults
```

thay vì:

```text
maximum dynamic flexibility
```

---

# 199. Không tạo hidden programming language

Targeting không phải programming language.

Experiment rules không phải scripting.

Dynamic policy không phải arbitrary expression evaluator.

Mục tiêu:

```text
declarative + bounded + deterministic
```

---

# 200. Architecture invariant

637 phải giữ các invariant:

1. Dynamic config không thực thi arbitrary code.
2. Security authority thuộc 603.
3. Deployment authority thuộc 636.
4. Service routing authority thuộc 631/632.
5. Distributed persistence thuộc 628.
6. Consensus thuộc 635.
7. Telemetry thuộc 633.
8. Event transport thuộc 634.
9. Every active configuration có schema.
10. Every revision immutable.
11. Rollback tạo revision mới.
12. Read path không cần network.
13. Read path không giữ global mutex.
14. Watch overflow dẫn tới resync.
15. Revision ordering deterministic.
16. Target evaluation deterministic.
17. Percentage assignment deterministic.
18. Experiment assignment không tự suy ra winner.
19. Secret material không nằm trong history.
20. Capability không được nâng cấp qua config.
21. Resource hard limit không bị dynamic config bypass.
22. Control-plane outage không mặc định crash data plane.
23. Expired values follow explicit fallback.
24. Stale writers bị fencing.
25. Scope precedence deterministic.
26. Conflict phải explicit.
27. No implicit distributed transaction.
28. No mandatory external registry.
29. No mandatory external feature flag service.
30. No mandatory GC.
31. No mandatory third-party runtime.
32. Unused features dead-strip.
33. Dynamic values phải bounded.
34. Registry không trở thành duplicate service discovery.
35. Source-of-truth phải explicit.
36. Audit mutation phải deterministic.
37. Rollout không xóa lịch sử.
38. Signed snapshots phải chống replay.
39. Offline authority phải có expiry.
40. Edge authority phải có fencing.
41. Watcher không được block activation.
42. Slow consumer không được block producer.
43. Invalid schema không được activate.
44. Invalid signature không được activate.
45. Unauthorized mutation phải fail.
46. Tenant isolation phải được enforce.
47. Target expression không có side effects.
48. Time-dependent behavior phải explicit.
49. Revision metadata phải đủ để reproduce state.
50. Application data plane không phụ thuộc per-request control-plane availability.

---

# 201. Acceptance Criteria

Implementation phải đạt tối thiểu **300 acceptance criteria** bao phủ:

### Configuration
- typed config;
- schemas;
- revisions;
- snapshots;
- precedence;
- transactions;
- rollback;
- validation;
- migration.

### Watch
- initial snapshot;
- monotonic revisions;
- gap detection;
- resync;
- backpressure;
- cancellation;
- reconnection.

### Feature flags
- boolean;
- enum;
- structured values;
- targeting;
- percentage rollout;
- deterministic assignment;
- kill switch;
- expiry.

### Experiments
- variants;
- allocation;
- deterministic subject assignment;
- experiment groups;
- exposure events;
- lifecycle;
- privacy.

### Dynamic policies
- precedence;
- bounds;
- fallback;
- resource interaction;
- security boundary;
- policy references.

### Signals
- metric sources;
- windows;
- thresholds;
- stale handling;
- insufficient data;
- 633 integration;
- 636 health-gate integration.

### Registry
- namespaces;
- metadata;
- revisions;
- source-of-truth;
- consistency;
- federation.

### Federation
- global/region/cluster/edge;
- delegated authority;
- fencing;
- offline;
- reconnect;
- conflict resolution.

### Security
- authentication;
- authorization;
- capability;
- audit;
- signature;
- replay protection;
- tenant isolation;
- secret exclusion.

### Reliability
- provider failure;
- control-plane partition;
- stale snapshots;
- crash recovery;
- rollback;
- deterministic reconciliation.

### Performance
- O(1) reads;
- lock-free/low-lock read path;
- bounded watch queues;
- bounded target evaluation;
- snapshot atomicity;
- dead stripping.

### Toolchain
- compiler annotations;
- generated metadata;
- CLI;
- diff;
- explain;
- simulator;
- schema validation.

### Testing
- unit;
- property;
- fuzz;
- model;
- fault injection;
- security;
- compatibility;
- deterministic replay.

---

# 202. Final architecture

```text
                     ┌───────────────────────────────┐
                     │       Axiom Application        │
                     └───────────────┬───────────────┘
                                     │
                         Typed Control API
                                     │
              ┌──────────────────────▼──────────────────────┐
              │                 637 Runtime                 │
              ├─────────────────────────────────────────────┤
              │ Config                                       │
              │ Feature Flags                                │
              │ Experiments                                  │
              │ Dynamic Policies                             │
              │ Progressive Signals                          │
              │ Global Control Registry                     │
              ├─────────────────────────────────────────────┤
              │ Snapshot / Revision / Watch / Rollout       │
              ├─────────────────────────────────────────────┤
              │ Provider / Cache / Federation / Edge        │
              └──────────────────────┬──────────────────────┘
                                     │
        ┌──────────────┬─────────────┼─────────────┬──────────────┐
        ▼              ▼             ▼             ▼              ▼
      628            635           633           634            636
 Distributed       Control       Telemetry       Events       Deployment
    State           Plane
        │              │             │             │              │
        └──────────────┴─────────────┴─────────────┴──────────────┘
                                     │
                              603 Security
                              606 Resources
                              610 Crypto
                              601 Bootstrap
```

---

# 203. Core principle

BOOTSTRAP-637 hoàn thiện một lớp quan trọng của Axiom:

```text
STATIC BINARY
     │
     ▼
RUNTIME CONTROL
     │
     ├── configuration
     ├── feature flags
     ├── experiments
     ├── operational policy
     ├── progressive signals
     └── global metadata
```

Trong đó:

```text
Code = static authority
Config = dynamic data
Policy = bounded control
Feature = deterministic behavior switch
Experiment = deterministic assignment
Signal = measurement
Deployment = orchestration
Security = authority
```

Đây là ranh giới giúp Axiom có khả năng điều khiển hệ thống phân tán rất mạnh mà không biến runtime thành một scripting engine không kiểm soát.

---

# 204. Trạng thái

**BOOTSTRAP-637 = COMPLETE**

Đã xác định:

- architecture;
- ownership boundaries;
- distributed configuration;
- feature flags;
- experimentation;
- dynamic operational policy;
- progressive delivery signals;
- global registry;
- federation;
- edge control;
- offline snapshots;
- revision model;
- watch model;
- security model;
- rollback;
- reconciliation;
- compiler integration;
- runtime API;
- CLI;
- testing;
- performance;
- binary-size strategy;
- 50 architecture invariants;
- ≥300 acceptance criteria target.

**Task tiếp theo: BOOTSTRAP-638 — Native Distributed Secrets, Key Rotation, Certificate Rotation, Identity Rotation, Trust Registry & Global Credential Lifecycle Runtime 5.0.**
:::

BOOTSTRAP-637 đã hoàn tất. Theo chuỗi tự động, task kế tiếp là **BOOTSTRAP-638**.