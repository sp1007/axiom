# BOOTSTRAP-766 — AXREGISTRY

**Title:** Native Naming, Service Discovery, Resource Registry, Endpoint Registry, Type/Schema Registry & Versioned Resolution Runtime 5.0  
**Namespace:** `AXREGISTRY`  
**Phase:** Axiom Civilization Runtime / Native Registry & Resolution Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXREGISTRY` là infrastructure layer chuẩn của Axiom cho việc:

- đăng ký resource;
- đặt tên;
- namespace;
- service discovery;
- endpoint discovery;
- resource resolution;
- version selection;
- schema/type registration;
- lifecycle tracking;
- dependency resolution;
- local/remote registry;
- deterministic lookup.

Core principle:

```text
NAME
  ↓
NAMESPACE
  ↓
REGISTRY
  ↓
IDENTITY
  ↓
RESOURCE / SERVICE / ENDPOINT
  ↓
RESOLUTION
  ↓
AUTHORIZATION
```

`AXREGISTRY` **không quyết định quyền truy cập**.

---

# 2. Boundary

`AXREGISTRY` sở hữu:

- registry;
- namespace;
- registration;
- names;
- aliases;
- resource identity;
- service identity;
- endpoint discovery;
- version;
- compatibility;
- resolution;
- leases;
- health metadata;
- dependency metadata;
- local/remote registry;
- watch/change notifications.

Không sở hữu:

- authentication → `AXAUTH`;
- authorization → `AXPOLICY` / `AXSECURITY`;
- identity authority → `AXIDENTITY`;
- networking → `AXNETWORK`;
- service execution → application/runtime owner;
- configuration → `AXCONFIG`;
- schema serialization → `AXCODEC`.

---

# 3. Kiến trúc

```text id="regarch"
                    AXREGISTRY
                         │
       ┌─────────────────┼──────────────────┐
       ▼                 ▼                  ▼
   Namespace          Registry           Resolver
       │                 │                  │
       ▼                 ▼                  ▼
    Naming         Registration         Discovery
                         │                  │
                         └────────┬─────────┘
                                  ▼
                             Resource ID
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                 AXIDENTITY    AXNETWORK      AXSECURITY
                    │             │             │
                    └─────────────┼─────────────┘
                                  ▼
                              Consumer
```

---

# 4. Registry object

```text id="regobj"
registry {
    registry_id
    namespace
    version
    authority
    entries
    revision
    capabilities
}
```

Registry có revision để hỗ trợ:

- cache;
- watch;
- optimistic concurrency;
- deterministic snapshots.

---

# 5. Registry entry

```text id="entry"
registry_entry {
    entry_id
    name
    namespace
    kind
    resource_id
    version
    state
    metadata
    endpoints
    owner
    revision
    lease
}
```

---

# 6. Entry kinds

Baseline:

```text id="kinds"
SERVICE
RESOURCE
ENDPOINT
DEVICE
PROCESS
APPLICATION
DATABASE
SCHEMA
TYPE
PLUGIN
MODULE
PACKAGE
NAMESPACE
```

Không phải mọi kind đều cần cùng metadata.

---

# 7. Namespace

Namespace ngăn collision:

```text id="namespace"
namespace {
    namespace_id
    parent
    name
    authority
}
```

Ví dụ:

```text id="example"
system/
system/network/
system/storage/
app/com.example.chat/
```

---

# 8. Hierarchical naming

Canonical name:

```text id="hiername"
system.network.dns
```

hoặc URI-like canonical representation tùy ABI.

Axiom phải chọn một canonical encoding và không cho nhiều equivalent forms trong registry core.

---

# 9. Name normalization

Tên phải được normalize trước registration/resolution.

Rules phải xác định:

- Unicode normalization;
- case sensitivity;
- separator;
- escaping;
- reserved names.

---

# 10. UTF-8

Registry names mặc định UTF-8.

Nhưng identifier canonicalization phải tránh trường hợp hai Unicode representations tạo hai tên visually identical nhưng binary khác nhau.

---

# 11. Case sensitivity

Registry namespace khai báo:

```text id="cases"
CASE_SENSITIVE
CASE_INSENSITIVE
```

Không được tự động assume Windows-like case folding cho mọi platform.

---

# 12. Resource identity

Tên không phải identity.

```text id="nameid"
"name/service-A"
       ↓
resource_id = stable identity
```

Tên có thể thay đổi; identity có thể giữ nguyên.

---

# 13. Identity integration

`resource_id` có thể liên kết với:

```text id="identitylink"
AXIDENTITY
```

Registry không tự tạo authoritative identity nếu resource đã có identity authority.

---

# 14. Aliases

Một resource có thể có:

```text id="aliases"
primary-name
alias-A
alias-B
```

Resolution trả về cùng resource identity.

---

# 15. Alias lifecycle

Alias phải có:

```text id="aliaslife"
created
active
deprecated
removed
```

Không silently redirect forever.

---

# 16. Version

Registry entry có version:

```text id="version"
major
minor
patch
build
```

Semantic interpretation có thể phụ thuộc resource kind.

---

# 17. Version identity

Version phải là typed data, không chỉ string.

```text id="verstruct"
version {
    major
    minor
    patch
    pre_release
    build
}
```

---

# 18. Version constraints

Resolver hỗ trợ:

```text id="constraints"
exact
minimum
maximum
range
compatible
latest_allowed
```

---

# 19. No implicit latest

Application không nên mặc định:

```text id="badlatest"
resolve("service")
→ latest forever
```

Nếu reproducibility cần thiết, resolution phải pin version/revision.

---

# 20. Compatibility

Entry có thể declare:

```text id="compat"
api_version
abi_version
schema_version
capabilities
```

Resolver có thể reject incompatible entries.

---

# 21. API vs ABI

Registry phân biệt:

```text id="apiabi"
API compatibility
ABI compatibility
schema compatibility
```

Một service có API-compatible version nhưng ABI-incompatible implementation vẫn phải được nhận diện đúng.

---

# 22. Service

```text id="service"
service {
    service_id
    interface_id
    version
    endpoints
    capabilities
    state
}
```

---

# 23. Endpoint

```text id="endpoint"
endpoint {
    endpoint_id
    transport
    address
    protocol
    version
    health
    metadata
}
```

AXNETWORK sở hữu transport semantics.

---

# 24. Local endpoint

Ví dụ:

```text id="localep"
IPC endpoint
Unix socket
Windows named endpoint
shared-memory endpoint
```

Registry chỉ lưu/resolve metadata.

---

# 25. Remote endpoint

Ví dụ:

```text id="remoteep"
tcp
udp
quic
http
```

AXNETWORK chịu trách nhiệm kết nối.

---

# 26. Discovery

Discovery query:

```text id="discover"
service = "database"
version >= 3
capability = "transactions"
```

Registry trả candidate set.

---

# 27. Resolution

Resolution pipeline:

```text id="resolve"
query
 ↓
namespace
 ↓
name lookup
 ↓
version filtering
 ↓
compatibility filtering
 ↓
health/state filtering
 ↓
policy/security check
 ↓
selected resource
```

Registry không tự bypass security.

---

# 28. Authorization boundary

```text id="authboundary"
AXREGISTRY
    ↓
candidate resource
    ↓
AXSECURITY
    ↓
allowed / denied
```

Registry resolution không đồng nghĩa permission.

---

# 29. Capability filtering

Query có thể include:

```text id="capfilter"
required_capability
```

Registry có thể filter metadata.

Nhưng authoritative capability enforcement vẫn thuộc AXSECURITY.

---

# 30. Health

Entry có state:

```text id="health"
UNKNOWN
STARTING
READY
DEGRADED
UNAVAILABLE
STOPPING
FAILED
```

Health information không tự grant authorization.

---

# 31. Health freshness

Health metadata phải có:

```text id="fresh"
observed_at
expires_at
source
```

Resolver không dùng stale health như current truth.

---

# 32. Lease

Dynamic registration sử dụng lease:

```text id="lease"
registration
    ↓
lease
    ↓
renew
    ↓
expire
```

---

# 33. Lease semantics

Lease có:

```text id="lease2"
lease_id
issued_at
expires_at
renewal_policy
generation
```

Expiration dùng `AXTIME` monotonic/deadline semantics khi phù hợp.

---

# 34. Registration lifecycle

```text id="reglife"
CREATE
  ↓
ACTIVE
  ↓
RENEWING
  ↓
EXPIRED / WITHDRAWN
```

---

# 35. Atomic registration

Register phải atomic.

Không để:

```text id="halfreg"
name exists
resource metadata missing
```

ở trạng thái observable.

---

# 36. Duplicate registration

Nếu cùng canonical name:

```text id="dup"
existing
+
new
```

registry phải trả:

```text id="duperr"
REGISTRY_NAME_CONFLICT
```

trừ khi explicit replacement/update semantics được sử dụng.

---

# 37. Ownership

Entry có owner identity:

```text id="owner"
owner_id
```

Owner không mặc nhiên có mọi privileges; security layer xác định quyền mutation.

---

# 38. Update

Entry update sử dụng revision:

```text id="revision"
expected_revision
```

Nếu mismatch:

```text id="conflict"
REGISTRY_CONFLICT
```

---

# 39. Compare-and-swap

Dynamic registry hỗ trợ:

```text id="cas"
update_if_revision(expected, new)
```

cho lock-free/optimistic workflows.

---

# 40. Registry revision

Mỗi mutation tạo:

```text id="regrev"
revision + 1
```

Revision phải monotonic trong một registry authority.

---

# 41. Snapshot

```text id="snapshot"
registry_snapshot {
    registry_id
    revision
    timestamp
    entries
}
```

Snapshot dùng cho deterministic resolution.

---

# 42. Snapshot consistency

Một snapshot phải biểu diễn một logical registry state.

Không cho consumer thấy nửa revision cũ + nửa revision mới.

---

# 43. Watch

API:

```text id="watch"
registry_watch(query)
```

events:

```text id="watchevents"
ADDED
UPDATED
REMOVED
EXPIRED
HEALTH_CHANGED
VERSION_CHANGED
```

---

# 44. Watch ordering

Events trong cùng registry phải có ordered revision:

```text id="watchorder"
revision 100
revision 101
revision 102
```

Consumer có thể detect missing revisions.

---

# 45. Watch recovery

Nếu consumer mất event:

```text id="watchrecover"
last_revision
      ↓
resync
      ↓
snapshot
      ↓
watch from revision
```

---

# 46. Registry cache

Client-side cache:

```text id="cache"
query
 ↓
cache
 ↓
revision
 ↓
resolve
```

Cache entry phải có freshness/revision semantics.

---

# 47. Cache invalidation

Watch có thể invalidate cache.

Không dựa chỉ vào TTL nếu correctness yêu cầu current registry state.

---

# 48. Negative cache

Not-found results có thể cache bounded-time.

```text id="negative"
NOT_FOUND
```

phải có expiration để tránh stale absence.

---

# 49. Local registry

Every process có thể có process-local registry:

```text id="localreg"
process
 └── local registry
```

Fastest resolution path.

---

# 50. Host registry

OS/runtime host registry:

```text id="hostreg"
machine
 └── host registry
```

cho services/resources chung.

---

# 51. Cluster registry

Distributed deployments có thể có:

```text id="clusterreg"
cluster registry
```

nhưng consistency semantics phải explicit.

---

# 52. Distributed registry

AXREGISTRY core không ép một consensus algorithm.

Backend có thể sử dụng:

- centralized authority;
- replicated registry;
- consensus-based store;
- eventually consistent discovery.

Consistency level phải được công khai.

---

# 53. Consistency modes

```text id="consistency"
LOCAL_STRONG
AUTHORITY_STRONG
SNAPSHOT
EVENTUAL
STALE_ALLOWED
```

---

# 54. Discovery correctness

Consumer phải biết resolution guarantee:

```text id="guarantee"
freshness
revision
consistency
authority
```

Không coi eventually consistent result là authoritative current state.

---

# 55. Registry authority

```text id="authority"
registry_authority {
    authority_id
    scope
    parent
    trust
}
```

Authority xác định registry nào có quyền canonical cho namespace.

---

# 56. Namespace delegation

Parent namespace có thể delegate:

```text id="delegate"
system/
  ↓
delegate
system.example/
```

Delegation phải explicit.

---

# 57. Namespace collision

Hai authorities không được đồng thời claim canonical ownership cùng namespace mà không có explicit federation rule.

---

# 58. Federation

Registry federation:

```text id="federation"
registry A
   │
   ├── namespace X
   │
registry B
   └── namespace Y
```

Resolver biết authority boundary.

---

# 59. Remote resolution

Remote registry:

```text id="remote"
local resolver
      ↓
remote registry
      ↓
result
```

Network transport thuộc AXNETWORK.

---

# 60. Security of remote registry

Remote result không mặc nhiên trusted.

```text id="remotesec"
remote registry
      ↓
identity/trust
      ↓
AXTRUST
      ↓
AXSECURITY
```

---

# 61. Registry poisoning

Registry architecture phải chống:

- unauthorized registration;
- unauthorized overwrite;
- namespace hijacking;
- stale endpoint reuse;
- identity mismatch.

Enforcement thuộc AXSECURITY.

---

# 62. Endpoint identity

Endpoint metadata phải có stable endpoint ID.

Address có thể thay đổi:

```text id="endpointid"
endpoint_id = stable
address = mutable
```

---

# 63. Endpoint generation

Khi endpoint được replaced:

```text id="endpointgen"
endpoint_id
generation++
```

Consumer có thể phát hiện stale handles.

---

# 64. Stale resolution

Resolved handle nên chứa:

```text id="handle"
resource_id
entry_revision
generation
```

Resource replacement không được silently masquerade as same instance nếu semantics yêu cầu instance identity.

---

# 65. Service instances

Một service name có thể map tới nhiều instances:

```text id="instances"
service
 ├── instance A
 ├── instance B
 └── instance C
```

---

# 66. Instance selection

Resolver có thể filter:

- version;
- capability;
- health;
- locality;
- architecture;
- protocol;
- resource constraints.

Không tự quyết định load balancing policy ngoài declared policy.

---

# 67. Locality

Metadata:

```text id="locality"
process
host
NUMA node
zone
region
```

AXREGISTRY lưu metadata; infrastructure policy quyết định selection.

---

# 68. Architecture compatibility

Service instance có thể declare:

```text id="arch"
x86_64
arm64
wasm
```

Resolver có thể filter based on consumer target.

---

# 69. Device registry

Devices có thể register:

```text id="device"
device class
vendor
model
instance
capabilities
```

AXDEVICE sở hữu actual device operations.

---

# 70. Process registry

AXPROCESS có thể publish:

```text id="process"
process_id
application_id
endpoints
services
state
```

Registry không thay thế process manager.

---

# 71. Application registry

AXAPPLICATION có thể publish:

```text id="application"
application_id
version
services
UI endpoints
protocols
```

---

# 72. Database registry

AXDATABASE có thể publish:

```text id="database"
database_id
logical_name
version
endpoint
schema_version
capabilities
```

Registry không quản lý database transactions.

---

# 73. Schema registry

AXREGISTRY có thể register:

```text id="schema"
schema_id
namespace
version
hash
compatibility
```

Actual encoding/decoding thuộc AXCODEC.

---

# 74. Type registry

Compiler/runtime metadata có thể register:

```text id="type"
type_id
module_id
version
layout_hash
abi_hash
```

Không biến runtime registry thành mandatory reflection system.

---

# 75. Static linking

Static applications có thể resolve registry references compile-time:

```text id="static"
source
 ↓
registry metadata
 ↓
compiler
 ↓
direct symbol binding
```

Không cần runtime registry.

---

# 76. Dynamic linking

Dynamic modules có thể resolve:

```text id="dynamic"
module
 ↓
runtime registry
 ↓
ABI-compatible provider
```

---

# 77. Symbol registry boundary

Linker symbol resolution vẫn thuộc compiler/linker/object subsystem.

AXREGISTRY chỉ xử lý runtime resource/service naming.

---

# 78. Dependency registration

Package/module có thể declare:

```text id="deps"
requires:
    service A >= 2
    schema B = 5
```

Resolver produces dependency graph.

---

# 79. Dependency cycle

Cycle:

```text id="cycle"
A → B → C → A
```

phải được phát hiện khi dependency semantics yêu cầu DAG.

Registry không tự phá cycle.

---

# 80. Resolution query

Canonical query:

```text id="query"
registry_query {
    namespace
    name
    kind
    version_constraint
    required_capabilities
    health_requirement
    locality
    architecture
}
```

---

# 81. Resolution result

```text id="result"
resolution {
    resource_id
    entry_id
    version
    endpoint_set
    registry_revision
    authority
    freshness
}
```

---

# 82. Multiple results

Resolver có thể trả:

```text id="candidates"
resolution_set {
    candidates[]
    revision
}
```

Selection policy có thể do caller/application/service-discovery policy quyết định.

---

# 83. Deterministic resolution

Nếu caller yêu cầu deterministic:

```text id="detres"
snapshot revision
+
explicit selection policy
```

phải cho cùng result khi state không đổi.

---

# 84. Randomized selection

Load balancing có thể dùng `AXRANDOM`.

Nhưng registry core không tự dùng randomness để chọn instance trừ khi caller yêu cầu.

---

# 85. Time integration

Leases, TTL, expiration sử dụng `AXTIME`.

Không dùng wall clock để xác định lease timeout nếu elapsed-time semantics được yêu cầu.

---

# 86. Configuration integration

AXCONFIG có thể cấu hình:

- registry endpoints;
- namespaces;
- discovery policy;
- cache limits;
- lease intervals.

Security policy vẫn thuộc AXSECURITY.

---

# 87. Observability

AXOBSERVABILITY metrics:

```text id="regmetrics"
lookup_count
lookup_latency
cache_hit
cache_miss
registration_count
lease_expiration
watch_events
resolution_failures
```

---

# 88. Logging

AXLOGGING có thể record:

```text id="reglog"
registration failure
resolution failure
watch resync
authority change
```

Không log credentials/secrets.

---

# 89. Audit

AXAUDIT ghi:

```text id="regaudit"
administrative registration
namespace delegation
authority change
unauthorized registry mutation
```

Không audit every read nếu không required.

---

# 90. Diagnostics

AXDIAGNOSTICS có thể inspect:

```text id="regdiag"
registry revision
cache
watch state
lease state
resolution latency
stale entries
```

---

# 91. Compiler integration

Compiler có thể resolve static service declarations:

```text id="compreg"
@requires("system.logging", version >= 2)
```

Compiler validates metadata when registry is available.

Runtime semantics vẫn explicit.

---

# 92. AI metadata

Registry entries có thể chứa machine-readable:

```text id="aimeta"
description
capabilities
input_schema
output_schema
examples
compatibility
```

AI tooling có thể discover services.

Metadata không grant authority.

---

# 93. AI safety boundary

AI agent có thể:

- query registry;
- discover service;
- inspect schema;
- generate client binding.

AI không được tự:

- register privileged service;
- replace authority;
- bypass AXSECURITY;
- claim namespace ownership.

---

# 94. Native API — registry

```text id="api1"
registry_create()
registry_open()
registry_close()
registry_snapshot()
registry_revision()
```

---

# 95. Native API — namespace

```text id="api2"
namespace_create()
namespace_open()
namespace_delegate()
namespace_info()
namespace_delete()
```

---

# 96. Native API — registration

```text id="api3"
registry_register()
registry_update()
registry_unregister()
registry_renew()
registry_get()
```

---

# 97. Native API — resolution

```text id="api4"
registry_resolve()
registry_resolve_all()
registry_query()
registry_select()
```

---

# 98. Native API — watch

```text id="api5"
registry_watch()
watch_next()
watch_ack()
watch_resync()
watch_close()
```

---

# 99. Native API — lease

```text id="api6"
lease_create()
lease_renew()
lease_release()
lease_status()
```

---

# 100. Native API — version

```text id="api7"
version_parse()
version_compare()
version_satisfies()
version_constraint_parse()
```

---

# 101. Native API — aliases

```text id="api8"
registry_alias_add()
registry_alias_remove()
registry_alias_list()
```

---

# 102. Native API — schema/type

```text id="api9"
schema_register()
schema_resolve()
type_register()
type_resolve()
```

---

# 103. Native API — diagnostics

```text id="api10"
registry_stats()
registry_validate()
registry_export_snapshot()
registry_simulate()
registry_replay()
```

---

# 104. Native ABI

```text id="abi"
AXREGISTRY_ABI_1
```

Canonical types:

```text id="types"
Registry
Namespace
RegistryEntry
ResourceId
ServiceId
Endpoint
Version
VersionConstraint
Lease
RegistrySnapshot
Resolution
ResolutionSet
RegistryWatch
SchemaId
TypeId
```

---

# 105. Error model

```text id="errors"
REGISTRY_INVALID
REGISTRY_NOT_FOUND
REGISTRY_NAME_CONFLICT
REGISTRY_NAMESPACE_INVALID
REGISTRY_NAMESPACE_EXISTS
REGISTRY_NAMESPACE_NOT_FOUND
REGISTRY_PERMISSION_DENIED
REGISTRY_REVISION_CONFLICT
REGISTRY_VERSION_INVALID
REGISTRY_VERSION_UNSATISFIED
REGISTRY_INCOMPATIBLE
REGISTRY_ENDPOINT_INVALID
REGISTRY_ENDPOINT_UNAVAILABLE
REGISTRY_LEASE_EXPIRED
REGISTRY_LEASE_INVALID
REGISTRY_WATCH_CLOSED
REGISTRY_WATCH_OVERFLOW
REGISTRY_WATCH_RESYNC_REQUIRED
REGISTRY_STALE
REGISTRY_AUTHORITY_INVALID
REGISTRY_AUTHORITY_UNAVAILABLE
REGISTRY_SNAPSHOT_INVALID
REGISTRY_SCHEMA_INVALID
REGISTRY_TYPE_INVALID
REGISTRY_DEPENDENCY_CYCLE
REGISTRY_LIMIT
```

---

# 106. Performance architecture

Primary fast path:

```text id="fastpath"
resolve()
   ↓
local cache
   ↓
revision validation
   ↓
resource handle
```

Remote lookup chỉ xảy ra khi cache không đủ.

---

# 107. Data structure

Local registry có thể sử dụng:

```text id="datastruct"
hash table
radix tree
sorted namespace index
version index
```

Implementation choice.

Không yêu cầu một structure duy nhất cho mọi registry.

---

# 108. Read path

Registry reads nên:

- lock-free hoặc read-optimized;
- immutable snapshots;
- zero allocation cho common cache hit.

---

# 109. Write path

Registration/update có thể dùng:

```text id="write"
transaction
 ↓
validate
 ↓
CAS revision
 ↓
publish immutable snapshot
 ↓
watch events
```

---

# 110. No global lock requirement

Không được thiết kế architecture bắt buộc:

```text id="globalmutex"
all lookups
 ↓
global mutex
```

---

# 111. Snapshot publication

Một snapshot mới được publish atomically.

Reader thấy:

```text old snapshot
```

hoặc:

```text new snapshot
```

không thấy partial mutation.

---

# 112. Memory reclamation

Old immutable snapshots có thể được reclaim bằng:

- epoch;
- reference counting;
- hazard pointers;
- arena generations.

Không yêu cầu GC.

---

# 113. Resource limits

Registry phải giới hạn:

```text id="limits"
max_entries
max_namespaces
max_aliases
max_watchers
max_metadata
max_endpoint_count
max_query_results
```

---

# 114. Metadata size

Arbitrary huge metadata không được phép trong registry hot path.

Large metadata nên nằm ở AXSTORAGE/content store và registry giữ reference.

---

# 115. Registry persistence

Persistent registry có thể snapshot:

```text id="persist"
registry
 ↓
snapshot
 ↓
AXSTORAGE
```

Crash recovery phải atomic.

---

# 116. Journal

Dynamic authoritative registry có thể dùng append-only mutation journal:

```text id="journal"
register
update
renew
remove
```

AXAUDIT vẫn giữ security evidence riêng.

Registry journal không thay thế audit log.

---

# 117. Crash recovery

```text id="recover"
snapshot
+
journal
 ↓
validate
 ↓
reconstruct revision
 ↓
publish
```

---

# 118. Stale lease recovery

Sau restart, dynamic leases không được tự coi là valid vô thời hạn.

Lease restoration phải theo explicit persistence semantics.

---

# 119. Security context

Registry mutation phải receive:

```text id="secctx"
AXSECURITY security_context
```

để enforce:

- namespace ownership;
- registration capability;
- delegation;
- replacement rights.

---

# 120. No trust by discovery

Discovery result:

```text id="nottrust"
resolve(service)
```

không đồng nghĩa:

```text trusted(service)
```

Trust thuộc AXTRUST/AXSECURITY.

---

# 121. Service identity verification

Caller có thể verify resolved service identity before use.

Registry cung cấp identity metadata; verification authority thuộc AXIDENTITY/AXTRUST.

---

# 122. Endpoint freshness

Endpoint result phải có:

```text id="freshness"
registry_revision
endpoint_generation
observed_time
lease_expiry
```

để caller detect stale result.

---

# 123. Hot replacement

Service có thể replace endpoint:

```text id="replace"
old endpoint
   ↓
new endpoint
```

với generation increment.

Clients dùng stale handle phải nhận defined error/reconnect semantics.

---

# 124. Graceful retirement

Entry có thể:

```text id="retire"
ACTIVE
 ↓
DRAINING
 ↓
REMOVED
```

để service migration.

---

# 125. Health vs lifecycle

`FAILED` và `REMOVED` không đồng nghĩa.

- `FAILED` = resource vẫn registered nhưng unhealthy.
- `REMOVED` = no longer registered.

---

# 126. Dependency health

Registry có thể expose dependency metadata.

Không tự recursively health-check arbitrary dependencies trên mỗi lookup.

---

# 127. Discovery storm prevention

Remote discovery phải có:

- bounded retries;
- caching;
- backoff;
- request coalescing.

---

# 128. Request coalescing

Nếu 100 tasks cùng resolve:

```text id="coalesce"
service-X
```

runtime có thể coalesce một remote query thay vì tạo 100 network requests.

---

# 129. Negative lookup coalescing

Not-found queries cũng có thể coalesce nhưng phải bounded.

---

# 130. Watch backpressure

Watcher chậm:

```text id="watchbp"
producer
 ↓
bounded queue
 ↓
slow consumer
```

không được gây block toàn registry.

Overflow → `RESYNC_REQUIRED`.

---

# 131. Deterministic watch

Simulation có thể replay:

```text id="watchreplay"
revision
event
revision
event
```

theo exact order.

---

# 132. Registry simulation

Virtual registry:

```text id="regsim"
registry_simulate()
```

cho test discovery/failover.

Không truy cập production registry.

---

# 133. Fault injection

Test profile có thể mô phỏng:

- stale entry;
- expired lease;
- endpoint failure;
- registry unavailable;
- watch overflow;
- revision conflict.

---

# 134. Network partition

Distributed registry adapter phải expose:

```text id="partition"
CONNECTED
PARTITIONED
STALE
RECOVERING
```

không che giấu eventual consistency.

---

# 135. Authority failure

Nếu authoritative registry unavailable:

```text id="authfail"
```

resolver phải tuân theo declared consistency policy.

Không tự giả định cached result là authoritative current truth.

---

# 136. Offline operation

Applications có thể dùng pinned snapshot:

```text id="offline"
snapshot revision 100
```

cho deterministic/offline execution.

---

# 137. Registry export

Export:

```text id="export"
registry_snapshot
```

phải preserve:

- IDs;
- names;
- versions;
- revision;
- authority;
- endpoint generations.

Secrets phải được redacted.

---

# 138. Registry import

Import phải validate:

- schema;
- authority;
- identity;
- revision;
- signatures nếu applicable;
- namespace ownership.

Không overwrite authoritative registry silently.

---

# 139. Interoperability

AXREGISTRY có thể cung cấp adapters cho:

- DNS;
- service discovery systems;
- OS registries;
- container/service orchestrators.

Adapters không trở thành core dependencies.

---

# 140. Formal invariants

```text id="reginv"
REG-INV-01
Tên registry không phải resource identity.

REG-INV-02
Mỗi canonical entry phải có stable entry identity.

REG-INV-03
Canonical name không được có hai owners đồng thời trong cùng authority scope.

REG-INV-04
Namespace ownership phải explicit.

REG-INV-05
Namespace delegation phải explicit.

REG-INV-06
Registry resolution không đồng nghĩa authorization.

REG-INV-07
Registry resolution không đồng nghĩa trust.

REG-INV-08
Registry không được bypass AXSECURITY.

REG-INV-09
Registry mutation phải chịu authorization.

REG-INV-10
Entry update phải có atomic semantics.

REG-INV-11
Registry revision phải monotonic trong một authority.

REG-INV-12
Snapshot phải biểu diễn một logical registry state.

REG-INV-13
Reader không được thấy partial snapshot publication.

REG-INV-14
Version constraint phải được evaluate theo explicit semantics.

REG-INV-15
"latest" không được mặc định là immutable/reproducible resolution.

REG-INV-16
API compatibility và ABI compatibility phải được phân biệt.

REG-INV-17
Stale endpoint phải có khả năng được phát hiện.

REG-INV-18
Endpoint replacement phải có generation semantics.

REG-INV-19
Lease expiration phải có deterministic semantics.

REG-INV-20
Lease timeout phải dùng appropriate AXTIME clock semantics.

REG-INV-21
Health information phải có freshness metadata.

REG-INV-22
Stale health không được mặc định coi là current health.

REG-INV-23
Watch event phải có ordered revision.

REG-INV-24
Watch overflow phải có resynchronization mechanism.

REG-INV-25
Slow watcher không được block toàn registry.

REG-INV-26
Remote registry result không mặc định trusted.

REG-INV-27
Registry cache phải có revision/freshness semantics.

REG-INV-28
Negative cache phải bounded lifetime.

REG-INV-29
Registry read hot path không được bắt buộc global lock.

REG-INV-30
Common local resolution phải hỗ trợ zero-allocation fast path.

REG-INV-31
Large metadata không được bắt buộc nằm trong hot registry entry.

REG-INV-32
Registry persistence phải có crash-consistent recovery.

REG-INV-33
Registry journal không thay thế security audit.

REG-INV-34
Service lifecycle và health state phải được phân biệt.

REG-INV-35
Dynamic service replacement phải preserve explicit instance identity semantics.

REG-INV-36
Distributed registry consistency level phải được công khai.

REG-INV-37
Deterministic resolution phải pin snapshot/revision hoặc equivalent state.

REG-INV-38
AI discovery không được grant authority.

REG-INV-39
Registry adapters không được trở thành mandatory third-party runtime dependencies.

REG-INV-40
AXREGISTRY chỉ chịu trách nhiệm naming, registration, discovery và resolution; authorization/trust/execution phải thuộc subsystem tương ứng.
```

---

# 141. Definition of Done

`AXREGISTRY 5.0` được freeze khi Axiom có:

- registry core;
- namespace;
- hierarchical naming;
- UTF-8 names;
- normalization;
- case policy;
- stable resource identity;
- aliases;
- version model;
- version constraints;
- compatibility metadata;
- service registration;
- endpoint registration;
- local discovery;
- remote discovery;
- resource resolution;
- multi-instance resolution;
- health metadata;
- leases;
- registration lifecycle;
- atomic updates;
- revision/CAS;
- immutable snapshots;
- watch;
- watch recovery;
- cache;
- negative cache;
- authority;
- namespace delegation;
- federation;
- consistency modes;
- schema registry;
- type registry;
- dependency metadata;
- dependency-cycle detection;
- static/dynamic integration;
- persistence;
- journal;
- crash recovery;
- stale detection;
- endpoint generation;
- service draining;
- request coalescing;
- backpressure;
- deterministic simulation;
- replay;
- fault injection;
- AXIDENTITY integration;
- AXTRUST integration;
- AXSECURITY integration;
- AXNETWORK integration;
- AXPROCESS integration;
- AXAPPLICATION integration;
- AXDATABASE integration;
- AXCODEC integration;
- AXTIME integration;
- AXCONFIG integration;
- AXOBSERVABILITY integration;
- AXLOGGING integration;
- AXAUDIT integration;
- AXDIAGNOSTICS integration;
- compiler metadata;
- AI metadata;
- native ABI;
- native APIs;
- 40 invariants.

**AXREGISTRY 5.0 → FROZEN.**

---

# BOOTSTRAP-767 — AXPACKAGE

**Native Package, Module Artifact, Dependency, Manifest, Repository, Version Resolution, Installation & Reproducible Package Runtime 5.0**

Module tiếp theo sẽ xây lớp **package/module distribution** phía trên `AXREGISTRY`:

```text
AXREGISTRY
     │
     │ discovers
     ▼
AXPACKAGE
     │
     ├── package identity
     ├── module identity
     ├── manifest
     ├── dependency graph
     ├── artifact
     ├── version
     ├── repository
     ├── cache
     ├── install
     ├── upgrade
     ├── rollback
     └── reproducible build metadata
```

Điểm kiến trúc quan trọng sẽ là **package manager không được biến Axiom thành một ngôn ngữ phụ thuộc runtime vào package repository**: compiler vẫn phải có khả năng build native artifact độc lập, offline và không có third-party compiler/runtime dependency.